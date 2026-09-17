---
type: concept
name: Transaction Cost Model
aliases: [TCM, Transaction Cost]
layer: Pre-trade Analysis
framework: UCL Trading Components
source_count: 1
sources: [raw/reports/TraderChit-by-Tanulytics-v2.pdf]
updated: 2026-06-28
tags: [tcm, costs, slippage, commission]
---

# Transaction Cost Model (TCM)

## Summary
The TCM estimates the cost of executing a trade — commissions, slippage, spread, and market impact. It feeds into the [[PortfolioConstructionModel]] alongside [[AlphaModel]] and [[RiskModel]] to ensure alpha net of costs justifies the trade.

## Role
Without a TCM, the Portfolio Optimizer would over-trade, eroding alpha through execution costs. The TCM acts as a friction term on portfolio rebalancing decisions.

## Open questions
- Are costs modelled per-broker (IBKR vs Schwab have very different commission structures)?
- Is market impact modelled for less liquid positions?
- Does the TCM feed slippage data back from [[XeQT]] post-execution?

## Sources

| File | Date | Key takeaway |
|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | 2026-06-28 | Pre-trade analysis component in UCL framework |
