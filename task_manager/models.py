from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from task_manager.task_observer import TaskObserver


@dataclass
class User:
    name: str


class TaskStatus(Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class Task:
    title: str
    assignee: User
    status: TaskStatus
    priority: TaskPriority
    task_type: str = "general"
    description: str = ""
    deadline: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.now)
    _observers: list["TaskObserver"] = field(
        default_factory=list,
        init=False,
        repr=False,
        compare=False,
    )

    def complete(self) -> None:
        self.change_status(TaskStatus.DONE)

    def change_status(self, new_status: TaskStatus) -> None:
        if not isinstance(new_status, TaskStatus):
            raise TypeError("new_status must be TaskStatus")

        if self.status == new_status:
            return

        if self.status == TaskStatus.DONE and new_status != TaskStatus.DONE:
            print("Invalid transition")
            return

        if self.status == TaskStatus.IN_PROGRESS and new_status == TaskStatus.TODO:
            print("Invalid transition")
            return

        old_status = self.status
        self.status = new_status
        self._notify(f"status: {old_status.value} -> {new_status.value}")

    def subscribe(self, observer: "TaskObserver") -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: "TaskObserver") -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify(self, message: str) -> None:
        for observer in tuple(self._observers):
            observer.update(self, message)

    def assign_to(self, user: User) -> None:
        if not isinstance(user, User):
            raise TypeError("user must be User")

        if self.assignee == user:
            return

        old_name = self.assignee.name
        self.assignee = user
        self._notify(f"assigned: {old_name} -> {user.name}")
