"""Tests for API endpoints."""

import pytest
from httpx import AsyncClient


class TestLLMAPI:
    """Tests for LLM API endpoints."""

    @pytest.mark.asyncio
    async def test_get_providers(self, client: AsyncClient):
        """Test getting LLM providers."""
        response = await client.get("/api/v1/llm/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "default" in data

    @pytest.mark.asyncio
    async def test_get_models(self, client: AsyncClient):
        """Test getting models for a provider."""
        response = await client.get("/api/v1/llm/models/openai")
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert "models" in data
        assert data["provider"] == "openai"


class TestConfigAPI:
    """Tests for Config API endpoints."""

    @pytest.mark.asyncio
    async def test_get_config(self, client: AsyncClient):
        """Test getting configuration."""
        response = await client.get("/api/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "app_version" in data


class TestChatAPI:
    """Tests for Chat API endpoints."""

    @pytest.mark.asyncio
    async def test_create_session(self, client: AsyncClient):
        """Test creating a chat session."""
        response = await client.post(
            "/api/v1/chat/sessions",
            json={"title": "Test Session"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Session"

    @pytest.mark.asyncio
    async def test_list_sessions(self, client: AsyncClient):
        """Test listing chat sessions."""
        response = await client.get("/api/v1/chat/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)