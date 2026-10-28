import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "SQL" / "task_manager.db"

if not DB_PATH.is_file():
    raise FileNotFoundError(f"Không tìm thấy database: {DB_PATH}")

# Log SQL mặc định TẮT. Bật bằng: TASK_MANAGER_SQL_ECHO=1 python <script>
SQL_ECHO = os.getenv("TASK_MANAGER_SQL_ECHO", "").lower() in {"1", "true", "yes"}

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=SQL_ECHO,
)


@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()
