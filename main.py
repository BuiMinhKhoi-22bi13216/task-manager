from task_manager.models import User, TaskStatus, Task, TaskPriority
from task_manager.project import Project
from task_manager.notifier import ConsoleNotifier, EmailNotifier
from task_manager.taskdisplayer import TaskDisplayer

# 1. Create User and Project
user1 = User("Khôi")
project1 = Project("AI Camera")


# 2. Create Tasks
task1 = Task("Learn Python", user1, priority=TaskPriority.HIGH)
task2 = Task("Learn Docker", user1)

project1.add_task(task1)
project1.add_task(task2)


# 3. Update Task Status
task1.change_status(TaskStatus.IN_PROGRESS)
task1.complete()

# Test invalid transition
task1.change_status(TaskStatus.TODO)


# 4. Show Tasks
print("=== TASK MANAGER ===")
print("Project:", project1.name)

displayer = TaskDisplayer()
displayer.show_task(project1)

print("Total tasks:", len(project1.tasks))
print("Priority:", task1.priority.value)


# 5. Test Notifiers
print("=== NOTIFICATIONS ===")

console1 = ConsoleNotifier()
email1 = EmailNotifier()

console1.send("Task completed")
email1.send("Task completed")
