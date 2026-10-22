class TaskStorage:
    def __init__(self) -> None:
        self._tasks_by_id: dict = {}

    def add_task(self, task_id: int, task) -> None:
        if task_id in self._tasks_by_id:
            raise ValueError("Duplicate task ID")

        self._tasks_by_id[task_id] = task

    def get_task(self, task_id: int):
        return self._tasks_by_id.get(task_id)

    def __len__(self) -> int:
        return len(self._tasks_by_id)
