from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(Text, unique=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    full_name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(
        Text,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[str | None] = mapped_column(
        Text,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    owner: Mapped[UserModel | None] = relationship()
    tasks: Mapped[list[TaskModel]] = relationship(
        back_populates="project"
    )


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Text,
        server_default=text("'TODO'"),
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        server_default=text("2"),
    )
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    due_date: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(
        Text,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[str | None] = mapped_column(Text)

    project: Mapped[ProjectModel | None] = relationship(
        back_populates="tasks"
    )
    creator: Mapped[UserModel | None] = relationship(
        foreign_keys=[creator_id]
    )
    assignee: Mapped[UserModel] = relationship(
        foreign_keys=[assignee_id]
    )
