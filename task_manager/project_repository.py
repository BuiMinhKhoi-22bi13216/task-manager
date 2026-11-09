import builtins
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .exceptions import InvalidDataError, ProjectNotFoundError
from .orm_models import ProjectModel, TaskModel, UserModel


class ProjectRepository:
    def __init__(self, session: Session):
        self._session = session

    def _row(self, project_id: int) -> ProjectModel:
        row = self._session.get(ProjectModel, project_id)

        if row is None:
            raise ProjectNotFoundError(project_id)

        return row

    def _data(self, row: ProjectModel) -> dict[str, Any]:
        return {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "owner_id": row.owner_id,
            "created_at": row.created_at,
        }

    def _check_owner(self, owner_id: int | None) -> None:
        if owner_id is not None and self._session.get(UserModel, owner_id) is None:
            raise InvalidDataError(f"User not found: {owner_id}")

    def get(self, project_id: int) -> dict[str, Any]:
        return self._data(self._row(project_id))

    def list(self) -> list[dict[str, Any]]:
        rows = self._session.scalars(select(ProjectModel).order_by(ProjectModel.id))
        return [self._data(row) for row in rows]

    def add(
        self,
        name: str,
        description: str | None,
        owner_id: int | None,
    ) -> dict[str, Any]:
        self._check_owner(owner_id)

        row = ProjectModel(
            name=name,
            description=description,
            owner_id=owner_id,
        )
        self._session.add(row)
        self._session.flush()

        return self._data(row)

    def update(self, project_id: int, changes: dict[str, Any]) -> dict[str, Any]:
        row = self._row(project_id)

        if "owner_id" in changes:
            self._check_owner(changes["owner_id"])

        for field in ("name", "description", "owner_id"):
            if field in changes:
                setattr(row, field, changes[field])

        self._session.flush()
        return self._data(row)

    def list_task_participants(
        self, project_id: int
    ) -> builtins.list[tuple[int | None, int]]:
        self._row(project_id)

        statement = select(TaskModel.creator_id, TaskModel.assignee_id).where(
            TaskModel.project_id == project_id
        )
        rows = self._session.execute(statement).all()

        return [(row.creator_id, row.assignee_id) for row in rows]

    def delete(self, project_id: int) -> None:
        self._row(project_id)

        # Database handles ON DELETE CASCADE; avoid ORM setting task FKs to NULL.
        self._session.execute(
            delete(ProjectModel).where(ProjectModel.id == project_id)
        )
        self._session.flush()