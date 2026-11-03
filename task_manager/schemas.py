from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .models import PRIORITY_RANK, Task

StatusValue = Literal["TODO", "IN_PROGRESS", "DONE"]
TaskType = Literal["bug", "feature", "chore"]


class TaskCreate(BaseModel):
    title: str
    project_id: int = Field(gt=0)
    assignee: str
    description: str = ""
    status: StatusValue = "TODO"
    priority: int = Field(default=2, ge=1, le=3)
    task_type: TaskType = "chore"

    @field_validator("title", "assignee")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: StatusValue | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    task_type: TaskType | None = None
    assignee: str | None = None

    @field_validator("*")
    @classmethod
    def not_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("omit unchanged fields; null is not supported")
        return value


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: int
    task_type: str
    assignee: str

    @classmethod
    def from_task(cls, task_id: int, task: Task) -> "TaskResponse":
        return cls(
            id=task_id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=PRIORITY_RANK[task.priority],
            task_type=task.task_type,
            assignee=task.assignee.name,
        )


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None = None
    created_at: str | None = None


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    owner_id: int | None = Field(default=None, gt=0)

    @field_validator("name")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    owner_id: int | None = Field(default=None, gt=0)

    @field_validator("name")
    @classmethod
    def name_not_null(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("name must not be empty")
        return value

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    owner_id: int | None = None
    created_at: str | None = None
