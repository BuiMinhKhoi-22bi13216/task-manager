class TaskStorage:
    def __init__(self):
        self._tasks_by_id = {}

    def add_task(self, task_id, task):
        if task_id in self._tasks_by_id:
            raise ValueError("Duplicate task ID")

        self._tasks_by_id[task_id] = task

    def get_task(self, task_id):
        return self._tasks_by_id.get(task_id)

    def __len__(self):
        return len(self._tasks_by_id)