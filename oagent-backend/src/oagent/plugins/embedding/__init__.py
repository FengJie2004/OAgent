"""Embedding plugins initialization."""

from oagent.plugins.embedding.base import EmbeddingPluginBase
from oagent.plugins.embedding.dashscope import DashScopeEmbeddingPlugin

__all__ = ["EmbeddingPluginBase", "DashScopeEmbeddingPlugin"]
