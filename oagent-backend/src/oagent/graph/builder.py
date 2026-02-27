"""LangGraph StateGraph workflow builder."""

from typing import Callable, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from loguru import logger

from oagent.graph.state import AgentState


class WorkflowBuilder:
    """LangGraph 工作流构建器。

    提供流式 API 来构建 StateGraph 工作流。

    Example:
        ```python
        builder = WorkflowBuilder()
        builder.add_node("llm", llm_node_func)
               .add_node("tools", tool_node_func)
               .set_entry_point("llm")
               .add_conditional_edges("llm", should_continue, {"tools": "tools", "end": "end"})
               .add_edge("tools", "llm")
               .set_finish_point("llm")
        graph = builder.compile()
        ```
    """

    def __init__(self):
        """初始化工作流构建器。"""
        self.graph = StateGraph(AgentState)
        self._nodes_added: set = set()
        self._entry_point_set: bool = False
        self._logger = logger

    def add_node(
        self,
        name: str,
        node_func: Callable[[AgentState], Any]
    ) -> "WorkflowBuilder":
        """添加节点到图。

        Args:
            name: 节点名称
            node_func: 节点执行函数

        Returns:
            self for method chaining
        """
        if name in self._nodes_added:
            self._logger.warning(f"Node '{name}' already added, overwriting")

        self.graph.add_node(name, node_func)
        self._nodes_added.add(name)
        self._logger.debug(f"Added node: {name}")
        return self

    def add_edge(
        self,
        from_node: str,
        to_node: str
    ) -> "WorkflowBuilder":
        """添加有向边到图。

        Args:
            from_node: 源节点名称
            to_node: 目标节点名称

        Returns:
            self for method chaining
        """
        if from_node not in self._nodes_added:
            raise ValueError(f"Node '{from_node}' has not been added")
        if to_node not in self._nodes_added and to_node != END:
            raise ValueError(f"Node '{to_node}' has not been added")

        self.graph.add_edge(from_node, to_node)
        self._logger.debug(f"Added edge: {from_node} -> {to_node}")
        return self

    def add_conditional_edges(
        self,
        source: str,
        condition: Callable[[AgentState], str],
        mapping: Optional[Dict[str, str]] = None
    ) -> "WorkflowBuilder":
        """添加条件边到图。

        Args:
            source: 源节点名称
            condition: 条件函数，接收 state 返回目标节点名称
            mapping: 可选的条件结果到节点名称的映射

        Returns:
            self for method chaining
        """
        if source not in self._nodes_added:
            raise ValueError(f"Node '{source}' has not been added")

        self.graph.add_conditional_edges(source, condition, mapping)
        self._logger.debug(f"Added conditional edges from: {source}")
        return self

    def set_entry_point(self, node: str) -> "WorkflowBuilder":
        """设置图的入口节点。

        Args:
            node: 入口节点名称

        Returns:
            self for method chaining
        """
        if node not in self._nodes_added:
            raise ValueError(f"Node '{node}' has not been added")

        self.graph.set_entry_point(node)
        self._entry_point_set = True
        self._logger.debug(f"Set entry point: {node}")
        return self

    def set_finish_point(self, node: str) -> "WorkflowBuilder":
        """设置图的结束点。

        添加从指定节点到 END 的边。

        Args:
            node: 结束节点名称

        Returns:
            self for method chaining
        """
        if node not in self._nodes_added:
            raise ValueError(f"Node '{node}' has not been added")

        self.graph.add_edge(node, END)
        self._logger.debug(f"Set finish point: {node}")
        return self

    def compile(
        self,
        checkpointer: Optional[Any] = None,
        interrupt_before: Optional[list] = None
    ) -> Any:
        """编译工作流。

        Args:
            checkpointer: 可选的检查点器用于持久化
            interrupt_before: 在这些节点前中断（用于人工审核）

        Returns:
            编译后的图实例

        Raises:
            RuntimeError: 如果入口节点未设置
        """
        if not self._entry_point_set:
            raise RuntimeError("Entry point must be set before compiling")

        self._logger.info("Compiling workflow")

        return self.graph.compile(
            checkpointer=checkpointer,
            interrupt_before=interrupt_before
        )

    def get_nodes(self) -> set:
        """获取所有已添加的节点名称。

        Returns:
            节点名称集合
        """
        return self._nodes_added.copy()
