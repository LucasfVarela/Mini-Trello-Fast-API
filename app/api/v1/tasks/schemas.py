from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.projects.schemas import MemberRead
from app.models.task import TaskPriority, TaskStatus


class TaskOrderBy(str, Enum):
    ID = "id"
    TITLE = "title"
    DUE_DATE = "due_date"
    PRIORITY = "priority"
    CREATED_AT = "created_at"


class OrderDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None
    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    assignee_id: int | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    project_id: int
    assignee: MemberRead | None
    created_by: MemberRead
    created_at: datetime
    updated_at: datetime


class TaskPage(BaseModel):
    items: list[TaskRead]
    total: int
    page: int
    size: int


class BoardRead(BaseModel):
    todo: list[TaskRead]
    in_progress: list[TaskRead]
    done: list[TaskRead]
