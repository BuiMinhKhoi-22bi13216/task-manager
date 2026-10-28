import ast
import importlib.util
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from task_manager.exceptions import (
    InvalidTaskTypeError,
    TaskLockedError,
    TaskManagerError,
    TaskNotFoundError,
)
from task_manager.models import (
    PRIORITY_RANK,
    Task,
    TaskPriority,
    TaskStatus,
    User,
)
from task_manager.project import Project
from task_manager.strategies import PrioritySortStrategy
from task_manager.task_factory import TaskFactory
from task_manager.task_service import TaskService

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "SQL"
HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None


def build_sample_database(db_path: Path) -> None:
    """Tạo DB tạm từ đúng schema.sql và example_data.sql của dự án."""
    connection = sqlite3.connect(db_path)

    try:
        for name in ("schema.sql", "example_data.sql"):
            script = (SQL_DIR / name).read_text(encoding="utf-8")
            connection.executescript(script)

        connection.commit()
    finally:
        connection.close()


class TestSchemaMatchesDomain(unittest.TestCase):
    """Không cần SQLAlchemy: kiểm tra DB mẫu khớp với domain."""

    def setUp(self):
        self.connection = sqlite3.connect(":memory:")

        for name in ("schema.sql", "example_data.sql"):
            script = (SQL_DIR / name).read_text(encoding="utf-8")
            self.connection.executescript(script)

    def tearDown(self):
        self.connection.close()

    def test_sample_priorities_exist_in_domain(self):
        rows = self.connection.execute(
            "SELECT DISTINCT priority FROM tasks"
        ).fetchall()

        self.assertLessEqual(
            {priority for (priority,) in rows},
            set(PRIORITY_RANK.values()),
        )

    def test_sample_tasks_all_have_assignee(self):
        count = self.connection.execute(
            "SELECT COUNT(*) FROM tasks WHERE assignee_id IS NULL"
        ).fetchone()[0]

        self.assertEqual(count, 0)

    def test_schema_rejects_priority_outside_domain(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO tasks "
                "(project_id, title, task_type, priority, assignee_id) "
                "VALUES (1, 'x', 'bug', 4, 1)"
            )

    def test_schema_rejects_task_without_assignee(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO tasks "
                "(project_id, title, task_type, assignee_id) "
                "VALUES (1, 'x', 'bug', NULL)"
            )


class TestServiceIndependence(unittest.TestCase):
    """Không cần SQLAlchemy: tầng service không phụ thuộc ORM."""

    def test_task_service_does_not_import_sqlalchemy(self):
        source = (ROOT / "task_manager" / "task_service.py").read_text(
            encoding="utf-8"
        )
        imported: set[str] = set()

        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)

        forbidden = {
            "task_manager.task_repository",
            "task_manager.orm_models",
            "task_manager.database",
        }

        self.assertFalse(
            [name for name in imported if name.startswith("sqlalchemy")]
        )
        self.assertFalse(imported & forbidden)

    def test_get_task_without_repository_raises_domain_error(self):
        service = TaskService(PrioritySortStrategy())

        with self.assertRaises(TaskManagerError):
            service.get_task(1)


