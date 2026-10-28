from sqlalchemy import select
from sqlalchemy.orm import Session

from task_manager.database import engine
from task_manager.orm_models import TaskModel


def main():
    with Session(engine) as session:
        statement = (
            select(TaskModel)
            .order_by(TaskModel.id)
            .limit(3)
        )

        tasks = session.scalars(statement).all()

        for task in tasks:
            print(
                f"ID={task.id} | "
                f"Tiêu đề={task.title} | "
                f"Trạng thái={task.status} | "
                f"Ưu tiên={task.priority}"
            )


if __name__ == "__main__":
    main()