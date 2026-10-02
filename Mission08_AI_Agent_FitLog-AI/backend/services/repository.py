"""Lazy Firestore access. Never log raw SDK exceptions or credentials."""
from typing import Protocol

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud.firestore_v1.transaction import transactional

from backend.firebase import get_firestore_client


class ServiceError(Exception):
    status_code = 503
    detail = "저장소 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요."


class MissingRecord(ServiceError):
    status_code = 404
    detail = "해당 기록이 없습니다."


class DuplicateRecord(ServiceError):
    status_code = 409
    detail = "해당 날짜의 운동 기록이 이미 존재합니다."


class InvalidInput(ServiceError):
    status_code = 422
    detail = "입력값을 확인해 주세요. 날짜 ID는 실제 YYYY-MM-DD 날짜여야 합니다."


class DateMismatch(InvalidInput):
    detail = "URL의 날짜 ID와 본문의 date가 같아야 합니다. 날짜 변경은 지원하지 않습니다."


class InvalidConversationId(InvalidInput):
    detail = "대화 ID는 생성 응답에서 받은 32자리 소문자 16진수 문자열이어야 합니다."


class ConversationConflict(ServiceError):
    status_code = 409
    detail = "대화가 다른 요청으로 변경되었습니다. 최신 대화를 조회해 주세요."


class Repository(Protocol):
    def list(self) -> list[dict]: ...
    def get(self, id: str) -> dict: ...
    def create(self, id: str, record: dict) -> None: ...
    def update(self, id: str, record: dict) -> None: ...
    def delete(self, id: str) -> None: ...


class FirestoreRepository:
    def __init__(self, collection: str):
        if collection not in {"data", "conversations"}:
            raise ValueError("Unsupported collection")
        self.collection = collection

    def _run(self, operation):
        try:
            return operation(get_firestore_client().collection(self.collection))
        except ServiceError:
            raise
        except AlreadyExists:
            raise DuplicateRecord() from None
        except NotFound:
            raise MissingRecord() from None
        except Exception:
            raise ServiceError() from None

    @staticmethod
    def _record(snapshot):
        if not snapshot.exists:
            raise MissingRecord()
        return {**snapshot.to_dict(), "id": snapshot.id}

    def list(self):
        return self._run(lambda c: [self._record(d) for d in c.stream(timeout=30)])

    def get(self, id):
        return self._run(lambda c: self._record(c.document(id).get(timeout=30)))

    def create(self, id, record):
        # Atomic create: two concurrent requests cannot overwrite each other.
        self._run(lambda c: c.document(id).create(record, timeout=30))

    def update(self, id, record):
        # Firestore update requires existence; no get-then-set race / upsert.
        self._run(lambda c: c.document(id).update(record, timeout=30))

    def delete(self, id):
        def remove(collection):
            reference = collection.document(id)

            @transactional
            def delete_existing(transaction):
                snapshot = reference.get(transaction=transaction, timeout=30)
                if not snapshot.exists:
                    raise MissingRecord()
                transaction.delete(reference)

            delete_existing(get_firestore_client().transaction())

        # Existence check and delete share a transaction, including retries.
        self._run(remove)

    def append_turn(self, id, expected, messages, updated_at):
        if self.collection != "conversations":
            raise ValueError("Conversation storage required")

        def append(collection):
            reference = collection.document(id)

            @transactional
            def save(transaction):
                current = self._record(reference.get(transaction=transaction, timeout=30))
                if current != expected:
                    raise ConversationConflict()
                transaction.update(reference, {"messages": messages, "updated_at": updated_at})

            # Only storage is retried by Firestore, never the GPT request.
            save(get_firestore_client().transaction())

        self._run(append)
