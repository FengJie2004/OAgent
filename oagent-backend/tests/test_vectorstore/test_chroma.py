"""Tests for ChromaDB VectorStore plugin."""

import pytest
import os
import shutil
from pathlib import Path

from oagent.plugins.vectorstore.chroma import ChromaVectorStorePlugin
from oagent.plugins.vectorstore.base import Document


class TestChromaVectorStorePlugin:
    """Tests for ChromaDB VectorStore plugin."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return ChromaVectorStorePlugin()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for ChromaDB."""
        return str(tmp_path / "chroma_test")

    @pytest.mark.asyncio
    async def test_plugin_name(self, plugin):
        """Test plugin name."""
        assert plugin.name == "chroma"

    @pytest.mark.asyncio
    async def test_plugin_version(self, plugin):
        """Test plugin version."""
        assert plugin.version == "0.1.0"

    @pytest.mark.asyncio
    async def test_plugin_description(self, plugin):
        """Test plugin description."""
        assert "ChromaDB" in plugin.description

    @pytest.mark.asyncio
    async def test_supported_models(self, plugin):
        """Test supported models."""
        models = plugin.supported_models
        assert "persistent" in models
        assert "memory" in models

    @pytest.mark.asyncio
    async def test_initialize_memory_mode(self, plugin):
        """Test initialization in memory mode."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=1024,
            persist_directory=None
        )
        assert plugin._client is not None
        assert plugin._collection is not None

    @pytest.mark.asyncio
    async def test_initialize_persistent_mode(self, plugin, temp_dir):
        """Test initialization in persistent mode."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=1024,
            persist_directory=temp_dir
        )
        assert plugin._client is not None
        assert plugin._persist_directory == temp_dir

    @pytest.mark.asyncio
    async def test_add_documents(self, plugin):
        """Test adding documents."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=1024
        )

        documents = [
            Document(id="doc1", content="Hello world", metadata={"source": "test"}),
            Document(id="doc2", content="Test document", metadata={"source": "test"})
        ]
        embeddings = [
            [0.1] * 1024,
            [0.2] * 1024
        ]

        ids = await plugin.add_documents(documents, embeddings)
        assert len(ids) == 2
        assert "doc1" in ids
        assert "doc2" in ids

    @pytest.mark.asyncio
    async def test_add_documents_without_embeddings(self, plugin):
        """Test adding documents without pre-computed embeddings."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=1024
        )

        documents = [
            Document(id="doc3", content="Hello world", metadata={"source": "test"})
        ]
        # ChromaDB requires embeddings, so we must provide them
        embeddings = [[0.5] * 1024]

        ids = await plugin.add_documents(documents, embeddings)
        assert len(ids) == 1

    @pytest.mark.asyncio
    async def test_similarity_search_by_vector(self, plugin):
        """Test similarity search by vector."""
        # Use unique collection name for test isolation
        await plugin.initialize(
            collection_name="test_similarity_search_collection",
            embedding_dimension=1024
        )

        # Add documents with embeddings - use distinct vectors
        documents = [
            Document(id="sim_doc1", content="Hello world", metadata={"type": "greeting"}),
            Document(id="sim_doc2", content="Goodbye world", metadata={"type": "farewell"})
        ]
        # Use normalized-like vectors for better similarity testing
        emb1 = [1.0 / (i + 1) for i in range(1024)]  # Decreasing values
        emb2 = [0.0] * 1024  # All zeros
        embeddings = [emb1, emb2]

        await plugin.add_documents(documents, embeddings)

        # Search with vector similar to doc1
        query_embedding = [0.9 / (i + 1) for i in range(1024)]  # Similar pattern to emb1
        results = await plugin.similarity_search_by_vector(query_embedding, k=2)

        assert len(results) >= 1
        # First result should be sim_doc1 due to similarity
        assert results[0].document.id == "sim_doc1"

    @pytest.mark.asyncio
    async def test_get_document(self, plugin):
        """Test getting a document by ID."""
        # Use unique collection name for test isolation
        await plugin.initialize(
            collection_name="test_get_document_collection",
            embedding_dimension=1024
        )

        documents = [
            Document(id="doc1", content="Test content", metadata={"key": "value"})
        ]
        await plugin.add_documents(documents, [[0.5] * 1024])

        retrieved = await plugin.get_document("doc1")
        assert retrieved is not None
        assert retrieved.id == "doc1"
        assert retrieved.content == "Test content"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, plugin):
        """Test getting a non-existent document."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=1024
        )

        retrieved = await plugin.get_document("nonexistent")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_documents(self, plugin):
        """Test deleting documents."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=1024
        )

        documents = [Document(id="doc_to_delete", content="Delete me", metadata={"status": "pending"})]
        await plugin.add_documents(documents, [[0.1] * 1024])

        result = await plugin.delete_documents(["doc_to_delete"])
        assert result is True

        # Verify deletion
        retrieved = await plugin.get_document("doc_to_delete")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_clear_collection(self, plugin):
        """Test clearing all documents."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=1024
        )

        documents = [
            Document(id="doc1", content="First", metadata={"num": 1}),
            Document(id="doc2", content="Second", metadata={"num": 2})
        ]
        await plugin.add_documents(documents, [[0.1] * 1024, [0.2] * 1024])

        result = await plugin.clear()
        assert result is True

        # Verify cleared
        retrieved = await plugin.get_document("doc1")
        assert retrieved is None

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
