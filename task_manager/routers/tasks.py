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
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db, get_task_service
from ..notifier import ConsoleNotifier
from ..orm_models import UserModel
from ..schemas import StatusValue, TaskCreate, TaskResponse, TaskUpdate
from ..task_attachments import (
    UPLOAD_DIR,
    AttachmentResponse,
    find_attachment,
    save_attachment,
)
from ..task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])
notifier = ConsoleNotifier()


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
    background_tasks: BackgroundTasks,
    current_user: UserModel = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task_id, saved = service.create_api_task(
        **task.model_dump(), creator_id=current_user.id
    )
    response = TaskResponse.from_task(task_id, saved)
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
) -> TaskResponse:
    changes = task.model_dump(exclude_unset=True)
    previous_assignee = None
    if "assignee" in changes:
        previous_assignee = service.get_task(task_id, current_user.id).assignee.name

    saved = service.patch_task(task_id, changes, current_user.id)
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
) -> Response:
    service.delete_task(task_id, current_user.id)
    return Response(status_code=204)


@router.post(
    "/{task_id}/attachments", status_code=201, response_model=AttachmentResponse
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
        raise HTTPException(status_code=404, detail="File đính kèm không còn trên ổ đĩa")
    return FileResponse(
        path, filename=attachment.original_filename, media_type="application/octet-stream"
    )