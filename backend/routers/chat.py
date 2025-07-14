from fastapi import APIRouter
from models.schemas import ChatRequest
from services.agent_service import process_query

router = APIRouter()

@router.post("/api/v1/chat")
def chat(request: ChatRequest):
    """
    Handles the chat request by invoking the query processing service.
    """
    return process_query(request.query)