import unittest

from task_manager.exceptions import (
    DuplicateTaskError,
    InvalidTaskTypeError,
    TaskLockedError,
    TaskNotFoundError,
)
from task_manager.models import Task, TaskPriority, TaskStatus, User
from task_manager.project import Project
from task_manager.task_factory import TaskFactory
from task_manager.task_storage import TaskStorage


def make_task():
    return Task("Test", User("An"), TaskStatus.TODO, TaskPriority.HIGH)


class TestStorageProject(unittest.TestCase):
    def test_storage_lookup_and_missing(self):
        storage = TaskStorage()
        task = make_task()
        storage.add_task(1, task)

        self.assertIs(storage.get_task(1), task)
        self.assertIsNone(storage.find_task(2))

        with self.assertRaises(TaskNotFoundError):
            storage.get_task(2)

    def test_duplicate_preserves_original(self):
        storage = TaskStorage()
        task = make_task()
        storage.add_task(1, task)

        with self.assertRaises(DuplicateTaskError):
            storage.add_task(1, make_task())

        self.assertIs(storage.get_task(1), task)

    def test_invalid_ids_rejected_by_all_operations(self):
        storage = TaskStorage()

        for task_id in (True, None, "1"):
            for action in (storage.get_task, storage.find_task, storage.remove_task):
                with self.subTest(task_id=task_id, action=action.__name__):
                    with self.assertRaises(TypeError):
                        action(task_id)

            with self.assertRaises(TypeError):
                storage.add_task(task_id, make_task())

        self.assertEqual(len(storage), 0)

    def test_invalid_task_rejected(self):
        storage = TaskStorage()

        with self.assertRaises(TypeError):
            storage.add_task(1, None)

        self.assertEqual(len(storage), 0)

    def test_remove_and_list_copy(self):
        storage = TaskStorage()
        task = make_task()
        storage.add_task(1, task)

        storage.all_tasks().clear()

        self.assertEqual(len(storage), 1)
        self.assertIs(storage.remove_task(1), task)

        with self.assertRaises(TaskNotFoundError):
            storage.remove_task(1)

    def test_project_ids_and_list_copy(self):
        project = Project("Demo")
        task = make_task()
        first_id = project.add_task(task)

        self.assertIs(project.get_task(first_id), task)

        project.tasks.clear()

        self.assertEqual(len(project.tasks), 1)

        project.remove_task(first_id)

        self.assertIsNone(project.find_task(first_id))
        self.assertGreater(project.add_task(make_task()), first_id)

    def test_failed_add_does_not_consume_id(self):
        project = Project("Demo")

        with self.assertRaises(TypeError):
            project.add_task(None)

        self.assertEqual(project.add_task(make_task()), 1)

    def test_invalid_factory_type(self):
        with self.assertRaises(InvalidTaskTypeError):
            TaskFactory.create_task("unknown", "Test", User("An"))

    def test_done_same_assignee_requires_reopen(self):
        task = make_task()
        task.change_status(TaskStatus.IN_PROGRESS)
        task.complete()

        with self.assertRaises(TaskLockedError):
            task.assign_to(task.assignee)

        task.reopen()
        task.assign_to(task.assignee)


if __name__ == "__main__":
    unittest.main()