class TaskDisplayer:
    def show_task(self, project):
        for task in project.tasks:
            print(task.title, "-", task.assignee.name, "-", task.status.value)
