"""Compatibility entry point; new callers should use market_data_tools."""

from market_data_tools.company_evidence_admin import main

if __name__ == "__main__":
    raise SystemExit(main())
