"""Tests for LangGraph workflow builder."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from oagent.graph.state import AgentState
from oagent.graph.builder import WorkflowBuilder


class TestWorkflowBuilder:
    """测试工作流构建器。"""

    def test_build_simple_graph(self):
        """测试构建简单图。"""
        builder = WorkflowBuilder()

        # 定义简单节点
        async def node_a(state):
            return {}

        async def node_b(state):
            return {}

        # 构建图
        builder.add_node("a", node_a)
        builder.add_node("b", node_b)
        builder.set_entry_point("a")
        builder.add_edge("a", "b")
        builder.set_finish_point("b")

        # 编译
        graph = builder.compile()

        assert graph is not None
        assert builder.get_nodes() == {"a", "b"}

    def test_build_conditional_graph(self):
        """测试构建条件图。"""
        builder = WorkflowBuilder()

        def condition(state):
            return "b" if state.get("flag") else "c"

        async def node_a(state):
            return {}

        async def node_b(state):
            return {}

        async def node_c(state):
            return {}

        # 构建图
        builder.add_node("a", node_a)
        builder.add_node("b", node_b)
        builder.add_node("c", node_c)
        builder.set_entry_point("a")
        builder.add_conditional_edges(
            "a",
            condition,
            {"b": "b", "c": "c"}
        )
        builder.set_finish_point("b")
        builder.set_finish_point("c")

        # 编译
        graph = builder.compile()

        assert graph is not None

    def test_add_node_duplicate(self):
        """测试添加重复节点。"""
        builder = WorkflowBuilder()

        async def node_func(state):
            return {}

        builder.add_node("test", node_func)

        # LangGraph 不允许添加重复节点，应该抛出 ValueError
        with pytest.raises(ValueError, match="Node `test` already present"):
            builder.add_node("test", node_func)

        assert builder.get_nodes() == {"test"}

    def test_add_edge_nonexistent_node(self):
        """测试添加不存在节点的边。"""
        builder = WorkflowBuilder()

        async def node_func(state):
            return {}

        builder.add_node("a", node_func)

        # 尝试添加指向不存在节点的边
        with pytest.raises(ValueError, match="Node 'b' has not been added"):
            builder.add_edge("a", "b")

    def test_add_edge_from_nonexistent_node(self):
        """测试从不存在节点添加边。"""
        builder = WorkflowBuilder()

        async def node_func(state):
            return {}

        builder.add_node("b", node_func)

        # 尝试从不存在的节点添加边
        with pytest.raises(ValueError, match="Node 'a' has not been added"):
            builder.add_edge("a", "b")

    def test_set_entry_point_nonexistent_node(self):
        """测试设置不存在的入口节点。"""
        builder = WorkflowBuilder()

        with pytest.raises(ValueError, match="Node 'nonexistent' has not been added"):
            builder.set_entry_point("nonexistent")

    def test_set_finish_point_nonexistent_node(self):
        """测试设置不存在的结束点。"""
        builder = WorkflowBuilder()

        with pytest.raises(ValueError, match="Node 'nonexistent' has not been added"):
            builder.set_finish_point("nonexistent")

    def test_compile_without_entry_point(self):
        """测试在没有设置入口点时编译。"""
        builder = WorkflowBuilder()

        async def node_func(state):
            return {}

        builder.add_node("a", node_func)

        with pytest.raises(RuntimeError, match="Entry point must be set"):
            builder.compile()

    def test_compile_with_checkpointer(self):
        """测试带检查点器编译。"""
        from langgraph.checkpoint.memory import MemorySaver

        builder = WorkflowBuilder()

        async def node_func(state):
            return {}

        builder.add_node("a", node_func)
        builder.set_entry_point("a")
        builder.set_finish_point("a")

        # 使用真实的 MemorySaver
        checkpointer = MemorySaver()
        graph = builder.compile(checkpointer=checkpointer)

        assert graph is not None

    def test_compile_with_interrupt(self):
        """测试带中断点编译。"""
        builder = WorkflowBuilder()

        async def node_a(state):
            return {}

        async def node_b(state):
            return {}

        builder.add_node("a", node_a)
        builder.add_node("b", node_b)
        builder.set_entry_point("a")
        builder.add_edge("a", "b")
        builder.set_finish_point("b")

        # 在节点 b 前中断
        graph = builder.compile(interrupt_before=["b"])

        assert graph is not None

    def test_method_chaining(self):
        """测试方法链式调用。"""
        builder = WorkflowBuilder()

        async def node_a(state):
            return {}

        async def node_b(state):
            return {}

        # 链式调用
        result = (
            builder
            .add_node("a", node_a)
            .add_node("b", node_b)
            .set_entry_point("a")
            .add_edge("a", "b")
            .set_finish_point("b")
        )

        assert result is builder
        assert builder.get_nodes() == {"a", "b"}

    def test_get_nodes(self):
        """测试获取节点列表。"""
        builder = WorkflowBuilder()

        async def node_func(state):
            return {}

        builder.add_node("node1", node_func)
        builder.add_node("node2", node_func)
        builder.add_node("node3", node_func)

        nodes = builder.get_nodes()

        assert nodes == {"node1", "node2", "node3"}
        # 验证返回的是副本
        nodes.add("node4")
        assert builder.get_nodes() == {"node1", "node2", "node3"}


# 需要 MagicMock
from unittest.mock import MagicMock
