# Consolidated Task History

**Reconciled**: 2026-11-06. This ledger is historical evidence, not an executable
backlog or acceptance claim for current requirements. Task IDs are qualified by
feature and must not be renumbered, reused, or reopened as new work.

## Completion and Retirement Ledger

Ranges are inclusive and account for every task in the removed historical backlogs.
Completed records retain their historical status; unchecked retired work is
**Superseded (not completed)**, never checked complete.

| Feature | Task IDs | Status | Current owner / disposition |
|---|---|---|---|
| 001 | T001-T048 | Completed | Original foundation and live-discovery increments; not proof of revised technical screening or acceptance |
| 001 | T049-T098 | Superseded (not completed) | Retired weekly/multi-market/breadth/flow and obsolete runtime-mode work; current [001 backlog](001-market-leadership-screener/tasks.md) starts at T099 |
| 003 | T001-T011 | Completed | Historical snapshot/live momentum increments; current navigation, controls and evidence follow [004](004-sector-stock-explorer/spec.md) and lookup placement follows 015 |
| 005 | T001-T006 | Completed | Historical aggregate-score/table increment; current five-column presentation follows [006](006-stock-table-columns/spec.md) |
| 007 | T001-T011 | Superseded (not completed) | Independent ETF-only backlog retired by consolidation into [008](008-industry-representation-tools/spec.md); accepted ETF/basket requirements remain, not claimed implemented by retirement |

**Totals**: 65 completed IDs and 61 superseded IDs across four historical backlogs.
002 separately retains completed T001-T004 and superseded T005-T008 in its
[current task document](002-fundamental-grading-layout/tasks.md).
Other active backlogs and their completion markers remain unchanged.

## Original Descriptions and Evidence

The immutable pre-cleanup Git baseline preserves the complete original task
descriptions, referenced tests, dependency histories, plans and specifications:

- [001 original tasks](https://github.com/cempting/stocks-speckit/blob/429b58961efaa944f052025baff555b2841017f1/specs/001-market-leadership-screener/tasks.md)
- [003 original tasks](https://github.com/cempting/stocks-speckit/blob/429b58961efaa944f052025baff555b2841017f1/specs/003-industry-momentum-table/tasks.md)
- [005 original tasks](https://github.com/cempting/stocks-speckit/blob/429b58961efaa944f052025baff555b2841017f1/specs/005-contained-stock-score/tasks.md)
- [007 original tasks](https://github.com/cempting/stocks-speckit/blob/429b58961efaa944f052025baff555b2841017f1/specs/007-industry-etf-momentum/tasks.md)

These sources can also be inspected locally with `git show
429b58961efaa944f052025baff555b2841017f1:specs/<feature>/tasks.md`.
001's later retirement of T049-T098 is recorded above; the older source's unchecked
boxes must not be interpreted as current pending work. Historical filenames,
selectors, modes, column labels and storage designs are not current instructions.

The retained redirect specifications map original FR/SC IDs to their active owners:
[003](003-industry-momentum-table/spec.md),
[005](005-contained-stock-score/spec.md) and
[007](007-industry-etf-momentum/spec.md).
Supporting contracts remain where referenced, especially
[003's live UI contract](003-industry-momentum-table/contracts/live-discovery-ui.md).
Preserve the current four tabs, five-column stock table, chart geometry, palettes,
controls, explicit loading and independent state. Cleanup adds no implementation,
migration, source permission, new validation result or constitution exception.
