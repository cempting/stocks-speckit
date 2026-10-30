from datetime import date

import pandas as pd
import pytest

from market_leadership.domain.industry_momentum import industry_momentum_frame


def test_industry_rows_show_sector_style_trend_columns() -> None:
    history = {
        "SOXX": pd.DataFrame(
            {"close": [100.0] * 299 + [105.0], "volume": [1_000] * 300},
            index=pd.date_range(end="2026-10-26", periods=300, freq="B"),
        )
    }

    frame = industry_momentum_frame(
        history,
        as_of=date(2026, 10, 26),
        sectors=("Information Technology",),
    )

    assert {
        "Industry",
        "Sector",
        "Representation",
        "1 week",
        "1 month",
        "3 months",
        "6 months",
        "12 months",
    } == set(frame.columns)
    assert frame.loc[frame["Industry"] == "Semiconductors", "1 month"].item() == pytest.approx(0.05)
    assert pd.isna(frame.loc[frame["Industry"] == "Software", "12 months"].item())
