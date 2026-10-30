"""Build and load the provisional US provider-taxonomy catalog."""

import argparse
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pandas as pd

_REQUIRED_COLUMNS = frozenset({"Ticker", "Name", "Sector", "Industry"})
_UNCLASSIFIED = frozenset({"", "undefined"})
_SYMBOL = re.compile(r"[A-Z0-9.-]+")


@dataclass(frozen=True, slots=True)
class UniverseSource:
    source_id: str
    path: Path
    priority: int


@dataclass(frozen=True, slots=True)
class ExperimentalIndustry:
    industry_id: str
    sector: str
    industry: str
    member_count: int
    source_ids: tuple[str, ...]
    classification_conflict_count: int


@dataclass(frozen=True, slots=True)
class ExperimentalUniverseCatalog:
    generated_at: datetime
    sources: tuple[str, ...]
    member_count: int
    industries: tuple[ExperimentalIndustry, ...]


@dataclass(frozen=True, slots=True)
class _Candidate:
    source: UniverseSource
    ticker: str
    sector: str
    industry: str


def _normalized_text(value: object) -> str:
    return str(value).strip()


def _is_classified_symbol(ticker: str, sector: str, industry: str) -> bool:
    return (
        _SYMBOL.fullmatch(ticker) is not None
        and sector.casefold() not in _UNCLASSIFIED
        and industry.casefold() not in _UNCLASSIFIED
    )


def _industry_id(sector: str, industry: str) -> str:
    normalized = f"{sector}-{industry}".upper()
    return re.sub(r"[^A-Z0-9]+", "-", normalized).strip("-")


def _read_source(source: UniverseSource) -> tuple[_Candidate, ...]:
    frame = pd.read_csv(source.path, dtype=str, keep_default_na=False)
    if missing := _REQUIRED_COLUMNS.difference(frame.columns):
        raise ValueError(
            f"{source.path} is missing required columns: {', '.join(sorted(missing))}"
        )
    candidates: list[_Candidate] = []
    for row in frame.loc[:, ["Ticker", "Sector", "Industry"]].itertuples(index=False):
        ticker, sector, industry = (_normalized_text(value) for value in row)
        if _is_classified_symbol(ticker, sector, industry):
            candidates.append(_Candidate(source, ticker, sector, industry))
    return tuple(candidates)


def build_experimental_catalog(
    sources: tuple[UniverseSource, ...],
    *,
    generated_at: datetime,
) -> ExperimentalUniverseCatalog:
    if not sources:
        raise ValueError("at least one universe source is required")
    if len({source.source_id for source in sources}) != len(sources):
        raise ValueError("universe source IDs must be unique")
    if len({source.priority for source in sources}) != len(sources):
        raise ValueError("universe source priorities must be unique")

    candidates_by_ticker: dict[str, list[_Candidate]] = {}
    for source in sorted(sources, key=lambda value: value.priority):
        for candidate in _read_source(source):
            candidates_by_ticker.setdefault(candidate.ticker, []).append(candidate)

    aggregates: dict[tuple[str, str], list[tuple[_Candidate, int, tuple[str, ...]]]] = {}
    for candidates in candidates_by_ticker.values():
        selected = min(candidates, key=lambda candidate: candidate.source.priority)
        classifications = {(candidate.sector, candidate.industry) for candidate in candidates}
        source_ids = tuple(
            candidate.source.source_id
            for candidate in sorted(candidates, key=lambda candidate: candidate.source.priority)
        )
        aggregates.setdefault((selected.sector, selected.industry), []).append(
            (selected, int(len(classifications) > 1), source_ids)
        )

    industries = tuple(
        ExperimentalIndustry(
            industry_id=_industry_id(sector, industry),
            sector=sector,
            industry=industry,
            member_count=len(members),
            source_ids=tuple(sorted({source_id for _, _, ids in members for source_id in ids})),
            classification_conflict_count=sum(conflicts for _, conflicts, _ in members),
        )
        for (sector, industry), members in sorted(
            aggregates.items(), key=lambda item: (item[0][0], item[0][1])
        )
    )
    return ExperimentalUniverseCatalog(
        generated_at=generated_at.astimezone(UTC),
        sources=tuple(
            source.source_id for source in sorted(sources, key=lambda value: value.priority)
        ),
        member_count=len(candidates_by_ticker),
        industries=industries,
    )


