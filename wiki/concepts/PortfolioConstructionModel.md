---
type: concept
name: Portfolio Construction Model
layer: Trading Signal
framework: UCL Trading Components
source_count: 1
sources: [raw/reports/TraderChit-by-Tanulytics-v2.pdf]
updated: 2026-06-28
tags: [portfolio-construction, optimisation, target-portfolio]
---

# Portfolio Construction Model

## Summary
The Portfolio Construction Model synthesises [[AlphaModel]] forecasts, [[RiskModel]] constraints, and [[TransactionCostModel]] estimates into a Target Portfolio — the optimal set of positions to hold. Output feeds directly to [[XeQT]] for execution.

## Role in the stack
The output of pre-trade analysis. Takes three inputs and produces one output:

```
Alpha Model  →  ↘
Risk Model   →   Portfolio Construction Model → Target Portfolio → XeQT
TCM          →  ↗
```

## TraderChit implementation
Implemented as the **Portfolio Optimizer** inside [[LearnAI]]. Takes the N-Day Forecast, Current Portfolio state, and risk/cost constraints to produce the Target Portfolio.

## Open questions
- What optimisation method is used — mean-variance, Black-Litterman, risk parity?
- Are there hard constraints (e.g. max position per broker, no shorting on Robinhood)?
- How often does the model reoptimise — daily, intraday, event-driven?

## Sources

| File | Date | Key takeaway |
|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | 2026-06-28 | Trading Signal layer; bridges pre-trade analysis and execution |
