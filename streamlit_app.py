import os
from pathlib import Path
from runpy import run_module

from dotenv import load_dotenv

CATALOG_ENVIRONMENT_VARIABLE = "MARKET_CATALOG_MANIFEST_PATH"
DEFAULT_CATALOG = (
    Path(__file__).resolve().parent / "data" / "catalog-us-etf-clusters" / "CURRENT.json"
)


def configure_default_catalog() -> Path:
    load_dotenv(override=False)
    configured = os.getenv(CATALOG_ENVIRONMENT_VARIABLE, "").strip()
    if configured:
        return Path(configured).absolute()
    os.environ[CATALOG_ENVIRONMENT_VARIABLE] = str(DEFAULT_CATALOG)
    return DEFAULT_CATALOG


def main() -> None:
    configure_default_catalog()
    run_module("market_leadership.app", run_name="__main__")


if __name__ == "__main__":
    main()
