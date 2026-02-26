"""Plugins module initialization."""

# Import all plugins to trigger registration
from oagent.plugins import llm

__all__ = ["llm"]