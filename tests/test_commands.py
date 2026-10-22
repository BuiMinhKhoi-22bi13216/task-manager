import unittest
from unittest.mock import Mock

from task_manager.commands import (
    AssignTaskCommand,
    ChangeStatusCommand,
    CommandManager,
)
from task_manager.models import Task, TaskPriority, TaskStatus, User
from task_manager.exceptions import InvalidStatusTransitionError


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.an = User("An")
        self.khoi = User("Khoi")
        self.task = Task("Learn Docker", self.an, TaskStatus.TODO, TaskPriority.HIGH)
        self.manager = CommandManager()

    def test_status_execute(self):
        self.assertTrue(
            self.manager.execute(ChangeStatusCommand(self.task, TaskStatus.IN_PROGRESS))
        )
        self.assertEqual(self.task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(self.manager.history_size, 1)

    def test_status_undo(self):
        self.manager.execute(ChangeStatusCommand(self.task, TaskStatus.IN_PROGRESS))
        self.assertTrue(self.manager.undo_last())
        self.assertEqual(self.task.status, TaskStatus.TODO)
        self.assertEqual(self.manager.history_size, 0)

    def test_assignment_undo(self):
        self.manager.execute(AssignTaskCommand(self.task, self.khoi))
        self.assertEqual(self.task.assignee, self.khoi)
        self.assertTrue(self.manager.undo_last())
        self.assertEqual(self.task.assignee, self.an)

    def test_last_in_first_out(self):
        self.manager.execute(ChangeStatusCommand(self.task, TaskStatus.IN_PROGRESS))
        self.manager.execute(AssignTaskCommand(self.task, self.khoi))
        self.manager.undo_last()
        self.assertEqual(self.task.assignee, self.an)
        self.assertEqual(self.task.status, TaskStatus.IN_PROGRESS)
        self.manager.undo_last()
        self.assertEqual(self.task.status, TaskStatus.TODO)

    def test_invalid_transition_not_saved(self):
        self.task.change_status(TaskStatus.IN_PROGRESS)
        self.task.change_status(TaskStatus.DONE)

        with self.assertRaises(InvalidStatusTransitionError):
            self.manager.execute(
                ChangeStatusCommand(self.task, TaskStatus.TODO)
        )

        self.assertEqual(self.manager.history_size, 0)
        self.assertFalse(self.manager.undo_last())
        self.assertEqual(self.task.status, TaskStatus.DONE)
    
    def test_noop_not_saved(self):
        self.assertFalse(
            self.manager.execute(ChangeStatusCommand(self.task, TaskStatus.TODO))
        )
        self.assertEqual(self.manager.history_size, 0)

    def test_undo_sends_observer_notification(self):
        observer = Mock()
        self.task.subscribe(observer)
        self.manager.execute(ChangeStatusCommand(self.task, TaskStatus.IN_PROGRESS))
        self.manager.undo_last()
        self.assertEqual(observer.update.call_count, 2)
        undo_msg = observer.update.call_args.args[1]
        self.assertIn("(undo)", undo_msg)
        self.assertIn("IN_PROGRESS -> TODO", undo_msg)

    def test_changed_outside_command_rejects_undo(self):
        self.manager.execute(ChangeStatusCommand(self.task, TaskStatus.IN_PROGRESS))
        self.task.complete()  # DONE is different from the command's expected state.
        with self.assertRaises(RuntimeError):
            self.manager.undo_last()
        self.assertEqual(self.task.status, TaskStatus.DONE)
        self.assertEqual(self.manager.history_size, 1)


if __name__ == "__main__":
    unittest.main()
