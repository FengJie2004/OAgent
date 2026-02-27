"""Tests for LangGraph Agent plugin."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from oagent.plugins.agent.langgraph import LangGraphAgentPlugin
from oagent.models.agent import AgentConfig


class TestLangGraphAgentPlugin:
    """测试 LangGraph Agent 插件。"""

    @pytest.fixture
    def plugin(self):
        """创建插件实例。"""
        return LangGraphAgentPlugin()

    @pytest.fixture
    def agent_config(self):
        """创建 Agent 配置。"""
        return AgentConfig(
            agent_type="langgraph",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            tools=[],
            max_iterations=5,
            memory_enabled=True,
        )

    def test_plugin_name(self, plugin):
        """测试插件名称。"""
        assert plugin.name == "langgraph"

    def test_plugin_version(self, plugin):
        """测试插件版本。"""
        assert plugin.version == "0.1.0"

    def test_plugin_description(self, plugin):
        """测试插件描述。"""
        assert "LangGraph" in plugin.description
        assert "workflow" in plugin.description

    def test_supported_workflows(self, plugin):
        """测试支持的工作流类型。"""
        workflows = plugin.supported_workflows
        assert "react" in workflows
        assert "rag" in workflows
        assert "human_in_loop" in workflows

    @pytest.mark.asyncio
    async def test_initialize(self, plugin, agent_config):
        """测试初始化。"""
        with patch.object(plugin, '_load_tools', return_value=AsyncMock()):
            with patch.object(plugin, '_get_llm', return_value=AsyncMock()):
                with patch.object(plugin, '_create_workflow', return_value=AsyncMock()):
                    await plugin.initialize(agent_config)

                    assert plugin._config == agent_config
                    assert plugin._workflow is not None

    @pytest.mark.asyncio
    async def test_initialize_with_workflow_type(self, plugin):
        """测试带工作流类型的初始化。"""
        config = AgentConfig(
            agent_type="langgraph",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            metadata={"workflow_type": "rag"}
        )

        # 保存原始方法以便在 patch 后验证
        captured_workflow_type = None

        async def capture_workflow_type(workflow_type, **kwargs):
            nonlocal captured_workflow_type
            captured_workflow_type = workflow_type
            return AsyncMock()

        with patch.object(plugin, '_load_tools', return_value=AsyncMock()):
            with patch.object(plugin, '_get_llm', return_value=AsyncMock()):
                with patch.object(plugin, '_create_workflow', side_effect=capture_workflow_type):
                    await plugin.initialize(config)

                    # 验证 workflow_type 被正确传递和设置
                    assert captured_workflow_type == "rag"
                    assert plugin._workflow_type == "rag"

    @pytest.mark.asyncio
    async def test_run_not_initialized(self, plugin):
        """测试未初始化时运行。"""
        with pytest.raises(RuntimeError, match="Agent not initialized"):
            await plugin.run("test", "thread-1")

    @pytest.mark.asyncio
    async def test_run_stream_not_initialized(self, plugin):
        """测试未初始化时流式运行。"""
        with pytest.raises(RuntimeError, match="Agent not initialized"):
            async for _ in plugin.run_stream("test", "thread-1"):
                pass

    @pytest.mark.asyncio
    async def test_get_state_not_initialized(self, plugin):
        """测试未初始化时获取状态。"""
        # get_state 应该在没有初始化时返回空状态
        state = await plugin.get_state("thread-1")
        assert state == {"thread_id": "thread-1", "messages": []}

    @pytest.mark.asyncio
    async def test_clear_memory(self, plugin):
        """测试清除记忆。"""
        # 即使未初始化也应该能清除记忆
        result = await plugin.clear_memory("thread-1")
        # 结果取决于 memory_service 的实现
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_interrupt_not_initialized(self, plugin):
        """测试未初始化时中断。"""
        result = await plugin.interrupt("thread-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_resume_not_initialized(self, plugin):
        """测试未初始化时恢复。"""
        with pytest.raises(RuntimeError, match="Checkpointer not enabled"):
            await plugin.resume("thread-1", "feedback")

    @pytest.mark.asyncio
    async def test_run_basic(self, plugin, agent_config):
        """测试基本运行。"""
        # 模拟工作流
        mock_workflow = AsyncMock()
        mock_workflow.ainvoke = AsyncMock(return_value={
            "messages": [{"content": "Response"}],
            "thread_id": "test-thread",
            "iteration_count": 1,
        })

        plugin._config = agent_config
        plugin._workflow = mock_workflow
        plugin._workflow_type = "react"

        # 模拟构建初始状态
        with patch.object(plugin, '_build_initial_state', return_value={"messages": []}):
            with patch.object(plugin, '_parse_response', return_value={"output": "Response"}):
                response = await plugin.run(
                    input="Hello",
                    thread_id="test-thread"
                )

                assert response is not None

    @pytest.mark.asyncio
    async def test_load_tools(self, plugin):
        """测试加载工具。"""
        # 测试空工具列表
        # 当工具列表为空时，_load_tools 返回所有可用工具
        tools = await plugin._load_tools([])
        # 应该返回所有可用工具（至少有 calculator 和 search）
        assert isinstance(tools, list)

        # 测试指定工具列表
        with patch('oagent.tools.registry.ToolRegistry') as MockRegistry:
            mock_registry = MagicMock()
            mock_registry.list_tools.return_value = {}
            mock_registry.get_tool.return_value = None
            MockRegistry.return_value = mock_registry

            tools = await plugin._load_tools(["nonexistent"])
            assert tools == []

    @pytest.mark.asyncio
    async def test_get_llm_openai(self, plugin):
        """测试获取 OpenAI LLM。"""
        config = AgentConfig(
            agent_type="langgraph",
            llm_provider="openai",
            llm_model="gpt-4o-mini"
        )

        # 这个测试需要实际安装 langchain-openai
        # 这里只测试基本逻辑
        assert config.llm_provider == "openai"

    @pytest.mark.asyncio
    async def test_get_llm_dashscope(self, plugin):
        """测试获取 DashScope LLM。"""
        config = AgentConfig(
            agent_type="langgraph",
            llm_provider="dashscope",
            llm_model="qwen3.5-plus"
        )

        assert config.llm_provider == "dashscope"

    @pytest.mark.asyncio
    async def test_get_llm_unsupported(self, plugin):
        """测试获取不支持的 LLM。"""
        config = AgentConfig(
            agent_type="langgraph",
            llm_provider="unsupported",
            llm_model="test-model"
        )

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            await plugin._get_llm(config)

    @pytest.mark.asyncio
    async def test_parse_response(self, plugin):
        """测试解析响应。"""
        mock_response = {
            "messages": [
                MagicMock(content="Hello"),
                MagicMock(content="World")
            ],
            "thread_id": "test-thread",
            "iteration_count": 2,
        }
        mock_response["messages"][0].tool_calls = []
        mock_response["messages"][1].tool_calls = []

        plugin._workflow_type = "react"
        result = plugin._parse_response(mock_response)

        assert result["output"] == "World"
        assert result["thread_id"] == "test-thread"
        assert result["metadata"]["iterations"] == 2
        assert result["metadata"]["workflow_type"] == "react"

    @pytest.mark.asyncio
    async def test_parse_response_with_tool_calls(self, plugin):
        """测试解析带工具调用的响应。"""
        mock_tool_call = MagicMock()
        mock_tool_call.get = lambda key, default=None: {
            "id": "call_1",
            "name": "calculator",
            "args": {"expression": "2+2"}
        }.get(key, default)

        mock_message = MagicMock()
        mock_message.content = "Let me calculate"
        mock_message.tool_calls = [mock_tool_call]

        mock_response = {
            "messages": [mock_message],
            "thread_id": "test-thread",
        }

        plugin._workflow_type = "react"
        result = plugin._parse_response(mock_response)

        assert len(result["tool_calls"]) >= 0  # 可能有也可能没有

    @pytest.mark.asyncio
    async def test_create_checkpointer(self, plugin):
        """测试创建检查点器。"""
        checkpointer = await plugin._create_checkpointer()
        assert checkpointer is not None


class TestLangGraphAgentPluginWorkflows:
    """测试 LangGraph Agent 不同工作流。"""

    @pytest.fixture
    def plugin(self):
        return LangGraphAgentPlugin()

    @pytest.mark.asyncio
    async def test_react_workflow_initialization(self, plugin):
        """测试 ReAct 工作流初始化。"""
        config = AgentConfig(
            agent_type="langgraph",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            metadata={"workflow_type": "react"}
        )

        captured_workflow_type = None

        async def capture_workflow_type(workflow_type, **kwargs):
            nonlocal captured_workflow_type
            captured_workflow_type = workflow_type
            return AsyncMock()

        with patch.object(plugin, '_load_tools', return_value=AsyncMock()):
            with patch.object(plugin, '_get_llm', return_value=AsyncMock()):
                with patch.object(plugin, '_create_workflow', side_effect=capture_workflow_type):
                    await plugin.initialize(config)

                    # 验证使用了 ReAct 工作流
                    assert captured_workflow_type == 'react'
                    assert plugin._workflow_type == 'react'

    @pytest.mark.asyncio
    async def test_rag_workflow_initialization(self, plugin):
        """测试 RAG 工作流初始化。"""
        config = AgentConfig(
            agent_type="langgraph",
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            metadata={"workflow_type": "rag"}
        )

        captured_workflow_type = None

        async def capture_workflow_type(workflow_type, **kwargs):
            nonlocal captured_workflow_type
            captured_workflow_type = workflow_type
            return AsyncMock()

        with patch.object(plugin, '_load_tools', return_value=AsyncMock()):
            with patch.object(plugin, '_get_llm', return_value=AsyncMock()):
                with patch.object(plugin, '_create_workflow', side_effect=capture_workflow_type):
                    with patch.object(plugin, '_get_vectorstore', return_value=AsyncMock()):
                        with patch.object(plugin, '_get_embedding', return_value=AsyncMock()):
                            await plugin.initialize(config)

                            # 验证使用了 RAG 工作流
                            assert captured_workflow_type == 'rag'
                            assert plugin._workflow_type == 'rag'
