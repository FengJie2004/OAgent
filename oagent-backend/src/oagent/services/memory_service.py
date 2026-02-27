"""Memory service for conversation history."""

from typing import Dict, List, Optional, Any
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from loguru import logger

from oagent.models.llm import Message


class InMemoryChatMessageHistory(BaseChatMessageHistory):
    """In-memory chat message history for a single conversation."""

    def __init__(self) -> None:
        self._messages: List[BaseMessage] = []

    @property
    def messages(self) -> List[BaseMessage]:
        """List of messages."""
        return self._messages

    def add_message(self, message: BaseMessage) -> None:
        """Add message to history."""
        self._messages.append(message)

    def add_user_message(self, message: str) -> None:
        """Add user message."""
        self.add_message(HumanMessage(content=message))

    def add_ai_message(self, message: str) -> None:
        """Add AI message."""
        self.add_message(AIMessage(content=message))

    def clear(self) -> None:
        """Clear all messages."""
        self._messages = []

    def __len__(self) -> int:
        return len(self._messages)


class MemoryService:
    """Service for managing conversation memory across threads."""

    def __init__(self):
        self._histories: Dict[str, InMemoryChatMessageHistory] = {}
        self._logger = logger

    def get_history(self, thread_id: str) -> InMemoryChatMessageHistory:
        """Get or create chat history for a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            Chat message history for the thread
        """
        if thread_id not in self._histories:
            self._histories[thread_id] = InMemoryChatMessageHistory()
            self._logger.debug(f"Created new chat history for thread: {thread_id}")
        return self._histories[thread_id]

    async def get_messages(self, thread_id: str) -> List[BaseMessage]:
        """Get messages for a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            List of messages
        """
        history = self.get_history(thread_id)
        return history.messages

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str
    ) -> None:
        """Add a message to thread history.

        Args:
            thread_id: Thread identifier
            role: Message role (user/assistant/system)
            content: Message content
        """
        history = self.get_history(thread_id)

        if role == "user":
            history.add_user_message(content)
        elif role == "assistant":
            history.add_ai_message(content)
        elif role == "system":
            history.add_message(SystemMessage(content=content))
        else:
            self._logger.warning(f"Unknown role: {role}")

    async def add_messages(
        self,
        thread_id: str,
        messages: List[Message]
    ) -> None:
        """Add multiple messages to thread history.

        Args:
            thread_id: Thread identifier
            messages: List of messages to add
        """
        for msg in messages:
            await self.add_message(thread_id, msg.role, msg.content)

    async def clear(self, thread_id: str) -> bool:
        """Clear conversation history for a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            True if successful
        """
        if thread_id in self._histories:
            self._histories[thread_id].clear()
            self._logger.info(f"Cleared memory for thread: {thread_id}")
        return True

    async def delete(self, thread_id: str) -> bool:
        """Delete chat history for a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            True if deleted
        """
        if thread_id in self._histories:
            del self._histories[thread_id]
            self._logger.info(f"Deleted memory for thread: {thread_id}")
            return True
        return False

    def list_threads(self) -> List[str]:
        """List all active thread IDs.

        Returns:
            List of thread IDs
        """
        return list(self._histories.keys())
