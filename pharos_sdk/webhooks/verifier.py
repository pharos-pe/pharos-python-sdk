"""Webhook verification for Pharos Connect."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Dict, Optional, Tuple, Union
from urllib.parse import parse_qsl

from pharos_sdk.exceptions import ResponseDecodeError, WebhookVerificationError
from pharos_sdk.models import WebhookEvent
from pharos_sdk.parsers import parse_webhook_event
from pharos_sdk.types import JSONObject

JSON_CONTENT_TYPE = "application/json"
FORM_CONTENT_TYPE = "application/x-www-form-urlencoded"

# What the form encoding flattened, and all it flattened: the objects Pharos
# sends as JSON text, and the one integer it sends as digits.
FORM_OBJECT_FIELDS = ("declaration", "importer", "validation")
FORM_INTEGER_FIELDS = ("revision",)


class WebhookVerifier:
    """Verify Pharos Connect webhook signatures and parse event payloads."""

    def __init__(self, secret: str, *, tolerance_seconds: int = 300) -> None:
        """Create a verifier for one webhook endpoint signing secret."""
        if not secret:
            raise WebhookVerificationError("Webhook secret is required.")
        elif tolerance_seconds < 0:
            raise WebhookVerificationError("Webhook tolerance must be non-negative.")
        self.secret = secret
        self.tolerance_seconds = tolerance_seconds

    def verify(
        self,
        payload: Union[bytes, str],
        signature: str,
        *,
        content_type: Optional[str] = None,
        now: Optional[int] = None,
    ) -> WebhookEvent:
        """Verify a raw webhook payload and return the parsed event dataclass.

        Pass the `Content-Type` of the request to accept an endpoint configured
        for `application/x-www-form-urlencoded`. There is nothing to infer from
        the body itself: Pharos always sends the header, so it is the sender's
        own statement of which shape it used. Omitted, the body is read as JSON.
        """
        body = payload.encode("utf-8") if isinstance(payload, str) else payload
        timestamp, received_signature = parse_signature_header(signature)
        current_timestamp = int(time.time())
        current_time = current_timestamp if now is None else now
        if abs(current_time - timestamp) > self.tolerance_seconds:
            raise WebhookVerificationError("Webhook timestamp is outside the allowed tolerance.")
        expected_signature = compute_signature(self.secret, body, timestamp)
        if not hmac.compare_digest(expected_signature, received_signature):
            raise WebhookVerificationError("Webhook signature does not match.")
        # Last, and only now: the signature covers the bytes as they arrived, so
        # nothing may reshape them before it has been checked.
        event_payload = decode_webhook_body(body, content_type=content_type)
        try:
            return parse_webhook_event(event_payload)
        except ResponseDecodeError as e:
            message = str(e)
            raise WebhookVerificationError(message) from e


def compute_signature(secret: str, payload: bytes, timestamp: int) -> str:
    """Compute the Pharos webhook HMAC signature."""
    timestamp_bytes = str(timestamp).encode("ascii")
    signed_payload = timestamp_bytes + b"." + payload
    secret_bytes = secret.encode("utf-8")
    digest = hmac.new(secret_bytes, signed_payload, hashlib.sha256)
    return digest.hexdigest()


def parse_signature_header(header: str) -> Tuple[int, str]:
    """Parse `t=<epoch>,v1=<hex>` into timestamp and signature."""
    timestamp: Optional[int] = None
    signature: Optional[str] = None
    for part in header.split(","):
        key, separator, value = part.partition("=")
        if not separator:
            raise WebhookVerificationError("Malformed webhook signature header.")
        if key == "t":
            timestamp = parse_timestamp(value)
        elif key == "v1":
            signature = value
    if timestamp is None or not signature:
        raise WebhookVerificationError("Webhook signature header must include t and v1.")
    else:
        validate_signature_hex(signature)
        return timestamp, signature.lower()


def parse_timestamp(value: str) -> int:
    """Parse a webhook signature timestamp."""
    try:
        return int(value)
    except ValueError as e:
        raise WebhookVerificationError("Malformed webhook timestamp.") from e


def validate_signature_hex(signature: str) -> None:
    """Validate the HMAC hex value from a webhook signature header."""
    hex_chars = "0123456789abcdefABCDEF"
    if len(signature) != 64 or any(char not in hex_chars for char in signature):
        raise WebhookVerificationError("Malformed webhook HMAC.")


def decode_webhook_body(body: bytes, content_type: Optional[str] = None) -> JSONObject:
    """Decode a webhook body according to the content type it arrived with."""
    media_type = base_media_type(content_type)
    if media_type == JSON_CONTENT_TYPE:
        return decode_json_body(body)
    elif media_type == FORM_CONTENT_TYPE:
        return decode_form_body(body)
    else:
        raise WebhookVerificationError(
            f"Unsupported webhook content type: {media_type}. Pharos sends "
            f"{JSON_CONTENT_TYPE} or {FORM_CONTENT_TYPE}."
        )


def base_media_type(content_type: Optional[str]) -> str:
    """The media type without its parameters.

    Frameworks hand over what the request carried, which is usually something
    like `application/json; charset=utf-8`.
    """
    if content_type is None:
        return JSON_CONTENT_TYPE
    else:
        return content_type.split(";")[0].strip().lower()


def decode_json_body(body: bytes) -> JSONObject:
    """Decode a webhook body as a JSON object."""
    try:
        body_text = body.decode("utf-8")
        decoded = json.loads(body_text)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise WebhookVerificationError("Webhook payload is not valid JSON.") from e
    else:
        if not isinstance(decoded, dict):
            raise WebhookVerificationError("Webhook payload must be a JSON object.")
        else:
            return decoded


def decode_form_body(body: bytes) -> JSONObject:
    """Decode a form-encoded webhook body into the shape the parsers expect.

    A form carries no types, so Pharos sends every value as text and the two
    objects as text holding JSON. This undoes exactly that, and nothing more:
    the fields below are the ones the contract defines, and any extra field
    configured for the endpoint stays a string, because the form did not carry
    its type either.
    """
    try:
        body_text = body.decode("utf-8")
    except UnicodeDecodeError as e:
        raise WebhookVerificationError("Webhook payload is not valid UTF-8.") from e

    # `parse_qsl` yields text and only text, so the decoding below is the
    # only place a form field stops being a string.
    text_fields: Dict[str, str] = dict(parse_qsl(body_text, keep_blank_values=True))
    fields: JSONObject = dict(text_fields)
    for key in FORM_OBJECT_FIELDS:
        if key in text_fields:
            fields[key] = decode_form_object(text_fields[key], key=key)
    for key in FORM_INTEGER_FIELDS:
        if key in text_fields:
            fields[key] = decode_form_integer(text_fields[key], key=key)
    return fields


def decode_form_object(value: str, key: str) -> JSONObject:
    """Read one of the JSON objects a form-encoded body carries as text."""
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as e:
        raise WebhookVerificationError(f"Webhook field {key} is not valid JSON.") from e
    else:
        if not isinstance(decoded, dict):
            raise WebhookVerificationError(f"Webhook field {key} must be a JSON object.")
        else:
            return decoded


def decode_form_integer(value: str, key: str) -> int:
    """Read one of the integers a form-encoded body carries as text."""
    try:
        return int(value)
    except ValueError as e:
        raise WebhookVerificationError(f"Webhook field {key} is not a whole number.") from e
