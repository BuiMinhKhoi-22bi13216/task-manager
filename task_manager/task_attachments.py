from shutil import copyfileobj
from typing import BinaryIO
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from .config import PROJECT_ROOT
from .database import engine, settings
from .orm_models import Base

UPLOAD_DIR = PROJECT_ROOT / settings.upload_dir


class TaskAttachmentModel(Base):
    __tablename__ = "task_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    original_filename: Mapped[str] = mapped_column(Text)
    stored_filename: Mapped[str] = mapped_column(Text, unique=True)


class AttachmentResponse(BaseModel):
    id: int
    task_id: int
    filename: str


def save_attachment(
    db: Session, task_id: int, filename: str, source: BinaryIO
) -> AttachmentResponse:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_filename = uuid4().hex
    path = UPLOAD_DIR / stored_filename

    with path.open("xb") as target:
        db.info.setdefault("pending_uploads", []).append(path)
        copyfileobj(source, target)

    attachment = TaskAttachmentModel(
        task_id=task_id,
        original_filename=filename,
        stored_filename=stored_filename,
    )
    db.add(attachment)
    db.flush()
    return AttachmentResponse(id=attachment.id, task_id=task_id, filename=filename)


def find_attachment(
    db: Session, task_id: int, attachment_id: int
) -> TaskAttachmentModel | None:
    attachment = db.get(TaskAttachmentModel, attachment_id)
    if attachment is None or attachment.task_id != task_id:
        return None
    return attachment


if __name__ == "__main__":
    Base.metadata.tables["task_attachments"].create(engine, checkfirst=True)
    print("Bảng task_attachments đã sẵn sàng.")