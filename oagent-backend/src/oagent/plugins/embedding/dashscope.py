"""DashScope Embedding plugin implementation."""

from typing import List, Optional
from loguru import logger

from oagent.core.registry import register_plugin
from oagent.config.settings import settings
from oagent.plugins.embedding.base import EmbeddingPluginBase


@register_plugin("embedding", "dashscope")
class DashScopeEmbeddingPlugin(EmbeddingPluginBase):
    """DashScope Embedding plugin for text-embedding models.

    Uses OpenAI-compatible API mode provided by DashScope.
    Supports text-embedding-v4, v3, v2, v1 models.
    """

    @property
    def name(self) -> str:
        return "dashscope"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "DashScope (Alibaba) Embedding provider - OpenAI-compatible API"

    @property
    def supported_models(self) -> List[str]:
        """List of supported embedding models."""
        return [
            "text-embedding-v4",
            "text-embedding-v3",
            "text-embedding-v2",
            "text-embedding-v1",
        ]

    @property
    def embedding_dimension(self) -> int:
        """Return embedding dimension for default model."""
        return 1024  # text-embedding-v4 dimension

    def _get_client(self):
        """Get OpenAI-compatible client for DashScope."""
        from openai import AsyncOpenAI

        api_key = settings.dashscope_api_key
        base_url = settings.dashscope_base_url

        if not api_key:
            raise ValueError(
                "DashScope API key is required. Set DASHSCOPE_API_KEY environment variable."
            )

        return AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def embed_documents(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Embed documents using DashScope embedding models.

        Args:
            texts: List of texts to embed
            model: Embedding model to use (defaults to settings)

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If API key is not configured
            Exception: If embedding request fails
        """
        from openai import AsyncOpenAI

        model = model or settings.dashscope_embedding_model
        logger.info(f"DashScope embedding request: model={model}, texts={len(texts)}")

        client = self._get_client()

        try:
            response = await client.embeddings.create(
                input=texts,
                model=model,
            )
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"DashScope embedding error: {e}")
            raise

    async def embed_query(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Embed a query text.

        Args:
            text: Query text to embed
            model: Embedding model to use

        Returns:
            Embedding vector
        """
        embeddings = await self.embed_documents([text], model)
        return embeddings[0] if embeddings else []
