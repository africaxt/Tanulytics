---
type: entity
category: system
name: LearnAI
aliases: [LearnAI, Learn AI, ML AI]
layer: Machine Learning AI
infrastructure: Google Cloud Platform
source_count: 1
sources: [raw/reports/TraderChit-by-Tanulytics-v2.pdf]
updated: 2026-06-28
tags: [learnai, ml, forecasting, portfolio-optimisation]
---

# LearnAI

## Summary
LearnAI is the Machine Learning AI subsystem of TraderChit. It ingests market data and generates N-day price forecasts, feeds them into a Portfolio Optimizer to produce a Target Portfolio, and hands off to [[XeQT]] for execution. Runs on [[GCPInfrastructure]].

## Architecture

```
Information Feed
      ↓
Forecasting Algorithm  ←→  Historical Data
      ↓
N-Day Forecast
      ↓
Portfolio Optimizer  ←  Current Portfolio
      ↓
Target Portfolio  →→→  [[XeQT]]
```

## Components

| Component | Role |
|---|---|
| Information Feed | External market data, news, signals fed into the model |
| Forecasting Algorithm | ML model producing N-day price/return forecasts |
| N-Day Forecast | Output predictions for the next N trading days |
| Portfolio Optimizer | Constructs optimal weights given forecast + constraints |
| Historical Data | Shared data store used by both forecasting and optimisation |
| Current Portfolio | State fed in from [[XeQT]] (live portfolio snapshot) |
| Target Portfolio | Output: desired allocation handed to XeQT for execution |

## Relation to trading components (UCL framework)
LearnAI covers the **Pre-trade Analysis** layer:
- Forecasting Algorithm → [[AlphaModel]]
- Portfolio Optimizer incorporates → [[RiskModel]] + [[TransactionCostModel]]
- Output feeds → [[PortfolioConstructionModel]]

## Infrastructure
Runs on **Google Cloud Platform**. See [[GCPInfrastructure]].

## Open questions
- Which ML models power the Forecasting Algorithm? (decision tree, LSTM, ensemble?)
- What is N in the N-day forecast? Configurable per strategy?
- How are Information Feeds sourced — vendor data, internal signals, or both?
- How does Portfolio Optimizer handle cross-broker constraints?

## Sources

| File | Date | Key takeaway |
|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | 2026-06-28 | Architecture diagrams for LearnAI subsystem and GCP computing infrastructure |
