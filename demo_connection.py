from sqlalchemy import text

from task_manager.database import DB_PATH, engine


def main():
    print(f"Database đang dùng: {DB_PATH}")

    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT 'users' AS table_name, COUNT(*) AS total FROM users
                UNION ALL
                SELECT 'projects', COUNT(*) FROM projects
                UNION ALL
                SELECT 'tasks', COUNT(*) FROM tasks
                """
            )
        )

        for table_name, total in result:
            print(f"{table_name}: {total} bản ghi")


if __name__ == "__main__":
    main()