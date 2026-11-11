from collections.abc import Iterable
from typing import Any

from task_manager.exceptions import (
    PermissionDeniedError,
    TaskManagerError,
    TaskNotFoundError,
)
from task_manager.models import PRIORITY_RANK, Task, TaskStatus, User
from task_manager.notifier import Notifier
from task_manager.project import Project
from task_manager.strategies import TaskSortStrategy
from task_manager.task_observer import NotifierObserver
from task_manager.task_repository_port import TaskRepositoryPort


class TaskService:
    def __init__(
        self,
        strategy: TaskSortStrategy,
        notifiers: Iterable[Notifier] = (),
        repository: TaskRepositoryPort | None = None,
    ):
        self._strategy = strategy
        self._observers = [NotifierObserver(notifier) for notifier in notifiers]
        self._repository = repository

    def set_strategy(self, strategy: TaskSortStrategy) -> None:
        self._strategy = strategy

    def get_sorted_tasks(self, project: Project) -> list[Task]:
        if self._repository is None:
            tasks = project.tasks
        else:
            tasks = self._repository.list(project.name)

            for task in tasks:
                self.watch_task(task)

        return self._strategy.sort(tasks)

    def watch_task(self, task: Task) -> None:
        for observer in self._observers:
            task.subscribe(observer)

    def watch_project(self, project: Project) -> None:
        for task in project.tasks:
            self.watch_task(task)

    def add_task(self, project: Project, task: Task) -> int:
        if self._repository is None:
            task_id = project.add_task(task)
        else:
            task_id = self._repository.add(project.name, task)

        self.watch_task(task)
        return task_id

    def _get_repository(self) -> TaskRepositoryPort:
        if self._repository is None:
            raise TaskManagerError("Chưa truyền Repository cho TaskService")

        return self._repository

    def _check_task_access(self, task_id: int, user_id: int) -> None:
        participants = self._get_repository().get_participant_ids(task_id)

        if participants is None:
            raise TaskNotFoundError(task_id)

        creator_id, assignee_id = participants

        if user_id != creator_id and user_id != assignee_id:
            raise PermissionDeniedError(str(user_id), "access", f"ID {task_id}")

    def get_task(self, task_id: int, user_id: int | None = None) -> Task:
        if user_id is not None:
            self._check_task_access(task_id, user_id)

        task = self._get_repository().get_by_id(task_id)

        if task is None:
            raise TaskNotFoundError(task_id)

        self.watch_task(task)
        return task

    def update_task(self, task_id: int, task: Task) -> None:
        self._get_repository().update(task_id, task)

    def create_api_task(
        self,
        project_id: int,
        title: str,
        description: str,
        status: str,
        priority: int,
        task_type: str,
        assignee: str,
        creator_id: int | None = None,
    ) -> tuple[int, Task]:
        priorities = {rank: value for value, rank in PRIORITY_RANK.items()}

        task = Task(
            title=title,
            description=description,
            status=TaskStatus(status),
            priority=priorities[priority],
            task_type=task_type,
            assignee=User(assignee),
        )

        task_id = self._get_repository().add_to_project(project_id, task, creator_id)

        self.watch_task(task)
        return task_id, task

    def list_api_tasks(
        self,
        status: str | None,
        limit: int,
        offset: int,
        sort_by: str,
        order: str,
        user_id: int | None = None,
        project_id: int | None = None,
    ) -> list[tuple[int, Task]]:
        return self._get_repository().list_with_ids(
            status,
            limit,
            offset,
            sort_by,
            order,
            user_id,
            project_id,
        )

    def patch_task(
        self, task_id: int, changes: dict[str, Any], user_id: int | None = None
    ) -> Task:
        task = self.get_task(task_id, user_id)

        # Validate status before editing other fields. No automatic reopen.
        if "status" in changes:
            task.change_status(TaskStatus(changes["status"]))

        for field in ("title", "description", "task_type"):
            if field in changes:
                setattr(task, field, changes[field])

        if "priority" in changes:
            priorities = {rank: value for value, rank in PRIORITY_RANK.items()}
            task.priority = priorities[changes["priority"]]

        if "assignee" in changes:
            task.assign_to(User(changes["assignee"]))

        self.update_task(task_id, task)
        return task

    def delete_task(self, task_id: int, user_id: int | None = None) -> None:
        if user_id is not None:
            self._check_task_access(task_id, user_id)

        if not self._get_repository().delete(task_id):
            raise TaskNotFoundError(task_id)