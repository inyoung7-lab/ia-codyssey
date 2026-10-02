"""Explicit read-only external MCP client. No GPT calls or writes."""
import asyncio
import json
import sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def unpack(result):
    if result.isError:
        raise RuntimeError("MCP tool failed")
    if result.structuredContent is not None:
        data = result.structuredContent
        return data["result"] if set(data) == {"result"} else data
    return json.loads(result.content[0].text)


async def verify(conversation_id, module="backend.mcp_server", args=None):
    parameters = StdioServerParameters(command=sys.executable, args=["-m", module, *(args or [])],
        cwd=Path(__file__).resolve().parents[1], env={"PYTHONIOENCODING": "utf-8"})
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=90)) as client:
            await client.initialize()
            listing = await client.list_tools()
            names = sorted(tool.name for tool in listing.tools)
            assert names == ["get_conversation", "get_data_summary", "get_recent_records"]
            assert all(tool.annotations.readOnlyHint for tool in listing.tools)
            summary = unpack(await client.call_tool("get_data_summary", {}))
            recent = unpack(await client.call_tool("get_recent_records", {"limit": 3}))
            conversation = unpack(await client.call_tool("get_conversation", {"conversation_id": conversation_id}))
            assert len(recent) == 3
            assert conversation["id"] == conversation_id
            return {"tools": names, "summary_count": summary["count"], "recent": recent,
                    "conversation_found": True}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conversation-id", required=True)
    options = parser.parse_args()
    try:
        print(json.dumps(asyncio.run(verify(options.conversation_id)), ensure_ascii=False))
    except Exception:
        print("MCP verification failed; no credentials or raw exception were printed.")
        sys.exit(1)
