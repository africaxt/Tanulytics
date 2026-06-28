---
type: log
---

# Wiki Log

> Append-only. One entry per ingest, query, or lint pass.
> Format: `## [YYYY-MM-DD] <operation> | <title>`
> Parse with: `grep "^## \[" wiki/log.md | tail -10`

---

## [2026-06-28] init | Wiki initialised

- Created three-layer structure: `raw/` → `wiki/` → schema (CLAUDE.md)
- Seed entity pages created for 4 brokers and 4 strategies
- Index and log files established
- Karpathy LLM Wiki pattern adopted

## [2026-06-28] ingest | TraderChit by Tanulytics v2.pdf

- Source: `raw/reports/TraderChit-by-Tanulytics-v2.pdf`
- Pages created: `entities/systems/LearnAI`, `entities/systems/XeQT`
- Concepts created: `AlphaModel`, `RiskModel`, `TransactionCostModel`, `PortfolioConstructionModel`, `DecisionEngine`, `GCPInfrastructure`
- Pages updated: `entities/strategies/Algorithmic`, `concepts/PipelineArchitecture`
- `wiki/index.md` updated — systems section added, all 6 new concepts listed, source recorded
- Key finding: Tanulytics pipeline sits downstream of LearnAI → XeQT; the pipeline extracts state, not drives execution
