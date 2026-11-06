import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext  # type: ignore[import-untyped]

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


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
    secret = os.environ.get("TASK_MANAGER_JWT_SECRET")
    if not secret:
        raise RuntimeError("Chưa đặt biến môi trường TASK_MANAGER_JWT_SECRET")
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at}, secret, algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> dict[str, Any]:
    secret = os.environ.get("TASK_MANAGER_JWT_SECRET")
    if not secret:
        raise RuntimeError("Chưa đặt biến môi trường TASK_MANAGER_JWT_SECRET")
    return jwt.decode(
        token,
        secret,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "exp"]},
    )