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

## [2026-07-15] synthesis | AfricaX × Highland VC Trading Plan v1.0

- Source: `uploads/HBC - IP & CT Overview_compressed.pdf` (HBC IPS + group treasury statements)
- Pages created: `synthesis/TradingPlan`, `entities/watchlists/HighlandVC`, `entities/watchlists/AfricaXTrading`
- Also delivered: `synthesis/TradingPlan.docx` (formatted Word version)
- `wiki/index.md` updated — new "Entities — Watchlists" section; TradingPlan added to Synthesis; HBC source recorded
- Two-book model: Highland VC (senior IPS treasury) vs AfricaX (junior, capped hedge/basis + ring-fenced proprietary) — squares Tanulytics' proprietary mandate with the IPS's capital-preservation-first priority
- Key finding: 5 of 7 crops in the AfricaX basket (potato, sorghum, beans, cashew, + post-Jun-2026 potato delisting) have no clean listed hedge — the "missing benchmark" gap Ai4Ag/MerchantX are positioned to close under AfCFTA

## [2026-07-15] reconcile | TradingPlan v1.1 aligned to Enterprise IP boundaries

- Cross-checked against the Dbuntu Ai (Enterprise) entity register
- Removed the "ring-fenced proprietary sleeve" — it violated AfricaX Trading's non-negotiable mandate (no speculation / no brokerage / no custody)
- Re-attributed securities activity to the HBC treasury layer, advised by Dbuntu LABS; AfricaX designs hedges only; MerchantX/BDL do physical execution; Ai4Ag is intelligence-only
- Added an IP-boundary table (§1) and dropped matrix row 7; §4 is now purely hedging tied to real physical exposure
- Aligned wikilinks to canonical names: [[HBC]], [[Dbuntu LABS]], [[AfricaX Trading]], [[MerchantX]], [[Ai4Ag]], [[Tanulytics]]
- Created Notion-canonical pointer stubs under `wiki/entities/` (HBC, Dbuntu LABS, AfricaX Trading, MerchantX, Ai4Ag, Tanulytics) so links resolve locally while Notion stays the single source of truth
- Enterprise vault: added `wiki/entities/Tanulytics.md`, updated its index (14→15) and log

## [2026-09-10] reorg | Airtable bases + TradingPlan v1.2 — three-entity model locked

- **Model locked:** Tanulytics = securities · MerchantX = physical · AfricaX Trading = facilitation & hedging · HBC = treasury.
- **Airtable `Tanulytics – Trade Log`** (renamed from "Alvin B. Mbabazi - Trade Log") is now the securities system of record: `Trades` augmented with securities columns (Broker, Asset Class, Direction, Entry/TP/SL/Exit USD, P&L USD, Strategy, Broker Position ID, Currency, Fees, Month, Year); `Securities` master (17 tickers incl. XAU/XAG) linked to `Markets` (market types); `Logistics Partners` → renamed `Brokers` (FXCM/IBKR/Schwab/Robinhood); `Partners` + `Transactions` hold the capital ledger.
- **Migrations:** physical trades + reference data (markets/partners/logistics) → MerchantX; MerchantX securities (Trades + Securities master) → Tanulytics; MerchantX `Investment` (capital contributions) → Tanulytics `Partners`/`Transactions` (deduped, 3 duplicate deposits dropped).
- **Logged the live FXCM trades:** XAU/USD (ID 75013713) & XAG/USD (ID 75013742) in `Trades`, linked to Securities/Brokers; rationale in `notes/theses/XAUUSD`, `notes/theses/XAGUSD`, and `journal/2026-09-10`.
- **Docs updated:** `TradingPlan` v1.1→v1.2 (three-entity division + Airtable system-of-record); `CLAUDE.md` ecosystem-division section added; Enterprise `AGENTS.md` IP-boundary rules updated (AfricaX = facilitation & hedging; Tanulytics = securities); `wiki/entities/AfricaX Trading` stub updated.
- **Open:** `TradingPlan.docx` still v1.1 (regenerate if a fresh Word copy is needed); vestigial physical UGX columns remain on the `Trades` table (removable on request).

