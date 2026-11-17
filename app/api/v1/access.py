from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.attachment import Attachment
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


def get_project_for_user(db: Session, project_id: int, user: User) -> Project:
    project = db.get(Project, project_id)
    if project is None or not project.has_access(user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    return project


def get_owned_project(db: Session, project_id: int, user: User) -> Project:
    project = get_project_for_user(db, project_id, user)
    if not project.is_owner(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el dueño del proyecto puede realizar esta acción",
        )
    return project


def get_task_for_user(db: Session, task_id: int, user: User) -> Task:
    task = db.get(Task, task_id)
    if task is None or not task.project.has_access(user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return task


def get_attachment_for_user(db: Session, attachment_id: int, user: User) -> Attachment:
    attachment = db.get(Attachment, attachment_id)
    if attachment is None or not attachment.task.project.has_access(user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    return attachment
