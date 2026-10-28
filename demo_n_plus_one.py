from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from task_manager.database import engine
from task_manager.models import User
from task_manager.orm_models import ProjectModel, UserModel
from task_manager.task_factory import TaskFactory
from task_manager.task_repository import TaskRepository


def main():
    # Bật log SQL cho demo (mặc định database.py tắt echo).
    engine.echo = True

    # Chuẩn bị ba task giao cho ba user có sẵn.
    with Session(engine) as session:
        usernames = session.scalars(
            select(UserModel.username)
            .order_by(UserModel.id)
            .limit(3)
        ).all()

        if len(usernames) < 3:
            raise RuntimeError(
                "Demo cần ít nhất 3 user có sẵn từ ngày 9"
            )

        project = ProjectModel(
            name=f"Demo N+1 {datetime.now().isoformat()}"
        )
        session.add(project)
        session.flush()

        project_id = project.id
        project_name = project.name

        repository = TaskRepository(session)
        task_ids = []

        for number, username in enumerate(usernames, start=1):
            task = TaskFactory.create_task(
                "chore",
                f"Task N+1 số {number}",
                User(username),
            )

            task_id = repository.add(project_name, task)
            task_ids.append(task_id)

        session.commit()

    try:
        # Session mới để dữ liệu chuẩn bị không che mất N+1.
        print(
            "\n=== BẮT ĐẦU ĐỌC DANH SÁCH ===",
            flush=True,
        )

        with Session(engine) as session:
            repository = TaskRepository(session)
            tasks = repository.list(project_name)

            assert len(tasks) == 3
            assert [
                task.assignee.name for task in tasks
            ] == list(usernames)

            for task in tasks:
                print(
                    f"{task.title} | "
                    f"assignee={task.assignee.name}"
                )

        print(
            "=== KẾT THÚC ĐỌC DANH SÁCH ===\n",
            flush=True,
        )

    finally:
        # Dọn đúng các bản ghi vừa tạo cho demo.
        with Session(engine) as session:
            repository = TaskRepository(session)

            for task_id in task_ids:
                repository.delete(task_id)

            project = session.get(ProjectModel, project_id)

            if project is not None:
                session.delete(project)

            session.commit()

        print("Đã dọn ba task và project thử.")


if __name__ == "__main__":
    main()
