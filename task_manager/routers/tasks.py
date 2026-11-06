from typing import Literal

from fastapi import APIRouter, Depends, Query, Response

from ..dependencies import get_current_user, get_task_service
from ..orm_models import UserModel
from ..schemas import StatusValue, TaskCreate, TaskResponse, TaskUpdate
from ..task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    status: StatusValue | None = None,
    limit: int = Query(default=10, gt=0),
    offset: int = Query(default=0, ge=0),
    sort_by: Literal["id", "priority", "created_at"] = "id",
    order: Literal["asc", "desc"] = "asc",
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    return [
        TaskResponse.from_task(task_id, task)
        for task_id, task in service.list_api_tasks(
            status, limit, offset, sort_by, order, current_user.id
        )
    ]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return TaskResponse.from_task(task_id, service.get_task(task_id, current_user.id))


@router.post("", status_code=201, response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task_id, saved = service.create_api_task(
        **task.model_dump(), creator_id=current_user.id
    )
    return TaskResponse.from_task(task_id, saved)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task: TaskUpdate,
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    saved = service.patch_task(
        task_id, task.model_dump(exclude_unset=True), current_user.id
    )
    return TaskResponse.from_task(task_id, saved)


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> Response:
    service.delete_task(task_id, current_user.id)
    return Response(status_code=204)