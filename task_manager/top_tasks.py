import heapq
from datetime import date, datetime
from typing import Iterable

from task_manager.models import PRIORITY_RANK, Task, TaskStatus


def urgency_key(task: Task) -> tuple[int, bool, date, datetime]:

    return (
        -PRIORITY_RANK[task.priority],
        task.deadline is None,
        task.deadline or date.max,
        task.created_at,
    )


def top_tasks(
    tasks: Iterable[Task],
    n: int = 10,
    *,
    include_done: bool = False,
) -> list[Task]:

    if n <= 0:
        return []

    candidates = (
        tasks
        if include_done
        else (task for task in tasks if task.status != TaskStatus.DONE)
    )
    return heapq.nsmallest(n, candidates, key=urgency_key)
