from datetime import date

import pandas as pd
import pytest

from market_leadership.domain.industry_momentum import (
    IndustryRepresentation,
    industry_momentum_frame,
    industry_symbols,
)

REPRESENTATIONS = (
    IndustryRepresentation("cloud", "Cloud Computing", "Information Technology", "SKYY"),
    IndustryRepresentation("cyber", "Cybersecurity", "Information Technology", "CIBR"),
    IndustryRepresentation("homes", "Homebuilders", "Consumer Discretionary", "XHB"),
    IndustryRepresentation("retail", "Retail", "Consumer Discretionary", "XRT"),
    IndustryRepresentation("semis", "Semiconductors", "Information Technology", "SOXX"),
    IndustryRepresentation("software", "Software", "Information Technology", "IGV"),
)


def _trend_history(final_close: float) -> pd.DataFrame:
    closes = [100.0] * 299 + [final_close]
    return pd.DataFrame(
        {"close": closes, "volume": [1_000] * len(closes)},
        index=pd.date_range(end="2026-10-26", periods=len(closes), freq="B"),
    )


def test_industry_symbols_require_explicit_representations_and_deduplicate() -> None:
    representations = {
        representation.industry_name: (representation.sector, representation.symbol)
        for representation in REPRESENTATIONS
    }

    assert representations["Cloud Computing"] == ("Information Technology", "SKYY")
    assert representations["Cybersecurity"] == ("Information Technology", "CIBR")
    assert representations["Homebuilders"] == ("Consumer Discretionary", "XHB")
    assert industry_symbols(()) == ()
    assert industry_symbols(REPRESENTATIONS + (REPRESENTATIONS[0],)) == (
        "SKYY",
        "CIBR",
        "XHB",
        "XRT",
        "SOXX",
        "IGV",
    )


def test_industry_momentum_shows_sector_style_trends_for_selected_sectors() -> None:
    history = {
        "SOXX": _trend_history(110),
        "IGV": _trend_history(110),
        "XRT": _trend_history(90),
        "XHB": _trend_history(120),
    }

    frame = industry_momentum_frame(
        history,
        as_of=date(2026, 10, 26),
        sectors=("Information Technology", "Consumer Discretionary"),
        representations=REPRESENTATIONS,
    )

    assert frame["Industry"].tolist() == [
        "Cloud Computing",
        "Cybersecurity",
        "Homebuilders",
        "Retail",
        "Semiconductors",
        "Software",
    ]
    assert frame.columns.tolist() == [
        "Industry",
        "Sector",
        "Representation",
        "ETF",
        "Evidence state",
        "1 week",
        "1 month",
        "3 months",
        "6 months",
        "12 months",
    ]
    assert frame.loc[frame["Industry"] == "Homebuilders", "1 week"].item() == pytest.approx(0.2)
    assert frame.loc[frame["Industry"] == "Retail", "12 months"].item() == pytest.approx(-0.1)
    assert frame.loc[frame["Industry"] == "Semiconductors", "3 months"].item() == pytest.approx(0.1)
    assert pd.isna(frame.loc[frame["Industry"] == "Cloud Computing", "1 week"].item())
    assert pd.isna(frame.loc[frame["Industry"] == "Cybersecurity", "12 months"].item())


def test_reviewed_basket_momentum_is_weighted_constituent_returns_only() -> None:
    from decimal import Decimal

    from market_leadership.domain.industry_representations import (
        BasketConstituent,
        ReviewedRepresentation,
        representation_performance,
    )

    basket = ReviewedRepresentation(
        representation_id="basket",
        node_id="cloud",
        kind="basket",
        name="Cloud basket",
        source_id="source",
        approval_reference="review",
        effective_from=date(2020, 1, 1),
        constituents=(
            BasketConstituent("a", "AAA", Decimal("60")),
            BasketConstituent("b", "BBB", Decimal("40")),
        ),
    )
    history = {"AAA": _trend_history(110), "BBB": _trend_history(90), "XLK": _trend_history(200)}
    result = representation_performance(basket, history, as_of=date(2026, 10, 26))
    assert all(value == pytest.approx(0.02) for value in result.values())
    with pytest.raises(ValueError, match="BBB"):
        representation_performance(
            basket, {"AAA": history["AAA"], "XLK": history["XLK"]}, as_of=date(2026, 10, 26)
        )


def test_inactive_and_invalid_representations_never_produce_momentum() -> None:
    from market_leadership.domain.industry_representations import (
        ReviewedRepresentation,
        representation_performance,
    )

    for overrides in ({"effective_to": date(2025, 1, 1)}, {"reason": "Invalid listing"}):
        representation = ReviewedRepresentation(
            representation_id="etf",
            node_id="cloud",
            kind="etf",
            name="AAA",
            source_id="source",
            approval_reference="review",
            effective_from=date(2020, 1, 1),
            symbol="AAA",
            **overrides,
        )
        with pytest.raises(ValueError):
            representation_performance(
                representation, {"AAA": _trend_history(110)}, as_of=date(2026, 10, 26)
            )
