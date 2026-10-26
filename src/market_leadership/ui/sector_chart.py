import altair as alt
import pandas as pd


def build_sector_chart(frame: pd.DataFrame, *, dark_mode: bool = False) -> alt.VConcatChart:
    background = "#111820" if dark_mode else "#f7f8f6"
    foreground = "#aebbc8" if dark_mode else "#64707d"
    grid = "#2c3a46" if dark_mode else "#dce2e7"
    close_color = "#7dd3fc" if dark_mode else "#17324d"
    sma_color = "#f4b860" if dark_mode else "#e09f3e"
    volume_color = "#8fb39b" if dark_mode else "#6f8f7b"
    chart_data = frame.tail(260).reset_index(names="date")
    price_data = chart_data.melt(
        id_vars="date",
        value_vars=["close", "sma50"],
        var_name="series",
        value_name="value",
    )
    price = (
        alt.Chart(price_data)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("date:T", axis=alt.Axis(title=None, labels=False, ticks=False)),
            y=alt.Y("value:Q", title="Price", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "series:N",
                title=None,
                scale=alt.Scale(
                    domain=["close", "sma50"],
                    range=[close_color, sma_color],
                ),
                legend=alt.Legend(orient="top", direction="horizontal"),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Session"),
                alt.Tooltip("series:N", title="Series"),
                alt.Tooltip("value:Q", title="Value", format=",.2f"),
            ],
        )
        .properties(height=190)
    )
    volume = (
        alt.Chart(chart_data)
        .mark_bar(color=volume_color, opacity=0.75)
        .encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("volume:Q", title="Volume", axis=alt.Axis(format="~s", tickCount=3)),
            tooltip=[
                alt.Tooltip("date:T", title="Session"),
                alt.Tooltip("volume:Q", title="Volume", format=","),
            ],
        )
        .properties(height=70)
    )
    return (
        alt.vconcat(price, volume, spacing=4)
        .resolve_scale(x="shared")
        .properties(background=background)
        .configure_axis(
            domainColor=grid,
            gridColor=grid,
            labelColor=foreground,
            tickColor=grid,
            titleColor=foreground,
        )
        .configure_legend(labelColor=foreground)
        .configure_view(stroke=None)
    )
