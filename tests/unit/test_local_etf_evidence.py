from dataclasses import replace

from market_data.domain.local_etf_evidence import Evidence, group_candidates


def evidence(**changes):
    base = Evidence(
        resource="analyzer",
        root="/controlled",
        file="config.py",
        catalog="INDUSTRY_ETFS",
        label="Semiconductors",
        ticker=" soxx ",
        catalog_type="industry",
        region=None,
        classification=None,
        node_level=None,
        ordinal=0,
        line=1,
        end_line=1,
        column=0,
        end_column=10,
        catalog_content_id="snapshot",
        context=(),
        observed_at="2026-10-31T00:00:00+00:00",
    )
    return replace(base, **changes)


def test_identity_preserves_scope_labels_suffixes_and_occurrences():
    original = evidence()
    assert original.normalized_ticker == "SOXX"
    assert original.candidate_id == evidence(ticker="SOXX").candidate_id
    for changes in (
        {"region": "US"},
        {"label": "semiconductors"},
        {"label": " Semiconductors"},
        {"ticker": "SOXX.DE"},
    ):
        assert evidence(**changes).candidate_id != original.candidate_id
    copies = [original, evidence(ordinal=1), evidence(resource="stockfinder")]
    grouped = group_candidates(tuple(copies))
    assert len(grouped) == 1
    assert len(grouped[0].evidence) == 3
    assert len({item.evidence_id for item in copies}) == 3


def test_location_moves_do_not_change_meaning_and_context_is_not_candidate():
    original = evidence()
    moved = evidence(line=10, end_line=10)
    assert moved.evidence_id != original.evidence_id
    assert moved.semantic_fingerprint == original.semantic_fingerprint
    assert evidence(catalog_type="sector_context").candidate_id is None
    assert group_candidates((evidence(catalog_type="sector_context"),)) == ()


def test_qualification_and_explicit_selection_projection():
    from market_data.domain.local_etf_evidence import (
        ReviewDecision,
        qualification_issues,
        selected_review,
    )

    assert "non_etf" in qualification_issues(evidence(ticker="^INDEX"))
    assert "broad_sector_proxy" in qualification_issues(
        evidence(context=("sector_context:Technology",))
    )
    first = ReviewDecision(
        "first",
        1,
        "candidate-a",
        "US",
        "GICS",
        "node",
        "2026-10-30",
        "run",
        "accept",
        "reason",
        "reference",
        ("evidence",),
        (True, True, True),
        (),
        "2026-10-31T00:00:00+00:00",
    )
    rejected_other = replace(
        first, review_id="second", event_order=2, candidate_id="candidate-b", decision="reject"
    )
    assert selected_review((first, rejected_other), "US", "GICS", "node") == first
    rejected_selected = replace(first, review_id="third", event_order=3, decision="reject")
    assert selected_review((first, rejected_selected), "US", "GICS", "node") is None
    assert selected_review((first,), "US", "OTHER", "node") is None


def test_acceptance_rejects_empty_review_and_non_etf_even_with_confirmations():
    import pytest

    from market_data.domain.local_etf_evidence import ReviewDecision, validate_review

    item = evidence(ticker="^INDEX")
    review = ReviewDecision(
        "first",
        1,
        item.candidate_id,
        "US",
        "GICS",
        "node",
        "2026-10-30",
        "run",
        "accept",
        "reason",
        "reference",
        (item.evidence_id,),
        (True, True, True),
        (("non_etf", "not a valid workaround"),),
        "2026-10-31T00:00:00+00:00",
    )
    with pytest.raises(ValueError, match="non-ETF"):
        validate_review(review, (item,), node_level="industry")
    with pytest.raises(ValueError, match="reason"):
        validate_review(
            replace(review, decision="reject", reason=""), (item,), node_level="industry"
        )
