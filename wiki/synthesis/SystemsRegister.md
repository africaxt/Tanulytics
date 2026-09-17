<<<<<<< HEAD
---
type: synthesis
canonical: notion
name: Systems Register
category: infrastructure
status: active
updated: 2026-09-04
version: 1.0
source_count: 2
sources: ["Notion Systems Register", "TradingPlan.md v1.1 §5.2"]
tags: [infrastructure, airtable, brokers, resolution-layer, pointer]
---

# Systems Register

> **Canonical source:** the live register lives in Notion — DMB OS → Systems Register. This note holds the **stable identifiers only**. Status, purpose and review flags change; they are deliberately not mirrored here.

**Resolution rule:** resolve on `System ID`, never on a system's name. Names are a display layer and change freely — three teamspace renames on 2026-09-04 alone.

---

## Why this exists

Entities resolved to vault notes and Notion hubs but not to the Airtable bases holding their records, and the broker rails in [[TradingPlan]] §5.2 existed only as a table inside that document. Neither was queryable. The register makes *"which entity places orders at FXCM, under what mandate"* an answerable question.

## Entity → Airtable base ID

| Entity | Base ID(s) |
|---|---|
| [[AfricaX Trading]] | `appQOGhLjKJyOFqEm` |
| [[MerchantX]] | `appVToJQQEDgjS9nS` |
| [[HBC]] | `appEs9fojfiysCbTD` |
| [[Ai4Ag]] | `appInyz1DDrxQurQ2` · `appD1YGxw8GMVZ4rx` (D4Ag) |
| [[Karibu Trust]] | `apphmSUd0TWgzJxhO` |
| [[Batuma BGE]] | `appOGYlRgzIIcPMuN` · `app6M92TLOfvE7Wve` · `appMEvC7eYtNczcbf` · `appfLgwtu701vCI1R` |
| [[Dbuntu LABS]] | `appMdYEFpUaaT5wx2` · `appKdOMkvsKfoqfg6` · `appV5pzgcrV5TVPiQ` · `appI7tE8aB2EF9cWg` · `appB7UwSaTaMaNcIx` · `apptgbmdEg2XVj9oi` |
| [[MBZ Group Africa]] | `appzuEbt177qMuhxr` · `appeD9D61Qc0G4TCr` · `appFODGEc1H6QbG20` |
| [[Tanulytics]] | *none — read-only aggregation, holds no records of its own* |
| [[MBZ Global Management FZCO]] | *none — brokerage and custody shell* |

## Broker → executing entity (§5.2)

| Broker | Executes for | Aggregation |
|---|---|---|
| [[IBKR]] | [[MBZ Global Management FZCO]] | Automated |
| [[FXCM]] | [[MBZ Global Management FZCO]] | Automated |
| [[Schwab]] | [[MBZ Global Management FZCO]] | Automated |
| [[Robinhood]] | [[MBZ Global Management FZCO]] | Automated |
| Emirates NBD | [[MBZ Global Management FZCO]] | **Outside** — weekly CSV |
| XENO | [[HBC]] | **Outside** — weekly CSV |

## Notion teamspace UUIDs

| Vertical | Teamspace UUID |
|---|---|
| AfricaX Trading | `4d2d96af-6844-40bc-b9c2-e7b489daff7e` |
| Highland VC | `6c60be94-28e3-4846-99b4-5e1fccbac615` |
| Register layer | `376c9f23-0499-81ad-bf06-00427e3c7301` |

Entities belonging to neither book carry the sentinel `root`.

## Personal boundary

`appwAsI8qHESxg3bO` — **personal discretionary trading**, deliberately unlinked from every register entity. [[TradingPlan]] does not govern it. The separation is what the plan's no-speculation mandate depends on.

