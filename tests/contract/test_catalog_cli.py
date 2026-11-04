import json
from hashlib import sha256
from pathlib import Path

import pytest

from market_data.catalog import PublicationError
from market_data_tools.catalog_admin import main as catalog_admin_main
from market_leadership.universe_admin import main


@pytest.fixture(autouse=True)
def isolated_catalog_entry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "MARKET_CATALOG_MANIFEST_PATH", str(tmp_path / "default-store/CURRENT.json")
    )


def test_lifecycle_commands_do_not_initialize_sql(
    catalog_release: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("File lifecycle must never initialize SQL")

    monkeypatch.setattr("market_data_tools.legacy.universe_admin.RegionDatabase", forbidden)
    store = tmp_path / "catalog"
    assert main(["catalog-init", "--directory", str(store)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["report_version"] == "market-catalog-cli-1"
    assert report["publication_state"] == "not_published"
    assert not (store / "CURRENT.json").exists()
    before = {p.name: p.read_bytes() for p in catalog_release.parent.iterdir()}
    assert main(["validate-catalog", "--release-manifest", str(catalog_release)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "complete"
    assert before == {p.name: p.read_bytes() for p in catalog_release.parent.iterdir()}
    assert (
        main(
            [
                "activate-catalog",
                "--manifest",
                str(store / "CURRENT.json"),
                "--release-manifest",
                str(catalog_release),
                "--expected-release",
                "none",
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["publication_state"] == "published"
    assert report["catalog"]["catalog_changed"] is True
    assert (
        main(
            [
                "activate-catalog",
                "--manifest",
                str(store / "CURRENT.json"),
                "--release-manifest",
                str(catalog_release),
                "--expected-release",
                "none",
            ]
        )
        == 2
    )
    output = capsys.readouterr()
    report = json.loads(output.out)
    assert report["status"] == "conflict"
    assert report["publication_state"] == "not_published"
    assert "release_conflict" in output.err


def test_standalone_catalog_tool_validates_contract_without_legacy_commands(
    catalog_release: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        catalog_admin_main(
            ["validate-catalog", "--release-manifest", str(catalog_release)]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["report_version"] == "market-catalog-cli-1"
    assert report["status"] == "complete"
    assert report["catalog"]["release_id"]
    with pytest.raises(SystemExit) as error:
        catalog_admin_main(["init"])
    assert error.value.code == 2


def test_catalog_selection_cli_overrides_environment(
    catalog_release: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    environment = tmp_path / "env/CURRENT.json"
    monkeypatch.setenv("MARKET_CATALOG_MANIFEST_PATH", str(environment))
    explicit = tmp_path / "explicit/CURRENT.json"
    assert (
        main(
            [
                "activate-catalog",
                "--manifest",
                str(explicit),
                "--release-manifest",
                str(catalog_release),
                "--expected-release",
                "none",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert explicit.exists()
    assert not environment.exists()


def test_invalid_catalog_returns_truthful_bounded_report(
    catalog_release: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    catalog_release.write_text('{"format":"PRIVATE_PAYLOAD"}')
    assert main(["validate-catalog", "--release-manifest", str(catalog_release)]) == 2
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["status"] == "failed"
    assert report["publication_state"] == "not_published"
    assert "PRIVATE_PAYLOAD" not in captured.out + captured.err


def test_mutation_requires_expected_release(catalog_release: Path) -> None:
    with pytest.raises(SystemExit) as error:
        main(["activate-catalog", "--release-manifest", str(catalog_release)])
    assert error.value.code == 2


def test_uncertain_commit_is_never_reported_as_rollback(
    catalog_release: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def uncertain(*args: object, **kwargs: object) -> None:
        raise PublicationError("commit_indeterminate", publication_state="unknown")

    monkeypatch.setattr(
        "market_data_tools.catalog_admin.activate_release", uncertain
    )
    assert (
        main(
            [
                "activate-catalog",
                "--release-manifest",
                str(catalog_release),
                "--expected-release",
                "none",
            ]
        )
        == 2
    )
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "indeterminate"
    assert report["publication_state"] == "unknown"


def test_recovery_cli_verifies_both_hashes_and_records_receipt(
    catalog_release: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    entry = tmp_path / "store/CURRENT.json"
    assert main([
        "activate-catalog", "--manifest", str(entry), "--release-manifest", str(catalog_release),
        "--expected-release", "none",
    ]) == 0
    published = json.loads(capsys.readouterr().out)
    target = Path(published["result"]["manifest_path"])
    entry.write_bytes(b"CORRUPTED")
    assert main([
        "recover-catalog", "--manifest", str(entry), "--release-manifest", str(target),
        "--target-manifest-sha256", sha256(target.read_bytes()).hexdigest(),
        "--expected-entry-sha256", sha256(entry.read_bytes()).hexdigest(),
    ]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "complete"
    assert report["publication_state"] == "published"
    assert report["catalog"]["release_id"] != published["catalog"]["release_id"]
