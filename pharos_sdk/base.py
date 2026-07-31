"""Base client contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseClient(ABC):
    """Common contract shared by sync and async clients."""

    @abstractmethod
    def is_closed(self) -> bool:
        """Return whether the underlying SDK-owned transport is closed."""
