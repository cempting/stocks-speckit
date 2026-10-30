from datetime import date

import pandas as pd

from market_leadership.domain.peer_scores import (
    BlockPeerScore,
    MetricPeerScore,
    PeerScorecard,
)
from market_leadership.ui.components.progressive_tape import (
    StockTapeRow,
    attach_chart_series,
    build_stock_tape_frame,
)


def _history(closes: tuple[float, ...]) -> pd.DataFrame:
    return pd.DataFrame(
        {"close": closes, "volume": [100.0] * len(closes)},
        index=pd.date_range("2026-10-19", periods=len(closes), freq="D"),
    )


def _scorecard(instrument_id: str) -> PeerScorecard:
    metric = MetricPeerScore("metric", 1.0, 62.5, 5, "available")
    quality = BlockPeerScore("Quality", 62.5, "available", (metric, metric))
    growth = BlockPeerScore("Growth", None, "insufficient", (metric, metric))
    cash_flow = BlockPeerScore("Cash Flow", None, "insufficient", (metric, metric))
    return PeerScorecard(instrument_id, quality, growth, cash_flow)


def test_chart_previews_are_joined_by_each_rows_own_identity():
    rows = pd.DataFrame({"ID": ["sector-a", "sector-b"]})

    result = attach_chart_series(
        rows,
        identity_column="ID",
        history_by_id={
            "sector-a": _history((1, 2, 3)),
            "sector-b": _history((10, 20, 30)),
        },
    )

    assert result["Chart"].tolist() == [[1, 2, 3], [10, 20, 30]]
    industries = attach_chart_series(
        pd.DataFrame({"Representation": ["AERO", "CLOUD"]}),
        identity_column="Representation",
        history_by_id={
            "AERO": _history((3, 2, 1)),
            "CLOUD": _history((30, 20, 10)),
        },
    )
    assert industries["Chart"].tolist() == [[3, 2, 1], [30, 20, 10]]


def test_stock_tape_contains_identity_price_and_three_explicit_score_states():
    frame = build_stock_tape_frame(
        (
            StockTapeRow(
                instrument_id="instrument-a",
                ticker="AAA",
                name="Alpha",
                history=_history((10, 12)),
                price_state="available",
                observed_on=date(2026, 10, 20),
                scorecard=_scorecard("instrument-a"),
                score_state="available",
            ),
            StockTapeRow(
                instrument_id="instrument-b",
                ticker="BBB",
                name="Beta",
                history=pd.DataFrame(columns=["close", "volume"]),
                price_state="unavailable",
                score_state="not_loaded",
            ),
        )
    )

    assert frame["Chart"].tolist() == [[10, 12], []]
    assert frame["Observed"].tolist() == ["2026-10-20", "Unavailable"]
    assert [frame[column].iloc[0] for column in ("Ticker", "Name", "Price")] == [
        "AAA",
        "Alpha",
        "12.00",
    ]
    assert [frame[column].iloc[0] for column in ("Quality", "Growth", "Cash Flow")] == [
        "62.5",
        "Insufficient",
        "Insufficient",
    ]
    assert [frame[column].iloc[1] for column in ("Ticker", "Name", "Price")] == [
        "BBB",
        "Beta",
        "Unavailable",
    ]
    assert [frame[column].iloc[1] for column in ("Quality", "Growth", "Cash Flow")] == [
        "Not loaded",
        "Not loaded",
        "Not loaded",
    ]
