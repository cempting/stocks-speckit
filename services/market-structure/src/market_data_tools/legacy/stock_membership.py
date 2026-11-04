"""Eligibility helpers for legacy reviewed membership records."""

from market_data_tools.legacy.region_database import StockMembershipRecord


def verified_primary_provider_symbols(
    members: tuple[StockMembershipRecord, ...],
) -> tuple[str, ...]:
    symbols: list[str] = []
    for member in members:
        primary = member.primary_listing
        if (
            member.resolution_state == "identified"
            and primary is not None
            and primary.resolution_state == "verified"
        ):
            symbol = primary.provider_symbol or primary.symbol
            if symbol and symbol not in symbols:
                symbols.append(symbol)
    return tuple(symbols)
