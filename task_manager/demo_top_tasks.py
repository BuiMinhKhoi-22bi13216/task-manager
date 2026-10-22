from datetime import date, datetime, timedelta
from random import Random

from task_manager.models import Task, TaskPriority, TaskStatus, User
from task_manager.top_tasks import top_tasks


def main() -> None:
    owner = User("Demo user")
    priorities = (
        [TaskPriority.HIGH] * 6 + [TaskPriority.MEDIUM] * 8 + [TaskPriority.LOW] * 6
    )
    tasks = []
    for i, priority in enumerate(priorities, start=1):
        tasks.append(
            Task(
                title=f"Task {i:02d}",
                assignee=owner,
                status=TaskStatus.DONE if i in (2, 10) else TaskStatus.TODO,
                priority=priority,
                deadline=(date(2026, 11, 1) + timedelta(days=i % 7))
                if i % 4 != 0
                else None,
                created_at=datetime(2026, 10, 1) + timedelta(days=i),
            )
        )

    Random(7).shuffle(tasks)
    original_ids = [id(task) for task in tasks]
    selected = top_tasks(tasks, 10)

    assert len(selected) == 10
    assert all(task.status != TaskStatus.DONE for task in selected)
    assert [id(task) for task in tasks] == original_ids

    print(f"Total tasks: {len(tasks)}")
    print("Top 10 urgent non-DONE tasks:")
    print(f"{'Title':<12} {'Priority':<9} {'Deadline':<14} {'Status'}")
    for task in selected:
        print(
            f"{task.title:<12} {task.priority.name:<9} "
            f"{str(task.deadline or '-'): <14} {task.status.value}"
        )
    print("PASS: 10 tasks, DONE excluded, input list unchanged")


if __name__ == "__main__":
    main()
