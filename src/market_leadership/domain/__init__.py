"""Compatibility imports for domain modules now owned by market_data."""

import importlib
import sys

for _name in (
    "catalog",
    "company_evidence",
    "fundamentals",
    "industry_etf_mappings",
    "industry_momentum",
    "industry_proxies",
    "industry_representations",
    "local_etf_evidence",
    "models",
    "peer_scores",
    "progressive_selection",
    "proxies",
    "rankings",
    "regimes",
    "relative_strength",
    "sector_performance",
    "stock_chart",
    "stock_selection",
):
    _module = importlib.import_module(f"market_data.domain.{_name}")
    sys.modules[f"{__name__}.{_name}"] = _module
    globals()[_name] = _module
