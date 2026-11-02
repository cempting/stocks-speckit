"""Compatibility alias for the shared catalog store."""

import sys

from market_data import catalog

sys.modules[__name__] = catalog
