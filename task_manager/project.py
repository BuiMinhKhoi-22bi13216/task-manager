from .decorator import log_execution_time
from .models import Task


class Project:
    def __init__(self, name):
        self.name = name
        self.tasks = []

    @log_execution_time
    def add_task(self, task: Task) -> None:
        if not isinstance(task, Task):
            raise TypeError("task must be Task")
        self.tasks.append(task)
