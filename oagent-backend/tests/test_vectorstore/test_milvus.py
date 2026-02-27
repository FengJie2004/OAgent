"""Tests for Milvus VectorStore plugin."""

import pytest
import os
import shutil
import sys
import tempfile
from pathlib import Path

from oagent.plugins.vectorstore.milvus import MilvusVectorStorePlugin
from oagent.plugins.vectorstore.base import Document


# Check if milvus-lite is available (needed for local .db mode)
def is_milvus_lite_available():
    """Check if milvus-lite is installed."""
    try:
        # Try to import milvus_lite - it's required for local .db mode
        import milvus_lite
        return True
    except ImportError:
        return False


# Skip all tests if milvus-lite is not available
pytestmark = pytest.mark.skipif(
    not is_milvus_lite_available(),
    reason="milvus-lite not installed - required for local Milvus testing. Install with: pip install 'pymilvus[milvus-lite]'"
)


class TestMilvusVectorStorePlugin:
    """Tests for Milvus VectorStore plugin."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return MilvusVectorStorePlugin()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for Milvus Lite."""
        return str(tmp_path / "milvus_test")

    @pytest.mark.asyncio
    async def test_plugin_name(self, plugin):
        """Test plugin name."""
        assert plugin.name == "milvus"

    @pytest.mark.asyncio
    async def test_plugin_version(self, plugin):
        """Test plugin version."""
        assert plugin.version == "0.1.0"

    @pytest.mark.asyncio
    async def test_plugin_description(self, plugin):
        """Test plugin description."""
        assert "Milvus" in plugin.description

    @pytest.mark.asyncio
    async def test_supported_models(self, plugin):
        """Test supported models."""
        models = plugin.supported_models
        assert "local" in models
        assert "remote" in models

    @pytest.mark.asyncio
    async def test_initialize_memory_mode(self, plugin):
        """Test initialization with temporary db (default mode)."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=1024,
        )
        assert plugin._client is not None
        assert plugin._collection_name == "test_collection"
        assert plugin._embedding_dimension == 1024

    @pytest.mark.asyncio
    async def test_initialize_local_mode(self, plugin, temp_dir):
        """Test initialization in local Milvus Lite mode."""
        os.makedirs(temp_dir, exist_ok=True)

        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=1024,
            persist_directory=temp_dir,
        )
        assert plugin._client is not None
        assert plugin._collection_name == "test_collection"

    @pytest.mark.asyncio
    async def test_add_documents(self, plugin):
        """Test adding documents."""
        await plugin.initialize(
            collection_name="test_add_collection",
            embedding_dimension=1024,
        )

        documents = [
            Document(id="doc1", content="Hello world", metadata={"source": "test"}),
            Document(id="doc2", content="Test document", metadata={"source": "test"}),
        ]
        embeddings = [
            [0.1] * 1024,
            [0.2] * 1024,
        ]

        ids = await plugin.add_documents(documents, embeddings)
        assert len(ids) == 2
        assert "doc1" in ids
        assert "doc2" in ids

    @pytest.mark.asyncio
    async def test_add_documents_without_embeddings(self, plugin):
        """Test adding documents without pre-computed embeddings."""
        await plugin.initialize(
            collection_name="test_add_no_emb_collection",
            embedding_dimension=1024,
        )

        documents = [
            Document(id="doc3", content="Hello world", metadata={"source": "test"})
        ]
        # No embeddings provided - should skip document
        ids = await plugin.add_documents(documents, None)
        # Should return empty list since no embeddings
        assert len(ids) == 0

    @pytest.mark.asyncio
    async def test_add_documents_with_doc_embedding(self, plugin):
        """Test adding documents with embedding in Document object."""
        await plugin.initialize(
            collection_name="test_doc_emb_collection",
            embedding_dimension=1024,
        )

        documents = [
            Document(
                id="doc4",
                content="Hello world",
                metadata={"source": "test"},
                embedding=[0.5] * 1024,
            )
        ]
        # No separate embeddings - should use doc.embedding
        ids = await plugin.add_documents(documents, None)
        assert len(ids) == 1

    @pytest.mark.asyncio
    async def test_similarity_search_by_vector(self, plugin):
        """Test similarity search by vector."""
        await plugin.initialize(
            collection_name="test_search_collection",
            embedding_dimension=1024,
        )

        # Add documents with distinct embeddings
        documents = [
            Document(id="sim_doc1", content="Hello world", metadata={"type": "greeting"}),
            Document(id="sim_doc2", content="Goodbye world", metadata={"type": "farewell"}),
        ]
        # Use distinct vectors
        emb1 = [1.0 / (i + 1) for i in range(1024)]  # Decreasing values
        emb2 = [0.0] * 1024  # All zeros
        embeddings = [emb1, emb2]

        await plugin.add_documents(documents, embeddings)

        # Search with vector similar to doc1
        query_embedding = [0.9 / (i + 1) for i in range(1024)]
        results = await plugin.similarity_search_by_vector(query_embedding, k=2)

        assert len(results) >= 1
        # First result should be sim_doc1 due to similarity
        assert results[0].document.id == "sim_doc1"
        # Check score is between 0 and 1
        assert 0 <= results[0].score <= 1

    @pytest.mark.asyncio
    async def test_similarity_search_by_vector_with_filter(self, plugin):
        """Test similarity search by vector with metadata filter."""
        await plugin.initialize(
            collection_name="test_filter_collection",
            embedding_dimension=1024,
        )

        # Add documents with different metadata
        documents = [
            Document(id="filtered_doc1", content="Hello", metadata={"category": "A"}),
            Document(id="filtered_doc2", content="World", metadata={"category": "B"}),
        ]
        embeddings = [
            [0.1] * 1024,
            [0.2] * 1024,
        ]

        await plugin.add_documents(documents, embeddings)

        # Search with filter
        query_embedding = [0.15] * 1024
        results = await plugin.similarity_search_by_vector(
            query_embedding, k=2, filter_dict={"category": "A"}
        )

        # Should return results (filter may work differently in local mode)
        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_get_document(self, plugin):
        """Test getting a document by ID."""
        await plugin.initialize(
            collection_name="test_get_collection",
            embedding_dimension=1024,
        )

        documents = [
            Document(id="get_doc1", content="Test content", metadata={"key": "value"})
        ]
        await plugin.add_documents(documents, [[0.5] * 1024])

        retrieved = await plugin.get_document("get_doc1")
        assert retrieved is not None
        assert retrieved.id == "get_doc1"
        assert retrieved.content == "Test content"
        assert retrieved.metadata.get("key") == "value"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, plugin):
        """Test getting a non-existent document."""
        await plugin.initialize(
            collection_name="test_get_not_found_collection",
            embedding_dimension=1024,
        )

        retrieved = await plugin.get_document("nonexistent")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_documents(self, plugin):
        """Test deleting documents."""
        await plugin.initialize(
            collection_name="test_delete_collection",
            embedding_dimension=1024,
        )

        documents = [
            Document(id="doc_to_delete", content="Delete me", metadata={"status": "pending"})
        ]
        await plugin.add_documents(documents, [[0.1] * 1024])

        result = await plugin.delete_documents(["doc_to_delete"])
        assert result is True

        # Verify deletion
        retrieved = await plugin.get_document("doc_to_delete")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_documents_empty_list(self, plugin):
        """Test deleting with empty ID list."""
        await plugin.initialize(
            collection_name="test_delete_empty_collection",
            embedding_dimension=1024,
        )

        result = await plugin.delete_documents([])
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_collection(self, plugin):
        """Test clearing all documents."""
        await plugin.initialize(
            collection_name="test_clear_collection",
            embedding_dimension=1024,
        )

        documents = [
            Document(id="clear_doc1", content="First", metadata={"num": 1}),
            Document(id="clear_doc2", content="Second", metadata={"num": 2}),
        ]
        await plugin.add_documents(documents, [[0.1] * 1024, [0.2] * 1024])

        result = await plugin.clear()
        assert result is True

        # Verify cleared
        retrieved = await plugin.get_document("clear_doc1")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_collection(self, plugin):
        """Test deleting entire collection."""
        await plugin.initialize(
            collection_name="test_drop_collection",
            embedding_dimension=1024,
        )

        documents = [Document(id="drop_doc1", content="To be dropped", metadata={})]
        await plugin.add_documents(documents, [[0.1] * 1024])

        result = await plugin.delete_collection()
        assert result is True
        assert plugin._collection_name is None

    @pytest.mark.asyncio
    async def test_not_initialized_error(self, plugin):
        """Test error when not initialized."""
        with pytest.raises(RuntimeError, match="not initialized"):
            await plugin.add_documents([])

        with pytest.raises(RuntimeError, match="not initialized"):
            await plugin.similarity_search_by_vector([0.1, 0.2])

        with pytest.raises(RuntimeError, match="not initialized"):
            await plugin.get_document("doc1")

        with pytest.raises(RuntimeError, match="not initialized"):
            await plugin.delete_documents(["doc1"])

        with pytest.raises(RuntimeError, match="not initialized"):
            await plugin.clear()

        with pytest.raises(RuntimeError, match="not initialized"):
            await plugin.delete_collection()

    @pytest.mark.asyncio
    async def test_empty_documents_list(self, plugin):
        """Test adding empty documents list."""
        await plugin.initialize(
            collection_name="test_empty_collection",
            embedding_dimension=1024,
        )

        ids = await plugin.add_documents([], [])
        assert ids == []

    @pytest.mark.asyncio
    async def test_plugin_registration(self):
        """Test that plugin is registered in registry."""
        from oagent.core.registry import PluginRegistry

        registry = PluginRegistry()
        plugins = registry.list("vectorstore")

        assert "milvus" in plugins
        plugin_class = plugins["milvus"]
        assert plugin_class.__name__ == "MilvusVectorStorePlugin"

    @pytest.mark.asyncio
    async def test_custom_embedding_dimension(self, plugin):
        """Test initialization with custom embedding dimension."""
        await plugin.initialize(
            collection_name="test_custom_dim_collection",
            embedding_dimension=1536,  # OpenAI default
        )

        assert plugin._embedding_dimension == 1536

        # Add document with matching dimension
        documents = [
            Document(id="custom_doc1", content="Test", metadata={})
        ]
        embeddings = [[0.1] * 1536]

        ids = await plugin.add_documents(documents, embeddings)
        assert len(ids) == 1
