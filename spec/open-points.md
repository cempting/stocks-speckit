---
id: OPEN-POINTS
title: Open points register
status: living
---

# Open points register

All open points are closed. This register is generated from section 9 of each aspect spec and the persona (`python3 gen_open.py`); it lists no open item.

- Round 2 and round 3 user resolutions closed their items as `D-R01`…`D-R45` in [decisions.md](decisions.md).
- Every remaining item was closed with a documented practitioner default, `D-DEF-01`…`D-DEF-42`, in the section "Defaults by recommendation (reviewable)" of [decisions.md](decisions.md). These defaults are binding but **await user review** (review status "pending user review"); each aspect marks them in its parameter table and section 9 ("Closed by D-DEF-nn").
- The former proposed defaults are settled: bear-market threshold −20 % (D-DEF-06), equal criterion weights within a scorecard pillar (D-DEF-21), trend exit without buffer or slope condition (D-R35), stop-raise mode structure (D-R34).

To reopen a point, add an `OPEN-Axx-n` item to section 9 of its aspect, regenerate this register, and record the eventual decision as a new `D-…` entry.

## Open items by aspect


None. All OPEN items are closed (see decisions.md).
