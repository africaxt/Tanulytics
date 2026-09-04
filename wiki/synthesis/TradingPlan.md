---
type: synthesis
name: AfricaX × Highland VC — Trading Plan
category: strategy
status: draft
updated: 2026-07-15
version: 1.1
source_count: 2
sources: ["HBC - IP & CT Overview_compressed.pdf", "Dbuntu Ai (Enterprise) wiki/entities"]
tags: [trading-plan, ips, treasury, commodities, hedging, africax, highland-vc, tanulytics]
---

# AfricaX × Highland VC — Trading Plan (v1.1)

> **One-line summary:** A two-book operating playbook. **Highland VC** is HBC's capital-preservation-first treasury book. The **AfricaX-linked hedging overlay** uses listed securities to protect the margin the group already carries in the physical crop trade — hedges *designed* by the [[AfricaX Trading]] risk model, *executed* in group-entity brokerage accounts, *advised* by [[Dbuntu LABS]], and *observed/reported* by [[Tanulytics]]. No speculation, no proprietary book.

**Advisor:** [[Dbuntu LABS]] (investment advisory — [[wiki/concepts/investment-advisory|KIFC]] target)
**System:** [[Tanulytics]] (read-only aggregation & signal system)
**Governing mandate:** HBC Investment Policy Statement (IPS) for MBZ Group Africa
**Effective:** 2026-07-15 · **Review cycle:** Quarterly (next 2026-10-15)

