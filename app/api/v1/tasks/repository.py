from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.api.v1.tasks.schemas import OrderDirection, TaskOrderBy
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User

PRIORITY_RANK = case(
    {TaskPriority.LOW: 1, TaskPriority.MEDIUM: 2, TaskPriority.HIGH: 3},
    value=Task.priority,
)

ORDER_COLUMNS = {
    TaskOrderBy.ID: Task.id,
    TaskOrderBy.TITLE: Task.title,
    TaskOrderBy.DUE_DATE: Task.due_date,
    TaskOrderBy.PRIORITY: PRIORITY_RANK,
    TaskOrderBy.CREATED_AT: Task.created_at,
}


def list_tasks(
    db: Session,
    project_id: int,
    *,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    assignee_id: int | None = None,
    search: str | None = None,
    overdue: bool = False,
    order_by: TaskOrderBy = TaskOrderBy.ID,
    direction: OrderDirection = OrderDirection.ASC,
    page: int = 1,
    size: int = 10,
) -> tuple[list[Task], int]:
    stmt = select(Task).where(Task.project_id == project_id)

    if status is not None:
        stmt = stmt.where(Task.status == status)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if assignee_id is not None:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if search:
        stmt = stmt.where(Task.title.ilike(f"%{search}%"))
    if overdue:
        stmt = stmt.where(Task.due_date < date.today(), Task.status != TaskStatus.DONE)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    column = ORDER_COLUMNS[order_by]
    ordering = column.desc() if direction == OrderDirection.DESC else column.asc()
    stmt = stmt.order_by(ordering, Task.id).offset((page - 1) * size).limit(size)

    return list(db.scalars(stmt)), total


def list_board(db: Session, project_id: int) -> dict[TaskStatus, list[Task]]:
    stmt = (
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(PRIORITY_RANK.desc(), Task.due_date.is_(None), Task.due_date, Task.id)
    )
    board: dict[TaskStatus, list[Task]] = {status: [] for status in TaskStatus}
    for task in db.scalars(stmt):
        board[task.status].append(task)
    return board


def list_assigned_to(db: Session, user: User, status: TaskStatus | None = None) -> list[Task]:
    stmt = select(Task).where(Task.assignee_id == user.id)
    if status is not None:
        stmt = stmt.where(Task.status == status)
    stmt = stmt.order_by(Task.due_date.is_(None), Task.due_date, Task.id)
    return list(db.scalars(stmt))


def create(db: Session, project_id: int, creator: User, data: dict) -> Task:
    task = Task(project_id=project_id, created_by_id=creator.id, **data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update(db: Session, task: Task, changes: dict) -> Task:
    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete(db: Session, task: Task) -> list[str]:
    stored_names = [attachment.stored_name for attachment in task.attachments]
    db.delete(task)
    db.commit()
    return stored_names
