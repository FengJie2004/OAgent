"""Configuration management using Pydantic Settings."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "OAgent"
    app_version: str = "0.1.0"
    debug: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Security
    secret_key: str = Field(default="change-me-in-production", alias="OAGENT_SECRET")
    api_keys: Optional[str] = Field(
        default=None,
        alias="OAGENT_API_KEYS"
    )

    @property
    def api_keys_list(self) -> List[str]:
        """Get API keys as a list."""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(',')]

    # LLM Providers
    # DashScope (阿里百炼) - 默认使用
    dashscope_api_key: Optional[str] = Field(default=None, alias="DASHSCOPE_API_KEY")
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="DASHSCOPE_BASE_URL"
    )
    dashscope_chat_model: str = Field(
        default="qwen3.5-plus",
        alias="DASHSCOPE_CHAT_MODEL"
    )
    dashscope_embedding_model: str = Field(
        default="text-embedding-v4",
        alias="DASHSCOPE_EMBEDDING_MODEL"
    )

    # OpenAI (可选)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")

    # Anthropic (可选)
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")

    # Google (可选)
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")

    # Ollama (本地)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL"
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/oagent.db",
        alias="DATABASE_URL"
    )

    # Vector Store
    vector_store_type: str = Field(default="chroma", alias="VECTOR_STORE_TYPE")
    vector_store_path: str = Field(
        default="./data/chroma",
        alias="VECTOR_STORE_PATH"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, alias="LOG_FILE")

    # Default configurations
    default_llm_provider: str = "dashscope"
    default_llm_model: str = "qwen3.5-plus"
    default_embedding_provider: str = "dashscope"
    default_embedding_model: str = "text-embedding-v4"
    default_temperature: float = 0.7
    default_max_tokens: int = 2048

    # Agent defaults
    default_agent_type: str = "langchain"
    default_max_iterations: int = 10

    def is_api_key_valid(self, key: str) -> bool:
        """Check if the provided API key is valid."""
        valid_keys = self.api_keys_list
        if not valid_keys:
            return True  # No API keys configured, allow all
        return key in valid_keys


# Global settings instance
settings = Settings()