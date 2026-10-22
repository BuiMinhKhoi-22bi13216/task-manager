import unittest
from task_manager.models import User, Task, TaskStatus, TaskPriority
from task_manager.notifier import Notifier
from task_manager.strategies import PrioritySortStrategy
from task_manager.task_service import TaskService
from task_manager.task_observer import NotifierObserver
from task_manager.exceptions import InvalidStatusTransitionError


class SpyNotifier(Notifier):
    def __init__(self):
        self.messages = []

    def send(self, message: str) -> None:
        self.messages.append(message)


class TestObserver(unittest.TestCase):
    def setUp(self):
        self.task = Task(
            title="Learn Python",
            assignee=User("Khoi"),
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
        )
        self.spy = SpyNotifier()
        self.service = TaskService(PrioritySortStrategy(), [self.spy])
        self.service.watch_task(self.task)

    def test_valid_change_sends_message(self):
        self.task.change_status(TaskStatus.IN_PROGRESS)
        self.assertEqual(len(self.spy.messages), 1)
        self.assertIn("TODO -> IN_PROGRESS", self.spy.messages[0])

    def test_invalid_change_does_not_notify(self):
        self.task.change_status(TaskStatus.IN_PROGRESS)
        self.task.change_status(TaskStatus.DONE)

        self.spy.messages.clear()

        with self.assertRaises(InvalidStatusTransitionError):
            self.task.change_status(TaskStatus.TODO)

        self.assertEqual(self.task.status, TaskStatus.DONE)
        self.assertEqual(self.spy.messages, [])
 
    def test_same_status_does_not_notify(self):
        self.task.change_status(TaskStatus.TODO)
        self.assertEqual(self.spy.messages, [])

    def test_assignment_sends_message(self):
        self.task.assign_to(User("An"))
        self.assertEqual(len(self.spy.messages), 1)
        self.assertIn("Khoi -> An", self.spy.messages[0])

    def test_unsubscribe(self):
        second_task = Task("Learn Docker", User("Khoi"), TaskStatus.TODO, TaskPriority.LOW)
        observer = NotifierObserver(self.spy)
        second_task.subscribe(observer)
        second_task.unsubscribe(observer)
        second_task.change_status(TaskStatus.IN_PROGRESS)
        self.assertEqual(self.spy.messages, [])

    def test_multiple_notifiers(self):
        a, b = SpyNotifier(), SpyNotifier()
        task = Task("Learn Git", User("Khoi"), TaskStatus.TODO, TaskPriority.LOW)
        service = TaskService(PrioritySortStrategy(), [a, b])
        service.watch_task(task)
        service.watch_task(task)
        task.change_status(TaskStatus.IN_PROGRESS)
        # Xóa thông báo trước đó để chỉ kiểm tra sự kiện hoàn thành
        a.messages.clear()
        b.messages.clear()

        task.complete()
        
        self.assertEqual(len(a.messages), 1)
        self.assertEqual(len(b.messages), 1)


if __name__ == "__main__":
    unittest.main()