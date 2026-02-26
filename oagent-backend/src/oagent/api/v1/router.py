"""API v1 router initialization."""

from fastapi import APIRouter

from oagent.api.v1 import llm, agent, chat, config

api_router = APIRouter()

# Include all API routes
api_router.include_router(llm.router, prefix="/llm", tags=["LLM"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(config.router, prefix="/config", tags=["Config"])