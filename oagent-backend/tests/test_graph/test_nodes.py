"""Tests for LangGraph node implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from oagent.graph.state import AgentState
from oagent.graph.nodes import (
    llm_node,
    tool_node,
    rag_node,
    human_review_node,
    error_handler_node,
)


class TestLLMNode:
    """测试 LLM 节点。"""

    @pytest.mark.asyncio
    async def test_llm_node_basic(self):
        """测试 LLM 节点基本功能。"""
        # 创建模拟 LLM
        mock_llm = AsyncMock()
        mock_response = AIMessage(content="Hello, I am an AI assistant.")
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        # 创建节点函数
        node_func = await llm_node(mock_llm)

        # 创建状态
        state = AgentState(
            thread_id="test-1",
            messages=[HumanMessage(content="Hello")]
        )

        # 执行节点
        result = await node_func(state)

        # 验证结果
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "Hello, I am an AI assistant."
        assert result["iteration_count"] == 1

    @pytest.mark.asyncio
    async def test_llm_node_with_tool_calls(self):
        """测试带工具调用的 LLM 节点。"""
        # 创建模拟 LLM，返回带工具调用的响应
        mock_llm = AsyncMock()
        mock_response = AIMessage(
            content="Let me calculate that for you.",
            tool_calls=[
                {"id": "call_1", "name": "calculator", "args": {"expression": "2+2"}}
            ]
        )
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        node_func = await llm_node(mock_llm)

        state = AgentState(
            thread_id="test-2",
            messages=[HumanMessage(content="What is 2+2?")]
        )

        result = await node_func(state)

        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "calculator"
        assert result["tool_calls"][0]["args"] == {"expression": "2+2"}

    @pytest.mark.asyncio
    async def test_llm_node_with_system_prompt(self):
        """测试带系统提示词的 LLM 节点。"""
        mock_llm = AsyncMock()
        mock_response = AIMessage(content="Response with system prompt.")
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        node_func = await llm_node(mock_llm, system_prompt="You are a helpful assistant.")

        state = AgentState(
            thread_id="test-3",
            messages=[HumanMessage(content="Hello")]
        )

        result = await node_func(state)

        # 验证 LLM 被调用
        assert mock_llm.ainvoke.called
        # 验证迭代次数增加
        assert result["iteration_count"] == 1


class TestToolNode:
    """测试工具节点。"""

    @pytest.mark.asyncio
    async def test_tool_node_basic(self):
        """测试工具节点基本功能。"""
        # 创建模拟工具
        mock_tool = MagicMock()
        mock_tool.ainvoke = AsyncMock(return_value="4")
        mock_tool.name = "calculator"

        tools = {"calculator": mock_tool}
        node_func = await tool_node(tools)

        state = AgentState(
            thread_id="test-4",
            tool_calls=[
                {"id": "call_1", "name": "calculator", "args": {"expression": "2+2"}}
            ]
        )

        result = await node_func(state)

        # 验证工具被调用
        mock_tool.ainvoke.assert_called_once_with({"expression": "2+2"})
        # 验证结果
        assert len(result["tool_results"]) == 1
        assert result["tool_results"][0]["result"] == "4"
        assert result["tool_results"][0]["error"] is None

    @pytest.mark.asyncio
    async def test_tool_node_tool_not_found(self):
        """测试工具节点找不到工具的情况。"""
        tools = {"other_tool": MagicMock()}
        node_func = await tool_node(tools)

        state = AgentState(
            thread_id="test-5",
            tool_calls=[
                {"id": "call_1", "name": "nonexistent", "args": {}}
            ]
        )

        result = await node_func(state)

        assert len(result["tool_results"]) == 1
        assert "Tool not found" in result["tool_results"][0]["error"]

    @pytest.mark.asyncio
    async def test_tool_node_execution_error(self):
        """测试工具节点执行错误的情况。"""
        mock_tool = MagicMock()
        mock_tool.ainvoke = AsyncMock(side_effect=Exception("Tool execution failed"))
        mock_tool.name = "failing_tool"

        tools = {"failing_tool": mock_tool}
        node_func = await tool_node(tools)

        state = AgentState(
            thread_id="test-6",
            tool_calls=[
                {"id": "call_1", "name": "failing_tool", "args": {}}
            ]
        )

        result = await node_func(state)

        assert len(result["tool_results"]) == 1
        assert result["tool_results"][0]["error"] == "Tool execution failed"
        assert result["tool_results"][0]["result"] is None

    @pytest.mark.asyncio
    async def test_tool_node_without_tool_calls(self):
        """测试没有工具调用的情况。"""
        tools = {"calculator": MagicMock()}
        node_func = await tool_node(tools)

        state = AgentState(thread_id="test-7")

        result = await node_func(state)

        assert result["tool_results"] == []


class TestRAGNode:
    """测试 RAG 节点。"""

    @pytest.mark.asyncio
    async def test_rag_node_basic(self):
        """测试 RAG 节点基本功能。"""
        # 创建模拟向量存储和嵌入模型
        mock_vectorstore = MagicMock()
        mock_embedding = MagicMock()

        # 模拟嵌入
        mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 1024)

        # 模拟向量存储搜索
        mock_doc1 = MagicMock()
        mock_doc1.content = "Document 1 content"
        mock_doc1.metadata = {"source": "test1"}

        mock_doc2 = MagicMock()
        mock_doc2.content = "Document 2 content"
        mock_doc2.metadata = {"source": "test2"}

        mock_vectorstore.similarity_search_by_vector = AsyncMock(
            return_value=[mock_doc1, mock_doc2]
        )

        node_func = await rag_node(mock_vectorstore, mock_embedding, top_k=2)

        state = AgentState(
            thread_id="test-8",
            messages=[HumanMessage(content="What is the capital of France?")]
        )

        result = await node_func(state)

        # 验证嵌入模型被调用
        mock_embedding.embed_query.assert_called_once()
        # 验证向量存储搜索被调用
        mock_vectorstore.similarity_search_by_vector.assert_called_once()
        # 验证结果
        assert len(result["retrieved_docs"]) == 2
        assert result["rag_context"] is not None

    @pytest.mark.asyncio
    async def test_rag_node_no_human_message(self):
        """测试 RAG 节点没有人类消息的情况。"""
        mock_vectorstore = MagicMock()
        mock_embedding = MagicMock()

        node_func = await rag_node(mock_vectorstore, mock_embedding)

        state = AgentState(
            thread_id="test-9",
            messages=[AIMessage(content="AI message only")]
        )

        result = await node_func(state)

        assert result["retrieved_docs"] == []
        assert result["rag_context"] is None

    @pytest.mark.asyncio
    async def test_rag_node_error_handling(self):
        """测试 RAG 节点错误处理。"""
        mock_vectorstore = MagicMock()
        mock_embedding = MagicMock()

        mock_embedding.embed_query = AsyncMock(side_effect=Exception("Embedding failed"))

        node_func = await rag_node(mock_vectorstore, mock_embedding)

        state = AgentState(
            thread_id="test-10",
            messages=[HumanMessage(content="Test")]
        )

        result = await node_func(state)

        assert result["retrieved_docs"] == []
        assert result["rag_context"] is None
        assert result["error"] is not None


class TestHumanReviewNode:
    """测试人工审核节点。"""

    @pytest.mark.asyncio
    async def test_human_review_node(self):
        """测试人工审核节点基本功能。"""
        node_func = await human_review_node()

        state = AgentState(thread_id="test-11")

        result = await node_func(state)

        assert result["requires_human_review"] is True
        assert result["next_action"] == "wait"


class TestErrorHandlerNode:
    """测试错误处理节点。"""

    @pytest.mark.asyncio
    async def test_error_handler_node(self):
        """测试错误处理节点基本功能。"""
        node_func = await error_handler_node()

        state = AgentState(
            thread_id="test-12",
            error="Test error message"
        )

        result = await node_func(state)

        assert result["next_action"] == "end"
        assert len(result["messages"]) == 1
