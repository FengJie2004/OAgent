"""Tests for DashScope LLM plugin."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from oagent.models.llm import LLMConfig, Message


class TestDashScopeLLMPlugin:
    """Tests for DashScope LLM plugin."""

    def test_plugin_name(self):
        """Test plugin name."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        assert plugin.name == "dashscope"

    def test_plugin_version(self):
        """Test plugin version."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        assert plugin.version == "0.1.0"

    def test_plugin_description(self):
        """Test plugin description."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        assert "DashScope" in plugin.description
        assert "Qwen" in plugin.description

    def test_supported_models(self):
        """Test supported models list."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        models = plugin.supported_models
        assert "qwen3.5-plus" in models
        assert "qwen-max" in models
        assert "qwen-turbo" in models
        assert "qwen2.5-72b-instruct" in models

    def test_supported_embedding_models(self):
        """Test supported embedding models list."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        models = plugin.supported_embedding_models
        assert "text-embedding-v4" in models
        assert "text-embedding-v3" in models

    def test_validate_config_valid(self):
        """Test config validation with valid model."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        config = LLMConfig(
            provider="dashscope",
            model_name="qwen3.5-plus",
            api_key="test-api-key"
        )
        assert plugin.validate_config(config) is True

    def test_validate_config_invalid(self):
        """Test config validation with invalid model."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        config = LLMConfig(
            provider="dashscope",
            model_name="invalid-model",
            api_key="test-api-key"
        )
        with pytest.raises(ValueError):
            plugin.validate_config(config)

    def test_convert_messages(self):
        """Test message conversion to OpenAI format."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello!"),
        ]
        converted = plugin._convert_messages(messages)
        assert len(converted) == 2
        assert converted[0]["role"] == "system"
        assert converted[0]["content"] == "You are a helpful assistant."
        assert converted[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_chat_complete(self):
        """Test non-streaming chat completion."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        config = LLMConfig(
            provider="dashscope",
            model_name="qwen3.5-plus",
            api_key="test-api-key"
        )
        messages = [Message(role="user", content="Hello")]

        # Mock the OpenAI client
        with patch.object(plugin, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello! How can I help you?"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await plugin.chat_complete(messages, config)
            assert result == "Hello! How can I help you?"

    @pytest.mark.asyncio
    async def test_embed(self):
        """Test embedding generation."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()

        with patch('oagent.plugins.llm.dashscope.settings') as mock_settings:
            mock_settings.dashscope_api_key = "test-key"
            mock_settings.dashscope_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            mock_settings.dashscope_embedding_model = "text-embedding-v4"

            with patch('oagent.plugins.llm.dashscope.AsyncOpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
                mock_client.embeddings.create = AsyncMock(return_value=mock_response)
                mock_openai.return_value = mock_client

                result = await plugin.embed(["test text"])
                assert result == [[0.1, 0.2, 0.3]]

    def test_get_client_with_config_api_key(self):
        """Test client creation with config API key."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        config = LLMConfig(
            provider="dashscope",
            model_name="qwen3.5-plus",
            api_key="config-api-key",
            base_url="https://custom-url.com"
        )

        with patch('oagent.plugins.llm.dashscope.AsyncOpenAI') as mock_openai:
            plugin._get_client(config)
            mock_openai.assert_called_once_with(
                api_key="config-api-key",
                base_url="https://custom-url.com"
            )

    def test_get_client_without_api_key_raises(self):
        """Test that missing API key raises error."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        config = LLMConfig(
            provider="dashscope",
            model_name="qwen3.5-plus",
        )

        with patch('oagent.plugins.llm.dashscope.settings') as mock_settings:
            mock_settings.dashscope_api_key = None
            mock_settings.dashscope_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

            with pytest.raises(ValueError, match="DashScope API key is required"):
                plugin._get_client(config)

    @pytest.mark.asyncio
    async def test_chat_streaming(self):
        """Test streaming chat completion."""
        from oagent.plugins.llm.dashscope import DashScopeLLMPlugin
        plugin = DashScopeLLMPlugin()
        config = LLMConfig(
            provider="dashscope",
            model_name="qwen3.5-plus",
            api_key="test-api-key"
        )
        messages = [Message(role="user", content="Hello")]

        # Mock the streaming response
        async def mock_stream():
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta.content = "Hello"
            yield mock_chunk

            mock_chunk2 = MagicMock()
            mock_chunk2.choices = [MagicMock()]
            mock_chunk2.choices[0].delta.content = "!"
            yield mock_chunk2

        with patch.object(plugin, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
            mock_get_client.return_value = mock_client

            result = []
            async for token in plugin.chat(messages, config):
                result.append(token)

            assert result == ["Hello", "!"]