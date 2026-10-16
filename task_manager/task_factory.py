from .models import Task, TaskPriority


class TaskFactory:

    @staticmethod
    def create_task(task_type, title, assignee):

        if task_type == "bug":
            priority = TaskPriority.HIGH

        elif task_type == "feature":
            priority = TaskPriority.MEDIUM

        elif task_type == "chore":
            priority = TaskPriority.LOW

        else:
            raise ValueError("Invalid task type")

        return Task(
            title=title,
            assignee=assignee,
            priority=priority,
            task_type=task_type
        )


