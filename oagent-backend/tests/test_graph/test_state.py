"""Tests for LangGraph state definitions."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from oagent.graph.state import AgentState


class TestAgentState:
    """测试 AgentState 状态定义。"""

    def test_initial_state(self):
        """测试初始状态。"""
        state = AgentState(thread_id="test-123")

        assert state.thread_id == "test-123"
        assert state.messages == []
        assert state.iteration_count == 0
        assert state.next_action == "continue"
        assert state.tool_calls == []
        assert state.tool_results == []
        assert state.retrieved_docs == []
        assert state.rag_context is None
        assert state.human_feedback is None
        assert state.requires_human_review is False
        assert state.error is None
        assert state.metadata == {}

    def test_state_with_messages(self):
        """测试带消息的状态。"""
        state = AgentState(thread_id="test-456")

        # 添加消息
        state.messages.append(HumanMessage(content="Hello"))
        state.messages.append(AIMessage(content="Hi there!"))

        assert len(state.messages) == 2
        assert state.messages[0].content == "Hello"
        assert state.messages[1].content == "Hi there!"

    def test_state_with_tool_calls(self):
        """测试带工具调用的状态。"""
        state = AgentState(
            thread_id="test-789",
            tool_calls=[
                {"id": "call_1", "name": "calculator", "args": {"expression": "2+2"}}
            ],
            iteration_count=1
        )

        assert len(state.tool_calls) == 1
        assert state.tool_calls[0]["name"] == "calculator"
        assert state.iteration_count == 1

    def test_state_with_rag_context(self):
        """测试带 RAG 上下文的状态。"""
        state = AgentState(
            thread_id="test-rag",
            rag_context="Document content here",
            retrieved_docs=[
                {"content": "Doc 1", "metadata": {"source": "test"}},
                {"content": "Doc 2", "metadata": {"source": "test"}}
            ]
        )

        assert state.rag_context == "Document content here"
        assert len(state.retrieved_docs) == 2

    def test_state_with_error(self):
        """测试带错误的状态。"""
        state = AgentState(
            thread_id="test-error",
            error="Something went wrong",
            next_action="end"
        )

        assert state.error == "Something went wrong"
        assert state.next_action == "end"

    def test_state_metadata(self):
        """测试状态元数据。"""
        state = AgentState(
            thread_id="test-meta",
            metadata={"workflow_type": "react", "custom_key": "custom_value"}
        )

        assert state.metadata["workflow_type"] == "react"
        assert state.metadata["custom_key"] == "custom_value"
