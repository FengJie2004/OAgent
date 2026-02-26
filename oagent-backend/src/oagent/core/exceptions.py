"""Custom exceptions for OAgent."""


class OAgentError(Exception):
    """Base exception for OAgent."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class PluginError(OAgentError):
    """Plugin-related errors."""

    pass


class PluginNotFoundError(PluginError):
    """Plugin not found."""

    def __init__(self, plugin_type: str, plugin_name: str):
        super().__init__(
            f"Plugin not found: {plugin_name} of type {plugin_type}"
        )


class PluginRegistrationError(PluginError):
    """Plugin registration failed."""

    def __init__(self, plugin_type: str, plugin_name: str, reason: str):
        super().__init__(
            f"Failed to register plugin {plugin_name} of type {plugin_type}: {reason}"
        )


class ConfigurationError(OAgentError):
    """Configuration-related errors."""

    pass


class ValidationError(OAgentError):
    """Validation-related errors."""

    pass


class LLMError(OAgentError):
    """LLM-related errors."""

    pass


class EmbeddingError(OAgentError):
    """Embedding-related errors."""

    pass


class VectorStoreError(OAgentError):
    """Vector store-related errors."""

    pass


class RAGError(OAgentError):
    """RAG-related errors."""

    pass


class AgentError(OAgentError):
    """Agent-related errors."""

    pass


class ToolError(OAgentError):
    """Tool-related errors."""

    pass


class AuthenticationError(OAgentError):
    """Authentication-related errors."""

    pass


class RateLimitError(OAgentError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message)