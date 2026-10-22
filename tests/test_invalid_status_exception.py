import unittest

from task_manager.exceptions import InvalidStatusTransitionError
from task_manager.models import Task, TaskPriority, TaskStatus, User


class TestInvalidStatusException(unittest.TestCase):
    def test_done_cannot_return_to_todo(self):
        task = Task(
            title="Fix login",
            assignee=User("An"),
            status=TaskStatus.DONE,
            priority=TaskPriority.HIGH,
        )

        with self.assertRaises(InvalidStatusTransitionError) as context:
            task.change_status(TaskStatus.TODO)

        error = context.exception

        self.assertEqual(error.current, TaskStatus.DONE)
        self.assertEqual(error.requested, TaskStatus.TODO)
        self.assertEqual(task.status, TaskStatus.DONE)

    def test_in_progress_cannot_return_to_todo(self):
        task = Task(
            title="Write API",
            assignee=User("An"),
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
        )

        with self.assertRaises(InvalidStatusTransitionError):
            task.change_status(TaskStatus.TODO)

        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)

    def test_todo_cannot_go_directly_to_done(self):
        task = Task(
            title="Learn Python",
            assignee=User("An"),
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
        )

        with self.assertRaises(InvalidStatusTransitionError):
            task.change_status(TaskStatus.DONE)

        self.assertEqual(task.status, TaskStatus.TODO)


if __name__ == "__main__":
    unittest.main()
