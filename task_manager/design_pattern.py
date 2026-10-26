from datetime import date

from .builder import TaskBuilder
from .external_sms import ExternalSMSService
from .models import Task, TaskPriority, User
from .project import Project
from .sms_adapter import SMSAdapter
from .task_factory import TaskFactory


def main() -> None:
    print("=== TASK MANAGER - DAY 5 ===")

    user1 = User("An")
    project = Project("Intern Project")

    bug = TaskFactory.create_task("bug", "Fix login", user1)

    print("Factory:", bug.task_type, bug.priority)

    task = (
        TaskBuilder.from_task(bug)
        .set_description("Sua loi dang nhap")
        .set_deadline(date(2026, 10, 20))
        .build()
    )

    print("Builder:", task.description, task.deadline)

    project.add_task(task)

    sms_service = ExternalSMSService()
    notifier = SMSAdapter(sms_service, "0901234567")

    notifier.send(f"New {task.task_type} task: {task.title}")

    assert isinstance(task, Task)
    assert task.task_type == "bug"
    assert task.priority == TaskPriority.HIGH
    assert task.description == "Sua loi dang nhap"
    assert task.deadline == date(2026, 10, 20)
    assert task in project.tasks
    assert sms_service.sent_messages == [("0901234567", "New bug task: Fix login")]

    print("INTEGRATION TEST: PASS")


if __name__ == "__main__":
    main()