from datetime import date

import numpy as np
import pandas as pd


def canonicalize_daily_history(
    result: dict[str, pd.DataFrame],
    symbols: tuple[str, ...],
    *,
    start: date,
    end: date,
    source_id: str,
) -> dict[str, pd.DataFrame]:
    if end < start:
        raise ValueError("history end date must not precede its start")
    if len(set(symbols)) != len(symbols):
        raise ValueError("requested symbols must be unique")

    canonical: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        history = result.get(symbol)
        if history is None or history.empty:
            frame = _empty_history()
        else:
            if not {"close", "volume"}.issubset(history.columns):
                raise ValueError(f"Daily history for {symbol} lacks canonical columns")
            frame = history.loc[:, ["close", "volume"]].copy()
            index = pd.DatetimeIndex(frame.index)
            if index.tz is not None:
                index = index.tz_localize(None)
            index = index.normalize()
            if index.has_duplicates:
                raise ValueError(f"Daily history for {symbol} contains duplicate dates")
            frame.index = index
            frame.index.name = "date"
            frame = frame.loc[(frame.index.date >= start) & (frame.index.date <= end)].sort_index()
            frame = frame.astype({"close": "float64", "volume": "float64"})
            if not np.isfinite(frame["close"]).all() or (frame["close"] <= 0).any():
                raise ValueError(f"Daily history for {symbol} contains invalid close")
            if not np.isfinite(frame["volume"]).all() or (frame["volume"] < 0).any():
                raise ValueError(f"Daily history for {symbol} contains invalid volume")
        frame.attrs["source_id"] = source_id
        frame.attrs["available_on"] = (
            frame.index[-1].date().isoformat() if not frame.empty else None
        )
        canonical[symbol] = frame
    return canonical


def canonicalize_fx_rates(
    rates: pd.DataFrame,
    *,
    base_currency: str,
    quote_currency: str,
    as_of: date,
    source_id: str,
) -> pd.DataFrame:
    if not source_id.strip():
        raise ValueError("FX source ID must not be empty")
    for currency in (base_currency, quote_currency):
        if (
            len(currency) != 3
            or not currency.isascii()
            or not currency.isalpha()
            or not currency.isupper()
        ):
            raise ValueError("FX currencies must be uppercase three-letter ISO 4217 codes")
    required = {"date", "close", "available_on"}
    if not required.issubset(rates.columns):
        raise ValueError("FX rates lack canonical date, close, or available_on columns")

    canonical = rates.loc[:, ["date", "close", "available_on"]].copy()
    canonical["date"] = pd.to_datetime(canonical["date"], errors="raise").dt.normalize()
    canonical["available_on"] = pd.to_datetime(
        canonical["available_on"], errors="raise"
    ).dt.normalize()
    if canonical["date"].duplicated().any():
        raise ValueError("FX rates contain duplicate dates")
    if (canonical["available_on"] < canonical["date"]).any():
        raise ValueError("FX rate availability cannot precede its observation date")
    canonical = canonical.loc[
        (canonical["date"].dt.date <= as_of) & (canonical["available_on"].dt.date <= as_of)
    ].sort_values("date", kind="stable")
    canonical["close"] = canonical["close"].astype("float64")
    canonical["base_currency"] = pd.Series(base_currency, index=canonical.index, dtype="string")
    canonical["quote_currency"] = pd.Series(quote_currency, index=canonical.index, dtype="string")
    canonical["source_id"] = pd.Series(source_id, index=canonical.index, dtype="string")
    return canonical.loc[
        :,
        [
            "base_currency",
            "quote_currency",
            "date",
            "close",
            "source_id",
            "available_on",
        ],
    ].reset_index(drop=True)


def _empty_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "close": pd.Series(dtype="float64"),
            "volume": pd.Series(dtype="float64"),
        },
        index=pd.DatetimeIndex([], name="date"),
    )
