import altair as alt
import pandas as pd

from market_data.domain.consolidation import ConsolidationInterval


def build_sector_chart(
    frame: pd.DataFrame,
    *,
    dark_mode: bool = False,
    max_rows: int | None = 260,
    consolidation_interval: ConsolidationInterval | None = None,
) -> alt.VConcatChart:
    background = "#111820" if dark_mode else "#f7f8f6"
    foreground = "#aebbc8" if dark_mode else "#64707d"
    grid = "#2c3a46" if dark_mode else "#dce2e7"
    close_color = "#7dd3fc" if dark_mode else "#17324d"
    sma_color = "#f4b860" if dark_mode else "#e09f3e"
    chart_data = frame.tail(max_rows) if max_rows is not None else frame
    chart_data = chart_data.reset_index(names="date")
    if "volume" not in chart_data.columns:
        chart_data["volume"] = float("nan")
    prior_close = chart_data["close"].shift()
    chart_data["volume_signal"] = "Neutral"
    chart_data.loc[chart_data["close"] > prior_close, "volume_signal"] = "Buy"
    chart_data.loc[chart_data["close"] < prior_close, "volume_signal"] = "Sell"
    price_series = ["close", "sma50"]
    color_domain = ["close", "sma50"]
    color_range = [close_color, sma_color]
    if "sma150" in chart_data.columns:
        price_series.append("sma150")
        color_domain.append("sma150")
        color_range.append("#a78bfa" if dark_mode else "#6a4c93")
    price_data = chart_data.melt(
        id_vars="date",
        value_vars=price_series,
        var_name="series",
        value_name="value",
    )
    price = (
        alt.Chart(price_data)
        .properties(mark=alt.MarkDef(type="line", strokeWidth=2))
        .encode(
            x=alt.X("date:T", axis=alt.Axis(title=None, labels=False, ticks=False)),
            y=alt.Y("value:Q", title="Price", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "series:N",
                title=None,
                scale=alt.Scale(
                    domain=color_domain,
                    range=color_range,
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
    if consolidation_interval is not None and not chart_data.empty:
        visible_start = pd.Timestamp(chart_data["date"].min()).date()
        visible_end = pd.Timestamp(chart_data["date"].max()).date()
        plot_start = max(consolidation_interval.start_session, visible_start)
        plot_end = min(consolidation_interval.end_session, visible_end)
        if plot_start <= plot_end:
            annotation = pd.DataFrame(
                [
                    {
                        "plot_start": pd.Timestamp(plot_start),
                        "plot_end": pd.Timestamp(plot_end),
                        "lower": consolidation_interval.lower,
                        "upper": consolidation_interval.upper,
                    }
                ]
            )
            shade = (
                alt.Chart(annotation)
                .properties(
                    mark=alt.MarkDef(
                        type="rect",
                        color="#38bdf8" if dark_mode else "#3b82f6",
                        opacity=0.1,
                    )
                )
                .encode(
                    x=alt.X("plot_start:T", axis=alt.Axis(title=None, labels=False, ticks=False)),
                    x2=alt.X2("plot_end:T"),
                    y=alt.Y("lower:Q", scale=alt.Scale(zero=False)),
                    y2=alt.Y2("upper:Q"),
                    tooltip=[
                        alt.Tooltip("lower:Q", title="Observed corridor low", format=",.2f"),
                        alt.Tooltip("upper:Q", title="Observed corridor high", format=",.2f"),
                    ],
                )
            )
            bounds = pd.DataFrame(
                [
                    {
                        "plot_start": pd.Timestamp(plot_start),
                        "plot_end": pd.Timestamp(plot_end),
                        "bound": bound,
                        "boundary": boundary,
                    }
                    for boundary, bound in (
                        ("Lower corridor", consolidation_interval.lower),
                        ("Upper corridor", consolidation_interval.upper),
                    )
                ]
            )
            corridor = (
                alt.Chart(bounds)
                .properties(
                    mark=alt.MarkDef(
                        type="rule",
                        color="#38bdf8" if dark_mode else "#2563eb",
                        strokeDash=[4, 3],
                        strokeWidth=1.5,
                    )
                )
                .encode(
                    x=alt.X("plot_start:T"),
                    x2=alt.X2("plot_end:T"),
                    y=alt.Y("bound:Q", scale=alt.Scale(zero=False)),
                    tooltip=[
                        alt.Tooltip("boundary:N", title="Boundary"),
                        alt.Tooltip("bound:Q", title="Observed price", format=",.2f"),
                    ],
                )
            )
            price = alt.layer(shade, corridor, price)
    volume = (
        alt.Chart(chart_data)
        .properties(mark=alt.MarkDef(type="bar", opacity=0.75))
        .encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("volume:Q", title="Volume", axis=alt.Axis(format="~s", tickCount=3)),
            color=alt.Color(
                "volume_signal:N",
                title="Volume signal",
                scale=alt.Scale(
                    domain=["Buy", "Sell", "Neutral"],
                    range=(
                        ["#22c55e", "#ef4444", "#8fb39b"]
                        if dark_mode
                        else ["#16a34a", "#dc2626", "#6f8f7b"]
                    ),
                ),
                legend=alt.Legend(orient="top", direction="horizontal"),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Session"),
                alt.Tooltip("volume:Q", title="Volume", format=","),
                alt.Tooltip("volume_signal:N", title="Volume signal"),
            ],
        )
        .properties(height=70)
    )
    return alt.vconcat(price, volume, spacing=4).properties(
        background=background,
        resolve=alt.Resolve(scale=alt.ScaleResolveMap(x="shared")),
        config=alt.Config(
            axis=alt.AxisConfig(
                domainColor=grid,
                gridColor=grid,
                labelColor=foreground,
                tickColor=grid,
                titleColor=foreground,
            ),
            legend=alt.LegendConfig(labelColor=foreground),
            view=alt.ViewConfig(stroke=None),
        ),
    )
