"""RAG (Retrieval-Augmented Generation) workflow implementation.

RAG workflow:
User Input -> Retrieve -> LLM (with context) -> Tool Call -> Execute -> Output
"""

from typing import Dict, List, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from oagent.graph.builder import WorkflowBuilder
from oagent.graph import nodes, edges


def create_rag_workflow(
    llm: BaseChatModel,
    tools: List[BaseTool],
    vectorstore: Any,
    embedding_model: Any,
    rag_top_k: int = 3,
    system_prompt: Optional[str] = None
) -> Any:
    """创建 RAG 增强工作流。

    工作流结构：
    ```
    [Entry] -> retrieve -> llm -> should_continue -> [tools, end]
                              ^                       |
                              |-----------------------+
    ```

    Args:
        llm: LangChain LLM 实例
        tools: 工具列表
        vectorstore: 向量存储实例
        embedding_model: 嵌入模型
        rag_top_k: 检索文档数量，默认 3
        system_prompt: 可选的系统提示词

    Returns:
        编译后的 StateGraph 实例
    """
    builder = WorkflowBuilder()

    # 将工具列表转换为字典
    tool_dict: Dict[str, BaseTool] = {tool.name: tool for tool in tools}

    # 添加节点
    builder.add_node(
        "retrieve",
        nodes.rag_node(vectorstore, embedding_model, top_k=rag_top_k)
    )
    builder.add_node(
        "llm",
        nodes.llm_node(llm, system_prompt=system_prompt)
    )
    builder.add_node("tools", nodes.tool_node(tool_dict))

    # 设置入口点
    builder.set_entry_point("retrieve")

    # 添加边：retrieve -> llm
    builder.add_edge("retrieve", "llm")

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
