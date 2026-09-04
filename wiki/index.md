---
type: index
updated: 2026-07-15
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

## Entities — Watchlists

| Page | Summary |
|---|---|
| [[HighlandVC]] | Treasury/IPS reserve watchlist — DFM equities/REITs, fixed income, cash, crypto sleeve, hedges |
| [[AfricaXTrading]] | Commodity-linked watchlist mirroring the physical crop basket — hedge/basis proxies per crop |

## Entities — Group register (Notion-canonical pointers)

> Source of truth lives in Notion (Dbuntu Ai Enterprise). These are thin pointer stubs so `[[links]]` resolve in this vault; edit content in Notion.

| Page | Canonical | Summary |
|---|---|---|
| [[HBC]] | Notion | Group-CFO layer — treasury, fixed income, custody, advisory reporting |
| [[Dbuntu LABS]] | Notion | HQ / IP layer; KIFC-target Investment Advisor |
| [[AfricaX Trading]] | Notion | Risk/hedging model IP — no speculation/brokerage/custody |
| [[MerchantX]] | Notion | Physical commodity execution methodology (BDL) |
| [[Ai4Ag]] | Notion | Farm/market intelligence platform (intelligence only) |
| [[Tanulytics]] | Notion | Proprietary securities aggregation & signal system (this vault) |

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
| [[TradingPlan]] | AfricaX × Highland VC two-book operating playbook (v1.0) — treasury + commodity books under the HBC IPS |

## Sources (raw/)

| File | Type | Ingested | Summary |
|---|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | report | 2026-06-28 | TraderChit architecture: LearnAI, XeQT, UCL trading components, GCP infrastructure, operational timeline |
| [[HBC - IP & CT Overview_compressed.pdf]] | mandate | 2026-07-15 | HBC IPS: four objectives, permitted assets, treasury statements (MBZ Global Management FZCO / Emirates NBD; XENO) |

---
tags: index meta
