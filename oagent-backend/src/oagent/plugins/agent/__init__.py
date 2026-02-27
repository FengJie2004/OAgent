"""Agent plugins initialization."""

from oagent.plugins.agent.base import AgentPluginBase
from oagent.plugins.agent.langchain import LangChainAgentPlugin

__all__ = ["AgentPluginBase", "LangChainAgentPlugin"]
