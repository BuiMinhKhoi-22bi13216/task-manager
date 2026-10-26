from .project import Project


class TaskDisplayer:
    def show_task(self, project: Project) -> None:
        for task in project.tasks:
            print(task.title, "-", task.assignee.name, "-", task.status.value)