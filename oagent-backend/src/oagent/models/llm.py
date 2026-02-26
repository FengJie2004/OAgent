"""Pydantic models for LLM configurations."""

from typing import List, Optional
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for LLM provider."""

    provider: str = Field(..., description="LLM provider name (openai, anthropic, etc.)")
    model_name: str = Field(..., description="Model name to use")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    base_url: Optional[str] = Field(default=None, description="Base URL for the API")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    max_tokens: int = Field(default=2048, ge=1, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, ge=0, le=1, description="Top-p sampling")
    frequency_penalty: float = Field(default=0.0, ge=-2, le=2, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=-2, le=2, description="Presence penalty")
    stream: bool = Field(default=True, description="Enable streaming response")

    # Model configuration
    id: Optional[str] = Field(default=None, description="Config ID")
    name: Optional[str] = Field(default=None, description="Config display name")
    is_default: bool = Field(default=False, description="Is this the default config")


class Message(BaseModel):
    """Chat message."""

    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(default=None, description="Name for the message")


class ChatRequest(BaseModel):
    """Chat request model."""

    messages: List[Message] = Field(..., description="List of messages")
    config: Optional[LLMConfig] = None
    stream: bool = Field(default=True, description="Enable streaming")


class ChatResponse(BaseModel):
    """Chat response model."""

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider used")
    usage: Optional[dict] = Field(default=None, description="Token usage")
    finish_reason: Optional[str] = Field(default=None, description="Finish reason")


class EmbeddingRequest(BaseModel):
    """Embedding request model."""

    texts: List[str] = Field(..., description="Texts to embed")
    model: Optional[str] = Field(default=None, description="Embedding model")
    provider: Optional[str] = Field(default=None, description="Embedding provider")


class EmbeddingResponse(BaseModel):
    """Embedding response model."""

    embeddings: List[List[float]] = Field(..., description="Embedding vectors")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider used")
    dimension: int = Field(..., description="Embedding dimension")