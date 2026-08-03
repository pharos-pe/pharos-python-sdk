from __future__ import annotations

import hashlib
import hmac
import json
from typing import List, cast
from urllib.parse import urlencode

import pytest

from pharos_sdk.exceptions import UnsupportedWebhookEvent, WebhookVerificationError
from pharos_sdk.models import DeclarationIngestedEvent, DeclarationValidationCompletedEvent
from pharos_sdk.types import JSONObject
from pharos_sdk.webhooks import WebhookVerifier
from pharos_sdk.webhooks.verifier import decode_webhook_body, parse_signature_header
from tests.fixtures import validation_webhook_payload, webhook_payload


def signed_header(secret: str, body: bytes, timestamp: int) -> str:
    material = str(timestamp).encode("ascii") + b"." + body
    digest = hmac.new(secret.encode("utf-8"), material, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def test_webhook_verifier_validates_signature_and_parses_event() -> None:
    payload = webhook_payload()
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = signed_header(
        secret="whsec_test",
        body=body,
        timestamp=1000,
    )
    verifier = WebhookVerifier(secret="whsec_test")

    event = verifier.verify(
        body,
        header,
        now=1000,
    )

    assert isinstance(event, DeclarationIngestedEvent)
    assert event.event == "declaration.ingested"
    assert event.extra == {"client_reference": "abc"}


def test_webhook_verifier_rejects_bad_signature() -> None:
    payload = webhook_payload()
    body = json.dumps(payload).encode("utf-8")
    header = signed_header(
        secret="whsec_test",
        body=body,
        timestamp=1000,
    )
    verifier = WebhookVerifier(secret="whsec_other")

    with pytest.raises(WebhookVerificationError):
        verifier.verify(
            body,
            header,
            now=1000,
        )


def test_webhook_verifier_rejects_expired_timestamp() -> None:
    payload = webhook_payload()
    body = json.dumps(payload).encode("utf-8")
    header = signed_header(
        secret="whsec_test",
        body=body,
        timestamp=1000,
    )
    verifier = WebhookVerifier(secret="whsec_test", tolerance_seconds=300)

    with pytest.raises(WebhookVerificationError):
        verifier.verify(
            body,
            header,
            now=2000,
        )


def test_webhook_verifier_rejects_malformed_header() -> None:
    payload = webhook_payload()
    body = json.dumps(payload).encode("utf-8")
    signature = "t=1000"
    verifier = WebhookVerifier(secret="whsec_test")

    with pytest.raises(WebhookVerificationError):
        verifier.verify(
            body,
            signature,
            now=1000,
        )


def test_webhook_verifier_rejects_invalid_options() -> None:
    with pytest.raises(WebhookVerificationError, match="secret"):
        WebhookVerifier(secret="")

    with pytest.raises(WebhookVerificationError, match="non-negative"):
        WebhookVerifier(secret="whsec_test", tolerance_seconds=-1)


def test_webhook_verifier_rejects_malformed_timestamp_and_hmac() -> None:
    with pytest.raises(WebhookVerificationError, match="timestamp"):
        signature = "t=soon,v1=" + "a" * 64
        parse_signature_header(signature)

    with pytest.raises(WebhookVerificationError, match="HMAC"):
        parse_signature_header("t=1000,v1=not-hex")


def test_webhook_verifier_rejects_invalid_json_body() -> None:
    with pytest.raises(WebhookVerificationError, match="valid JSON"):
        decode_webhook_body(b"not json")

    with pytest.raises(WebhookVerificationError, match="JSON object"):
        decode_webhook_body(b"[]")


def test_webhook_verifier_rejects_payload_schema_errors() -> None:
    payload = {"event": "declaration.ingested"}
    body = json.dumps(payload).encode("utf-8")
    header = signed_header(
        secret="whsec_test",
        body=body,
        timestamp=1000,
    )
    verifier = WebhookVerifier(secret="whsec_test")

    with pytest.raises(WebhookVerificationError, match="event_id"):
        verifier.verify(
            body,
            header,
            now=1000,
        )


def test_webhook_verifier_rejects_header_part_without_separator() -> None:
    with pytest.raises(WebhookVerificationError, match="Malformed"):
        parse_signature_header("t=1000,broken")


def test_verify_surfaces_an_unknown_event_without_disguising_it() -> None:
    # The signature was already checked, so the delivery is authentic. It must
    # not arrive as WebhookVerificationError: the handler has to be able to
    # tell "Pharos published a new event" from "this delivery is not genuine",
    # acknowledge the first, and refuse the second.
    payload = webhook_payload()
    payload["event"] = "declaration.archived"
    body = json.dumps(payload).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)
    verifier = WebhookVerifier(secret="whsec_test")

    with pytest.raises(UnsupportedWebhookEvent) as raised:
        verifier.verify(body, header, now=1000)

    assert raised.value.event == "declaration.archived"
    assert not isinstance(raised.value, WebhookVerificationError)
    assert "declaration.archived" in str(raised.value)


