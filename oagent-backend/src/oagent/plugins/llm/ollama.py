"""Ollama LLM plugin implementation for local models."""

import asyncio
from typing import AsyncIterator, List, Optional
from loguru import logger

from oagent.core.registry import register_plugin
from oagent.config.settings import settings
from oagent.models.llm import LLMConfig, Message
from oagent.plugins.llm.base import LLMPluginBase
from oagent.plugins.embedding.base import EmbeddingPluginBase


@register_plugin("llm", "ollama")
class OllamaLLMPlugin(LLMPluginBase):
    """Ollama LLM plugin for local models.

    Features:
    - Full streaming support with astream()
    - Configurable base_url from settings
    - Proper error handling and timeout configuration
    - Support for popular open-source models
    """

    # Default timeout in seconds
    DEFAULT_TIMEOUT = 120.0

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Ollama local LLM provider with streaming support"

    @property
    def supported_models(self) -> List[str]:
        """List of supported embedding models."""
        return [
            "llama3.2",
            "llama3.1",
            "llama3",
            "llama2",
            "mistral",
            "mixtral",
            "codellama",
            "deepseek-coder",
            "qwen2.5",
            "qwen2.5-coder",
            "phi3",
            "phi4",
            "gemma2",
            "gemma3",
            "llava",
            "nomic-embed-text",
        ]

    def _get_client(self, config: LLMConfig):
        """Get Ollama chat client with timeout configuration."""
        from langchain_ollama import ChatOllama

        base_url = config.base_url or settings.ollama_base_url

        return ChatOllama(
            model=config.model_name,
            base_url=base_url,
            temperature=config.temperature,
            num_predict=config.max_tokens,
            timeout=self.DEFAULT_TIMEOUT,
        )

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """Convert messages to Ollama format."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def chat(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        """
        Stream chat completion with full streaming support.

        Args:
            messages: List of messages
            config: LLM configuration

        Yields:
            Tokens from the LLM stream

        Raises:
            ValueError: If configuration is invalid
            TimeoutError: If request times out
            Exception: If chat request fails
        """
        self.validate_config(config)
        client = self._get_client(config)

        logger.info(f"Ollama chat request: model={config.model_name}, base_url={client.base_url}")

        try:
            # Use astream() for proper streaming support
            async for chunk in client.astream(self._convert_messages(messages)):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content

        except asyncio.TimeoutError as e:
            logger.error(f"Ollama chat timeout: {e}")
            raise TimeoutError(f"Ollama request timed out after {self.DEFAULT_TIMEOUT}s") from e
        except Exception as e:
            logger.error(f"Ollama chat error: {type(e).__name__}: {e}")
            raise

    async def chat_complete(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> str:
        """
        Non-streaming chat completion.

        Args:
            messages: List of messages
            config: LLM configuration

        Returns:
            Complete response from the LLM

        Raises:
            ValueError: If configuration is invalid
            TimeoutError: If request times out
            Exception: If chat request fails
        """
        self.validate_config(config)
        client = self._get_client(config)

        logger.info(f"Ollama chat complete request: model={config.model_name}")

        try:
            response = await asyncio.wait_for(
                client.ainvoke(self._convert_messages(messages)),
                timeout=self.DEFAULT_TIMEOUT
            )
            return response.content

        except asyncio.TimeoutError as e:
            logger.error(f"Ollama chat complete timeout: {e}")
            raise TimeoutError(f"Ollama request timed out after {self.DEFAULT_TIMEOUT}s") from e
        except Exception as e:
            logger.error(f"Ollama chat complete error: {type(e).__name__}: {e}")
            raise

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings using Ollama embedding models.

        This method delegates to the OllamaEmbeddingPlugin for actual embedding generation.

        Args:
            texts: List of texts to embed
            model: Embedding model to use (defaults to nomic-embed-text)

        Returns:
            List of normalized embedding vectors

        Raises:
            ValueError: If texts list is empty
            TimeoutError: If request times out
            Exception: If embedding request fails
        """
        # Use the embedding plugin for actual embedding generation
        embedding_plugin = OllamaEmbeddingPlugin()
        return await embedding_plugin.embed_documents(texts, model)


@register_plugin("embedding", "ollama")
class OllamaEmbeddingPlugin(EmbeddingPluginBase):
    """Ollama Embedding plugin for local embedding models.

    Features:
    - Support for popular embedding models (nomic-embed-text, mxbai-embed-large, etc.)
    - Configurable base_url from settings
    - Proper error handling and timeout configuration
    - Normalized embeddings by default
    """

    # Default timeout in seconds
    DEFAULT_TIMEOUT = 60.0

    # Supported embedding models
    EMBEDDING_MODELS = [
        "nomic-embed-text",
        "nomic-embed-text-v1.5",
        "mxbai-embed-large",
        "all-minilm",
        "all-minilm:22m",
        "all-minilm:33m",
        "snowflake-arctic-embed",
        "bge-large",
        "bge-m3",
    ]

    # Embedding dimensions for each model
    MODEL_DIMENSIONS = {
        "nomic-embed-text": 768,
        "nomic-embed-text-v1.5": 768,
        "mxbai-embed-large": 1024,
        "all-minilm": 384,
        "all-minilm:22m": 384,
        "all-minilm:33m": 384,
        "snowflake-arctic-embed": 1024,
        "bge-large": 1024,
        "bge-m3": 1024,
    }

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Ollama local embedding provider"

    @property
    def supported_models(self) -> List[str]:
        """List of supported embedding models."""
        return self.EMBEDDING_MODELS

    @property
    def embedding_dimension(self) -> int:
        """Return embedding dimension for default model."""
        default_model = "nomic-embed-text"
        return self.MODEL_DIMENSIONS.get(default_model, 768)

    def _get_embeddings_client(self, model: str):
        """Get Ollama embeddings client with timeout configuration."""
        from langchain_ollama import OllamaEmbeddings

        base_url = settings.ollama_base_url

        return OllamaEmbeddings(
            model=model,
            base_url=base_url,
        )

    async def embed_documents(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Embed documents using Ollama embedding models.

        Args:
            texts: List of texts to embed
            model: Embedding model to use (defaults to nomic-embed-text)

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If texts list is empty
            TimeoutError: If request times out
            Exception: If embedding request fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        model = model or "nomic-embed-text"
        logger.info(f"Ollama embedding request: model={model}, texts={len(texts)}")

        try:
            embeddings = self._get_embeddings_client(model)
            result = await asyncio.wait_for(
                embeddings.aembed_documents(texts),
                timeout=self.DEFAULT_TIMEOUT
            )

            # Normalize embeddings
            normalized = self._normalize_embeddings(result)
            logger.debug(f"Generated {len(normalized)} normalized embeddings")
            return normalized

        except asyncio.TimeoutError as e:
            logger.error(f"Ollama embedding timeout: {e}")
            raise TimeoutError(f"Ollama embedding request timed out after {self.DEFAULT_TIMEOUT}s") from e
        except Exception as e:
            logger.error(f"Ollama embedding error: {type(e).__name__}: {e}")
            raise

    async def embed_query(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Embed a query text.

        Args:
            text: Query text to embed
            model: Embedding model to use

        Returns:
            Embedding vector

        Raises:
            ValueError: If text is empty
            TimeoutError: If request times out
            Exception: If embedding request fails
        """
        if not text:
            raise ValueError("Query text cannot be empty")

        embeddings = await self.embed_documents([text], model)
        return embeddings[0] if embeddings else []