from .exceptions import DuplicateTaskError, TaskNotFoundError
from .models import Task


class TaskStorage:
    def __init__(self) -> None:
        self._tasks_by_id: dict[int, Task] = {}

    @staticmethod
    def _validate_id(task_id: int) -> None:
        if type(task_id) is not int:
            raise TypeError("task_id must be int")

    def add_task(self, task_id: int, task: Task) -> None:
        self._validate_id(task_id)

        if not isinstance(task, Task):
            raise TypeError("task must be Task")

        if task_id in self._tasks_by_id:
            raise DuplicateTaskError(f"Duplicate task ID: {task_id}")

        self._tasks_by_id[task_id] = task

    def get_task(self, task_id: int) -> Task:
        self._validate_id(task_id)

        try:
            return self._tasks_by_id[task_id]
        except KeyError:
            raise TaskNotFoundError(task_id) from None

    def find_task(self, task_id: int) -> Task | None:
        self._validate_id(task_id)
        return self._tasks_by_id.get(task_id)

    def remove_task(self, task_id: int) -> Task:
        self._validate_id(task_id)

        try:
            return self._tasks_by_id.pop(task_id)
        except KeyError:
            raise TaskNotFoundError(task_id) from None

    def all_tasks(self) -> list[Task]:
        return list(self._tasks_by_id.values())

    def __len__(self) -> int:
        return len(self._tasks_by_id)