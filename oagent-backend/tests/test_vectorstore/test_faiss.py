"""FAISS VectorStore plugin tests."""

import pytest
import os
import shutil
from pathlib import Path

from oagent.plugins.vectorstore.faiss import FAISSVectorStorePlugin
from oagent.plugins.vectorstore.base import Document


class TestFAISSVectorStorePlugin:
    """Tests for FAISS VectorStore plugin."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return FAISSVectorStorePlugin()

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for FAISS persistence."""
        return str(tmp_path / "faiss_test")

    @pytest.mark.asyncio
    async def test_plugin_name(self, plugin):
        """Test plugin name."""
        assert plugin.name == "faiss"

    @pytest.mark.asyncio
    async def test_plugin_version(self, plugin):
        """Test plugin version."""
        assert plugin.version == "0.1.0"

    @pytest.mark.asyncio
    async def test_plugin_description(self, plugin):
        """Test plugin description."""
        assert "FAISS" in plugin.description
        assert "L2" in plugin.description or "Inner Product" in plugin.description

    @pytest.mark.asyncio
    async def test_supported_models(self, plugin):
        """Test supported index types."""
        models = plugin.supported_models
        assert "l2" in models
        assert "inner_product" in models
        assert "flat" in models

    @pytest.mark.asyncio
    async def test_initialize_memory_mode(self, plugin):
        """Test initialization in memory mode."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=768
        )
        assert plugin._vectorstore is not None
        assert plugin._embedding_dimension == 768

    @pytest.mark.asyncio
    async def test_initialize_l2_index(self, plugin):
        """Test initialization with L2 index type."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=512,
            index_type="l2"
        )
        assert plugin._index_type == "l2"
        assert plugin._vectorstore is not None

    @pytest.mark.asyncio
    async def test_initialize_inner_product_index(self, plugin):
        """Test initialization with Inner Product index type."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=512,
            index_type="inner_product"
        )
        assert plugin._index_type == "inner_product"
        assert plugin._vectorstore is not None

    @pytest.mark.asyncio
    async def test_initialize_invalid_index_type(self, plugin):
        """Test initialization with invalid index type."""
        with pytest.raises(ValueError, match="Unsupported index type"):
            await plugin.initialize(
                collection_name="test_collection",
                embedding_dimension=512,
                index_type="invalid_type"
            )

    @pytest.mark.asyncio
    async def test_initialize_persistent_mode(self, plugin, temp_dir):
        """Test initialization in persistent mode."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=512,
            persist_directory=temp_dir
        )
        assert plugin._vectorstore is not None
        assert plugin._persist_directory == temp_dir

    @pytest.mark.asyncio
    async def test_add_documents(self, plugin):
        """Test adding documents with embeddings."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=768
        )

        documents = [
            Document(id="doc1", content="Hello world", metadata={"source": "test"}),
            Document(id="doc2", content="Test document", metadata={"source": "test"})
        ]
        embeddings = [
            [0.1] * 768,
            [0.2] * 768
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
            embedding_dimension=768
        )

        documents = [
            Document(id="doc3", content="Hello world", metadata={"source": "test"})
        ]

        # Should add with zero embeddings (with warning)
        ids = await plugin.add_documents(documents)
        assert len(ids) == 1

    @pytest.mark.asyncio
    async def test_add_documents_dimension_mismatch(self, plugin):
        """Test adding documents with wrong embedding dimension."""
        await plugin.initialize(
            collection_name="test_collection",
            embedding_dimension=768
        )

        documents = [
            Document(id="doc1", content="Hello world", metadata={})
        ]
        # Wrong dimension
        embeddings = [
            [0.1] * 512  # Should be 768
        ]

        with pytest.raises(ValueError, match="dimension mismatch"):
            await plugin.add_documents(documents, embeddings)

    @pytest.mark.asyncio
    async def test_similarity_search_by_vector_l2(self, plugin):
        """Test similarity search by vector with L2 index."""
        await plugin.initialize(
            collection_name="test_search_l2",
            embedding_dimension=4,
            index_type="l2"
        )

        # Add documents with distinct vectors
        documents = [
            Document(id="vec1", content="Vector one", metadata={"type": "first"}),
            Document(id="vec2", content="Vector two", metadata={"type": "second"})
        ]
        # Use simple 4D vectors for easy testing
        emb1 = [1.0, 0.0, 0.0, 0.0]
        emb2 = [0.0, 1.0, 0.0, 0.0]
        embeddings = [emb1, emb2]

        await plugin.add_documents(documents, embeddings)

        # Search with vector similar to doc1
        query_embedding = [0.9, 0.1, 0.0, 0.0]  # Closer to emb1
        results = await plugin.similarity_search_by_vector(query_embedding, k=2)

        assert len(results) >= 1
        # First result should be vec1 due to similarity
        assert results[0].document.id == "vec1"

    @pytest.mark.asyncio
    async def test_similarity_search_by_vector_inner_product(self, plugin):
        """Test similarity search by vector with Inner Product index."""
        await plugin.initialize(
            collection_name="test_search_ip",
            embedding_dimension=4,
            index_type="inner_product"
        )

        documents = [
            Document(id="ip_vec1", content="Vector one", metadata={"type": "first"}),
            Document(id="ip_vec2", content="Vector two", metadata={"type": "second"})
        ]
        emb1 = [1.0, 0.0, 0.0, 0.0]
        emb2 = [0.0, 1.0, 0.0, 0.0]
        embeddings = [emb1, emb2]

        await plugin.add_documents(documents, embeddings)

        # Search with vector similar to doc1
        query_embedding = [0.9, 0.1, 0.0, 0.0]
        results = await plugin.similarity_search_by_vector(query_embedding, k=2)

        assert len(results) >= 1
        assert results[0].document.id == "ip_vec1"

    @pytest.mark.asyncio
    async def test_similarity_search_empty_index(self, plugin):
        """Test similarity search on empty index."""
        await plugin.initialize(
            collection_name="test_empty",
            embedding_dimension=768
        )

        results = await plugin.similarity_search_by_vector(
            [0.1] * 768,
            k=5
        )
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_document(self, plugin):
        """Test getting a document by ID."""
        await plugin.initialize(
            collection_name="test_get",
            embedding_dimension=768
        )

        documents = [
            Document(id="get_doc1", content="Test content", metadata={"key": "value"})
        ]
        await plugin.add_documents(documents, [[0.5] * 768])

        retrieved = await plugin.get_document("get_doc1")
        assert retrieved is not None
        assert retrieved.id == "get_doc1"
        assert retrieved.content == "Test content"
        assert retrieved.metadata == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, plugin):
        """Test getting a non-existent document."""
        await plugin.initialize(
            collection_name="test_get",
            embedding_dimension=768
        )

        retrieved = await plugin.get_document("nonexistent")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_documents(self, plugin):
        """Test deleting documents."""
        await plugin.initialize(
            collection_name="test_delete",
            embedding_dimension=768
        )

        documents = [
            Document(id="to_delete", content="Delete me", metadata={})
        ]
        await plugin.add_documents(documents, [[0.1] * 768])

        result = await plugin.delete_documents(["to_delete"])
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_collection(self, plugin):
        """Test clearing all documents."""
        await plugin.initialize(
            collection_name="test_clear",
            embedding_dimension=768
        )

        documents = [
            Document(id="clear1", content="First", metadata={}),
            Document(id="clear2", content="Second", metadata={})
        ]
        await plugin.add_documents(documents, [[0.1] * 768, [0.2] * 768])

        result = await plugin.clear()
        assert result is True

        # Verify cleared
        results = await plugin.similarity_search_by_vector([0.1] * 768, k=5)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_save_local(self, plugin, temp_dir):
        """Test saving FAISS index to disk."""
        await plugin.initialize(
            collection_name="test_save",
            embedding_dimension=768,
            persist_directory=temp_dir
        )

        documents = [
            Document(id="save_doc", content="To save", metadata={})
        ]
        await plugin.add_documents(documents, [[0.3] * 768])

        # Save to disk
        result = await plugin.save_local()
        assert result is True

        # Verify files exist
        index_path = Path(temp_dir) / "test_save" / "index.faiss"
        assert index_path.exists()

    @pytest.mark.asyncio
    async def test_save_local_custom_path(self, plugin, temp_dir):
        """Test saving FAISS index to custom path."""
        await plugin.initialize(
            collection_name="test_save",
            embedding_dimension=768
        )

        documents = [
            Document(id="save_doc", content="To save", metadata={})
        ]
        await plugin.add_documents(documents, [[0.3] * 768])

        save_path = Path(temp_dir) / "custom_save"
        result = await plugin.save_local(folder_path=str(save_path))
        assert result is True

        # Verify files exist at custom location (uses collection_name as subfolder)
        index_path = save_path / "test_save" / "index.faiss"
        assert index_path.exists()

    @pytest.mark.asyncio
    async def test_save_local_no_path_error(self, plugin):
        """Test save_local error when no path provided."""
        await plugin.initialize(
            collection_name="test_save",
            embedding_dimension=768
        )

        with pytest.raises(ValueError, match="No save path provided"):
            await plugin.save_local()

    @pytest.mark.asyncio
    async def test_delete_collection(self, plugin, temp_dir):
        """Test deleting entire collection."""
        await plugin.initialize(
            collection_name="test_delete_coll",
            embedding_dimension=768,
            persist_directory=temp_dir
        )

        documents = [
            Document(id="del_doc", content="To delete", metadata={})
        ]
        await plugin.add_documents(documents, [[0.3] * 768])

        # Save first
        await plugin.save_local()

        # Delete collection
        result = await plugin.delete_collection()
        assert result is True

        # Verify index is cleared
        results = await plugin.similarity_search_by_vector([0.1] * 768, k=5)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_not_initialized_error(self, plugin):
        """Test errors when not initialized."""
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
            await plugin.save_local()

        with pytest.raises(RuntimeError, match="not initialized"):
            await plugin.delete_collection()

    @pytest.mark.asyncio
    async def test_similarity_search_requires_vector_method(self, plugin):
        """Test that similarity_search warns about using vector method."""
        await plugin.initialize(
            collection_name="test_search",
            embedding_dimension=768
        )

        # Should return empty list with warning
        results = await plugin.similarity_search("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_multiple_documents_search(self, plugin):
        """Test search with multiple documents."""
        await plugin.initialize(
            collection_name="test_multi",
            embedding_dimension=4,
            index_type="l2"
        )

        # Add multiple documents with varied vectors
        documents = [
            Document(id=f"doc_{i}", content=f"Content {i}", metadata={"idx": i})
            for i in range(10)
        ]
        embeddings = [
            [float(i * 0.1), 0.0, 0.0, 0.0] for i in range(10)
        ]

        await plugin.add_documents(documents, embeddings)

        # Search
        query = [0.5, 0.0, 0.0, 0.0]  # Closest to doc_5
        results = await plugin.similarity_search_by_vector(query, k=3)

        assert len(results) == 3
        # Results should be ordered by similarity

    @pytest.mark.asyncio
    async def test_persistence_load(self, tmp_path):
        """Test that persisted index can be reloaded."""
        persist_dir = str(tmp_path / "persistence_test")

        # Create and populate first plugin
        plugin1 = FAISSVectorStorePlugin()
        await plugin1.initialize(
            collection_name="persist_test",
            embedding_dimension=4,
            persist_directory=persist_dir,
            index_type="l2"
        )

        documents = [
            Document(id="persist_doc", content="Persistent content", metadata={})
        ]
        await plugin1.add_documents(documents, [[1.0, 0.0, 0.0, 0.0]])
        await plugin1.save_local()

        # Create new plugin and load
        plugin2 = FAISSVectorStorePlugin()
        await plugin2.initialize(
            collection_name="persist_test",
            embedding_dimension=4,
            persist_directory=persist_dir,
            index_type="l2"
        )

        # Verify document is loaded
        retrieved = await plugin2.get_document("persist_doc")
        assert retrieved is not None
        assert retrieved.content == "Persistent content"
