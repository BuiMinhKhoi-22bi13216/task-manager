from datetime import date, datetime

from task_manager.commands import (
    AssignTaskCommand,
    ChangeStatusCommand,
    CommandManager,
)
from task_manager.exceptions import InvalidStatusTransitionError
from task_manager.models import Task, TaskPriority, TaskStatus, User
from task_manager.notifier import ConsoleNotifier, EmailNotifier
from task_manager.project import Project
from task_manager.strategies import (
    CreatedAtSortStrategy,
    DeadlineSortStrategy,
    PrioritySortStrategy,
)
from task_manager.task_service import TaskService
from task_manager.taskdisplayer import TaskDisplayer


def main() -> None:
    user1 = User("Khôi")
    project1 = Project("AI Camera")

    task1 = Task(
        title="Learn Python",
        assignee=user1,
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
    )

    task2 = Task(
        title="Learn Docker",
        assignee=user1,
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
    )

    task1_id = project1.add_task(task1)
    project1.add_task(task2)
    print("Find by ID:", project1.get_task(task1_id).title)

    console1 = ConsoleNotifier()
    email1 = EmailNotifier()

    service = TaskService(
        PrioritySortStrategy(),
        notifiers=[console1, email1],
    )
    service.watch_project(project1)

    print("=== OBSERVER NOTIFICATIONS ===")

    task1.change_status(TaskStatus.IN_PROGRESS)
    task1.complete()

    try:
        task1.change_status(TaskStatus.TODO)
    except InvalidStatusTransitionError as error:
        print("Expected rejection:", error)

    user2 = User("An")
    task2.assign_to(user2)

    print("\n=== COMMAND + UNDO ===")

    manager = CommandManager()

    manager.execute(ChangeStatusCommand(task2, TaskStatus.IN_PROGRESS))
    manager.execute(AssignTaskCommand(task2, user1))

    print(
        "Before Undo:",
        task2.status.value,
        task2.assignee.name,
    )

    manager.undo_last()

    print(
        "After Undo 1:",
        task2.status.value,
        task2.assignee.name,
    )

    manager.undo_last()

    print(
        "After Undo 2:",
        task2.status.value,
        task2.assignee.name,
    )

    print("\n=== TASK MANAGER ===")
    print("Project:", project1.name)
    TaskDisplayer().show_task(project1)
    print("Total tasks:", len(project1.tasks))

    print("\n=== TASKS SORTED BY PRIORITY ===")

    for task in service.get_sorted_tasks(project1):
        print(f"{task.title} - {task.priority.value}")

    # Xóa history trước khi chỉnh task trực tiếp.
    manager.clear_history()

    # Task DONE phải reopen trước khi chỉnh.
    task1.reopen()

    task1.deadline = date(2026, 10, 25)
    task2.deadline = date(2026, 10, 20)

    service.set_strategy(DeadlineSortStrategy())

    print("\n=== TASKS SORTED BY DEADLINE ===")

    for task in service.get_sorted_tasks(project1):
        print(f"{task.title} - {task.deadline}")

    task1.created_at = datetime(2026, 10, 15, 8, 0)
    task2.created_at = datetime(2026, 10, 15, 9, 0)

    service.set_strategy(CreatedAtSortStrategy())

    print("\n=== TASKS SORTED BY CREATED AT ===")

    for task in service.get_sorted_tasks(project1):
        print(f"{task.title} - {task.created_at}")


if __name__ == "__main__":
    main()