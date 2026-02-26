"""LLM API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from oagent.core.registry import PluginRegistry
from oagent.models.llm import LLMConfig, Message, ChatRequest, EmbeddingRequest
from oagent.config.settings import settings

router = APIRouter()


class ProviderResponse(BaseModel):
    """Response for provider list."""

    providers: List[str]
    default: str


class ModelResponse(BaseModel):
    """Response for model list."""

    provider: str
    models: List[str]


@router.get("/providers", response_model=ProviderResponse)
async def get_providers() -> ProviderResponse:
    """Get available LLM providers."""
    registry = PluginRegistry()
    providers = list(registry.list("llm").keys())
    return ProviderResponse(
        providers=providers,
        default=settings.default_llm_provider
    )


@router.get("/models/{provider}", response_model=ModelResponse)
async def get_models(provider: str) -> ModelResponse:
    """Get available models for a provider."""
    registry = PluginRegistry()

    try:
        plugin_class = registry.get("llm", provider)
        plugin = plugin_class()
        return ModelResponse(
            provider=provider,
            models=plugin.supported_models
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat with LLM (streaming)."""
    registry = PluginRegistry()

    # Use default config if not provided
    config = request.config or LLMConfig(
        provider=settings.default_llm_provider,
        model_name=settings.default_llm_model,
        temperature=settings.default_temperature,
        max_tokens=settings.default_max_tokens,
    )

    try:
        plugin_class = registry.get("llm", config.provider)
        plugin = plugin_class()

        if request.stream:
            async def generate():
                async for token in plugin.chat(request.messages, config):
                    yield f"data: {token}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            response = await plugin.chat_complete(request.messages, config)
            return {"content": response, "model": config.model_name, "provider": config.provider}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embed")
async def embed(request: EmbeddingRequest):
    """Generate embeddings for texts."""
    registry = PluginRegistry()

    provider = request.provider or settings.default_embedding_provider

    try:
        plugin_class = registry.get("llm", provider)
        plugin = plugin_class()

        embeddings = await plugin.embed(request.texts, request.model)

        return {
            "embeddings": embeddings,
            "model": request.model or "default",
            "provider": provider,
            "dimension": len(embeddings[0]) if embeddings else 0
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))