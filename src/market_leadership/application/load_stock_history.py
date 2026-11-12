"""Load canonical daily history for one selected industry's active members."""

from dataclasses import dataclass
from datetime import date, timedelta
from math import isfinite

import pandas as pd

from market_data.catalog import CatalogSnapshot
from market_data.domain.company_evidence import CompanyAssociation
from market_leadership.application.ports import MarketDataProvider


@dataclass(frozen=True, slots=True)
class StockHistorySeries:
    symbol: str
    history: pd.DataFrame
    observed_on: date | None
    state: str
    reason: str | None = None
    price_state: str = "unavailable"
    volume_state: str = "unavailable"
    unverifiable_intervals: tuple[tuple[date, date], ...] = ()


@dataclass(frozen=True, slots=True)
class StockHistoryBatch:
    provider_id: str
    requested_as_of: date
    series: tuple[StockHistorySeries, ...]


@dataclass(frozen=True, slots=True)
class ListingHistoryWindow:
    symbol: str
    requested_start: date
    eligible_start: date
    eligible_end: date
    unverifiable_intervals: tuple[tuple[date, date], ...]


def prepare_listing_history_window(
    catalog: CatalogSnapshot,
    association: CompanyAssociation,
    *,
    as_of: date,
    lookback_days: int = 550,
    require_primary: bool = True,
) -> tuple[ListingHistoryWindow | None, str | None]:
    if not 1 <= lookback_days <= 3650:
        raise ValueError("Selected history lookback must be between 1 and 3650 days")
    requested_start = as_of - timedelta(days=lookback_days)
    if (
        association.state not in ("verified", "unresolved")
        or association.binding_reference is None
        or not any((association.cik, association.issuer_domain, association.issuer_key))
        or association.catalog_revision != catalog.catalog_revision
        or not association.active_on(as_of)
    ):
        return None, "A current reviewed listing-to-issuer continuity binding is required."
    resolution = catalog.listing_for_instrument(
        association.region_id,
        association.instrument_id,
        as_of,
        listing_id=association.listing_id,
    )
    listing = resolution.listing
    if (
        resolution.state != "available"
        or listing is None
        or listing.instrument_type != "stock"
        or listing.resolution_state != "verified"
        or (require_primary and listing.is_primary is not True)
        or listing.provider_symbol != association.provider_symbol
        or listing.exchange != association.exchange
        or listing.currency != association.trading_currency
        or listing.period is None
    ):
        return None, "The selected listing is not eligible for this history request."
    eligible_start = max(association.effective_from, listing.period.start, requested_start)
    eligible_end = min(
        as_of,
        association.effective_to or as_of,
        listing.period.end or as_of,
    )
    if eligible_start > eligible_end:
        return None, "No reviewed listing/issuer continuity overlaps the requested history window."
    unverifiable: list[tuple[date, date]] = []
    if requested_start < eligible_start:
        unverifiable.append((requested_start, eligible_start - timedelta(days=1)))
    if eligible_end < as_of:
        unverifiable.append((eligible_end + timedelta(days=1), as_of))
    return (
        ListingHistoryWindow(
            symbol=association.provider_symbol,
            requested_start=requested_start,
            eligible_start=eligible_start,
            eligible_end=eligible_end,
            unverifiable_intervals=tuple(unverifiable),
        ),
        None,
    )


def load_stock_history(
    provider: MarketDataProvider,
    symbols: tuple[str, ...],
    *,
    as_of: date,
    force: bool = False,
) -> StockHistoryBatch:
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("Stock history requires a nonempty, duplicate-free member set")
    if any(not symbol or symbol != symbol.upper() for symbol in symbols):
        raise ValueError("Stock history symbols must be nonempty canonical uppercase symbols")
    requested_start = as_of - timedelta(days=550)
    requested = provider.fetch_daily_history(
        symbols,
        start=requested_start,
        end=as_of,
        force=force,
    )
    series: list[StockHistorySeries] = []
    for symbol in symbols:
        series.append(
            _series_from_response(
                symbol,
                requested.get(symbol),
                as_of=as_of,
                start=requested_start,
                end=as_of,
                history_truncated=True,
            )
        )
    return StockHistoryBatch(provider.provider_id, as_of, tuple(series))