@unittest.skipUnless(HAS_SQLALCHEMY, "cần cài sqlalchemy")
class TestTaskRepository(unittest.TestCase):
    def setUp(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        from task_manager.task_repository import TaskRepository

        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / "test.db"
        build_sample_database(db_path)

        self.engine = create_engine(f"sqlite:///{db_path}")
        self.session = Session(self.engine)
        self.repository = TaskRepository(self.session)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()
        self._tmp.cleanup()

    def test_list_reads_sample_data_of_both_projects(self):
        ai_camera = self.repository.list("AI Camera")
        task_manager = self.repository.list("Task Manager")

        self.assertEqual(len(ai_camera), 5)
        self.assertEqual(len(task_manager), 5)

        first = ai_camera[0]
        self.assertEqual(first.title, "Sửa lỗi kết nối camera")
        self.assertEqual(first.priority, TaskPriority.HIGH)
        self.assertEqual(first.assignee, User("an"))
        self.assertEqual(first.deadline, date(2026, 10, 25))

        unassigned_in_old_data = ai_camera[4]
        self.assertEqual(unassigned_in_old_data.title, "Dọn thư mục log")
        self.assertEqual(unassigned_in_old_data.assignee, User("khoi"))

    def test_list_issues_no_n_plus_one_queries(self):
        from sqlalchemy import event

        statements: list[str] = []

        @event.listens_for(self.engine, "before_cursor_execute")
        def record(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        tasks = self.repository.list("AI Camera")

        self.assertEqual(len(tasks), 5)
        # 1 truy vấn tasks + 1 truy vấn users (selectinload), không phải 1 + N.
        self.assertLessEqual(len(statements), 2)

    def test_get_by_id_found_and_missing(self):
        task = self.repository.get_by_id(2)

        assert task is not None
        self.assertEqual(task.title, "Thêm chức năng chụp ảnh")
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertIsNone(self.repository.get_by_id(999))

    def test_add_then_get(self):
        task = TaskFactory.create_task("bug", "Task mới", User("linh"))

        task_id = self.repository.add("AI Camera", task)
        saved = self.repository.get_by_id(task_id)

        assert saved is not None
        self.assertEqual(saved.title, "Task mới")
        self.assertEqual(saved.task_type, "bug")
        self.assertEqual(saved.priority, TaskPriority.HIGH)
        self.assertEqual(saved.assignee, User("linh"))
        self.assertEqual(len(self.repository.list("AI Camera")), 6)

    def test_add_rejects_unknown_project(self):
        task = TaskFactory.create_task("bug", "x", User("khoi"))

        with self.assertRaises(TaskManagerError):
            self.repository.add("Không tồn tại", task)

    def test_add_rejects_unknown_assignee(self):
        task = TaskFactory.create_task("bug", "x", User("nguoi_la"))

        with self.assertRaises(TaskManagerError):
            self.repository.add("AI Camera", task)

    def test_add_rejects_task_type_not_in_schema(self):
        task = Task(
            "x",
            User("khoi"),
            TaskStatus.TODO,
            TaskPriority.LOW,
        )  # task_type mặc định là "general"

        with self.assertRaises(InvalidTaskTypeError):
            self.repository.add("AI Camera", task)

    def test_update_persists_changes_and_sets_updated_at(self):
        from task_manager.orm_models import TaskModel

        task = self.repository.get_by_id(1)
        assert task is not None

        task.change_status(TaskStatus.IN_PROGRESS)
        task.title = "Tiêu đề mới"
        self.repository.update(1, task)

        self.session.expire_all()
        reloaded = self.repository.get_by_id(1)

        assert reloaded is not None
        self.assertEqual(reloaded.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(reloaded.title, "Tiêu đề mới")

        row = self.session.get(TaskModel, 1)
        assert row is not None
        self.assertIsNotNone(row.updated_at)

    def test_assignment_is_current_in_same_and_new_session(self):
        from sqlalchemy.orm import Session

        from task_manager.orm_models import TaskModel
        from task_manager.task_repository import TaskRepository

        # Giữ ORM row và tải quan hệ cũ để tái hiện đúng lỗi đã review.
        row = self.session.get(TaskModel, 2)
        assert row is not None
        self.assertEqual(row.assignee.username, "khoi")

        task = self.repository.get_by_id(2)
        assert task is not None
        task.assign_to(User("linh"))
        self.repository.update(2, task)

        # Đọc trước commit/expire: không được trả lại người phụ trách cũ.
        reloaded = self.repository.get_by_id(2)
        assert reloaded is not None
        self.assertEqual(reloaded.assignee, User("linh"))
        self.assertEqual(row.assignee.username, "linh")
        self.assertEqual(row.assignee_id, row.assignee.id)

        self.session.commit()

        with Session(self.engine) as new_session:
            saved = TaskRepository(new_session).get_by_id(2)
            assert saved is not None
            self.assertEqual(saved.assignee, User("linh"))

    def test_update_missing_task_raises(self):
        task = TaskFactory.create_task("bug", "x", User("khoi"))

        with self.assertRaises(TaskNotFoundError):
            self.repository.update(999, task)

    def test_delete(self):
        self.assertTrue(self.repository.delete(1))
        self.assertIsNone(self.repository.get_by_id(1))
        self.assertFalse(self.repository.delete(1))

    def test_done_task_loaded_from_db_stays_locked(self):
        task = self.repository.get_by_id(3)

        assert task is not None
        self.assertEqual(task.status, TaskStatus.DONE)

        with self.assertRaises(TaskLockedError):
            task.title = "Không được sửa"


@unittest.skipUnless(HAS_SQLALCHEMY, "cần cài sqlalchemy")
class TestTaskServiceWithRepository(unittest.TestCase):
    def setUp(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        from task_manager.task_repository import TaskRepository

        self._tmp = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp.name) / "test.db"
        build_sample_database(db_path)

        self.engine = create_engine(f"sqlite:///{db_path}")
        self.session = Session(self.engine)
        self.service = TaskService(
            PrioritySortStrategy(),
            repository=TaskRepository(self.session),
        )
        self.project = Project("AI Camera")

    def tearDown(self):
        self.session.close()
        self.engine.dispose()
        self._tmp.cleanup()

    def test_add_and_sort_through_repository(self):
        task = TaskFactory.create_task("chore", "Việc nhẹ", User("khoi"))
        task_id = self.service.add_task(self.project, task)

        titles = [t.title for t in self.service.get_sorted_tasks(self.project)]

        self.assertEqual(len(titles), 6)
        self.assertEqual(titles[0], "Sửa lỗi kết nối camera")
        self.assertEqual(titles[-1], "Việc nhẹ")
        self.assertEqual(self.service.get_task(task_id).title, "Việc nhẹ")

    def test_get_task_missing_raises(self):
        with self.assertRaises(TaskNotFoundError):
            self.service.get_task(9999)


if __name__ == "__main__":
    unittest.main()

