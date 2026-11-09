import unittest

from fastapi.testclient import TestClient

from task_manager.api import app

ORIGIN = "http://localhost:3000"


def preflight(client, origin):
    return client.options(
        "/tasks/1",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )


class TestMiddlewareAndCors(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_timing_header_on_401_and_404(self):
        for path, status in (("/tasks", 401), ("/khong-ton-tai", 404)):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, status, response.text)
                self.assertGreaterEqual(
                    float(response.headers["x-process-time-ms"]), 0
                )

    def test_log_line(self):
        with self.assertLogs("uvicorn.error", level="INFO") as logs:
            self.client.get("/tasks")

        self.assertTrue(
            any("GET /tasks status=401 duration_ms=" in line for line in logs.output)
        )

    def test_preflight_allowed_also_gets_timing_header(self):
        response = preflight(self.client, ORIGIN)

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["access-control-allow-origin"], ORIGIN)
        self.assertGreaterEqual(float(response.headers["x-process-time-ms"]), 0)

        allowed_headers = {
            name.strip().lower()
            for name in response.headers["access-control-allow-headers"].split(",")
        }
        self.assertTrue({"authorization", "content-type"} <= allowed_headers)

        allowed_methods = {
            name.strip()
            for name in response.headers["access-control-allow-methods"].split(",")
        }
        self.assertIn("PATCH", allowed_methods)

    def test_preflight_disallowed(self):
        response = preflight(self.client, "http://localhost:9999")

        self.assertEqual(response.status_code, 400, response.text)
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_allowed_origin_still_needs_token(self):
        response = self.client.get("/tasks", headers={"Origin": ORIGIN})

        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(response.headers["access-control-allow-origin"], ORIGIN)

        exposed_headers = {
            name.strip().lower()
            for name in response.headers["access-control-expose-headers"].split(",")
        }
        self.assertIn("x-process-time-ms", exposed_headers)

    def test_unknown_origin_actual_request(self):
        response = self.client.get(
            "/tasks", headers={"Origin": "http://localhost:9999"}
        )

        self.assertEqual(response.status_code, 401, response.text)
        self.assertNotIn("access-control-allow-origin", response.headers)
        self.assertIn("x-process-time-ms", response.headers)

    def test_no_origin_no_cors_headers(self):
        response = self.client.get("/tasks")

        self.assertEqual(response.status_code, 401, response.text)
        self.assertNotIn("access-control-allow-origin", response.headers)