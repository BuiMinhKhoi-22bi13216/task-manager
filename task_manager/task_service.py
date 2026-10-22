from collections.abc import Iterable

from task_manager.project import Project
from task_manager.models import Task
from task_manager.strategies import TaskSortStrategy
from task_manager.notifier import Notifier
from task_manager.task_observer import NotifierObserver, TaskObserver


class TaskService:

    def __init__(
        self,
        strategy: TaskSortStrategy,
        notifiers: Iterable[Notifier] = (),
        *,
        observers: Iterable[TaskObserver] = (),
    ):
        self._strategy = strategy
        self._observers = list(observers) + [
            NotifierObserver(item)
            for item in notifiers
        ]

    def set_strategy(self, strategy: TaskSortStrategy):
        self._strategy = strategy

    def get_sorted_tasks(self, project: Project) -> list[Task]:
        return self._strategy.sort(project.tasks)

    def watch_task(self, task: Task) -> None:
        for observer in self._observers:
            task.subscribe(observer)

    def watch_project(self, project: Project) -> None:
        """Subscribe existing tasks; use add_task() for later additions."""
        for task in project.tasks:
            self.watch_task(task)

    def add_task(self, project: Project, task: Task) -> None:
        """Add and watch a new task through one service operation."""
        project.add_task(task)
        self.watch_task(task)
