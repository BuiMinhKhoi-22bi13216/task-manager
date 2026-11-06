from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .exceptions import InvalidDataError
from .orm_models import UserModel


class UserRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, user_id: int) -> UserModel | None:
        return self._session.get(UserModel, user_id)

    def get_by_username(self, username: str) -> UserModel | None:
        return self._session.scalar(
            select(UserModel).where(UserModel.username == username)
        )

    def get_by_email(self, email: str) -> UserModel | None:
        return self._session.scalar(
            select(UserModel).where(UserModel.email == email)
        )

    def add(
        self,
        username: str,
        email: str,
        password_hash: str,
        full_name: str | None,
    ) -> UserModel:
        user = UserModel(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
        )
        self._session.add(user)
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise InvalidDataError("Username hoặc email đã tồn tại") from exc
        return user