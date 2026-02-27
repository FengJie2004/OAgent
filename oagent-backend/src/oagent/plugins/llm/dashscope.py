"""DashScope (Alibaba Qwen) LLM plugin implementation."""

from typing import AsyncIterator, List, Optional
from loguru import logger

from oagent.core.registry import register_plugin
from oagent.config.settings import settings
from oagent.models.llm import LLMConfig, Message
from oagent.plugins.llm.base import LLMPluginBase


@register_plugin("llm", "dashscope")
class DashScopeLLMPlugin(LLMPluginBase):
    """DashScope LLM plugin for Alibaba Qwen models.

    Uses OpenAI-compatible API mode provided by DashScope.
    Supports Qwen series models for chat and text-embedding models for embeddings.
    """

    @property
    def name(self) -> str:
        return "dashscope"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "DashScope (Alibaba Qwen) LLM provider - OpenAI-compatible API"

    @property
    def supported_models(self) -> List[str]:
        """List of supported chat models."""
        return [
            # Qwen3.5 Series
            "qwen3.5-plus",
            "qwen3.5-turbo",
            "qwen3.5-longcontext",
            # Qwen3 Series
            "qwen3-235b-a22b",
            "qwen3-32b",
            # Qwen2.5 Series
            "qwen2.5-72b-instruct",
            "qwen2.5-32b-instruct",
            "qwen2.5-14b-instruct",
            "qwen2.5-7b-instruct",
            "qwen2.5-3b-instruct",
            "qwen2.5-1.5b-instruct",
            "qwen2.5-0.5b-instruct",
            # Qwen2 Series
            "qwen2-72b-instruct",
            "qwen2-57b-a14b-instruct",
            "qwen2-7b-instruct",
            # Qwen-Max Series
            "qwen-max",
            "qwen-max-latest",
            "qwen-max-longcontext",
            # Qwen-Plus Series
            "qwen-plus",
            "qwen-plus-latest",
            # Qwen-Turbo Series
            "qwen-turbo",
            "qwen-turbo-latest",
            # Qwen-Long
            "qwen-long",
        ]

    @property
    def supported_embedding_models(self) -> List[str]:
        """List of supported embedding models."""
        return [
            "text-embedding-v4",
            "text-embedding-v3",
            "text-embedding-v2",
            "text-embedding-v1",
        ]

    def _get_client(self, config: LLMConfig):
        """Get OpenAI-compatible client for DashScope.

        Args:
            config: LLM configuration

        Returns:
            AsyncOpenAI client configured for DashScope

        Raises:
            ValueError: If API key is not provided
        """
        from openai import AsyncOpenAI

        api_key = config.api_key or settings.dashscope_api_key
        base_url = config.base_url or settings.dashscope_base_url

        if not api_key:
            raise ValueError(
                "DashScope API key is required. Set DASHSCOPE_API_KEY environment "
                "variable or provide api_key in config."
            )

        return AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """Convert messages to OpenAI-compatible format.

        Args:
            messages: List of Message objects

        Returns:
            List of message dictionaries in OpenAI format
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def chat(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        """Stream chat completion.

        Args:
            messages: List of conversation messages
            config: LLM configuration

        Yields:
            Tokens from the model response
        """
        self.validate_config(config)
        client = self._get_client(config)

        logger.info(f"DashScope chat request: model={config.model_name}")

        response = await client.chat.completions.create(
            model=config.model_name,
            messages=self._convert_messages(messages),
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            stream=True,
        )

        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

    async def chat_complete(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> str:
        """Non-streaming chat completion.

        Args:
            messages: List of conversation messages
            config: LLM configuration

        Returns:
            Complete model response
        """
        self.validate_config(config)
        client = self._get_client(config)

        logger.info(f"DashScope chat complete request: model={config.model_name}")

        response = await client.chat.completions.create(
            model=config.model_name,
            messages=self._convert_messages(messages),
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            frequency_penalty=config.frequency_penalty,
            presence_penalty=config.presence_penalty,
            stream=False,
        )

        return response.choices[0].message.content

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using DashScope embedding models.

        Args:
            texts: List of texts to embed
            model: Embedding model to use (defaults to settings)

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If API key is not provided
            Exception: If embedding request fails
        """
        from openai import AsyncOpenAI

        api_key = settings.dashscope_api_key
        base_url = settings.dashscope_base_url
        model = model or settings.dashscope_embedding_model

        if not api_key:
            raise ValueError(
                "DashScope API key is required for embeddings. "
                "Set DASHSCOPE_API_KEY environment variable."
            )

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        logger.info(f"DashScope embedding request: model={model}, texts={len(texts)}")

        try:
            response = await client.embeddings.create(
                input=texts,
                model=model,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"DashScope embedding error: {e}")
            raise