"""ChromaDB VectorStore plugin implementation."""

from typing import List, Optional, Dict, Any
from loguru import logger

from oagent.core.registry import register_plugin
from oagent.plugins.vectorstore.base import VectorStorePluginBase, Document, SearchResult


@register_plugin("vectorstore", "chroma")
class ChromaVectorStorePlugin(VectorStorePluginBase):
    """ChromaDB VectorStore plugin.

    Uses langchain_chroma.Chroma for integration.
    Supports local persistence and in-memory modes.
    """

    @property
    def name(self) -> str:
        return "chroma"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "ChromaDB vector store - lightweight, local persistence supported"

    @property
    def supported_models(self) -> List[str]:
        """List of supported chroma types."""
        return ["persistent", "memory"]

    def __init__(self):
        self._client = None
        self._collection = None
        self._persist_directory: Optional[str] = None
        self._logger = logger

    async def initialize(
        self,
        collection_name: str,
        embedding_dimension: int = 1024,
        persist_directory: Optional[str] = None
    ) -> None:
        """Initialize ChromaDB vector store.

        Args:
            collection_name: Collection name
            embedding_dimension: Dimension of embeddings (default 1024 for text-embedding-v4)
            persist_directory: Directory to persist data (None for in-memory)
        """
        import chromadb
        from chromadb.config import Settings

        self._persist_directory = persist_directory

        if persist_directory:
            # Persistent mode
            self._client = chromadb.PersistentClient(
                path=persist_directory,
            )
            self._logger.info(f"ChromaDB initialized with persistence: {persist_directory}")
        else:
            # In-memory mode
            self._client = chromadb.EphemeralClient()
            self._logger.info("ChromaDB initialized in ephemeral mode")

        # Get or create collection
        # ChromaDB auto-creates collections with HNSW index
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine", "dimension": embedding_dimension}
        )
        self._logger.info(f"Collection ready: {collection_name}")

    async def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """Add documents to ChromaDB.

        Args:
            documents: List of documents to add
            embeddings: Optional pre-computed embeddings

        Returns:
            List of document IDs
        """
        if not self._collection:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        ids = []
        contents = []
        metadatas = []
        doc_embeddings = []

        for i, doc in enumerate(documents):
            # Generate ID if not provided
            doc_id = doc.id or f"doc_{len(ids) + 1}"
            ids.append(doc_id)
            contents.append(doc.content)
            metadatas.append(doc.metadata or {})

            if embeddings:
                doc_embeddings.append(embeddings[i])

        # Add to ChromaDB
        if doc_embeddings:
            self._collection.add(
                ids=ids,
                embeddings=doc_embeddings,
                documents=contents,
                metadatas=metadatas
            )
        else:
            # ChromaDB can embed automatically with some configurations
            self._collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )

        self._logger.info(f"Added {len(documents)} documents to ChromaDB")
        return ids

    async def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents by query text.

        Args:
            query: Query text
            k: Number of results
            filter_dict: Optional metadata filters

        Returns:
            List of search results
        """
        if not self._collection:
            raise RuntimeError("Vector store not initialized.")

        # ChromaDB requires embeddings for search
        # The caller should provide embeddings or configure an embedding function
        # For now, return empty results - caller should use similarity_search_by_vector
        self._logger.warning(
            "similarity_search requires embedding function configured. "
            "Use similarity_search_by_vector with pre-computed embeddings."
        )
        return []

    async def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents by embedding vector.

        Args:
            embedding: Embedding vector
            k: Number of results
            filter_dict: Optional metadata filters (where clause)

        Returns:
            List of search results
        """
        if not self._collection:
            raise RuntimeError("Vector store not initialized.")

        # Convert filter_dict to ChromaDB where clause
        where = filter_dict if filter_dict else None

        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        search_results = []
        if results and results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                content = results['documents'][0][i] if results['documents'] else ""
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0.0

                # Convert distance to similarity score (cosine distance to cosine similarity)
                score = 1.0 - distance

                search_results.append(
                    SearchResult(
                        document=Document(
                            id=doc_id,
                            content=content,
                            metadata=metadata
                        ),
                        score=score,
                        distance=distance
                    )
                )

        self._logger.debug(f"Found {len(search_results)} results")
        return search_results

    async def delete_documents(
        self,
        ids: List[str]
    ) -> bool:
        """Delete documents by IDs.

        Args:
            ids: List of document IDs

        Returns:
            True if successful
        """
        if not self._collection:
            raise RuntimeError("Vector store not initialized.")

        self._collection.delete(ids=ids)
        self._logger.info(f"Deleted {len(ids)} documents")
        return True

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
        if not self._collection:
            raise RuntimeError("Vector store not initialized.")

        results = self._collection.get(ids=[id], include=["documents", "metadatas"])

        if results and results['ids'] and len(results['ids']) > 0:
            return Document(
                id=results['ids'][0],
                content=results['documents'][0] if results['documents'] else "",
                metadata=results['metadatas'][0] if results['metadatas'] else {}
            )

        return None

    async def clear(self) -> bool:
        """Clear all documents from collection.

        Returns:
            True if successful
        """
        if not self._collection:
            raise RuntimeError("Vector store not initialized.")

        # Delete all documents by getting all IDs first
        all_docs = self._collection.get(include=[])
        if all_docs and all_docs['ids']:
            self._collection.delete(ids=all_docs['ids'])

        self._logger.info("Cleared all documents from collection")
        return True
