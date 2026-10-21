import heapq
from datetime import date, datetime
from typing import Iterable

from task_manager.models import Task, TaskPriority, TaskStatus


PRIORITY_RANK = {
    TaskPriority.HIGH: 3,
    TaskPriority.MEDIUM: 2,
    TaskPriority.LOW: 1,
}


def urgency_key(task: Task) -> tuple[int, bool, date, datetime]:
    """Smaller tuple means higher urgency (heapq is a min-heap)."""
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
    """Return up to n highest-priority tasks without modifying the input.

    For n small compared with N: O(N log n) time and O(n) auxiliary
    heap space. Filtering non-DONE tasks is an O(N) scan.
    """
    if n <= 0:
        return []

    candidates = (
        tasks
        if include_done
        else (task for task in tasks if task.status != TaskStatus.DONE)
    )
    return heapq.nsmallest(n, candidates, key=urgency_key)
