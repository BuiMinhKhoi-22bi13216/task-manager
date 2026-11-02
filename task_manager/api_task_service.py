from itertools import count

from .exceptions import TaskNotFoundError

tasks: dict[int, dict[str, int | str]] = {}
task_ids = count(1)


def list_tasks(status: str | None = None) -> list[dict[str, int | str]]:
    if status is None:
        return list(tasks.values())

    result: list[dict[str, int | str]] = []
    for task in tasks.values():
        if task["status"] == status:
            result.append(task)
    return result


def get_task(task_id: int) -> dict[str, int | str]:
    task = tasks.get(task_id)
    if task is None:
        raise TaskNotFoundError(task_id)
    return task


def create_task(
    title: str,
    description: str,
    status: str,
) -> dict[str, int | str]:
    task_id = next(task_ids)
    new_task: dict[str, int | str] = {
        "id": task_id,
        "title": title,
        "description": description,
        "status": status,
    }
    tasks[task_id] = new_task
    return new_task