"""LLM plugin base class and implementations."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional
from pydantic import BaseModel

from oagent.core.plugin_base import PluginBase
from oagent.models.llm import LLMConfig, Message


class LLMPluginBase(PluginBase, ABC):
    """Base class for LLM plugins."""

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """List of supported models."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        """
        Chat with the LLM (streaming).

        Args:
            messages: List of messages
            config: LLM configuration

        Yields:
            Tokens from the LLM
        """
        pass

    @abstractmethod
    async def chat_complete(
        self,
        messages: List[Message],
        config: LLMConfig
    ) -> str:
        """
        Chat with the LLM (non-streaming).

        Args:
            messages: List of messages
            config: LLM configuration

        Returns:
            Complete response
        """
        pass

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed
            model: Embedding model to use

        Returns:
            List of embedding vectors
        """
        pass

    def validate_config(self, config: LLMConfig) -> bool:
        """
        Validate the configuration.

        Args:
            config: LLM configuration

        Returns:
            True if valid

        Raises:
            ValidationError: If configuration is invalid
        """
        if config.model_name not in self.supported_models:
            raise ValueError(
                f"Model {config.model_name} not supported. "
                f"Supported models: {self.supported_models}"
            )
        return True