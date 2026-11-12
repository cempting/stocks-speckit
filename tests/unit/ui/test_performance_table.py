import re

import pandas as pd
import pytest

from market_leadership.ui.performance_table import (
    industry_performance_frame,
    performance_column_styles,
    performance_table_height,
    style_performance_table,
)


def _contrast_ratio(foreground: str, background: str) -> float:
    def luminance(color: str) -> float:
        channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return sum(
            weight * channel
            for weight, channel in zip((0.2126, 0.7152, 0.0722), linear, strict=True)
        )

    lighter, darker = sorted(
        (luminance(foreground), luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_performance_table_height_fits_all_rows() -> None:
    assert performance_table_height(11) == 440


@pytest.mark.parametrize("dark_mode", [False, True])
def test_generated_return_palette_meets_wcag_aa(
    dark_mode: bool,
) -> None:
    values = pd.Series(range(-10000, 10001), dtype="float64")
    styles = performance_column_styles(values, dark_mode=dark_mode)
    pairs = {
        (foreground, background)
        for background, foreground in re.findall(
            r"background-color: (#[0-9a-f]{6}); color: (#[0-9a-f]{6})",
            " ".join(styles),
        )
    }

    assert len(pairs) > 3
    for foreground, background in pairs:
        ratio = _contrast_ratio(foreground, background)
        assert ratio >= 4.5, f"{foreground} on {background} has contrast {ratio:.2f}:1"
        assert ratio >= 3.0, f"{foreground} on {background} has contrast {ratio:.2f}:1"

    frame = pd.DataFrame({"1 day": [1.0, -1.0, 0.0]})
    html = style_performance_table(frame, dark_mode=dark_mode).to_html()
    for value in ("1.0", "-1.0", "0.0"):
        assert value in html


@pytest.mark.parametrize("year_column", ["1 year", "12 months"])
@pytest.mark.parametrize("dark_mode", [False, True])
def test_yearly_and_legacy_frames_retain_performance_styles(
    year_column: str, dark_mode: bool
) -> None:
    frame = pd.DataFrame({year_column: [8.0, -4.0, 0.0, None]})
    html = style_performance_table(frame, dark_mode=dark_mode).to_html()
    assert f">{year_column}</th>" in html
    for color in (
        ("#166534", "#991b1b", "#18232d")
        if dark_mode else ("#5f9f75", "#d66d65", "#f4f6f5")
    ):
        assert f"background-color: {color}" in html


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
