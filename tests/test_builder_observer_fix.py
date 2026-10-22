import unittest
from datetime import datetime

from task_manager.builder import TaskBuilder
from task_manager.models import Task, TaskPriority, TaskStatus, User


class TestReviewFixes(unittest.TestCase):
    def make_task(self):
        return Task(
            title="Test task",
            assignee=User("Intern"),
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
        )

    def test_builder_preserves_created_at(self):
        original = self.make_task()
        original.created_at = datetime(2020, 1, 1, 8, 30)
        rebuilt = TaskBuilder.from_task(original).build()
        self.assertEqual(rebuilt.created_at, original.created_at)
        self.assertIsNot(rebuilt, original)

    def test_one_failed_observer_does_not_block_later_observers(self):
        task = self.make_task()
        received = []

        class BrokenObserver:
            def update(self, task, message):
                raise RuntimeError("Simulated notifier error")

        class WorkingObserver:
            def update(self, task, message):
                received.append(message)

        task.subscribe(BrokenObserver())
        task.subscribe(WorkingObserver())
        with self.assertLogs(level="ERROR") as logs:
            task.change_status(TaskStatus.IN_PROGRESS)
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(len(received), 1)
        self.assertIn("status: TODO -> IN_PROGRESS", received[0])
        self.assertTrue(any("Simulated notifier error" in x for x in logs.output))


if __name__ == "__main__":
    unittest.main()
