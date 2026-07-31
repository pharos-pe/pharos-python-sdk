"""Client configuration for Pharos Connect."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Union

from pharos_sdk.exceptions import ConfigurationError


class AuthScheme(str, Enum):
    """Supported authentication header schemes."""

    BEARER = "bearer"
    API_KEY = "api_key"


AuthSchemeInput = Union[AuthScheme, str]
BASE_URL = "https://app.pharos.pe/api/v1"


@dataclass(frozen=True)
class ClientConfig:
    """Configuration shared by sync and async clients."""

    api_key: str
    base_url: str = BASE_URL
    timeout: float = 10.0
    headers: Dict[str, str] = field(default_factory=dict)
    auth_scheme: AuthScheme = AuthScheme.BEARER

    def auth_headers(self) -> Dict[str, str]:
        """Return authentication headers for the configured scheme."""
        if self.auth_scheme == AuthScheme.BEARER:
            return {"Authorization": f"Bearer {self.api_key}"}
        elif self.auth_scheme == AuthScheme.API_KEY:
            return {"X-Pharos-Key": self.api_key}
        else:
            raise ValueError(f"Unsupported auth scheme: {self.auth_scheme}")


def normalize_auth_scheme(auth_scheme: AuthSchemeInput) -> AuthScheme:
    """Normalize a public auth scheme value into AuthScheme."""
    if isinstance(auth_scheme, AuthScheme):
        return auth_scheme
    try:
        return AuthScheme(auth_scheme)
    except ValueError as e:
        raise ValueError(f"Unsupported auth scheme: {auth_scheme}") from e


def make_config(
    *,
    api_key: str,
    base_url: str,
    timeout: float,
    headers: Optional[Dict[str, str]],
    auth_scheme: AuthSchemeInput,
) -> ClientConfig:
    """Validate client options and return a ClientConfig."""
    if not api_key:
        raise ConfigurationError("api_key is required.")
    try:
        normalized_auth_scheme = normalize_auth_scheme(auth_scheme)
    except ValueError as e:
        raise ConfigurationError("auth_scheme must be 'bearer' or 'api_key'.") from e
    else:
        return ClientConfig(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            headers=headers or {},
            auth_scheme=normalized_auth_scheme,
        )
