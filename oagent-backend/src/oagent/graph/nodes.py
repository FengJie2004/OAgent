"""LangGraph StateGraph node implementations."""

import json
from typing import Dict, Any, Callable, Awaitable, List, Optional
from loguru import logger

from oagent.graph.state import AgentState
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langchain_core.tools import BaseTool


async def llm_node(
    llm,
    system_prompt: Optional[str] = None
) -> Callable[[AgentState], Awaitable[Dict[str, Any]]]:
    """LLM 推理节点。

    Args:
        llm: LangChain LLM 实例
        system_prompt: 可选的系统提示词

    Returns:
        节点执行函数
    """
    async def execute(state: AgentState) -> Dict[str, Any]:
        logger.debug(f"LLM node executing, messages count: {len(state.messages)}")

        # 构建消息列表
        messages = list(state.messages)

        # 添加系统提示词（如果有）
        if system_prompt:
            from langchain_core.messages import SystemMessage
            messages.insert(0, SystemMessage(content=system_prompt))

        # 调用 LLM
        response = await llm.ainvoke(messages)

        # 提取工具调用
        tool_calls = []
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_calls = [
                {
                    "id": tc.get("id", ""),
                    "name": tc.get("name", ""),
                    "args": tc.get("args", {})
                }
                for tc in response.tool_calls
            ]

        return {
            "messages": [response],
            "tool_calls": tool_calls,
            "iteration_count": state.iteration_count + 1,
        }

    return execute


async def tool_node(
    tools: Dict[str, BaseTool]
) -> Callable[[AgentState], Awaitable[Dict[str, Any]]]:
    """工具执行节点。

    Args:
        tools: 工具名称到工具实例的映射

    Returns:
        节点执行函数
    """
    async def execute(state: AgentState) -> Dict[str, Any]:
        logger.debug(f"Tool node executing, tool_calls: {len(state.tool_calls)}")

        if not state.tool_calls:
            return {"tool_results": []}

        tool_results = []

        for tool_call in state.tool_calls:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            tool_call_id = tool_call.get("id", "")

            if tool_name not in tools:
                logger.warning(f"Tool not found: {tool_name}")
                tool_results.append({
                    "tool_call_id": tool_call_id,
                    "result": None,
                    "error": f"Tool not found: {tool_name}"
                })
                continue

            try:
                tool = tools[tool_name]
                # 同步执行工具
                if hasattr(tool, 'ainvoke'):
                    result = await tool.ainvoke(tool_args)
                else:
                    result = tool.invoke(tool_args)

                tool_results.append({
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name,
                    "result": result,
                    "error": None
                })
                logger.debug(f"Tool {tool_name} executed successfully")

            except Exception as e:
                logger.error(f"Tool execution error: {tool_name}: {e}")
                tool_results.append({
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name,
                    "result": None,
                    "error": str(e)
                })

        # 创建 ToolMessage 列表
        tool_messages = [
            ToolMessage(
                content=json.dumps(result.get("result", result)),
                tool_call_id=result["tool_call_id"]
            )
            for result in tool_results
            if result.get("tool_call_id")
        ]

        return {
            "messages": tool_messages,
            "tool_results": tool_results,
        }

    return execute


async def rag_node(
    vectorstore,
    embedding_model,
    top_k: int = 3
) -> Callable[[AgentState], Awaitable[Dict[str, Any]]]:
    """RAG 检索节点。

    Args:
        vectorstore: 向量存储实例
        embedding_model: 嵌入模型
        top_k: 检索文档数量

    Returns:
        节点执行函数
    """
    async def execute(state: AgentState) -> Dict[str, Any]:
        logger.debug(f"RAG node executing, top_k: {top_k}")

        # 获取最后一条用户消息
        last_message = None
        for msg in reversed(state.messages):
            if isinstance(msg, HumanMessage):
                last_message = msg.content
                break

        if not last_message:
            return {
                "retrieved_docs": [],
                "rag_context": None
            }

        try:
            # 生成查询嵌入
            query_embedding = await embedding_model.embed_query(last_message)

            # 执行相似度搜索
            results = await vectorstore.similarity_search_by_vector(
                query_embedding,
                k=top_k
            )

            # 提取文档内容
            retrieved_docs = [
                {
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "score": getattr(doc, 'score', None)
                }
                for doc in results
            ]

            # 构建 RAG 上下文
            rag_context = "\n\n".join([
                f"[Document {i+1}]\n{doc['content']}"
                for i, doc in enumerate(retrieved_docs)
            ])

            logger.info(f"RAG retrieved {len(retrieved_docs)} documents")

            return {
                "retrieved_docs": retrieved_docs,
                "rag_context": rag_context
            }

        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return {
                "retrieved_docs": [],
                "rag_context": None,
                "error": str(e)
            }

    return execute


async def human_review_node() -> Callable[[AgentState], Awaitable[Dict[str, Any]]]:
    """人工审核节点。

    Returns:
        节点执行函数
    """
    async def execute(state: AgentState) -> Dict[str, Any]:
        logger.info("Human review node executing - waiting for human feedback")

        # 此节点会中断工作流，等待人工输入
        # 实际实现依赖于 LangGraph 的 interrupt 功能
        from langgraph.errors import GraphInterrupt

        # 设置需要人工审核的标志
        return {
            "requires_human_review": True,
            "next_action": "wait",
        }

    return execute


async def error_handler_node() -> Callable[[AgentState], Awaitable[Dict[str, Any]]]:
    """错误处理节点。

    Returns:
        节点执行函数
    """
    async def execute(state: AgentState) -> Dict[str, Any]:
        logger.error(f"Error handler node executing, error: {state.error}")

        return {
            "next_action": "end",
            "messages": [AIMessage(content=f"Error occurred: {state.error}")]
        }

    return execute
