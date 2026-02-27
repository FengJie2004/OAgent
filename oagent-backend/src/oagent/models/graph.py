"""Pydantic models for LangGraph workflows."""

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    """工作流配置。

    Attributes:
        workflow_type: 工作流类型 (react, rag, human_in_loop, custom)
        max_iterations: 最大迭代次数
        rag_top_k: RAG 检索文档数量
        rag_threshold: RAG 相似度阈值
        auto_review_keywords: 触发人工审核的关键词
        checkpointer_enabled: 启用检查点器
        checkpointer_type: 检查点器类型
    """

    workflow_type: Literal["react", "rag", "human_in_loop", "custom"] = Field(
        default="react",
        description="工作流类型"
    )
    max_iterations: int = Field(default=10, ge=1, description="最大迭代次数")

    # RAG 特定配置
    rag_top_k: int = Field(default=3, ge=1, description="RAG 检索文档数量")
    rag_threshold: float = Field(default=0.7, ge=0, le=1, description="RAG 相似度阈值")

    # 人工审核配置
    auto_review_keywords: List[str] = Field(
        default_factory=list,
        description="触发人工审核的关键词"
    )

    # 检查点配置
    checkpointer_enabled: bool = Field(default=True, description="启用检查点器")
    checkpointer_type: Literal["memory", "sqlite", "redis"] = Field(
        default="memory",
        description="检查点器类型"
    )


class GraphState(BaseModel):
    """图状态快照。

    Attributes:
        thread_id: 线程 ID
        current_node: 当前节点
        messages: 消息列表
        tool_calls: 工具调用列表
        iteration_count: 迭代次数
        metadata: 元数据
    """

    thread_id: str = Field(..., description="线程 ID")
    current_node: str = Field(default="", description="当前节点")
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="消息列表"
    )
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="工具调用列表"
    )
    iteration_count: int = Field(default=0, description="迭代次数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class GraphInterruptState(BaseModel):
    """图中断状态。

    Attributes:
        thread_id: 线程 ID
        interrupted_at: 中断位置
        pending_actions: 待处理动作
        human_feedback_required: 是否需要人工反馈
    """

    thread_id: str = Field(..., description="线程 ID")
    interrupted_at: str = Field(..., description="中断位置")
    pending_actions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="待处理动作"
    )
    human_feedback_required: bool = Field(
        default=False,
        description="是否需要人工反馈"
    )
