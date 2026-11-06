from .exceptions import InvalidDataError
from .security import create_access_token, hash_password, verify_password
from .user_repository import UserRepository


class AuthService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    def register(
        self, username: str, email: str, password: str, full_name: str | None
    ) -> str:
        if self._repository.get_by_username(username) is not None:
            raise InvalidDataError("Username đã tồn tại")
        if self._repository.get_by_email(email) is not None:
            raise InvalidDataError("Email đã tồn tại")
        user = self._repository.add(
            username, email, hash_password(password), full_name
        )
        return create_access_token(user.id)

    def login(self, username: str, password: str) -> str | None:
        user = self._repository.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return create_access_token(user.id)