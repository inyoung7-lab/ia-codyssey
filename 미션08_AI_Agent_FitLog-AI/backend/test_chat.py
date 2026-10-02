"""No real provider calls or Firestore writes: fake stores and SDK MockTransport."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import httpx2

from backend.main import app
from backend.routers.chat import get_chat_service
from backend.schemas.conversation import ConversationInput
from backend.services.chat_service import ChatService
from backend.services.conversation_service import ConversationService
from backend.services.data_service import DataService
from backend.services.gpt_client import ChatError, GPTClient, settings, safe_diagnostic
from backend.services.repository import ConversationConflict, FirestoreRepository, ServiceError
from backend.test_mission_api import MemoryRepository

HTTPClient = httpx2.Client


class ChatStore(MemoryRepository):
    def append_turn(self, id, expected, messages, updated_at):
        if self.get(id) != expected:
            raise ConversationConflict()
        self.rows[id]["messages"] = deepcopy(messages)
        self.rows[id]["updated_at"] = updated_at


class ChatTests(unittest.TestCase):
    def setUp(self):
        block = patch("backend.services.repository.get_firestore_client", side_effect=AssertionError("No real Firestore"))
        block.start()
        self.addCleanup(block.stop)
        self.store = ChatStore()
        self.data = MemoryRepository()
        self.data.create("2026-09-28", {"date": "2026-09-28", "value": 60, "memo": "RAW_MEMO_NOT_FOR_GPT"})
        self.conversations = ConversationService(self.store)
        self.gpt = MagicMock()
        self.gpt.complete.return_value = "최근 기록은 60분입니다."
        self.service = ChatService(DataService(self.data), self.conversations, self.gpt)
        app.dependency_overrides[get_chat_service] = lambda: self.service
        self.addCleanup(app.dependency_overrides.clear)
        self.api = TestClient(app)
        self.addCleanup(self.api.close)

    def post(self, **kwargs):
        return self.api.post("/api/chat", json={"message": "최근 운동 추세는?", **kwargs})

    def test_success_context_and_auto_save(self):
        before = deepcopy(self.data.rows)
        response = self.post(message="  최근 운동 추세는?  ")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["provider"], "codyssey-openai-compatible")
        self.assertEqual(result["model"], "gpt-5-mini")
        self.assertEqual(result["answer"], self.gpt.complete.return_value)
        saved = self.store.get(result["conversation_id"])
        self.assertEqual(saved["title"], "최근 운동 추세는?")
        self.assertEqual([m["role"] for m in saved["messages"]], ["user", "assistant"])
        self.assertEqual(saved["created_at"], saved["updated_at"])
        messages = self.gpt.complete.call_args.args[0]
        self.assertEqual(len(messages), 2)
        injected = json.loads(messages[0]["content"].split("SUMMARY:\n", 1)[1])
        self.assertEqual(injected, DataService(self.data).summary())
        self.assertEqual(set(injected), {"period", "count", "metrics", "trend", "insights"})
        self.assertNotIn("RAW_MEMO_NOT_FOR_GPT", str(messages))
        self.assertNotIn('"memo"', str(messages))
        self.assertEqual(before, self.data.rows)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.gpt.complete.assert_called_once()

    def test_continue_recent_ten_and_keep_all_saved_messages(self):
        history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"turn {i}"} for i in range(14)]
        old = self.conversations.create(ConversationInput(title="Original", messages=history))
        response = self.post(conversation_id=old["id"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["conversation_id"], old["id"])
        sent = self.gpt.complete.call_args.args[0]
        self.assertEqual(sent[1:-1], history[-10:])
        new = self.store.get(old["id"])
        self.assertEqual(len(new["messages"]), 16)
        self.assertEqual(new["messages"][:14], history)
        self.assertEqual(new["title"], old["title"])
        self.assertEqual(new["created_at"], old["created_at"])
        self.assertGreaterEqual(new["updated_at"], old["updated_at"])

    def test_missing_conversation_does_not_call_provider(self):
        self.assertEqual(self.post(conversation_id="a" * 32).status_code, 404)
        self.gpt.complete.assert_not_called()

    def test_input_validation(self):
        for message in ["", "  ", "x" * 4001, 123, None]:
            self.assertEqual(self.post(message=message).status_code, 422)
        self.assertEqual(self.post(conversation_id="bad").status_code, 422)
        self.assertEqual(self.api.post("/api/chat", json={}).status_code, 422)
        self.gpt.complete.assert_not_called()

    def test_history_full_prevents_charge(self):
        old = self.conversations.create(ConversationInput(title="Full", messages=[{"role": "user", "content": "x"}] * 50))
        self.assertEqual(self.post(conversation_id=old["id"]).status_code, 409)
        self.gpt.complete.assert_not_called()

    def test_summary_failure_prevents_charge(self):
        with patch.object(self.service.data, "summary", side_effect=ServiceError()):
            self.assertEqual(self.post().status_code, 503)
        self.gpt.complete.assert_not_called()
        self.assertEqual(self.store.rows, {})

    def test_provider_failure_does_not_save(self):
        for code in [429, 502, 503, 504]:
            self.gpt.complete.side_effect = ChatError(code, "안전한 오류")
            response = self.post()
            self.assertEqual(response.status_code, code)
        self.assertEqual(self.store.rows, {})

    def test_success_then_save_failure_returns_5xx(self):
        with patch.object(self.store, "create", side_effect=ServiceError()):
            response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertIn("저장", response.json()["detail"])
        self.assertNotIn("answer", response.json())
        self.gpt.complete.assert_called_once()
        self.assertEqual(self.store.rows, {})

    def test_concurrent_change_not_overwritten(self):
        old = self.conversations.create(ConversationInput(title="Original", messages=[{"role": "user", "content": "x"}]))
        def generate(messages, **kwargs):
            self.store.rows[old["id"]]["title"] = "Changed concurrently"
            return "답변"
        self.gpt.complete.side_effect = generate
        response = self.post(conversation_id=old["id"])
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.store.rows[old["id"]]["title"], "Changed concurrently")
        self.assertEqual(len(self.store.rows[old["id"]]["messages"]), 1)

    def test_empty_data_context(self):
        self.data.rows.clear()
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["count"], 0)

    def test_swagger_contract(self):
        schema = self.api.get("/openapi.json").json()
        endpoint = schema["paths"]["/api/chat"]["post"]
        self.assertIn("requestBody", endpoint)
        fields = schema["components"]["schemas"]["ChatOutput"]["required"]
        self.assertTrue({"conversation_id", "answer", "provider", "model"} <= set(fields))

    def test_firestore_append_transaction_conflict(self):
        client = MagicMock()
        doc = client.collection.return_value.document.return_value
        row = {"id": "a" * 32, "title": "x", "messages": []}
        doc.get.return_value.exists = True
        doc.get.return_value.id = row["id"]
        doc.get.return_value.to_dict.return_value = deepcopy(row)
        repo = FirestoreRepository("conversations")
        now = datetime.now(timezone.utc)
        with patch("backend.services.repository.get_firestore_client", return_value=client), patch("backend.services.repository.transactional", side_effect=lambda f: f):
            repo.append_turn(row["id"], row, [], now)
            client.transaction.return_value.update.assert_called_once_with(doc, {"messages": [], "updated_at": now})
            doc.get.return_value.to_dict.return_value = {**row, "title": "new"}
            with self.assertRaises(ConversationConflict):
                repo.append_turn(row["id"], row, [], now)
            self.assertEqual(client.transaction.return_value.update.call_count, 1)


class SDKTests(unittest.TestCase):
    def test_diagnostic_redacts_credentials_and_ignores_headers(self):
        from types import SimpleNamespace
        key = "dummy-credential-for-redaction-test"
        for message in ["Invalid key " + key, "Authorization: Bearer " + key, "private_key: sensitive", "token=unknown-credential-value"]:
            error = SimpleNamespace(status_code=400, body={"error": {"type": "invalid_request_error", "code": "bad_parameter", "message": message}}, headers={"sensitive": key})
            result = safe_diagnostic(error, key)
            self.assertEqual(set(result), {"http_status", "exception_class", "error_type", "error_code", "message"})
            self.assertNotIn(key, str(result))
            self.assertNotIn("unknown-credential-value", str(result))
            self.assertNotIn("headers", result)
        error.body = {"message": "Unsupported parameter: max_completion_tokens", "code": "unsupported_parameter"}
        self.assertEqual(safe_diagnostic(error, key)["message"], error.body["message"])

    def transport(self, handler):
        return patch("backend.services.gpt_client._http_client", side_effect=lambda: HTTPClient(transport=httpx2.MockTransport(handler), trust_env=False, follow_redirects=False, timeout=60))

    def config(self):
        return patch("backend.services.gpt_client.settings", return_value=("unit-test-placeholder", "https://copa.codyssey.kr/v1", "gpt-5-mini"))

    def test_actual_sdk_url_minimal_payload_and_single_request_offline(self):
        requests = []
        def handler(request):
            requests.append(request)
            return httpx2.Response(200, json={"id": "test", "object": "chat.completion", "created": 0, "model": "gpt-5-mini", "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "검증 답변"}}]})
        with self.config(), self.transport(handler):
            self.assertEqual(GPTClient().complete([{"role": "user", "content": "test"}]), "검증 답변")
        self.assertEqual(len(requests), 1)
        self.assertEqual(str(requests[0].url), "https://copa.codyssey.kr/v1/chat/completions")
        payload = json.loads(requests[0].content)
        self.assertEqual(set(payload), {"model", "messages"})
        self.assertEqual(payload["model"], "gpt-5-mini")

    def test_sdk_error_mapping_no_retries_or_secret_leaks(self):
        for upstream, expected in [(401, 502), (403, 502), (429, 429), (500, 502), (400, 502)]:
            calls = []
            def handler(request):
                calls.append(1)
                return httpx2.Response(upstream, json={"error": {"message": "SECRET_SENTINEL", "type": "test"}})
            with self.subTest(upstream=upstream), self.config(), self.transport(handler):
                with self.assertRaises(ChatError) as caught:
                    GPTClient().complete([])
                self.assertEqual(caught.exception.status_code, expected)
                self.assertNotIn("SECRET_SENTINEL", str(caught.exception))
                self.assertEqual(len(calls), 1)

    def test_timeout_and_connection(self):
        for exception, code in [(httpx2.ReadTimeout, 504), (httpx2.ConnectError, 502)]:
            calls = []
            def handler(request):
                calls.append(1)
                raise exception("SECRET_SENTINEL", request=request)
            with self.config(), self.transport(handler), self.assertRaises(ChatError) as caught:
                GPTClient().complete([])
            self.assertEqual(caught.exception.status_code, code)
            self.assertNotIn("SECRET_SENTINEL", str(caught.exception))
            self.assertEqual(len(calls), 1)

    def test_missing_key_and_invalid_host_without_network(self):
        with patch("backend.services.gpt_client.os.getenv", side_effect=lambda name, default: "" if name == "OPENAI_API_KEY" else default):
            with self.assertRaises(ChatError) as caught:
                GPTClient().complete([])
            self.assertEqual(caught.exception.status_code, 503)
        with patch("backend.services.gpt_client.os.getenv", side_effect=lambda name, default: {"OPENAI_API_KEY": "placeholder", "OPENAI_BASE_URL": "https://api.openai.com/v1", "OPENAI_MODEL": "gpt-5-mini"}[name]):
            with self.assertRaises(ChatError): settings()

    def test_incomplete_and_empty_output_rejected(self):
        for content, finish in [("", "stop"), ("partial", "length"), (None, "stop")]:
            def handler(request):
                return httpx2.Response(200, json={"id": "test", "object": "chat.completion", "created": 0, "model": "gpt-5-mini", "choices": [{"index": 0, "finish_reason": finish, "message": {"role": "assistant", "content": content}}]})
            with self.config(), self.transport(handler), self.assertRaises(ChatError) as caught:
                GPTClient().complete([])
            self.assertEqual(caught.exception.status_code, 502)


if __name__ == "__main__":
    unittest.main()
