from .decorator import log_execution_time
from .models import Task
from .task_storage import TaskStorage


class Project:
    def __init__(self, name: str) -> None:
        self.name = name
        self._storage = TaskStorage()
        self._next_id = 1

    @property
    def tasks(self) -> list[Task]:
        return self._storage.all_tasks()

    @log_execution_time
    def add_task(self, task: Task) -> int:
        task_id = self._next_id
        self._storage.add_task(task_id, task)
        self._next_id += 1
        return task_id

    def get_task(self, task_id: int) -> Task:
        return self._storage.get_task(task_id)

    def find_task(self, task_id: int) -> Task | None:
        return self._storage.find_task(task_id)

    def remove_task(self, task_id: int) -> Task:
        return self._storage.remove_task(task_id)