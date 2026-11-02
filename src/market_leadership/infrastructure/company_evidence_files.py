"""Compatibility alias for the shared issuer-evidence store."""

import sys

from market_data import company_evidence

sys.modules[__name__] = company_evidence
