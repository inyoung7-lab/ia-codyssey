"""Shared, strictly validated, read-only tools for GPT and local MCP."""
import json
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from backend.services.repository import ServiceError


class EmptyArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RecentArgs(EmptyArgs):
    limit: int = Field(default=7, ge=1, le=30)


class ConversationArgs(EmptyArgs):
    conversation_id: str = Field(pattern=r"^[0-9a-f]{32}$")


SPEC = {
    "get_data_summary": (EmptyArgs, "운동 기록의 확정 통계와 추세, Insight를 조회합니다."),
    "get_recent_records": (RecentArgs, "최신 날짜부터 최근 운동 기록을 조회합니다. limit은 1~30, 기본 7입니다."),
    "get_conversation": (ConversationArgs, "알고 있는 conversation_id에 해당하는 저장된 대화를 조회합니다. ID를 추측하지 마세요."),
}
TOOLS = [{"type": "function", "function": {"name": name, "description": description,
          "parameters": model.model_json_schema()}} for name, (model, description) in SPEC.items()]


class ToolDispatcher:
    def __init__(self, data, conversations):
        self.data, self.conversations = data, conversations

    def execute(self, name, arguments):
        if name not in SPEC:
            return {"error": "unknown_tool"}
        try:
            if isinstance(arguments, str):
                if len(arguments) > 2000:
                    return {"error": "invalid_arguments"}
                arguments = json.loads(arguments)
            args = SPEC[name][0].model_validate(arguments)
        except (ValueError, TypeError, ValidationError):
            return {"error": "invalid_arguments"}
        try:
            if name == "get_data_summary":
                result = self.data.summary()
            elif name == "get_recent_records":
                rows = sorted(self.data.list(), key=lambda row: row["date"], reverse=True)[:args.limit]
                result = [{key: row[key] for key in ("date", "value", "memo")} for row in rows]
            else:
                result = self.conversations.get(args.conversation_id)
            return json.loads(json.dumps(result, ensure_ascii=False, default=lambda value: value.isoformat()))
        except ServiceError as error:
            return {"error": "not_found" if error.status_code == 404 else "service_unavailable"}
        except Exception:
            return {"error": "service_unavailable"}
