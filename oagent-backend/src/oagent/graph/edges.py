"""LangGraph StateGraph edge and condition implementations."""

from typing import Literal
from loguru import logger
from oagent.graph.state import AgentState


def has_tool_calls(state: AgentState) -> bool:
    """检查是否有工具调用。

    Args:
        state: Agent state

    Returns:
        True if there are tool calls to execute
    """
    # 先检查 tool_calls 列表
    if state.tool_calls:
        return True

    # 检查最新的 AI 消息是否有工具调用
    if not state.messages:
        return False

    last_message = state.messages[-1]

    # 检查消息本身的工具调用
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return True

    return False


def should_continue(state: AgentState) -> Literal["tools", "llm", "end", "human_review"]:
    """决定是否继续执行以及下一步去哪里。

    决策逻辑：
    1. 如果有错误，结束
    2. 如果达到最大迭代次数，结束
    3. 如果需要人工审核，去人工审核节点
    4. 如果有工具调用，去工具节点
    5. 否则继续 LLM

    Args:
        state: Agent state

    Returns:
        下一个节点名称
    """
    # 检查错误
    if state.error:
        logger.debug("Should continue: error present, ending")
        return "end"

    # 检查迭代次数
    if state.iteration_count >= state.max_iterations:
        logger.debug(f"Should continue: max iterations ({state.max_iterations}) reached, ending")
        return "end"

    # 检查是否需要人工审核
    if state.requires_human_review:
        logger.debug("Should continue: human review required")
        return "human_review"

    # 检查是否有工具调用
    if has_tool_calls(state):
        logger.debug("Should continue: tool calls present, going to tools")
        return "tools"

    # 默认继续 LLM
    logger.debug("Should continue: no tool calls, going to llm")
    return "llm"


def route_after_tool(state: AgentState) -> Literal["llm", "end"]:
    """工具执行后的路由决策。

    工具执行后总是返回 LLM 进行下一步推理。

    Args:
        state: Agent state

    Returns:
        下一个节点名称
    """
    # 检查是否有错误
    if state.error:
        return "end"

    # 检查迭代次数
    if state.iteration_count >= state.max_iterations:
        return "end"

    # 总是返回 LLM
    return "llm"


def route_after_llm(state: AgentState) -> Literal["tools", "end", "human_review"]:
    """LLM 执行后的路由决策。

    Args:
        state: Agent state

    Returns:
        下一个节点名称
    """
    # 检查错误
    if state.error:
        return "end"

    # 检查迭代次数
    if state.iteration_count >= state.max_iterations:
        return "end"

    # 检查是否需要人工审核
    if state.requires_human_review:
        return "human_review"

    # 检查是否有工具调用
    if has_tool_calls(state):
        return "tools"

    # 没有工具调用，结束
    return "end"


def check_human_feedback(state: AgentState) -> Literal["continue", "wait"]:
    """检查是否收到人工反馈。

    Args:
        state: Agent state

    Returns:
        "continue" if feedback received, "wait" otherwise
    """
    if state.human_feedback is not None:
        return "continue"
    return "wait"
