"""Tests for LangGraph edge conditions."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from oagent.graph.state import AgentState
from oagent.graph.edges import (
    has_tool_calls,
    should_continue,
    route_after_tool,
    route_after_llm,
    check_human_feedback,
)


class TestHasToolCalls:
    """测试 has_tool_calls 函数。"""

    def test_has_tool_calls_empty_state(self):
        """测试空状态。"""
        state = AgentState(thread_id="test-1")
        assert has_tool_calls(state) is False

    def test_has_tool_calls_with_tool_calls_list(self):
        """测试有工具调用列表。"""
        state = AgentState(
            thread_id="test-2",
            tool_calls=[{"id": "1", "name": "calculator", "args": {}}]
        )
        assert has_tool_calls(state) is True

    def test_has_tool_calls_with_message_tool_calls(self):
        """测试有消息工具调用。"""
        state = AgentState(
            thread_id="test-3",
            messages=[
                AIMessage(
                    content="Let me calculate",
                    tool_calls=[{"id": "1", "name": "calculator", "args": {}}]
                )
            ]
        )
        assert has_tool_calls(state) is True

    def test_has_tool_calls_no_tool_calls(self):
        """测试没有工具调用。"""
        state = AgentState(
            thread_id="test-4",
            messages=[
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there!")
            ]
        )
        assert has_tool_calls(state) is False


class TestShouldContinue:
    """测试 should_continue 函数。"""

    def test_should_continue_with_error(self):
        """测试有错误的情况。"""
        state = AgentState(
            thread_id="test-5",
            error="Something went wrong"
        )
        assert should_continue(state) == "end"

    def test_should_continue_max_iterations(self):
        """测试达到最大迭代次数。"""
        state = AgentState(
            thread_id="test-6",
            iteration_count=10,
            max_iterations=10
        )
        assert should_continue(state) == "end"

    def test_should_continue_with_tool_calls(self):
        """测试有工具调用。"""
        state = AgentState(
            thread_id="test-7",
            tool_calls=[{"id": "1", "name": "calculator", "args": {}}],
            iteration_count=1,
            max_iterations=10
        )
        assert should_continue(state) == "tools"

    def test_should_continue_no_tool_calls(self):
        """测试没有工具调用。"""
        state = AgentState(
            thread_id="test-8",
            messages=[AIMessage(content="Hello")],
            iteration_count=1,
            max_iterations=10
        )
        assert should_continue(state) == "llm"

    def test_should_continue_human_review(self):
        """测试需要人工审核。"""
        state = AgentState(
            thread_id="test-9",
            requires_human_review=True,
            iteration_count=1,
            max_iterations=10
        )
        assert should_continue(state) == "human_review"


class TestRouteAfterTool:
    """测试 route_after_tool 函数。"""

    def test_route_after_tool_normal(self):
        """测试正常情况。"""
        state = AgentState(thread_id="test-10")
        assert route_after_tool(state) == "llm"

    def test_route_after_tool_with_error(self):
        """测试有错误的情况。"""
        state = AgentState(
            thread_id="test-11",
            error="Tool execution failed"
        )
        assert route_after_tool(state) == "end"

    def test_route_after_tool_max_iterations(self):
        """测试达到最大迭代次数。"""
        state = AgentState(
            thread_id="test-12",
            iteration_count=10,
            max_iterations=10
        )
        assert route_after_tool(state) == "end"


class TestRouteAfterLLM:
    """测试 route_after_llm 函数。"""

    def test_route_after_llm_no_tool_calls(self):
        """测试没有工具调用。"""
        state = AgentState(
            thread_id="test-13",
            messages=[AIMessage(content="Hello")]
        )
        assert route_after_llm(state) == "end"

    def test_route_after_llm_with_tool_calls(self):
        """测试有工具调用。"""
        state = AgentState(
            thread_id="test-14",
            tool_calls=[{"id": "1", "name": "calculator", "args": {}}]
        )
        assert route_after_llm(state) == "tools"

    def test_route_after_llm_with_error(self):
        """测试有错误的情况。"""
        state = AgentState(
            thread_id="test-15",
            error="LLM failed"
        )
        assert route_after_llm(state) == "end"

    def test_route_after_llm_human_review(self):
        """测试需要人工审核。"""
        state = AgentState(
            thread_id="test-16",
            requires_human_review=True
        )
        assert route_after_llm(state) == "human_review"


class TestCheckHumanFeedback:
    """测试 check_human_feedback 函数。"""

    def test_check_human_feedback_with_feedback(self):
        """测试有反馈的情况。"""
        state = AgentState(
            thread_id="test-17",
            human_feedback="Approved"
        )
        assert check_human_feedback(state) == "continue"

    def test_check_human_feedback_no_feedback(self):
        """测试没有反馈的情况。"""
        state = AgentState(thread_id="test-18")
        assert check_human_feedback(state) == "wait"

    def test_check_human_feedback_empty_feedback(self):
        """测试空反馈的情况。"""
        state = AgentState(
            thread_id="test-19",
            human_feedback=""
        )
        # 空字符串也算有反馈值
        assert check_human_feedback(state) == "continue"
