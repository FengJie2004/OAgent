"""Human-in-the-loop workflow implementation.

Human-in-the-loop workflow:
LLM -> Review Check -> [Requires Review] -> Human Feedback -> LLM -> Output
                     -> [No Review] -> Output
"""

from typing import List, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from oagent.graph.builder import WorkflowBuilder
from oagent.graph import nodes, edges


def create_human_in_loop_workflow(
    llm: BaseChatModel,
    tools: List[BaseTool],
    system_prompt: Optional[str] = None
) -> Any:
    """创建人工审核工作流。

    工作流结构：
    ```
    [Entry] -> llm -> should_continue -> [tools, human_review, end]
                    ^                       |
                    |-----------------------+
                    ^
                    |
            human_feedback
    ```

    特点：
    - 支持工具调用
    - 支持人工审核中断
    - 使用 LangGraph 的 interrupt_before 功能

    Args:
        llm: LangChain LLM 实例
        tools: 工具列表
        system_prompt: 可选的系统提示词

    Returns:
        编译后的 StateGraph 实例（带有人工审核中断功能）
    """
    builder = WorkflowBuilder()

    # 将工具列表转换为字典
    tool_dict: dict[str, BaseTool] = {tool.name: tool for tool in tools}

    # 添加节点
    builder.add_node(
        "llm",
        nodes.llm_node(llm, system_prompt=system_prompt)
    )
    builder.add_node("tools", nodes.tool_node(tool_dict))
    builder.add_node("human_review", nodes.human_review_node())

    # 设置入口点
    builder.set_entry_point("llm")

    # 添加条件边：LLM -> 工具、人工审核或结束
    builder.add_conditional_edges(
        "llm",
        edges.should_continue,
        {
            "tools": "tools",
            "human_review": "human_review",
            "end": "end"
        }
    )

    # 添加边：工具 -> LLM
    builder.add_edge("tools", "llm")

    # 添加边：人工审核 -> LLM（等待反馈后继续）
    builder.add_edge("human_review", "llm")

    # 设置结束点
    builder.set_finish_point("llm")

    # 编译时在 human_review 节点前中断
    # 这样可以在需要人工审核时暂停工作流
    return builder.compile(interrupt_before=["human_review"])