def form_encoded(payload: JSONObject) -> bytes:
    """The body exactly as Pharos sends it to a form-encoded endpoint."""
    flattened = {
        key: value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        for key, value in payload.items()
    }
    return urlencode(flattened).encode("utf-8")


def test_webhook_verifier_reads_a_form_encoded_body() -> None:
    # The same event, delivered to an endpoint configured as a form. Nothing
    # about the signature changes: it covers the bytes that arrived, whatever
    # shape they are in.
    payload = webhook_payload()
    body = form_encoded(payload)
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)
    verifier = WebhookVerifier(secret="whsec_test")

    event = verifier.verify(
        body,
        header,
        content_type="application/x-www-form-urlencoded",
        now=1000,
    )

    assert isinstance(event, DeclarationIngestedEvent)
    assert event.revision == payload["revision"]
    assert event.declaration.full_number == payload["declaration"]["full_number"]
    assert event.importer.ruc == payload["importer"]["ruc"]


def test_webhook_verifier_accepts_a_content_type_with_parameters() -> None:
    """Frameworks hand over the header as it arrived, charset and all."""
    payload = webhook_payload()
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)
    verifier = WebhookVerifier(secret="whsec_test")

    event = verifier.verify(
        body,
        header,
        content_type="Application/JSON; charset=utf-8",
        now=1000,
    )

    assert isinstance(event, DeclarationIngestedEvent)


def test_webhook_verifier_rejects_an_unknown_content_type() -> None:
    payload = webhook_payload()
    body = json.dumps(payload).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)
    verifier = WebhookVerifier(secret="whsec_test")

    with pytest.raises(WebhookVerificationError, match="Unsupported webhook content type"):
        verifier.verify(body, header, content_type="text/xml", now=1000)


def test_decode_form_body_rejects_an_object_field_that_is_not_json() -> None:
    body = urlencode({"declaration": "not json"}).encode("utf-8")

    with pytest.raises(WebhookVerificationError, match="declaration is not valid JSON"):
        decode_webhook_body(body, content_type="application/x-www-form-urlencoded")


def test_decode_form_body_rejects_an_object_field_that_is_not_an_object() -> None:
    body = urlencode({"declaration": "[]"}).encode("utf-8")

    with pytest.raises(WebhookVerificationError, match="declaration must be a JSON object"):
        decode_webhook_body(body, content_type="application/x-www-form-urlencoded")


def test_decode_form_body_rejects_a_revision_that_is_not_a_number() -> None:
    body = urlencode({"revision": "two"}).encode("utf-8")

    with pytest.raises(WebhookVerificationError, match="revision is not a whole number"):
        decode_webhook_body(body, content_type="application/x-www-form-urlencoded")


def test_decode_form_body_rejects_bytes_that_are_not_utf8() -> None:
    with pytest.raises(WebhookVerificationError, match="not valid UTF-8"):
        decode_webhook_body(b"revision=\xff", content_type="application/x-www-form-urlencoded")


def test_validation_event_is_parsed_with_its_result() -> None:
    payload = validation_webhook_payload()
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)
    verifier = WebhookVerifier(secret="whsec_test")

    event = verifier.verify(body, header, now=1000)

    assert isinstance(event, DeclarationValidationCompletedEvent)
    assert event.validation is not None
    assert event.validation.status == "issues_detected"
    assert event.validation.findings_count == 2
    assert event.validation.severity_counts.high == 2
    assert event.validation.severity_counts.critical == 0
    assert event.validation.evaluated_at is not None