> **v1.1 change note:** Reconciled to the canonical entity/IP boundaries in the Dbuntu Ai (Enterprise) vault. Removed the "ring-fenced proprietary sleeve" (violated [[AfricaX Trading]]'s no-speculation mandate). Securities activity re-attributed to the HBC treasury layer, advised by Dbuntu LABS.

---

## 1. Purpose & governing context

This plan translates HBC's Investment Policy Statement into an executable trading playbook. It is an **internal operating document**, not an investor prospectus.

[[HBC]] (Highland Business Centre) is MBZ Group Africa's Group-CFO layer — corporate treasury, fixed income, and investment-advisory reporting. It sets the IPS, which governs excess liquidity, reserves, and long-term capital, with a stated purpose of **balance-sheet resilience and disciplined capital stewardship over speculative or proprietary trading**.

IPS objectives, in strict priority order:

1. **Capital preservation**
2. **Liquidity management**
3. **Risk-adjusted returns**
4. **Portfolio resilience through diversification**

Permitted assets: cash & equivalents, listed equities & ETFs, fixed income, cryptocurrencies, and **derivative hedging tools/strategies**. Execution is carried out by authorised group-entity brokerage accounts, in their own names, at regulated institutions (IPS §5).

### IP boundaries (non-negotiable — from the Enterprise entity register)

| Entity | Mandate | Must NOT |
|---|---|---|
| [[Ai4Ag]] | Farm/market **intelligence** — forecasts, climate & pricing signals | Trade, execute, or custody |
| [[MerchantX]] | **Physical** commodity trade execution methodology (operated by Bunyonyi Distributors / BDL under licence) | Speculate; use financial instruments |
| [[AfricaX Trading]] | **Risk-mitigation / hedging model IP** | Speculate; broker; custody |
| [[HBC]] | Corporate **treasury, fixed income, custody**, advisory reporting | — |
| [[Dbuntu LABS]] | **Investment advisory** (KIFC-regulated target) | Custody or execute (advisory only) |
| [[Tanulytics]] | Securities **aggregation & signals** | Place orders (read-only) |

**The operating principle:** Ai4Ag informs → AfricaX models the hedge → the hedge is executed in a group-entity brokerage account (custody at HBC) on Dbuntu LABS's advice → Tanulytics records and reports it. Every securities position must be either **(a) a treasury reserve holding** or **(b) a hedge/basis position tied to real physical exposure.** There is no third, speculative category.

---

## 2. Governance & roles

| Party | Role | Authority |
|---|---|---|
| [[HBC]] | Mandate owner + treasury/custody | Sets IPS limits, drawdown thresholds, rebalancing; holds the capital |
| [[Dbuntu LABS]] | Investment Advisor | Recommends allocations & hedges; advisory only — no custody, no execution |
| [[AfricaX Trading]] | Risk model | Supplies the hedge design/logic — no brokerage, no custody, no speculation |
| [[MerchantX]] / BDL | Physical execution | Times & executes the physical crop trades; bears execution risk |
| [[Tanulytics]] | System | Signals, backtests, read-only aggregation & reporting |
| Group entities (MBZ Global Management FZCO, others) | Brokerage & custody | Hold accounts in their own names; place all orders at regulated institutions (IPS §5) |

**Separation of duties:** Advisor advises, treasury holds, the model designs, the system reports, group entities execute. No Tanulytics script places orders ([[PipelineArchitecture]]).

---

## 3. The two books

### 3.1 Book overview

| | **Highland VC** | **AfricaX-linked hedging overlay** |
|---|---|---|
| Purpose | Preserve & grow Group treasury reserves | Protect physical-trade margin via listed hedges |
| Watchlist | [[HighlandVC]] | [[AfricaXTrading]] |
| Nature | Treasury reserve book | Hedge / basis overlay (risk mitigation only) |
| Designed by | HBC treasury policy | [[AfricaX Trading]] risk model |
| Executed in | Group-entity brokerage accounts (custody: HBC) | Group-entity brokerage accounts (custody: HBC) |
| IPS priority | Objectives 1→2→3→4 (preservation first) | Serves objective 1 (protects the physical book) |
| Return character | Capital preservation + modest carry | Margin protection + basis capture — not alpha |
| Max drawdown | 8% peak-to-trough | Hedge loss is bounded by the physical gain it offsets |

### 3.2 Highland VC — the treasury book

**Mandate:** Steward the Group's excess liquidity and long-term reserves within IPS limits. Capital *sleeps safely* here.

**Observed live holdings (HBC treasury statements):**
- **DFM equities / REITs (AED):** Emaar Properties (EMAAR), Dubai Residential REIT (DUBAIRESI) — MBZ Global Management FZCO via Emirates NBD.
- **Fixed income & money markets (UGX):** ~UGX 78.4M bonds + ~UGX 19.5M money markets via XENO (Uganda CMA-regulated).

**Target allocation ranges (to be ratified by HBC):**

| Sleeve | Range | Instruments | Role |
|---|---|---|---|
| Cash & equivalents | 10–30% | UGX/USD/AED money markets, T-bills | Liquidity buffer |
| Fixed income | 25–45% | UG govt bonds (XENO), global IG bond ETFs | Ballast, carry |
| Listed equity & ETF | 20–40% | DFM blue-chips/REITs, global index ETFs | Growth |
| Crypto sleeve | 0–7% | BTC, ETH (spot or regulated ETF) | Asymmetric diversifier — hard cap |
| Hedging derivatives | overlay | Index puts, FX forwards | Tail protection |

**Rules:** no single non-cash position >15%; crypto ≤7% hard; ≥10% redeemable in 48h; rebalance to mid-band on >5pt drift; −8% peak-to-trough circuit breaker → de-risk + escalate to HBC.

### 3.3 AfricaX-linked hedging overlay — the commodity book

**Mandate:** Use listed securities to hedge the price, FX, and freight risk the group already carries in the physical crop trade, and to monitor basis between local physical prices and global benchmarks. The [[AfricaX Trading]] model designs the hedge; execution sits in a group-entity brokerage account (custody at HBC), on Dbuntu LABS's advice. **AfricaX itself takes no positions, holds no custody, and does not speculate.** This is the book that lets you *"profit from all scenarios"* — meaning the physical margin is protected whether prices rise, fall, or move sideways.

**Physical basket → securities reality:**

| Physical crop | Group role | Nearest liquid benchmark | Instrument / ticker | Hedge quality |
|---|---|---|---|---|
| **Maize** | Core | CBOT Corn | ZC futures · CORN ETF · corn CFD | **Good** — EA white maize trades at a basis to yellow #2 |
| **Sorghum** | Core | *None* — basis to corn | Cross-hedge via CBOT Corn (ZC) | Moderate — China import demand a swing factor |
| **Barley** | Core | Euronext (wheat liquidity) | Euronext Milling Wheat (EBM) · CBOT Wheat (ZW) | Moderate — priced off the wheat complex |
| **Beans** (dry edible) | Core | *None* (≠ soybeans) | Weak proxy via Soybeans (ZS) | **Poor** — basis/informational |
| **Potatoes** | Core | *None post-2026* — EEX potato future delisted Jun 2026 | No clean listed hedge | **None** — pure physical/basis |
| **Sunflower seed** | Facilitation (live) | OTC/CFD only | Cross-hedge via Soybean Oil (ZL), Canola (RS), Rapeseed (ECO) | Moderate — oilseed-complex proxy |
| **Cashew nuts** | Facilitation (upcoming) | *None* anywhere | Thin equity proxies | **None** — informational/basis |

> **The "missing benchmark" thesis.** Five of seven items have *no clean listed hedge*. Where a benchmark exists (maize; cross-hedges for sorghum/barley/sunflower), the overlay hedges mechanically. Where none exists (potato, beans, cashew), the edge is **informational and basis-driven** — the exact gap [[Ai4Ag]] and [[MerchantX]] are built to close by creating local/regional/continental price references, in line with **AfCFTA**. Today the overlay hedges the securities that exist; over time the group helps *build the benchmarks that don't*.

---

## 4. "Profit from all scenarios" — the hedging matrix

The physical business (via [[MerchantX]] / BDL) is structurally **long the crop**. Each real exposure gets a defined securities-side hedge, so the *combined* physical + hedge position protects margin in every price scenario. Every row is risk-mitigation tied to a real position — none is speculative.

| # | Physical situation | Price move | Hedge (securities side) | Effect |
|---|---|---|---|---|
| 1 | Long physical inventory (bought, unsold) | Falls | **Short** benchmark proxy (ZC / ZL) | Futures gain offsets inventory loss — margin locked |
| 2 | Forward sale at fixed price (unsourced) | Rises | **Long** benchmark proxy | Futures gain offsets higher sourcing cost |
| 3 | Local cheap vs global (freight+FX adj.) | Converges | **Long physical / short future** | Capture the basis as it narrows (commercial margin) |
| 4 | Local rich vs global | Converges | **Long future / lighten physical** | Capture the basis from the other side |
| 5 | No-benchmark crop (potato/beans/cashew) | Any | Correlated macro: fertiliser, freight (BDRY), FX | Informational hedge where no direct instrument exists |
| 6 | UGX / AED / USD margin exposure | FX swings | **FX forward / CFD** overlay (FXCM) | Protect the currency leg of physical margins |

**Sizing discipline:** hedge notional ≤ 100% of the matched physical exposure — **never larger** (over-hedging would create a speculative position, which is out of mandate).

---

## 5. Tanulytics integration

[[Tanulytics]] generates signals, backtests them, supports execution, and aggregates everything into one read-only reporting layer.

### 5.1 Flow

```
Ai4Ag intelligence → AfricaX hedge model → Dbuntu LABS advice → group-entity execution
TradingView (Pine) → QuantConnect / VectorBT (backtest) → broker execution → aggregator.py
                                                                     → Airtable / Notion / Obsidian
```

### 5.2 Broker → rail mapping

| Broker | Strategy | Role in this plan |
|---|---|---|
| [[IBKR]] | Algorithmic + Global Macro | Commodity hedges (ZC, ZS, ZL, ZW), global ETFs |
| [[FXCM]] | Forex / CFDs | FX overlay + commodity CFDs (rows 1–6) |
| [[Schwab]] | Global Macro | Treasury ETFs, fixed-income & crypto ETFs |
| [[Robinhood]] | Value | Treasury equity sleeve (e.g. ADM, Bunge) |
| Emirates NBD (DFM) | *Treasury — outside aggregation* | Highland VC DFM equities/REITs |
| XENO | *Treasury — outside aggregation* | Highland VC UGX bonds & money markets |

> Emirates NBD and XENO sit outside the automated 4-broker fetch — reconcile **weekly** via CSV/manual import ([[PipelineArchitecture]]).

### 5.3 Watchlist linkage

- **[[HighlandVC]]** → treasury monitoring dashboard, checked against IPS bands.
- **[[AfricaXTrading]]** → hedge-design & basis engine; each symbol tagged to a physical crop and a matrix row (§4).

---

## 6. Risk framework

Layered on the IPS limits ([[RiskFramework]]).

- **Highland VC:** max 8% peak-to-trough; preservation dominates.
- **Hedging overlay:** hedge notional ≤ matched physical exposure; the overlay's loss in any scenario is bounded by the offsetting physical gain (that is the definition of a hedge). No standalone directional risk budget, because there is no directional book.
- **FX:** UGX not directly tradable on these brokers — hedge via USD/AED crosses & DXY on FXCM; monitor residual UGX basis.
- **Liquidity:** no position larger than can be exited in one trading day without material slippage.
- **Correlation:** cap aggregate soy-complex delta (sunflower + beans both lean on the soy complex).
- **Mandate breach escalation:** any over-hedge (which would create a speculative position), drawdown breach, or IPS band violation is logged and escalated to HBC within 24h.

---

## 7. Operating cadence

**Daily** — Tanulytics run; review both watchlists; confirm every open position is either a treasury holding or a hedge tied to live physical exposure; log Market Context.

**Weekly** — Reconcile Emirates NBD & XENO; review maize/sunflower basis vs benchmarks; re-check hedge ratios against current physical inventory & forward book; rebalance Highland VC bands if breached.

**Monthly** — Attribution by book; confirm no position has drifted out of mandate; update watchlists for new facilitation deals (e.g. cashew).

**Quarterly** — HBC review: IPS bands, drawdown thresholds, and roadmap check-in with [[Ai4Ag]] / [[MerchantX]] on benchmark-building.

---

## 8. Roadmap — building the missing benchmarks

- **Near term:** hedge the liquid proxies (ZC, ZL, ZW, canola/rapeseed); use informational/basis edge on no-benchmark crops.
- **Medium term:** [[Ai4Ag]] price discovery + [[MerchantX]] marketplace generate local/regional reference prices for potato, beans, sorghum, cashew.
- **Long term (AfCFTA-aligned):** the group becomes an early reference/liquidity provider in a continental commodities ecosystem — turning the "missing benchmark" gap into a franchise.

---

## 9. Open questions

- Which group entity books the hedges (MBZ Global Management FZCO vs a dedicated vehicle), and is the account already open in its own name (IPS §5)?
- KIFC investment-advisory licence status for [[Dbuntu LABS]] — does any advice need to wait on it?
- Crypto sleeve: spot custody vs regulated ETF given UAE/Uganda jurisdictions?
- Confirm the AfricaX model's hedge-ratio outputs are consumable by Tanulytics for automated reconciliation.

---

## Sources

| File | Date | Key takeaway |
|---|---|---|
| HBC - IP & CT Overview_compressed.pdf | 2026-01-26 | IPS objectives, permitted assets, treasury statements |
| Dbuntu Ai (Enterprise) wiki/entities | 2026-06-28 | Canonical IP boundaries: AfricaX no-spec, MerchantX physical-only, Ai4Ag intelligence-only, Dbuntu LABS advisory |
| EEX potato delisting; Euronext wheat; oilseed cross-hedge | 2026-07 | Most of the basket has no clean listed hedge |

## Related
[[HighlandVC]] · [[AfricaXTrading]] · [[HBC]] · [[Dbuntu LABS]] · [[AfricaX Trading]] · [[MerchantX]] · [[Ai4Ag]] · [[Tanulytics]] · [[PortfolioOverview]] · [[RiskFramework]] · [[PipelineArchitecture]]
