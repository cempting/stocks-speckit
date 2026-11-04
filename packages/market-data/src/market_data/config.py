"""Data-store locations shared by readers and maintenance tools."""

import os
from pathlib import Path

from dotenv import load_dotenv


def resolve_catalog_manifest(path: Path | None = None) -> Path:
    load_dotenv(override=False)
    if path is not None:
        return path.absolute()
    configured = os.getenv("MARKET_CATALOG_MANIFEST_PATH", "").strip()
    return Path(configured or ".data/catalog/CURRENT.json").absolute()


def resolve_company_evidence_root(path: Path | None = None) -> Path:
    load_dotenv(override=False)
    if path is not None:
        return path
    return Path(os.getenv("COMPANY_EVIDENCE_ROOT", ".data/company-evidence"))
