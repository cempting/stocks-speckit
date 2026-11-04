"""Versioned, immutable file storage for reviewed issuer evidence."""

import fcntl
import json
import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal, cast

from market_data.domain.company_evidence import (
    AssessmentRole,
    AssessmentStatus,
    ClaimKind,
    ClaimState,
    ClaimTopic,
    CompanyAssociation,
    CompanyEvidenceOutcome,
    CompanyEvidenceRequest,
    CompanyEvidenceSnapshot,
    CompanyResearchClaim,
    EvidenceMode,
    EvidenceProvenance,
    EvidenceScope,
    EvidenceUse,
    FinancialBasis,
    FinancialObservation,
    ObservationOrigin,
    ObservationState,
    SourceAssessment,
    company_evidence_snapshot_digest,
)

SOURCE_FORMAT = "company-source-assessments-1"
BINDING_FORMAT = "company-issuer-bindings-1"
SNAPSHOT_FORMAT = "company-evidence-snapshot-1"
ENTRY_FORMAT = "company-evidence-entry-1"
_HEX = frozenset("0123456789abcdef")
_MAX_EVIDENCE_FILE_SIZE = 10 * 1024 * 1024


class CompanyEvidenceStoreError(ValueError):
    """A safe, actionable error reading or publishing issuer evidence."""


class RevisionConflictError(CompanyEvidenceStoreError):
    """The latest pointer changed from the caller's expected revision."""


def _jsonable(value: object) -> object:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_jsonable(item) for item in cast(tuple[object, ...], value)]
    if isinstance(value, list):
        return [_jsonable(item) for item in cast(list[object], value)]
    if isinstance(value, dict):
        mapping = cast(dict[object, object], value)
        return {str(key): _jsonable(item) for key, item in mapping.items()}
    return value


def _encode(data: object) -> bytes:
    return (
        json.dumps(
            _jsonable(data),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _digest(data: object) -> str:
    return sha256(_encode(data)).hexdigest()


def _object(value: object, field: str, keys: set[str]) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CompanyEvidenceStoreError(f"Invalid evidence object: {field}")
    mapping = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in mapping):
        raise CompanyEvidenceStoreError(f"Invalid evidence object keys: {field}")
    result = cast(dict[str, object], mapping)
    if set(result) != keys:
        raise CompanyEvidenceStoreError(f"Invalid evidence object: {field}")
    return result


def _read_json(path: Path) -> dict[str, object]:
    try:
        if path.stat().st_size > _MAX_EVIDENCE_FILE_SIZE:
            raise CompanyEvidenceStoreError("Evidence JSON exceeds the 10 MiB size limit")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise CompanyEvidenceStoreError("Unable to read valid evidence JSON") from None
    if not isinstance(value, dict):
        raise CompanyEvidenceStoreError("Evidence JSON root must be an object")
    return cast(dict[str, object], value)


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise CompanyEvidenceStoreError(f"Invalid evidence field: {field}")
    return value


def _optional_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field)


def _date(value: object, field: str) -> date:
    try:
        return date.fromisoformat(_string(value, field))
    except ValueError:
        raise CompanyEvidenceStoreError(f"Invalid evidence date: {field}") from None


def _optional_date(value: object, field: str) -> date | None:
    return None if value is None else _date(value, field)


