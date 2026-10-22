import unittest
from task_manager.models import TaskStatus

from task_manager.exceptions import (
    TaskManagerError,
    TaskNotFoundError,
    InvalidStatusTransitionError,
    PermissionDeniedError,
)


class TestExceptions(unittest.TestCase):

    def test_inheritance(self):
        self.assertTrue(
            issubclass(TaskNotFoundError, TaskManagerError)
        )
        self.assertTrue(
            issubclass(
                InvalidStatusTransitionError,
                TaskManagerError
            )
        )
        self.assertTrue(
            issubclass(PermissionDeniedError, TaskManagerError)
        )

    def test_task_not_found(self):
        error = TaskNotFoundError(99)

        self.assertEqual(error.task_id, 99)
        self.assertEqual(str(error), "Task not found: 99")

        
    def test_invalid_status_transition(self):
        error = InvalidStatusTransitionError(
            TaskStatus.DONE,
            TaskStatus.TODO,
            "Fix login"
        )

        self.assertIsInstance(error, TaskManagerError)
        self.assertEqual(error.current, TaskStatus.DONE)
        self.assertEqual(error.requested, TaskStatus.TODO)
        self.assertEqual(error.task_title, "Fix login")

        self.assertEqual(
            str(error),
            'Task "Fix login": cannot change status from DONE to TODO'
        )

    def test_permission_denied(self):
        error = PermissionDeniedError(
            "Binh",
            "change status",
            "Fix login"
        )

        self.assertIsInstance(error, TaskManagerError)
        self.assertEqual(error.user_name, "Binh")
        self.assertEqual(error.action, "change status")
        self.assertEqual(error.task_title, "Fix login")

        self.assertEqual(
            str(error),
            'User \'Binh\' is not allowed to change status on task "Fix login"'
        )



if __name__ == "__main__":
    unittest.main()