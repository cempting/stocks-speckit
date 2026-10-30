"""Command-line administration for reviewed regional stock-universe data."""

import argparse
import sys
from datetime import date
from pathlib import Path

from market_leadership.infrastructure.region_database import RegionDatabase
from market_leadership.infrastructure.universe_import import (
    ImportReport,
    import_reviewed_file,
    validate_import,
)


def _database_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="SQLite database path (default: .data/market-universe.sqlite)",
    )


def _source_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--region", required=True)
    parser.add_argument("--classification", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--exchange")
    parser.add_argument("input", type=Path)
    _database_argument(parser)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="market-universe")
    commands = parser.add_subparsers(dest="command", required=True)

    initialize = commands.add_parser("init", help="initialize the regional universe database")
    _database_argument(initialize)

    validate = commands.add_parser("validate", help="validate a reviewed CSV or JSON file")
    _source_arguments(validate)

    import_command = commands.add_parser("import", help="import reviewed local membership")
    import_command.add_argument("--coverage", required=True)
    import_command.add_argument("--approval-reference", required=True)
    _source_arguments(import_command)

    representation = commands.add_parser(
        "represent", help="add a reviewed chart representation for a sector or industry"
    )
    representation.add_argument("--region", required=True)
    representation.add_argument("--classification", required=True)
    representation.add_argument("--entity-type", choices=("sector", "industry"), required=True)
    representation.add_argument("--entity-id", required=True)
    representation.add_argument("--exchange", required=True)
    representation.add_argument("--symbol", required=True)
    representation.add_argument("--source-id", required=True)
    representation.add_argument("--approval-reference", required=True)
    representation.add_argument("--effective-from", type=date.fromisoformat, required=True)
    representation.add_argument("--effective-to", type=date.fromisoformat)
    _database_argument(representation)

    refresh = commands.add_parser("refresh", help="refresh through the approved live provider")
    refresh.add_argument("--region", required=True)
    refresh.add_argument("--source-id", required=True)
    _database_argument(refresh)
    return parser


def _print_report(report: ImportReport) -> None:
    print(
        f"{report.status}: rows={report.row_count}, accepted={report.accepted_rows}, "
        f"inserted={report.inserted_rows}, placeholders={report.placeholder_rows}, "
        f"unclassified={report.unclassified_rows}, conflicts={report.conflicting_rows}"
    )
    for issue in report.issues:
        row = f"row {issue.source_row}" if issue.source_row is not None else "input"
        entity = f" ({issue.entity_id})" if issue.entity_id else ""
        print(f"{issue.severity.upper()} {row}{entity}: {issue.detail}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    database = RegionDatabase(arguments.database)
    try:
        if arguments.command == "init":
            database.initialize()
            print(f"Initialized regional database: {database.path} (schema {1})")
            return 0
        if arguments.command == "validate":
            report = validate_import(
                arguments.input,
                region_id=arguments.region,
                classification_id=arguments.classification,
                source_id=arguments.source_id,
                exchange_id=arguments.exchange,
                database=database,
            )
            _print_report(report)
            return 1 if any(issue.severity == "error" for issue in report.issues) else 0
        if arguments.command == "import":
            report = import_reviewed_file(
                database,
                arguments.input,
                region_id=arguments.region,
                classification_id=arguments.classification,
                source_id=arguments.source_id,
                exchange_id=arguments.exchange,
                coverage=arguments.coverage,
                approval_reference=arguments.approval_reference,
            )
            _print_report(report)
            return 0 if report.status == "committed" else 2
        if arguments.command == "represent":
            representation_id = database.add_entity_representation(
                region_id=arguments.region,
                classification_id=arguments.classification,
                entity_type=arguments.entity_type,
                entity_id=arguments.entity_id,
                exchange_id=arguments.exchange,
                symbol=arguments.symbol,
                source_id=arguments.source_id,
                approval_reference=arguments.approval_reference,
                effective_from=arguments.effective_from,
                effective_to=arguments.effective_to,
            )
            print(f"Added reviewed chart representation: {representation_id}")
            return 0
        if arguments.command == "refresh":
            print(
                "Live membership refresh is disabled until the single selected provider's "
                "coverage, terms, and display rights are approved.",
                file=sys.stderr,
            )
            return 2
    except (OSError, ValueError) as error:
        print(f"Universe administration failed: {error}", file=sys.stderr)
        return 2
    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
