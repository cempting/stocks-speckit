"""Compatibility entry point; new callers should use market_data_tools."""

from market_data_tools.catalog_admin import main

if __name__ == "__main__":
    raise SystemExit(main())
