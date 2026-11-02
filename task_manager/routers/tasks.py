from fastapi import APIRouter

from .. import api_task_service
from ..schemas import TaskCreate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=list[TaskResponse])
def list_tasks(status: str | None = None) -> list[dict[str, int | str]]:
    return api_task_service.list_tasks(status)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int) -> dict[str, int | str]:
    return api_task_service.get_task(task_id)


@router.post("", status_code=201, response_model=TaskResponse)
def create_task(task: TaskCreate) -> dict[str, int | str]:
    return api_task_service.create_task(
        title=task.title,
        description=task.description,
        status=task.status,
    )