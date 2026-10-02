"""Local stdio MCP server. stdout is reserved for the MCP protocol."""
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from typing import Annotated
from pydantic import Field
from backend.services.ai_tools import ToolDispatcher
from backend.routers.data import get_data_service
from backend.routers.conversations import get_conversation_service


def build_server(dispatcher=None):
    dispatcher = dispatcher or ToolDispatcher(get_data_service(), get_conversation_service())
    server = FastMCP("FitLog-AI", log_level="ERROR")
    read_only = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True)

    @server.tool(annotations=read_only)
    def get_data_summary() -> dict:
        """운동 기록의 period/count/metrics/trend/insights를 읽습니다."""
        return dispatcher.execute("get_data_summary", {})

    @server.tool(annotations=read_only)
    def get_recent_records(limit: Annotated[int, Field(strict=True, ge=1, le=30)] = 7) -> list[dict] | dict:
        """최근 운동 기록을 최신순으로 읽습니다. limit: 1~30, 기본 7."""
        return dispatcher.execute("get_recent_records", {"limit": limit})

    @server.tool(annotations=read_only)
    def get_conversation(conversation_id: Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]) -> dict:
        """알고 있는 32자리 conversation_id의 대화를 읽습니다."""
        return dispatcher.execute("get_conversation", {"conversation_id": conversation_id})

    return server


if __name__ == "__main__":
    build_server().run(transport="stdio")
