"""LLM plugins initialization."""

from oagent.plugins.llm.base import LLMPluginBase
from oagent.plugins.llm.openai import OpenAILLMPlugin
from oagent.plugins.llm.ollama import OllamaLLMPlugin

__all__ = ["LLMPluginBase", "OpenAILLMPlugin", "OllamaLLMPlugin"]