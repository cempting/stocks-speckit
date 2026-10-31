from datetime import UTC, datetime

import pytest

from market_leadership.infrastructure.local_etf_sources import inspect_sources

NOW = datetime(2026, 10, 31, tzinfo=UTC)
VIEWER = ("stockviewer=config.py:INDUSTRY_ETFS",)


def inspect(roots, catalogs=VIEWER):
    return inspect_sources(roots=roots, catalogs=catalogs, observed_at=NOW)


def test_literal_duplicates_scope_unicode_context_and_no_execution(local_etf_roots):
    inventory = inspect(local_etf_roots)
    assert inventory.run.status == "complete"
    assert len([e for e in inventory.evidence if e.catalog_type == "industry"]) == 10
    assert len([e for e in inventory.evidence if e.catalog_type != "industry"]) == 4
    assert sum(e.label == "Semiconductors" for e in inventory.evidence) == 7
    assert any(e.label == "Software\u2014Application" for e in inventory.evidence)
    assert all(e.region is None for e in inventory.evidence if e.resource == "analyzer")
    assert "excluded-fixture-value" not in str(inventory.report())
    assert all(e.line > 0 and e.end_line >= e.line for e in inventory.evidence)
    us = sorted(
        (e for e in inventory.evidence if e.catalog == "US_INDUSTRY_ETFS"),
        key=lambda e: e.ordinal,
    )
    assert [(e.label, e.ticker, e.line, e.column) for e in us] == [
        ("Semiconductors", "SOXX", 4, 4),
        ("Semiconductors", "SMH", 5, 4),
        ("Semiconductors", "SOXX", 6, 4),
        ("Hardware", "XLK", 7, 4),
    ]
    lines = (local_etf_roots["sector_rotation"] / "src/constants.py").read_text().splitlines()
    for occurrence in us:
        assert occurrence.end_line == occurrence.line
        assert occurrence.end_column == lines[occurrence.line - 1].rindex('"') + 1


@pytest.mark.parametrize(
    "expression",
    [
        "dict(a='ETF')",
        "{'Good': 'ETF', 'Bad': call()}",
        "{**OTHER, 'Good': 'ETF'}",
        "{'Good': 'ETF', 'Bad': 123}",
        "{'Good': 'ETF', 'Bad': {'nested': 'ETF'}}",
        "{x: 'ETF' for x in items}",
        "OTHER",
        "{'Bad': f'{SECRET}'}",
    ],
)
def test_unsupported_forms_are_partial_and_keep_supported_siblings(
    local_etf_roots,
    expression,
):
    path = local_etf_roots["analyzer"] / "config.py"
    path.write_text(f"INDUSTRY_ETFS = {expression}\n")
    inventory = inspect(local_etf_roots)
    assert inventory.run.status == "partial"
    outcome = next(r for r in inventory.run.resources if r.alias == "analyzer")
    assert outcome.status in ("inspected_with_issues", "unsupported")
    if "'Good': 'ETF'" in expression:
        assert any(e.label == "Good" for e in inventory.evidence)


def test_missing_root_corrected_root_and_catalog_status(local_etf_roots, tmp_path):
    local_etf_roots["stockviewer"] = tmp_path / "absent"
    assert inspect(local_etf_roots).run.status == "partial"
    for alias in local_etf_roots:
        local_etf_roots[alias] = tmp_path / f"missing-{alias}"
    assert inspect(local_etf_roots).run.status == "failed"


def test_traversal_symlink_encoding_and_private_syntax_errors(local_etf_roots, tmp_path):
    outside = tmp_path / "outside.py"
    outside.write_text("INDUSTRY_ETFS = {'Secret': 'PRIVATE'}")
    (local_etf_roots["stockviewer"] / "escape.py").symlink_to(outside)
    for descriptor in (
        "stockviewer=../outside.py:INDUSTRY_ETFS",
        "stockviewer=escape.py:INDUSTRY_ETFS",
    ):
        inventory = inspect(local_etf_roots, (descriptor,))
        assert inventory.run.status == "partial"
        assert "PRIVATE" not in str(inventory.report())
    path = local_etf_roots["analyzer"] / "config.py"
    path.write_text("PRIVATE = 'do-not-leak'\nINDUSTRY_ETFS = {'Broken':\n")
    inventory = inspect(local_etf_roots)
    assert "do-not-leak" not in str(inventory.report())
    path.write_bytes(b"# coding: latin-1\nINDUSTRY_ETFS = {'Caf\xe9': 'ETF'}\n")
    assert any(e.label == "Caf\u00e9" for e in inspect(local_etf_roots).evidence)


def test_catalogs_read_once_and_ignore_local_or_unselected_assignments(
    local_etf_roots,
    monkeypatch,
):
    from pathlib import Path

    original = Path.read_bytes
    calls = []

    def read(path):
        calls.append(path)
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    inventory = inspect(local_etf_roots)
    assert inventory.run.status == "complete"
    assert len(calls) == len(set(calls)) == 4
    path = local_etf_roots["analyzer"] / "config.py"
    path.write_text("PRIVATE = call()\ndef local():\n    INDUSTRY_ETFS = {'Bad': 'BAD'}\n")
    inventory = inspect(local_etf_roots)
    assert not any(e.ticker == "BAD" for e in inventory.evidence)


def test_complete_empty_catalogs_and_inaccessible_source(local_etf_roots, monkeypatch):
    from pathlib import Path

    for path in (
        local_etf_roots["sector_rotation"] / "src/constants.py",
        local_etf_roots["analyzer"] / "config.py",
        local_etf_roots["stockfinder"] / "src/stockfinder/data.py",
        local_etf_roots["stockviewer"] / "config.py",
    ):
        path.write_text("US_INDUSTRY_ETFS = {}\nEUROPE_INDUSTRY_ETFS = {}\nINDUSTRY_ETFS = {}\n")
    assert inspect(local_etf_roots).run.status == "complete"
    assert inspect(local_etf_roots).candidates == ()
    original = Path.read_bytes

    def denied(path):
        if path == local_etf_roots["analyzer"] / "config.py":
            raise PermissionError("excluded-private-error-text")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", denied)
    inventory = inspect(local_etf_roots)
    assert (
        next(r for r in inventory.run.resources if r.alias == "analyzer").status == "inaccessible"
    )
    assert "excluded-private-error-text" not in str(inventory.report())
