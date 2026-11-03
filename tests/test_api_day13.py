import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from task_manager.api import app
from task_manager.dependencies import get_db


class TestDay13API(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.db"
        source = Path(__file__).resolve().parents[1] / "SQL/task_manager.db"
        shutil.copy2(source, self.path)
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
        self.client = TestClient(app)
        self.project_id = self.client.post(
            "/projects", json={"name": "Day13 test", "owner_id": 1}
        ).json()["id"]

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()
        self.tmp.cleanup()

    def create_task(self, **changes):
        body = {
            "title": "Test", "project_id": self.project_id,
            "assignee": "khoi", "task_type": "chore",
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
        self.assertEqual(self.client.delete(f"/projects/{self.project_id}").status_code, 204)
        self.assertEqual(self.client.get(f"/projects/{self.project_id}").status_code, 404)
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
        self.assertEqual([r["priority"] for r in first + second],
                         sorted([r["priority"] for r in first + second], reverse=True))
        self.assertEqual(self.client.get("/tasks?offset=999999").json(), [])

    def test_validation_and_uniform_errors(self):
        for url in ["/tasks/abc", "/tasks?limit=0", "/tasks?offset=-1",
                    "/tasks?status=wrong", "/tasks?sort_by=wrong"]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(set(response.json()["error"]), {"code", "message", "details"})
        self.assertEqual(self.client.post("/tasks", json={}).status_code, 422)
        task_id = self.create_task().json()["id"]
        self.assertEqual(self.client.patch(f"/tasks/{task_id}", json={"title": None}).status_code, 422)

    def test_domain_rules_and_rollback(self):
        task_id = self.create_task().json()["id"]
        url = f"/tasks/{task_id}"
        self.assertEqual(self.client.patch(url, json={"status": "DONE"}).status_code, 400)
        self.assertEqual(self.client.get(url).json()["status"], "TODO")
        self.assertEqual(self.client.patch(url, json={"status": "IN_PROGRESS"}).status_code, 200)
        # Changing status then failing title validation must roll back the DB write.
        self.assertEqual(self.client.patch(url, json={"title": "", "status": "DONE"}).status_code, 400)
        self.assertEqual(self.client.get(url).json()["status"], "IN_PROGRESS")
        self.assertEqual(self.client.patch(url, json={"status": "DONE"}).status_code, 200)
        self.assertEqual(self.client.patch(url, json={"title": "Locked"}).status_code, 400)
        self.assertEqual(self.client.patch(url, json={"status": "TODO"}).status_code, 400)

    def test_new_session_sees_committed_data(self):
        task_id = self.create_task().json()["id"]
        self.engine.dispose()
        with TestClient(app) as another_client:
            self.assertEqual(another_client.get(f"/tasks/{task_id}").status_code, 200)
        self.assertGreater(self.closed, 1)

    def test_invalid_references_and_same_project_name(self):
        self.assertEqual(self.create_task(assignee="missing_user").status_code, 400)
        self.assertEqual(self.create_task(project_id=999999).status_code, 404)
        second = self.client.post("/projects", json={"name": "Day13 test"})
        self.assertEqual(second.status_code, 201)
        self.assertEqual(self.create_task(project_id=second.json()["id"]).status_code, 201)
