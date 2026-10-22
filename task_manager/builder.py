from datetime import date, datetime

from .exceptions import TaskLockedError
from .models import Task, TaskPriority, TaskStatus, User


class TaskBuilder:
    def __init__(self, title: str, assignee: User):
        self.title = title
        self.assignee = assignee
        self.status = TaskStatus.TODO
        self.task_type = "general"
        self.priority = TaskPriority.MEDIUM
        self.description = ""

        self.deadline: date | None = None
        self.created_at: datetime | None = None
        self._locked_values: dict[str, object] | None = None

    @classmethod
    def from_task(cls, task: Task) -> "TaskBuilder":
        builder = cls(task.title, task.assignee)

        builder.status = task.status
        builder.task_type = task.task_type
        builder.priority = task.priority
        builder.description = task.description
        builder.deadline = task.deadline
        builder.created_at = task.created_at

        if task.status == TaskStatus.DONE:
            builder._locked_values = {
                name: getattr(task, name) for name in Task._LOCKED_FIELDS | {"status"}
            }

        return builder

    def set_description(self, description: str) -> "TaskBuilder":
        self.description = description
        return self

    def set_priority(self, priority: TaskPriority) -> "TaskBuilder":
        self.priority = priority
        return self

    def set_deadline(self, deadline: date | None) -> "TaskBuilder":
        self.deadline = deadline
        return self

    def build(self) -> Task:
        if self._locked_values is not None:
            for name, original in self._locked_values.items():
                if getattr(self, name) != original:
                    raise TaskLockedError(
                        str(self._locked_values["title"]),
                        name,
                    )

        created_at = self.created_at if self.created_at is not None else datetime.now()

        return Task(
            title=self.title,
            assignee=self.assignee,
            status=self.status,
            priority=self.priority,
            task_type=self.task_type,
            description=self.description,
            deadline=self.deadline,
            created_at=created_at,
        )
