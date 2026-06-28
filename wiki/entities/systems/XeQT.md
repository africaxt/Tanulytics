---
type: entity
category: system
name: XeQT
aliases: [XeQT, Trade Execution System]
layer: Trade Execution
infrastructure: Google Cloud Platform
source_count: 1
sources: [raw/reports/TraderChit-by-Tanulytics-v2.pdf]
updated: 2026-06-28
tags: [xeqt, execution, trading-algorithm, order-management]
---

# XeQT

## Summary
XeQT (Trade Execution System) is the execution layer of TraderChit. It receives a Target Portfolio from [[LearnAI]], compares it to the Live Portfolio, and routes orders to exchanges via broker APIs. Strategy code lives in `strategies/chit/XeQT/`.

## Architecture

```
Target Portfolio  ←  [[LearnAI]]
      ↓
Trading Algorithm  ←  Live Portfolio
      ↓
Order  →  Exchange
      ↓
Live Portfolio (updated)  →  back to [[LearnAI]]
```

## Broker integrations

| Broker | Strategy | Code path |
|---|---|---|
| [[IBKR]] | Algorithmic / Global Macro | `strategies/chit/XeQT/ibkr/` |
| [[FXCM]] | Forex / CFDs | `strategies/chit/XeQT/fxcm/` |
| [[Schwab]] | Global Macro | `strategies/chit/XeQT/schwab/` |
| [[Robinhood]] | Value Investing | `strategies/chit/XeQT/robinhood/` |

## Key responsibilities
- Receive Target Portfolio from LearnAI Portfolio Optimizer
- Diff against Live Portfolio to determine required trades
- Route orders via broker APIs (IBKR TWS, Schwab OAuth, Robinhood, FXCM webhook)
- Feed Live Portfolio state back to LearnAI

## Relation to trading components (UCL framework)
XeQT covers the **Trading Execution** and **Post-trade Analysis** layers:
- Trading Algorithm → Execution Model
- Order → Exchange
- Resulting Live Portfolio feeds back into [[LearnAI]] Current Portfolio input

## Data extraction
The Tanulytics pipeline (`run_all.py`) reads XeQT's live state via broker APIs and normalises it into the aggregated schema for Airtable and Notion. XeQT itself is **read-only** from the pipeline's perspective — no orders are placed by the data scripts.

## Open questions
- Is the Trading Algorithm rule-based, adaptive, or a hybrid?
- Does XeQT handle partial fills and slippage feedback to LearnAI?
- Where does post-trade analysis output go — back into Historical Data?

## Sources

| File | Date | Key takeaway |
|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | 2026-06-28 | XeQT architecture: Trading Algorithm, Exchange routing, Live Portfolio feedback loop |
