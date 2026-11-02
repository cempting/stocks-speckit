"""File-only administration for reviewed company evidence."""

import argparse
import json
import re
import sys
from dataclasses import asdict, replace
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

from market_data.catalog import load_release
from market_data.company_evidence import CompanyEvidenceFiles
from market_data.config import resolve_company_evidence_root
from market_data.domain.company_evidence import (
    CompanyAssociation,
    SourceAssessment,
    company_association_id,
)

REPORT_VERSION = "company-evidence-admin-1"
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="company-evidence-admin")
    commands = parser.add_subparsers(dest="command", required=True)

    source = commands.add_parser(
        "review-source", help="record source provenance and independently reviewed uses"
    )
    source.add_argument("--source-id", required=True)
    source.add_argument("--role", choices=("financial", "disclosure", "reference"), required=True)
    source.add_argument("--publisher", required=True)
    source.add_argument("--terms-url", required=True)
    source.add_argument("--coverage-reference", required=True)
    source.add_argument("--authority", required=True)
    source.add_argument(
        "--status",
        choices=("unreviewed", "approved", "denied", "revoked"),
        required=True,
    )
    source.add_argument("--reviewed-at", type=date.fromisoformat)
    source.add_argument("--review-reference", required=True)
    source.add_argument("--expires-at", type=date.fromisoformat)
    source.add_argument("--structured-capability", action="append", default=[])
    source.add_argument(
        "--permission",
        action="append",
        choices=("collection", "display", "normalized_retention", "raw_retention"),
        default=[],
    )
    source.add_argument("--allowed-host", action="append", default=[])
    source.add_argument("--allowed-route", action="append", default=[])
    _common_arguments(source)

    binding = commands.add_parser(
        "bind-issuer", help="record a dated issuer reference for a captured listing"
    )
    binding.add_argument("--manifest", type=Path, required=True)
    binding.add_argument("--instrument-id", required=True)
    binding.add_argument("--listing-id", required=True)
    binding.add_argument("--provider-id", required=True)
    binding.add_argument("--cik")
    binding.add_argument("--issuer-domain")
    binding.add_argument("--effective-from", type=date.fromisoformat, required=True)
    binding.add_argument("--effective-to", type=date.fromisoformat)
    binding.add_argument("--identity-reference", required=True)
    binding.add_argument("--research-identity-reference")
    _common_arguments(binding)
    return parser


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument(
        "--expected-revision",
        required=True,
        help="current SHA-256 revision, or 'none' only when creating a record",
    )


def _expected_revision(value: str) -> str | None:
    if value == "none":
        return None
    if _SHA256.fullmatch(value) is None:
        raise ValueError("--expected-revision must be 'none' or a lowercase SHA-256 digest")
    return value


def _store(root: Path | None) -> CompanyEvidenceFiles:
    return CompanyEvidenceFiles(resolve_company_evidence_root(root))


def _source_assessment(arguments: argparse.Namespace) -> SourceAssessment:
    role = arguments.role
    status = arguments.status
    uses = tuple(arguments.permission)
    capabilities = tuple(arguments.structured_capability)
    hosts = tuple(host.casefold() for host in arguments.allowed_host)
    routes = tuple(arguments.allowed_route)
    if len(set(uses)) != len(uses):
        raise ValueError("--permission values must be unique")
    if len(set(capabilities)) != len(capabilities):
        raise ValueError("--structured-capability values must be unique")
    if len(set(hosts)) != len(hosts):
        raise ValueError("--allowed-host values must be unique")
    if len(set(routes)) != len(routes):
        raise ValueError("--allowed-route values must be unique")
    if role == "reference" and uses:
        raise ValueError("Reference-only sources cannot be granted collection or retention uses")
    if status != "approved" and uses:
        raise ValueError("Only an approved source can record permitted uses")
    if status == "approved":
        if arguments.reviewed_at is None:
            raise ValueError("Approved sources require --reviewed-at")
        if arguments.expires_at is not None and arguments.expires_at < arguments.reviewed_at:
            raise ValueError("Source expiry cannot precede its review date")
    if "collection" in uses and (
        not capabilities or not hosts
    ):
        raise ValueError(
            "Collection permission requires structured capabilities and allowed hosts"
        )
    terms_url = cast(str, arguments.terms_url)
    terms = urlsplit(terms_url)
    if (
        terms.scheme not in ("http", "https")
        or not terms.hostname
        or terms.username
        or terms.password
        or terms.query
        or terms.fragment
    ):
        raise ValueError("--terms-url must be a public HTTP(S) URL without credentials or query")

    draft = SourceAssessment(
        assessment_id="pending",
        source_id=arguments.source_id,
        role=role,
        status=status,
        allowed_uses=uses,
        reviewed_at=arguments.reviewed_at,
        review_reference=arguments.review_reference,
        expires_at=arguments.expires_at,
        fingerprint="0" * 64,
        publisher=arguments.publisher,
        terms_url=terms_url,
        coverage_reference=arguments.coverage_reference,
        authority=arguments.authority,
        structured_capabilities=capabilities,
        allowed_hosts=hosts,
        allowed_routes=routes,
    )
    material = asdict(draft)
    material.pop("fingerprint")
    fingerprint = sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    return replace(
        draft,
        assessment_id=f"assessment-{fingerprint[:24]}",
        fingerprint=fingerprint,
    )


