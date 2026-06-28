---
type: concept
name: DataviewQueries
category: infrastructure
updated: 2026-06-28
source_count: 0
tags: [dataview, obsidian, queries]
---

# Dataview Queries

One-sentence summary: Dataview is an Obsidian community plugin that lets you query YAML frontmatter across notes using SQL-like syntax.

## Overview

All `journal/` entries written by `obsidian_write.py` include YAML frontmatter with trading metrics. Dataview can query across them to build rolling performance views.

## Frontmatter fields available in journal notes

| Field | Type | Description |
|---|---|---|
| `date` | date | Trading session date (YYYY-MM-DD) |
| `net_liq` | number | Total net liquidation across all brokers |
| `daily_pnl` | number | Realised daily P&L |
| `unrealised_pnl` | number | Unrealised P&L on open positions |
| `positions` | number | Count of open positions |
| `trades_today` | number | Number of trades executed |
| `brokers` | list | Brokers successfully synced |

## Useful queries

### Last 30 days P&L

```dataview
TABLE date, daily_pnl, unrealised_pnl, net_liq, positions
FROM "journal"
WHERE type = "journal"
SORT date DESC
LIMIT 30
```

### Days with trades

```dataview
TABLE date, trades_today, daily_pnl
FROM "journal"
WHERE trades_today > 0
SORT date DESC
```

### Net liquidation trend

```dataview
TABLE date, net_liq, daily_pnl
FROM "journal"
WHERE net_liq != null
SORT date ASC
```

### Broker sync failures

```dataview
TABLE date, brokers
FROM "journal"
WHERE length(brokers) < 4
SORT date DESC
```

## Open questions

- Add `strategy_breakdown` frontmatter once aggregator exposes per-strategy P&L
- Consider a weekly summary note type with rolled-up metrics

## Sources

| Source | Date | Notes |
|---|---|---|
| Dataview plugin docs | — | https://blacksmithgu.github.io/obsidian-dataview/ |
