from datetime import date, datetime

from task_manager.models import User, TaskStatus, Task, TaskPriority
from task_manager.project import Project
from task_manager.notifier import ConsoleNotifier, EmailNotifier
from task_manager.taskdisplayer import TaskDisplayer
from task_manager.strategies import (
    PrioritySortStrategy,
    DeadlineSortStrategy,
    CreatedAtSortStrategy,
)
from task_manager.task_service import TaskService
from task_manager.task_observer import NotifierObserver
from task_manager.decorator import PrefixNotifier
from task_manager.exceptions import InvalidStatusTransitionError
from task_manager.commands import (
    ChangeStatusCommand,
    AssignTaskCommand,
    CommandManager,
)


def main() -> None:
    # 1. Create user and project
    user1 = User("Khôi")
    project1 = Project("AI Camera")

    # 2. Create tasks
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

    project1.add_task(task1)
    project1.add_task(task2)

    # 3. Set up observers and reuse the existing Strategy service
    console1 = ConsoleNotifier()
    email1 = EmailNotifier()
    service = TaskService(
        PrioritySortStrategy(),
        observers=[NotifierObserver(console1),
                   NotifierObserver(PrefixNotifier(email1, "[Task Manager] "))],
    )
    service.watch_project(project1)

    # 4. Test automatic notifications
    print("=== OBSERVER NOTIFICATIONS ===")
    task1.change_status(TaskStatus.IN_PROGRESS)
    task1.complete()
    try:
        task1.change_status(TaskStatus.TODO)
    except InvalidStatusTransitionError as error:
        print("Expected rejection:", error)

    user2 = User("An")
    task2.assign_to(user2)  # Notify both registered notifiers
    print("\n=== COMMAND + UNDO ===")

    manager = CommandManager()

    # Execute Command 1
    manager.execute(
        ChangeStatusCommand(task2, TaskStatus.IN_PROGRESS)
    )

    # Execute Command 2
    manager.execute(
        AssignTaskCommand(task2, user1)
    )

    print(
        "Before Undo:",
        task2.status.value,
        task2.assignee.name
    )

    # Undo Command 2
    manager.undo_last()

    print(
        "After Undo 1:",
        task2.status.value,
        task2.assignee.name
    )

    # Undo Command 1
    manager.undo_last()

    print(
        "After Undo 2:",
        task2.status.value,
        task2.assignee.name
    )


    # 5. Show tasks
    print("\n=== TASK MANAGER ===")
    print("Project:", project1.name)
    TaskDisplayer().show_task(project1)
    print("Total tasks:", len(project1.tasks))
    print("Priority:", task1.priority.value)

    # 6. Sort by priority
    sorted_tasks = service.get_sorted_tasks(project1)
    print("\n=== TASKS SORTED BY PRIORITY ===")
    for task in sorted_tasks:
        print(f"{task.title} - {task.priority.value}")

    # 7. Explicitly reopen before editing a completed task.
    task1.reopen()
    task1.deadline = date(2026, 10, 25)
    task2.deadline = date(2026, 10, 20)
    service.set_strategy(DeadlineSortStrategy())
    sorted_tasks = service.get_sorted_tasks(project1)
    print("\n=== TASKS SORTED BY DEADLINE ===")
    for task in sorted_tasks:
        print(f"{task.title} - {task.deadline}")

    # 8. Sort by creation time (fixed timestamps for demonstration)
    task1.created_at = datetime(2026, 10, 15, 8, 0)
    task2.created_at = datetime(2026, 10, 15, 9, 0)
    service.set_strategy(CreatedAtSortStrategy())
    sorted_tasks = service.get_sorted_tasks(project1)
    print("\n=== TASKS SORTED BY CREATED AT ===")
    for task in sorted_tasks:
        print(f"{task.title} - {task.created_at}")



if __name__ == "__main__":
    main()