def _datetime(value: object, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(_string(value, field).replace("Z", "+00:00"))
    except ValueError:
        raise CompanyEvidenceStoreError(f"Invalid evidence timestamp: {field}") from None
    if parsed.utcoffset() != UTC.utcoffset(parsed):
        raise CompanyEvidenceStoreError(f"Evidence timestamp is not UTC: {field}")
    return parsed


def _strings(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CompanyEvidenceStoreError(f"Invalid evidence string list: {field}")
    values = cast(list[object], value)
    if not all(isinstance(item, str) for item in values):
        raise CompanyEvidenceStoreError(f"Invalid evidence string list: {field}")
    return tuple(cast(list[str], values))


def association_to_record(association: CompanyAssociation) -> dict[str, object]:
    return _object(
        _jsonable(asdict(association)), "association", set(CompanyAssociation.__dataclass_fields__)
    )


def association_from_record(data: object) -> CompanyAssociation:
    keys = set(CompanyAssociation.__dataclass_fields__)
    value = _object(data, "association", keys)
    return CompanyAssociation(
        association_id=_string(value["association_id"], "association_id"),
        instrument_id=_string(value["instrument_id"], "instrument_id"),
        listing_id=_string(value["listing_id"], "listing_id"),
        region_id=_string(value["region_id"], "region_id"),
        company_id=_optional_string(value["company_id"], "company_id"),
        provider_id=_string(value["provider_id"], "provider_id"),
        provider_symbol=_string(value["provider_symbol"], "provider_symbol"),
        exchange=_string(value["exchange"], "exchange"),
        trading_currency=_string(value["trading_currency"], "trading_currency"),
        catalog_revision=_string(value["catalog_revision"], "catalog_revision"),
        effective_from=_date(value["effective_from"], "effective_from"),
        effective_to=_optional_date(value["effective_to"], "effective_to"),
        issuer_key=_optional_string(value["issuer_key"], "issuer_key"),
        cik=_optional_string(value["cik"], "cik"),
        issuer_domain=_optional_string(value["issuer_domain"], "issuer_domain"),
        binding_reference=_optional_string(value["binding_reference"], "binding_reference"),
        identity_evidence=_optional_string(value["identity_evidence"], "identity_evidence"),
        state=cast(
            Literal["verified", "unresolved", "mismatch", "expired"],
            _string(value["state"], "state"),
        ),
        reason=_optional_string(value["reason"], "reason"),
        research_binding_reference=_optional_string(
            value["research_binding_reference"], "research_binding_reference"
        ),
        research_identity_evidence=_optional_string(
            value["research_identity_evidence"], "research_identity_evidence"
        ),
    )


def assessment_to_record(assessment: SourceAssessment) -> dict[str, object]:
    return _object(
        _jsonable(asdict(assessment)),
        "source_assessment",
        set(SourceAssessment.__dataclass_fields__),
    )


def assessment_from_record(data: object) -> SourceAssessment:
    keys = set(SourceAssessment.__dataclass_fields__)
    value = _object(data, "source_assessment", keys)
    return SourceAssessment(
        assessment_id=_string(value["assessment_id"], "assessment_id"),
        source_id=_string(value["source_id"], "source_id"),
        role=cast(AssessmentRole, _string(value["role"], "role")),
        status=cast(AssessmentStatus, _string(value["status"], "status")),
        allowed_uses=cast(
            tuple[EvidenceUse, ...], _strings(value["allowed_uses"], "allowed_uses")
        ),
        reviewed_at=_optional_date(value["reviewed_at"], "reviewed_at"),
        review_reference=_optional_string(value["review_reference"], "review_reference"),
        expires_at=_optional_date(value["expires_at"], "expires_at"),
        fingerprint=_string(value["fingerprint"], "fingerprint"),
        publisher=_optional_string(value["publisher"], "publisher"),
        terms_url=_optional_string(value["terms_url"], "terms_url"),
        coverage_reference=_optional_string(
            value["coverage_reference"], "coverage_reference"
        ),
        authority=_optional_string(value["authority"], "authority"),
        structured_capabilities=_strings(
            value["structured_capabilities"], "structured_capabilities"
        ),
        allowed_hosts=_strings(value["allowed_hosts"], "allowed_hosts"),
        allowed_routes=_strings(value["allowed_routes"], "allowed_routes"),
    )


def _provenance(data: object) -> EvidenceProvenance:
    keys = set(EvidenceProvenance.__dataclass_fields__)
    value = _object(data, "provenance", keys)
    return EvidenceProvenance(
        source_id=_string(value["source_id"], "source_id"),
        provider_id=_string(value["provider_id"], "provider_id"),
        assessment_fingerprint=_string(value["assessment_fingerprint"], "assessment_fingerprint"),
        source_url=_optional_string(value["source_url"], "source_url"),
        locator=_optional_string(value["locator"], "locator"),
        publication_date=_optional_date(value["publication_date"], "publication_date"),
        publication_precision=cast(
            Literal["day", "month", "year", "unknown"],
            _string(value["publication_precision"], "publication_precision"),
        ),
        observed_at=_datetime(value["observed_at"], "observed_at"),
        period_start=_optional_date(value["period_start"], "period_start"),
        period_end=_optional_date(value["period_end"], "period_end"),
        payload_sha256=_string(value["payload_sha256"], "payload_sha256"),
        schema_revision=_string(value["schema_revision"], "schema_revision"),
        limitations=_strings(value["limitations"], "limitations"),
    )


def _observation(data: object) -> FinancialObservation:
    keys = set(FinancialObservation.__dataclass_fields__)
    value = _object(data, "financial_observation", keys)
    raw_value = value["value"]
    if raw_value is not None and (
        isinstance(raw_value, bool) or not isinstance(raw_value, (int, float))
    ):
        raise CompanyEvidenceStoreError("Invalid financial observation value")
    raw_scale = value["source_scale"]
    if isinstance(raw_scale, bool) or not isinstance(raw_scale, (int, float)):
        raise CompanyEvidenceStoreError("Invalid financial observation scale")
    return FinancialObservation(
        observation_id=_string(value["observation_id"], "observation_id"),
        association_id=_string(value["association_id"], "association_id"),
        metric_key=_string(value["metric_key"], "metric_key"),
        value=cast(float | None, raw_value),
        unit=_string(value["unit"], "unit"),
        currency=_optional_string(value["currency"], "currency"),
        source_scale=float(raw_scale),
        period_start=_optional_date(value["period_start"], "period_start"),
        period_end=_date(value["period_end"], "period_end"),
        basis=cast(FinancialBasis, _string(value["basis"], "basis")),
        origin=cast(ObservationOrigin, _string(value["origin"], "origin")),
        definition=_string(value["definition"], "definition"),
        derivation_input_ids=_strings(value["derivation_input_ids"], "derivation_input_ids"),
        provenance=_provenance(value["provenance"]),
        state=cast(ObservationState, _string(value["state"], "state")),
        reason=_optional_string(value["reason"], "reason"),
    )


def _claim(data: object) -> CompanyResearchClaim:
    keys = set(CompanyResearchClaim.__dataclass_fields__)
    value = _object(data, "research_claim", keys)
    raw_value = value["value"]
    if raw_value is not None and (
        isinstance(raw_value, bool) or not isinstance(raw_value, (int, float))
    ):
        raise CompanyEvidenceStoreError("Invalid research claim value")
    basis = _optional_string(value["basis"], "basis")
    return CompanyResearchClaim(
        claim_id=_string(value["claim_id"], "claim_id"),
        association_id=_string(value["association_id"], "association_id"),
        issuer_key=_optional_string(value["issuer_key"], "issuer_key"),
        topic=cast(ClaimTopic, _string(value["topic"], "topic")),
        field_key=_string(value["field_key"], "field_key"),
        summary=_optional_string(value["summary"], "summary"),
        value=cast(float | None, raw_value),
        unit=_optional_string(value["unit"], "unit"),
        currency=_optional_string(value["currency"], "currency"),
        definition=_string(value["definition"], "definition"),
        qualifications=_string(value["qualifications"], "qualifications"),
        kind=cast(ClaimKind, _string(value["kind"], "kind")),
        provenance=_provenance(value["provenance"]),
        state=cast(ClaimState, _string(value["state"], "state")),
        reason=_optional_string(value["reason"], "reason"),
        named_source=_optional_string(value["named_source"], "named_source"),
        inspected_disclosure_scope=_optional_string(
            value["inspected_disclosure_scope"], "inspected_disclosure_scope"
        ),
        basis=cast(FinancialBasis | None, basis),
    )


def _request(data: object) -> CompanyEvidenceRequest:
    keys = set(CompanyEvidenceRequest.__dataclass_fields__)
    value = _object(data, "request", keys)
    history_window = value["history_window"]
    refresh = value["refresh"]
    if type(history_window) is not int or type(refresh) is not bool:
        raise CompanyEvidenceStoreError("Invalid evidence request limits")
    return CompanyEvidenceRequest(
        association=association_from_record(value["association"]),
        scope=cast(EvidenceScope, _string(value["scope"], "scope")),
        mode=cast(EvidenceMode, _string(value["mode"], "mode")),
        as_of=_date(value["as_of"], "as_of"),
        provider_id=_string(value["provider_id"], "provider_id"),
        source_ids=_strings(value["source_ids"], "source_ids"),
        binding_fingerprint=_string(value["binding_fingerprint"], "binding_fingerprint"),
        assessment_fingerprint=_string(
            value["assessment_fingerprint"], "assessment_fingerprint"
        ),
        history_window=history_window,
        normalization_revision=_string(value["normalization_revision"], "normalization_revision"),
        schema_revision=_string(value["schema_revision"], "schema_revision"),
        refresh=refresh,
    )


def _outcome(data: object) -> CompanyEvidenceOutcome:
    keys = set(CompanyEvidenceOutcome.__dataclass_fields__)
    value = _object(data, "outcome", keys)
    raw_observations = value["observations"]
    raw_claims = value["claims"]
    if not isinstance(raw_observations, list) or not isinstance(raw_claims, list):
        raise CompanyEvidenceStoreError("Invalid evidence outcome arrays")
    observations = cast(list[object], raw_observations)
    claims = cast(list[object], raw_claims)
    return CompanyEvidenceOutcome(
        state=cast(
            Literal["complete", "partial", "blocked", "error"],
            _string(value["state"], "state"),
        ),
        observations=tuple(_observation(item) for item in observations),
        claims=tuple(_claim(item) for item in claims),
        failures=_strings(value["failures"], "failures"),
        started_at=_datetime(value["started_at"], "started_at"),
        captured_at=_datetime(value["captured_at"], "captured_at"),
        completed_at=_datetime(value["completed_at"], "completed_at"),
        association_state=cast(
            Literal["verified", "unresolved", "mismatch", "expired"],
            _string(value["association_state"], "association_state"),
        ),
        association_reason=_optional_string(
            value["association_reason"], "association_reason"
        ),
        verified_association=(
            association_from_record(value["verified_association"])
            if value["verified_association"] is not None
            else None
        ),
    )


class CompanyEvidenceFiles:
    def __init__(self, root: Path) -> None:
        self._root = root.expanduser().absolute()

    def save_source_assessment(
        self, assessment: SourceAssessment, *, expected_revision: str | None
    ) -> str:
        return self._publish_record(
            category="sources",
            identity=assessment.source_id,
            format_name=SOURCE_FORMAT,
            revision=assessment.fingerprint,
            payload=assessment_to_record(assessment),
            expected_revision=expected_revision,
        )

    def load_source_assessment(self, source_id: str) -> SourceAssessment:
        record = self._load_record("sources", source_id, SOURCE_FORMAT)
        return assessment_from_record(record)

    def list_source_assessments(self) -> tuple[SourceAssessment, ...]:
        sources = self._contained("sources")
        if not sources.exists():
            return ()
        assessments: list[SourceAssessment] = []
        for pointer_path in sorted(sources.glob("*/CURRENT.json")):
            pointer = _read_json(
                self._contained(
                    pointer_path.relative_to(self._root.resolve()).as_posix()
                )
            )
            if pointer.get("format") != SOURCE_FORMAT:
                raise CompanyEvidenceStoreError("Source assessment pointer has an invalid format")
            identity = _string(pointer.get("identity"), "source_identity")
            if pointer_path.parent.name != sha256(identity.encode()).hexdigest():
                raise CompanyEvidenceStoreError(
                    "Source assessment pointer identity is inconsistent"
                )
            assessments.append(self.load_source_assessment(identity))
        return tuple(assessments)

    def save_association(
        self, association: CompanyAssociation, *, expected_revision: str | None
    ) -> str:
        payload = association_to_record(association)
        return self._publish_record(
            category="bindings",
            identity=association.association_id,
            format_name=BINDING_FORMAT,
            revision=_digest(payload),
            payload=payload,
            expected_revision=expected_revision,
        )

    def load_association(self, association_id: str) -> CompanyAssociation:
        record = self._load_record("bindings", association_id, BINDING_FORMAT)
        return association_from_record(record)

    def find_active_association(
        self,
        *,
        instrument_id: str,
        listing_id: str,
        provider_id: str,
        as_of: date,
    ) -> CompanyAssociation | None:
        bindings = self._contained("bindings")
        if not bindings.exists():
            return None
        matches: list[CompanyAssociation] = []
        for pointer_path in sorted(bindings.glob("*/CURRENT.json")):
            relative = pointer_path.relative_to(self._root.resolve())
            pointer = _read_json(self._contained(relative.as_posix()))
            if pointer.get("format") != BINDING_FORMAT:
                raise CompanyEvidenceStoreError("Issuer binding pointer has an invalid format")
            identity = _string(pointer.get("identity"), "binding_identity")
            if pointer_path.parent.name != sha256(identity.encode()).hexdigest():
                raise CompanyEvidenceStoreError("Issuer binding pointer identity is inconsistent")
            association = self.load_association(identity)
            if (
                association.instrument_id == instrument_id
                and association.listing_id == listing_id
                and association.provider_id == provider_id
                and association.active_on(as_of)
                and association.state in ("verified", "unresolved")
            ):
                matches.append(association)
        if len(matches) > 1:
            raise CompanyEvidenceStoreError(
                "Multiple active issuer bindings exist for the selected listing"
            )
        return matches[0] if matches else None

    def publish_snapshot(
        self,
        snapshot: CompanyEvidenceSnapshot,
        *,
        expected_revision: str | None,
    ) -> str:
        if expected_revision is not None:
            _validate_revision(expected_revision)
        association_id = snapshot.request.association.association_id
        scope = snapshot.request.scope
        key = sha256(f"{association_id}:{scope}".encode()).hexdigest()
        lock_path = self._contained(f"locks/{key}.lock")
        pointer_path = self._contained(f"entries/{key}.json")
        relative_snapshot = (
            f"snapshots/{key}/{snapshot.content_sha256}.json"
        )
        snapshot_path = self._contained(relative_snapshot)
        envelope = {
            "format": SNAPSHOT_FORMAT,
            "version": 1,
            "content_sha256": snapshot.content_sha256,
            "snapshot": asdict(snapshot),
        }
        with self._locked(lock_path):
            current = self._read_entry(pointer_path, association_id, scope)
            current_revision = current["revision"] if current else None
            if current_revision != expected_revision:
                raise RevisionConflictError(
                    "Evidence entry revision changed; reload before publishing"
                )
            self._write_immutable(snapshot_path, _encode(envelope))
            entry = {
                "format": ENTRY_FORMAT,
                "association_id": association_id,
                "scope": scope,
                "revision": snapshot.content_sha256,
                "snapshot_path": relative_snapshot,
                "snapshot_sha256": snapshot.content_sha256,
            }
            self._atomic_replace(pointer_path, _encode(entry))
        return snapshot.content_sha256

    def load_latest_snapshot(
        self, association_id: str, scope: EvidenceScope
    ) -> CompanyEvidenceSnapshot | None:
        reference = self.latest_snapshot_reference(association_id, scope)
        if reference is None:
            return None
        relative_path, revision = reference
        snapshot = self.load_snapshot(relative_path)
        if (
            snapshot.request.association.association_id != association_id
            or snapshot.request.scope != scope
            or snapshot.content_sha256 != revision
        ):
            raise CompanyEvidenceStoreError("Evidence entry points to a different snapshot")
        return snapshot

    def latest_snapshot_reference(
        self, association_id: str, scope: EvidenceScope
    ) -> tuple[str, str] | None:
        key = sha256(f"{association_id}:{scope}".encode()).hexdigest()
        pointer = self._read_entry(
            self._contained(f"entries/{key}.json"), association_id, scope
        )
        if pointer is None:
            return None
        return (
            cast(str, pointer["snapshot_path"]),
            cast(str, pointer["snapshot_sha256"]),
        )

    def list_latest_snapshots(
        self, scope: EvidenceScope
    ) -> tuple[CompanyEvidenceSnapshot, ...]:
        snapshots: list[CompanyEvidenceSnapshot] = []
        for association_id, relative_path, revision in self.list_latest_snapshot_references(
            scope
        ):
            snapshot = self.load_snapshot(relative_path)
            if (
                snapshot.request.association.association_id != association_id
                or snapshot.request.scope != scope
                or snapshot.content_sha256 != revision
            ):
                raise CompanyEvidenceStoreError("Evidence entry points to a different snapshot")
            snapshots.append(snapshot)
        return tuple(snapshots)

    def list_latest_snapshot_references(
        self, scope: EvidenceScope
    ) -> tuple[tuple[str, str, str], ...]:
        entries = self._contained("entries")
        if not entries.exists():
            return ()
        references: list[tuple[str, str, str]] = []
        for pointer_path in sorted(entries.glob("*.json")):
            pointer_entry_path = self._contained(
                pointer_path.relative_to(self._root.resolve()).as_posix()
            )
            pointer = _read_json(pointer_entry_path)
            association_id = _string(pointer.get("association_id"), "association_id")
            raw_scope = _string(pointer.get("scope"), "scope")
            if raw_scope not in ("financial", "research"):
                raise CompanyEvidenceStoreError("Evidence entry has an invalid scope")
            entry_scope = raw_scope
            expected_name = sha256(f"{association_id}:{entry_scope}".encode()).hexdigest()
            if pointer_path.stem != expected_name:
                raise CompanyEvidenceStoreError("Evidence entry path does not match its identity")
            if entry_scope == scope:
                entry = self._read_entry(pointer_entry_path, association_id, entry_scope)
                if entry is not None:
                    references.append(
                        (
                            association_id,
                            cast(str, entry["snapshot_path"]),
                            cast(str, entry["snapshot_sha256"]),
                        )
                    )
        return tuple(references)

    def load_snapshot(self, relative_path: str) -> CompanyEvidenceSnapshot:
        path = self._contained(relative_path)
        envelope = _object(
            _read_json(path),
            "snapshot_envelope",
            {"format", "version", "content_sha256", "snapshot"},
        )
        if envelope["format"] != SNAPSHOT_FORMAT or envelope["version"] != 1:
            raise CompanyEvidenceStoreError("Unsupported evidence snapshot format")
        snapshot_data = _object(
            envelope["snapshot"],
            "snapshot",
            {
                "version",
                "request",
                "outcome",
                "content_sha256",
                "predecessor_sha256",
                "policy_references",
            },
        )
        request = _request(snapshot_data["request"])
        outcome = _outcome(snapshot_data["outcome"])
        predecessor = _optional_string(
            snapshot_data["predecessor_sha256"], "predecessor_sha256"
        )
        policy_references = _strings(snapshot_data["policy_references"], "policy_references")
        snapshot_version = snapshot_data["version"]
        if type(snapshot_version) is not int:
            raise CompanyEvidenceStoreError("Invalid evidence snapshot version")
        snapshot = CompanyEvidenceSnapshot(
            version=snapshot_version,
            request=request,
            outcome=outcome,
            content_sha256=_string(snapshot_data["content_sha256"], "content_sha256"),
            predecessor_sha256=predecessor,
            policy_references=policy_references,
        )
        if (
            snapshot.content_sha256 != envelope["content_sha256"]
            or snapshot.content_sha256
            != company_evidence_snapshot_digest(
                request=request,
                outcome=outcome,
                version=snapshot.version,
                predecessor_sha256=predecessor,
                policy_references=policy_references,
            )
        ):
            raise CompanyEvidenceStoreError("Evidence snapshot hash mismatch")
        return snapshot

    def _publish_record(
        self,
        *,
        category: str,
        identity: str,
        format_name: str,
        revision: str,
        payload: dict[str, object],
        expected_revision: str | None,
    ) -> str:
        _validate_revision(revision)
        if expected_revision is not None:
            _validate_revision(expected_revision)
        key = sha256(identity.encode()).hexdigest()
        directory = f"{category}/{key}"
        pointer_path = self._contained(f"{directory}/CURRENT.json")
        record_path = self._contained(f"{directory}/{revision}.json")
        lock_path = self._contained(f"locks/{category}-{key}.lock")
        with self._locked(lock_path):
            current = _read_json(pointer_path) if pointer_path.exists() else None
            if current is not None and (
                current.get("format") != format_name or current.get("identity") != identity
            ):
                raise CompanyEvidenceStoreError("Evidence current pointer is corrupt")
            current_revision = current.get("revision") if current else None
            if current_revision != expected_revision:
                raise RevisionConflictError("Evidence revision changed; reload before publishing")
            envelope = {
                "format": format_name,
                "version": 1,
                "identity": identity,
                "revision": revision,
                "payload_sha256": _digest(payload),
                "payload": payload,
            }
            self._write_immutable(record_path, _encode(envelope))
            self._atomic_replace(
                pointer_path,
                _encode(
                    {
                        "format": format_name,
                        "identity": identity,
                        "revision": revision,
                        "record_path": f"{directory}/{revision}.json",
                    }
                ),
            )
        return revision

    def _load_record(self, category: str, identity: str, format_name: str) -> object:
        key = sha256(identity.encode()).hexdigest()
        pointer_path = self._contained(f"{category}/{key}/CURRENT.json")
        pointer = _read_json(pointer_path)
        if pointer.get("format") != format_name or pointer.get("identity") != identity:
            raise CompanyEvidenceStoreError("Evidence current pointer is corrupt")
        relative_path = _string(pointer.get("record_path"), "record_path")
        envelope = _read_json(self._contained(relative_path))
        if (
            envelope.get("format") != format_name
            or envelope.get("version") != 1
            or envelope.get("identity") != identity
            or envelope.get("revision") != pointer.get("revision")
            or envelope.get("payload_sha256") != _digest(envelope.get("payload"))
            or not isinstance(envelope.get("payload"), dict)
        ):
            raise CompanyEvidenceStoreError("Evidence record does not match its pointer")
        return envelope["payload"]

    def _read_entry(
        self, path: Path, association_id: str, scope: EvidenceScope
    ) -> dict[str, object] | None:
        if not path.exists():
            return None
        entry = _object(
            _read_json(path),
            "evidence_entry",
            {
                "format",
                "association_id",
                "scope",
                "revision",
                "snapshot_path",
                "snapshot_sha256",
            },
        )
        if (
            entry["format"] != ENTRY_FORMAT
            or entry["association_id"] != association_id
            or entry["scope"] != scope
            or entry["revision"] != entry["snapshot_sha256"]
        ):
            raise CompanyEvidenceStoreError("Evidence entry is corrupt")
        _validate_revision(_string(entry["revision"], "revision"))
        _string(entry["snapshot_path"], "snapshot_path")
        return entry

    def _contained(self, relative_path: str) -> Path:
        relative = Path(relative_path)
        root = self._root.resolve()
        if relative.is_absolute() or ".." in relative.parts:
            raise CompanyEvidenceStoreError("Unsafe evidence-relative path")
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            raise CompanyEvidenceStoreError("Evidence path escapes its configured root") from None
        return candidate

    @contextmanager
    def _locked(self, path: Path) -> Generator[None, None, None]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a+b") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _write_immutable(path: Path, raw: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".evidence-", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                if path.read_bytes() != raw:
                    raise CompanyEvidenceStoreError(
                        "Immutable evidence revision already differs"
                    ) from None
            CompanyEvidenceFiles._sync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _atomic_replace(path: Path, raw: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".entry-", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            CompanyEvidenceFiles._sync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _sync_directory(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _validate_revision(value: str) -> None:
    if len(value) != 64 or any(character not in _HEX for character in value):
        raise CompanyEvidenceStoreError("Revision must be a lowercase SHA-256 digest")
