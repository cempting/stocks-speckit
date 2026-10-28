from datetime import date

import pandas as pd
import pytest

from market_leadership.application.ports import DataPointRequest
from market_leadership.infrastructure.fixture_provider import FixtureProvider
from market_leadership.infrastructure.parquet_provider import ParquetSnapshotProvider
from market_leadership.infrastructure.parquet_repository import ParquetSnapshotRepository
from market_leadership.infrastructure.provider_validation import (
    canonicalize_daily_history,
    canonicalize_fx_rates,
)


@pytest.mark.parametrize(
    ("symbol", "first_session", "first_close", "last_close"),
    [
        ("SPX", date(2026, 1, 2), 5785.0, 6800.0),
        ("N225", date(2026, 1, 5), 51000.0, 51000.0),
        ("UKX", date(2026, 1, 2), 11040.0, 9400.0),
    ],
)
def test_fixture_local_benchmarks_follow_market_sessions_and_declared_closes(
    symbol: str, first_session: date, first_close: float, last_close: float
) -> None:
    history = FixtureProvider().fetch_daily_history(
        (symbol,), start=first_session, end=date(2026, 10, 23)
    )[symbol]

    assert history.index[0].date() == first_session
    assert history.index[-1].date() == date(2026, 10, 23)
    assert history["close"].iloc[0] == first_close
    assert history["close"].iloc[-1] == last_close
    assert history.attrs == {"source_id": "fixture", "available_on": "2026-10-23"}


@pytest.mark.parametrize("symbol", ["SPX", "N225", "UKX"])
def test_fixture_benchmarks_reject_dates_outside_effective_source_interval(
    symbol: str,
) -> None:
    provider = FixtureProvider()
    with pytest.raises(ValueError, match="outside its fixture benchmark availability"):
        provider.fetch_daily_history((symbol,), start=date(2024, 12, 31), end=date(2026, 10, 23))
    with pytest.raises(ValueError, match="outside its fixture benchmark availability"):
        provider.fetch_daily_history((symbol,), start=date(2026, 10, 23), end=date(2026, 10, 24))


@pytest.mark.parametrize(
    ("market_id", "symbol", "currency"),
    [("US", "SPX", "USD"), ("JP", "N225", "JPY"), ("GB", "UKX", "GBP")],
)
def test_fixture_capabilities_are_local_effective_and_source_bounded(
    market_id: str, symbol: str, currency: str
) -> None:
    capabilities = FixtureProvider.capabilities()

    def request(*, market: str, ticker: str, unit: str, session: date) -> DataPointRequest:
        return DataPointRequest(
            data_point="daily_history",
            market_id=market,
            identifiers=(ticker,),
            frequency="1d",
            start=session,
            end=session,
            currency=unit,
            return_basis="adjusted",
        )

    assert (
        sum(
            capability.covers(
                request(market=market_id, ticker=symbol, unit=currency, session=date(2026, 10, 23))
            )
            for capability in capabilities
        )
        == 1
    )
    for market, ticker, unit, session in (
        (market_id, symbol, currency, date(2024, 12, 31)),
        (market_id, symbol, currency, date(2026, 10, 24)),
        (market_id, symbol, "EUR", date(2026, 10, 23)),
        (market_id, "SPY" if market_id != "US" else "N225", currency, date(2026, 10, 23)),
    ):
        assert not any(
            capability.covers(request(market=market, ticker=ticker, unit=unit, session=session))
            for capability in capabilities
        )


def _parquet_provider(tmp_path) -> ParquetSnapshotProvider:
    repository = ParquetSnapshotRepository(tmp_path)
    repository.publish(
        snapshot_id="provider-contract",
        as_of=date(2026, 10, 24),
        markets=("US",),
        ruleset_version="1",
        tables={
            "prices": pd.DataFrame(
                {
                    "symbol": ["SPY", "XLB", "SPY", "SPY"],
                    "date": [
                        date(2026, 10, 24),
                        date(2026, 10, 22),
                        date(2026, 10, 22),
                        date(2026, 10, 20),
                    ],
                    "close": [102.0, 50.0, 101.0, 100.0],
                    "volume": [1_200.0, 500.0, 1_100.0, 1_000.0],
                }
            )
        },
        sources=(
            {
                "source_id": "fixture",
                "name": "Fixture",
                "dataset": "prices",
                "version": "1",
                "retrieved_at": "2026-10-24T12:00:00Z",
                "checksum": "a" * 64,
                "license_label": None,
            },
        ),
    )
    return ParquetSnapshotProvider(tmp_path, "provider-contract")


