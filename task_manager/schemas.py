from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "TODO"


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None = None
    created_at: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    owner_id: int | None = None
    created_at: str | None = None