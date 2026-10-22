"""Behavioral regressions found while reviewing the supplied project."""
import contextlib
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone
import io
import random
import unittest
from unittest.mock import patch

from task_manager.builder import TaskBuilder
from task_manager.commands import AssignTaskCommand, ChangeStatusCommand, CommandManager
from task_manager.decorator import NotifierDecorator, PrefixNotifier
from task_manager.exceptions import CommandStateError, TaskLockedError, TaskManagerError, UndoConflictError
from task_manager.models import Task, TaskPriority as P, TaskStatus as S, User
from task_manager.notifier import Notifier
from task_manager.project import Project
from task_manager.strategies import PrioritySortStrategy
from task_manager.task_factory import TaskFactory
from task_manager.task_observer import NotifierObserver
from task_manager.task_service import TaskService


def make_task(status=S.TODO):
    return Task("Audit", User("An"), status, P.HIGH)


class SpyNotifier(Notifier):
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)


class TestDomainIntegrity(unittest.TestCase):
    def test_constructor_rejects_invalid_business_fields(self):
        invalid = {
            "title": (" ", ValueError), "assignee": ("An", TypeError),
            "status": ("TODO", TypeError), "priority": ("HIGH", TypeError),
            "task_type": ("", ValueError), "description": (None, TypeError),
            "deadline": ("2026-10-22", TypeError), "created_at": (None, TypeError),
        }
        for name, (value, error_type) in invalid.items():
            with self.subTest(field=name):
                args = dict(title="Valid", assignee=User("An"), status=S.TODO, priority=P.HIGH)
                args[name] = value
                with self.assertRaises(error_type):
                    Task(**args)

    def test_invalid_edit_keeps_old_value_revision_and_events(self):
        invalid = {"title": "", "assignee": "An", "priority": "HIGH",
                   "description": None, "deadline": "soon", "created_at": None}
        for name, value in invalid.items():
            with self.subTest(field=name):
                task = make_task()
                spy = SpyNotifier()
                task.subscribe(NotifierObserver(spy))
                original = getattr(task, name)
                with self.assertRaises((TypeError, ValueError)):
                    setattr(task, name, value)
                self.assertEqual(getattr(task, name), original)
                self.assertEqual(task.revision, 0)
                self.assertEqual(spy.messages, [])

    def test_invalid_transition_keeps_state_revision_and_events(self):
        task = make_task()
        spy = SpyNotifier()
        task.subscribe(NotifierObserver(spy))
        with self.assertRaises(TaskManagerError):
            task.complete()
        self.assertEqual(task.status, S.TODO)
        self.assertEqual(task.revision, 0)
        self.assertEqual(spy.messages, [])

    def test_legacy_bad_status_is_checked_before_mutation(self):
        task = make_task()
        object.__setattr__(task, "status", "TODO")  # Simulate corrupt legacy data.
        with self.assertRaises(TypeError):
            task.change_status(S.DONE)
        self.assertEqual(task.status, "TODO")
        self.assertEqual(task.revision, 0)

    def test_done_blocks_assignment_and_deletion_of_business_fields(self):
        task = make_task(S.DONE)
        for name in Task._LOCKED_FIELDS:
            with self.subTest(field=name):
                original = getattr(task, name)
                with self.assertRaises(TaskLockedError):
                    setattr(task, name, original)
                with self.assertRaises(TaskLockedError):
                    delattr(task, name)
                self.assertEqual(getattr(task, name), original)

    def test_status_cannot_be_assigned_or_deleted(self):
        task = make_task()
        with self.assertRaises(AttributeError):
            task.status = S.DONE
        with self.assertRaises(AttributeError):
            del task.status

    def test_nested_user_cannot_mutate_locked_task(self):
        task = make_task(S.DONE)
        with self.assertRaises(FrozenInstanceError):
            task.assignee.name = "Changed"
        self.assertEqual(task.assignee.name, "An")

    def test_direct_assignee_assignment_notifies_once(self):
        task = make_task()
        spy = SpyNotifier()
        task.subscribe(NotifierObserver(spy))
        task.assignee = User("Binh")
        self.assertEqual(len(spy.messages), 1)
        self.assertIn("An -> Binh", spy.messages[0])
        task.assignee = User("Binh")
        self.assertEqual(len(spy.messages), 1)

    def test_reopen_allows_edits(self):
        task = make_task(S.DONE)
        task.reopen()
        task.title = "Edited"
        task.deadline = date(2026, 11, 1)
        task.assign_to(User("Binh"))
        self.assertEqual(task.title, "Edited")
        self.assertEqual(task.assignee.name, "Binh")

    def test_date_types_cannot_make_sorting_inconsistent(self):
        task = make_task()
        with self.assertRaises(TypeError):
            task.deadline = datetime(2026, 11, 1)
        with self.assertRaises(ValueError):
            task.created_at = datetime.now(timezone.utc)

    def test_user_rejects_empty_and_non_string_names(self):
        for name, error_type in [(" ", ValueError), (42, TypeError)]:
            with self.subTest(name=name), self.assertRaises(error_type):
                User(name)