def test_validation_finding_carries_the_rule_that_produced_it() -> None:
    payload = validation_webhook_payload()
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)

    event = WebhookVerifier(secret="whsec_test").verify(body, header, now=1000)

    assert isinstance(event, DeclarationValidationCompletedEvent)
    assert event.validation is not None
    finding = event.validation.findings[0]
    assert finding.rule_code == "duplicate_vin_in_declaration"
    assert finding.rule_version == 1
    assert finding.severity == "high"
    assert finding.item_number == 3
    assert finding.evidence.identifier_value == "LZPAERLMXRB000946"
    assert finding.evidence.item_numbers == (3, 7)
    assert finding.evidence.item_numbers_truncated is False


def test_an_external_occurrence_carries_only_what_may_be_told() -> None:
    payload = validation_webhook_payload()
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)

    event = WebhookVerifier(secret="whsec_test").verify(body, header, now=1000)

    assert isinstance(event, DeclarationValidationCompletedEvent)
    assert event.validation is not None
    mine, theirs = event.validation.findings[1].evidence.occurrences
    assert mine.match_scope == "authorized_importers"
    assert mine.declaration_full_number == "118-2025-10-009876-00"
    assert theirs.match_scope == "external_importer"
    assert theirs.declaration_full_number is None
    assert theirs.item_number is None
    assert theirs.customs_office_code == "235"


def test_evidence_keeps_a_key_this_version_does_not_document() -> None:
    payload = validation_webhook_payload()
    validation = cast(JSONObject, payload["validation"])
    findings = cast(List[JSONObject], validation["findings"])
    evidence = cast(JSONObject, findings[0]["evidence"])
    evidence["drivetrain"] = "3X1"
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)

    event = WebhookVerifier(secret="whsec_test").verify(body, header, now=1000)

    assert isinstance(event, DeclarationValidationCompletedEvent)
    assert event.validation is not None
    assert event.validation.findings[0].evidence.extra == {"drivetrain": "3X1"}


def test_validation_survives_the_form_encoding() -> None:
    payload = validation_webhook_payload()
    form = {
        "event_id": payload["event_id"],
        "event": payload["event"],
        "occurred_at": payload["occurred_at"],
        "revision": str(payload["revision"]),
        "declaration": json.dumps(payload["declaration"]),
        "importer": json.dumps(payload["importer"]),
        "resource_url": payload["resource_url"],
        "validation": json.dumps(payload["validation"]),
    }
    body = urlencode(form).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)

    event = WebhookVerifier(secret="whsec_test").verify(
        body,
        header,
        content_type="application/x-www-form-urlencoded",
        now=1000,
    )

    assert isinstance(event, DeclarationValidationCompletedEvent)
    assert event.validation is not None
    assert event.validation.findings_count == 2
    assert event.validation.findings[0].evidence.item_numbers == (3, 7)


def test_validation_is_not_repeated_in_extra() -> None:
    payload = validation_webhook_payload()
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)

    event = WebhookVerifier(secret="whsec_test").verify(body, header, now=1000)

    assert event.extra == {}


def test_a_finding_flag_that_is_not_a_boolean_is_refused() -> None:
    payload = validation_webhook_payload()
    validation = cast(JSONObject, payload["validation"])
    findings = cast(List[JSONObject], validation["findings"])
    evidence = cast(JSONObject, findings[0]["evidence"])
    evidence["item_numbers_truncated"] = "false"
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)

    with pytest.raises(WebhookVerificationError):
        WebhookVerifier(secret="whsec_test").verify(body, header, now=1000)


def test_a_result_without_an_evaluation_time_is_accepted() -> None:
    payload = validation_webhook_payload()
    validation = cast(JSONObject, payload["validation"])
    validation["evaluated_at"] = None
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = signed_header(secret="whsec_test", body=body, timestamp=1000)

    event = WebhookVerifier(secret="whsec_test").verify(body, header, now=1000)

    assert isinstance(event, DeclarationValidationCompletedEvent)
    assert event.validation is not None
    assert event.validation.evaluated_at is None
