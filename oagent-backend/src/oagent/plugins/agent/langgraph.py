"""LangGraph StateGraph Agent plugin implementation."""

import json
from typing import AsyncIterator, Dict, List, Optional, Any
from loguru import logger

from oagent.core.registry import register_plugin
from oagent.config.settings import settings
from oagent.models.agent import AgentConfig, ToolCall
from oagent.models.llm import Message
from oagent.plugins.agent.base import AgentPluginBase
from oagent.services.memory_service import MemoryService
from oagent.tools.registry import ToolRegistry
from oagent.graph.workflows import (
    create_react_workflow,
    create_rag_workflow,
    create_human_in_loop_workflow,
)


@register_plugin("agent", "langgraph")
class LangGraphAgentPlugin(AgentPluginBase):
    """LangGraph StateGraph Agent 实现复杂工作流编排。

    支持的工作流类型：
    - react: 基础 ReAct 工作流 (Reasoning + Acting)
    - rag: RAG 增强工作流 (Retrieval-Augmented Generation)
    - human_in_loop: 人工审核工作流

    特性：
    - 流式和非流式执行
    - 对话记忆持久化
    - 人工审核中断/恢复
    - 工具调用支持
    """

    def __init__(self):
        self._config: Optional[AgentConfig] = None
        self._workflow: Any = None  # CompiledGraph
        self._memory_service: MemoryService = MemoryService()
        self._tools: List[Any] = []
        self._logger = logger
        self._checkpointer: Optional[Any] = None
        self._workflow_type: str = "react"

    @property
    def name(self) -> str:
        return "langgraph"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "LangGraph StateGraph Agent for complex workflow orchestration"

    @property
    def supported_tools(self) -> List[str]:
        """获取支持的工具列表。"""
        registry = ToolRegistry()
        return list(registry.list_tools().keys())

    @property
    def supported_workflows(self) -> List[str]:
        """支持的工作流类型。"""
        return ["react", "rag", "human_in_loop"]

    async def initialize(self, config: AgentConfig) -> None:
        """初始化 LangGraph Agent。

        Args:
            config: Agent 配置

        Raises:
            ValueError: 如果配置无效
            RuntimeError: 如果初始化失败
        """
        self._config = config
        self._logger.info(f"Initializing LangGraph agent: {config.agent_type}")

        try:
            # 加载工具
            self._tools = await self._load_tools(config.tools)

            # 获取 LLM
            llm = await self._get_llm(config)

            # 获取工作流类型
            self._workflow_type = getattr(config, 'metadata', {}).get('workflow_type', 'react')

            # 创建工作流
            self._workflow = await self._create_workflow(
                workflow_type=self._workflow_type,
                llm=llm,
                tools=self._tools,
                config=config
            )

            # 设置检查点器 (持久化)
            if config.memory_enabled:
                self._checkpointer = await self._create_checkpointer()

            self._logger.info("LangGraph agent initialized successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize LangGraph agent: {e}")
            raise RuntimeError(f"Initialization failed: {e}")

    async def run(
        self,
        input: str,
        thread_id: str,
        stream: bool = False
    ) -> Dict[str, Any]:
        """运行工作流。

        Args:
            input: 用户输入
            thread_id: 对话线程 ID
            stream: 是否流式返回

        Returns:
            Agent 响应

        Raises:
            RuntimeError: 如果 agent 未初始化
        """
        if not self._workflow:
            raise RuntimeError("Agent not initialized")

        # 构建初始状态
        initial_state = await self._build_initial_state(input, thread_id)

        # 执行工作流
        config = {"configurable": {"thread_id": thread_id}}

        if stream:
            # 流式执行
            response = await self._run_streaming(initial_state, config)
        else:
            # 非流式执行
            response = await self._workflow.ainvoke(initial_state, config=config)

        # 提取输出
        return self._parse_response(response)

    async def run_stream(
        self,
        input: str,
        thread_id: str
    ) -> AsyncIterator[str]:
        """流式运行工作流。

        Args:
            input: 用户输入
            thread_id: 线程 ID

        Yields:
            Agent 响应的 token

        Raises:
            RuntimeError: 如果 agent 未初始化
        """
        if not self._workflow:
            raise RuntimeError("Agent not initialized")

        initial_state = await self._build_initial_state(input, thread_id)
        config = {"configurable": {"thread_id": thread_id}}

        # 使用 astream_events 获取流式输出
        async for event in self._workflow.astream_events(
            initial_state,
            config=config,
            version="v2"
        ):
            event_type = event.get("event")

            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content"):
                    token = chunk.content
                    if token:
                        yield token

    async def get_state(self, thread_id: str) -> Dict[str, Any]:
        """获取线程状态。

        Args:
            thread_id: 线程 ID

        Returns:
            当前状态
        """
        if not self._checkpointer:
            return {"thread_id": thread_id, "messages": []}

        try:
            state = await self._checkpointer.aget_tuple(thread_id=thread_id)

            if state:
                return self._convert_state_for_response(state)
            return {"thread_id": thread_id, "messages": []}

        except Exception as e:
            self._logger.error(f"Failed to get state: {e}")
            return {"thread_id": thread_id, "messages": []}

    async def clear_memory(self, thread_id: str) -> bool:
        """清除线程记忆。

        Args:
            thread_id: 线程 ID

        Returns:
            True 如果成功
        """
        try:
            await self._memory_service.clear(thread_id)
            return True
        except Exception as e:
            self._logger.error(f"Failed to clear memory: {e}")
            return False

    async def interrupt(self, thread_id: str) -> bool:
        """中断工作流。

        Args:
            thread_id: 线程 ID

        Returns:
            True 如果成功
        """
        if self._checkpointer:
            try:
                await self._checkpointer.delete(thread_id)
                return True
            except Exception as e:
                self._logger.error(f"Failed to interrupt: {e}")
        return False

    async def resume(
        self,
        thread_id: str,
        human_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """恢复被中断的工作流。

        Args:
            thread_id: 线程 ID
            human_feedback: 人工反馈

        Returns:
            Agent 响应

        Raises:
            RuntimeError: 如果未启用检查点器
        """
        if not self._checkpointer:
            raise RuntimeError("Checkpointer not enabled")

        # 使用 LangGraph 的 resume 功能
        response = await self._workflow.ainvoke(
            {"human_feedback": human_feedback},
            config={"configurable": {"thread_id": thread_id}}
        )

        return self._parse_response(response)

    # ==================== 辅助方法 ====================

    async def _load_tools(self, tool_names: List[str]) -> List[Any]:
        """加载工具。

        Args:
            tool_names: 工具名称列表

        Returns:
            工具实例列表
        """
        registry = ToolRegistry()

        if not tool_names:
            # 返回所有可用工具
            return list(registry.list_tools().values())

        # 返回指定工具
        tools = []
        for name in tool_names:
            tool = registry.get_tool(name)
            if tool:
                tools.append(tool)
            else:
                self._logger.warning(f"Tool not found: {name}")

        return tools

    async def _get_llm(self, config: AgentConfig) -> Any:
        """获取 LLM 实例。

        Args:
            config: Agent 配置

        Returns:
            LLM 实例

        Raises:
            ValueError: 如果不支持该 LLM 提供商
        """
        from langchain_openai import ChatOpenAI
        from langchain_anthropic import ChatAnthropic
        from langchain_ollama import ChatOllama

        provider = config.llm_provider.lower()

        if provider == "openai":
            return ChatOpenAI(
                model=config.llm_model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        elif provider == "dashscope":
            return ChatOpenAI(
                model=config.llm_model,
                api_key=settings.dashscope_api_key,
                base_url=settings.dashscope_base_url,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model=config.llm_model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        elif provider == "ollama":
            return ChatOllama(
                model=config.llm_model,
                base_url=settings.ollama_base_url,
                temperature=config.temperature,
                num_predict=config.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    async def _create_checkpointer(self) -> Any:
        """创建检查点器。

        Returns:
            检查点器实例
        """
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

    async def _create_workflow(
        self,
        workflow_type: str,
        llm: Any,
        tools: List[Any],
        config: AgentConfig
    ) -> Any:
        """创建工作流。

        Args:
            workflow_type: 工作流类型
            llm: LLM 实例
            tools: 工具列表
            config: Agent 配置

        Returns:
            编译后的工作流
        """
        if workflow_type == "rag":
            # RAG 工作流需要向量存储和嵌入模型
            vectorstore = await self._get_vectorstore(config)
            embedding = await self._get_embedding(config)
            return create_rag_workflow(
                llm,
                tools,
                vectorstore,
                embedding,
                rag_top_k=getattr(config, 'metadata', {}).get('rag_top_k', 3),
                system_prompt=config.system_prompt,
            )
        elif workflow_type == "human_in_loop":
            return create_human_in_loop_workflow(
                llm,
                tools,
                system_prompt=config.system_prompt,
            )
        else:  # default to react
            return create_react_workflow(llm, tools)

    async def _get_vectorstore(self, config: AgentConfig) -> Any:
        """获取向量存储实例。"""
        # 从插件系统获取向量存储
        from oagent.plugins.vectorstore.chroma import ChromaVectorStorePlugin

        vectorstore_plugin = ChromaVectorStorePlugin()
        await vectorstore_plugin.initialize(
            collection_name="oagent_rag",
            embedding_dimension=1024,
            persist_directory=settings.vector_store_path,
        )
        return vectorstore_plugin

    async def _get_embedding(self, config: AgentConfig) -> Any:
        """获取嵌入模型实例。"""
        from oagent.plugins.embedding.dashscope import DashScopeEmbeddingPlugin

        embedding_plugin = DashScopeEmbeddingPlugin()
        # 简单包装以适配 LangChain 接口
        class EmbeddingWrapper:
            def __init__(self, plugin):
                self._plugin = plugin

            async def embed_query(self, text: str) -> List[float]:
                embeddings = await self._plugin.embed_documents([text])
                return embeddings[0] if embeddings else []

        return EmbeddingWrapper(embedding_plugin)

    async def _build_initial_state(
        self,
        input: str,
        thread_id: str
    ) -> Dict[str, Any]:
        """构建初始状态。

        Args:
            input: 用户输入
            thread_id: 线程 ID

        Returns:
            初始状态字典
        """
        from langchain_core.messages import HumanMessage

        # 获取历史消息
        history = await self._memory_service.get_messages(thread_id)

        # 转换为 LangChain 消息格式
        lc_messages = []
        for msg in history:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            else:
                from langchain_core.messages import AIMessage
                lc_messages.append(AIMessage(content=msg.content))

        # 添加当前输入
        lc_messages.append(HumanMessage(content=input))

        return {
            "messages": lc_messages,
            "thread_id": thread_id,
            "iteration_count": 0,
            "max_iterations": self._config.max_iterations if self._config else 10,
        }

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析响应。

        Args:
            response: 工作流响应

        Returns:
            解析后的响应
        """
        messages = response.get("messages", [])
        last_message = messages[-1] if messages else None

        # 提取工具调用
        tool_calls = []
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls.extend([
                    {
                        "id": tc.get("id", ""),
                        "tool_name": tc.get("name", ""),
                        "args": tc.get("args", {}),
                    }
                    for tc in msg.tool_calls
                ])

        return {
            "output": last_message.content if last_message else "",
            "thread_id": response.get("thread_id", ""),
            "tool_calls": tool_calls,
            "metadata": {
                "iterations": response.get("iteration_count", 0),
                "workflow_type": self._workflow_type,
            }
        }

    def _convert_state_for_response(self, state: Any) -> Dict[str, Any]:
        """将内部状态转换为响应格式。

        Args:
            state: 内部状态

        Returns:
            响应格式的状态
        """
        messages = []
        if hasattr(state, 'messages'):
            for msg in state.messages:
                messages.append({
                    "role": getattr(msg, 'type', 'unknown'),
                    "content": getattr(msg, 'content', ''),
                })

        return {
            "thread_id": getattr(state, 'thread_id', ''),
            "messages": messages,
            "current_node": getattr(state, 'current_node', ''),
            "iteration_count": getattr(state, 'iteration_count', 0),
        }
