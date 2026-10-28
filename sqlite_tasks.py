"""CRUD cho bảng tasks bằng module sqlite3 thuần (Ngày 9).

Mọi câu lệnh đều được tham số hóa bằng dấu ? để tránh SQL Injection.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "SQL" / "task_manager.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)

    # SQLite mặc định KHÔNG kiểm tra khóa ngoại; phải bật cho từng kết nối.
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


def get_task(task_id):
    connection = _connect()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM tasks WHERE id = ?;",
            (task_id,)
        )

        return cursor.fetchone()

    finally:
        connection.close()


def create_task(
    project_id,
    title,
    task_type,
    creator_id,
    assignee_id,
    description=None,
    status="TODO",
    priority=2,
    due_date=None
):
    connection = _connect()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO tasks (
                project_id,
                title,
                description,
                task_type,
                status,
                priority,
                creator_id,
                assignee_id,
                due_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                project_id,
                title,
                description,
                task_type,
                status,
                priority,
                creator_id,
                assignee_id,
                due_date
            )
        )

        new_task_id = cursor.lastrowid

        connection.commit()

        return new_task_id

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_task(task_id, description):
    connection = _connect()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE tasks
            SET description = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (description, task_id)
        )

        updated_count = cursor.rowcount

        connection.commit()

        return updated_count

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_task(task_id):
    connection = _connect()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM tasks WHERE id = ?;",
            (task_id,)
        )

        deleted_count = cursor.rowcount

        connection.commit()

        return deleted_count

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    # Demo đủ 4 thao tác CRUD trên một task tạm, rồi dọn lại.
    new_id = create_task(
        project_id=1,
        title="Task demo CRUD",
        task_type="chore",
        creator_id=1,
        assignee_id=1,
        description="Mô tả ban đầu",
    )
    print("Đã tạo task id =", new_id)
    print("Đọc lại      :", get_task(new_id))

    print("Số hàng sửa  :", update_task(new_id, "Mô tả đã sửa"))
    print("Sau khi sửa  :", get_task(new_id))

    print("Số hàng xóa  :", delete_task(new_id))
    print("Sau khi xóa  :", get_task(new_id))

