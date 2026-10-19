import unittest
from datetime import date, datetime

from task_manager.models import (
    User, Task, TaskStatus, TaskPriority
)
from task_manager.project import Project
from task_manager.task_service import TaskService
from task_manager.strategies import (
    PrioritySortStrategy,
    DeadlineSortStrategy,
    CreatedAtSortStrategy
)


class TestStrategies(unittest.TestCase):

    def setUp(self):
        user = User("Khoi")
        self.project = Project("AI Camera")

        self.task1 = Task(
            "Learn Python", user,
            TaskStatus.TODO, TaskPriority.HIGH
        )

        self.task2 = Task(
            "Learn Docker", user,
            TaskStatus.TODO, TaskPriority.MEDIUM
        )

        self.task3 = Task(
            "Learn Git", user,
            TaskStatus.TODO, TaskPriority.LOW
        )

        self.task1.deadline = date(2026, 10, 25)
        self.task2.deadline = date(2026, 10, 20)
        # Task 3 khong co deadline

        self.task1.created_at = datetime(2026, 10, 15, 8)
        self.task2.created_at = datetime(2026, 10, 15, 9)
        self.task3.created_at = datetime(2026, 10, 15, 7)

        for task in [self.task1, self.task2, self.task3]:
            self.project.add_task(task)

    def test_priority_sort(self):
        service = TaskService(PrioritySortStrategy())
        result = service.get_sorted_tasks(self.project)

        self.assertEqual(
            [t.title for t in result],
            ["Learn Python", "Learn Docker", "Learn Git"]
        )

    def test_deadline_sort(self):
        service = TaskService(DeadlineSortStrategy())
        result = service.get_sorted_tasks(self.project)

        self.assertEqual(
            [t.title for t in result],
            ["Learn Docker", "Learn Python", "Learn Git"]
        )

    def test_created_at_sort(self):
        service = TaskService(CreatedAtSortStrategy())
        result = service.get_sorted_tasks(self.project)

        self.assertEqual(
            [t.title for t in result],
            ["Learn Docker", "Learn Python", "Learn Git"]
        )

    def test_switch_strategy(self):
        service = TaskService(PrioritySortStrategy())

        priority_result = service.get_sorted_tasks(self.project)
        self.assertIs(priority_result[0], self.task1)

        service.set_strategy(DeadlineSortStrategy())

        deadline_result = service.get_sorted_tasks(self.project)
        self.assertIs(deadline_result[0], self.task2)

    def test_original_order_unchanged(self):
        service = TaskService(DeadlineSortStrategy())
        original = list(self.project.tasks)

        service.get_sorted_tasks(self.project)

        self.assertEqual(self.project.tasks, original)


if __name__ == "__main__":
    unittest.main()
