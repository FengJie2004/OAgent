"""Milvus VectorStore plugin implementation."""

import os
import tempfile
from typing import List, Optional, Dict, Any
from loguru import logger

from oagent.core.registry import register_plugin
from oagent.plugins.vectorstore.base import VectorStorePluginBase, Document, SearchResult


@register_plugin("vectorstore", "milvus")
class MilvusVectorStorePlugin(VectorStorePluginBase):
    """Milvus VectorStore plugin.

    Uses pymilvus for integration.
    Supports both local (Milvus Lite with .db file) and remote Milvus connections.
    """

    @property
    def name(self) -> str:
        return "milvus"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Milvus vector store - supports local (Milvus Lite) and remote connections"

    @property
    def supported_models(self) -> List[str]:
        """List of supported Milvus connection types."""
        return ["local", "remote"]

    def __init__(self):
        self._client = None
        self._collection = None
        self._collection_name: Optional[str] = None
        self._embedding_dimension: int = 1024
        self._logger = logger
        self._temp_db_path: Optional[str] = None
        self._index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 8, "efConstruction": 200},
        }

    async def initialize(
        self,
        collection_name: str,
        embedding_dimension: int = 1024,
        persist_directory: Optional[str] = None,
        uri: Optional[str] = None,
        token: Optional[str] = None,
        db_name: str = "default",
    ) -> None:
        """Initialize Milvus vector store.

        Args:
            collection_name: Collection name
            embedding_dimension: Dimension of embeddings (default 1024 for text-embedding-v4)
            persist_directory: Directory for local Milvus Lite (.db file)
            uri: Remote Milvus URI (e.g., "http://localhost:19530" or Milvus Cloud URL)
            token: Authentication token for remote Milvus (optional)
            db_name: Database name (default: "default")

        Note:
            - If persist_directory is provided, uses Milvus Lite with local .db file
            - If uri is provided, connects to remote Milvus instance
            - If neither is provided, uses a temporary .db file for testing

        Raises:
            ImportError: If pymilvus is not installed
            RuntimeError: If milvus-lite is not installed for local mode
        """
        from pymilvus import MilvusClient, DataType

        self._collection_name = collection_name
        self._embedding_dimension = embedding_dimension

        # Determine connection mode
        if persist_directory:
            # Local Milvus Lite mode - use .db file
            try:
                db_path = f"{persist_directory}/milvus.db"
                self._client = MilvusClient(uri=db_path)
                self._logger.info(f"Milvus Lite initialized with local db: {db_path}")
            except Exception as e:
                if "milvus-lite" in str(e).lower():
                    raise RuntimeError(
                        "milvus-lite is required for local database connections. "
                        "Please install it with: pip install pymilvus[milvus_lite]"
                    ) from e
                raise
        elif uri:
            # Remote Milvus connection
            connect_kwargs = {"uri": uri}
            if token:
                connect_kwargs["token"] = token
            self._client = MilvusClient(**connect_kwargs)
            self._logger.info(f"Milvus initialized with remote URI: {uri}")
        else:
            # Fallback: use a temporary .db file for testing/demo
            # This allows testing without a running Milvus server
            self._temp_db_path = os.path.join(tempfile.gettempdir(), f"milvus_temp_{collection_name}.db")
            try:
                self._client = MilvusClient(uri=self._temp_db_path)
                self._logger.info(f"Milvus initialized with temporary db: {self._temp_db_path}")
            except Exception as e:
                if "milvus-lite" in str(e).lower():
                    raise RuntimeError(
                        "milvus-lite is required for local database connections. "
                        "Please install it with: pip install pymilvus[milvus_lite]"
                    ) from e
                raise

        # Get or create collection
        try:
            if self._client.has_collection(collection_name):
                # Collection exists, load it
                self._collection = self._client.describe_collection(collection_name)
                self._logger.info(f"Using existing collection: {collection_name}")
            else:
                # Create new collection with schema
                from pymilvus import FieldSchema, CollectionSchema

                # Define schema
                fields = [
                    FieldSchema(
                        name="id",
                        dtype=DataType.VARCHAR,
                        is_primary=True,
                        max_length=256,
                    ),
                    FieldSchema(
                        name="content",
                        dtype=DataType.VARCHAR,
                        max_length=65535,
                    ),
                    FieldSchema(
                        name="metadata",
                        dtype=DataType.JSON,
                    ),
                    FieldSchema(
                        name="embedding",
                        dtype=DataType.FLOAT_VECTOR,
                        dim=embedding_dimension,
                    ),
                ]

                schema = CollectionSchema(fields, description=f"Collection for {collection_name}")

                # Create collection
                self._client.create_collection(
                    collection_name=collection_name,
                    schema=schema,
                    consistency_level="Strong",
                )

                # Create index for vector search
                index_params = {
                    "field_name": "embedding",
                    "index_type": self._index_params["index_type"],
                    "index_params": self._index_params["params"],
                    "metric_type": self._index_params["metric_type"],
                }
                self._client.create_index(
                    collection_name=collection_name,
                    index_params=index_params,
                )

                self._logger.info(f"Created collection: {collection_name}")
                self._logger.info(f"Created index with metric_type: {self._index_params['metric_type']}")

        except Exception as e:
            self._logger.error(f"Error initializing Milvus collection: {e}")
            raise

        self._logger.info(f"Collection ready: {collection_name}")

    async def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[str]:
        """Add documents to Milvus.

        Args:
            documents: List of documents to add
            embeddings: Optional pre-computed embeddings

        Returns:
            List of document IDs

        Raises:
            RuntimeError: If not initialized
        """
        if not self._client:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")

        if not documents:
            return []

        ids = []
        entities = []

        for i, doc in enumerate(documents):
            # Generate ID if not provided
            doc_id = doc.id or f"doc_{len(ids) + 1}"
            ids.append(doc_id)

            # Get embedding for this document
            if embeddings and i < len(embeddings):
                embedding = embeddings[i]
            elif doc.embedding:
                embedding = doc.embedding
            else:
                self._logger.warning(f"Document {doc_id} has no embedding, skipping")
                continue

            # Prepare entity
            entity = {
                "id": doc_id,
                "content": doc.content,
                "metadata": doc.metadata or {},
                "embedding": embedding,
            }
            entities.append(entity)

        if not entities:
            self._logger.warning("No entities to add - all documents missing embeddings")
            return []

        # Insert into Milvus
        result = self._client.insert(
            collection_name=self._collection_name,
            data=entities,
        )

        self._logger.info(f"Added {len(entities)} documents to Milvus")
        return ids

    async def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents by query text.

        Args:
            query: Query text
            k: Number of results
            filter_dict: Optional metadata filters

        Returns:
            List of search results

        Note:
            This method requires an embedding function to be configured.
            For now, returns empty results - use similarity_search_by_vector
            with pre-computed embeddings instead.
        """
        if not self._client:
            raise RuntimeError("Vector store not initialized.")

        # Milvus requires embeddings for search
        # The caller should provide embeddings or configure an embedding function
        self._logger.warning(
            "similarity_search requires embedding function configured. "
            "Use similarity_search_by_vector with pre-computed embeddings."
        )
        return []

    async def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents by embedding vector.

        Args:
            embedding: Embedding vector
            k: Number of results
            filter_dict: Optional metadata filters (filter expression)

        Returns:
            List of search results

        Raises:
            RuntimeError: If not initialized
        """
        if not self._client:
            raise RuntimeError("Vector store not initialized.")

        # Build filter expression
        expr = None
        if filter_dict:
            # Convert dict to Milvus filter expression
            # e.g., {"source": "test"} -> 'source == "test"'
            filter_parts = []
            for key, value in filter_dict.items():
                if isinstance(value, str):
                    filter_parts.append(f'metadata["{key}"] == "{value}"')
                elif isinstance(value, bool):
                    filter_parts.append(f'metadata["{key}"] == {str(value).lower()}')
                elif isinstance(value, (int, float)):
                    filter_parts.append(f'metadata["{key}"] == {value}')
                else:
                    # For complex types, try string representation
                    filter_parts.append(f'metadata["{key}"] == "{value}"')
            expr = " and ".join(filter_parts)

        # Search
        results = self._client.search(
            collection_name=self._collection_name,
            data=[embedding],
            limit=k,
            filter=expr,
            output_fields=["content", "metadata", "embedding"],
        )

        search_results = []

        if results and len(results) > 0:
            for hit in results[0]:
                doc_id = hit["entity"].get("id", "")
                content = hit["entity"].get("content", "")
                metadata = hit["entity"].get("metadata", {})
                distance = hit.get("distance", 0.0)

                # For COSINE metric, distance is angular distance (1 - cosine_similarity)
                # Convert to similarity score
                score = 1.0 - distance

                search_results.append(
                    SearchResult(
                        document=Document(
                            id=doc_id,
                            content=content,
                            metadata=metadata,
                        ),
                        score=score,
                        distance=distance,
                    )
                )

        self._logger.debug(f"Found {len(search_results)} results")
        return search_results

    async def delete_documents(
        self,
        ids: List[str],
    ) -> bool:
        """Delete documents by IDs.

        Args:
            ids: List of document IDs

        Returns:
            True if successful

        Raises:
            RuntimeError: If not initialized
        """
        if not self._client:
            raise RuntimeError("Vector store not initialized.")

        if not ids:
            return True

        # Build delete expression
        id_list = ", ".join([f'"{id}"' for id in ids])
        expr = f'id in [{id_list}]'

        self._client.delete(
            collection_name=self._collection_name,
            filter=expr,
        )

        self._logger.info(f"Deleted {len(ids)} documents")
        return True

    async def get_document(
        self,
        id: str,
    ) -> Optional[Document]:
        """Get document by ID.

        Args:
            id: Document ID

        Returns:
            Document or None

        Raises:
            RuntimeError: If not initialized
        """
        if not self._client:
            raise RuntimeError("Vector store not initialized.")

        # Get by ID
        expr = f'id == "{id}"'
        results = self._client.query(
            collection_name=self._collection_name,
            filter=expr,
            output_fields=["content", "metadata", "embedding"],
        )

        if results and len(results) > 0:
            entity = results[0]
            return Document(
                id=id,
                content=entity.get("content", ""),
                metadata=entity.get("metadata", {}),
                embedding=entity.get("embedding"),
            )

        return None

    async def clear(self) -> bool:
        """Clear all documents from collection.

        Returns:
            True if successful

        Raises:
            RuntimeError: If not initialized
        """
        if not self._client:
            raise RuntimeError("Vector store not initialized.")

        # Delete all documents by using empty filter
        self._client.delete(
            collection_name=self._collection_name,
            filter='id != ""',  # Delete all documents
        )

        self._logger.info("Cleared all documents from collection")
        return True

    async def delete_collection(self) -> bool:
        """Delete the collection.

        Returns:
            True if successful

        Raises:
            RuntimeError: If not initialized
        """
        if not self._client:
            raise RuntimeError("Vector store not initialized.")

        if self._collection_name:
            self._client.drop_collection(self._collection_name)
            self._logger.info(f"Deleted collection: {self._collection_name}")
            self._collection = None
            self._collection_name = None

        return True

    async def close(self) -> None:
        """Close the Milvus client connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._logger.info("Milvus client connection closed")
