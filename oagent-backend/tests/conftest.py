"""Test configuration and fixtures."""

import pytest
from typing import Generator

import pytest_asyncio


@pytest.fixture
def app():
    """Create test application."""
    from oagent.main import create_app
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    """Create async test client."""
    from httpx import AsyncClient

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac