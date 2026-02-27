"""Agent plugin base class."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional, Any
from pydantic import BaseModel

from oagent.core.plugin_base import PluginBase
from oagent.models.agent import AgentConfig, ToolCall
from oagent.models.llm import Message


class AgentMetadata(BaseModel):
    """Agent execution metadata."""
    iterations: int = 0
    tokens_used: int = 0
    execution_time_ms: float = 0.0
    tool_calls: List[ToolCall] = []


class AgentPluginBase(PluginBase, ABC):
    """Base class for Agent plugins."""

    @property
    @abstractmethod
    def supported_tools(self) -> List[str]:
        """List of supported tool names."""
        pass

    @abstractmethod
    async def initialize(self, config: AgentConfig) -> None:
        """Initialize agent with configuration.

        Args:
            config: Agent configuration
        """
        pass

    @abstractmethod
    async def run(
        self,
        input: str,
        thread_id: str,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Run agent with input (non-streaming).

        Args:
            input: User input
            thread_id: Conversation thread ID
            stream: Whether to stream response

        Returns:
            Agent response
        """
        pass

    @abstractmethod
    async def run_stream(
        self,
        input: str,
        thread_id: str
    ) -> AsyncIterator[str]:
        """Run agent with streaming response.

        Args:
            input: User input
            thread_id: Conversation thread ID

        Yields:
            Tokens from agent response
        """
        pass

    @abstractmethod
    async def get_state(self, thread_id: str) -> Dict[str, Any]:
        """Get agent state for a thread.

        Args:
            thread_id: Thread ID

        Returns:
            Current agent state
        """
        pass

    @abstractmethod
    async def clear_memory(self, thread_id: str) -> bool:
        """Clear conversation memory for a thread.

        Args:
            thread_id: Thread ID

        Returns:
            True if successful
        """
        pass

    def shutdown(self) -> None:
        """Cleanup agent resources."""
        pass
