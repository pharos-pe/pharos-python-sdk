"""Base transport contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

from pharos_sdk.version import __version__

USER_AGENT = f"pharos-sdk/{__version__}"


def build_url(base_url: str, path: str) -> str:
    """Join a base URL and a resource path into an absolute URL.

    Requests are addressed absolutely rather than through httpx's `base_url`,
    so an HTTP client supplied by the caller works without having to repeat our
    base URL on it.
    """
    root = base_url.rstrip("/")
    resource = path.lstrip("/")
    return f"{root}/{resource}"


class BaseTransport(ABC):
    """Common contract implemented by sync and async transports."""

    @abstractmethod
    def headers(self) -> Dict[str, str]:
        """Return request headers including authentication."""
