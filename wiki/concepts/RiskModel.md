---
type: concept
name: Risk Model
layer: Pre-trade Analysis
framework: UCL Trading Components
source_count: 1
sources: [raw/reports/TraderChit-by-Tanulytics-v2.pdf]
updated: 2026-06-28
tags: [risk, position-sizing, drawdown]
---

# Risk Model

## Summary
The Risk Model quantifies portfolio risk (volatility, correlation, drawdown exposure) used as a constraint in the Portfolio Optimizer. Part of the pre-trade analysis layer alongside [[AlphaModel]] and [[TransactionCostModel]].

## Role
Constrains the [[PortfolioConstructionModel]] — ensures Target Portfolio stays within acceptable risk bounds before orders are sent to [[XeQT]].

## Relation to AfricaX risk framework
The operational expression of this is the [[RiskFramework]] — daily loss limits, position size constraints, circuit breakers. The Risk Model is the quantitative input; the Risk Framework is the protocol enforcement.

## Open questions
- Is risk modelled per-broker or across the consolidated book?
- What risk metrics are used — VaR, CVaR, max drawdown, Sharpe?
- Does the model update intraday or only pre-market?

## Sources

| File | Date | Key takeaway |
|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | 2026-06-28 | Pre-trade analysis component in UCL framework |
