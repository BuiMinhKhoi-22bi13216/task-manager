from .models import Task, TaskPriority, TaskStatus, User


class TaskFactory:
    @staticmethod
    def create_task(
        task_type: str,
        title: str,
        assignee: User,
    ) -> Task:
        priorities = {
            "bug": TaskPriority.HIGH,
            "feature": TaskPriority.MEDIUM,
            "chore": TaskPriority.LOW,
        }

        if task_type not in priorities:
            raise ValueError("Invalid task type")

        return Task(
            title=title,
            assignee=assignee,
            status=TaskStatus.TODO,
            priority=priorities[task_type],
            task_type=task_type,
        )
