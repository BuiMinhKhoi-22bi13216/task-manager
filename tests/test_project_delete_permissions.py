import os
import secrets
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from task_manager.api import app
from task_manager.dependencies import get_db
from task_manager.security import create_access_token


class TestProjectDeletePermissions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "test.db"

        sql_dir = Path(__file__).resolve().parents[1] / "SQL"
        with sqlite3.connect(self.path) as db:
            for name in ("schema.sql", "example_data.sql"):
                db.executescript((sql_dir / name).read_text(encoding="utf-8"))

        self.engine = create_engine(
            f"sqlite:///{self.path}", connect_args={"check_same_thread": False}
        )
        self.addCleanup(self.engine.dispose)

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(conn, record):
            conn.execute("PRAGMA foreign_keys=ON")

        def test_db():
            with Session(self.engine) as db:
                try:
                    yield db
                    db.commit()
                except Exception:
                    db.rollback()
                    raise

        override = patch.dict(app.dependency_overrides, {get_db: test_db})
        override.start()
        self.addCleanup(override.stop)

        env = patch.dict(os.environ, {"TASK_MANAGER_JWT_SECRET": secrets.token_hex(32)})
        env.start()
        self.addCleanup(env.stop)

        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def headers(self, user_id):
        return {"Authorization": f"Bearer {create_access_token(user_id)}"}

    def counts(self, project_id):
        with sqlite3.connect(self.path) as db:
            project_count = db.execute(
                "SELECT COUNT(*) FROM projects WHERE id = ?", (project_id,)
            ).fetchone()[0]

            task_count = db.execute(
                "SELECT COUNT(*) FROM tasks WHERE project_id = ?", (project_id,)
            ).fetchone()[0]

        return project_count, task_count

    def create_project_with_tasks(self, participants):
        with sqlite3.connect(self.path) as db:
            cursor = db.execute(
                "INSERT INTO projects (name, owner_id) VALUES (?, ?)",
                ("Permission test", 1),
            )
            project_id = cursor.lastrowid

            for creator_id, assignee_id in participants:
                db.execute(
                    "INSERT INTO tasks "
                    "(project_id, title, task_type, creator_id, assignee_id) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (project_id, "Permission task", "chore", creator_id, assignee_id),
                )

        return project_id

    def test_anonymous_cannot_delete_project(self):
        response = self.client.delete("/projects/1")

        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(self.counts(1), (1, 5))

    def test_outsider_cannot_bypass_task_permission(self):
        headers = self.headers(3)

        self.assertEqual(
            self.client.delete("/tasks/1", headers=headers).status_code, 403
        )

        response = self.client.delete("/projects/1", headers=headers)

        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json()["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual(self.counts(1), (1, 5))

    def test_creator_of_all_tasks_can_delete_project(self):
        response = self.client.delete("/projects/1", headers=self.headers(1))

        self.assertEqual(response.status_code, 204, response.text)
        self.assertEqual(self.counts(1), (0, 0))

    def test_assignee_of_all_tasks_can_delete_project(self):
        project_id = self.create_project_with_tasks([(1, 2), (3, 2)])

        response = self.client.delete(
            f"/projects/{project_id}", headers=self.headers(2)
        )

        self.assertEqual(response.status_code, 204, response.text)
        self.assertEqual(self.counts(project_id), (0, 0))

    def test_one_forbidden_task_blocks_whole_delete(self):
        project_id = self.create_project_with_tasks([(1, 2), (2, 3)])

        response = self.client.delete(
            f"/projects/{project_id}", headers=self.headers(1)
        )

        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(self.counts(project_id), (1, 2))

    def test_null_creator_still_uses_assignee_permission(self):
        project_id = self.create_project_with_tasks([(None, 2)])
        url = f"/projects/{project_id}"

        self.assertEqual(
            self.client.delete(url, headers=self.headers(1)).status_code, 403
        )
        self.assertEqual(self.counts(project_id), (1, 1))

        self.assertEqual(
            self.client.delete(url, headers=self.headers(2)).status_code, 204
        )
        self.assertEqual(self.counts(project_id), (0, 0))

    def test_authenticated_user_can_delete_empty_project(self):
        project_id = self.create_project_with_tasks([])

        response = self.client.delete(
            f"/projects/{project_id}", headers=self.headers(2)
        )

        self.assertEqual(response.status_code, 204, response.text)
        self.assertEqual(self.counts(project_id), (0, 0))

    def test_missing_project_returns_404(self):
        response = self.client.delete("/projects/999999", headers=self.headers(1))

        self.assertEqual(response.status_code, 404, response.text)