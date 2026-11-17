from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.attachment import Attachment
from app.models.project import Project
from app.models.task import Task
from app.models.user import User


def list_for_user(db: Session, user: User) -> list[Project]:
    stmt = (
        select(Project)
        .where(or_(Project.owner_id == user.id, Project.members.any(User.id == user.id)))
        .order_by(Project.id)
    )
    return list(db.scalars(stmt))


def create(db: Session, owner: User, name: str, description: str | None) -> Project:
    project = Project(name=name, description=description, owner=owner)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update(db: Session, project: Project, changes: dict) -> Project:
    for field, value in changes.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete(db: Session, project: Project) -> list[str]:
    stored_names = list(
        db.scalars(
            select(Attachment.stored_name).join(Task).where(Task.project_id == project.id)
        )
    )
    db.delete(project)
    db.commit()
    return stored_names


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def add_member(db: Session, project: Project, user: User) -> Project:
    project.members.append(user)
    db.commit()
    db.refresh(project)
    return project


def remove_member(db: Session, project: Project, user: User) -> Project:
    project.members.remove(user)
    for task in project.tasks:
        if task.assignee_id == user.id:
            task.assignee_id = None
    db.commit()
    db.refresh(project)
    return project
