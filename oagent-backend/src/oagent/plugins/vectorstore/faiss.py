"""FAISS VectorStore plugin implementation."""

from typing import List, Optional, Dict, Any
from pathlib import Path
import uuid
from loguru import logger

from oagent.core.registry import register_plugin
from oagent.plugins.vectorstore.base import VectorStorePluginBase, Document, SearchResult


@register_plugin("vectorstore", "faiss")
class FAISSVectorStorePlugin(VectorStorePluginBase):
    """FAISS VectorStore plugin.

    Uses langchain_community.vectorstores.FAISS for integration.
    Supports in-memory and local persistence modes.
    Supports L2 (Euclidean) and Inner Product index types.
    """

    @property
    def name(self) -> str:
        return "faiss"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "FAISS vector store - Facebook AI Similarity Search with L2 and Inner Product support"

    @property
    def supported_models(self) -> List[str]:
        """List of supported FAISS index types."""
        return ["l2", "inner_product", "flat"]

    def __init__(self):
        self._vectorstore = None
        self._embedding_dimension: int = 0
        self._index_type: str = "l2"
        self._logger = logger
        # Track document metadata for retrieval
        self._doc_store: Dict[str, Document] = {}
        self._persist_directory: Optional[str] = None
        self._collection_name: str = ""

    def _create_embedding_function(self):
        """Create an embedding function for FAISS.

        FAISS requires an embedding function, but we handle embeddings externally.
        This dummy function is required by the FAISS interface.
        """
        from langchain_core.embeddings import Embeddings

        class FakeEmbeddings(Embeddings):
            """Fake embeddings that returns zero vectors.

            Real embeddings should be provided externally.
            """

            def __init__(self, dimension: int = 1536):
                self.dimension = dimension

            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                """Return zero embeddings for documents."""
                return [[0.0] * self.dimension for _ in texts]

            def embed_query(self, text: str) -> List[float]:
                """Return zero embedding for query."""
                return [0.0] * self.dimension

        return FakeEmbeddings(self._embedding_dimension)

    async def initialize(
        self,
        collection_name: str,
        embedding_dimension: int = 1536,
        persist_directory: Optional[str] = None,
        index_type: str = "l2"
    ) -> None:
        """Initialize FAISS vector store.

        Args:
            collection_name: Collection name (used as identifier for persistence)
            embedding_dimension: Dimension of embeddings
            persist_directory: Directory to persist data (None for in-memory)
            index_type: Type of FAISS index - "l2" or "inner_product"
        """
        import faiss
        from langchain_community.vectorstores import FAISS
        from langchain_community.docstore.in_memory import InMemoryDocstore

        self._embedding_dimension = embedding_dimension
        self._index_type = index_type
        self._doc_store = {}
        self._persist_directory = persist_directory
        self._collection_name = collection_name

        # Validate index type
        if index_type not in self.supported_models:
            raise ValueError(
                f"Unsupported index type: {index_type}. "
                f"Supported types: {self.supported_models}"
            )

        # Create embedding function (required by LangChain FAISS)
        embedding_func = self._create_embedding_function()

        # Create FAISS index based on type
        if index_type == "inner_product":
            faiss_index = faiss.IndexFlatIP(embedding_dimension)
        else:  # l2 or flat
            faiss_index = faiss.IndexFlatL2(embedding_dimension)

        # Create docstore
        docstore = InMemoryDocstore()

        if persist_directory:
            # Try to load existing index
            index_path = Path(persist_directory) / collection_name
            index_file = index_path / "index.faiss"

            if index_file.exists():
                # Load existing FAISS index
                self._vectorstore = FAISS.load_local(
                    folder_path=str(index_path),
                    embeddings=embedding_func,
                    allow_dangerous_deserialization=True
                )
                self._logger.info(f"FAISS index loaded from: {index_path}")
            else:
                # Create new FAISS instance with proper index
                self._vectorstore = FAISS(
                    embedding_function=embedding_func,
                    index=faiss_index,
                    docstore=docstore,
                    index_to_docstore_id={}
                )
                self._logger.info(f"FAISS initialized with new {index_type} index (persist: {persist_directory})")
        else:
            # In-memory mode - create FAISS with proper index
            self._vectorstore = FAISS(
                embedding_function=embedding_func,
                index=faiss_index,
                docstore=docstore,
                index_to_docstore_id={}
            )
            self._logger.info(f"FAISS initialized in memory mode with {index_type} index")

    async def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """Add documents to FAISS vector store.

        Args:
            documents: List of documents to add
            embeddings: Optional pre-computed embeddings

        Returns:
            List of document IDs

        Raises:
            RuntimeError: If vector store not initialized
            ValueError: If embeddings dimension mismatch
        """
        if not self._vectorstore:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        from langchain_core.documents import Document as LangChainDocument

        ids = []
        langchain_docs = []

        for i, doc in enumerate(documents):
            # Generate ID if not provided
            doc_id = doc.id or str(uuid.uuid4())
            ids.append(doc_id)

            # Create LangChain document for FAISS
            langchain_doc = LangChainDocument(
                page_content=doc.content,
                metadata=doc.metadata or {}
            )
            langchain_docs.append(langchain_doc)

            # Store document for later retrieval
            self._doc_store[doc_id] = doc

        # Add to FAISS with embeddings
        if embeddings:
            # Validate embedding dimensions
            for emb in embeddings:
                if len(emb) != self._embedding_dimension:
                    raise ValueError(
                        f"Embedding dimension mismatch: expected {self._embedding_dimension}, "
                        f"got {len(emb)}"
                    )

            # Use add_embeddings method - expects iterable of (text, embedding) tuples
            text_embeddings = list(zip(
                [doc.page_content for doc in langchain_docs],
                embeddings
            ))

            self._vectorstore.add_embeddings(
                text_embeddings=text_embeddings,
                metadatas=[doc.metadata or {} for doc in documents],
                ids=ids
            )

            self._logger.info(f"Added {len(documents)} documents with embeddings to FAISS")
        else:
            # Without embeddings, use zero embeddings
            zero_embeddings = [
                [0.0] * self._embedding_dimension for _ in documents
            ]

            text_embeddings = list(zip(
                [doc.page_content for doc in langchain_docs],
                zero_embeddings
            ))

            self._vectorstore.add_embeddings(
                text_embeddings=text_embeddings,
                metadatas=[doc.metadata or {} for doc in documents],
                ids=ids
            )

            self._logger.warning(
                "Documents added without embeddings - zero vectors used. "
                "Search results will not be meaningful."
            )

        return ids

    async def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents by query text.

        Note: This method requires an embedding function to be configured.
        For FAISS with external embeddings, use similarity_search_by_vector.

        Args:
            query: Query text
            k: Number of results
            filter_dict: Optional metadata filters (not supported by FAISS)

        Returns:
            List of search results
        """
        if not self._vectorstore:
            raise RuntimeError("Vector store not initialized.")

        self._logger.warning(
            "similarity_search requires embedding function. "
            "Use similarity_search_by_vector with pre-computed embeddings for FAISS."
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
            filter_dict: Optional metadata filters (not supported by FAISS)

        Returns:
            List of search results with scores and distances
        """
        if not self._vectorstore:
            raise RuntimeError("Vector store not initialized.")

        import numpy as np

        # Check if index is empty
        index = self._vectorstore.index
        if index is None or index.ntotal == 0:
            self._logger.debug("FAISS index is empty")
            return []

        # Convert embedding to numpy array
        query_embedding = np.array([embedding], dtype=np.float32)

        # Search the index - FAISS returns (distances, indices)
        distances, indices = index.search(query_embedding, k)

        search_results = []
        distances = distances[0]
        indices = indices[0]

        for i, idx in enumerate(indices):
            if idx == -1:  # FAISS returns -1 for not found
                continue

            # Get document ID from index_to_docstore_id mapping
            try:
                doc_id = self._vectorstore.index_to_docstore_id[idx]
            except (KeyError, IndexError, AttributeError):
                self._logger.warning(f"Document ID not found for index {idx}")
                continue

            # Retrieve document from our store
            stored_doc = self._doc_store.get(doc_id)
            if not stored_doc:
                # Try to get from FAISS docstore
                try:
                    faiss_doc = self._vectorstore.docstore.search(doc_id)
                    content = faiss_doc.page_content if faiss_doc else ""
                    metadata = faiss_doc.metadata if faiss_doc else {}
                except Exception:
                    content = ""
                    metadata = {}
                stored_doc = Document(
                    id=doc_id,
                    content=content,
                    metadata=metadata
                )

            distance = float(distances[i])

            # Convert distance to similarity score based on index type
            if self._index_type == "inner_product":
                # For inner product, higher score = more similar
                score = distance
                # Convert to distance-like metric for consistency
                distance = max(0.0, 1.0 - score)
            else:
                # For L2, lower distance = more similar
                # Convert L2 distance to similarity score (using exponential decay)
                score = float(np.exp(-distance))

            search_results.append(
                SearchResult(
                    document=stored_doc,
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

        Note: FAISS does not support efficient deletion.
        This method removes from tracking but the index vectors remain.
        For complete deletion, a rebuild would be required.

        Args:
            ids: List of document IDs to delete

        Returns:
            True if successful
        """
        if not self._vectorstore:
            raise RuntimeError("Vector store not initialized.")

        if not ids:
            return True

        # Remove from our document store
        for doc_id in ids:
            self._doc_store.pop(doc_id, None)

        # Note: FAISS doesn't support efficient deletion
        # We remove from tracking, but vectors remain in index
        # For complete removal, the index would need to be rebuilt
        self._logger.info(f"Removed {len(ids)} documents from tracking (FAISS index not rebuilt)")
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
        if not self._vectorstore:
            raise RuntimeError("Vector store not initialized.")

        # Check our document store first
        if id in self._doc_store:
            return self._doc_store[id]

        # Try FAISS docstore
        try:
            doc = self._vectorstore.docstore.search(id)
            if doc:
                return Document(
                    id=id,
                    content=doc.page_content,
                    metadata=doc.metadata or {}
                )
        except Exception:
            pass

        return None

    async def clear(self) -> bool:
        """Clear all documents from FAISS index.

        Returns:
            True if successful
        """
        if not self._vectorstore:
            raise RuntimeError("Vector store not initialized.")

        import faiss
        from langchain_community.vectorstores import FAISS
        from langchain_community.docstore.in_memory import InMemoryDocstore

        # Recreate index and docstore
        embedding_func = self._create_embedding_function()

        if self._index_type == "inner_product":
            faiss_index = faiss.IndexFlatIP(self._embedding_dimension)
        else:
            faiss_index = faiss.IndexFlatL2(self._embedding_dimension)

        self._vectorstore = FAISS(
            embedding_function=embedding_func,
            index=faiss_index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={}
        )
        self._doc_store = {}

        self._logger.info("FAISS index cleared")
        return True

    async def save_local(self, folder_path: Optional[str] = None) -> bool:
        """Save FAISS index to disk.

        Args:
            folder_path: Directory to save index (uses initialize path if None)

        Returns:
            True if successful
        """
        if not self._vectorstore:
            raise RuntimeError("Vector store not initialized.")

        save_path = folder_path or self._persist_directory
        if not save_path:
            raise ValueError(
                "No save path provided. "
                "Either provide folder_path or initialize with persist_directory."
            )

        index_path = Path(save_path) / self._collection_name

        # Create directory if needed
        index_path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        self._vectorstore.save_local(folder_path=str(index_path))

        self._logger.info(f"FAISS index saved to: {index_path}")
        return True

    async def delete_collection(self) -> bool:
        """Delete/reset the entire collection.

        Returns:
            True if successful
        """
        if not self._vectorstore:
            raise RuntimeError("Vector store not initialized.")

        # Clear all data
        await self.clear()

        # Delete persisted files if any
        if self._persist_directory and self._collection_name:
            import shutil
            index_path = Path(self._persist_directory) / self._collection_name
            if index_path.exists():
                shutil.rmtree(index_path)
                self._logger.info(f"Deleted persisted index: {index_path}")

        self._logger.info("FAISS collection deleted/reset")
        return True
