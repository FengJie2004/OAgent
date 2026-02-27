"""VectorStore plugins initialization."""

from oagent.plugins.vectorstore.base import VectorStorePluginBase, Document, SearchResult
from oagent.plugins.vectorstore.chroma import ChromaVectorStorePlugin
from oagent.plugins.vectorstore.faiss import FAISSVectorStorePlugin
from oagent.plugins.vectorstore.milvus import MilvusVectorStorePlugin

__all__ = [
    "VectorStorePluginBase",
    "Document",
    "SearchResult",
    "ChromaVectorStorePlugin",
    "FAISSVectorStorePlugin",
    "MilvusVectorStorePlugin",
]
