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


def test_sector_chart_colors_volume_by_close_direction() -> None:
    index = pd.date_range("2026-01-01", periods=4, freq="B")
    frame = pd.DataFrame(
        {
            "close": [100, 105, 101, 101],
            "sma50": [100, 101, 102, 103],
            "volume": [1_000_000, 1_100_000, 900_000, 800_000],
        },
        index=index,
    )

    specification = build_sector_chart(frame).to_dict()
    volume_specification = specification["vconcat"][1]

    assert volume_specification["encoding"]["color"]["field"] == "volume_signal"
    assert volume_specification["encoding"]["color"]["scale"] == {
        "domain": ["Buy", "Sell", "Neutral"],
        "range": ["#16a34a", "#dc2626", "#6f8f7b"],
    }
    assert volume_specification["encoding"]["tooltip"][2]["field"] == "volume_signal"
    volume_data_name = volume_specification["data"]["name"]
    assert [row["volume_signal"] for row in specification["datasets"][volume_data_name]] == [
        "Neutral",
        "Buy",
        "Sell",
        "Neutral",
    ]
