"""Exception hierarchy for Pharos Connect."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


class PharosError(Exception):
    """Base class for all SDK errors."""


class ConfigurationError(PharosError):
    """Raised when client configuration is invalid."""


class TransportError(PharosError):
    """Raised when the HTTP transport cannot complete a request."""


class ResponseDecodeError(PharosError):
    """Raised when Pharos returns a response that cannot be decoded as JSON."""


@dataclass
class APIError(PharosError):
    """Raised for documented Pharos API errors."""

    message: str
    status_code: int
    code: Optional[str] = None
    retry_after: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        code = f" ({self.code})" if self.code else ""
        return f"Pharos API error {self.status_code}{code}: {self.message}"


class AuthenticationError(APIError):
    """Raised for missing or invalid API keys."""


class AuthorizationError(APIError):
    """Raised when the credential is valid but not allowed to access the API."""


class NotFoundError(APIError):
    """Raised when a resource does not exist or is outside the credential scope."""


class RateLimitError(APIError):
    """Raised when the API rate limit is exceeded."""


class InvalidRequestError(APIError):
    """Raised when request parameters are invalid."""


class ServerError(APIError):
    """Raised for unexpected Pharos server errors."""


class WebhookVerificationError(PharosError):
    """Raised when a webhook signature or payload cannot be verified."""


@dataclass
class UnsupportedWebhookEvent(PharosError):
    """Raised when a webhook carries an event type this version does not know.

    The signature and the timestamp were already checked, so the delivery is
    authentic — only its type is unrecognised. **Catch this and answer 2xx**: a
    rejected delivery counts as a failure, and enough consecutive failures
    suspend the endpoint, so treating a new event type as an error would take
    the whole integration down instead of only the part that is new.
    """

    event: str

    def __str__(self) -> str:
        return f"Unsupported Pharos webhook event: {self.event}"
