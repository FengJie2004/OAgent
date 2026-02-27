"""Pydantic models for Agent configurations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for Agent."""

    agent_type: str = Field(
        default="langchain",
        description="Agent type (langchain, langgraph, deep_agent, react)"
    )
    name: Optional[str] = Field(default=None, description="Agent name")

    # LLM configuration
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model")
    llm_config_id: Optional[str] = Field(default=None, description="LLM config ID")

    # Agent behavior
    system_prompt: Optional[str] = Field(default=None, description="System prompt")
    tools: List[str] = Field(default_factory=list, description="Tool names to use")
    max_iterations: int = Field(default=10, ge=1, description="Maximum iterations")

    # Memory
    memory_enabled: bool = Field(default=True, description="Enable conversation memory")
    memory_type: str = Field(default="buffer", description="Memory type")
    memory_window: int = Field(default=10, description="Memory window size")

    # Model parameters
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1)

    # Metadata
    id: Optional[str] = Field(default=None, description="Config ID")
    is_default: bool = Field(default=False, description="Is default config")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentState(BaseModel):
    """Agent execution state."""

    thread_id: str = Field(..., description="Thread/conversation ID")
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Message history"
    )
    current_step: str = Field(default="idle", description="Current step")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentRunRequest(BaseModel):
    """Request to run an agent."""

    input: str = Field(..., description="User input")
    config: Optional[AgentConfig] = None
    config_id: Optional[str] = Field(default=None, description="Use saved config")
    thread_id: Optional[str] = Field(default=None, description="Continue conversation")
    stream: bool = Field(default=True, description="Enable streaming")


class AgentRunResponse(BaseModel):
    """Response from agent run."""

    output: str = Field(..., description="Agent output")
    thread_id: str = Field(..., description="Thread ID")
    agent_type: str = Field(..., description="Agent type used")
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tool calls made"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Tool call information."""

    tool_name: str = Field(..., description="Tool name")
    tool_args: Dict[str, Any] = Field(..., description="Tool arguments")
    result: Optional[str] = Field(default=None, description="Tool result")
    error: Optional[str] = Field(default=None, description="Error if any")