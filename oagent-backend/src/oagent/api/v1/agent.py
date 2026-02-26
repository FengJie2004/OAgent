"""Agent API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from oagent.core.registry import PluginRegistry
from oagent.models.agent import AgentConfig, AgentRunRequest

router = APIRouter()


class AgentTypeResponse(BaseModel):
    """Response for agent types."""

    types: List[str]
    descriptions: dict[str, str]


@router.get("/types", response_model=AgentTypeResponse)
async def get_agent_types() -> AgentTypeResponse:
    """Get available agent types."""
    registry = PluginRegistry()
    agent_types = list(registry.list("agent").keys())

    # Get descriptions
    descriptions = {}
    for agent_type in agent_types:
        try:
            plugin_class = registry.get("agent", agent_type)
            plugin = plugin_class()
            descriptions[agent_type] = plugin.description
        except Exception:
            descriptions[agent_type] = ""

    return AgentTypeResponse(
        types=agent_types,
        descriptions=descriptions
    )


@router.post("/run")
async def run_agent(request: AgentRunRequest):
    """Run an agent."""
    # This is a placeholder - actual agent execution will be implemented
    # with the Agent service layer

    return {
        "message": "Agent run endpoint - implementation pending",
        "input": request.input,
        "agent_type": request.config.agent_type if request.config else "default"
    }


@router.get("/tools")
async def get_available_tools():
    """Get available tools for agents."""
    # Placeholder - will be implemented with tool registry
    return {
        "tools": [
            {"name": "search", "description": "Search the web"},
            {"name": "calculator", "description": "Perform calculations"},
            {"name": "code_executor", "description": "Execute Python code"},
        ]
    }