@pytest.mark.parametrize("provider_kind", ["fixture", "parquet"])
def test_daily_history_conformance_filters_dates_and_preserves_symbol_order(
    provider_kind: str, tmp_path
) -> None:
    provider = FixtureProvider() if provider_kind == "fixture" else _parquet_provider(tmp_path)

    history = provider.fetch_daily_history(
        ("XLB", "SPY"),
        start=date(2026, 10, 20),
        end=date(2026, 10, 23),
    )

    assert tuple(history) == ("XLB", "SPY")
    assert all(
        date(2026, 10, 20) <= session.date() <= date(2026, 10, 23)
        for frame in history.values()
        for session in frame.index
    )
    for frame in history.values():
        assert frame.index.is_monotonic_increasing
        assert frame.index.name == "date"
        assert list(frame.columns) == ["close", "volume"]
        assert frame["close"].dtype == "float64"
        assert frame["volume"].dtype == "float64"
        assert frame.attrs["source_id"] == provider.provider_id
        assert frame.attrs["available_on"] <= "2026-10-23"


@pytest.mark.parametrize("provider_kind", ["fixture", "parquet"])
def test_daily_history_conformance_returns_typed_empty_data_and_source_traceability(
    provider_kind: str, tmp_path
) -> None:
    provider = FixtureProvider() if provider_kind == "fixture" else _parquet_provider(tmp_path)
    history = provider.fetch_daily_history(
        ("SPY",),
        start=date(2026, 10, 25),
        end=date(2026, 10, 25),
    )["SPY"]

    assert list(history.columns) == ["close", "volume"]
    assert str(history["close"].dtype) == "float64"
    assert str(history["volume"].dtype) == "float64"
    assert history.empty
    assert history.attrs["source_id"] == provider.provider_id
    assert history.attrs["available_on"] is None


def test_fixture_history_availability_does_not_exceed_requested_as_of() -> None:
    history = FixtureProvider().fetch_daily_history(
        ("SPY",),
        start=date(2026, 10, 20),
        end=date(2026, 10, 23),
    )["SPY"]

    assert history.attrs["available_on"] <= "2026-10-23"


def test_provider_validation_rejects_conflicting_duplicate_dates() -> None:
    history = pd.DataFrame(
        {"close": [100.0, 101.0], "volume": [1_000.0, 1_100.0]},
        index=pd.to_datetime(["2026-10-23", "2026-10-23"]),
    )

    with pytest.raises(ValueError, match="duplicate dates"):
        canonicalize_daily_history(
            {"SPY": history},
            ("SPY",),
            start=date(2026, 10, 1),
            end=date(2026, 10, 31),
            source_id="fixture",
        )


def test_provider_validation_rejects_duplicate_requests_and_missing_schema() -> None:
    incomplete = pd.DataFrame(
        {"close": [100.0]},
        index=pd.to_datetime(["2026-10-23"]),
    )
    with pytest.raises(ValueError, match="symbols must be unique"):
        canonicalize_daily_history(
            {},
            ("SPY", "SPY"),
            start=date(2026, 10, 1),
            end=date(2026, 10, 31),
            source_id="fixture",
        )
    with pytest.raises(ValueError, match="lacks canonical columns"):
        canonicalize_daily_history(
            {"SPY": incomplete},
            ("SPY",),
            start=date(2026, 10, 1),
            end=date(2026, 10, 31),
            source_id="fixture",
        )


