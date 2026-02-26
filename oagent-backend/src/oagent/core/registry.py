"""Plugin registry for managing pluggable components."""

from typing import Dict, List, Type, Any, Optional
from loguru import logger


class PluginRegistry:
    """
    Central registry for all plugin types.

    Supports registration and retrieval of:
    - LLM plugins
    - Embedding plugins
    - VectorStore plugins
    - RAG plugins
    - Agent plugins
    - Tool plugins
    """

    _instance: Optional["PluginRegistry"] = None

    # Plugin type definitions
    PLUGIN_TYPES = {
        "llm": "LLM providers",
        "embedding": "Embedding models",
        "vectorstore": "Vector databases",
        "rag": "RAG frameworks",
        "agent": "Agent types",
        "tool": "Tools",
    }

    def __new__(cls) -> "PluginRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins: Dict[str, Dict[str, Type]] = {
                plugin_type: {} for plugin_type in cls.PLUGIN_TYPES
            }
            cls._instance._instances: Dict[str, Dict[str, Any]] = {
                plugin_type: {} for plugin_type in cls.PLUGIN_TYPES
            }
        return cls._instance

    @classmethod
    def get_instance(cls) -> "PluginRegistry":
        """Get singleton instance."""
        return cls()

    def register(
        self,
        plugin_type: str,
        name: str,
        plugin_class: Type,
        force: bool = False
    ) -> None:
        """
        Register a plugin class.

        Args:
            plugin_type: Type of plugin (llm, embedding, vectorstore, etc.)
            name: Unique name for the plugin
            plugin_class: The plugin class to register
            force: Overwrite existing plugin if True

        Raises:
            ValueError: If plugin type is invalid or plugin already exists
        """
        if plugin_type not in self.PLUGIN_TYPES:
            raise ValueError(
                f"Invalid plugin type: {plugin_type}. "
                f"Valid types: {list(self.PLUGIN_TYPES.keys())}"
            )

        if name in self._plugins[plugin_type] and not force:
            raise ValueError(
                f"Plugin '{name}' already registered for type '{plugin_type}'. "
                f"Use force=True to overwrite."
            )

        self._plugins[plugin_type][name] = plugin_class
        logger.info(f"Registered {plugin_type} plugin: {name}")

    def unregister(self, plugin_type: str, name: str) -> bool:
        """
        Unregister a plugin.

        Args:
            plugin_type: Type of plugin
            name: Name of the plugin

        Returns:
            True if plugin was unregistered, False if not found
        """
        if plugin_type not in self._plugins:
            return False

        if name in self._plugins[plugin_type]:
            del self._plugins[plugin_type][name]
            # Also remove cached instance
            if name in self._instances[plugin_type]:
                del self._instances[plugin_type][name]
            logger.info(f"Unregistered {plugin_type} plugin: {name}")
            return True
        return False

    def get(self, plugin_type: str, name: str) -> Type:
        """
        Get a plugin class by type and name.

        Args:
            plugin_type: Type of plugin
            name: Name of the plugin

        Returns:
            The plugin class

        Raises:
            ValueError: If plugin type or name not found
        """
        if plugin_type not in self._plugins:
            raise ValueError(f"Invalid plugin type: {plugin_type}")

        if name not in self._plugins[plugin_type]:
            raise ValueError(
                f"Plugin '{name}' not found for type '{plugin_type}'. "
                f"Available: {list(self._plugins[plugin_type].keys())}"
            )

        return self._plugins[plugin_type][name]

    def get_instance_of(
        self,
        plugin_type: str,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        fresh: bool = False
    ) -> Any:
        """
        Get or create a plugin instance.

        Args:
            plugin_type: Type of plugin
            name: Name of the plugin
            config: Configuration for the plugin
            fresh: Create a new instance even if cached

        Returns:
            Plugin instance
        """
        if fresh or name not in self._instances[plugin_type]:
            plugin_class = self.get(plugin_type, name)
            instance = plugin_class()
            if hasattr(instance, "initialize"):
                instance.initialize(config)
            self._instances[plugin_type][name] = instance

        return self._instances[plugin_type][name]

    def list(self, plugin_type: str) -> Dict[str, Type]:
        """
        List all plugins of a given type.

        Args:
            plugin_type: Type of plugin

        Returns:
            Dictionary of plugin name to class
        """
        if plugin_type not in self._plugins:
            raise ValueError(f"Invalid plugin type: {plugin_type}")
        return self._plugins[plugin_type].copy()

    def list_all(self) -> Dict[str, Dict[str, Type]]:
        """
        List all registered plugins.

        Returns:
            Dictionary of all plugins by type
        """
        return {
            plugin_type: plugins.copy()
            for plugin_type, plugins in self._plugins.items()
        }

    def get_available_plugins(self) -> Dict[str, List[str]]:
        """
        Get list of available plugin names by type.

        Returns:
            Dictionary mapping plugin type to list of plugin names
        """
        return {
            plugin_type: list(plugins.keys())
            for plugin_type, plugins in self._plugins.items()
        }

    def clear(self) -> None:
        """Clear all registered plugins."""
        for plugin_type in self._plugins:
            self._plugins[plugin_type].clear()
            self._instances[plugin_type].clear()
        logger.info("Cleared all plugins from registry")


# Decorator for plugin registration
def register_plugin(plugin_type: str, name: str, force: bool = False):
    """
    Decorator for registering a plugin class.

    Usage:
        @register_plugin("llm", "openai")
        class OpenAILLMPlugin(LLMPluginBase):
            ...

    Args:
        plugin_type: Type of plugin
        name: Unique name for the plugin
        force: Overwrite existing plugin if True
    """
    def decorator(cls: Type) -> Type:
        registry = PluginRegistry()
        registry.register(plugin_type, name, cls, force=force)
        return cls
    return decorator


# Global registry instance
registry = PluginRegistry()