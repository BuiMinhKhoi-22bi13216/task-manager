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
    notifiers=[console1, email1],
)
service.watch_project(project1)

# 4. Test automatic notifications
print("=== OBSERVER NOTIFICATIONS ===")
task1.change_status(TaskStatus.IN_PROGRESS)
task1.complete()
task1.change_status(TaskStatus.TODO)  # Invalid transition: no notification

user2 = User("An")
task2.assign_to(user2)  # Notify both registered notifiers

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

# 7. Sort by deadline
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


