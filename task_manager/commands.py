from abc import ABC, abstractmethod

from task_manager.exceptions import CommandStateError, UndoConflictError
from task_manager.models import Task, TaskStatus, User


class Command(ABC):
    @abstractmethod
    def execute(self) -> bool:
        pass

    @abstractmethod
    def undo(self) -> bool:
        pass


class ChangeStatusCommand(Command):
    def __init__(self, task: Task, new_status: TaskStatus):
        self._task = task
        self._new_status = new_status
        self._old_status: TaskStatus | None = None
        self._executed = False

    def execute(self) -> bool:
        if self._executed:
            raise CommandStateError("Command already executed")

        old_status = self._task.status
        self._task.change_status(self._new_status)

        if self._task.status == old_status:
            return False

        self._old_status = old_status
        self._executed = True
        return True

    def undo(self) -> bool:
        if not self._executed or self._old_status is None:
            return False

        self._task._restore_status_for_undo(
            expected_current=self._new_status,
            previous_status=self._old_status,
        )

        self._executed = False
        return True


class AssignTaskCommand(Command):
    def __init__(self, task: Task, new_assignee: User):
        self._task = task
        self._new_assignee = new_assignee
        self._old_assignee: User | None = None
        self._executed = False

    def execute(self) -> bool:
        if self._executed:
            raise CommandStateError("Command already executed")

        old_assignee = self._task.assignee
        self._task.assign_to(self._new_assignee)

        if self._task.assignee == old_assignee:
            return False

        self._old_assignee = old_assignee
        self._executed = True
        return True

    def undo(self) -> bool:
        if not self._executed or self._old_assignee is None:
            return False

        if self._task.assignee != self._new_assignee:
            raise UndoConflictError(
                "Cannot undo: task assignee changed outside Command"
            )

        self._task.assign_to(self._old_assignee)
        self._executed = False
        return True


class CommandManager:
    def __init__(self) -> None:
        self._history: list[Command] = []

    def execute(self, command: Command) -> bool:
        if not command.execute():
            return False

        self._history.append(command)
        return True

    def undo_last(self) -> bool:
        if not self._history:
            return False

        command = self._history[-1]

        if not command.undo():
            return False

        self._history.pop()
        return True

    def clear_history(self) -> None:
        self._history.clear()

    @property
    def history_size(self) -> int:
        return len(self._history)
