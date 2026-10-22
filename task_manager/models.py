import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

from .exceptions import (
    InvalidStatusTransitionError,
    TaskLockedError,
    UndoConflictError,
)

if TYPE_CHECKING:
    from .task_observer import TaskObserver

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class User:
    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name must be str")

        if not self.name.strip():
            raise ValueError("name must not be empty")


class TaskStatus(Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


PRIORITY_RANK = {
    TaskPriority.LOW: 1,
    TaskPriority.MEDIUM: 2,
    TaskPriority.HIGH: 3,
}


@dataclass
class Task:
    _LOCKED_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "title",
            "description",
            "deadline",
            "priority",
            "assignee",
            "task_type",
            "created_at",
        }
    )

    title: str
    assignee: User
    status: TaskStatus
    priority: TaskPriority
    task_type: str = "general"
    description: str = ""
    deadline: date | None = None
    created_at: datetime = field(default_factory=datetime.now)

    _observers: list["TaskObserver"] = field(
        default_factory=list,
        init=False,
        repr=False,
        compare=False,
    )

    @staticmethod
    def _validate_field(name: str, value: Any) -> None:
        if name in {"title", "description", "task_type"}:
            if not isinstance(value, str):
                raise TypeError(f"{name} must be str")

            if name != "description" and not value.strip():
                raise ValueError(f"{name} must not be empty")

        elif name == "assignee" and not isinstance(value, User):
            raise TypeError("assignee must be User")

        elif name == "status" and not isinstance(value, TaskStatus):
            raise TypeError("status must be TaskStatus")

        elif name == "priority" and not isinstance(value, TaskPriority):
            raise TypeError("priority must be TaskPriority")

        elif name == "deadline":
            if value is not None and type(value) is not date:
                raise TypeError("deadline must be date or None")

        elif name == "created_at":
            if not isinstance(value, datetime):
                raise TypeError("created_at must be datetime")

            if value.tzinfo is not None:
                raise ValueError("created_at must be a naive local datetime")

    def __post_init__(self) -> None:
        for name in self._LOCKED_FIELDS | {"status"}:
            self._validate_field(name, getattr(self, name))

        object.__setattr__(self, "_initialized", True)

    def __setattr__(self, name: str, value: Any) -> None:
        initialized = self.__dict__.get("_initialized", False)

        if initialized and name == "status":
            raise AttributeError("Use change_status() or reopen()")

        if initialized and name in self._LOCKED_FIELDS:
            if self.status == TaskStatus.DONE:
                raise TaskLockedError(self.title, name)

            self._validate_field(name, value)

            if name == "assignee":
                self.assign_to(value)
                return

            if getattr(self, name) == value:
                return

            object.__setattr__(self, name, value)
            return

        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if self.__dict__.get("_initialized", False):
            if name == "status":
                raise AttributeError("Cannot delete status")

            if name in self._LOCKED_FIELDS:
                if self.status == TaskStatus.DONE:
                    raise TaskLockedError(self.title, name)

                raise AttributeError(f"Cannot delete business field: {name}")

        object.__delattr__(self, name)

    def _set_status(self, new_status: TaskStatus, message: str) -> None:
        object.__setattr__(self, "status", new_status)
        self._notify(message)

    def complete(self) -> None:
        self.change_status(TaskStatus.DONE)

    def change_status(self, new_status: TaskStatus) -> None:
        self._validate_field("status", new_status)
        self._validate_field("status", self.status)

        if self.status == new_status:
            return

        allowed = {
            (TaskStatus.TODO, TaskStatus.IN_PROGRESS),
            (TaskStatus.IN_PROGRESS, TaskStatus.DONE),
        }

        if (self.status, new_status) not in allowed:
            raise InvalidStatusTransitionError(
                self.status,
                new_status,
                self.title,
            )

        message = f"status: {self.status.value} -> {new_status.value}"
        self._set_status(new_status, message)

    def assign_to(self, user: User) -> None:
        self._validate_field("assignee", user)

        if self.assignee == user:
            return

        if self.status == TaskStatus.DONE:
            raise TaskLockedError(self.title, "assignee")

        message = f"assigned: {self.assignee.name} -> {user.name}"

        object.__setattr__(self, "assignee", user)
        self._notify(message)

    def reopen(
        self,
        new_status: TaskStatus = TaskStatus.IN_PROGRESS,
    ) -> None:
        self._validate_field("status", new_status)

        if self.status != TaskStatus.DONE or new_status not in {
            TaskStatus.IN_PROGRESS,
            TaskStatus.TODO,
        }:
            raise InvalidStatusTransitionError(
                self.status,
                new_status,
                self.title,
            )

        message = f"reopened: {self.status.value} -> {new_status.value}"
        self._set_status(new_status, message)

    def _restore_status_for_undo(
        self,
        *,
        expected_current: TaskStatus,
        previous_status: TaskStatus,
    ) -> None:
        if self.status != expected_current:
            raise UndoConflictError("Cannot undo: task status changed outside Command")

        if self.status == TaskStatus.DONE and previous_status == TaskStatus.IN_PROGRESS:
            self.reopen(previous_status)

        elif (
            self.status == TaskStatus.IN_PROGRESS and previous_status == TaskStatus.TODO
        ):
            self._set_status(
                previous_status,
                "status: IN_PROGRESS -> TODO (undo)",
            )

        else:
            raise InvalidStatusTransitionError(
                self.status,
                previous_status,
                self.title,
            )

    def subscribe(self, observer: "TaskObserver") -> None:
        if not callable(getattr(observer, "update", None)):
            raise TypeError("observer must provide update(task, message)")

        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: "TaskObserver") -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify(self, message: str) -> None:
        for observer in tuple(self._observers):
            try:
                observer.update(self, message)
            except Exception:
                logger.exception("Observer %r failed", observer)