def write_experimental_catalog(catalog: ExperimentalUniverseCatalog, path: str | Path) -> None:
    destination = Path(path)
    document = {
        "schema_version": 1,
        "taxonomy": "Experimental provider labels; not GICS",
        "generated_at": catalog.generated_at.isoformat(),
        "sources": list(catalog.sources),
        "member_count": catalog.member_count,
        "industries": [
            {
                "industry_id": industry.industry_id,
                "sector": industry.sector,
                "industry": industry.industry,
                "member_count": industry.member_count,
                "source_ids": list(industry.source_ids),
                "classification_conflict_count": industry.classification_conflict_count,
            }
            for industry in catalog.industries
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(f"{destination.suffix}.tmp")
    temporary.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    temporary.replace(destination)


def load_experimental_catalog(path: str | Path) -> ExperimentalUniverseCatalog:
    source = Path(path)
    raw_document = json.loads(source.read_text())
    if not isinstance(raw_document, dict):
        raise ValueError("experimental universe catalog must be a JSON object")
    document = cast(dict[str, object], raw_document)
    if document.get("schema_version") != 1:
        raise ValueError("experimental universe catalog requires schema version 1")
    if document.get("taxonomy") != "Experimental provider labels; not GICS":
        raise ValueError("experimental universe catalog taxonomy is invalid")
    source_ids = _string_list(document, "sources")
    industries = document.get("industries")
    member_count = document.get("member_count")
    if (
        not isinstance(industries, list)
        or not isinstance(member_count, int)
        or member_count < 0
    ):
        raise ValueError("experimental universe catalog has invalid metadata")
    parsed_industries: list[ExperimentalIndustry] = []
    for row in cast(list[object], industries):
        if not isinstance(row, dict):
            raise ValueError("experimental universe catalog industries must be objects")
        record = cast(dict[str, object], row)
        parsed_industries.append(
            ExperimentalIndustry(
                _required_string(record, "industry_id"),
                _required_string(record, "sector"),
                _required_string(record, "industry"),
                _required_positive_int(record, "member_count"),
                _string_list(record, "source_ids"),
                _required_nonnegative_int(record, "classification_conflict_count"),
            )
        )
    return ExperimentalUniverseCatalog(
        datetime.fromisoformat(_required_string(document, "generated_at")),
        source_ids,
        member_count,
        tuple(parsed_industries),
    )


def _required_string(record: dict[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"experimental universe catalog requires nonempty {key}")
    return value


def _string_list(record: dict[str, object], key: str) -> tuple[str, ...]:
    value = record.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"experimental universe catalog requires nonempty {key}")
    items = cast(list[object], value)
    if not all(isinstance(item, str) and item for item in items):
        raise ValueError(f"experimental universe catalog {key} must contain nonempty strings")
    return tuple(cast(list[str], items))


def _required_positive_int(record: dict[str, object], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"experimental universe catalog requires positive {key}")
    return value


def _required_nonnegative_int(record: dict[str, object], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"experimental universe catalog requires nonnegative {key}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a provisional US provider-taxonomy catalog")
    parser.add_argument("--sp500", required=True, type=Path)
    parser.add_argument("--russell2000", required=True, type=Path)
    parser.add_argument("--nasdaq", required=True, type=Path)
    parser.add_argument("--nyse", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    catalog = build_experimental_catalog(
        (
            UniverseSource("wikipedia-sp500-gics", args.sp500, 0),
            UniverseSource("ishares-financedatabase-russell2000", args.russell2000, 1),
            UniverseSource("financedatabase-nasdaq", args.nasdaq, 2),
            UniverseSource("financedatabase-nyse", args.nyse, 3),
        ),
        generated_at=datetime.now(UTC),
    )
    write_experimental_catalog(catalog, args.output)


if __name__ == "__main__":
    main()
