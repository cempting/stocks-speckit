import pandas as pd

from market_leadership.ui.performance_table import (
    industry_performance_frame,
    performance_table_height,
    style_performance_table,
)


def test_performance_table_height_fits_all_rows() -> None:
    assert performance_table_height(11) == 440


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