def _issuer_association(arguments: argparse.Namespace) -> CompanyAssociation:
    if arguments.cik is None and arguments.issuer_domain is None:
        raise ValueError("At least one of --cik or --issuer-domain is required")
    if arguments.cik is not None and re.fullmatch(r"[0-9]{10}", arguments.cik) is None:
        raise ValueError("--cik must contain exactly ten digits")
    domain = arguments.issuer_domain
    if domain is not None:
        parsed_domain = urlsplit(f"//{domain}")
        if (
            parsed_domain.hostname != domain
            or domain != domain.casefold()
            or parsed_domain.port is not None
            or parsed_domain.path
            or parsed_domain.query
            or parsed_domain.fragment
        ):
            raise ValueError("--issuer-domain must be a lowercase hostname without a scheme")

    catalog = load_release(arguments.manifest)
    listing = next(
        (
            item
            for item in (*catalog.listings, *catalog.regional_listings)
            if item.listing_id == arguments.listing_id
            and item.instrument_id == arguments.instrument_id
        ),
        None,
    )
    if listing is None:
        raise ValueError("The exact instrument/listing pair is not present in the captured catalog")
    if listing.instrument_type != "stock" or listing.resolution_state != "verified":
        raise ValueError("Issuer binding requires a verified stock listing")
    if not listing.active_on(arguments.effective_from):
        raise ValueError("Listing is not active on --effective-from")
    if (
        arguments.effective_to is not None
        and (
            arguments.effective_to < arguments.effective_from
            or not listing.active_on(arguments.effective_to)
        )
    ):
        raise ValueError("Issuer binding dates must be ordered and covered by the listing")
    if listing.period is None:
        raise ValueError("Verified listing is missing its reviewed effective period")
    if arguments.effective_from < listing.period.start or (
        arguments.effective_to is None
        and listing.period.end is not None
    ):
        raise ValueError("Issuer binding dates must be contained in the reviewed listing period")

    issuer_key = f"cik:{arguments.cik}" if arguments.cik else f"domain:{domain}"
    association_id = company_association_id(
        instrument_id=listing.instrument_id,
        listing_id=listing.listing_id,
        source_id=arguments.provider_id,
        effective_from=arguments.effective_from,
        effective_to=arguments.effective_to,
    )
    research_reference = arguments.research_identity_reference
    return CompanyAssociation(
        association_id=association_id,
        instrument_id=listing.instrument_id,
        listing_id=listing.listing_id,
        region_id=listing.region_id,
        company_id=None,
        provider_id=arguments.provider_id,
        provider_symbol=listing.provider_symbol or "",
        exchange=listing.exchange or "",
        trading_currency=listing.currency or "",
        catalog_revision=catalog.catalog_revision,
        effective_from=arguments.effective_from,
        effective_to=arguments.effective_to,
        issuer_key=issuer_key,
        cik=arguments.cik,
        issuer_domain=domain,
        binding_reference=arguments.identity_reference,
        identity_evidence=None,
        state="unresolved",
        reason="Awaiting corroboration by the provider issuer profile",
        research_binding_reference=research_reference,
        research_identity_evidence=research_reference,
    )


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        expected_revision = _expected_revision(arguments.expected_revision)
        store = _store(arguments.evidence_root)
        if arguments.command == "review-source":
            record = _source_assessment(arguments)
            revision = store.save_source_assessment(
                record, expected_revision=expected_revision
            )
            result = {"assessment_id": record.assessment_id, "revision": revision}
            permissions_recorded = list(record.allowed_uses)
            permission_granted = None
        elif arguments.command == "bind-issuer":
            record = _issuer_association(arguments)
            revision = store.save_association(
                record, expected_revision=expected_revision
            )
            result = {
                "association_id": record.association_id,
                "revision": revision,
                "state": record.state,
                "company_id": None,
                "issuer_key": record.issuer_key,
            }
            permissions_recorded = []
            permission_granted = False
        else:
            parser.error("unsupported command")
            return 2
        print(
            json.dumps(
                {
                    "report_version": REPORT_VERSION,
                    "command": arguments.command,
                    "status": "recorded",
                    "permission_granted": permission_granted,
                    "permissions_recorded": permissions_recorded,
                    "result": result,
                },
                sort_keys=True,
            )
        )
        return 0
    except (OSError, ValueError) as error:
        print(f"Company evidence administration failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
