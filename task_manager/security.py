from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext  # type: ignore[import-untyped]

from .config import load_settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return str(password_context.hash(password))


def verify_password(password: str, password_hash: str) -> bool:
    if len(password.encode("utf-8")) > 72 or "\x00" in password:
        return False
    try:
        return bool(password_context.verify(password, password_hash))
    except ValueError:
        # Các tài khoản mẫu cũ chưa có hash hợp lệ: từ chối đăng nhập.
        return False


def create_access_token(user_id: int) -> str:
    settings = load_settings()
    secret = settings.jwt_secret.get_secret_value()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.token_expire_minutes
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at}, secret, algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> dict[str, Any]:
    settings = load_settings()
    secret = settings.jwt_secret.get_secret_value()
    return jwt.decode(
        token,
        secret,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "exp"]},
    )