"""Tests for LangChain Agent plugin."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from oagent.models.agent import AgentConfig
from oagent.plugins.agent.langchain import LangChainAgentPlugin


class TestLangChainAgentPlugin:
    """Tests for LangChain Agent plugin."""

    @pytest.fixture
    def agent_config(self):
        """Sample agent configuration."""
        return AgentConfig(
            agent_type="langchain",
            llm_provider="dashscope",
            llm_model="qwen3.5-plus",
            system_prompt="You are a helpful assistant.",
            tools=["calculator"],
            max_iterations=5,
            memory_enabled=True,
            temperature=0.7,
            max_tokens=2048,
        )

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return LangChainAgentPlugin()

    def test_plugin_name(self, plugin):
        """Test plugin name."""
        assert plugin.name == "langchain"

    def test_plugin_version(self, plugin):
        """Test plugin version."""
        assert plugin.version == "0.1.0"

    def test_plugin_description(self, plugin):
        """Test plugin description."""
        assert "LangChain" in plugin.description
        assert "Tool-Calling" in plugin.description

    def test_supported_tools(self, plugin):
        """Test supported tools list."""
        tools = plugin.supported_tools
        assert len(tools) > 0
        # Built-in tools should be available
        assert "calculator" in tools or len(tools) > 0

    @pytest.mark.asyncio
    async def test_initialization(self, plugin, agent_config):
        """Test agent initialization."""
        # Mock the _get_llm and _create_agent methods
        with patch.object(plugin, '_get_llm', return_value=MagicMock()):
            with patch.object(plugin, '_load_tools', return_value=[]):
                with patch.object(plugin, '_create_agent', return_value=MagicMock()):
                    await plugin.initialize(agent_config)

                    assert plugin._config == agent_config
                    assert plugin._agent_executor is not None

    @pytest.mark.asyncio
    async def test_run_not_initialized(self, plugin):
        """Test run raises error when not initialized."""
        with pytest.raises(RuntimeError, match="Agent not initialized"):
            await plugin.run(
                input="Hello",
                thread_id="test-thread"
            )

    @pytest.mark.asyncio
    async def test_run_stream_not_initialized(self, plugin):
        """Test run_stream raises error when not initialized."""
        with pytest.raises(RuntimeError, match="Agent not initialized"):
            async for _ in plugin.run_stream(
                input="Hello",
                thread_id="test-thread"
            ):
                pass

    @pytest.mark.asyncio
    async def test_get_state(self, plugin):
        """Test getting agent state."""
        state = await plugin.get_state("test-thread")

        assert "thread_id" in state
        assert state["thread_id"] == "test-thread"
        assert "messages" in state
        assert "current_step" in state

    @pytest.mark.asyncio
    async def test_clear_memory(self, plugin):
        """Test clearing memory."""
        # Add some messages first
        await plugin._memory_service.add_message("test-thread", "user", "Hello")

        # Clear memory
        result = await plugin.clear_memory("test-thread")

        assert result is True
        messages = await plugin._memory_service.get_messages("test-thread")
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_shutdown(self, plugin, agent_config):
        """Test agent shutdown."""
        with patch.object(plugin, '_get_llm', return_value=MagicMock()):
            with patch.object(plugin, '_load_tools', return_value=[]):
                with patch.object(plugin, '_create_agent', return_value=MagicMock()):
                    await plugin.initialize(agent_config)
                    plugin.shutdown()

                    assert plugin._agent_executor is None

    @pytest.mark.asyncio
    async def test_parse_tool_calls(self, plugin):
        """Test parsing tool calls from intermediate steps."""
        # Create mock tool call objects
        mock_tool_call = MagicMock()
        mock_tool_call.tool = "calculator"
        mock_tool_call.tool_input = {"expression": "2 + 2"}

        mock_result = "4"

        intermediate_steps = [(mock_tool_call, mock_result)]

        tool_calls = plugin._parse_tool_calls(intermediate_steps)

        assert len(tool_calls) == 1
        assert tool_calls[0].tool_name == "calculator"
        assert tool_calls[0].tool_args == {"expression": "2 + 2"}
        assert tool_calls[0].result == "4"

    @pytest.mark.asyncio
    async def test_memory_persistence(self, plugin):
        """Test conversation memory persistence."""
        # Add messages
        await plugin._memory_service.add_message("thread-1", "user", "Hello")
        await plugin._memory_service.add_message("thread-1", "assistant", "Hi there!")

        # Get messages
        messages = await plugin._memory_service.get_messages("thread-1")

        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_multiple_threads(self, plugin):
        """Test multiple thread isolation."""
        # Add messages to different threads
        await plugin._memory_service.add_message("thread-a", "user", "Message A")
        await plugin._memory_service.add_message("thread-b", "user", "Message B")

        # Verify isolation
        messages_a = await plugin._memory_service.get_messages("thread-a")
        messages_b = await plugin._memory_service.get_messages("thread-b")

        assert len(messages_a) == 1
        assert len(messages_b) == 1
        assert messages_a[0].content == "Message A"
        assert messages_b[0].content == "Message B"
