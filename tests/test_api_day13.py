import os
import secrets
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from task_manager.api import app
from task_manager.dependencies import get_db
from task_manager.orm_models import TaskModel


class TestDay13API(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.db"

        sql_dir = Path(__file__).resolve().parents[1] / "SQL"
        connection = sqlite3.connect(self.path)
        try:
            for name in ("schema.sql", "example_data.sql"):
                connection.executescript((sql_dir / name).read_text(encoding="utf-8"))
            connection.commit()
        finally:
            connection.close()

        self.engine = create_engine(
            f"sqlite:///{self.path}", connect_args={"check_same_thread": False}
        )

        @event.listens_for(self.engine, "connect")
        def foreign_keys(conn, record):
            conn.execute("PRAGMA foreign_keys=ON")

        self.closed = 0

        def test_db():
            db = Session(self.engine)
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
                self.closed += 1

        app.dependency_overrides[get_db] = test_db

        env = patch.dict(os.environ, {"TASK_MANAGER_JWT_SECRET": secrets.token_hex(32)})
        env.start()
        self.addCleanup(env.stop)

        self.client = TestClient(app)
        self.headers = self.register_and_login("day14_api_test")
        self.client.headers.update(self.headers)

        self.project_id = self.client.post(
            "/projects", json={"name": "Day13 test", "owner_id": 1}
        ).json()["id"]

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()
        self.tmp.cleanup()

    def register_and_login(self, username):
        body = {
            "username": username,
            "email": f"{username}@example.com",
            "password": "VNPT_demo_14",
        }

        response = self.client.post("/auth/register", json=body)
        self.assertEqual(response.status_code, 201, response.text)

        response = self.client.post(
            "/auth/login",
            data={"username": username, "password": body["password"]},
        )
        self.assertEqual(response.status_code, 200, response.text)

        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def create_task(self, **changes):
        body = {
            "title": "Test",
            "project_id": self.project_id,
            "assignee": "khoi",
            "task_type": "chore",
        }
        body.update(changes)
        return self.client.post("/tasks", json=body)

    def test_task_crud(self):
        created = self.create_task()
        self.assertEqual(created.status_code, 201, created.text)

        task_id = created.json()["id"]
        self.assertEqual(self.client.get(f"/tasks/{task_id}").status_code, 200)

        updated = self.client.patch(f"/tasks/{task_id}", json={"title": "Edited"})
        self.assertEqual(updated.json()["title"], "Edited")

        self.assertEqual(self.client.delete(f"/tasks/{task_id}").status_code, 204)
        self.assertEqual(self.client.get(f"/tasks/{task_id}").status_code, 404)

    def test_project_crud_and_cascade(self):
        task_id = self.create_task().json()["id"]

        response = self.client.patch(
            f"/projects/{self.project_id}", json={"name": "Renamed"}
        )
        self.assertEqual(response.json()["name"], "Renamed")
        self.assertTrue(self.client.get("/projects").json())

        self.assertEqual(
            self.client.delete(f"/projects/{self.project_id}").status_code, 204
        )
        self.assertEqual(
            self.client.get(f"/projects/{self.project_id}").status_code, 404
        )
        self.assertEqual(self.client.get(f"/tasks/{task_id}").status_code, 404)

    def test_filter_sort_and_pagination(self):
        for priority in [1, 2, 3]:
            self.assertEqual(self.create_task(priority=priority).status_code, 201)

        query = "/tasks?status=TODO&sort_by=priority&order=desc&limit=2"
        first = self.client.get(query).json()
        second = self.client.get(query + "&offset=2").json()

        self.assertTrue(all(row["status"] == "TODO" for row in first + second))
        self.assertEqual(len(first), 2)
        self.assertFalse({r["id"] for r in first} & {r["id"] for r in second})
        self.assertEqual(
            [r["priority"] for r in first + second],
            sorted([r["priority"] for r in first + second], reverse=True),
        )
        self.assertEqual(self.client.get("/tasks?offset=999999").json(), [])

    def test_validation_and_uniform_errors(self):
        for url in [
            "/tasks/abc",
            "/tasks?limit=0",
            "/tasks?offset=-1",
            "/tasks?status=wrong",
            "/tasks?sort_by=wrong",
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(
                set(response.json()["error"]), {"code", "message", "details"}
            )

        self.assertEqual(self.client.post("/tasks", json={}).status_code, 422)

        task_id = self.create_task().json()["id"]
        self.assertEqual(
            self.client.patch(f"/tasks/{task_id}", json={"title": None}).status_code,
            422,
        )

    def test_domain_rules_and_rollback(self):
        task_id = self.create_task().json()["id"]
        url = f"/tasks/{task_id}"

        self.assertEqual(
            self.client.patch(url, json={"status": "DONE"}).status_code, 400
        )
        self.assertEqual(self.client.get(url).json()["status"], "TODO")

        self.assertEqual(
            self.client.patch(url, json={"status": "IN_PROGRESS"}).status_code, 200
        )

        # Changing status then failing title validation must roll back the DB write.
        self.assertEqual(
            self.client.patch(url, json={"title": "", "status": "DONE"}).status_code,
            400,
        )
        self.assertEqual(self.client.get(url).json()["status"], "IN_PROGRESS")

        self.assertEqual(
            self.client.patch(url, json={"status": "DONE"}).status_code, 200
        )
        self.assertEqual(
            self.client.patch(url, json={"title": "Locked"}).status_code, 400
        )
        self.assertEqual(
            self.client.patch(url, json={"status": "TODO"}).status_code, 400
        )

    def test_new_session_sees_committed_data(self):
        task_id = self.create_task().json()["id"]
        self.engine.dispose()

        with TestClient(app) as another_client:
            self.assertEqual(
                another_client.get(
                    f"/tasks/{task_id}", headers=self.headers
                ).status_code,
                200,
            )

        self.assertGreater(self.closed, 1)

    def test_invalid_references_and_same_project_name(self):
        self.assertEqual(self.create_task(assignee="missing_user").status_code, 400)
        self.assertEqual(self.create_task(project_id=999999).status_code, 404)

        second = self.client.post("/projects", json={"name": "Day13 test"})
        self.assertEqual(second.status_code, 201)
        self.assertEqual(
            self.create_task(project_id=second.json()["id"]).status_code, 201
        )

    def test_missing_token_on_task_apis(self):
        task_id = self.create_task().json()["id"]

        with TestClient(app) as anonymous:
            responses = [
                anonymous.get("/tasks"),
                anonymous.get(f"/tasks/{task_id}"),
                anonymous.post(
                    "/tasks",
                    json={
                        "title": "Anonymous",
                        "project_id": self.project_id,
                        "assignee": "khoi",
                    },
                ),
                anonymous.patch(f"/tasks/{task_id}", json={"title": "Anonymous"}),
                anonymous.delete(f"/tasks/{task_id}"),
            ]

            for response in responses:
                self.assertEqual(response.status_code, 401, response.text)
                self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_creator_assignee_and_outsider_permissions(self):
        assignee_headers = self.register_and_login("day14_assignee")
        outsider_headers = self.register_and_login("day14_outsider")

        created = self.create_task(assignee="day14_assignee")
        self.assertEqual(created.status_code, 201, created.text)
        task_id = created.json()["id"]
        url = f"/tasks/{task_id}"

        self.assertEqual(self.client.get(url).status_code, 200)

        with Session(self.engine) as db:
            row = db.get(TaskModel, task_id)
            self.assertIsNotNone(row)
            self.assertIsNotNone(row.creator_id)
            self.assertNotEqual(row.creator_id, row.assignee_id)

        self.assertEqual(
            self.client.get(url, headers=assignee_headers).status_code, 200
        )

        edited = self.client.patch(
            url, json={"title": "Assignee edit"}, headers=assignee_headers
        )
        self.assertEqual(edited.status_code, 200, edited.text)

        responses = [
            self.client.get(url, headers=outsider_headers),
            self.client.patch(
                url, json={"title": "Forbidden"}, headers=outsider_headers
            ),
            self.client.delete(url, headers=outsider_headers),
        ]

        for response in responses:
            self.assertEqual(response.status_code, 403, response.text)
            self.assertEqual(response.json()["error"]["code"], "PERMISSION_DENIED")
            self.assertEqual(
                response.json()["error"]["message"],
                "Bạn không có quyền truy cập task này",
            )

        self.assertEqual(self.client.get(url).json()["title"], "Assignee edit")
        self.assertEqual(self.client.get("/tasks", headers=outsider_headers).json(), [])

        private = self.client.post(
            "/tasks",
            headers=outsider_headers,
            json={
                "title": "Private",
                "project_id": self.project_id,
                "assignee": "day14_outsider",
            },
        )
        self.assertEqual(private.status_code, 201, private.text)

        visible = self.client.get("/tasks?limit=1", headers=outsider_headers).json()
        self.assertEqual([row["id"] for row in visible], [private.json()["id"]])
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_assignee_can_delete_task(self):
        headers = self.register_and_login("delete_assignee")

        created = self.create_task(assignee="delete_assignee")
        self.assertEqual(created.status_code, 201, created.text)
        url = f"/tasks/{created.json()['id']}"

        self.assertEqual(self.client.delete(url, headers=headers).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_invalid_and_expired_tokens(self):
        expired = jwt.encode(
            {
                "sub": "1",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            os.environ["TASK_MANAGER_JWT_SECRET"],
            algorithm="HS256",
        )

        for token in ("invalid-token", expired):
            with self.subTest(token=token):
                response = self.client.get(
                    "/tasks", headers={"Authorization": f"Bearer {token}"}
                )
                self.assertEqual(response.status_code, 401, response.text)
                self.assertEqual(response.headers["www-authenticate"], "Bearer")
                self.assertEqual(response.json()["error"]["code"], "HTTP_401")

    def test_null_creator_uses_assignee_permission(self):
        assignee_headers = self.register_and_login("null_creator_assignee")
        outsider_headers = self.register_and_login("null_creator_outsider")

        created = self.create_task(assignee="null_creator_assignee")
        self.assertEqual(created.status_code, 201, created.text)
        task_id = created.json()["id"]
        url = f"/tasks/{task_id}"

        with Session(self.engine) as db:
            row = db.get(TaskModel, task_id)
            self.assertIsNotNone(row)
            row.creator_id = None
            db.commit()

        self.assertEqual(
            self.client.get(url, headers=assignee_headers).status_code, 200
        )

        response = self.client.patch(
            url, headers=assignee_headers, json={"title": "Legacy edited"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["title"], "Legacy edited")

        for response in (
            self.client.get(url, headers=outsider_headers),
            self.client.patch(url, headers=outsider_headers, json={"title": "Denied"}),
            self.client.delete(url, headers=outsider_headers),
        ):
            self.assertEqual(response.status_code, 403, response.text)

        self.assertEqual(
            self.client.get(url, headers=assignee_headers).json()["title"],
            "Legacy edited",
        )