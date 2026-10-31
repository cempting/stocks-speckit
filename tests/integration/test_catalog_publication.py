import fcntl
import json
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from threading import Barrier

import pytest

from market_leadership.domain.catalog import CatalogError
from market_leadership.infrastructure.catalog_files import (
    CatalogReader,
    PublicationError,
    activate_release,
    initialize_store,
    recover_release,
)


def test_bootstrap_copies_and_preserves_authoring_inputs(
    catalog_release: Path, tmp_path: Path
) -> None:
    store = tmp_path / "store"
    initialize_store(store)
    entry = store / "CURRENT.json"
    assert not entry.exists()
    before = {p.name: p.read_bytes() for p in catalog_release.parent.iterdir()}
    published = activate_release(entry, catalog_release, expected_release=None)
    snapshot = CatalogReader().read(entry)
    assert snapshot.release.release_id == published.release_id
    assert snapshot.release.parent_release is None
    assert snapshot.ledger[-1].record_id == published.release_id
    assert before == {p.name: p.read_bytes() for p in catalog_release.parent.iterdir()}
    for artifact in snapshot.release.artifacts:
        target = published.manifest_path.parent / artifact.path
        source = catalog_release.parent / artifact.path
        assert target.stat().st_ino != source.stat().st_ino


def test_expected_release_and_lock_conflicts(catalog_release: Path, tmp_path: Path) -> None:
    entry = tmp_path / "store/CURRENT.json"
    first = activate_release(entry, catalog_release, expected_release=None)
    before = entry.read_bytes()
    with pytest.raises(PublicationError, match="release_conflict"):
        activate_release(entry, catalog_release, expected_release=None)
    assert entry.read_bytes() == before
    with (entry.parent / ".writer.lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(PublicationError, match="writer_conflict"):
            activate_release(entry, catalog_release, expected_release=first.release_id)
    assert entry.read_bytes() == before


@pytest.mark.parametrize("point", ["staged", "release_renamed", "before_commit", "after_commit"])
def test_failure_outcomes_are_truthful(catalog_release: Path, tmp_path: Path, point: str) -> None:
    entry = tmp_path / "store/CURRENT.json"
    first = activate_release(entry, catalog_release, expected_release=None)
    before = entry.read_bytes()

    def fail(stage: str) -> None:
        if stage == point:
            raise OSError("controlled interruption")

    with pytest.raises(PublicationError) as error:
        activate_release(entry, first.manifest_path, expected_release=first.release_id, fault=fail)
    if point == "after_commit":
        assert error.value.publication_state == "unknown"
        assert entry.read_bytes() != before
        assert error.value.operation_id == CatalogReader().read(entry).release.release_id
    else:
        assert error.value.publication_state == "not_published"
        assert entry.read_bytes() == before
    assert CatalogReader().read(entry).release.release_id


def test_recovery_requires_raw_entry_and_reviewed_target_hash(
    catalog_release: Path, tmp_path: Path
) -> None:
    entry = tmp_path / "store/CURRENT.json"
    first = activate_release(entry, catalog_release, expected_release=None)
    entry.write_bytes(b'{"broken":true}')
    damaged = sha256(entry.read_bytes()).hexdigest()
    with pytest.raises(CatalogError):
        recover_release(
            entry,
            first.manifest_path,
            target_sha256="f" * 64,
            expected_entry_sha256=damaged,
        )
    result = recover_release(
        entry,
        first.manifest_path,
        target_sha256=sha256(first.manifest_path.read_bytes()).hexdigest(),
        expected_entry_sha256=damaged,
    )
    assert result.release_id != first.release_id
    snapshot = CatalogReader().read(entry)
    assert snapshot.ledger[-1].payload.action == "recovery"
    assert snapshot.release.parent_release.release_id == first.release_id
    assert json.loads(entry.read_text())["release_id"] == result.release_id


def test_recovery_never_discards_a_newer_valid_ledger(
    catalog_release: Path, tmp_path: Path
) -> None:
    entry = tmp_path / "store/CURRENT.json"
    first = activate_release(entry, catalog_release, expected_release=None)
    activate_release(entry, first.manifest_path, expected_release=first.release_id)
    before = entry.read_bytes()
    with pytest.raises(PublicationError, match="ledger_prefix_mismatch"):
        recover_release(
            entry,
            first.manifest_path,
            target_sha256=sha256(first.manifest_path.read_bytes()).hexdigest(),
            expected_entry_sha256=sha256(before).hexdigest(),
        )
    assert entry.read_bytes() == before


def test_research_only_publication_preserves_revision(
    catalog_release: Path, tmp_path: Path
) -> None:
    entry = tmp_path / "store/CURRENT.json"
    first = activate_release(entry, catalog_release, expected_release=None)
    second = activate_release(entry, first.manifest_path, expected_release=first.release_id)
    assert first.catalog_revision == second.catalog_revision
    assert not second.catalog_changed
    snapshot = CatalogReader().read(entry)
    assert snapshot.release.parent_release.release_id == first.release_id
    assert len(snapshot.ledger) == 5


def test_entry_change_during_staging_cannot_be_overwritten(
    catalog_release: Path, tmp_path: Path
) -> None:
    entry = tmp_path / "store/CURRENT.json"
    first = activate_release(entry, catalog_release, expected_release=None)

    def change_entry(point: str) -> None:
        if point == "before_commit":
            entry.write_bytes(b"EXTERNAL_EDIT")

    with pytest.raises(PublicationError, match="entry_conflict") as error:
        activate_release(
            entry, first.manifest_path, expected_release=first.release_id, fault=change_entry
        )
    assert error.value.publication_state == "not_published"
    assert entry.read_bytes() == b"EXTERNAL_EDIT"


def test_competing_publishers_have_exactly_one_commit(
    catalog_release: Path, tmp_path: Path
) -> None:
    entry = tmp_path / "store/CURRENT.json"
    first = activate_release(entry, catalog_release, expected_release=None)
    start = Barrier(2)

    def publish() -> str:
        start.wait(timeout=10)
        try:
            return activate_release(
                entry, first.manifest_path, expected_release=first.release_id
            ).release_id
        except PublicationError as error:
            assert error.code in ("writer_conflict", "release_conflict")
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as workers:
        outcomes = tuple(workers.map(lambda _: publish(), range(2)))
    assert outcomes.count("conflict") == 1
    selected = CatalogReader().read(entry)
    assert selected.release.release_id in outcomes
    assert selected.release.parent_release.release_id == first.release_id
    assert len(selected.ledger) == 5
