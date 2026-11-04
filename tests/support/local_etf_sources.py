"""Explicit source selections for the controlled research fixtures."""

CATALOGS = (
    "sector_rotation=src/constants.py:US_INDUSTRY_ETFS",
    "sector_rotation=src/constants.py:EUROPE_INDUSTRY_ETFS",
    "analyzer=config.py:INDUSTRY_ETFS",
    "stockfinder=src/stockfinder/data.py:INDUSTRY_ETFS",
    "stockviewer=config.py:INDUSTRY_ETFS",
)
