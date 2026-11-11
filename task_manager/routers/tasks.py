from typing import Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from ..dependencies import (
    get_current_user,
    get_db,
    get_task_service,
    get_token_user_id,
    get_user_repository,
)
from ..notifier import ConsoleNotifier
from ..orm_models import TaskModel, UserModel
from ..schemas import StatusValue, TaskCreate, TaskResponse, TaskUpdate
from ..task_attachments import (
    UPLOAD_DIR,
    AttachmentResponse,
    find_attachment,
    save_attachment,
)
from ..task_cache import cache_enabled, cached
from ..task_service import TaskService
from ..user_repository import UserRepository

router = APIRouter(prefix="/tasks", tags=["Tasks"])
notifier = ConsoleNotifier()
task_adapter = TypeAdapter(TaskResponse)
task_list_adapter = TypeAdapter(list[TaskResponse])


def schedule_task_cache_invalidation(db: Session, task_id: int) -> None:
    if cache_enabled():
        task = db.get(TaskModel, task_id)
        if task is not None:
            db.info["task_cache_scopes"] = (
                f"task:{task_id}",
                f"project:{task.project_id}",
            )


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    status: StatusValue | None = None,
    limit: int = Query(default=10, gt=0),
    offset: int = Query(default=0, ge=0),
    sort_by: Literal["id", "priority", "created_at"] = "id",
    order: Literal["asc", "desc"] = "asc",
    project_id: int | None = Query(default=None, gt=0),
    user_id: int = Depends(get_token_user_id),
    users: UserRepository = Depends(get_user_repository),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    def load() -> list[TaskResponse]:
        user = get_current_user(user_id, users)
        return [
            TaskResponse.from_task(task_id, task)
            for task_id, task in service.list_api_tasks(
                status,
                limit,
                offset,
                sort_by,
                order,
                user.id,
                project_id,
            )
        ]

    if project_id is None:
        return load()

    variant = f"{user_id}:{status}:{limit}:{offset}:{sort_by}:{order}"
    return cached(
        f"project:{project_id}",
        variant,
        task_list_adapter,
        load,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    user_id: int = Depends(get_token_user_id),
    users: UserRepository = Depends(get_user_repository),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    def load() -> TaskResponse:
        user = get_current_user(user_id, users)
        return TaskResponse.from_task(
            task_id,
            service.get_task(task_id, user.id),
        )

    return cached(
        f"task:{task_id}",
        str(user_id),
        task_adapter,
        load,
    )


@router.post("", status_code=201, response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
    db: Session = Depends(get_db, scope="function"),
) -> TaskResponse:
    task_id, saved = service.create_api_task(
        **task.model_dump(),
        creator_id=current_user.id,
    )
    response = TaskResponse.from_task(task_id, saved)

    if cache_enabled():
        db.info["task_cache_scopes"] = (f"project:{task.project_id}",)

    background_tasks.add_task(
        notifier.send,
        f'Task #{task_id} "{response.title}" được giao cho {response.assignee}.',
    )
    return response


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task: TaskUpdate,
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
    db: Session = Depends(get_db, scope="function"),
) -> TaskResponse:
    changes = task.model_dump(exclude_unset=True)
    previous_assignee = None

    if "assignee" in changes:
        previous_assignee = service.get_task(
            task_id,
            current_user.id,
        ).assignee.name

    saved = service.patch_task(task_id, changes, current_user.id)
    schedule_task_cache_invalidation(db, task_id)
    response = TaskResponse.from_task(task_id, saved)

    if previous_assignee is not None and previous_assignee != response.assignee:
        background_tasks.add_task(
            notifier.send,
            f'Task #{task_id} "{response.title}" được giao lại cho {response.assignee}.',
        )

    return response


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
    db: Session = Depends(get_db, scope="function"),
) -> Response:
    schedule_task_cache_invalidation(db, task_id)
    service.delete_task(task_id, current_user.id)
    return Response(status_code=204)


@router.post(
    "/{task_id}/attachments",
    status_code=201,
    response_model=AttachmentResponse,
)
def upload_attachment(
    task_id: int,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
    db: Session = Depends(get_db, scope="function"),
) -> AttachmentResponse:
    service.get_task(task_id, current_user.id)

    filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    if not filename.strip() or filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="Tên file không hợp lệ")

    return save_attachment(db, task_id, filename, file.file)


@router.get("/{task_id}/attachments/{attachment_id}")
def download_attachment(
    task_id: int,
    attachment_id: int,
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
    db: Session = Depends(get_db, scope="function"),
) -> FileResponse:
    service.get_task(task_id, current_user.id)
    attachment = find_attachment(db, task_id, attachment_id)

    if attachment is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy file đính kèm")

    path = UPLOAD_DIR / attachment.stored_filename
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="File đính kèm không còn trên ổ đĩa",
        )

    return FileResponse(
        path,
        filename=attachment.original_filename,
        media_type="application/octet-stream",
    )