class TestUndoIntegrity(unittest.TestCase):
    def setUp(self):
        self.task = make_task()
        self.manager = CommandManager()

    def test_status_cycle_outside_command_blocks_stale_undo(self):
        self.manager.execute(ChangeStatusCommand(self.task, S.IN_PROGRESS))
        self.task.complete()
        self.task.reopen()
        with self.assertRaises(UndoConflictError):
            self.manager.undo_last()
        self.assertEqual(self.task.status, S.IN_PROGRESS)
        self.assertEqual(self.manager.history_size, 1)

    def test_assignment_cycle_outside_command_blocks_stale_undo(self):
        self.manager.execute(AssignTaskCommand(self.task, User("Binh")))
        self.task.assign_to(User("Cuong"))
        self.task.assign_to(User("Binh"))
        with self.assertRaises(UndoConflictError):
            self.manager.undo_last()
        self.assertEqual(self.task.assignee.name, "Binh")
        self.assertEqual(self.manager.history_size, 1)

    def test_direct_edit_also_invalidates_history(self):
        self.manager.execute(ChangeStatusCommand(self.task, S.IN_PROGRESS))
        self.task.description = "Edited outside command"
        with self.assertRaises(UndoConflictError):
            self.manager.undo_last()

    def test_two_status_commands_undo_in_lifo_order(self):
        self.manager.execute(ChangeStatusCommand(self.task, S.IN_PROGRESS))
        self.manager.execute(ChangeStatusCommand(self.task, S.DONE))
        self.assertTrue(self.manager.undo_last())
        self.assertEqual(self.task.status, S.IN_PROGRESS)
        self.assertTrue(self.manager.undo_last())
        self.assertEqual(self.task.status, S.TODO)
        self.assertEqual(self.manager.history_size, 0)
        self.assertEqual(self.task.revision, 4)

    def test_undo_completion_calls_reopen_and_emits_one_event(self):
        self.task.change_status(S.IN_PROGRESS)
        self.manager.execute(ChangeStatusCommand(self.task, S.DONE))
        spy = SpyNotifier()
        self.task.subscribe(NotifierObserver(spy))
        with patch.object(self.task, "reopen", wraps=self.task.reopen) as reopen:
            self.manager.undo_last()
        reopen.assert_called_once_with(S.IN_PROGRESS)
        self.assertEqual(len(spy.messages), 1)
        self.assertIn("reopened: DONE -> IN_PROGRESS", spy.messages[0])

    def test_two_assignment_commands_undo(self):
        self.manager.execute(AssignTaskCommand(self.task, User("Binh")))
        self.manager.execute(AssignTaskCommand(self.task, User("Cuong")))
        self.manager.undo_last()
        self.manager.undo_last()
        self.assertEqual(self.task.assignee.name, "An")
        self.assertEqual(self.manager.history_size, 0)

    def test_mixed_commands_and_completion_all_undo(self):
        self.manager.execute(ChangeStatusCommand(self.task, S.IN_PROGRESS))
        self.manager.execute(AssignTaskCommand(self.task, User("Binh")))
        self.manager.execute(ChangeStatusCommand(self.task, S.DONE))
        for _ in range(3):
            self.assertTrue(self.manager.undo_last())
        self.assertEqual(self.task.status, S.TODO)
        self.assertEqual(self.task.assignee.name, "An")

    def test_noops_do_not_invalidate_previous_command(self):
        self.manager.execute(ChangeStatusCommand(self.task, S.IN_PROGRESS))
        self.task.change_status(S.IN_PROGRESS)
        self.task.assign_to(self.task.assignee)
        self.task.title = self.task.title
        self.assertTrue(self.manager.undo_last())

    def test_command_can_execute_again_after_undo(self):
        command = ChangeStatusCommand(self.task, S.IN_PROGRESS)
        self.manager.execute(command)
        self.manager.undo_last()
        self.assertTrue(self.manager.execute(command))
        self.assertEqual(self.task.status, S.IN_PROGRESS)

    def test_failed_or_repeated_command_does_not_add_history(self):
        command = ChangeStatusCommand(self.task, S.IN_PROGRESS)
        self.manager.execute(command)
        with self.assertRaises(CommandStateError):
            self.manager.execute(command)
        self.assertEqual(self.manager.history_size, 1)
        self.assertIsInstance(CommandStateError("test"), RuntimeError)
        self.assertIsInstance(UndoConflictError("test"), TaskManagerError)

    def test_commands_on_multiple_tasks_undo(self):
        other = make_task()
        self.manager.execute(ChangeStatusCommand(self.task, S.IN_PROGRESS))
        self.manager.execute(ChangeStatusCommand(other, S.IN_PROGRESS))
        self.manager.undo_last()
        self.manager.undo_last()
        self.assertEqual((self.task.status, other.status), (S.TODO, S.TODO))

    def test_long_interleaved_history_restores_every_snapshot(self):
        generator = random.Random(20261022)
        tasks = [make_task() for _ in range(20)]
        snapshots = []
        for step in range(200):
            available = [task for task in tasks if task.status != S.DONE]
            if not available:
                new_task = make_task()
                tasks.append(new_task)
                available = [new_task]
            task = generator.choice(available)
            before = (task.status, task.assignee)
            if generator.randrange(4) == 0:
                destination = S.IN_PROGRESS if task.status == S.TODO else S.DONE
                command = ChangeStatusCommand(task, destination)
            else:
                command = AssignTaskCommand(task, User(f"User-{step}"))
            self.assertTrue(self.manager.execute(command))
            snapshots.append((task, before))
        for task, before in reversed(snapshots):
            self.assertTrue(self.manager.undo_last())
            self.assertEqual((task.status, task.assignee), before)
        self.assertEqual(self.manager.history_size, 0)

    def test_observer_mutation_is_not_recorded_as_command_owned(self):
        class MutatingObserver:
            fired = False

            def update(inner, task, message):
                if not inner.fired:
                    inner.fired = True
                    task.complete()
                    task.reopen()

        self.task.subscribe(MutatingObserver())
        self.manager.execute(ChangeStatusCommand(self.task, S.IN_PROGRESS))
        with self.assertRaises(UndoConflictError):
            self.manager.undo_last()

    def test_undo_does_not_hide_a_mutation_from_observer(self):
        self.manager.execute(ChangeStatusCommand(self.task, S.IN_PROGRESS))
        self.manager.execute(AssignTaskCommand(self.task, User("Binh")))

        class EditingObserver:
            def update(inner, task, message):
                task.description = "Changed during undo notification"

        self.task.subscribe(EditingObserver())
        self.manager.undo_last()
        with self.assertRaises(UndoConflictError):
            self.manager.undo_last()
        self.assertEqual(self.manager.history_size, 1)


