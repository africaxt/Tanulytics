---
type: index
updated: 2026-06-28
---

# Wiki Index

> This file is maintained by Claude. Updated on every ingest and lint pass.
> Read this first when answering any query to identify relevant pages.

## How to use
- Each entry: `[[page-link]] — one-line summary`
- After ingesting a new source or creating a new page, append it to the correct section
- On lint, verify all links resolve and summaries are still accurate

---

## Entities — Brokers

| Page | Summary |
|---|---|
| [[IBKR]] | Interactive Brokers — algorithmic & global macro, ib_async connection |
| [[FXCM]] | FXCM — forex/CFDs via TradingView webhook pipeline |
| [[Schwab]] | Charles Schwab — global macro, OAuth via schwabdev |
| [[Robinhood]] | Robinhood — US equities & options value investing, robin_stocks |

## Entities — Systems

| Page | Summary |
|---|---|
| [[LearnAI]] | Machine Learning AI subsystem — forecasting, portfolio optimisation, runs on GCP |
| [[XeQT]] | Trade Execution System — trading algorithm, order routing, broker connectivity |

## Entities — Strategies

| Page | Summary |
|---|---|
| [[Algorithmic]] | Rule-based algo strategies running on IBKR via LEAN/QuantConnect |
| [[Forex]] | Intraday forex/CFD strategies (XAUUSD, crude, spreads) via FXCM |
| [[GlobalMacro]] | Macro positioning across equities and bonds via Schwab |
| [[ValueInvesting]] | Long-horizon US equity + options via Robinhood |

## Concepts

| Page | Summary |
|---|---|
| [[RiskFramework]] | AfricaX Trading risk protocols — daily loss limits, position sizing, circuit breakers |
| [[PipelineArchitecture]] | Tanulytics data pipeline: brokers → aggregator → Airtable → Notion → Obsidian |
| [[AlphaModel]] | Forecasting signal layer (UCL framework) — implemented by LearnAI Forecasting Algorithm |
| [[RiskModel]] | Portfolio risk constraints in pre-trade analysis — feeds Portfolio Optimizer |
| [[TransactionCostModel]] | Cost estimation (commission, slippage) — friction term in portfolio optimisation |
| [[PortfolioConstructionModel]] | Synthesises alpha + risk + TCM into Target Portfolio — LearnAI Portfolio Optimizer |
| [[DecisionEngine]] | Human-computer UI checkpoint between signal generation and execution |
| [[GCPInfrastructure]] | Google Cloud Platform — hosts LearnAI and XeQT |
| [[DataviewQueries]] | Obsidian Dataview queries for journal YAML frontmatter |

## Comparisons

_None yet. Add comparison pages here as they are created._

## Synthesis

| Page | Summary |
|---|---|
| [[PortfolioOverview]] | Rolling synthesis of cross-broker portfolio state and performance |

## Sources (raw/)

| File | Type | Ingested | Summary |
|---|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | report | 2026-06-28 | TraderChit architecture: LearnAI, XeQT, UCL trading components, GCP infrastructure, operational timeline |

---
tags: index meta
