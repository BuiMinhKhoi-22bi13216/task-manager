from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL

from .config import PROJECT_ROOT, load_settings

settings = load_settings()
DB_PATH = PROJECT_ROOT / settings.db_path

if not DB_PATH.is_file():
    raise FileNotFoundError(f"Không tìm thấy database: {DB_PATH}")

engine = create_engine(
    URL.create("sqlite", database=str(DB_PATH)),
    echo=settings.sql_echo,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()