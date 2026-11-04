"""Explicit legacy ETF research workflows; no runtime market-data collection."""

from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from market_data.domain.local_etf_evidence import (
    Inventory,
    ReviewDecision,
    binding_nodes,
    qualification_issues,
    scope_compatible,
    selected_review,
    support_reasons,
)
from market_data_tools.legacy.industry_representations import representation_worklist
from market_data_tools.legacy.region_database import RegionDatabase
from market_data_tools.local_etf_sources import inspect_sources, utc_observation


class CandidateState(TypedDict):
    candidate_id: str
    ticker: str
    states: list[str]
    issues: tuple[str, ...]
    provisional_match: bool
    reviewed_binding: bool


def collect_etf_candidates(
    database: RegionDatabase,
    *,
    roots: dict[str, Path] | None = None,
    catalogs: tuple[str, ...] = (),
    observed_at: datetime | None = None,
) -> Inventory:
    if not database.is_initialized():
        raise ValueError(
            f"Local ETF research requires an initialized schema 3 database: {database.path}"
        )
    inventory = inspect_sources(roots=roots, catalogs=catalogs, observed_at=observed_at)
    database.save_etf_collection(inventory)
    return database.get_etf_inventory(inventory.run.run_id)


def review_etf_candidates(
    database: RegionDatabase,
    *,
    region_id: str,
    classification_id: str,
    as_of: date,
    collection_run: str | None = None,
) -> dict[str, object]:
    database.validate_etf_scope(region_id, classification_id, as_of)
    inventory = database.get_etf_inventory(collection_run)
    snapshot = database.get_etf_snapshot()
    report = inventory.report()
    nodes: list[dict[str, object]] = []
    bound_ids: set[str] = set()
    for row in representation_worklist(
        database,
        region_id=region_id,
        classification_id=classification_id,
        as_of=as_of,
    ):
        candidates: list[CandidateState] = []
        selected = selected_review(snapshot.reviews, region_id, classification_id, row.node_id)
        reasons = support_reasons(selected, snapshot) if selected else ()
        for candidate in inventory.candidates:
            binding = row.node_id in binding_nodes(
                candidate, snapshot, region_id, classification_id
            )
            first = candidate.evidence[0]
            provisional = (
                first.label.strip().casefold() == row.name.strip().casefold()
                and scope_compatible(first, region_id, classification_id)
            )
            if not binding and not provisional:
                continue
            if binding:
                bound_ids.add(candidate.candidate_id)
            decisions = [
                r
                for r in snapshot.reviews
                if (r.region_id, r.classification_id, r.entity_id, r.candidate_id)
                == (region_id, classification_id, row.node_id, candidate.candidate_id)
            ]
            states = [
                "needs_suitability_review" if binding else "needs_classification_reconciliation"
            ]
            if decisions:
                states.append(
                    "reviewer_accepted"
                    if decisions[-1].decision == "accept"
                    else "reviewer_rejected"
                )
                if (
                    selected is not None
                    and selected.review_id == decisions[-1].review_id
                    and not reasons
                ):
                    states = ["reviewer_accepted"]
                elif binding and decisions[-1].decision == "reject":
                    states = ["reviewer_rejected"]
            issues = tuple(
                sorted(
                    {
                        issue
                        for item in candidate.evidence
                        for issue in qualification_issues(
                            item,
                            region=region_id,
                            classification=classification_id,
                            node_level=row.node_type,
                        )
                    }
                )
            )
            candidates.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "ticker": first.normalized_ticker,
                    "states": states,
                    "issues": issues,
                    "provisional_match": provisional,
                    "reviewed_binding": binding,
                }
            )
        if len({c["ticker"] for c in candidates}) > 1 and (selected is None or reasons):
            for candidate in candidates:
                candidate["states"].append("conflicting_evidence")
        nodes.append(
            {
                **asdict(row),
                "approved_status": row.status,
                "candidate_states": candidates if candidates else [{"states": ["no_candidate"]}],
                "selected_review_id": selected.review_id if selected else None,
                "selected_review_status": "none"
                if not selected
                else "accepted_needs_re_review"
                if reasons
                else "accepted_current",
                "re_review_reasons": reasons,
            }
        )
    report.update(
        {
            "nodes": nodes,
            "unbound_candidates": [
                candidate
                for candidate in inventory.candidate_reports()
                if candidate["candidate_id"] not in bound_ids
            ],
            "reviews": [
                asdict(review)
                for review in snapshot.reviews
                if (review.region_id, review.classification_id) == (region_id, classification_id)
            ],
            "currentness_collection_run_id": snapshot.latest.run.run_id,
            "currentness_observed_at": snapshot.latest.run.observed_at,
        }
    )
    return report


def record_etf_candidate_review(
    database: RegionDatabase,
    *,
    candidate_id: str,
    collection_run: str,
    region_id: str,
    classification_id: str,
    entity_id: str,
    as_of: date,
    decision: str,
    reason: str,
    review_reference: str,
    evidence_ids: tuple[str, ...],
    confirmations: tuple[bool, bool, bool] = (False, False, False),
    resolutions: tuple[tuple[str, str], ...] = (),
    observed_at: datetime | None = None,
) -> ReviewDecision:
    review = ReviewDecision(
        str(uuid4()),
        0,
        candidate_id,
        region_id,
        classification_id,
        entity_id,
        as_of.isoformat(),
        collection_run,
        decision,
        reason,
        review_reference,
        evidence_ids,
        confirmations,
        resolutions,
        utc_observation(observed_at),
    )
    return database.add_etf_candidate_review(review)
