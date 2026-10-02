"""Protocol test runs a separate fake-only stdio server; never touches Firestore."""
import asyncio
import sys
import unittest
from unittest.mock import patch
from backend.check_mcp import verify
from backend.mcp_server import build_server
from backend.services.ai_tools import ToolDispatcher
from backend.services.data_service import DataService
from backend.services.conversation_service import ConversationService
from backend.test_chat import ChatStore
from backend.test_mission_api import MemoryRepository


def fake_dispatcher():
    rows = MemoryRepository()
    for day in range(1, 5):
        date = f"2026-09-{day:02}"
        rows.create(date, {"date": date, "value": day, "memo": "fake"})
    from datetime import datetime, timezone
    conversations = ChatStore()
    conversations.create("a" * 32, {"id": "a" * 32, "title": "fake", "messages": [{"role":"user", "content":"test"}],
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)})
    return ToolDispatcher(DataService(rows), ConversationService(conversations))


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_external_stdio_protocol(self):
        result = await verify("a" * 32, "backend.test_mcp", ["--serve-fake"])
        self.assertEqual(result["summary_count"], 4)
        self.assertEqual(len(result["recent"]), 3)
        self.assertTrue(result["conversation_found"])

    async def test_schema_and_validation(self):
        server = build_server(fake_dispatcher())
        tools = await server.list_tools()
        recent = next(tool for tool in tools if tool.name == "get_recent_records")
        self.assertEqual(recent.inputSchema["properties"]["limit"]["maximum"], 30)
        with self.assertRaises(Exception):
            await server.call_tool("get_recent_records", {"limit": 31})


if __name__ == "__main__":
    if "--serve-fake" in sys.argv:
        with patch("backend.services.repository.get_firestore_client", side_effect=AssertionError("No live Firestore")):
            build_server(fake_dispatcher()).run(transport="stdio")
    else:
        unittest.main()
