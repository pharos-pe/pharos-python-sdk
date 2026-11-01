# Changelog

## 0.3.0 - Unreleased

- Look a vehicle up by exact VIN or engine number with
  `client.vehicles.find(vin=...)` or `find(engine_number=...)`, on both
  clients. It needs a key Pharos has enabled for it; any other key raises
  `AuthorizationError`.
- Read each match as a `VehicleMatch`: the vehicle, the declaration and item it
  came from, and `in_scope`, whether that declaration belongs to your
  companies. The result's `scope` says whether the search covered only your
  companies or all of them.

## 0.2.0 - 2026-08-03

- Parse `declaration.validation_completed` into `DeclarationValidationCompletedEvent`,
  with the result typed as `ValidationResult`, `ValidationFinding`,
  `ValidationEvidence`, `ValidationOccurrence` and `SeverityCounts`.
- Read the evidence of a finding without assuming its shape: which keys a rule
  writes depends on the rule, and one this version does not document arrives in
  `evidence.extra` rather than being dropped.
- Accept the validation result over a form-encoded endpoint, where the whole
  block travels as one JSON string.

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
