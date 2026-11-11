import logging
from collections.abc import Iterator

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .auth_service import AuthService
from .database import engine
from .orm_models import UserModel
from .project_repository import ProjectRepository
from .project_service import ProjectService
from .security import decode_access_token
from .strategies import PrioritySortStrategy
from .task_cache import invalidate
from .task_repository import TaskRepository
from .task_service import TaskService
from .user_repository import UserRepository

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_db() -> Iterator[Session]:
    db = Session(engine)
    try:
        yield db
        db.commit()
        invalidate(db.info.get("task_cache_scopes", ()))
    except Exception:
        db.rollback()
        for path in db.info.get("pending_uploads", []):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                logger.exception("Không thể dọn file upload: %s", path)
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
    return TaskService(
        PrioritySortStrategy(),
        repository=repository,
    )


def get_project_repository(
    db: Session = Depends(get_db, scope="function"),
) -> ProjectRepository:
    return ProjectRepository(db)


def get_project_service(
    repository: ProjectRepository = Depends(get_project_repository),
) -> ProjectService:
    return ProjectService(repository)


def get_user_repository(
    db: Session = Depends(get_db, scope="function"),
) -> UserRepository:
    return UserRepository(db)


def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(repository)


def invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_token_user_id(
    token: str = Depends(oauth2_scheme),
) -> int:
    try:
        payload = decode_access_token(token)
        return int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise invalid_credentials() from exc


def get_current_user(
    user_id: int = Depends(get_token_user_id),
    repository: UserRepository = Depends(get_user_repository),
) -> UserModel:
    user = repository.get_by_id(user_id)
    if user is None:
        raise invalid_credentials()
    return user