class TestPlanIntegration(unittest.TestCase):
    def test_done_builder_clone_unchanged_is_allowed(self):
        original = make_task(S.DONE)
        clone = TaskBuilder.from_task(original).build()
        self.assertIsNot(original, clone)
        self.assertEqual(original, clone)
        self.assertEqual(original.created_at, clone.created_at)

    def test_done_builder_cannot_edit_business_fields(self):
        for name, value in [("description", "New"), ("priority", P.LOW),
                            ("title", "New"), ("status", S.TODO)]:
            with self.subTest(field=name):
                builder = TaskBuilder.from_task(make_task(S.DONE))
                setattr(builder, name, value)
                with self.assertRaises(TaskLockedError):
                    builder.build()

    def test_reopen_before_builder_allows_edit_and_preserves_created_at(self):
        original = make_task(S.DONE)
        original.reopen()
        clone = TaskBuilder.from_task(original).set_description("New").build()
        self.assertEqual(clone.description, "New")
        self.assertEqual(clone.created_at, original.created_at)
        self.assertEqual(original.description, "")

    def test_prefix_decorator_stacks_and_works_as_observer_notifier(self):
        spy = SpyNotifier()
        wrapped = PrefixNotifier(PrefixNotifier(spy, "[inner] "), "[outer] ")
        task = make_task()
        service = TaskService(PrioritySortStrategy(), observers=[NotifierObserver(wrapped)])
        service.watch_task(task)
        task.change_status(S.IN_PROGRESS)
        self.assertEqual(len(spy.messages), 1)
        self.assertTrue(spy.messages[0].startswith("[inner] [outer] Task"))

    def test_base_notifier_decorator_delegates(self):
        spy = SpyNotifier()
        NotifierDecorator(spy).send("message")
        self.assertEqual(spy.messages, ["message"])

    def test_service_new_task_is_subscribed_automatically_via_service(self):
        spy = SpyNotifier()
        service = TaskService(PrioritySortStrategy(), notifiers=[spy])
        project = Project("Test")
        service.watch_project(project)
        task = make_task()
        with contextlib.redirect_stdout(io.StringIO()):
            service.add_task(project, task)
        task.change_status(S.IN_PROGRESS)
        self.assertEqual(len(spy.messages), 1)
        self.assertIn(task, project.tasks)

    def test_custom_observer_injection_keeps_notifier_api_compatible(self):
        spy = SpyNotifier()
        messages = []

        class Observer:
            def update(self, task, message):
                messages.append(message)

        service = TaskService(PrioritySortStrategy(), [spy], observers=[Observer()])
        task = make_task()
        service.watch_task(task)
        task.change_status(S.IN_PROGRESS)
        self.assertEqual(len(messages), 1)
        self.assertEqual(len(spy.messages), 1)

    def test_project_rejects_invalid_task_before_modifying_list(self):
        project = Project("Test")
        with self.assertRaises(TypeError):
            project.add_task(None)
        self.assertEqual(project.tasks, [])

    def test_factory_supports_registration_without_editing_creation_method(self):
        original = TaskFactory._priorities
        try:
            TaskFactory.register_type("review-test", P.LOW)
            task = TaskFactory.create_task("review-test", "Test", User("An"))
            self.assertEqual(task.priority, P.LOW)
            self.assertEqual(task.task_type, "review-test")
            with self.assertRaises(ValueError):
                TaskFactory.register_type("review-test", P.HIGH)
        finally:
            TaskFactory._priorities = original


if __name__ == "__main__":
    unittest.main()
