from typing import Any


def _label(value: Any) -> str:
    return str(getattr(value, "value", value))


class TaskManagerError(Exception):
    """Lỗi nghiệp vụ chung của Task Manager."""

    pass


class CommandStateError(TaskManagerError, RuntimeError):
    """Command được sử dụng không đúng trạng thái."""

    pass


class UndoConflictError(CommandStateError):
    """Dữ liệu hiện tại không phù hợp để undo."""

    pass


class TaskNotFoundError(TaskManagerError):
    def __init__(self, task_id: Any) -> None:
        super().__init__(task_id)
        self.task_id = task_id

    def __str__(self) -> str:
        return f"Task not found: {self.task_id!r}"


class InvalidStatusTransitionError(TaskManagerError):
    def __init__(
        self,
        current: Any,
        requested: Any,
        task_title: str | None = None,
    ) -> None:
        super().__init__(current, requested, task_title)
        self.current = current
        self.requested = requested
        self.task_title = task_title

    def __str__(self) -> str:
        subject = f'Task "{self.task_title}"' if self.task_title else "Task"

        return (
            f"{subject}: cannot change status from "
            f"{_label(self.current)} to {_label(self.requested)}"
        )


class PermissionDeniedError(TaskManagerError):
    def __init__(
        self,
        user_name: str,
        action: str,
        task_title: str | None = None,
    ) -> None:
        super().__init__(user_name, action, task_title)
        self.user_name = user_name
        self.action = action
        self.task_title = task_title

    def __str__(self) -> str:
        target = f' on task "{self.task_title}"' if self.task_title else ""

        return f"User {self.user_name!r} is not allowed to {self.action}{target}"


class TaskLockedError(TaskManagerError):
    def __init__(self, task_title: str, field_name: str) -> None:
        super().__init__(task_title, field_name)
        self.task_title = task_title
        self.field_name = field_name

    def __str__(self) -> str:
        return (
            f'Task "{self.task_title}" is DONE. '
            f"Reopen before editing {self.field_name}."
        )
