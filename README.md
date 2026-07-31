# pharos-sdk

Official Python SDK for Pharos Connect.

- Documentation: https://pharos.pe/desarrolladores/
- Repository: https://github.com/pharos-pe/pharos-python-sdk

## Installation

```bash
pip install pharos-sdk
```

Supports Python 3.8+.

## API Client

Use the client directly when your application owns a long-lived process.

```python
import os

from pharos_sdk import PharosClient

client = PharosClient(os.environ["PHAROS_API_KEY"])
latest = client.declarations.latest(limit=10)

for summary in latest.data:
    declaration = client.declarations.get(summary.full_number)
    process_declaration(declaration)

client.close()
```

Use a context manager when the client is short-lived.

```python
import os

from pharos_sdk import PharosClient

with PharosClient(os.environ["PHAROS_API_KEY"]) as client:
    importers = client.importers.list()
```

### Sending the key in `X-Pharos-Key`

The key travels in `Authorization: Bearer …` by default. Pharos also accepts it
in `X-Pharos-Key`, which is what to reach for when something between you and the
API takes the `Authorization` header for itself — a corporate proxy or an API
gateway that authenticates you to itself and rewrites it on the way out.

```python
client = PharosClient(os.environ["PHAROS_API_KEY"], auth_scheme="api_key")
```

Both clients take it, and both accept the `AuthScheme` enum if you would rather
not pass a string:

```python
from pharos_sdk import AuthScheme

client = PharosClient(os.environ["PHAROS_API_KEY"], auth_scheme=AuthScheme.API_KEY)
```

Anything other than `"bearer"` or `"api_key"` raises `ConfigurationError` when
the client is built, rather than on the first request.

## Async Client

```python
import os

from pharos_sdk import AsyncPharosClient

client = AsyncPharosClient(os.environ["PHAROS_API_KEY"])
latest = await client.declarations.latest()
await client.close()
```

```python
import os

from pharos_sdk import AsyncPharosClient

async with AsyncPharosClient(os.environ["PHAROS_API_KEY"]) as client:
    importers = await client.importers.list()
```

## Errors

Every SDK exception derives from `PharosError`. Failures that reached the API and
came back with a status derive from `APIError`, which carries `status_code`, the
documented `code`, and the response `headers`.

```python
declaration = client.declarations.get("118-2026-10-001234-00")
```

Catch `NotFoundError` when a missing declaration is part of your normal workflow.
Catch `RateLimitError` or `ServerError` at your job boundary if you want to back
off and retry.

| Exception | Raised when |
|---|---|
| `AuthenticationError` | The key is missing or invalid (401) |
| `AuthorizationError` | Pharos Connect is not enabled for the account, or the source IP is not on the key's allowlist (403) |
| `NotFoundError` | The resource does not exist **or is outside your scope** (404) |
| `RateLimitError` | The hourly request limit was exceeded (429). `retry_after` holds the seconds to wait |
| `InvalidRequestError` | A parameter is not valid (400) |
| `ServerError` | An unexpected failure on the Pharos side, including gateway errors (5xx) |
| `TransportError` | The request never got a response — DNS, TLS, connection or timeout |
| `ResponseDecodeError` | A successful response did not match the published contract |

**The SDK does not retry.** Reads are idempotent, so retrying is safe, but the
policy is yours: catch `RateLimitError` and `ServerError`, and back off using
`retry_after` when it is set.

## Declaration Numbers

Declaration methods accept either the full DUA number as a string or a structured
`DeclarationNumber`.

```python
from pharos_sdk.models import DeclarationNumber

number = DeclarationNumber(
    customs_office="118",
    year=2026,
    regime="10",
    number=1234,
    control_number="00",
)

declaration = client.declarations.get(number)
items = client.declarations.items(number)
```

## Webhooks

```python
import os

from pharos_sdk.webhooks import WebhookVerifier

verifier = WebhookVerifier(os.environ["PHAROS_WEBHOOK_SECRET"])
event = verifier.verify(request_body, signature_header)
handle_event(event)
```

Pass the body **exactly as it arrived**, before any parsing: the signature covers
the raw bytes. `verify` checks the signature and the timestamp — five minutes of
tolerance by default — and raises `WebhookVerificationError` if either fails.

### Form-encoded endpoints

An endpoint can be configured to receive `application/x-www-form-urlencoded`
instead of JSON. Pass the request's `Content-Type` and the verifier reads either:

```python
event = verifier.verify(
    request_body,
    signature_header,
    content_type=request.headers["Content-Type"],
)
```

Nothing is inferred from the body — Pharos always sends the header, so it is the
sender's own statement of which shape it used. Omit the argument and the body is
read as JSON, which is what an endpoint receives unless you asked for the other.
A `Content-Type` that is neither raises `WebhookVerificationError` rather than
being read as a guess.

You get the same event object either way. A form carries no types, so Pharos
sends every value as text and the two objects as text holding JSON; the verifier
undoes exactly that. The one difference is `event.extra`: any additional field
configured for your endpoint stays a string, because the form did not carry its
type either.

An event type newer than your installed SDK raises `UnsupportedWebhookEvent`,
which is deliberately **not** a `WebhookVerificationError`: the delivery is
authentic, only its type is unknown. Catch it and answer 2xx, or repeated
failures will suspend your endpoint.

```python
event = verifier.verify(request_body, signature_header)
handle_event(event)
return http_200()
```

At your webhook boundary, answer `2xx` for `UnsupportedWebhookEvent` only when
your system deliberately ignores event types unknown to this SDK version.

Deduplicate on `event.event_id`. It is the same across retries **and** across
every endpoint subscribed to the same fact, which the delivery id is not.

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy --no-site-packages pharos_sdk
```

`pytest` prints coverage by default.