## In this vault
[[TradingPlan]] · [[PipelineArchitecture]] · [[HighlandVC]] · [[AfricaXTrading]] · [[MBZ Global Management FZCO]]
=======
---
type: synthesis
canonical: notion
name: Systems Register
category: infrastructure
status: active
updated: 2026-09-04
version: 1.0
source_count: 2
sources: ["Notion Systems Register", "TradingPlan.md v1.1 §5.2"]
tags: [infrastructure, airtable, brokers, resolution-layer, pointer]
---

# Systems Register

> **Canonical source:** the live register lives in Notion — DMB OS → Systems Register. This note holds the **stable identifiers only**. Status, purpose and review flags change; they are deliberately not mirrored here.

**Resolution rule:** resolve on `System ID`, never on a system's name. Names are a display layer and change freely — three teamspace renames on 2026-09-04 alone.

---

## Why this exists

Entities resolved to vault notes and Notion hubs but not to the Airtable bases holding their records, and the broker rails in [[TradingPlan]] §5.2 existed only as a table inside that document. Neither was queryable. The register makes *"which entity places orders at FXCM, under what mandate"* an answerable question.

## Entity → Airtable base ID

| Entity | Base ID(s) |
|---|---|
| [[AfricaX Trading]] | `appQOGhLjKJyOFqEm` |
| [[MerchantX]] | `appVToJQQEDgjS9nS` |
| [[HBC]] | `appEs9fojfiysCbTD` |
| [[Ai4Ag]] | `appInyz1DDrxQurQ2` · `appD1YGxw8GMVZ4rx` (D4Ag) |
| [[Karibu Trust]] | `apphmSUd0TWgzJxhO` |
| [[Batuma BGE]] | `appOGYlRgzIIcPMuN` · `app6M92TLOfvE7Wve` · `appMEvC7eYtNczcbf` · `appfLgwtu701vCI1R` |
| [[Dbuntu LABS]] | `appMdYEFpUaaT5wx2` · `appKdOMkvsKfoqfg6` · `appV5pzgcrV5TVPiQ` · `appI7tE8aB2EF9cWg` · `appB7UwSaTaMaNcIx` · `apptgbmdEg2XVj9oi` |
| [[MBZ Group Africa]] | `appzuEbt177qMuhxr` · `appeD9D61Qc0G4TCr` · `appFODGEc1H6QbG20` |
| [[Tanulytics]] | *none — read-only aggregation, holds no records of its own* |
| [[MBZ Global Management FZCO]] | *none — brokerage and custody shell* |

## Broker → executing entity (§5.2)

| Broker | Executes for | Aggregation |
|---|---|---|
| [[IBKR]] | [[MBZ Global Management FZCO]] | Automated |
| [[FXCM]] | [[MBZ Global Management FZCO]] | Automated |
| [[Schwab]] | [[MBZ Global Management FZCO]] | Automated |
| [[Robinhood]] | [[MBZ Global Management FZCO]] | Automated |
| Emirates NBD | [[MBZ Global Management FZCO]] | **Outside** — weekly CSV |
| XENO | [[HBC]] | **Outside** — weekly CSV |

## Notion teamspace UUIDs

| Vertical | Teamspace UUID |
|---|---|
| AfricaX Trading | `4d2d96af-6844-40bc-b9c2-e7b489daff7e` |
| Highland VC | `6c60be94-28e3-4846-99b4-5e1fccbac615` |
| Register layer | `376c9f23-0499-81ad-bf06-00427e3c7301` |

Entities belonging to neither book carry the sentinel `root`.

## Personal boundary

`appwAsI8qHESxg3bO` — **personal discretionary trading**, deliberately unlinked from every register entity. [[TradingPlan]] does not govern it. The separation is what the plan's no-speculation mandate depends on.

## In this vault
[[TradingPlan]] · [[PipelineArchitecture]] · [[HighlandVC]] · [[AfricaXTrading]] · [[MBZ Global Management FZCO]]
>>>>>>> c4461662d3e0c9889d8bb1ae887650fcc7835c35
