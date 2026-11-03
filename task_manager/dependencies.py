from collections.abc import Iterator

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import engine
from .project_repository import ProjectRepository
from .project_service import ProjectService
from .strategies import PrioritySortStrategy
from .task_repository import TaskRepository
from .task_service import TaskService


def get_db() -> Iterator[Session]:
    db = Session(engine)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_task_repository(
    db: Session = Depends(get_db, scope="function"),
) -> TaskRepository:
    return TaskRepository(db)


def get_task_service(
    repository: TaskRepository = Depends(get_task_repository),
) -> TaskService:
    return TaskService(PrioritySortStrategy(), repository=repository)


def get_project_repository(
    db: Session = Depends(get_db, scope="function"),
) -> ProjectRepository:
    return ProjectRepository(db)


def get_project_service(
    repository: ProjectRepository = Depends(get_project_repository),
) -> ProjectService:
    return ProjectService(repository)
