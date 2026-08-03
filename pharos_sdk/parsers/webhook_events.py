"""Parsers for webhook event schemas."""

from __future__ import annotations

from typing import Callable, Dict, Tuple, Type, cast
from uuid import UUID

from pharos_sdk.exceptions import UnsupportedWebhookEvent
from pharos_sdk.models import (
    DeclarationCorrectedEvent,
    DeclarationDeletedEvent,
    DeclarationIngestedEvent,
    DeclarationValidationCompletedEvent,
    ImporterRef,
    SeverityCounts,
    ValidationEvidence,
    ValidationFinding,
    ValidationOccurrence,
    ValidationResult,
    WebhookDeclarationRef,
    WebhookEvent,
)
from pharos_sdk.parsers.importers import parse_importer_ref
from pharos_sdk.parsers.primitives import (
    absent_or,
    as_object,
    boolean,
    field_date,
    field_datetime,
    field_int,
    field_object,
    field_optional_int,
    field_string,
    integer,
    parse_datetime,
    parse_tuple,
    parse_uuid,
    required,
    string,
)
from pharos_sdk.types import JSONObject, JSONValue

EventBuilder = Callable[
    [
        Type[WebhookEvent],
        str,
        JSONObject,
        str,
        UUID,
        WebhookDeclarationRef,
        ImporterRef,
        Dict[str, object],
    ],
    WebhookEvent,
]


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
        build = EVENT_BUILDERS[event_name]
        return build(
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


EVIDENCE_KEYS = {
    "identifier_type",
    "identifier_value",
    "match_scope",
    "occurrence_count",
    "item_numbers",
    "item_numbers_truncated",
    "occurrences",
    "occurrences_truncated",
}


def parse_item_number(value: JSONValue, path: str) -> int:
    """Parse one item number from an evidence list."""
    return integer(value, path=path)


def parse_validation_occurrence(value: JSONValue, path: str) -> ValidationOccurrence:
    """Parse one place an identifier was also recorded."""
    payload = as_object(value, path=path)
    return ValidationOccurrence(
        match_scope=field_string(payload, key="match_scope", path=path),
        numbering_date=field_date(payload, key="numbering_date", path=path),
        declaration_full_number=absent_or(
            payload, "declaration_full_number", string, path=path),
        item_number=absent_or(payload, "item_number", integer, path=path),
        customs_office_code=absent_or(payload, "customs_office_code", string, path=path),
    )


def parse_validation_evidence(payload: JSONObject, *, path: str) -> ValidationEvidence:
    """Parse the evidence of one finding, whose keys depend on the rule."""
    item_numbers_path = f"{path}.item_numbers"
    item_numbers: Tuple[int, ...] = ()
    if "item_numbers" in payload:
        item_numbers = parse_tuple(
            payload["item_numbers"],
            parser=parse_item_number,
            path=item_numbers_path,
        )
    occurrences_path = f"{path}.occurrences"
    occurrences: Tuple[ValidationOccurrence, ...] = ()
    if "occurrences" in payload:
        occurrences = parse_tuple(
            payload["occurrences"],
            parser=parse_validation_occurrence,
            path=occurrences_path,
        )
    extra = cast(
        Dict[str, object],
        {key: value for key, value in payload.items() if key not in EVIDENCE_KEYS},
    )
    return ValidationEvidence(
        identifier_type=absent_or(payload, "identifier_type", string, path=path),
        identifier_value=absent_or(payload, "identifier_value", string, path=path),
        match_scope=absent_or(payload, "match_scope", string, path=path),
        occurrence_count=absent_or(payload, "occurrence_count", integer, path=path),
        item_numbers=item_numbers,
        item_numbers_truncated=absent_or(
            payload, "item_numbers_truncated", boolean, path=path),
        occurrences=occurrences,
        occurrences_truncated=absent_or(
            payload, "occurrences_truncated", boolean, path=path),
        extra=extra,
    )


def parse_validation_finding(value: JSONValue, path: str) -> ValidationFinding:
    """Parse one finding of a validation result."""
    payload = as_object(value, path=path)
    evidence_payload = field_object(payload, key="evidence", path=path)
    evidence_path = f"{path}.evidence"
    return ValidationFinding(
        rule_code=field_string(payload, key="rule_code", path=path),
        rule_version=field_int(payload, key="rule_version", path=path),
        category=field_string(payload, key="category", path=path),
        severity=field_string(payload, key="severity", path=path),
        scope=field_string(payload, key="scope", path=path),
        item_number=field_optional_int(payload, key="item_number", path=path),
        message=field_string(payload, key="message", path=path),
        evidence=parse_validation_evidence(evidence_payload, path=evidence_path),
    )


def parse_severity_counts(payload: JSONObject, *, path: str) -> SeverityCounts:
    """Parse the per-severity tally of a validation result."""
    return SeverityCounts(
        critical=field_int(payload, key="critical", path=path),
        high=field_int(payload, key="high", path=path),
        medium=field_int(payload, key="medium", path=path),
        low=field_int(payload, key="low", path=path),
    )


def parse_validation_result(payload: JSONObject, *, path: str) -> ValidationResult:
    """Parse the aggregated result carried by a validation event."""
    counts_payload = field_object(payload, key="severity_counts", path=path)
    counts_path = f"{path}.severity_counts"
    findings_value = required(payload, key="findings", path=path)
    findings_path = f"{path}.findings"
    evaluated_at_value = required(payload, key="evaluated_at", path=path)
    evaluated_at_path = f"{path}.evaluated_at"
    if evaluated_at_value is None:
        evaluated_at = None
    else:
        evaluated_at = parse_datetime(evaluated_at_value, path=evaluated_at_path)
    return ValidationResult(
        status=field_string(payload, key="status", path=path),
        rules_evaluated_count=field_int(payload, key="rules_evaluated_count", path=path),
        findings_count=field_int(payload, key="findings_count", path=path),
        severity_counts=parse_severity_counts(counts_payload, path=counts_path),
        findings=parse_tuple(findings_value, parser=parse_validation_finding, path=findings_path),
        evaluated_at=evaluated_at,
    )


BASE_WEBHOOK_KEYS = {
    "event_id",
    "event",
    "occurred_at",
    "revision",
    "declaration",
    "importer",
    "resource_url",
    # Parsed onto its own field, so it must not also arrive raw in `extra`.
    "validation",
}
EVENT_CLASSES: Dict[str, Type[WebhookEvent]] = {
    "declaration.ingested": DeclarationIngestedEvent,
    "declaration.corrected": DeclarationCorrectedEvent,
    "declaration.deleted": DeclarationDeletedEvent,
    "declaration.validation_completed": DeclarationValidationCompletedEvent,
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


def build_validation_completed_event(
    event_class: Type[WebhookEvent],
    event_name: str,
    payload: JSONObject,
    path: str,
    event_id: UUID,
    declaration: WebhookDeclarationRef,
    importer: ImporterRef,
    extra: Dict[str, object],
) -> WebhookEvent:
    """Build a validation event, whose result is a field of its own."""
    validation_payload = field_object(payload, key="validation", path=path)
    validation_path = f"{path}.validation"
    return DeclarationValidationCompletedEvent(
        event_id=event_id,
        event=event_name,
        occurred_at=field_datetime(payload, key="occurred_at", path=path),
        revision=field_int(payload, key="revision", path=path),
        declaration=declaration,
        importer=importer,
        resource_url=field_string(payload, key="resource_url", path=path),
        extra=extra,
        validation=parse_validation_result(validation_payload, path=validation_path),
    )


EVENT_BUILDERS: Dict[str, EventBuilder] = {
    "declaration.ingested": build_event,
    "declaration.corrected": build_event,
    "declaration.deleted": build_event,
    "declaration.validation_completed": build_validation_completed_event,
}

assert EVENT_CLASSES.keys() == EVENT_BUILDERS.keys()
