"""Configuration API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from oagent.config.settings import settings

router = APIRouter()


class ConfigResponse(BaseModel):
    """Response for configuration."""

    app_name: str
    app_version: str
    default_llm_provider: str
    default_llm_model: str
    default_embedding_provider: str
    default_embedding_model: str
    default_agent_type: str


class LLMConfigCreate(BaseModel):
    """Request to create LLM config."""

    name: str
    provider: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    is_default: bool = False


@router.get("", response_model=ConfigResponse)
async def get_config():
    """Get current configuration."""
    return ConfigResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        default_llm_provider=settings.default_llm_provider,
        default_llm_model=settings.default_llm_model,
        default_embedding_provider=settings.default_embedding_provider,
        default_embedding_model=settings.default_embedding_model,
        default_agent_type=settings.default_agent_type,
    )


@router.get("/llm")
async def list_llm_configs():
    """List saved LLM configurations."""
    # Placeholder - will be implemented with database
    return {
        "configs": [],
        "default": None
    }


@router.post("/llm")
async def create_llm_config(config: LLMConfigCreate):
    """Create a new LLM configuration."""
    # Placeholder - will be implemented with database
    import uuid
    return {
        "id": str(uuid.uuid4()),
        "message": "LLM config created",
        "config": config.model_dump()
    }


@router.delete("/llm/{config_id}")
async def delete_llm_config(config_id: str):
    """Delete an LLM configuration."""
    # Placeholder - will be implemented with database
    return {"message": f"LLM config {config_id} deleted"}