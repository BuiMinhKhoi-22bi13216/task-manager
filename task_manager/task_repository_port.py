from __future__ import annotations

import builtins
from typing import Protocol

from task_manager.models import Task


class TaskRepositoryPort(Protocol):
    def add(self, project_name: str, task: Task) -> int: ...

    def get_by_id(self, task_id: int) -> Task | None: ...

    def list(self, project_name: str) -> list[Task]: ...

    def update(self, task_id: int, task: Task) -> None: ...

    def delete(self, task_id: int) -> bool: ...

    def add_to_project(self, project_id: int, task: Task) -> int: ...

    def list_with_ids(
        self,
        status: str | None,
        limit: int,
        offset: int,
        sort_by: str,
        order: str,
    ) -> builtins.list[tuple[int, Task]]: ...
