"""Basic ReAct workflow implementation.

ReAct (Reasoning + Acting) workflow:
LLM -> Tool Call -> Execute -> LLM -> Output
"""

from typing import Dict, List, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from oagent.graph.builder import WorkflowBuilder
from oagent.graph import nodes, edges


def create_react_workflow(
    llm: BaseChatModel,
    tools: List[BaseTool]
) -> Any:
    """创建基础 ReAct 工作流。

    工作流结构：
    ```
    [Entry] -> llm -> should_continue -> [tools, end]
                    ^                     |
                    |---------------------+
    ```

    Args:
        llm: LangChain LLM 实例
        tools: 工具列表

    Returns:
        编译后的 StateGraph 实例
    """
    builder = WorkflowBuilder()

    # 将工具列表转换为字典
    tool_dict: Dict[str, BaseTool] = {tool.name: tool for tool in tools}

    # 添加节点
    builder.add_node("llm", nodes.llm_node(llm))
    builder.add_node("tools", nodes.tool_node(tool_dict))

    # 设置入口点
    builder.set_entry_point("llm")

    # 添加条件边：LLM -> 工具或结束
    builder.add_conditional_edges(
        "llm",
        edges.should_continue,
        {
            "tools": "tools",
            "end": "end"
        }
    )

    # 添加边：工具 -> LLM
    builder.add_edge("tools", "llm")

    # 设置结束点
    builder.set_finish_point("llm")

    return builder.compile()
