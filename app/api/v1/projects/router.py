from fastapi import APIRouter, HTTPException, Response, status

from app.api.v1.access import get_owned_project, get_project_for_user
from app.api.v1.projects import repository
from app.api.v1.projects.schemas import MemberAdd, ProjectCreate, ProjectRead, ProjectUpdate
from app.core.deps import CurrentUser, DbSession
from app.models.project import Project
from app.services.file_storage import delete_files

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(db: DbSession, current_user: CurrentUser) -> list[Project]:
    return repository.list_for_user(db, current_user)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: DbSession, current_user: CurrentUser) -> Project:
    return repository.create(db, current_user, data.name, data.description)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: DbSession, current_user: CurrentUser) -> Project:
    return get_project_for_user(db, project_id, current_user)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int, data: ProjectUpdate, db: DbSession, current_user: CurrentUser
) -> Project:
    project = get_owned_project(db, project_id, current_user)
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes and changes["name"] is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="El nombre no puede ser nulo")
    return repository.update(db, project, changes)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: DbSession, current_user: CurrentUser) -> Response:
    project = get_owned_project(db, project_id, current_user)
    stored_names = repository.delete(db, project)
    delete_files(stored_names)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/members", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def add_member(project_id: int, data: MemberAdd, db: DbSession, current_user: CurrentUser) -> Project:
    project = get_owned_project(db, project_id, current_user)
    user = repository.get_user_by_username(db, data.username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if project.has_access(user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El usuario ya es parte del proyecto")
    return repository.add_member(db, project, user)


@router.delete("/{project_id}/members/{user_id}", response_model=ProjectRead)
def remove_member(project_id: int, user_id: int, db: DbSession, current_user: CurrentUser) -> Project:
    project = get_owned_project(db, project_id, current_user)
    member = next((m for m in project.members if m.id == user_id), None)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El usuario no es miembro del proyecto")
    return repository.remove_member(db, project, member)
