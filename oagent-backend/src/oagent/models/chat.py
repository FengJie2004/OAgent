"""Pydantic models for chat sessions."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message for session."""

    id: str = Field(..., description="Message ID")
    session_id: str = Field(..., description="Session ID")
    role: str = Field(..., description="Message role (user, assistant, system, tool)")
    content: str = Field(default="", description="Message content")
    tool_name: Optional[str] = Field(default=None, description="Tool name if tool call")
    tool_args: Optional[dict] = Field(default=None, description="Tool arguments")
    tool_result: Optional[str] = Field(default=None, description="Tool result")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")


class ChatSession(BaseModel):
    """Chat session."""

    id: str = Field(..., description="Session ID")
    title: Optional[str] = Field(default=None, description="Session title")
    agent_config_id: Optional[str] = Field(default=None, description="Agent config used")
    messages: List[ChatMessage] = Field(default_factory=list, description="Messages")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Update time")


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    title: Optional[str] = Field(default=None, description="Session title")
    agent_config_id: Optional[str] = Field(default=None, description="Agent config ID")


class SessionListResponse(BaseModel):
    """Response for session list."""

    sessions: List[ChatSession] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total count")