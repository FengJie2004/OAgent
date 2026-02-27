"""Embedding plugin base class."""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

from oagent.core.plugin_base import PluginBase


class EmbeddingPluginBase(PluginBase, ABC):
    """Base class for Embedding plugins."""

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """List of supported embedding models."""
        pass

    @property
    def embedding_dimension(self) -> int:
        """Return the embedding dimension for the default model."""
        return 1536  # Default dimension

    @abstractmethod
    async def embed_documents(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Embed documents.

        Args:
            texts: List of texts to embed
            model: Embedding model to use

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
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
        pass

    def _normalize_embeddings(
        self,
        embeddings: List[List[float]]
    ) -> List[List[float]]:
        """Normalize embedding vectors."""
        embeddings_array = np.array(embeddings)
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        normalized = embeddings_array / norms
        return normalized.tolist()
