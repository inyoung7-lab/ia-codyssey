"""Local Ollama phrasing of approved Python facts, with conservative fallback."""
import json
import logging
import os
import re
from urllib.parse import urlsplit
import httpx
from pydantic import BaseModel, ConfigDict, Field
from backend.workout_facts import build_facts, rules_feedback

logger = logging.getLogger(__name__)

class AIFeedback(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, strict=True)
    summary: str = Field(min_length=1, max_length=1000)
    strength: str = Field(min_length=1, max_length=1000)
    improvement: str = Field(min_length=1, max_length=1000)
    next_workout: str = Field(min_length=1, max_length=1000)

def get_ai_settings():
    # Read only Ollama process variables. Never load .env or read API keys.
    base = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
    model = os.getenv('OLLAMA_MODEL', 'hermes3:8b')
    url = urlsplit(base)
    if url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost', '::1'} or url.username or url.password or url.path or url.query or url.fragment:
        raise ValueError('Only local Ollama addresses are supported')
    if not model.strip():
        raise ValueError('Missing model')
    return base, model

def validate_feedback(raw, facts):
    feedback = AIFeedback.model_validate(raw).model_dump()
    allowed_numbers = set(re.findall(r'\d+(?:\.\d+)?', json.dumps(facts, ensure_ascii=False)))
    forbidden = r'과부하|부상|질병|치료|체력|건강|습관|회복|부족|늘리|늘려|높이|향상|권장|권고'
    for key, text in feedback.items():
        if re.search(r'[A-Za-z\u3400-\u9fff\u3040-\u30ff]', text):
            raise ValueError('foreign_language')
        if re.search(forbidden, re.sub(r'\s+', '', text)):
            raise ValueError('forbidden_claim')
        if not set(re.findall(r'\d+(?:\.\d+)?', text)) <= allowed_numbers:
            raise ValueError('new_number')
        # Number membership cannot catch swapped days or false causal claims.
        # Accept only approved sentences, optionally reordered or concatenated.
        remaining = re.sub(r'\s+', '', text)
        allowed = sorted((re.sub(r'\s+', '', sentence) for sentence in facts[key]), key=len, reverse=True)
        count = 0
        while remaining:
            sentence = next((sentence for sentence in allowed if remaining.startswith(sentence)), None)
            if sentence is None or count >= 3:
                raise ValueError('unapproved_statement')
            remaining = remaining[len(sentence):]
            count += 1
    return feedback

def generate_feedback(analysis):
    facts = build_facts(analysis)
    fallback = {'provider': 'rules', 'ai_feedback': rules_feedback(facts)}
    if not analysis['statistics']['record_count']:
        return fallback
    reason = 'configuration'
    try:
        base, model = get_ai_settings()
        reason = 'connection'
        with httpx.Client(timeout=httpx.Timeout(45, connect=5), trust_env=False, follow_redirects=False) as client:
            response = client.post(base + '/api/chat', json={
                'model': model, 'stream': False, 'format': AIFeedback.model_json_schema(),
                'messages': [
                    {'role': 'system', 'content': '당신의 역할은 분석이 아니라 제공된 사실을 자연스러운 한국어로 정리하는 것입니다. 각 필드의 허용 문장 중 1~3개를 골라 그대로 연결하세요. 문장이나 숫자를 새로 쓰거나 바꾸지 마세요. 새로운 계산, 사실, 운동량·운동시간 증가 권고, 운동 강도·휴식 필요성·건강 상태 판단, 부상·질병 추측을 금지합니다. 한국어 문장만 사용하고 네 필드 summary, strength, improvement, next_workout을 가진 JSON 객체만 반환하세요.'},
                    {'role': 'user', 'content': json.dumps({'FACTS': facts}, ensure_ascii=False)},
                ],
            })
            reason = 'http_error'
            response.raise_for_status()
            reason = 'invalid_json'
            payload = response.json()
            if payload.get('done') is not True or payload.get('model') != model or payload.get('done_reason') == 'length':
                raise ValueError('Incomplete response')
            raw = json.loads(payload['message']['content'])
            reason = 'content_validation'
            result = validate_feedback(raw, facts)
            return {'provider': 'ollama', 'ai_feedback': result}
    except httpx.TimeoutException:
        reason = 'timeout'
    except Exception:
        pass
    logger.warning('Local feedback fallback: %s', reason)
    return fallback
