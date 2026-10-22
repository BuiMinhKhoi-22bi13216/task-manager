import unittest
from unittest.mock import Mock, patch

from task_manager.builder import TaskBuilder
from task_manager.commands import ChangeStatusCommand, CommandManager
from task_manager.exceptions import TaskLockedError
from task_manager.models import Task, TaskPriority, TaskStatus, User


def make_task(status=TaskStatus.TODO):
    return Task(
        "Test",
        User("An"),
        status,
        TaskPriority.HIGH,
    )


class TestBasicRules(unittest.TestCase):
    def test_constructor_rejects_wrong_status(self):
        with self.assertRaises(TypeError):
            Task(
                "Test",
                User("An"),
                "TODO",
                TaskPriority.HIGH,
            )

    def test_done_blocks_editing(self):
        task = make_task(TaskStatus.DONE)

        for name in Task._LOCKED_FIELDS:
            with self.subTest(field=name):
                with self.assertRaises(TaskLockedError):
                    setattr(task, name, getattr(task, name))

    def test_done_blocks_assignment(self):
        task = make_task(TaskStatus.DONE)

        with self.assertRaises(TaskLockedError):
            task.assign_to(User("Binh"))

    def test_reopen_allows_editing(self):
        task = make_task(TaskStatus.DONE)
        task.reopen()
        task.title = "Edited"

        self.assertEqual(task.title, "Edited")

    def test_builder_cannot_edit_done_task(self):
        builder = TaskBuilder.from_task(make_task(TaskStatus.DONE))

        with self.assertRaises(TaskLockedError):
            builder.set_description("Edited").build()

    def test_invalid_edit_keeps_original_value(self):
        task = make_task()

        with self.assertRaises(TypeError):
            task.priority = "HIGH"

        self.assertEqual(
            task.priority,
            TaskPriority.HIGH,
        )

    def test_undo_completion_reopens_and_notifies_once(self):
        task = make_task(TaskStatus.IN_PROGRESS)
        manager = CommandManager()

        manager.execute(ChangeStatusCommand(task, TaskStatus.DONE))

        observer = Mock()
        task.subscribe(observer)

        with patch.object(
            task,
            "reopen",
            wraps=task.reopen,
        ) as reopen:
            self.assertTrue(manager.undo_last())

        reopen.assert_called_once_with(TaskStatus.IN_PROGRESS)
        self.assertEqual(observer.update.call_count, 1)

    def test_clear_history_before_direct_edit(self):
        task = make_task()
        manager = CommandManager()

        manager.execute(ChangeStatusCommand(task, TaskStatus.IN_PROGRESS))

        manager.clear_history()
        task.complete()
        task.reopen()

        self.assertFalse(manager.undo_last())
        self.assertEqual(manager.history_size, 0)


if __name__ == "__main__":
    unittest.main()
