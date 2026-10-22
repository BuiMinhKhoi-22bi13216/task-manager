from datetime import date
from typing import Optional
from .exceptions import TaskLockedError

from .models import (
    Task,
    User,
    TaskStatus,
    TaskPriority
)


class TaskBuilder:

    def __init__(self, title: str, assignee: User):
        self.title = title
        self.assignee = assignee
        self.status = TaskStatus.TODO
        self.task_type = "general"
        self.priority = TaskPriority.MEDIUM
        self.description = ""
        self.deadline = None
        self.created_at = None
        self._locked_values = None

    @classmethod
    def from_task(cls, task: Task):
        builder = cls(task.title, task.assignee)

        builder.status = task.status
        builder.task_type = task.task_type
        builder.priority = task.priority
        builder.description = task.description
        builder.deadline = task.deadline
        builder.created_at = task.created_at
        if task.status == TaskStatus.DONE:
            builder._locked_values = {
                name: getattr(task, name)
                for name in Task._LOCKED_FIELDS | {"status"}
            }

        return builder

    def set_description(self, description: str):
        self.description = description
        return self

    def set_priority(self, priority: TaskPriority):
        self.priority = priority
        return self

    def set_deadline(self, deadline: Optional[date]):
        self.deadline = deadline
        return self

    
    def build(self) -> Task:
        # Rebuild a DONE task unchanged; reopen the source before editing it.
        if self._locked_values is not None:
            for name, original in self._locked_values.items():
                if getattr(self, name) != original:
                    raise TaskLockedError(self._locked_values["title"], name)
        created_at_kwargs = {}

        if self.created_at is not None:
            created_at_kwargs["created_at"] = self.created_at

        return Task(
            title=self.title,
            assignee=self.assignee,
            status=self.status,
            task_type=self.task_type,
            priority=self.priority,
            description=self.description,
            deadline=self.deadline,
            **created_at_kwargs
        )


    
