"""OpenAI LLM plugin implementation."""

from typing import AsyncIterator, List, Optional
from loguru import logger

from oagent.core.registry import register_plugin
from oagent.models.llm import LLMConfig, Message
from oagent.plugins.llm.base import LLMPluginBase


@register_plugin("llm", "openai")
class OpenAILLMPlugin(LLMPluginBase):
    """OpenAI LLM plugin."""

    @property
    def name(self) -> str:
        return "openai"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "OpenAI LLM provider (GPT-4, GPT-4o, GPT-3.5)"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
        ]

    def _get_client(self, config: LLMConfig):
        """Get OpenAI client."""
        from openai import AsyncOpenAI

        return AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """Convert messages to OpenAI format."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def chat(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        """Stream chat completion."""
        self.validate_config(config)
        client = self._get_client(config)

        logger.info(f"OpenAI chat request: model={config.model_name}")

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
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def chat_complete(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> str:
        """Non-streaming chat completion."""
        self.validate_config(config)
        client = self._get_client(config)

        logger.info(f"OpenAI chat complete request: model={config.model_name}")

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
        """Generate embeddings."""
        from openai import AsyncOpenAI
        from oagent.config.settings import settings

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        model = model or "text-embedding-3-small"

        logger.info(f"OpenAI embedding request: model={model}, texts={len(texts)}")

        response = await client.embeddings.create(
            input=texts,
            model=model,
        )

        return [item.embedding for item in response.data]