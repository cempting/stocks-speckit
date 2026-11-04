"""Standalone administration for versioned stock-catalog releases."""

import argparse
import json
import sys
from pathlib import Path

from market_data.catalog import (
    PublicationError,
    activate_release,
    initialize_store,
    load_release,
    recover_release,
)
from market_data.config import resolve_catalog_manifest
from market_data.domain.catalog import CatalogError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="market-catalog")
    commands = parser.add_subparsers(dest="command", required=True)

    catalog_init = commands.add_parser(
        "catalog-init", help="initialize an empty file catalog store"
    )
    catalog_init.add_argument("--directory", type=Path, required=True)

    catalog_validate = commands.add_parser(
        "validate-catalog", help="validate a captured file release without mutation"
    )
    catalog_validate.add_argument("--release-manifest", type=Path, required=True)

    catalog_activate = commands.add_parser(
        "activate-catalog", help="publish a complete reviewed file release"
    )
    catalog_activate.add_argument("--manifest", type=Path)
    catalog_activate.add_argument("--release-manifest", type=Path, required=True)
    catalog_activate.add_argument("--expected-release", required=True)

    catalog_recover = commands.add_parser(
        "recover-catalog", help="recover from known entry and release checksums"
    )
    catalog_recover.add_argument("--manifest", type=Path)
    catalog_recover.add_argument("--release-manifest", type=Path, required=True)
    catalog_recover.add_argument("--target-manifest-sha256", required=True)
    catalog_recover.add_argument("--expected-entry-sha256", required=True)
    return parser


def run_command(arguments: argparse.Namespace) -> int:
    report: dict[str, object] = {
        "report_version": "market-catalog-cli-1",
        "command": arguments.command,
        "status": "complete",
        "publication_state": "not_published",
        "catalog": None,
        "result": {},
    }
    try:
        if arguments.command == "catalog-init":
            initialize_store(arguments.directory)
            report["result"] = {"directory": str(arguments.directory.absolute())}
        elif arguments.command == "validate-catalog":
            snapshot = load_release(arguments.release_manifest)
            report["catalog"] = {
                "release_id": snapshot.release.release_id,
                "catalog_revision": snapshot.catalog_revision,
                "catalog_changed": False,
            }
            report["result"] = {
                "nodes": len(snapshot.nodes),
                "stock_rows": len(snapshot.stocks),
                "ledger_records": len(snapshot.ledger),
                "coverage": [
                    {"region_id": region.region_id, "state": region.coverage_state}
                    for region in snapshot.release.regions
                ],
            }
        else:
            entry = resolve_catalog_manifest(arguments.manifest)
            if arguments.command == "activate-catalog":
                result = activate_release(
                    entry,
                    arguments.release_manifest,
                    expected_release=(
                        None
                        if arguments.expected_release == "none"
                        else arguments.expected_release
                    ),
                )
            elif arguments.command == "recover-catalog":
                result = recover_release(
                    entry,
                    arguments.release_manifest,
                    target_sha256=arguments.target_manifest_sha256,
                    expected_entry_sha256=arguments.expected_entry_sha256,
                )
            else:
                raise ValueError(f"Unknown catalog command: {arguments.command}")
            report["publication_state"] = "published"
            report["catalog"] = {
                "release_id": result.release_id,
                "catalog_revision": result.catalog_revision,
                "catalog_changed": result.catalog_changed,
            }
            report["result"] = {"manifest_path": str(result.manifest_path)}
    except (CatalogError, OSError) as error:
        code = error.code if isinstance(error, CatalogError) else "catalog_io"
        state = (
            error.publication_state
            if isinstance(error, PublicationError)
            else "not_published"
        )
        report["publication_state"] = state
        report["status"] = (
            "indeterminate"
            if state == "unknown"
            else "conflict"
            if code in ("release_conflict", "writer_conflict", "entry_conflict")
            else "failed"
        )
        report["result"] = {"error_code": code}
        if isinstance(error, PublicationError) and error.operation_id is not None:
            report["result"] = {
                "error_code": code,
                "operation_id": error.operation_id,
                "expected_release": error.expected_release,
            }
        print(f"Catalog operation failed: {code}", file=sys.stderr)
        print(json.dumps(report, indent=2))
        return 2
    print(json.dumps(report, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    return run_command(_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
