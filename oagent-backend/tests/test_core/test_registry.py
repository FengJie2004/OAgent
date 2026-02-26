"""Tests for Plugin Registry."""

import pytest

from oagent.core.registry import PluginRegistry, register_plugin
from oagent.core.plugin_base import PluginBase


class MockPlugin(PluginBase):
    """Mock plugin for testing."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def version(self) -> str:
        return "1.0.0"


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_singleton(self):
        """Test that registry is a singleton."""
        registry1 = PluginRegistry()
        registry2 = PluginRegistry()
        assert registry1 is registry2

    def test_register_plugin(self):
        """Test plugin registration."""
        registry = PluginRegistry()
        registry._plugins["llm"] = {}  # Clear for test

        registry.register("llm", "mock", MockPlugin)

        assert "mock" in registry._plugins["llm"]
        assert registry._plugins["llm"]["mock"] is MockPlugin

    def test_register_invalid_type(self):
        """Test registration with invalid type."""
        registry = PluginRegistry()

        with pytest.raises(ValueError):
            registry.register("invalid_type", "mock", MockPlugin)

    def test_get_plugin(self):
        """Test getting a plugin."""
        registry = PluginRegistry()
        registry._plugins["llm"]["mock"] = MockPlugin

        plugin_class = registry.get("llm", "mock")
        assert plugin_class is MockPlugin

    def test_get_nonexistent_plugin(self):
        """Test getting a nonexistent plugin."""
        registry = PluginRegistry()

        with pytest.raises(ValueError):
            registry.get("llm", "nonexistent")

    def test_list_plugins(self):
        """Test listing plugins."""
        registry = PluginRegistry()
        registry._plugins["llm"] = {"mock": MockPlugin}

        plugins = registry.list("llm")
        assert "mock" in plugins
        assert plugins["mock"] is MockPlugin

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        registry = PluginRegistry()
        registry._plugins["llm"]["mock"] = MockPlugin

        result = registry.unregister("llm", "mock")
        assert result is True
        assert "mock" not in registry._plugins["llm"]