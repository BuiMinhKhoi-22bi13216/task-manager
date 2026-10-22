from abc import ABC, abstractmethod
from datetime import date

from task_manager.models import PRIORITY_RANK, Task


# Strategy Interface
class TaskSortStrategy(ABC):
    @abstractmethod
    def sort(self, tasks: list[Task]) -> list[Task]:
        pass


# Concrete Strategy
class PrioritySortStrategy(TaskSortStrategy):
    def sort(self, tasks: list[Task]) -> list[Task]:

        return sorted(
            tasks, key=lambda task: PRIORITY_RANK[task.priority], reverse=True
        )


class DeadlineSortStrategy(TaskSortStrategy):
    def sort(self, tasks: list[Task]) -> list[Task]:
        return sorted(
            tasks, key=lambda task: (task.deadline is None, task.deadline or date.max)
        )


class CreatedAtSortStrategy(TaskSortStrategy):
    def sort(self, tasks: list[Task]) -> list[Task]:
        return sorted(tasks, key=lambda task: task.created_at, reverse=True)
