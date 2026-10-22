from .models import Task, TaskPriority, TaskStatus


class TaskFactory:
    _priorities = {
        "bug": TaskPriority.HIGH,
        "feature": TaskPriority.MEDIUM,
        "chore": TaskPriority.LOW,
    }

    @classmethod
    def register_type(cls, task_type: str, priority: TaskPriority) -> None:
        """Extend available types from application setup without editing create_task."""
        if not isinstance(task_type, str):
            raise TypeError("task_type must be str")
        if not task_type.strip():
            raise ValueError("task_type must not be empty")
        if not isinstance(priority, TaskPriority):
            raise TypeError("priority must be TaskPriority")
        if task_type in cls._priorities:
            raise ValueError("Task type already registered")
        cls._priorities = {**cls._priorities, task_type: priority}

    @classmethod
    def create_task(cls, task_type, title, assignee):
        if not isinstance(task_type, str):
            raise TypeError("task_type must be str")
        try:
            priority = cls._priorities[task_type]
        except KeyError:
            raise ValueError("Invalid task type") from None

        return Task(
            title=title,
            assignee=assignee,
            status=TaskStatus.TODO,
            priority=priority,
            task_type=task_type
        )


