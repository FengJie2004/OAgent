"""LangGraph StateGraph state definitions."""

from typing import Annotated, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


@dataclass
class AgentState:
    """LangGraph StateGraph 的核心状态定义。

    Attributes:
        messages: 消息历史，使用 LangGraph 的消息归约器
        next_action: 下一步执行动作 ("continue", "wait", "end")
        current_node: 当前执行的节点名称
        iteration_count: 当前迭代次数
        max_iterations: 最大迭代次数限制
        tool_calls: 工具调用列表
        tool_results: 工具执行结果列表
        rag_context: RAG 检索的上下文
        retrieved_docs: RAG 检索的文档列表
        human_feedback: 人工审核反馈
        requires_human_review: 是否需要人工审核
        thread_id: 对话线程 ID
        metadata: 元数据
        error: 错误信息
    """

    # 消息历史 - 使用 LangGraph 的消息归约器
    messages: Annotated[List[BaseMessage], add_messages] = field(default_factory=list)

    # 执行控制
    next_action: Literal["continue", "wait", "end"] = "continue"
    current_node: str = ""
    iteration_count: int = 0
    max_iterations: int = 10

    # 工具执行上下文
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)

    # RAG 上下文 (可选)
    rag_context: Optional[str] = None
    retrieved_docs: List[Dict[str, Any]] = field(default_factory=list)

    # 人工审核状态
    human_feedback: Optional[str] = None
    requires_human_review: bool = False

    # 元数据
    thread_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 错误处理
    error: Optional[str] = None
