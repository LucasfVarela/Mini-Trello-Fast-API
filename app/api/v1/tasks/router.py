from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.access import get_project_for_user, get_task_for_user
from app.api.v1.tasks import repository
from app.api.v1.tasks.schemas import (
    BoardRead,
    OrderDirection,
    TaskCreate,
    TaskOrderBy,
    TaskPage,
    TaskRead,
    TaskUpdate,
)
from app.core.deps import CurrentUser, DbSession
from app.models.project import Project
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.services.file_storage import delete_files

router = APIRouter(tags=["tasks"])

NON_NULLABLE_FIELDS = {"title", "status", "priority"}


def _validate_assignee(db: Session, project: Project, assignee_id: int | None) -> None:
    if assignee_id is None:
        return
    assignee = db.get(User, assignee_id)
    if assignee is None or not project.has_access(assignee):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario asignado debe ser miembro del proyecto",
        )


@router.get("/projects/{project_id}/tasks", response_model=TaskPage)
def list_tasks(
    project_id: int,
    db: DbSession,
    current_user: CurrentUser,
    status_filter: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: TaskPriority | None = None,
    assignee_id: int | None = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    overdue: bool = False,
    order_by: TaskOrderBy = TaskOrderBy.ID,
    direction: OrderDirection = OrderDirection.ASC,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> TaskPage:
    get_project_for_user(db, project_id, current_user)
    items, total = repository.list_tasks(
        db,
        project_id,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        overdue=overdue,
        order_by=order_by,
        direction=direction,
        page=page,
        size=size,
    )
    return TaskPage(
        items=[TaskRead.model_validate(task) for task in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/projects/{project_id}/board", response_model=BoardRead)
def get_board(project_id: int, db: DbSession, current_user: CurrentUser) -> BoardRead:
    get_project_for_user(db, project_id, current_user)
    board = repository.list_board(db, project_id)
    return BoardRead(
        todo=[TaskRead.model_validate(t) for t in board[TaskStatus.TODO]],
        in_progress=[TaskRead.model_validate(t) for t in board[TaskStatus.IN_PROGRESS]],
        done=[TaskRead.model_validate(t) for t in board[TaskStatus.DONE]],
    )


@router.post("/projects/{project_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(project_id: int, data: TaskCreate, db: DbSession, current_user: CurrentUser) -> Task:
    project = get_project_for_user(db, project_id, current_user)
    _validate_assignee(db, project, data.assignee_id)
    return repository.create(db, project.id, current_user, data.model_dump())


@router.get("/tasks/me", response_model=list[TaskRead])
def my_tasks(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: Annotated[TaskStatus | None, Query(alias="status")] = None,
) -> list[Task]:
    return repository.list_assigned_to(db, current_user, status_filter)


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: DbSession, current_user: CurrentUser) -> Task:
    return get_task_for_user(db, task_id, current_user)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, data: TaskUpdate, db: DbSession, current_user: CurrentUser) -> Task:
    task = get_task_for_user(db, task_id, current_user)
    changes = data.model_dump(exclude_unset=True)
    null_fields = [field for field in NON_NULLABLE_FIELDS if field in changes and changes[field] is None]
    if null_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Estos campos no pueden ser nulos: {', '.join(sorted(null_fields))}",
        )
    if "assignee_id" in changes:
        _validate_assignee(db, task.project, changes["assignee_id"])
    return repository.update(db, task, changes)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: DbSession, current_user: CurrentUser) -> Response:
    task = get_task_for_user(db, task_id, current_user)
    if task.created_by_id != current_user.id and not task.project.is_owner(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo quien creó la tarea o el dueño del proyecto pueden eliminarla",
        )
    stored_names = repository.delete(db, task)
    delete_files(stored_names)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
