import pandas as pd

from market_leadership.ui.performance_table import (
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
