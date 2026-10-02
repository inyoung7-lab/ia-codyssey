"""Codyssey Chat Completions only. No retries, redirects or raw error logging."""
import logging
import os
import json
import re

import httpx2
from openai import (
    OpenAI, APIConnectionError, APIStatusError, APITimeoutError,
    AuthenticationError, PermissionDeniedError, RateLimitError,
)

from backend.services.repository import ServiceError

logger = logging.getLogger(__name__)


def safe_diagnostic(error, key):
    """Extract only five fields; never stringify exceptions, headers or responses."""
    def sanitize(value):
        if not isinstance(value, str):
            return None
        if key:
            value = value.replace(key, "[REDACTED]")
            value = value.replace(json.dumps(key)[1:-1], "[REDACTED]")
        if re.search(r"(?i)authorization|private[_ -]?key|BEGIN .*KEY|request[_ ]headers|OPENAI_API_KEY", value):
            return "[sensitive diagnostic omitted]"
        value = re.sub(r"(?i)\bBearer\s+\S+", "Bearer [REDACTED]", value)
        value = re.sub(r"(?i)(?:api[_ -]?key|token|password|secret)\s*[:=]\s*[^\s,;]+", "[REDACTED]", value)
        value = re.sub(r"\b(?:sk-[\w-]+|[A-Za-z0-9_-]{24,})\b", "[REDACTED]", value)
        return re.sub(r"[\x00-\x1f\x7f]", " ", value)[:500]

    body = getattr(error, "body", None)
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        body = body["error"]
    if not isinstance(body, dict):
        body = {}
    status = getattr(error, "status_code", None)
    return {
        "http_status": status if type(status) is int else None,
        "exception_class": type(error).__name__,
        "error_type": sanitize(body.get("type")),
        "error_code": sanitize(body.get("code")),
        "message": sanitize(body.get("message")),
    }


def diagnostic_error(error, key, status, detail):
    logger.warning("Codyssey diagnostic: %s", json.dumps(safe_diagnostic(error, key), ensure_ascii=False))
    return ChatError(status, detail)


class ChatError(ServiceError):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def settings():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    base = os.getenv("OPENAI_BASE_URL", "https://copa.codyssey.kr/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()
    if not key:
        raise ChatError(503, "코디세이 API 인증키가 설정되지 않았습니다.")
    # Do not accidentally send the virtual key to an official or unrelated host.
    if base != "https://copa.codyssey.kr/v1" or model != "gpt-5-mini":
        raise ChatError(503, "코디세이 API 주소와 모델 설정을 확인해 주세요.")
    return key, base, model


def _http_client():
    return httpx2.Client(trust_env=False, follow_redirects=False, timeout=60)


class GPTClient:
    def complete(self, messages, dispatcher=None):
        self.tools_used = []
        key, base, model = settings()
        # SDK debug logs can include request headers. This app never emits them.
        for name in ("openai", "httpx2", "httpcore2"):
            logging.getLogger(name).setLevel(logging.WARNING)
        try:
            with OpenAI(
                api_key=key, base_url=base,
                max_retries=0, timeout=60,
                http_client=_http_client(),
            ) as client:
                # Only add standard tools when a read-only dispatcher is provided.
                from backend.services.ai_tools import TOOLS
                messages = list(messages)
                rounds = 0
                while True:
                    options = {"tools": TOOLS} if dispatcher is not None else {}
                    result = client.chat.completions.create(model=model, messages=messages, **options)
                    choice = result.choices[0]
                    calls = choice.message.tool_calls
                    if not calls:
                        break
                    if dispatcher is None or rounds >= 3 or len(calls) > 3:
                        raise ChatError(502, "도구 호출 한도에 도달했습니다. 자동 재시도하지 않습니다.")
                    if choice.finish_reason != "tool_calls" or len({call.id for call in calls}) != len(calls):
                        raise ChatError(502, "도구 응답 형식을 확인하지 못했습니다.")
                    messages.append(choice.message.model_dump(exclude_none=True))
                    for call in calls:
                        if call.type != "function" or not call.id:
                            raise ChatError(502, "도구 응답 형식을 확인하지 못했습니다.")
                        payload = dispatcher.execute(call.function.name, call.function.arguments)
                        if not (isinstance(payload, dict) and "error" in payload):
                            if call.function.name not in self.tools_used:
                                self.tools_used.append(call.function.name)
                        messages.append({"role": "tool", "tool_call_id": call.id,
                                         "content": json.dumps(payload, ensure_ascii=False)})
                    rounds += 1
            choice = result.choices[0]
            answer = choice.message.content
            if choice.finish_reason != "stop" or not isinstance(answer, str) or not answer.strip():
                raise ChatError(502, "완전한 GPT 답변을 받지 못했습니다.")
            answer = answer.strip()
            if len(answer) > 4000 or key in answer:
                raise ChatError(502, "GPT 답변 형식을 확인하지 못했습니다.")
            return answer
        except ChatError:
            raise
        except AuthenticationError as error:
            raise diagnostic_error(error, key, 502, "코디세이 API 인증에 실패했습니다. 키 설정을 확인해 주세요.") from None
        except PermissionDeniedError as error:
            raise diagnostic_error(error, key, 502, "코디세이 API 모델 접근 권한을 확인해 주세요.") from None
        except RateLimitError as error:
            raise diagnostic_error(error, key, 429, "API 사용 한도 또는 요청 빈도를 확인해 주세요.") from None
        except APITimeoutError as error:
            raise diagnostic_error(error, key, 504, "GPT 응답 시간이 초과되었습니다. 자동 재시도하지 않습니다.") from None
        except APIConnectionError as error:
            raise diagnostic_error(error, key, 502, "코디세이 API에 연결하지 못했습니다.") from None
        except APIStatusError as error:
            raise diagnostic_error(error, key, 502, "코디세이 API가 요청을 처리하지 못했습니다.") from None
        except Exception:
            raise ChatError(502, "GPT 응답을 처리하지 못했습니다.") from None
