"""Command-line administration for reviewed regional stock-universe data."""

import argparse
import json
import sqlite3
import sys
from dataclasses import asdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from market_data.domain.local_etf_evidence import (
    REPORT_VERSION,
    selected_review,
    support_reasons,
)
from market_data_tools.catalog_admin import run_command as run_catalog_command
from market_leadership.application.discover_etf_candidates import (
    collect_etf_candidates,
    record_etf_candidate_review,
    review_etf_candidates,
)
from market_leadership.application.industry_representations import representation_worklist
from market_leadership.infrastructure.region_database import SCHEMA_VERSION, RegionDatabase
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


def _review_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--region", required=True)
    parser.add_argument("--classification", required=True)
    parser.add_argument("--entity-id", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--approval-reference", required=True)
    parser.add_argument("--effective-from", type=date.fromisoformat, required=True)
    parser.add_argument("--effective-to", type=date.fromisoformat)
    _database_argument(parser)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="market-universe")
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
        "recover-catalog", help="recover explicitly from known entry and release checksums"
    )
    catalog_recover.add_argument("--manifest", type=Path)
    catalog_recover.add_argument("--release-manifest", type=Path, required=True)
    catalog_recover.add_argument("--target-manifest-sha256", required=True)
    catalog_recover.add_argument("--expected-entry-sha256", required=True)

    initialize = commands.add_parser("init", help="initialize the regional universe database")
    _database_argument(initialize)

    collect = commands.add_parser(
        "collect-etf-candidates", help="collect local literal ETF research without approval"
    )
    _database_argument(collect)
    collect.add_argument("--root", action="append", default=[], metavar="RESOURCE=PATH")
    collect.add_argument(
        "--catalog",
        action="append",
        default=[],
        metavar="RESOURCE=RELATIVE_PATH:CATALOG",
    )
    candidate_worklist = commands.add_parser(
        "review-etf-candidates",
        help="compare unapproved local ETF evidence with reviewed nodes",
    )
    _database_argument(candidate_worklist)
    candidate_worklist.add_argument("--region", required=True)
    candidate_worklist.add_argument("--classification", required=True)
    candidate_worklist.add_argument("--as-of", type=date.fromisoformat, required=True)
    candidate_worklist.add_argument("--collection-run")
    candidate_decision = commands.add_parser(
        "review-etf-candidate",
        help="record an explicit exact-node ETF research decision",
    )
    _database_argument(candidate_decision)
    for flag in (
        "candidate-id",
        "collection-run",
        "region",
        "classification",
        "entity-id",
        "reason",
        "review-reference",
    ):
        candidate_decision.add_argument(f"--{flag}", required=True)
    candidate_decision.add_argument("--as-of", type=date.fromisoformat, required=True)
    candidate_decision.add_argument("--decision", choices=("accept", "reject"), required=True)
    candidate_decision.add_argument("--evidence-id", action="append", required=True)
    for flag in ("confirm-etf-identity", "confirm-exact-scope", "confirm-suitability"):
        candidate_decision.add_argument(f"--{flag}", action="store_true")
    candidate_decision.add_argument("--issue-resolution", action="append", default=[])

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

    worklist = commands.add_parser(
        "review-representations",
        help="list every active industry/sub-industry and review evidence",
    )
    worklist.add_argument("--region", required=True)
    worklist.add_argument("--classification", required=True)
    worklist.add_argument("--as-of", type=date.fromisoformat, required=True)
    worklist.add_argument("--uncovered-only", action="store_true")
    _database_argument(worklist)

    listings = commands.add_parser(
        "review-listings",
        help="list verified active regional listing IDs and provider symbols",
    )
    listings.add_argument("--region", required=True)
    listings.add_argument("--as-of", type=date.fromisoformat, required=True)
    _database_argument(listings)

    etf = commands.add_parser("approve-etf", help="approve an industry/sub-industry ETF mapping")
    _review_arguments(etf)
    etf.add_argument("--exchange", required=True)
    etf.add_argument("--symbol", required=True)
    etf.add_argument("--candidate-review-id")

    basket = commands.add_parser(
        "approve-basket", help="approve a weighted stock-basket alternative"
    )
    _review_arguments(basket)
    basket.add_argument("--name", required=True)
    basket.add_argument(
        "--constituent",
        action="append",
        required=True,
        metavar="LISTING_ID=WEIGHT_PERCENT",
        help="repeat for each verified listing; positive decimal weights must total exactly 100",
    )

    node = commands.add_parser(
        "review-node",
        help="register a reviewed industry or sub-industry without stock members",
    )
    _review_arguments(node)
    node.add_argument("--name", required=True)
    node.add_argument("--sector-id", required=True)
    node.add_argument("--parent-industry-id", help="required for a sub-industry")

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
    if arguments.command in (
        "catalog-init",
        "validate-catalog",
        "activate-catalog",
        "recover-catalog",
    ):
        return run_catalog_command(arguments)
    database = RegionDatabase(arguments.database)
    try:
        if arguments.command == "init":
            database.initialize()
            print(f"Initialized regional database: {database.path} (schema {SCHEMA_VERSION})")
            return 0
        if arguments.command == "collect-etf-candidates":
            roots: dict[str, Path] = {}
            for override in arguments.root:
                alias, separator, path = override.partition("=")
                if not separator or not path:
                    raise ValueError("Root override must use RESOURCE=PATH")
                if alias in roots:
                    raise ValueError(f"Repeated root override for {alias}")
                roots[alias] = Path(path)
            inventory = collect_etf_candidates(
                database,
                roots=roots,
                catalogs=tuple(arguments.catalog),
            )
            print(json.dumps(inventory.report(), indent=2))
            for resource in inventory.run.resources:
                for issue in resource.issues:
                    print(f"{resource.alias}: {issue}", file=sys.stderr)
            return 0 if inventory.run.status == "complete" else 2
        if arguments.command == "review-etf-candidates":
            report = review_etf_candidates(
                database,
                region_id=arguments.region,
                classification_id=arguments.classification,
                as_of=arguments.as_of,
                collection_run=arguments.collection_run,
            )
            print(json.dumps(report, default=str, indent=2))
            return 0
        if arguments.command == "review-etf-candidate":
            resolutions: list[tuple[str, str]] = []
            for value in arguments.issue_resolution:
                issue, separator, rationale = value.partition("=")
                if not separator or not issue.strip() or not rationale.strip():
                    raise ValueError(
                        "Issue resolution must use ISSUE=RATIONALE with non-empty values"
                    )
                resolutions.append((issue, rationale))
            review = record_etf_candidate_review(
                database,
                candidate_id=arguments.candidate_id,
                collection_run=arguments.collection_run,
                region_id=arguments.region,
                classification_id=arguments.classification,
                entity_id=arguments.entity_id,
                as_of=arguments.as_of,
                decision=arguments.decision,
                reason=arguments.reason,
                review_reference=arguments.review_reference,
                evidence_ids=tuple(arguments.evidence_id),
                confirmations=(
                    arguments.confirm_etf_identity,
                    arguments.confirm_exact_scope,
                    arguments.confirm_suitability,
                ),
                resolutions=tuple(resolutions),
            )
            snapshot = database.get_etf_snapshot()
            selected = selected_review(
                snapshot.reviews,
                review.region_id,
                review.classification_id,
                review.entity_id,
            )
            status = (
                "none"
                if selected is None
                else "accepted_needs_re_review"
                if support_reasons(selected, snapshot)
                else "accepted_current"
            )
            print(
                json.dumps(
                    {
                        **asdict(review),
                        "report_version": REPORT_VERSION,
                        "selected_review_id": selected.review_id if selected else None,
                        "selected_review_status": status,
                    },
                    indent=2,
                )
            )
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
        if arguments.command == "review-representations":
            worklist = representation_worklist(
                database,
                region_id=arguments.region,
                classification_id=arguments.classification,
                as_of=arguments.as_of,
                only_uncovered=arguments.uncovered_only,
            )
            print(json.dumps([asdict(item) for item in worklist], default=str, indent=2))
            return 0
        if arguments.command == "review-listings":
            listings = database.get_verified_listings(arguments.region, as_of=arguments.as_of)
            print(json.dumps([asdict(item) for item in listings], indent=2))
            return 0
        if arguments.command == "review-node":
            database.add_review_node(
                region_id=arguments.region,
                classification_id=arguments.classification,
                entity_id=arguments.entity_id,
                name=arguments.name,
                sector_id=arguments.sector_id,
                parent_industry_id=arguments.parent_industry_id,
                source_id=arguments.source_id,
                approval_reference=arguments.approval_reference,
                effective_from=arguments.effective_from,
                effective_to=arguments.effective_to,
            )
            print(f"Registered reviewed classification node: {arguments.entity_id}")
            return 0
        if arguments.command == "approve-basket":
            constituents: list[tuple[str, Decimal]] = []
            for value in arguments.constituent:
                listing_id, separator, weight_text = value.partition("=")
                if not separator or not listing_id.strip():
                    raise ValueError("Constituents must use LISTING_ID=WEIGHT_PERCENT")
                try:
                    weight = Decimal(weight_text)
                except InvalidOperation as error:
                    raise ValueError(f"Invalid constituent weight: {weight_text!r}") from error
                if not weight.is_finite() or weight <= 0:
                    raise ValueError("Constituent weight must be finite and positive")
                constituents.append((listing_id, weight))
            identifier = database.add_stock_basket(
                region_id=arguments.region,
                classification_id=arguments.classification,
                entity_id=arguments.entity_id,
                name=arguments.name,
                source_id=arguments.source_id,
                approval_reference=arguments.approval_reference,
                effective_from=arguments.effective_from,
                effective_to=arguments.effective_to,
                constituents=tuple(constituents),
            )
            print(f"Approved stock basket alternative: {identifier}")
            return 0
        if arguments.command in ("represent", "approve-etf"):
            representation_id = database.add_entity_representation(
                region_id=arguments.region,
                classification_id=arguments.classification,
                entity_type=arguments.entity_type
                if arguments.command == "represent"
                else "industry",
                entity_id=arguments.entity_id,
                exchange_id=arguments.exchange,
                symbol=arguments.symbol,
                source_id=arguments.source_id,
                approval_reference=arguments.approval_reference,
                effective_from=arguments.effective_from,
                effective_to=arguments.effective_to,
                candidate_review_id=arguments.candidate_review_id
                if arguments.command == "approve-etf"
                else None,
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
    except (OSError, ValueError, sqlite3.Error) as error:
        print(f"Universe administration failed: {error}", file=sys.stderr)
        return 2
    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
