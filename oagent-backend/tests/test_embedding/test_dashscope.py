"""Tests for DashScope Embedding plugin."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from oagent.plugins.embedding.dashscope import DashScopeEmbeddingPlugin


class TestDashScopeEmbeddingPlugin:
    """Tests for DashScope Embedding plugin."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return DashScopeEmbeddingPlugin()

    def test_plugin_name(self, plugin):
        """Test plugin name."""
        assert plugin.name == "dashscope"

    def test_plugin_version(self, plugin):
        """Test plugin version."""
        assert plugin.version == "0.1.0"

    def test_plugin_description(self, plugin):
        """Test plugin description."""
        assert "DashScope" in plugin.description
        assert "Embedding" in plugin.description

    def test_supported_models(self, plugin):
        """Test supported embedding models."""
        models = plugin.supported_models
        assert "text-embedding-v4" in models
        assert "text-embedding-v3" in models
        assert "text-embedding-v2" in models

    def test_embedding_dimension(self, plugin):
        """Test embedding dimension."""
        assert plugin.embedding_dimension == 1024

    @pytest.mark.asyncio
    async def test_embed_documents(self, plugin):
        """Test embedding documents."""
        texts = ["Hello world", "Test embedding"]

        with patch('oagent.plugins.embedding.dashscope.settings') as mock_settings:
            mock_settings.dashscope_api_key = "test-key"
            mock_settings.dashscope_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            mock_settings.dashscope_embedding_model = "text-embedding-v4"

            with patch('openai.AsyncOpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.data = [
                    MagicMock(embedding=[0.1, 0.2, 0.3]),
                    MagicMock(embedding=[0.4, 0.5, 0.6])
                ]
                mock_client.embeddings.create = AsyncMock(return_value=mock_response)
                mock_openai.return_value = mock_client

                result = await plugin.embed_documents(texts)

                assert len(result) == 2
                assert result[0] == [0.1, 0.2, 0.3]
                assert result[1] == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_embed_query(self, plugin):
        """Test embedding a single query."""
        text = "Hello world"

        with patch('oagent.plugins.embedding.dashscope.settings') as mock_settings:
            mock_settings.dashscope_api_key = "test-key"
            mock_settings.dashscope_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

            with patch('openai.AsyncOpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
                mock_client.embeddings.create = AsyncMock(return_value=mock_response)
                mock_openai.return_value = mock_client

                result = await plugin.embed_query(text)

                assert result == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_embed_documents_no_api_key(self, plugin):
        """Test error when API key is missing."""
        with patch('oagent.plugins.embedding.dashscope.settings') as mock_settings:
            mock_settings.dashscope_api_key = None

            with pytest.raises(ValueError, match="DashScope API key is required"):
                await plugin.embed_documents(["test"])

    @pytest.mark.asyncio
    async def test_embed_documents_error(self, plugin):
        """Test error handling."""
        with patch('oagent.plugins.embedding.dashscope.settings') as mock_settings:
            mock_settings.dashscope_api_key = "test-key"

            with patch('openai.AsyncOpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_client.embeddings.create = AsyncMock(side_effect=Exception("API error"))
                mock_openai.return_value = mock_client

                with pytest.raises(Exception, match="API error"):
                    await plugin.embed_documents(["test"])

    def test_get_client(self, plugin):
        """Test client creation."""
        with patch('oagent.plugins.embedding.dashscope.settings') as mock_settings:
            mock_settings.dashscope_api_key = "test-key"
            mock_settings.dashscope_base_url = "https://test-url.com"

            with patch('openai.AsyncOpenAI') as mock_openai:
                plugin._get_client()
                mock_openai.assert_called_once_with(
                    api_key="test-key",
                    base_url="https://test-url.com"
                )
