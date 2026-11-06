from datetime import UTC, datetime
from pathlib import Path

import pytest

from market_data.catalog import CatalogReader
from market_leadership.infrastructure.yahoo_classifications import (
    YahooClassification,
    catalog_provider_symbols,
    classification_from_info,
    read_classification_cache,
    refresh_classification_cache,
    write_classification_cache,
)
from market_leadership.ui.workflows.yahoo_classification_preview import (
    _classification_frame,
)

ROOT = Path(__file__).parents[3]
DEFAULT_ENTRY = ROOT / "data" / "catalog-us-etf-clusters" / "CURRENT.json"
OBSERVED_AT = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)


def test_classification_from_info_preserves_labels_and_missing_states() -> None:
    classified = classification_from_info(
        " a ",
        {"sector": " Healthcare ", "industry": "Diagnostics & Research"},
        observed_at=OBSERVED_AT,
    )
    partial = classification_from_info(
        "AA",
        {"sector": "Basic Materials", "industry": None},
        observed_at=OBSERVED_AT,
    )
    unclassified = classification_from_info(
        "ABC",
        {"currency": "USD", "sector": "undefined", "industry": ""},
        observed_at=OBSERVED_AT,
    )
    unavailable = classification_from_info("AAN", {}, observed_at=OBSERVED_AT)

    assert classified == YahooClassification(
        "A", "classified", "Healthcare", "Diagnostics & Research", OBSERVED_AT
    )
    assert partial == YahooClassification("AA", "partial", "Basic Materials", None, OBSERVED_AT)
    assert unclassified == YahooClassification(
        "ABC", "unclassified", None, None, OBSERVED_AT
    )
    assert unavailable == YahooClassification("AAN", "no_metadata", None, None, OBSERVED_AT)


def test_classification_from_info_rejects_malformed_provider_values() -> None:
    with pytest.raises(TypeError, match="mapping"):
        classification_from_info("A", None)
    with pytest.raises(TypeError, match="sector"):
        classification_from_info("A", {"sector": 42})


def test_cache_round_trips_records_and_rejects_duplicate_symbols(tmp_path: Path) -> None:
    path = tmp_path / "cache" / "yahoo.json"
    records = {
        "A": YahooClassification(
            "A", "classified", "Healthcare", "Diagnostics & Research", OBSERVED_AT
        ),
        "AAN": YahooClassification("AAN", "no_metadata", None, None, OBSERVED_AT),
    }

    write_classification_cache(path, records)

    assert read_classification_cache(path) == records
    path.write_text(
        '{"schema_version":1,"records":['
        '{"provider_symbol":"A","status":"no_metadata","sector":null,'
        '"industry":null,"observed_at":"2026-11-04T12:00:00+00:00"},'
        '{"provider_symbol":"A","status":"no_metadata","sector":null,'
        '"industry":null,"observed_at":"2026-11-04T12:00:00+00:00"}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate symbols"):
        read_classification_cache(path)


def test_cache_rejects_unsupported_or_malformed_documents(tmp_path: Path) -> None:
    path = tmp_path / "cache.json"
    path.write_text('{"schema_version":2,"records":[]}', encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported schema"):
        read_classification_cache(path)


def test_preview_keeps_missing_labels_as_explicit_unknowns() -> None:
    frame = _classification_frame(
        (
            YahooClassification("AAN", "no_metadata", None, None, OBSERVED_AT),
            YahooClassification("AA", "partial", "Basic Materials", None, OBSERVED_AT),
        )
    )

    assert frame[["sector", "industry"]].to_dict("records") == [
        {"sector": "Unknown", "industry": "Unknown"},
        {"sector": "Basic Materials", "industry": "Unknown"},
    ]


def test_catalog_symbols_include_only_active_primary_us_listings() -> None:
    snapshot = CatalogReader().read(DEFAULT_ENTRY)

    symbols = catalog_provider_symbols(snapshot, as_of=datetime(2026, 11, 4).date())

    assert symbols == tuple(sorted(set(symbols)))
    assert "A" in symbols
    assert "AAN" in symbols


def test_refresh_is_bounded_incremental_and_preserves_failed_records(
    tmp_path: Path,
) -> None:
    snapshot = CatalogReader().read(DEFAULT_ENTRY)
    cache_path = tmp_path / "yahoo.json"

    first = refresh_classification_cache(
        snapshot,
        cache_path,
        symbols=("A",),
        fetch_info=lambda symbol: {
            "sector": "Healthcare",
            "industry": "Diagnostics & Research",
        },
        now=OBSERVED_AT,
        sleeper=lambda _: None,
    )

    def unexpected_fetch(_: str) -> dict[str, object]:
        pytest.fail("a cached symbol should not be fetched without --force")

    skipped = refresh_classification_cache(
        snapshot,
        cache_path,
        symbols=("A",),
        fetch_info=unexpected_fetch,
        now=OBSERVED_AT,
        sleeper=lambda _: None,
    )
    failed_refresh = refresh_classification_cache(
        snapshot,
        cache_path,
        symbols=("A",),
        fetch_info=lambda _: (_ for _ in ()).throw(RuntimeError("provider unavailable")),
        force=True,
        now=OBSERVED_AT,
        sleeper=lambda _: None,
    )

    assert first.attempted == first.stored == 1
    assert first.cache_size == 1
    assert skipped.attempted == skipped.stored == 0
    assert failed_refresh.attempted == 1
    assert failed_refresh.stored == 0
    assert failed_refresh.failures[0].error_type == "RuntimeError"
    assert read_classification_cache(cache_path)["A"].sector == "Healthcare"


def test_refresh_rejects_symbols_outside_the_active_catalog_and_oversized_batches(
    tmp_path: Path,
) -> None:
    snapshot = CatalogReader().read(DEFAULT_ENTRY)

    def fetch(_: str) -> dict[str, object]:
        return {"sector": "Technology", "industry": "Software"}

    with pytest.raises(ValueError, match="not active primary US"):
        refresh_classification_cache(
            snapshot, tmp_path / "cache.json", symbols=("NOT-A-TICKER",), fetch_info=fetch
        )
    with pytest.raises(ValueError, match="limit"):
        refresh_classification_cache(
            snapshot, tmp_path / "cache.json", fetch_info=fetch, limit=101
        )