def load_selected_listing_history(
    provider: MarketDataProvider,
    catalog: CatalogSnapshot,
    association: CompanyAssociation,
    *,
    as_of: date,
    lookback_days: int = 550,
    require_primary: bool = True,
    force: bool = False,
) -> StockHistoryBatch:
    window, failure = prepare_listing_history_window(
        catalog,
        association,
        as_of=as_of,
        lookback_days=lookback_days,
        require_primary=require_primary,
    )
    if window is None:
        return _unavailable_listing_history(
            provider.provider_id,
            association.provider_symbol,
            as_of,
            as_of - timedelta(days=lookback_days),
            failure or "Selected listing continuity is unavailable.",
        )
    if provider.provider_id != association.provider_id:
        return _unavailable_listing_history(
            provider.provider_id,
            window.symbol,
            as_of,
            window.requested_start,
            "The selected provider does not match the reviewed listing binding.",
        )
    history = provider.fetch_daily_history(
        (window.symbol,),
        start=window.eligible_start,
        end=window.eligible_end,
        force=force,
    ).get(window.symbol)
    projected = _series_from_response(
        window.symbol,
        history,
        as_of=window.eligible_end,
        start=window.eligible_start,
        end=window.eligible_end,
        history_truncated=True,
    )
    return StockHistoryBatch(
        provider.provider_id,
        as_of,
        (
            StockHistorySeries(
                symbol=projected.symbol,
                history=projected.history,
                observed_on=projected.observed_on,
                state=projected.state,
                reason=projected.reason,
                price_state=projected.price_state,
                volume_state=projected.volume_state,
                unverifiable_intervals=window.unverifiable_intervals,
            ),
        ),
    )


def _series_from_response(
    symbol: str,
    history: pd.DataFrame | None,
    *,
    as_of: date,
    start: date | None = None,
    end: date | None = None,
    history_truncated: bool = False,
) -> StockHistorySeries:
    empty = pd.DataFrame(columns=["close", "volume"], dtype="float64")
    if history is None or history.empty:
        return StockHistorySeries(
            symbol,
            empty,
            None,
            "unavailable",
            "The provider returned no history for this listing.",
        )
    dates = pd.DatetimeIndex(history.index).date
    mask = dates <= as_of
    if start is not None:
        mask &= dates >= start
    if end is not None:
        mask &= dates <= end
    optional_columns = [
        column for column in ("open", "high", "low", "split_ratio") if column in history.columns
    ]
    ordered_columns = [
        *[column for column in ("open", "high", "low") if column in optional_columns],
        "close",
        "volume",
    ]
    if "split_ratio" in optional_columns:
        ordered_columns.append("split_ratio")
    eligible = history.loc[mask].reindex(columns=ordered_columns).sort_index()
    eligible.attrs.update(history.attrs)
    eligible.attrs["history_truncated"] = (
        history_truncated or history.attrs.get("history_truncated") is True
    )
    if eligible.empty:
        return StockHistorySeries(
            symbol,
            empty,
            None,
            "unavailable",
            "The provider returned no observations inside the verified continuity window.",
        )
    if eligible.index.has_duplicates:
        return StockHistorySeries(
            symbol,
            empty,
            None,
            "insufficient",
            "The listing history contains duplicate observations.",
        )
    states: dict[str, str] = {}
    for column in ("close", "volume"):
        values = pd.to_numeric(eligible[column], errors="coerce")
        valid = values.map(lambda value: isfinite(float(value))) & (
            values > 0 if column == "close" else values >= 0
        )
        eligible[column] = values.where(valid)
        states[column] = "available" if valid.all() else "insufficient"
    complete = all(state == "available" for state in states.values())
    return StockHistorySeries(
        symbol,
        eligible,
        pd.DatetimeIndex(eligible.index)[-1].date(),
        "available" if complete else "insufficient",
        None if complete else "Close or volume evidence is incomplete; see series states.",
        states["close"],
        states["volume"],
    )


def _unavailable_listing_history(
    provider_id: str,
    symbol: str,
    as_of: date,
    requested_start: date,
    reason: str,
) -> StockHistoryBatch:
    return StockHistoryBatch(
        provider_id,
        as_of,
        (
            StockHistorySeries(
                symbol,
                pd.DataFrame(columns=["close", "volume"], dtype="float64"),
                None,
                "unavailable",
                reason,
                unverifiable_intervals=((requested_start, as_of),),
            ),
        ),
    )
