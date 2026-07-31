"""Parsers for webhook event schemas."""

from __future__ import annotations

from typing import Dict, Type, cast
from uuid import UUID

from pharos_sdk.exceptions import UnsupportedWebhookEvent
from pharos_sdk.models import (
    DeclarationCorrectedEvent,
    DeclarationDeletedEvent,
    DeclarationIngestedEvent,
    ImporterRef,
    WebhookDeclarationRef,
    WebhookEvent,
)
from pharos_sdk.parsers.importers import parse_importer_ref
from pharos_sdk.parsers.primitives import (
    field_date,
    field_datetime,
    field_int,
    field_object,
    field_string,
    parse_uuid,
    required,
)
from pharos_sdk.types import JSONObject


def parse_webhook_event(payload: JSONObject, *, path: str = "$") -> WebhookEvent:
    """Parse a webhook event payload into the event-specific dataclass."""
    event_name = field_string(payload, key="event", path=path)
    event_id_value = required(payload, key="event_id", path=path)
    event_id_path = f"{path}.event_id"
    event_id = parse_uuid(event_id_value, path=event_id_path)
    declaration_payload = field_object(payload, key="declaration", path=path)
    declaration_path = f"{path}.declaration"
    declaration = parse_webhook_declaration_ref(
        declaration_payload,
        path=declaration_path,
    )
    importer_payload = field_object(payload, key="importer", path=path)
    importer_path = f"{path}.importer"
    importer = parse_importer_ref(importer_payload, path=importer_path)
    extra = cast(
        Dict[str, object],
        {key: value for key, value in payload.items() if key not in BASE_WEBHOOK_KEYS},
    )
    # An event type this version does not know gets its own exception rather
    # than a decoding error, so a handler can tell "Pharos published something
    # new" apart from "this payload is broken" and acknowledge it. Failing the
    # delivery instead would count against the endpoint, and enough consecutive
    # failures suspend it.
    try:
        event_class = EVENT_CLASSES[event_name]
    except LookupError as e:
        raise UnsupportedWebhookEvent(event_name) from e
    else:
        return build_event(
            event_class,
            event_name,
            payload,
            path,
            event_id,
            declaration,
            importer,
            extra,
        )


def parse_webhook_declaration_ref(payload: JSONObject, *, path: str) -> WebhookDeclarationRef:
    """Parse the declaration reference inside a webhook event."""
    return WebhookDeclarationRef(
        full_number=field_string(payload, key="full_number", path=path),
        customs_office_code=field_string(payload, key="customs_office_code", path=path),
        year=field_int(payload, key="year", path=path),
        number=field_int(payload, key="number", path=path),
        numbering_date=field_date(payload, key="numbering_date", path=path),
        items_count=field_int(payload, key="items_count", path=path),
    )


BASE_WEBHOOK_KEYS = {
    "event_id",
    "event",
    "occurred_at",
    "revision",
    "declaration",
    "importer",
    "resource_url",
}
EVENT_CLASSES: Dict[str, Type[WebhookEvent]] = {
    "declaration.ingested": DeclarationIngestedEvent,
    "declaration.corrected": DeclarationCorrectedEvent,
    "declaration.deleted": DeclarationDeletedEvent,
}


def build_event(
    event_class: Type[WebhookEvent],
    event_name: str,
    payload: JSONObject,
    path: str,
    event_id: UUID,
    declaration: WebhookDeclarationRef,
    importer: ImporterRef,
    extra: Dict[str, object],
) -> WebhookEvent:
    """Build a webhook event dataclass from the common webhook fields."""
    return event_class(
        event_id=event_id,
        event=event_name,
        occurred_at=field_datetime(payload, key="occurred_at", path=path),
        revision=field_int(payload, key="revision", path=path),
        declaration=declaration,
        importer=importer,
        resource_url=field_string(payload, key="resource_url", path=path),
        extra=extra,
    )
