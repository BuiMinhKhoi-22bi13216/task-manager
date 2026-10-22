from collections.abc import Iterable

from task_manager.models import Task
from task_manager.notifier import Notifier
from task_manager.project import Project
from task_manager.strategies import TaskSortStrategy
from task_manager.task_observer import NotifierObserver


class TaskService:
    def __init__(
        self,
        strategy: TaskSortStrategy,
        notifiers: Iterable[Notifier] = (),
    ):
        self._strategy = strategy
        self._observers = [NotifierObserver(notifier) for notifier in notifiers]

    def set_strategy(self, strategy: TaskSortStrategy) -> None:
        self._strategy = strategy

    def get_sorted_tasks(self, project: Project) -> list[Task]:
        return self._strategy.sort(project.tasks)

    def watch_task(self, task: Task) -> None:
        for observer in self._observers:
            task.subscribe(observer)

    def watch_project(self, project: Project) -> None:
        for task in project.tasks:
            self.watch_task(task)

    def add_task(self, project: Project, task: Task) -> None:
        project.add_task(task)
        self.watch_task(task)
