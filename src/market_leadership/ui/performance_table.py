import pandas as pd
from pandas.io.formats.style import Styler

PERFORMANCE_COLUMNS = ("1 week", "1 month", "3 months", "6 months", "12 months")


def performance_table_height(row_count: int) -> int:
    return (row_count + 1) * 35 + 20


def _mix_color(start: str, end: str, amount: float) -> str:
    start_rgb = tuple(int(start[index : index + 2], 16) for index in (1, 3, 5))
    end_rgb = tuple(int(end[index : index + 2], 16) for index in (1, 3, 5))
    mixed = tuple(
        round(start_channel + (end_channel - start_channel) * amount)
        for start_channel, end_channel in zip(start_rgb, end_rgb, strict=True)
    )
    return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"


def _style_performance_column(values: pd.Series, *, dark_mode: bool) -> list[str]:
    numeric = values.astype("float64")
    finite = numeric.dropna()
    largest_gain = max(float(finite.max()), 0.0) if not finite.empty else 0.0
    largest_loss = abs(min(float(finite.min()), 0.0)) if not finite.empty else 0.0
    neutral = "#18232d" if dark_mode else "#f4f6f5"
    positive = "#166534" if dark_mode else "#5f9f75"
    negative = "#991b1b" if dark_mode else "#d66d65"
    foreground = "#edf3f7" if dark_mode else "#17212b"
    styles: list[str] = []

    for value in numeric:
        if pd.isna(value):
            styles.append("")
            continue
        if value > 0:
            amount = float(value) / largest_gain if largest_gain else 0.0
            background = _mix_color(neutral, positive, amount)
        elif value < 0:
            amount = abs(float(value)) / largest_loss if largest_loss else 0.0
            background = _mix_color(neutral, negative, amount)
        else:
            background = neutral
        styles.append(f"background-color: {background}; color: {foreground}")

    return styles


def style_performance_table(frame: pd.DataFrame, *, dark_mode: bool) -> Styler:
    background = "#18232d" if dark_mode else "#ffffff"
    header = "#22313d" if dark_mode else "#e9eeea"
    foreground = "#edf3f7" if dark_mode else "#17212b"
    styled = frame.style.set_properties(
        **{"background-color": background, "color": foreground}
    ).set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("background-color", header),
                    ("color", foreground),
                ],
            }
        ]
    )
    for column in PERFORMANCE_COLUMNS:
        if column in frame.columns:
            styled = styled.apply(
                _style_performance_column,
                dark_mode=dark_mode,
                subset=[column],
            )
    return styled