def test_fx_conformance_filters_as_of_and_availability_and_orders_canonically() -> None:
    rates = pd.DataFrame(
        {
            "date": ["2026-10-23", "2026-10-20", "2026-10-24", "2026-10-21"],
            "close": [1.08, 1.07, 1.09, 1.06],
            "available_on": [
                "2026-10-23",
                "2026-10-20",
                "2026-10-24",
                "2026-10-24",
            ],
        }
    )

    canonical = canonicalize_fx_rates(
        rates,
        base_currency="EUR",
        quote_currency="USD",
        as_of=date(2026, 10, 23),
        source_id="fixture-fx",
    )

    assert canonical["date"].tolist() == list(pd.to_datetime(["2026-10-20", "2026-10-23"]))
    assert canonical["close"].dtype == "float64"
    assert canonical["source_id"].tolist() == ["fixture-fx", "fixture-fx"]
    assert canonical["available_on"].tolist() == list(pd.to_datetime(["2026-10-20", "2026-10-23"]))
    assert canonical["base_currency"].tolist() == ["EUR", "EUR"]
    assert canonical["quote_currency"].tolist() == ["USD", "USD"]
    assert str(canonical["base_currency"].dtype) == "string"
    assert str(canonical["quote_currency"].dtype) == "string"
    assert str(canonical["source_id"].dtype) == "string"


def test_fx_conformance_uses_only_same_date_rates_without_forward_fill() -> None:
    rates = pd.DataFrame(
        {
            "date": ["2026-10-20", "2026-10-22"],
            "close": [1.07, 1.08],
            "available_on": ["2026-10-20", "2026-10-22"],
        }
    )
    canonical = canonicalize_fx_rates(
        rates,
        base_currency="EUR",
        quote_currency="USD",
        as_of=date(2026, 10, 22),
        source_id="fixture-fx",
    )
    price_dates = pd.DataFrame({"date": pd.to_datetime(["2026-10-20", "2026-10-21", "2026-10-22"])})

    joined = price_dates.merge(canonical[["date", "close"]], on="date", how="left")

    assert joined["close"].iloc[0] == 1.07
    assert pd.isna(joined["close"].iloc[1])
    assert joined["close"].iloc[2] == 1.08


def test_fx_conformance_returns_typed_empty_results_and_rejects_duplicates() -> None:
    empty = canonicalize_fx_rates(
        pd.DataFrame(
            {
                "date": pd.Series(dtype="datetime64[ns]"),
                "close": pd.Series(dtype="float64"),
                "available_on": pd.Series(dtype="datetime64[ns]"),
            }
        ),
        base_currency="EUR",
        quote_currency="USD",
        as_of=date(2026, 10, 23),
        source_id="fixture-fx",
    )

    assert list(empty.columns) == [
        "base_currency",
        "quote_currency",
        "date",
        "close",
        "source_id",
        "available_on",
    ]
    assert empty.empty
    assert empty["close"].dtype == "float64"
    assert str(empty["base_currency"].dtype) == "string"
    assert str(empty["quote_currency"].dtype) == "string"
    assert str(empty["source_id"].dtype) == "string"

    duplicate_rates = pd.DataFrame(
        {
            "date": ["2026-10-23", "2026-10-23"],
            "close": [1.07, 1.08],
            "available_on": ["2026-10-23", "2026-10-23"],
        }
    )
    with pytest.raises(ValueError, match="duplicate dates"):
        canonicalize_fx_rates(
            duplicate_rates,
            base_currency="EUR",
            quote_currency="USD",
            as_of=date(2026, 10, 23),
            source_id="fixture-fx",
        )


def test_fx_conformance_rejects_invalid_availability_and_currency() -> None:
    invalid_availability = pd.DataFrame(
        {
            "date": ["2026-10-23"],
            "close": [1.07],
            "available_on": ["2026-10-22"],
        }
    )
    with pytest.raises(ValueError, match="cannot precede"):
        canonicalize_fx_rates(
            invalid_availability,
            base_currency="EUR",
            quote_currency="USD",
            as_of=date(2026, 10, 23),
            source_id="fixture-fx",
        )
    with pytest.raises(ValueError, match="ISO 4217"):
        canonicalize_fx_rates(
            invalid_availability,
            base_currency="eur",
            quote_currency="USD",
            as_of=date(2026, 10, 23),
            source_id="fixture-fx",
        )
