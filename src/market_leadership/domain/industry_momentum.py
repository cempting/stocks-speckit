"""Qualified US industry ETF representations and their live momentum projection."""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from market_leadership.domain.sector_performance import (
    InsufficientHistoryError,
    calculate_absolute_performance,
)


@dataclass(frozen=True, slots=True)
class IndustryRepresentation:
    industry_id: str
    industry_name: str
    sector: str
    symbol: str


INDUSTRY_REPRESENTATIONS: tuple[IndustryRepresentation, ...] = (
    IndustryRepresentation("US-AERO", "Aerospace & Defense", "Industrials", "ITA"),
    IndustryRepresentation("US-AIRLINES", "Airlines", "Industrials", "JETS"),
    IndustryRepresentation("US-BANKS", "Banks", "Financials", "KBE"),
    IndustryRepresentation("US-BROKER-DEALERS", "Broker-Dealers", "Financials", "IAI"),
    IndustryRepresentation("US-CAPITAL-MARKETS", "Capital Markets", "Financials", "KCE"),
    IndustryRepresentation("US-CLOUD-COMPUTING", "Cloud Computing", "Information Technology", "SKYY"),
    IndustryRepresentation("US-COPPER-MINERS", "Copper Miners", "Materials", "COPX"),
    IndustryRepresentation("US-CYBERSECURITY", "Cybersecurity", "Information Technology", "CIBR"),
    IndustryRepresentation("US-ENERGY-INFRASTRUCTURE", "Energy Infrastructure", "Energy", "AMLP"),
    IndustryRepresentation("US-OIL-REFINING", "Oil Refining", "Energy", "CRAK"),
    IndustryRepresentation("US-REGIONAL-BANKS", "Regional Banks", "Financials", "KRE"),
    IndustryRepresentation("US-BIOTECH", "Biotechnology", "Health Care", "IBB"),
    IndustryRepresentation("US-ENERGY", "Oil & Gas Exploration", "Energy", "XOP"),
    IndustryRepresentation("US-ENERGY-SERVICES", "Oil & Gas Equipment & Services", "Energy", "XES"),
    IndustryRepresentation("US-GOLD-MINERS", "Gold Miners", "Materials", "GDX"),
    IndustryRepresentation("US-HOMEBUILDERS", "Homebuilders", "Consumer Discretionary", "XHB"),
    IndustryRepresentation("US-HEALTHCARE-PROVIDERS", "Health Care Providers", "Health Care", "IHF"),
    IndustryRepresentation("US-INSURANCE", "Insurance", "Financials", "KIE"),
    IndustryRepresentation("US-INDUSTRIAL-REITS", "Industrial REITs", "Real Estate", "INDS"),
    IndustryRepresentation("US-MEDICAL-DEVICES", "Medical Devices", "Health Care", "IHI"),
    IndustryRepresentation("US-MEDIA", "Media", "Communication Services", "PBS"),
    IndustryRepresentation("US-METALS", "Metals & Mining", "Materials", "XME"),
    IndustryRepresentation("US-MORTGAGE-REITS", "Mortgage REITs", "Real Estate", "REM"),
    IndustryRepresentation("US-PHARMACEUTICALS", "Pharmaceuticals", "Health Care", "XPH"),
    IndustryRepresentation("US-RETAIL", "Retail", "Consumer Discretionary", "XRT"),
    IndustryRepresentation("US-SEMICONDUCTORS", "Semiconductors", "Information Technology", "SOXX"),
    IndustryRepresentation("US-SILVER-MINERS", "Silver Miners", "Materials", "SIL"),
    IndustryRepresentation("US-SOFTWARE", "Software", "Information Technology", "IGV"),
    IndustryRepresentation("US-STEEL", "Steel", "Materials", "SLX"),
    IndustryRepresentation("US-TELECOM", "Telecommunications", "Communication Services", "XTL"),
)


def industry_symbols() -> tuple[str, ...]:
    return tuple(representation.symbol for representation in INDUSTRY_REPRESENTATIONS)


def industry_momentum_frame(
    history: dict[str, pd.DataFrame],
    *,
    as_of: date,
    sectors: tuple[str, ...],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    selected_sectors = set(sectors)
    for representation in INDUSTRY_REPRESENTATIONS:
        if selected_sectors and representation.sector not in selected_sectors:
            continue
        frame = history.get(representation.symbol)
        closes = (
            frame.loc[pd.DatetimeIndex(frame.index).date <= as_of, "close"]
            if frame is not None and not frame.empty
            else pd.Series(dtype="float64")
        )
        try:
            performance = (
                calculate_absolute_performance(closes, as_of=as_of)
                if not closes.empty
                else {"1w": None, "1m": None, "3m": None, "6m": None, "12m": None}
            )
        except InsufficientHistoryError:
            performance = {"1w": None, "1m": None, "3m": None, "6m": None, "12m": None}
        rows.append(
            {
                "Industry": representation.industry_name,
                "Sector": representation.sector,
                "Representation": representation.symbol,
                "1 week": performance["1w"],
                "1 month": performance["1m"],
                "3 months": performance["3m"],
                "6 months": performance["6m"],
                "12 months": performance["12m"],
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["Industry", "Representation"], kind="stable").reset_index(drop=True)
