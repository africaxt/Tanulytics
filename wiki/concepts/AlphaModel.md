---
type: concept
name: Alpha Model
layer: Pre-trade Analysis
framework: UCL Trading Components
source_count: 1
sources: [raw/reports/TraderChit-by-Tanulytics-v2.pdf]
updated: 2026-06-28
tags: [alpha, forecast, signal]
---

# Alpha Model

## Summary
The Alpha Model generates return forecasts (alpha signals) from market data. In TraderChit, this is implemented by [[LearnAI]]'s Forecasting Algorithm → N-Day Forecast pipeline.

## Role in the trading stack
Sits in the **Pre-trade Analysis** layer of the UCL Trading Components framework, alongside the [[RiskModel]] and [[TransactionCostModel]]. All three feed into the [[PortfolioConstructionModel]].

```
Data → Alpha Model → ↘
Data → Risk Model  →  Portfolio Construction Model → Execution
Data → TCM         → ↗
```

## TraderChit implementation
- **Input**: Information Feed + Historical Data
- **Model**: Forecasting Algorithm (ML-based, see [[LearnAI]])
- **Output**: N-Day Forecast → Portfolio Optimizer

## Open questions
- What signal horizon does the alpha model target? (intraday, daily, weekly)
- Are signals per-instrument or portfolio-level?

## Sources

| File | Date | Key takeaway |
|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | 2026-06-28 | Defined as pre-trade analysis component in UCL framework |
