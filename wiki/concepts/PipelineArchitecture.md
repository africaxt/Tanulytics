---
type: concept
name: Pipeline Architecture
updated: 2026-06-28
---

# Pipeline Architecture

## Overview
Tanulytics is a closed-loop data pipeline: brokers → aggregation → Airtable → Notion → Obsidian.

## Flow
```
run_all.py
  ├── ibkr_fetch.py    → data/raw/
  ├── fxcm_fetch.py    → data/raw/
  ├── schwab_fetch.py  → data/raw/
  ├── robinhood_fetch.py → data/raw/
  ↓
  aggregator.py        → data/processed/combined_*.json
  ↓
  airtable_push.py     → Airtable (Positions / Balances / Trade History / Daily Summary)
  ↓
  notion_summary.py    → Notion (Portfolio page + Mindset Stack)
  ↓
  obsidian_write.py    → journal/YYYY-MM-DD.md
```

## Design principles
1. **Code owns schema** — Airtable tables created programmatically
2. **Read-only everywhere** — no order placement
3. **Data first** — raw JSON preserved before processing
4. **Deduplication** — broker-native IDs prevent double-importing
5. **Graceful degradation** — one broker failure doesn't abort the run

## Related
- [[RiskFramework]], [[IBKR]], [[FXCM]], [[Schwab]], [[Robinhood]]

## Upstream: TraderChit architecture
The Tanulytics pipeline sits **downstream** of the TraderChit trading stack:

```
[[LearnAI]] → [[XeQT]] → Brokers
                                                                      ↓
                                                              run_all.py (data extraction)
                                                                      ↓
                                                              Airtable → Notion → Obsidian
```

The pipeline extracts the state of what XeQT has executed — it does not drive execution.

## Sources

| File | Date | Key takeaway |
|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | 2026-06-28 | TraderChit as the upstream execution system feeding pipeline data |
