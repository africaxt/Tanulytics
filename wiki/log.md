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

## [2026-06-28] notion-sync | Sourced live Notion context; implemented system-of-record split

**Notion pages read:**
- Portfolio page (a0124ec5): Rich fund dashboard — strategy allocation, products/services, personal philosophy. No pipeline output present yet.
- Mindset Stack (35ec9f23): 13 habits across Body/Mind/Capital/Enterprise. Morning check-in with Claude. Habit Log, Golf Score Log, Weekly Reviews DBs.
- Daily Review DB (2c2c9f23): Confirmed live in Portfolio page sidebar.

**Changes made:**
- `config/.env` — created with rotated FXCM secret + real Notion IDs
- `scripts/notion_summary.py` — removed Mindset Stack root fallback; Daily Review push now creates entry if none exists
- `scripts/obsidian_write.py` — added YAML frontmatter (net_liq, daily_pnl, unrealised_pnl, positions, trades_today, brokers) for Dataview queries; frontmatter updated on each repeat run
- `CLAUDE.md` — added System of Record table defining each layer's authoritative role

**System of record:**
- Airtable = source of truth (structured, queryable)
- Notion Portfolio = external reporting callout
- Notion Daily Review = morning check-in market context (1 line)
- Obsidian journal = private metrics (YAML) + reflection sections
- Obsidian wiki = knowledge accumulation
