from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from task_manager.notifier import Notifier

if TYPE_CHECKING:
    from task_manager.models import Task


class TaskObserver(ABC):
    @abstractmethod
    def update(self, task: "Task", message: str) -> None:
        pass


class NotifierObserver(TaskObserver):
    def __init__(self, notifier: Notifier):
        self._notifier = notifier

    def update(self, task: "Task", message: str) -> None:
        self._notifier.send(f'Task "{task.title}" {message}')
