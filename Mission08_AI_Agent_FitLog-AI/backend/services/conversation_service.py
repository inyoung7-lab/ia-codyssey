from datetime import datetime, timezone
import re
from uuid import uuid4

from pydantic import ValidationError

from backend.schemas.conversation import Conversation, ConversationInput
from backend.services.repository import InvalidConversationId, Repository, ServiceError


class ConversationService:
    def __init__(self, repository: Repository):
        self.repository = repository

    @staticmethod
    def validate_id(id):
        if not re.fullmatch(r"[0-9a-f]{32}", id):
            raise InvalidConversationId()

    @staticmethod
    def _validate(row):
        try:
            return Conversation.model_validate(row).model_dump()
        except ValidationError:
            raise ServiceError() from None

    def create(self, body: ConversationInput):
        id = uuid4().hex
        now = datetime.now(timezone.utc)
        row = {"id": id, **body.model_dump(), "created_at": now, "updated_at": now}
        self.repository.create(id, row)
        return row

    def list(self):
        rows = [self._validate(row) for row in self.repository.list()]
        rows.sort(key=lambda row: (row["updated_at"], row["id"]), reverse=True)
        return [{key: row[key] for key in ("id", "title", "created_at", "updated_at")}
                | {"message_count": len(row["messages"])} for row in rows]

    def get(self, id):
        self.validate_id(id)
        return self._validate(self.repository.get(id))

    def delete(self, id):
        self.validate_id(id)
        self.repository.delete(id)
