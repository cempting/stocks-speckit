from datetime import date

import pandas as pd
import pytest

from market_leadership.domain.industry_momentum import (
    INDUSTRY_REPRESENTATIONS,
    industry_momentum_frame,
    industry_symbols,
)


def _trend_history(final_close: float) -> pd.DataFrame:
    closes = [100.0] * 299 + [final_close]
    return pd.DataFrame(
        {"close": closes, "volume": [1_000] * len(closes)},
        index=pd.date_range(end="2026-10-26", periods=len(closes), freq="B"),
    )


def test_industry_catalog_includes_focused_representations_across_added_sectors() -> None:
    representations = {
        representation.industry_name: (representation.sector, representation.symbol)
        for representation in INDUSTRY_REPRESENTATIONS
    }

    assert representations["Banks"] == ("Financials", "KBE")
    assert representations["Broker-Dealers"] == ("Financials", "IAI")
    assert representations["Capital Markets"] == ("Financials", "KCE")
    assert representations["Cloud Computing"] == ("Information Technology", "SKYY")
    assert representations["Copper Miners"] == ("Materials", "COPX")
    assert representations["Cybersecurity"] == ("Information Technology", "CIBR")
    assert representations["Energy Infrastructure"] == ("Energy", "AMLP")
    assert representations["Gold Miners"] == ("Materials", "GDX")
    assert representations["Oil & Gas Equipment & Services"] == ("Energy", "XES")
    assert representations["Homebuilders"] == ("Consumer Discretionary", "XHB")
    assert representations["Health Care Providers"] == ("Health Care", "IHF")
    assert representations["Industrial REITs"] == ("Real Estate", "INDS")
    assert representations["Medical Devices"] == ("Health Care", "IHI")
    assert representations["Media"] == ("Communication Services", "PBS")
    assert representations["Mortgage REITs"] == ("Real Estate", "REM")
    assert representations["Oil Refining"] == ("Energy", "CRAK")
    assert representations["Pharmaceuticals"] == ("Health Care", "XPH")
    assert representations["Silver Miners"] == ("Materials", "SIL")
    assert representations["Steel"] == ("Materials", "SLX")
    assert representations["Telecommunications"] == ("Communication Services", "XTL")
    assert len(INDUSTRY_REPRESENTATIONS) == len(industry_symbols())
    assert len({representation.industry_id for representation in INDUSTRY_REPRESENTATIONS}) == len(
        INDUSTRY_REPRESENTATIONS
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
