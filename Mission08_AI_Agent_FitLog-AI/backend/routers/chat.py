from fastapi import APIRouter, Depends, Response

from backend.routers.data import get_data_service
from backend.routers.conversations import get_conversation_service
from backend.schemas.chat import ChatInput, ChatOutput
from backend.services.chat_service import ChatService
from backend.services.gpt_client import GPTClient

router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_chat_service(data=Depends(get_data_service), conversations=Depends(get_conversation_service)):
    return ChatService(data, conversations, GPTClient())


@router.post("", response_model=ChatOutput)
def chat(body: ChatInput, response: Response, service=Depends(get_chat_service)):
    response.headers["Cache-Control"] = "no-store"
    return service.chat(body)
