"""Display the local-only Yahoo classification cache without making provider requests."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from market_data.catalog import CatalogSnapshot
from market_leadership.config import Settings
from market_leadership.infrastructure.yahoo_classifications import (
    YahooClassification,
    catalog_provider_symbols,
    read_classification_cache,
)


def render_yahoo_classification_preview(
    settings: Settings, *, snapshot: CatalogSnapshot
) -> None:
    st.subheader("Experimental Yahoo sector and industry labels")
    st.caption(
        "This is a local, point-in-time provider-label preview, not an official or reviewed "
        "classification. The checked-in catalog remains authoritative. Opening this view "
        "does not contact Yahoo."
    )
    cache_path = Path(settings.yahoo_classification_cache_path)
    try:
        cache = read_classification_cache(cache_path)
    except (OSError, ValueError) as error:
        st.error(f"Local Yahoo classification cache is unavailable or invalid: {error}")
        return

    active_symbols = catalog_provider_symbols(snapshot, as_of=date.today())
    active_set = set(active_symbols)
    matched = tuple(cache[symbol] for symbol in sorted(active_set.intersection(cache)))
    classified_count = sum(record.status == "classified" for record in matched)
    metrics = st.columns(3)
    metrics[0].metric("Active catalog symbols", len(active_symbols))
    metrics[1].metric("Locally cached symbols", f"{len(matched)} / {len(active_symbols)}")
    metrics[2].metric("With both labels", classified_count)

    if not matched:
        st.info(
            f"No current catalog symbols are cached at `{cache_path}`. From the repository "
            "root, run `uv run market-yahoo-classifications --limit 25` to fetch a bounded "
            "batch. The command stores results outside Git and skips already-cached symbols."
        )
        return

    frame = _classification_frame(matched)
    st.caption(
        f"Cache contains {len(cache)} symbols; {len(matched)} match the current active US "
        "catalog. Missing labels are shown as Unknown and are not inferred."
    )
    st.markdown("#### Cached sector and industry groups")
    groups = (
        frame.groupby(["sector", "industry"], as_index=False, dropna=False)
        .size()
        .rename(columns={"size": "cached_symbols"})
        .sort_values(["sector", "industry"], kind="stable")
    )
    st.write(groups)
    st.markdown("#### Cached symbol classifications")
    st.write(frame.sort_values(["sector", "industry", "symbol"], kind="stable"))


def _classification_frame(
    records: tuple[YahooClassification, ...],
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": record.provider_symbol,
                "status": record.status,
                "sector": record.sector or "Unknown",
                "industry": record.industry or "Unknown",
                "observed_at": record.observed_at.isoformat(),
            }
            for record in records
        ],
        columns=("symbol", "status", "sector", "industry", "observed_at"),
    )
