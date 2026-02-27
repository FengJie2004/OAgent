"""VectorStore plugin base class."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from oagent.core.plugin_base import PluginBase


class Document(BaseModel):
    """Document model for vector store."""
    id: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = None
    embedding: Optional[List[float]] = None


class SearchResult(BaseModel):
    """Search result model."""
    document: Document
    score: float
    distance: float


class VectorStorePluginBase(PluginBase, ABC):
    """Base class for VectorStore plugins."""

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """List of supported vector store types/models."""
        pass

    @abstractmethod
    async def initialize(
        self,
        collection_name: str,
        embedding_dimension: int = 1536,
        persist_directory: Optional[str] = None
    ) -> None:
        """Initialize vector store.

        Args:
            collection_name: Collection name
            embedding_dimension: Dimension of embeddings
            persist_directory: Directory to persist data
        """
        pass

    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """Add documents to vector store.

        Args:
            documents: List of documents to add
            embeddings: Optional pre-computed embeddings

        Returns:
            List of document IDs
        """
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents.

        Args:
            query: Query text
            k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents by embedding vector.

        Args:
            embedding: Embedding vector
            k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def delete_documents(
        self,
        ids: List[str]
    ) -> bool:
        """Delete documents by IDs.

        Args:
            ids: List of document IDs to delete

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def get_document(
        self,
        id: str
    ) -> Optional[Document]:
        """Get document by ID.

        Args:
            id: Document ID

        Returns:
            Document or None
        """
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all documents from vector store.

        Returns:
            True if successful
        """
        pass
