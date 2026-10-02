"""Run: python -m unittest backend.test_workouts (no Firebase access)."""

import unittest
from copy import deepcopy
from unittest.mock import patch

from fastapi.testclient import TestClient
from google.api_core.exceptions import AlreadyExists

from backend.main import app


class MemoryStore:
    def __init__(self):
        self.records = {}

    def collection(self, name):
        assert name == "workouts"
        return self

    def document(self, day):
        store = self

        class Document:
            def create(self, record, timeout):
                if day in store.records:
                    raise AlreadyExists("duplicate")
                store.records[day] = deepcopy(record)

        return Document()


class WorkoutTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.patch = patch("backend.main.get_firestore_client", return_value=self.store)
        self.factory = self.patch.start()
        self.addCleanup(self.patch.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.record = {"date": "2026-09-28", "value": 60, "memo": "  exercise  "}

    def test_create_and_duplicate_preserves_original(self):
        response = self.client.post("/workouts", json=self.record)
        self.assertEqual(response.status_code, 201)
        expected = {**self.record, "memo": "exercise"}
        self.assertEqual(response.json(), expected)
        response = self.client.post("/workouts", json={**self.record, "value": 1})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.store.records, {self.record["date"]: expected})

    def test_invalid_inputs_never_access_storage(self):
        invalid = [
            ("date", "2026-02-30"), ("date", "2026-9-28"),
            ("date", "20260928"), ("date", "2026-09-28T00:00:00"),
            ("value", -1), ("value", 1441), ("value", 1.5),
            ("value", True), ("value", "60"),
            ("memo", "x" * 501), ("memo", 123),
        ]
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                self.assertEqual(self.client.post("/workouts", json={**self.record, field: value}).status_code, 422)
        self.factory.assert_not_called()

    def test_boundary_inputs(self):
        for day, value in [("2028-02-29", 0), ("2026-09-28", 1440)]:
            self.assertEqual(self.client.post("/workouts", json={"date": day, "value": value, "memo": "x" * 500}).status_code, 201)

    def test_storage_failure_is_sanitized(self):
        self.factory.side_effect = RuntimeError("internal detail must not escape")
        response = self.client.post("/workouts", json=self.record)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("internal detail", response.text)

    def test_post_cors(self):
        for origin in ["http://localhost:5500", "http://127.0.0.1:5500"]:
            response = self.client.options("/workouts", headers={"Origin": origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["access-control-allow-origin"], origin)
            self.assertIn("POST", response.headers["access-control-allow-methods"])
        response = self.client.options("/workouts", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_invalid_lookup_never_accesses_storage(self):
        for day in ["2026-02-30", "20260928", "2026-9-28"]:
            self.assertEqual(self.client.get(f"/workouts/{day}").status_code, 422)
        self.factory.assert_not_called()

    def test_read_failures_are_sanitized(self):
        self.factory.side_effect = RuntimeError("internal credential detail")
        for path in ["/workouts", "/workouts/summary", "/workouts/2026-09-28", "/workouts/ai-analysis"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("internal credential", response.text)

    def test_empty_summary(self):
        with patch("backend.main._read_workouts", return_value=[]):
            response = self.client.get("/workouts/summary")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_records"], 0)
        self.assertIsNone(response.json()["average_value"])


if __name__ == "__main__":
    unittest.main()
