"""OpenAI LLM plugin implementation."""

import asyncio
from typing import AsyncIterator, List, Optional
from loguru import logger

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    AsyncRetrying,
)

from oagent.core.registry import register_plugin
from oagent.config.settings import settings
from oagent.models.llm import LLMConfig, Message
from oagent.plugins.llm.base import LLMPluginBase
from oagent.plugins.embedding.base import EmbeddingPluginBase


# Rate limit error status codes
RATE_LIMIT_STATUS_CODES = [429, 500, 502, 503, 504]


def _is_rate_limit_error(exception: Exception) -> bool:
    """Check if exception is a rate limit error."""
    from openai import RateLimitError, APIConnectionError, APIStatusError

    if isinstance(exception, RateLimitError):
        return True
    if isinstance(exception, APIConnectionError):
        return True
    if isinstance(exception, APIStatusError):
        return exception.status_code in RATE_LIMIT_STATUS_CODES
    return False


@register_plugin("llm", "openai")
class OpenAILLMPlugin(LLMPluginBase):
    """OpenAI LLM plugin with full feature support.

    Features:
    - All LLM methods implemented (chat, chat_complete, embed)
    - Full streaming support with astream()
    - Azure OpenAI configuration support (optional)
    - Rate limit handling with exponential backoff retries
    - Comprehensive error handling
    """

    # Default timeout in seconds
    DEFAULT_TIMEOUT = 120.0

    # Retry configuration
    MAX_RETRY_ATTEMPTS = 3
    RETRY_MIN_WAIT = 1.0
    RETRY_MAX_WAIT = 10.0

    @property
    def name(self) -> str:
        return "openai"

    @property
    def version(self) -> str:
        return "0.2.0"

    @property
    def description(self) -> str:
        return "OpenAI LLM provider (GPT-4, GPT-4o, GPT-3.5) with Azure support"

    @property
    def supported_models(self) -> List[str]:
        """List of supported models."""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4o-2024-05-13",
            "gpt-4o-2024-08-06",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4-0125-preview",
            "gpt-4-1106-preview",
            "gpt-4",
            "gpt-4-0613",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-0125",
            "o1-preview",
            "o1-mini",
            "o1",
        ]

    def _get_client(self, config: LLMConfig, for_embedding: bool = False):
        """
        Get OpenAI client (standard or Azure).

        Args:
            config: LLM configuration
            for_embedding: Whether this client is for embeddings (uses different settings)

        Returns:
            AsyncOpenAI or AsyncAzureOpenAI client
        """
        from openai import AsyncOpenAI, AsyncAzureOpenAI

        # Check for Azure OpenAI configuration
        azure_deployment = config.extra.get("azure_deployment") if hasattr(config, 'extra') else None
        azure_endpoint = config.extra.get("azure_endpoint") if hasattr(config, 'extra') else None
        azure_api_version = config.extra.get("azure_api_version") if hasattr(config, 'extra') else None

        # Also check settings for Azure configuration
        if not azure_endpoint:
            azure_endpoint = getattr(settings, 'openai_azure_endpoint', None)
        if not azure_deployment:
            azure_deployment = getattr(settings, 'openai_azure_deployment', None)
        if not azure_api_version:
            azure_api_version = getattr(settings, 'openai_azure_api_version', None)

        # Use Azure client if endpoint is configured
        if azure_endpoint and azure_deployment:
            logger.info("Using Azure OpenAI configuration")
            return AsyncAzureOpenAI(
                azure_endpoint=azure_endpoint,
                azure_deployment=azure_deployment,
                api_version=azure_api_version or "2024-02-15-preview",
                api_key=config.api_key or settings.openai_api_key,
                timeout=self.DEFAULT_TIMEOUT,
            )

        # Standard OpenAI client
        api_key = config.api_key or settings.openai_api_key
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or provide api_key in config."
            )

        return AsyncOpenAI(
            api_key=api_key,
            base_url=config.base_url,
            timeout=self.DEFAULT_TIMEOUT,
        )

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """Convert messages to OpenAI format."""
        result = []
        for msg in messages:
            message_dict = {"role": msg.role, "content": msg.content}
            if msg.name:
                message_dict["name"] = msg.name
            result.append(message_dict)
        return result

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
            ValueError: If API key is not configured
            TimeoutError: If request times out
            Exception: If chat request fails after retries
        """
        self.validate_config(config)

        logger.info(f"OpenAI streaming chat request: model={config.model_name}")

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.MAX_RETRY_ATTEMPTS),
                wait=wait_exponential(
                    multiplier=1,
                    min=self.RETRY_MIN_WAIT,
                    max=self.RETRY_MAX_WAIT
                ),
                retry=retry_if_exception_type(_is_rate_limit_error),
                reraise=True,
            ):
                with attempt:
                    client = self._get_client(config)
                    response = await client.chat.completions.create(
                        model=config.model_name,
                        messages=self._convert_messages(messages),
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        top_p=config.top_p,
                        frequency_penalty=config.frequency_penalty,
                        presence_penalty=config.presence_penalty,
                        stream=True,
                        timeout=self.DEFAULT_TIMEOUT,
                    )

                    async for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content

        except asyncio.TimeoutError as e:
            logger.error(f"OpenAI chat timeout: {e}")
            raise TimeoutError(f"OpenAI request timed out after {self.DEFAULT_TIMEOUT}s") from e
        except Exception as e:
            logger.error(f"OpenAI chat error after {attempt.retry_state.attempt_number} attempts: {type(e).__name__}: {e}")
            raise

    async def chat_complete(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> str:
        """
        Non-streaming chat completion with rate limit retry.

        Args:
            messages: List of messages
            config: LLM configuration

        Returns:
            Complete response from the LLM

        Raises:
            ValueError: If API key is not configured
            TimeoutError: If request times out
            Exception: If chat request fails after retries
        """
        self.validate_config(config)

        logger.info(f"OpenAI chat complete request: model={config.model_name}")

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.MAX_RETRY_ATTEMPTS),
                wait=wait_exponential(
                    multiplier=1,
                    min=self.RETRY_MIN_WAIT,
                    max=self.RETRY_MAX_WAIT
                ),
                retry=retry_if_exception_type(_is_rate_limit_error),
                reraise=True,
            ):
                with attempt:
                    client = self._get_client(config)
                    response = await client.chat.completions.create(
                        model=config.model_name,
                        messages=self._convert_messages(messages),
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        top_p=config.top_p,
                        frequency_penalty=config.frequency_penalty,
                        presence_penalty=config.presence_penalty,
                        stream=False,
                        timeout=self.DEFAULT_TIMEOUT,
                    )
                    return response.choices[0].message.content

        except asyncio.TimeoutError as e:
            logger.error(f"OpenAI chat complete timeout: {e}")
            raise TimeoutError(f"OpenAI request timed out after {self.DEFAULT_TIMEOUT}s") from e
        except Exception as e:
            logger.error(f"OpenAI chat complete error after {attempt.retry_state.attempt_number} attempts: {type(e).__name__}: {e}")
            raise

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings with rate limit retry.

        Args:
            texts: List of texts to embed
            model: Embedding model to use

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If API key is not configured or texts is empty
            TimeoutError: If request times out
            Exception: If embedding request fails after retries
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        from openai import AsyncOpenAI

        model = model or "text-embedding-3-small"
        logger.info(f"OpenAI embedding request: model={model}, texts={len(texts)}")

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.MAX_RETRY_ATTEMPTS),
                wait=wait_exponential(
                    multiplier=1,
                    min=self.RETRY_MIN_WAIT,
                    max=self.RETRY_MAX_WAIT
                ),
                retry=retry_if_exception_type(_is_rate_limit_error),
                reraise=True,
            ):
                with attempt:
                    client = self._get_client({"api_key": settings.openai_api_key}, for_embedding=True)
                    response = await client.embeddings.create(
                        input=texts,
                        model=model,
                        timeout=self.DEFAULT_TIMEOUT,
                    )
                    return [item.embedding for item in response.data]

        except asyncio.TimeoutError as e:
            logger.error(f"OpenAI embedding timeout: {e}")
            raise TimeoutError(f"OpenAI embedding request timed out after {self.DEFAULT_TIMEOUT}s") from e
        except Exception as e:
            logger.error(f"OpenAI embedding error after {attempt.retry_state.attempt_number} attempts: {type(e).__name__}: {e}")
            raise


@register_plugin("embedding", "openai")
class OpenAIEmbeddingPlugin(EmbeddingPluginBase):
    """OpenAI Embedding plugin.

    Features:
    - Support for text-embedding-3-small and text-embedding-3-large
    - Rate limit handling with exponential backoff retries
    - Normalized embeddings by default
    - Comprehensive error handling
    """

    # Default timeout in seconds
    DEFAULT_TIMEOUT = 60.0

    # Retry configuration
    MAX_RETRY_ATTEMPTS = 3
    RETRY_MIN_WAIT = 1.0
    RETRY_MAX_WAIT = 10.0

    # Supported embedding models with their dimensions
    EMBEDDING_MODELS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    @property
    def name(self) -> str:
        return "openai"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "OpenAI Embedding provider (text-embedding-3-small, text-embedding-3-large)"

    @property
    def supported_models(self) -> List[str]:
        """List of supported embedding models."""
        return list(self.EMBEDDING_MODELS.keys())

    @property
    def embedding_dimension(self) -> int:
        """Return embedding dimension for default model."""
        default_model = "text-embedding-3-small"
        return self.EMBEDDING_MODELS.get(default_model, 1536)

    def _get_client(self):
        """Get OpenAI client."""
        from openai import AsyncOpenAI

        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable."
            )

        return AsyncOpenAI(
            api_key=api_key,
            timeout=self.DEFAULT_TIMEOUT,
        )

    async def embed_documents(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Embed documents using OpenAI embedding models.

        Args:
            texts: List of texts to embed
            model: Embedding model to use (defaults to text-embedding-3-small)

        Returns:
            List of normalized embedding vectors

        Raises:
            ValueError: If API key is not configured or texts is empty
            TimeoutError: If request times out
            Exception: If embedding request fails after retries
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        model = model or "text-embedding-3-small"
        if model not in self.EMBEDDING_MODELS:
            raise ValueError(
                f"Model {model} not supported. Supported models: {self.supported_models}"
            )

        logger.info(f"OpenAI embedding request: model={model}, texts={len(texts)}")

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.MAX_RETRY_ATTEMPTS),
                wait=wait_exponential(
                    multiplier=1,
                    min=self.RETRY_MIN_WAIT,
                    max=self.RETRY_MAX_WAIT
                ),
                retry=retry_if_exception_type(_is_rate_limit_error),
                reraise=True,
            ):
                with attempt:
                    client = self._get_client()
                    response = await client.embeddings.create(
                        input=texts,
                        model=model,
                        timeout=self.DEFAULT_TIMEOUT,
                    )
                    embeddings = [item.embedding for item in response.data]

            # Normalize embeddings
            normalized = self._normalize_embeddings(embeddings)
            logger.debug(f"Generated {len(normalized)} normalized embeddings")
            return normalized

        except asyncio.TimeoutError as e:
            logger.error(f"OpenAI embedding timeout: {e}")
            raise TimeoutError(f"OpenAI embedding request timed out after {self.DEFAULT_TIMEOUT}s") from e
        except Exception as e:
            logger.error(f"OpenAI embedding error after {attempt.retry_state.attempt_number} attempts: {type(e).__name__}: {e}")
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
            Normalized embedding vector

        Raises:
            ValueError: If API key is not configured or text is empty
            TimeoutError: If request times out
            Exception: If embedding request fails after retries
        """
        if not text:
            raise ValueError("Query text cannot be empty")

        embeddings = await self.embed_documents([text], model)
        return embeddings[0] if embeddings else []