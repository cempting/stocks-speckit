from dataclasses import replace
from datetime import date

import pytest

from market_data.company_evidence import (
    assessment_from_record,
    assessment_to_record,
    association_from_record,
    association_to_record,
)
from market_data.domain.company_evidence import (
    AssessmentStatus,
    EvidenceScope,
    EvidenceUse,
    SourceAssessment,
    company_association_fingerprint,
)
from tests.company_evidence_helpers import (
    association_for_case,
    financial_assessment,
    verified_association,
)


@pytest.mark.parametrize("nullable", [False, True])
def test_association_roundtrip_preserves_nullable_identity_and_review(nullable: bool) -> None:
    original = (
        association_for_case({"case": "nullable"})
        if nullable else verified_association()
    )
    serialized = association_to_record(original)
    assert serialized["effective_from"] == original.effective_from.isoformat()
    assert serialized["effective_to"] is None
    assert serialized["company_id"] is None
    assert serialized["cik"] is None
    restored = association_from_record(serialized)
    assert restored == original
    scopes: tuple[EvidenceScope, ...] = ("financial", "research")
    for scope in scopes:
        assert company_association_fingerprint(restored, scope) == (
            company_association_fingerprint(original, scope)
        )


@pytest.mark.parametrize("status", ["unreviewed", "approved", "denied", "revoked"])
def test_assessment_roundtrip_preserves_legacy_dates_and_fingerprint(
    status: AssessmentStatus,
) -> None:
    original = replace(
        financial_assessment(),
        status=status,
        allowed_uses=(
            ("collection", "display", "normalized_retention") if status == "approved" else ()
        ),
        expires_at=date(2026, 11, 4),
    )
    serialized = assessment_to_record(original)
    assert serialized["reviewed_at"] == "2025-01-01"
    assert serialized["expires_at"] == "2026-11-04"
    assert serialized["fingerprint"] == original.fingerprint
    restored = assessment_from_record(serialized)
    assert restored == original
    assert not restored.permits("display", date(2026, 11, 5), role="financial")
    assert restored.permits("display", date(2026, 11, 4), role="financial") == (
        status == "approved"
    )


def test_reference_only_assessment_never_acquires_retains_or_displays() -> None:
    original = SourceAssessment(
        assessment_id="reference-review", source_id="test-news", role="reference",
        status="approved", allowed_uses=(), reviewed_at=date(2026, 1, 1),
        review_reference="metadata-review", expires_at=None, fingerprint="a" * 64,
    )
    restored = assessment_from_record(assessment_to_record(original))
    uses: tuple[EvidenceUse, ...] = (
        "collection", "display", "normalized_retention", "raw_retention"
    )
    for use in uses:
        assert not restored.permits(use, date(2026, 11, 4), role="reference")


def test_record_codecs_reject_missing_extra_and_invalid_fields() -> None:
    association = association_to_record(verified_association())
    assessment = assessment_to_record(financial_assessment())
    for decoder, record in [
        (association_from_record, association), (assessment_from_record, assessment),
    ]:
        missing = dict(record)
        missing.pop(next(iter(missing)))
        with pytest.raises(ValueError):
            decoder(missing)
        with pytest.raises(ValueError):
            decoder({**record, "extra": "not part of the reviewed record"})
    with pytest.raises(ValueError):
        association_from_record({**association, "effective_from": "2026-02-30"})
    with pytest.raises(ValueError):
        assessment_from_record({**assessment, "role": "observation"})
    with pytest.raises(ValueError):
        assessment_from_record({**assessment, "fingerprint": "not-a-digest"})
