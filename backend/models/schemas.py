from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal


class ChatRequest(BaseModel):
    """Request model for chat API."""
    query: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat API."""
    type: Literal["text", "geojson"]
    data: str
    intent: str
    metadata: Optional[Dict[str, Any]] = None
