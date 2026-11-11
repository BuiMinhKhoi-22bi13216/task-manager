import logging
from collections.abc import Callable
from typing import TypeVar
from uuid import uuid4

from pydantic import TypeAdapter
from redis import Redis
from redis.exceptions import RedisError

from .config import load_settings

logger = logging.getLogger("uvicorn.error")
T = TypeVar("T")
TTL_SECONDS = 60
prefix = f"task-manager:{uuid4().hex}"
redis_url = load_settings().redis_url
client = (
    Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_timeout=1,
        socket_connect_timeout=1,
    )
    if redis_url
    else None
)


def cache_enabled() -> bool:
    return client is not None


def cached(
    scope: str,
    variant: str,
    adapter: TypeAdapter[T],
    load: Callable[[], T],
) -> T:
    redis = client
    if redis is None:
        return load()

    scope_key = f"{prefix}:{scope}"
    marker = f"{scope_key}:revision"
    revision = uuid4().hex

    try:
        # Lấy phiên bản cũ, hoặc tạo phiên bản nếu nhóm chưa có.
        previous = redis.set(
            marker,
            revision,
            nx=True,
            get=True,
            ex=TTL_SECONDS,
        )
        if isinstance(previous, str):
            revision = previous

        key = f"{scope_key}:{revision}:{variant}"
        value = redis.get(key)
    except RedisError:
        logger.warning("CACHE BYPASS %s", scope)
        return load()

    if isinstance(value, str):
        logger.info("CACHE HIT %s", scope)
        return adapter.validate_json(value)

    logger.info("CACHE MISS %s", scope)
    result = load()

    try:
        redis.set(
            key,
            adapter.dump_json(result),
            ex=TTL_SECONDS,
        )
    except RedisError:
        logger.warning("CACHE STORE FAILED %s", scope)

    return result


def invalidate(scopes: tuple[str, ...] | None) -> None:
    global client, prefix

    redis = client
    if redis is None:
        return

    if scopes is None:
        # Xóa project có thể làm SQLite xóa các task liên quan.
        prefix = f"task-manager:{uuid4().hex}"
        logger.info("CACHE RESET after project deletion")
        return

    if not scopes:
        return

    markers = [
        f"{prefix}:{scope}:revision"
        for scope in scopes
    ]

    try:
        # Phiên bản mới khiến mọi biến thể cũ mất hiệu lực.
        redis.delete(*markers)
        logger.info("CACHE INVALIDATE %s", ", ".join(scopes))
    except RedisError:
        # SQLite đã commit. Đọc trực tiếp tới khi API khởi động lại.
        client = None
        logger.warning(
            "CACHE DISABLED after invalidation failed",
            exc_info=True,
        )