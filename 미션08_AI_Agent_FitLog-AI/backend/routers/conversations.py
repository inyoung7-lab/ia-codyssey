from fastapi import APIRouter, Depends, Response

from backend.schemas.conversation import Conversation, ConversationInput, ConversationSummary
from backend.services.conversation_service import ConversationService
from backend.services.repository import FirestoreRepository

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def get_conversation_service():
    return ConversationService(FirestoreRepository("conversations"))


@router.post("", status_code=201, response_model=Conversation)
def create_conversation(body: ConversationInput, service: ConversationService = Depends(get_conversation_service)):
    return service.create(body)


@router.get("", response_model=list[ConversationSummary])
def list_conversations(service: ConversationService = Depends(get_conversation_service)):
    return service.list()


@router.get("/{id}", response_model=Conversation)
def get_conversation(id: str, service: ConversationService = Depends(get_conversation_service)):
    return service.get(id)


@router.delete("/{id}", status_code=204)
def delete_conversation(id: str, service: ConversationService = Depends(get_conversation_service)):
    service.delete(id)
    return Response(status_code=204)
