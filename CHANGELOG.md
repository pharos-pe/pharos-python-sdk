# Changelog

## 0.1.0 - 2026-08-02

- Initial Pharos Connect SDK with sync and async clients.
- Add dataclass response models and explicit parsers for the OpenAPI contract.
- Add webhook signature verification and event parsing. An unrecognised event
  type raises `UnsupportedWebhookEvent`, separate from
  `WebhookVerificationError`, so a handler can tell a new event apart from a
  bad delivery and acknowledge it: a rejected delivery counts as a failure, and
  enough of those suspend the endpoint.
- Accept a webhook body in either shape the platform delivers: pass the
  request's `Content-Type` to `verify` and a form-encoded endpoint is read
  as readily as a JSON one, producing the same event object.
- Send the API key as `Authorization: Bearer` or, with
  `auth_scheme="api_key"`, as `X-Pharos-Key`, for callers behind a proxy
  that claims the `Authorization` header.
- Ship inline type information (PEP 561).
- Map every error response to `APIError`, including gateway pages and empty
  bodies that never reached the API.
- Address requests absolutely, so a caller-supplied `httpx` client works without
  repeating the base URL.
- Identify the SDK with a `User-Agent` of `pharos-sdk/<version>`.
