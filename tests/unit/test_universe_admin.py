import json
from datetime import date

import pytest

from market_leadership.universe_admin import main


def _args(database):
    return [
        "--database",
        str(database.path),
        "--region",
        "US",
        "--classification",
        "TEST",
    ]


def test_legacy_administration_requires_explicit_database(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as error:
        main(["init"])
    assert error.value.code == 2
    assert "--database" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())


def test_review_worklist_cli_lists_all_nodes_and_can_filter_uncovered(
    representation_database,
    capsys,
):
    database = representation_database
    assert main(["review-representations", *_args(database), "--as-of", "2026-10-30"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert {item["node_id"] for item in rows} == {"test-cloud", "test-hardware"}
    assert all(item["status"] == "not_covered" for item in rows)
    assert (
        main(
            [
                "approve-etf",
                *_args(database),
                "--entity-id",
                "test-cloud",
                "--exchange",
                "NASDAQ",
                "--symbol",
                "AAA",
                "--source-id",
                "reviewed",
                "--approval-reference",
                "review-1",
                "--effective-from",
                "2020-01-01",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        main(
            [
                "review-representations",
                *_args(database),
                "--as-of",
                "2026-10-30",
                "--uncovered-only",
            ]
        )
        == 0
    )
    assert [item["node_id"] for item in json.loads(capsys.readouterr().out)] == ["test-hardware"]


def test_basket_cli_accepts_decimal_weights_and_reports_bad_input(representation_database, capsys):
    database = representation_database
    with database.connect() as connection:
        listings = {
            row["symbol"]: row["listing_id"]
            for row in connection.execute("SELECT symbol, listing_id FROM stock_listings")
        }
    base = [
        "approve-basket",
        *_args(database),
        "--entity-id",
        "test-cloud",
        "--name",
        "Cloud basket",
        "--source-id",
        "reviewed",
        "--approval-reference",
        "review-1",
        "--effective-from",
        "2020-01-01",
    ]
    assert (
        main(
            [
                *base,
                "--constituent",
                f"{listings['AAA']}=60",
                "--constituent",
                f"{listings['BBB']}=40",
            ]
        )
        == 0
    )
    assert "basket" in capsys.readouterr().out.lower()
    assert main([*base, "--constituent", f"{listings['AAA']}=99"]) == 2
    assert "100%" in capsys.readouterr().err
    assert database.get_stock_baskets("US", "TEST", as_of=date(2026, 10, 30))


@pytest.mark.parametrize("value", ["not-a-weight", "listing=bad", "listing=NaN", "listing=-1"])
def test_basket_cli_invalid_input_is_actionable(representation_database, capsys, value):
    status = main(
        [
            "approve-basket",
            *_args(representation_database),
            "--entity-id",
            "test-cloud",
            "--name",
            "Bad",
            "--source-id",
            "reviewed",
            "--approval-reference",
            "review-1",
            "--effective-from",
            "2020-01-01",
            "--constituent",
            value,
        ]
    )
    assert status == 2
    assert "failed" in capsys.readouterr().err.lower()


def test_review_listings_exposes_verified_ids_for_basket_administration(
    representation_database,
    capsys,
):
    database = representation_database
    with database.connect() as connection:
        connection.execute(
            "UPDATE stock_listings SET resolution_state = 'unverified' WHERE symbol = 'BBB'"
        )
    assert (
        main(
            [
                "review-listings",
                "--database",
                str(database.path),
                "--region",
                "US",
                "--as-of",
                "2026-10-30",
            ]
        )
        == 0
    )
    rows = json.loads(capsys.readouterr().out)
    assert [item["symbol"] for item in rows] == ["AAA", "CCC"]
    assert all(item["listing_id"] for item in rows)
