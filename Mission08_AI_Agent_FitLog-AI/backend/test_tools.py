import json
import unittest
from unittest.mock import patch
import httpx2
from backend.services.ai_tools import ToolDispatcher
from backend.services.gpt_client import GPTClient, ChatError
from backend.services.data_service import DataService
from backend.services.conversation_service import ConversationService
from backend.test_chat import ChatStore
from backend.test_mission_api import MemoryRepository
from backend.schemas.conversation import ConversationInput


class ToolTests(unittest.TestCase):
    def setUp(self):
        block = patch("backend.services.repository.get_firestore_client", side_effect=AssertionError("No real Firestore"))
        block.start()
        self.addCleanup(block.stop)
        self.rows = MemoryRepository()
        for day in range(1, 11):
            date = f"2026-09-{day:02}"
            self.rows.create(date, {"date": date, "value": day, "memo": "test"})
        self.conversations = ConversationService(ChatStore())
        self.dispatcher = ToolDispatcher(DataService(self.rows), self.conversations)

    def test_summary(self):
        result = self.dispatcher.execute("get_data_summary", "{}")
        self.assertEqual(result["count"], 10)
        self.assertEqual(set(result), {"period", "count", "metrics", "trend", "insights"})

    def test_recent(self):
        result = self.dispatcher.execute("get_recent_records", '{"limit":3}')
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["date"], "2026-09-10")
        self.assertEqual(set(result[0]), {"date", "value", "memo"})
        self.assertEqual(len(self.dispatcher.execute("get_recent_records", {})), 7)

    def test_invalid(self):
        for args in ['{', '[]', {"limit": 0}, {"limit": 31}, {"limit": True}, {"limit": "3"}, {"x": 1}]:
            self.assertEqual(self.dispatcher.execute("get_recent_records", args), {"error": "invalid_arguments"})
        self.assertEqual(self.dispatcher.execute("delete", {}), {"error": "unknown_tool"})

    def test_conversation(self):
        self.assertEqual(self.dispatcher.execute("get_conversation", {"conversation_id": "a" * 32}), {"error": "not_found"})
        saved = self.conversations.create(ConversationInput(title="test", messages=[{"role": "user", "content": "hi"}]))
        result = self.dispatcher.execute("get_conversation", {"conversation_id": saved["id"]})
        self.assertEqual(result["id"], saved["id"])

    def run_sdk(self, responses):
        self.sent = []
        def send(request):
            self.sent.append(json.loads(request.content))
            return httpx2.Response(200, json={"id": "test", "object": "chat.completion", "created": 0,
                "model": "gpt-5-mini", "choices": [responses[min(len(self.sent)-1, len(responses)-1)]]})
        with patch("backend.services.gpt_client.settings", return_value=("fake-key", "https://copa.codyssey.kr/v1", "gpt-5-mini")), patch("backend.services.gpt_client._http_client", side_effect=lambda: httpx2.Client(transport=httpx2.MockTransport(send))):
            self.client = GPTClient()
            return self.client.complete([{"role": "user", "content": "recent"}], self.dispatcher)

    @staticmethod
    def call(name="get_recent_records", arguments='{"limit":3}'):
        return {"index": 0, "finish_reason": "tool_calls", "message": {"role": "assistant", "content": None,
                "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": name, "arguments": arguments}}]}}

    def test_roundtrip(self):
        answer = self.run_sdk([self.call(), {"index":0, "finish_reason":"stop", "message":{"role":"assistant", "content":"done"}}])
        self.assertEqual(answer, "done")
        self.assertEqual(self.client.tools_used, ["get_recent_records"])
        self.assertEqual(len(self.sent), 2)
        self.assertEqual(len(self.sent[0]["tools"]), 3)
        tool = self.sent[1]["messages"][-1]
        self.assertEqual(tool["role"], "tool")
        self.assertEqual(tool["tool_call_id"], "call_1")
        self.assertEqual(len(json.loads(tool["content"])), 3)

    def test_loop_bound(self):
        with self.assertRaises(ChatError):
            self.run_sdk([self.call()])
        self.assertEqual(len(self.sent), 4)

    def test_error_tool_result(self):
        self.run_sdk([self.call("unknown"), {"index":0, "finish_reason":"stop", "message":{"role":"assistant", "content":"unavailable"}}])
        self.assertEqual(json.loads(self.sent[1]["messages"][-1]["content"]), {"error":"unknown_tool"})
        self.assertEqual(self.client.tools_used, [])

    def test_normal_no_call(self):
        self.assertEqual(self.run_sdk([{ "index":0, "finish_reason":"stop", "message":{"role":"assistant", "content":"normal"}}]), "normal")
        self.assertEqual(len(self.sent), 1)

    def test_chat_saves_final_answer_only_and_keeps_history_context(self):
        from backend.services.chat_service import ChatService
        from backend.schemas.chat import ChatInput
        from backend.schemas.chat import ChatOutput
        history = [{"role":"user" if i % 2 == 0 else "assistant", "content":f"message {i}"} for i in range(14)]
        old = self.conversations.create(ConversationInput(title="original", messages=history))
        sent = []
        def send(request):
            sent.append(json.loads(request.content))
            choice = self.call() if len(sent) == 1 else {"index":0, "finish_reason":"stop", "message":{"role":"assistant", "content":"final"}}
            return httpx2.Response(200, json={"id":"test", "object":"chat.completion", "created":0, "model":"gpt-5-mini", "choices":[choice]})
        with patch("backend.services.gpt_client.settings", return_value=("fake-key", "https://copa.codyssey.kr/v1", "gpt-5-mini")), patch("backend.services.gpt_client._http_client", side_effect=lambda: httpx2.Client(transport=httpx2.MockTransport(send))):
            service = ChatService(DataService(self.rows), self.conversations, GPTClient())
            output = service.chat(ChatInput(message="recent three", conversation_id=old["id"]))
        self.assertEqual(ChatOutput.model_validate(output).tools_used, ["get_recent_records"])
        self.assertEqual(sent[0]["messages"][1:-1], history[-10:])
        self.assertIn('"insights"', sent[0]["messages"][0]["content"])
        saved = self.conversations.get(old["id"])
        self.assertEqual(len(saved["messages"]), 16)
        self.assertEqual(saved["messages"][-1], {"role":"assistant", "content":"final"})
        self.assertNotIn("tool", [row["role"] for row in saved["messages"]])
