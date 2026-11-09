import builtins
from typing import Any, Protocol

from .exceptions import PermissionDeniedError


class ProjectRepositoryPort(Protocol):
    def get(self, project_id: int) -> dict[str, Any]: ...

    def list(self) -> list[dict[str, Any]]: ...

    def add(
        self,
        name: str,
        description: str | None,
        owner_id: int | None,
    ) -> dict[str, Any]: ...

    def update(self, project_id: int, changes: dict[str, Any]) -> dict[str, Any]: ...

    def list_task_participants(
        self, project_id: int
    ) -> builtins.list[tuple[int | None, int]]: ...

    def delete(self, project_id: int) -> None: ...


class ProjectService:
    def __init__(self, repository: ProjectRepositoryPort):
        self._repository = repository

    def get_project(self, project_id: int) -> dict[str, Any]:
        return self._repository.get(project_id)

    def list_projects(self) -> list[dict[str, Any]]:
        return self._repository.list()

    def create_project(
        self,
        name: str,
        description: str | None,
        owner_id: int | None,
    ) -> dict[str, Any]:
        return self._repository.add(name, description, owner_id)

    def update_project(
        self, project_id: int, changes: dict[str, Any]
    ) -> dict[str, Any]:
        return self._repository.update(project_id, changes)

    def delete_project(
        self, project_id: int, user_id: int, user_name: str
    ) -> None:
        participants = self._repository.list_task_participants(project_id)

        for creator_id, assignee_id in participants:
            if user_id != creator_id and user_id != assignee_id:
                raise PermissionDeniedError(user_name, "delete this project")

        self._repository.delete(project_id)