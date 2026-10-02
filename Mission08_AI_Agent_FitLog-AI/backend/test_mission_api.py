"""Offline regression tests. Firebase factory is blocked in every test."""
from copy import deepcopy
from datetime import date, timedelta
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from google.api_core.exceptions import AlreadyExists, NotFound

from backend.main import app
from backend.migrate_workouts import copy_workouts
from backend.routers.data import get_data_service
from backend.routers.conversations import get_conversation_service
from backend.services.data_service import DataService
from backend.services.conversation_service import ConversationService
from backend.services.repository import DuplicateRecord, FirestoreRepository, MissingRecord, ServiceError


class MemoryRepository:
    def __init__(self):
        self.rows = {}

    def list(self):
        return deepcopy(list(self.rows.values()))

    def get(self, id):
        if id not in self.rows:
            raise MissingRecord()
        return deepcopy(self.rows[id])

    def create(self, id, row):
        if id in self.rows:
            raise DuplicateRecord()
        self.rows[id] = {**deepcopy(row), "id": id}

    def update(self, id, row):
        self.get(id)
        self.rows[id] = {**deepcopy(row), "id": id}

    def delete(self, id):
        self.get(id)
        del self.rows[id]


class MissionAPITests(unittest.TestCase):
    def setUp(self):
        self.block = patch("backend.services.repository.get_firestore_client", side_effect=AssertionError("No real Firestore"))
        self.block.start()
        self.addCleanup(self.block.stop)
        self.data = MemoryRepository()
        self.conversations = MemoryRepository()
        app.dependency_overrides[get_data_service] = lambda: DataService(self.data)
        app.dependency_overrides[get_conversation_service] = lambda: ConversationService(self.conversations)
        self.addCleanup(app.dependency_overrides.clear)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.row = {"date": "2026-09-28", "value": 60, "memo": "  웨이트  "}
        self.conversation = {"title": "  운동 기록  ", "messages": [{"role": "user", "content": "  안녕하세요  "}, {"role": "assistant", "content": "반갑습니다"}]}

    def test_data_create_and_duplicate(self):
        response = self.client.post("/api/data", json=self.row)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {**self.row, "memo": "웨이트", "id": self.row["date"]})
        before = deepcopy(self.data.rows)
        self.assertEqual(self.client.post("/api/data", json={**self.row, "value": 1}).status_code, 409)
        self.assertEqual(self.data.rows, before)

    def test_data_validation_on_post_and_put(self):
        for key, value in [("date", "2026-02-30"), ("date", "20260928"), ("date", "2026-9-28"), ("value", -1), ("value", 1441), ("value", True), ("value", 1.2), ("value", "60"), ("memo", 5), ("memo", "x" * 501)]:
            for method, path in [("post", "/api/data"), ("put", "/api/data/2026-09-28")]:
                with self.subTest(method=method, key=key, value=value):
                    response = getattr(self.client, method)(path, json={**self.row, key: value})
                    self.assertEqual(response.status_code, 422)
        self.assertEqual(self.data.rows, {})

    def test_data_list_sorted(self):
        for day in ["2026-09-28", "2026-09-20", "2026-09-25"]:
            self.client.post("/api/data", json={**self.row, "date": day})
        result = self.client.get("/api/data").json()
        self.assertEqual([r["date"] for r in result], ["2026-09-20", "2026-09-25", "2026-09-28"])
        self.assertTrue(all(r["id"] == r["date"] for r in result))

    def test_update_missing_and_date_mismatch(self):
        url = "/api/data/2026-09-28"
        self.assertEqual(self.client.put(url, json=self.row).status_code, 404)
        self.client.post("/api/data", json=self.row)
        changed = {**self.row, "value": 0, "memo": " 휴식 "}
        response = self.client.put(url, json=changed)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["memo"], "휴식")
        self.assertEqual(self.client.put(url, json={**changed, "date": "2026-09-29"}).status_code, 422)
        self.assertEqual(len(self.data.rows), 1)
        self.assertEqual(self.data.rows["2026-09-28"]["value"], 0)

    def test_delete_success_missing_and_invalid_id(self):
        self.client.post("/api/data", json=self.row)
        response = self.client.delete("/api/data/2026-09-28")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertEqual(self.client.delete("/api/data/2026-09-28").status_code, 404)
        self.assertEqual(self.client.delete("/api/data/2026-02-30").status_code, 422)

    def test_summary_calendar_trend_and_all_time_metrics(self):
        for i in range(15):
            day = (date(2026, 9, 14) + timedelta(days=i)).isoformat()
            self.data.create(day, {"date": day, "value": 100 if i == 0 else 10 if i < 8 else 20, "memo": "운동"})
        response = self.client.get("/api/data/summary")
        self.assertEqual(response.status_code, 200)
        s = response.json()
        self.assertEqual(s["period"], {"start": "2026-09-14", "end": "2026-09-28"})
        self.assertEqual(s["count"], 15)
        self.assertEqual(s["metrics"], {"total": 310, "average": 20.67, "max": 100, "min": 10})
        self.assertEqual(s["trend"]["absolute_change"], 70)
        self.assertEqual(s["trend"]["percent_change"], 100)
        self.assertEqual(s["trend"]["direction"], "increase")
        self.assertEqual(s["trend"]["previous_period"], {"start": "2026-09-15", "end": "2026-09-21"})

    def test_empty_summary_and_zero_denominator(self):
        s = self.client.get("/api/data/summary").json()
        self.assertEqual(s["count"], 0)
        self.assertEqual(s["metrics"], {"total": 0, "average": None, "max": None, "min": None})
        self.assertEqual(s["trend"]["direction"], "no_data")
        self.client.post("/api/data", json=self.row)
        s = self.client.get("/api/data/summary").json()
        self.assertIsNone(s["trend"]["percent_change"])
        self.assertEqual(s["trend"]["previous_record_count"], 0)
        self.assertEqual(s["trend"]["recent_record_count"], 1)

    def test_summary_earliest_valid_date(self):
        self.client.post("/api/data", json={**self.row, "date": "0001-01-01"})
        response = self.client.get("/api/data/summary")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["trend"]["previous_period"]["end"])

    def test_conversation_lifecycle(self):
        response = self.client.post("/api/conversations", json=self.conversation)
        self.assertEqual(response.status_code, 201)
        row = response.json()
        self.assertEqual(row["title"], "운동 기록")
        self.assertEqual(row["messages"][0]["content"], "안녕하세요")
        self.assertEqual(row["created_at"], row["updated_at"])
        self.assertEqual(len(row["id"]), 32)
        listing = self.client.get("/api/conversations").json()
        self.assertEqual(listing[0]["message_count"], 2)
        self.assertNotIn("messages", listing[0])
        url = f'/api/conversations/{row["id"]}'
        self.assertEqual(self.client.get(url).json(), row)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(self.client.get("/api/conversations").json(), [])

    def test_conversation_validation(self):
        for body in [
            {**self.conversation, "title": "   "}, {**self.conversation, "title": "x" * 101},
            {**self.conversation, "messages": []}, {**self.conversation, "messages": [{"role": "system", "content": "hello"}]},
            {**self.conversation, "messages": [{"role": "user", "content": "  "}]},
            {**self.conversation, "messages": [{"role": "user", "content": "x" * 4001}]},
            {**self.conversation, "messages": [{"role": "user", "content": "a"}] * 51},
            {**self.conversation, "id": "client-supplied"},
        ]:
            with self.subTest(body_type=list(body)):
                self.assertEqual(self.client.post("/api/conversations", json=body).status_code, 422)
        self.assertEqual(self.conversations.rows, {})
        self.assertEqual(self.client.get("/api/conversations/invalid").status_code, 422)

    def test_storage_failure_safe_and_server_alive(self):
        with patch("backend.services.repository.get_firestore_client", side_effect=RuntimeError("SECRET_SENTINEL")):
            app.dependency_overrides.clear()
            requests = [("get", "/api/data", None), ("get", "/api/data/summary", None),
                        ("post", "/api/data", self.row), ("put", "/api/data/2026-09-28", self.row),
                        ("delete", "/api/data/2026-09-28", None),
                        ("get", "/api/conversations", None), ("post", "/api/conversations", self.conversation),
                        ("get", "/api/conversations/" + "a" * 32, None), ("delete", "/api/conversations/" + "a" * 32, None)]
            for method, url, body in requests:
                response = self.client.request(method, url, **({"json": body} if body else {}))
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("SECRET_SENTINEL", response.text)
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_swagger_and_cors(self):
        schema = self.client.get("/openapi.json").json()
        for path, methods in {"/api/data": ["get", "post"], "/api/data/{id}": ["put", "delete"], "/api/data/summary": ["get"], "/api/conversations": ["get", "post"], "/api/conversations/{id}": ["get", "delete"]}.items():
            for method in methods:
                self.assertIn(method, schema["paths"][path])
        self.assertEqual(self.client.get("/docs").status_code, 200)
        for method in ["PUT", "DELETE"]:
            response = self.client.options("/api/data/2026-09-28", headers={"Origin": "http://localhost:5500", "Access-Control-Request-Method": method})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5500")

    def test_migration_dry_run_repeat_and_no_overwrite(self):
        rows = [{"id": "2026-09-28", **self.row}]
        self.assertEqual(copy_workouts(rows, self.data)["would_create"], 1)
        self.assertEqual(self.data.rows, {})
        self.assertEqual(copy_workouts(rows, self.data, apply=True)["created"], 1)
        before = deepcopy(self.data.rows)
        self.assertEqual(copy_workouts([{**rows[0], "value": 1}], self.data, apply=True)["skipped"], 1)
        self.assertEqual(before, self.data.rows)
        self.assertEqual(rows[0]["value"], 60)

    def test_migration_validates_all_before_writing(self):
        rows = [{"id": "2026-09-28", **self.row}, {"id": "bad", **self.row}]
        with self.assertRaises(ValueError):
            copy_workouts(rows, self.data, apply=True)
        self.assertEqual(self.data.rows, {})

    def test_firestore_adapter_atomic_operations(self):
        client = MagicMock()
        ref = client.collection.return_value.document.return_value
        repo = FirestoreRepository("data")
        with patch("backend.services.repository.get_firestore_client", return_value=client):
            repo.create(self.row["date"], self.row)
            ref.create.assert_called_once_with(self.row, timeout=30)
            ref.create.side_effect = AlreadyExists("internal")
            with self.assertRaises(DuplicateRecord): repo.create(self.row["date"], self.row)
            ref.update.side_effect = NotFound("internal")
            with self.assertRaises(MissingRecord): repo.update(self.row["date"], self.row)
            ref.set.assert_not_called()
            transaction = client.transaction.return_value
            with patch("backend.services.repository.transactional", side_effect=lambda f: f):
                ref.get.return_value.exists = False
                with self.assertRaises(MissingRecord): repo.delete(self.row["date"])
                transaction.delete.assert_not_called()
                ref.get.return_value.exists = True
                repo.delete(self.row["date"])
                ref.get.assert_called_with(transaction=transaction, timeout=30)
                transaction.delete.assert_called_once_with(ref)
        self.assertTrue(all(call.args == ("data",) for call in client.collection.call_args_list))


if __name__ == "__main__":
    unittest.main()
