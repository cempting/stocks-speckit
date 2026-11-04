from pathlib import Path

from market_leadership.universe_admin import main


def test_init_and_validate_cli_use_selected_database(tmp_path: Path, capsys) -> None:
    database = tmp_path / "universe.sqlite"
    assert main(["init", "--database", str(database)]) == 0
    assert database.exists()
    csv_path = tmp_path / "members.csv"
    csv_path.write_text(
        "Ticker,Name,Sector,Industry\nAAA,Alpha,Technology,Cloud\n",
        encoding="utf-8",
    )

    status = main(
        [
            "validate",
            "--region",
            "US",
            "--classification",
            "TEST",
            "--source-id",
            "source-a",
            "--exchange",
            "NASDAQ",
            "--database",
            str(database),
            str(csv_path),
        ]
    )

    output = capsys.readouterr().out
    assert status == 0
    assert "validated" in output.lower()
    assert "1" in output


def test_import_commits_with_review_metadata_and_refresh_is_gated(tmp_path: Path, capsys) -> None:
    database = tmp_path / "universe.sqlite"
    source = tmp_path / "members.csv"
    source.write_text(
        "Ticker,Name,Sector,Industry\nAAA,Alpha,Technology,Cloud\n",
        encoding="utf-8",
    )

    status = main(
        [
            "import",
            "--region",
            "US",
            "--classification",
            "TEST",
            "--source-id",
            "source-a",
            "--exchange",
            "NASDAQ",
            "--coverage",
            "reviewed sample",
            "--approval-reference",
            "review-1",
            "--database",
            str(database),
            str(source),
        ]
    )
    imported_output = capsys.readouterr().out
    refresh_status = main(
        [
            "refresh",
            "--region",
            "US",
            "--source-id",
            "live-source",
            "--database",
            str(database),
        ]
    )
    refresh_capture = capsys.readouterr()

    assert status == 0
    assert "committed" in imported_output.lower()
    assert "review-1" not in imported_output
    assert refresh_status != 0
    assert refresh_capture.out == ""
    assert "review" in refresh_capture.err.lower() or "approved" in refresh_capture.err.lower()


def test_represent_requires_matching_reviewed_source_and_adds_database_mapping(
    tmp_path: Path, capsys
) -> None:
    database = tmp_path / "universe.sqlite"
    source = tmp_path / "members.csv"
    source.write_text(
        "Ticker,Name,Sector,Industry\nAAA,Alpha,Technology,Cloud\n",
        encoding="utf-8",
    )
    assert (
        main(
            [
                "import",
                "--region",
                "US",
                "--classification",
                "TEST",
                "--source-id",
                "source-a",
                "--exchange",
                "NASDAQ",
                "--coverage",
                "reviewed sample",
                "--approval-reference",
                "review-1",
                "--database",
                str(database),
                str(source),
            ]
        )
        == 0
    )
    capsys.readouterr()

    status = main(
        [
            "represent",
            "--region",
            "US",
            "--classification",
            "TEST",
            "--entity-type",
            "industry",
            "--entity-id",
            "test-cloud",
            "--exchange",
            "NASDAQ",
            "--symbol",
            "AAA",
            "--source-id",
            "source-a",
            "--approval-reference",
            "review-1",
            "--effective-from",
            "2020-01-01",
            "--database",
            str(database),
        ]
    )

    assert status == 0
    assert "chart representation" in capsys.readouterr().out.lower()


def test_cli_rejects_missing_exchange_and_bad_input_with_nonzero_status(
    tmp_path: Path, capsys
) -> None:
    source = tmp_path / "members.csv"
    source.write_text(
        "Ticker,Name,Sector,Industry\nAAA,Alpha,Technology,Cloud\n",
        encoding="utf-8",
    )
    status = main(
        [
            "validate",
            "--region",
            "US",
            "--classification",
            "TEST",
            "--source-id",
            "source-a",
            "--database",
            str(tmp_path / "universe.sqlite"),
            str(source),
        ]
    )

    assert status != 0
    assert "exchange" in capsys.readouterr().err.lower()


def test_validate_cli_checks_selected_database_without_modifying_it(
    tmp_path: Path, capsys
) -> None:
    database = tmp_path / "universe.sqlite"
    original = tmp_path / "original.csv"
    original.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Technology,Cloud\n",
        encoding="utf-8",
    )
    assert (
        main(
            [
                "import",
                "--region",
                "US",
                "--classification",
                "TEST",
                "--source-id",
                "source-a",
                "--coverage",
                "reviewed",
                "--approval-reference",
                "review-1",
                "--database",
                str(database),
                str(original),
            ]
        )
        == 0
    )
    capsys.readouterr()
    conflicting = tmp_path / "conflicting.csv"
    conflicting.write_text(
        "InstrumentId,Ticker,Name,Exchange,Sector,Industry\n"
        "stock-a,AAA,Alpha,NASDAQ,Finance,Banks\n",
        encoding="utf-8",
    )

    status = main(
        [
            "validate",
            "--region",
            "US",
            "--classification",
            "TEST",
            "--source-id",
            "source-b",
            "--database",
            str(database),
            str(conflicting),
        ]
    )
    capture = capsys.readouterr()

    assert status != 0
    assert "conflict" in f"{capture.out} {capture.err}".lower()


def test_validate_cli_does_not_initialize_missing_database(
    tmp_path: Path, capsys
) -> None:
    database = tmp_path / "not-created.sqlite"
    source = tmp_path / "members.csv"
    source.write_text(
        "Ticker,Name,Sector,Industry\nAAA,Alpha,Technology,Cloud\n",
        encoding="utf-8",
    )

    status = main(
        [
            "validate",
            "--region",
            "US",
            "--classification",
            "TEST",
            "--source-id",
            "source-a",
            "--exchange",
            "NASDAQ",
            "--database",
            str(database),
            str(source),
        ]
    )

    assert status == 0
    assert not database.exists()
    assert "validated" in capsys.readouterr().out.lower()
