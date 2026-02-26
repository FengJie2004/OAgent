"""Plugin base classes for OAgent."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class PluginBase(ABC):
    """Base class for all plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name identifier."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass

    @property
    def description(self) -> str:
        """Plugin description."""
        return ""

    @property
    def author(self) -> str:
        """Plugin author."""
        return ""

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize plugin with configuration."""
        pass

    def shutdown(self) -> None:
        """Cleanup plugin resources."""
        pass