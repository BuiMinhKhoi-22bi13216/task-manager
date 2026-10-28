from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from task_manager.database import engine
from task_manager.exceptions import (
    InvalidStatusTransitionError,
    TaskLockedError,
)
from task_manager.models import TaskStatus, User
from task_manager.notifier import ConsoleNotifier
from task_manager.orm_models import ProjectModel, TaskModel, UserModel
from task_manager.project import Project
from task_manager.strategies import PrioritySortStrategy
from task_manager.task_factory import TaskFactory
from task_manager.task_repository import TaskRepository
from task_manager.task_service import TaskService


def make_service(session: Session) -> TaskService:
    return TaskService(
        PrioritySortStrategy(),
        [ConsoleNotifier()],
        repository=TaskRepository(session),
    )


def main():
    with Session(engine) as session:
        initial_count = session.scalar(
            select(func.count()).select_from(TaskModel)
        )

        user_row = session.scalars(
            select(UserModel).order_by(UserModel.id)
        ).first()

        if user_row is None:
            raise RuntimeError("Cần user mẫu từ ngày 9")

        project_row = ProjectModel(
            name=f"Demo mục 3 {datetime.now().isoformat()}",
            owner_id=user_row.id,
        )
        session.add(project_row)
        session.flush()

        project_id = project_row.id
        project = Project(project_row.name)
        user = User(user_row.username)

        service = make_service(session)

        low_id = service.add_task(
            project,
            TaskFactory.create_task(
                "chore", "Task ưu tiên thấp", user
            ),
        )
        high_id = service.add_task(
            project,
            TaskFactory.create_task(
                "bug", "Task ưu tiên cao", user
            ),
        )

        titles = [
            task.title
            for task in service.get_sorted_tasks(project)
        ]

        assert titles == [
            "Task ưu tiên cao",
            "Task ưu tiên thấp",
        ]

        session.commit()
        print(
            "ĐẠT: add_task ghi DB, get_sorted_tasks "
            "đọc DB và sắp xếp đúng"
        )

    with Session(engine) as session:
        service = make_service(session)
        task = service.get_task(high_id)

        assert task.status == TaskStatus.TODO

        try:
            task.change_status(TaskStatus.DONE)
        except InvalidStatusTransitionError:
            print("ĐẠT: chặn TODO -> DONE")
        else:
            raise AssertionError(
                "Không chặn chuyển trạng thái sai"
            )

        task.change_status(TaskStatus.IN_PROGRESS)
        task.change_status(TaskStatus.DONE)

        try:
            task.title = "Không được sửa"
        except TaskLockedError:
            print("ĐẠT: task DONE vẫn bị khóa")
        else:
            raise AssertionError("Không khóa task DONE")

        service.update_task(high_id, task)
        session.commit()

    with Session(engine) as session:
        service = make_service(session)
        task = service.get_task(high_id)

        assert task.status == TaskStatus.DONE

        task.reopen()
        task.title = "Đã mở lại và sửa"

        service.update_task(high_id, task)
        session.commit()

    with Session(engine) as session:
        service = make_service(session)
        task = service.get_task(high_id)

        assert task.status == TaskStatus.IN_PROGRESS
        assert task.title == "Đã mở lại và sửa"

        print(
            "ĐẠT: đọc Session mới, trạng thái "
            "và tiêu đề được lưu đúng"
        )

        repository = TaskRepository(session)

        assert repository.delete(low_id)
        assert repository.delete(high_id)

        project_row = session.get(ProjectModel, project_id)
        assert project_row is not None

        session.delete(project_row)
        session.commit()

    with Session(engine) as session:
        repository = TaskRepository(session)

        assert repository.get_by_id(high_id) is None

        final_count = session.scalar(
            select(func.count()).select_from(TaskModel)
        )
        assert final_count == initial_count

    print(
        "TÍCH HỢP ĐẠT; đã xóa hai task và project thử."
    )


if __name__ == "__main__":
    main()