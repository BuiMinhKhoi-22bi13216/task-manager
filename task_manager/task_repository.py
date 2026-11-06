from __future__ import annotations

import builtins
from datetime import date, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from task_manager.exceptions import (
    InvalidTaskTypeError,
    ProjectNotFoundError,
    TaskManagerError,
    TaskNotFoundError,
)
from task_manager.models import PRIORITY_RANK, Task, TaskStatus, User
from task_manager.orm_models import ProjectModel, TaskModel, UserModel


class TaskRepository:
    def __init__(self, session: Session):
        self._session = session

    def _copy_to_model(self, task: Task, row: TaskModel) -> None:
        if task.task_type not in {"bug", "feature", "chore"}:
            raise InvalidTaskTypeError(
                f"Schema SQLite chưa hỗ trợ task_type={task.task_type!r}"
            )

        user = self._session.scalar(
            select(UserModel).where(UserModel.username == task.assignee.name)
        )

        if user is None:
            raise TaskManagerError(f"Không có username: {task.assignee.name!r}")

        row.title = task.title
        row.description = task.description
        row.task_type = task.task_type
        row.status = task.status.value
        row.priority = PRIORITY_RANK[task.priority]
        row.assignee = user
        row.due_date = task.deadline.isoformat() if task.deadline else None
        row.created_at = task.created_at.isoformat(sep=" ")

    def _to_domain(self, row: TaskModel) -> Task:
        priorities = {rank: priority for priority, rank in PRIORITY_RANK.items()}

        if row.priority not in priorities:
            raise TaskManagerError(
                f"Task {row.id}: priority={row.priority} chưa có trong domain"
            )

        if row.assignee is None or row.created_at is None:
            raise TaskManagerError(f"Task {row.id}: thiếu assignee hoặc created_at")

        return Task(
            title=row.title,
            description=row.description or "",
            task_type=row.task_type,
            status=TaskStatus(row.status),
            priority=priorities[row.priority],
            assignee=User(row.assignee.username),
            deadline=(date.fromisoformat(row.due_date) if row.due_date else None),
            created_at=datetime.fromisoformat(row.created_at),
        )

    def add(self, project_name: str, task: Task) -> int:
        projects = self._session.scalars(
            select(ProjectModel).where(ProjectModel.name == project_name)
        ).all()

        if len(projects) != 1:
            raise TaskManagerError(
                f"Cần đúng một project tên {project_name!r}; tìm thấy {len(projects)}"
            )

        row = TaskModel(project_id=projects[0].id)
        self._copy_to_model(task, row)

        self._session.add(row)
        self._session.flush()

        return row.id

    def get_by_id(self, task_id: int) -> Task | None:
        row = self._session.get(TaskModel, task_id)

        if row is None:
            return None

        return self._to_domain(row)

    def list(self, project_name: str) -> list[Task]:
        statement = (
            select(TaskModel)
            .options(selectinload(TaskModel.assignee))
            .join(TaskModel.project)
            .where(ProjectModel.name == project_name)
            .order_by(TaskModel.id)
        )

        rows = self._session.scalars(statement).all()
        return [self._to_domain(row) for row in rows]

    def update(self, task_id: int, task: Task) -> None:
        row = self._session.get(TaskModel, task_id)

        if row is None:
            raise TaskNotFoundError(task_id)

        self._copy_to_model(task, row)
        row.updated_at = datetime.now().isoformat(sep=" ")

        self._session.flush()

    def delete(self, task_id: int) -> bool:
        row = self._session.get(TaskModel, task_id)

        if row is None:
            return False

        self._session.delete(row)
        self._session.flush()

        return True

    def add_to_project(
        self, project_id: int, task: Task, creator_id: int | None = None
    ) -> int:
        if self._session.get(ProjectModel, project_id) is None:
            raise ProjectNotFoundError(project_id)

        row = TaskModel(project_id=project_id, creator_id=creator_id)
        self._copy_to_model(task, row)

        self._session.add(row)
        self._session.flush()

        return row.id

    def list_with_ids(
        self,
        status: str | None,
        limit: int,
        offset: int,
        sort_by: str,
        order: str,
        user_id: int | None = None,
    ) -> builtins.list[tuple[int, Task]]:
        columns = {
            "id": TaskModel.id,
            "priority": TaskModel.priority,
            "created_at": TaskModel.created_at,
        }
        column = columns[sort_by]

        statement = select(TaskModel).options(selectinload(TaskModel.assignee))

        if user_id is not None:
            statement = statement.where(
                or_(TaskModel.creator_id == user_id, TaskModel.assignee_id == user_id)
            )

        if status is not None:
            statement = statement.where(TaskModel.status == status)

        ordering = column.desc() if order == "desc" else column.asc()
        statement = statement.order_by(ordering, TaskModel.id.asc())

        rows = self._session.scalars(statement.offset(offset).limit(limit)).all()

        return [(row.id, self._to_domain(row)) for row in rows]

    def get_participant_ids(self, task_id: int) -> tuple[int | None, int] | None:
        row = self._session.get(TaskModel, task_id)

        if row is None:
            return None

        return row.creator_id, row.assignee_id