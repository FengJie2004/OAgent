"""LangChain Agent plugin implementation."""

from typing import AsyncIterator, Dict, List, Optional, Any
from loguru import logger

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from oagent.core.registry import register_plugin
from oagent.config.settings import settings
from oagent.models.agent import AgentConfig, ToolCall
from oagent.models.llm import Message
from oagent.plugins.agent.base import AgentPluginBase
from oagent.services.memory_service import MemoryService
from oagent.tools.registry import ToolRegistry


@register_plugin("agent", "langchain")
class LangChainAgentPlugin(AgentPluginBase):
    """LangChain Agent using create_tool_calling_agent.

    Features:
    - Tool calling with LangChain tools
    - Conversation memory support
    - Multi-LLM provider support (DashScope, OpenAI, Ollama, Anthropic)
    - Streaming response support
    """

    def __init__(self):
        self._config: Optional[AgentConfig] = None
        self._agent_executor: Optional[Any] = None
        self._memory_service: MemoryService = MemoryService()
        self._tools: List[Any] = []
        self._logger = logger

    @property
    def name(self) -> str:
        return "langchain"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "LangChain Tool-Calling Agent with memory support"

    @property
    def supported_tools(self) -> List[str]:
        registry = ToolRegistry()
        return registry.get_tool_names()

    async def initialize(self, config: AgentConfig) -> None:
        """Initialize LangChain agent with LLM and tools.

        Args:
            config: Agent configuration
        """
        self._config = config
        self._logger.info(f"Initializing LangChain agent: {config.agent_type}")

        # Get LLM instance
        llm = await self._get_llm(config)

        # Load tools
        self._tools = await self._load_tools(config.tools)

        # Create agent using LangChain v1.0 pattern
        agent = await self._create_agent(llm, config)

        self._agent_executor = agent
        self._logger.info("LangChain agent initialized successfully")

    async def _get_llm(self, config: AgentConfig):
        """Get LLM instance based on configuration."""
        # Import LangChain LLM classes
        from langchain_openai import ChatOpenAI
        from langchain_anthropic import ChatAnthropic
        from langchain_ollama import ChatOllama

        provider = config.llm_provider.lower()
        model = config.llm_model
        temperature = config.temperature
        max_tokens = config.max_tokens

        self._logger.info(f"Creating LLM: provider={provider}, model={model}")

        if provider == "openai":
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=True,
            )

        elif provider == "dashscope":
            # Use OpenAI-compatible interface for DashScope
            return ChatOpenAI(
                model=model,
                api_key=settings.dashscope_api_key,
                base_url=settings.dashscope_base_url,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=True,
            )

        elif provider == "ollama":
            return ChatOllama(
                model=model,
                base_url=settings.ollama_base_url,
                temperature=temperature,
                num_predict=max_tokens,
            )

        elif provider == "anthropic":
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    async def _load_tools(self, tool_names: List[str]) -> List[Any]:
        """Load tools from registry.

        Args:
            tool_names: List of tool names to load

        Returns:
            List of LangChain BaseTool instances
        """
        registry = ToolRegistry()

        if not tool_names:
            # Load all available tools if none specified
            return list(registry.list_tools().values())

        tools = registry.get_tools(tool_names)
        self._logger.info(f"Loaded {len(tools)} tools: {tool_names}")
        return tools

    async def _create_agent(self, llm, config: AgentConfig) -> Any:
        """Create LangChain agent executor.

        Args:
            llm: LangChain LLM instance
            config: Agent configuration

        Returns:
            AgentExecutor instance
        """
        from langchain.agents import create_tool_calling_agent, AgentExecutor
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        # Create system prompt
        system_message = config.system_prompt or (
            "You are a helpful AI assistant. "
            "Use the available tools to help answer user questions. "
            "If you don't have access to a tool that would be helpful, "
            "let the user know what you can do."
        )

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create tool-calling agent
        agent = create_tool_calling_agent(
            llm=llm,
            tools=self._tools,
            prompt=prompt,
        )

        # Create executor with memory options
        executor = AgentExecutor(
            agent=agent,
            tools=self._tools,
            max_iterations=config.max_iterations,
            verbose=settings.debug,  # Only verbose in debug mode
            handle_parsing_errors=True,
        )

        return executor

    async def run(
        self,
        input: str,
        thread_id: str,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Run agent and return response.

        Args:
            input: User input
            thread_id: Conversation thread ID
            stream: Whether to stream response

        Returns:
            Agent response with output, tool calls, and metadata

        Raises:
            RuntimeError: If agent not initialized
            ValueError: If input is invalid
        """
        if not self._agent_executor:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        # Input validation
        if not input or not input.strip():
            raise ValueError("Input cannot be empty")
        if len(input) > 10000:  # Prevent massive input attacks
            raise ValueError("Input too long (max 10000 characters)")

        self._logger.info(f"Running agent for thread {thread_id}")

        try:
            # Get chat history
            chat_history = await self._memory_service.get_messages(thread_id)

            # Run agent
            response = await self._agent_executor.ainvoke({
                "input": input,
                "chat_history": chat_history
            })

            # Extract output
            output = response.get("output", "")

            # Parse tool calls from intermediate steps
            intermediate_steps = response.get("intermediate_steps", [])
            tool_calls = self._parse_tool_calls(intermediate_steps)

            # Store messages in memory
            await self._memory_service.add_message(thread_id, "user", input)
            await self._memory_service.add_message(thread_id, "assistant", output)

            return {
                "output": output,
                "thread_id": thread_id,
                "tool_calls": [tc.model_dump() for tc in tool_calls],
                "intermediate_steps": len(intermediate_steps),
                "memory_enabled": self._config.memory_enabled if self._config else False,
            }

        except ValueError as e:
            # User input error - re-raise as-is
            self._logger.warning(f"Invalid input: {e}")
            raise
        except TimeoutError as e:
            # Timeout error
            self._logger.error(f"Agent execution timeout: {e}")
            raise RuntimeError(f"Request timed out. Please try again.") from e
        except Exception as e:
            # Internal error - log details, raise sanitized message
            self._logger.error(f"Agent execution failed: {e}", exc_info=True)
            raise RuntimeError("An internal error occurred. Please try again later.") from e

    async def run_stream(
        self,
        input: str,
        thread_id: str
    ) -> AsyncIterator[str]:
        """Stream agent response tokens.

        Args:
            input: User input
            thread_id: Conversation thread ID

        Yields:
            Tokens from agent response

        Raises:
            RuntimeError: If agent not initialized
        """
        if not self._agent_executor:
            raise RuntimeError("Agent not initialized.")

        # Input validation
        if not input or not input.strip():
            raise ValueError("Input cannot be empty")
        if len(input) > 10000:
            raise ValueError("Input too long (max 10000 characters)")

        chat_history = await self._memory_service.get_messages(thread_id)

        # Use LangChain's astream_events for streaming
        try:
            async for event in self._agent_executor.astream_events(
                {"input": input, "chat_history": chat_history},
                version="v2"
            ):
                event_type = event.get("event")

                # Yield tokens from LLM streaming
                if event_type == "on_llm_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content"):
                        token = chunk.content
                        if token:
                            yield token
        except Exception as e:
            self._logger.error(f"Streaming failed: {e}", exc_info=True)
            raise

    async def get_state(self, thread_id: str) -> Dict[str, Any]:
        """Get agent state for a thread.

        Args:
            thread_id: Thread ID

        Returns:
            Current agent state
        """
        messages = await self._memory_service.get_messages(thread_id)

        # Convert LangChain messages to internal format
        internal_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                internal_messages.append(Message(role="user", content=msg.content))
            elif isinstance(msg, AIMessage):
                internal_messages.append(Message(role="assistant", content=msg.content))
            elif isinstance(msg, SystemMessage):
                internal_messages.append(Message(role="system", content=msg.content))

        return {
            "thread_id": thread_id,
            "messages": [m.model_dump() for m in internal_messages],
            "current_step": "idle",
            "metadata": {
                "message_count": len(internal_messages),
            }
        }

    async def clear_memory(self, thread_id: str) -> bool:
        """Clear conversation memory for a thread.

        Args:
            thread_id: Thread ID

        Returns:
            True if successful
        """
        return await self._memory_service.clear(thread_id)

    def _parse_tool_calls(self, intermediate_steps: List) -> List[ToolCall]:
        """Parse tool calls from agent intermediate steps.

        Args:
            intermediate_steps: List of (tool_call, result) tuples

        Returns:
            List of ToolCall objects
        """
        tool_calls = []

        for step in intermediate_steps:
            if len(step) >= 2:
                tool_call, result = step[0], step[1]

                # Extract tool call information
                tool_name = getattr(tool_call, 'tool', 'unknown')
                tool_args = getattr(tool_call, 'tool_input', {})

                tool_calls.append(
                    ToolCall(
                        tool_name=tool_name,
                        tool_args=tool_args if isinstance(tool_args, dict) else {},
                        result=str(result) if result else None
                    )
                )

        return tool_calls

    def shutdown(self) -> None:
        """Cleanup agent resources."""
        self._logger.info("Shutting down LangChain agent")
        self._agent_executor = None
        self._tools = []
