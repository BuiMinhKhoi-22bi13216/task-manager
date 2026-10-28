import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "SQL" / "task_manager.db"


def find_user_unsafe(username):
    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.cursor()

        # Cố ý viết sai để minh họa SQL Injection.
        sql = (
            "SELECT id, username FROM users "
            f"WHERE username = '{username}';"
        )

        print("SQL nối chuỗi:", sql)

        cursor.execute(sql)

        return cursor.fetchall()

    finally:
        connection.close()


def find_user_safe(username):
    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, username FROM users WHERE username = ?;",
            (username,)
        )

        return cursor.fetchall()

    finally:
        connection.close()


if __name__ == "__main__":
    normal_input = "khoi"
    injection_input = "' OR 1=1 --"

    print("=== ĐẦU VÀO BÌNH THƯỜNG ===")

    print("Nối chuỗi:", find_user_unsafe(normal_input))
    print("Tham số hóa:", find_user_safe(normal_input))

    print("\n=== ĐẦU VÀO SQL INJECTION ===")

    print("Nối chuỗi:", find_user_unsafe(injection_input))
    print("Tham số hóa:", find_user_safe(injection_input))
