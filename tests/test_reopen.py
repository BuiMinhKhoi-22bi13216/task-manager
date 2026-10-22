import unittest

from task_manager.exceptions import InvalidStatusTransitionError
from task_manager.models import (
    Task,
    TaskPriority,
    TaskStatus,
    User,
)


class SpyObserver:
    def __init__(self):
        self.messages = []

    def update(self, task, message):
        self.messages.append(message)


class TestReopen(unittest.TestCase):
    def setUp(self):
        self.task = Task(
            title="Learn Python",
            assignee=User("An"),
            status=TaskStatus.DONE,
            priority=TaskPriority.HIGH,
        )

    def test_reopen_to_in_progress(self):
        self.task.reopen()

        self.assertEqual(self.task.status, TaskStatus.IN_PROGRESS)

    def test_reopen_to_todo(self):
        self.task.reopen(TaskStatus.TODO)

        self.assertEqual(self.task.status, TaskStatus.TODO)

    def test_reopen_when_not_done(self):
        for status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS):
            with self.subTest(status=status):
                task = Task(
                    title="Test",
                    assignee=User("An"),
                    status=status,
                    priority=TaskPriority.HIGH,
                )

                with self.assertRaises(InvalidStatusTransitionError):
                    task.reopen()

                self.assertEqual(task.status, status)

    def test_reopen_to_done_is_invalid(self):
        with self.assertRaises(InvalidStatusTransitionError):
            self.task.reopen(TaskStatus.DONE)

        self.assertEqual(self.task.status, TaskStatus.DONE)

    def test_reopen_invalid_type(self):
        with self.assertRaises(TypeError):
            self.task.reopen("TODO")

        self.assertEqual(self.task.status, TaskStatus.DONE)

    def test_reopen_notifies_observer(self):
        observer = SpyObserver()
        self.task.subscribe(observer)

        self.task.reopen(TaskStatus.IN_PROGRESS)

        self.assertEqual(len(observer.messages), 1)
        self.assertEqual(observer.messages[0], "reopened: DONE -> IN_PROGRESS")

    def test_invalid_reopen_does_not_notify(self):
        observer = SpyObserver()
        self.task.subscribe(observer)

        with self.assertRaises(InvalidStatusTransitionError):
            self.task.reopen(TaskStatus.DONE)

        self.assertEqual(observer.messages, [])
        self.assertEqual(self.task.status, TaskStatus.DONE)


if __name__ == "__main__":
    unittest.main()
