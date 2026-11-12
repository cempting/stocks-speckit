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
            has_ohlc = {"open", "high", "low"}.issubset(history.columns)
            columns = (
                ["open", "high", "low", "close", "volume"]
                if has_ohlc
                else ["close", "volume"]
            )
            if "split_ratio" in history.columns:
                columns.append("split_ratio")
            frame = history.loc[:, columns].copy()
            index = pd.DatetimeIndex(frame.index)
            if index.tz is not None:
                index = index.tz_localize(None)
            index = index.normalize()
            if index.has_duplicates:
                raise ValueError(f"Daily history for {symbol} contains duplicate dates")
            frame.index = index
            frame.index.name = "date"
            mask = pd.Series((index.date >= start) & (index.date <= end), index=index)
            frame = frame.loc[mask].sort_index()
            frame = frame.astype({"close": "float64", "volume": "float64"})
            if not np.isfinite(frame["close"]).all() or (frame["close"] <= 0).any():
                raise ValueError(f"Daily history for {symbol} contains invalid close")
            if not np.isfinite(frame["volume"]).all() or (frame["volume"] < 0).any():
                raise ValueError(f"Daily history for {symbol} contains invalid volume")
            for column in ("open", "high", "low", "split_ratio"):
                if column not in frame.columns:
                    continue
                try:
                    frame[column] = pd.to_numeric(frame[column], errors="raise").astype(
                        "float64"
                    )
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"Daily history for {symbol} contains invalid {column}"
                    ) from error
                observed = frame[column].dropna()
                if not np.isfinite(observed).all() or (
                    column != "split_ratio" and (observed <= 0).any()
                ):
                    raise ValueError(f"Daily history for {symbol} contains invalid {column}")
                if column == "split_ratio" and (observed < 0).any():
                    raise ValueError(f"Daily history for {symbol} contains invalid split_ratio")
            if has_ohlc:
                complete_bars = frame[["open", "high", "low", "close"]].notna().all(axis=1)
                upper_bound = frame[["open", "low", "close"]].max(axis=1)
                lower_bound = frame[["open", "high", "close"]].min(axis=1)
                invalid_bars = complete_bars & (
                    (frame["high"] < upper_bound) | (frame["low"] > lower_bound)
                )
                if invalid_bars.any():
                    raise ValueError(f"Daily history for {symbol} contains inconsistent OHLC")
            if has_ohlc or "split_ratio" in frame.columns:
                frame.attrs["adjusted_ohlc"] = (
                    has_ohlc and history.attrs.get("adjusted_ohlc") is True
                )
                frame.attrs["volume_comparable"] = (
                    frame.attrs["adjusted_ohlc"]
                    and "split_ratio" in frame.columns
                    and history.attrs.get("volume_comparable") is True
                )
        frame.attrs["source_id"] = source_id
        frame.attrs["available_on"] = (
            pd.DatetimeIndex(frame.index)[-1].date().isoformat() if not frame.empty else None
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
    mask: pd.Series[bool] = (canonical["date"].dt.date <= as_of) & (
        canonical["available_on"].dt.date <= as_of
    )
    canonical = canonical.loc[mask].sort_values("date", kind="stable")
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
