"""Tests for LLM plugins."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from oagent.models.llm import LLMConfig, Message
from oagent.plugins.llm.openai import OpenAILLMPlugin


class TestOpenAILLMPlugin:
    """Tests for OpenAI LLM plugin."""

    def test_plugin_name(self):
        """Test plugin name."""
        plugin = OpenAILLMPlugin()
        assert plugin.name == "openai"

    def test_supported_models(self):
        """Test supported models list."""
        plugin = OpenAILLMPlugin()
        models = plugin.supported_models
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models
        assert "gpt-3.5-turbo" in models

    def test_validate_config_valid(self):
        """Test config validation with valid model."""
        plugin = OpenAILLMPlugin()
        config = LLMConfig(
            provider="openai",
            model_name="gpt-4o",
            api_key="test-key"
        )
        assert plugin.validate_config(config) is True

    def test_validate_config_invalid(self):
        """Test config validation with invalid model."""
        plugin = OpenAILLMPlugin()
        config = LLMConfig(
            provider="openai",
            model_name="invalid-model",
            api_key="test-key"
        )
        with pytest.raises(ValueError):
            plugin.validate_config(config)