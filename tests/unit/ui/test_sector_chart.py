import pandas as pd

from market_leadership.ui.sector_chart import build_sector_chart


def test_sector_chart_uses_dark_mode_palette() -> None:
    index = pd.date_range("2026-01-01", periods=60, freq="B")
    frame = pd.DataFrame(
        {
            "close": range(100, 160),
            "sma50": range(95, 155),
            "volume": range(1_000_000, 1_000_060),
        },
        index=index,
    )

    specification = build_sector_chart(frame, dark_mode=True).to_dict()

    assert specification["background"] == "#111820"
    assert specification["vconcat"][0]["encoding"]["color"]["scale"]["range"] == [
        "#7dd3fc",
        "#f4b860",
    ]
    assert specification["config"]["axis"]["labelColor"] == "#aebbc8"
