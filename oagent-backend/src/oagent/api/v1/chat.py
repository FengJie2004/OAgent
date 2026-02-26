"""Chat API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from oagent.models.chat import ChatSession, ChatMessage, CreateSessionRequest

router = APIRouter()

# In-memory session storage (will be replaced with database)
sessions: dict[str, ChatSession] = {}


class ChatRequest(BaseModel):
    """Chat request."""

    session_id: str
    message: str
    stream: bool = True


@router.get("/sessions", response_model=List[ChatSession])
async def list_sessions():
    """List all chat sessions."""
    return list(sessions.values())


@router.post("/sessions", response_model=ChatSession)
async def create_session(request: CreateSessionRequest):
    """Create a new chat session."""
    import uuid

    session = ChatSession(
        id=str(uuid.uuid4()),
        title=request.title,
        agent_config_id=request.agent_config_id,
    )
    sessions[session.id] = session
    return session


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(session_id: str):
    """Get a chat session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del sessions[session_id]
    return {"message": "Session deleted"}