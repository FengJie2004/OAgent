"""Ollama LLM plugin implementation for local models."""

from typing import AsyncIterator, List, Optional
from loguru import logger

from oagent.core.registry import register_plugin
from oagent.config.settings import settings
from oagent.models.llm import LLMConfig, Message
from oagent.plugins.llm.base import LLMPluginBase


@register_plugin("llm", "ollama")
class OllamaLLMPlugin(LLMPluginBase):
    """Ollama LLM plugin for local models."""

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Ollama local LLM provider"

    @property
    def supported_models(self) -> List[str]:
        # Ollama supports many models, these are popular ones
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
            "phi3",
            "gemma2",
        ]

    def _get_client(self, config: LLMConfig):
        """Get Ollama client."""
        from langchain_ollama import ChatOllama

        base_url = config.base_url or settings.ollama_base_url

        return ChatOllama(
            model=config.model_name,
            base_url=base_url,
            temperature=config.temperature,
            num_predict=config.max_tokens,
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
        """Stream chat completion."""
        self.validate_config(config)
        client = self._get_client(config)

        logger.info(f"Ollama chat request: model={config.model_name}")

        try:
            response = await client.ainvoke(
                self._convert_messages(messages)
            )

            # Ollama returns complete response, yield as single chunk
            yield response.content

        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise

    async def chat_complete(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> str:
        """Non-streaming chat completion."""
        self.validate_config(config)
        client = self._get_client(config)

        logger.info(f"Ollama chat complete request: model={config.model_name}")

        response = await client.ainvoke(
            self._convert_messages(messages)
        )

        return response.content

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using Ollama."""
        from langchain_ollama import OllamaEmbeddings

        model = model or "nomic-embed-text"
        base_url = settings.ollama_base_url

        logger.info(f"Ollama embedding request: model={model}, texts={len(texts)}")

        embeddings = OllamaEmbeddings(
            model=model,
            base_url=base_url,
        )

        return await embeddings.aembed_documents(texts)