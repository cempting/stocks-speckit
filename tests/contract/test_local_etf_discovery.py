import json

from market_leadership.universe_admin import main


def roots_args(roots):
    result = []
    for alias, root in roots.items():
        result += ["--root", f"{alias}={root}"]
    return result + ["--catalog", "stockviewer=config.py:INDUSTRY_ETFS"]


def test_collection_json_complete_partial_errors(local_etf_database, local_etf_roots, capsys):
    args = ["collect-etf-candidates", "--database", str(local_etf_database.path)]
    assert main(args + roots_args(local_etf_roots)) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["report_version"] == "local-etf-discovery-1"
    assert len(report["resources"]) == 4
    assert len(report["candidates"]) > 0
    local_etf_roots["stockviewer"] /= "missing"
    assert main(args + roots_args(local_etf_roots)) == 2
    output = capsys.readouterr()
    assert json.loads(output.out)["status"] == "partial"
    assert "stockviewer" in output.err
    assert main(args + ["--root", "unknown=/tmp"]) == 2
    assert "unknown" in capsys.readouterr().err


def test_collection_requires_initialized_database(tmp_path, local_etf_roots, capsys):
    path = tmp_path / "uninitialized.sqlite"
    assert (
        main(["collect-etf-candidates", "--database", str(path)] + roots_args(local_etf_roots)) == 2
    )
    output = capsys.readouterr()
    assert output.out == ""
    assert "database" in output.err.lower()
    assert not path.exists()


def test_review_read_scope_historical_and_no_rescan(
    local_etf_database,
    local_etf_roots,
    capsys,
    monkeypatch,
):
    assert (
        main(
            ["collect-etf-candidates", "--database", str(local_etf_database.path)]
            + roots_args(local_etf_roots)
        )
        == 0
    )
    run = json.loads(capsys.readouterr().out)["collection_run_id"]
    from pathlib import Path

    def forbidden(path):
        raise AssertionError("Review must use persisted observations")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    args = [
        "review-etf-candidates",
        "--database",
        str(local_etf_database.path),
        "--region",
        "US",
        "--classification",
        "LOCAL-ETF-TEST",
        "--as-of",
        "2026-10-30",
        "--collection-run",
        run,
    ]
    assert main(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert len(report["nodes"]) == 4
    assert report["currentness_observed_at"]
    assert main(args[:-1] + ["unknown"]) == 2
    assert "run" in capsys.readouterr().err


def test_manual_review_and_optional_existing_approval(
    local_etf_database,
    local_etf_roots,
    capsys,
):
    database = str(local_etf_database.path)
    assert (
        main(["collect-etf-candidates", "--database", database] + roots_args(local_etf_roots)) == 0
    )
    report = json.loads(capsys.readouterr().out)
    candidate = next(
        c
        for c in report["candidates"]
        if c["label"] == "Semiconductors"
        and c["declared_region"] is None
        and c["normalized_ticker"] == "SOXX"
    )
    evidence = next(e for e in candidate["occurrences"] if e["resource"] == "analyzer")
    args = [
        "review-etf-candidate",
        "--database",
        database,
        "--candidate-id",
        candidate["candidate_id"],
        "--collection-run",
        report["collection_run_id"],
        "--region",
        "US",
        "--classification",
        "LOCAL-ETF-TEST",
        "--entity-id",
        "local-etf-test-semiconductors",
        "--as-of",
        "2026-10-30",
        "--decision",
        "accept",
        "--reason",
        "controlled suitability",
        "--review-reference",
        "test-only",
        "--evidence-id",
        evidence["evidence_id"],
    ]
    assert main(args) == 2
    assert capsys.readouterr().out == ""
    args += ["--confirm-etf-identity", "--confirm-exact-scope", "--confirm-suitability"]
    for issue in candidate["issues"]:
        args += ["--issue-resolution", f"{issue}=controlled assessment"]
    assert main(args) == 0
    decision = json.loads(capsys.readouterr().out)
    assert decision["report_version"] == "local-etf-discovery-1"
    assert decision["selected_review_status"] == "accepted_current"
    approval_args = [
        "approve-etf",
        "--database",
        database,
        "--region",
        "US",
        "--classification",
        "LOCAL-ETF-TEST",
        "--entity-id",
        "local-etf-test-semiconductors",
        "--exchange",
        "NASDAQ",
        "--symbol",
        "SOXX",
        "--source-id",
        "local-etf-test",
        "--approval-reference",
        "test-only",
        "--effective-from",
        "2020-01-01",
        "--candidate-review-id",
        decision["review_id"],
    ]
    assert main(approval_args[:-1] + ["unknown"]) == 2
    assert "selection" in capsys.readouterr().err
    assert main(approval_args) == 0
    assert "representation-" in capsys.readouterr().out
    with local_etf_database.connect() as connection:
        assert (
            connection.execute("SELECT review_id FROM etf_representation_provenance").fetchone()[0]
            == decision["review_id"]
        )
