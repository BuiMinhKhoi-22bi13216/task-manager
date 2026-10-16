from datetime import date
from typing import Optional

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

    @classmethod
    def from_task(cls, task: Task):
        builder = cls(task.title, task.assignee)

        builder.status = task.status
        builder.task_type = task.task_type
        builder.priority = task.priority
        builder.description = task.description
        builder.deadline = task.deadline

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
        return Task(
            title=self.title,
            assignee=self.assignee,
            status=self.status,
            task_type=self.task_type,
            priority=self.priority,
            description=self.description,
            deadline=self.deadline
        )


    