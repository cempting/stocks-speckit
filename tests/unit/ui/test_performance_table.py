import re

import pandas as pd
import pytest

from market_leadership.ui.performance_table import (
    industry_performance_frame,
    performance_column_styles,
    performance_table_height,
    style_performance_table,
)


def test_performance_table_height_fits_all_rows() -> None:
    assert performance_table_height(11) == 440


@pytest.mark.parametrize(
    "dark_mode, gain, loss, neutral",
    [
        (False, "#5f9f75", "#d66d65", "#f4f6f5"),
        (True, "#166534", "#991b1b", "#18232d"),
    ],
)
def test_daily_palette_is_recognized_and_scaled_independently(
    dark_mode: bool, gain: str, loss: str, neutral: str
) -> None:
    frame = pd.DataFrame({"1 day": [2.0, -1.0, 0.0, None], "1 week": [200.0, -300.0, 10.0, -20.0]})
    html = style_performance_table(frame, dark_mode=dark_mode).set_uuid("daily").to_html()
    css = html.split("</style>", 1)[0]
    for row, color in enumerate((gain, loss, neutral)):
        block = next(
            block
            for selectors, block in re.findall(r"([^{}]+)\{([^{}]+)\}", css)
            if f"#T_daily_row{row}_col0" in selectors
        )
        assert f"background-color: {color}" in block
    styles = performance_column_styles(frame["1 day"], dark_mode=dark_mode)
    assert styles[-1] == ""
    assert all(
        color in style for color, style in zip((gain, loss, neutral), styles[:3], strict=True)
    )
    frame["1 week"] *= 1000
    changed_css = (
        style_performance_table(frame, dark_mode=dark_mode)
        .set_uuid("daily")
        .to_html()
        .split("</style>", 1)[0]
    )
    assert css == changed_css


def test_performance_table_uses_diverging_light_palette() -> None:
    frame = pd.DataFrame(
        {
            "Sector": ["Leading", "Flat", "Lagging"],
            "1 week": [8.0, 0.0, -4.0],
            "1 month": [4.0, None, -8.0],
        }
    )

    html = style_performance_table(frame, dark_mode=False).to_html()

    assert "background-color: #5f9f75" in html
    assert "background-color: #d66d65" in html
    assert "background-color: #f4f6f5" in html


def test_performance_table_uses_readable_dark_palette() -> None:
    frame = pd.DataFrame(
        {
            "Sector": ["Leading", "Lagging"],
            "1 week": [8.0, -4.0],
        }
    )

    html = style_performance_table(frame, dark_mode=True).to_html()

    assert "background-color: #166534" in html
    assert "background-color: #991b1b" in html
    assert "background-color: #18232d" in html
    assert "background-color: #22313d" in html
    assert "color: #edf3f7" in html


def test_industry_performance_frame_discloses_short_period_outcomes_and_evidence() -> None:
    entries = pd.DataFrame(
        {
            "node_id": ["US-SOFT", "US-HARDWARE", "US-UNKNOWN"],
            "name": ["Software", "Hardware", "Unknown"],
            "rank": [1, 2, None],
            "absolute_1w": [0.08, -0.02, None],
            "absolute_1m": [0.12, -0.04, None],
            "proxy_type": ["INDEX", "ETF", "NONE"],
            "observation_date": ["2026-10-23", "2026-10-23", None],
            "source_id": ["fixture", "fixture", "fixture"],
            "sufficiency": ["SUFFICIENT", "SUFFICIENT", "INSUFFICIENT"],
            "missing_reasons": ["", "", "MISSING_PROXY_HISTORY"],
        }
    )

    frame = industry_performance_frame(entries, parent_sector="Information Technology")

    assert frame.columns.tolist() == [
        "Industry",
        "Sector",
        "Rank",
        "1 week",
        "1 month",
        "Direction",
        "Proxy",
        "Observed",
        "Source",
        "Sufficiency",
        "Missing evidence",
    ]
    assert frame["Industry"].tolist() == ["Software", "Hardware", "Unknown"]
    assert frame["Direction"].tolist() == ["Gaining", "Declining", "Insufficient"]
    assert frame["Sector"].tolist() == ["Information Technology"] * 3
