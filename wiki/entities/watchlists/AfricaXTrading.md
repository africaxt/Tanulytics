<<<<<<< HEAD
---
type: entity
category: watchlist
name: AfricaX Trading
source_count: 1
sources: ["HBC - IP & CT Overview_compressed.pdf"]
date: 2026-07-12
updated: 2026-07-12
status: monitoring
tags: [watchlist, commodities, hedging, basis, africax]
---

# AfricaX Trading — Watchlist

## Summary

The commodity-linked watchlist mirroring the Group's physical agricultural trade. Each symbol is tagged to a physical crop and a play-matrix row so securities positions hedge, basis-trade, or express views tied to real exposure. Governed by [[TradingPlan]] §3.3–§4.

## Key facts

**Physical basket → listed proxy**

| Physical crop | Proxy instrument | Hedge quality |
|---|---|---|
| Maize | CBOT Corn (ZC), CORN ETF | Good |
| Sorghum | Cross-hedge via CBOT Corn (ZC) | Moderate |
| Barley | Euronext Milling Wheat (EBM), CBOT Wheat (ZW) | Moderate |
| Beans (dry edible) | Weak macro proxy — Soybeans (ZS) | Poor / informational |
| Potatoes | No listed hedge (EEX potato future delisted Jun 2026) | None / basis |
| Sunflower seed | Soybean Oil (ZL), ICE Canola (RS), Euronext Rapeseed (ECO) | Moderate |
| Cashew nuts | No futures anywhere | None / informational |

**Support & overlay symbols**
- **Freight:** BDRY (dry bulk) — proxy for landed-cost moves on no-benchmark crops.
- **FX:** DXY, USD crosses (FXCM) — hedge the currency leg of physical margins (UGX/AED/USD).
- **Agribusiness equities:** ADM, Bunge (BG) — value-sleeve expression via [[Robinhood]].
- **Inputs:** fertiliser proxies — correlated macro for potato/beans/cashew.

**Rules**
- Hedge notional ≤ 100% of matched physical exposure (no over-hedging).
- Basis & proprietary trades draw only from the capped AfricaX risk budget.
- Cap aggregate soy-complex delta (sunflower + beans overlap).

## Cross-references
[[TradingPlan]] · [[HighlandVC]] · [[AfricaX Trading]] · [[Ai4Ag]] · [[MerchantX]] · [[RiskFramework]] · [[FXCM]] · [[Robinhood]]

## Open questions
- Which no-benchmark crops (potato, beans, cashew) warrant a proprietary local reference price via [[Ai4Ag]] / [[MerchantX]] first?
- Confirm liquid CFD availability for corn/wheat/soy-oil on the FXCM feed.

## Sources

| File | Date | Key takeaway |
|---|---|---|
| HBC - IP & CT Overview_compressed.pdf | 2026-01-26 | Group context; treasury vs proprietary mandate separation |
| Commodity instrument mapping (EEX, Euronext, oilseed cross-hedge) | 2026-07 | Most of the basket has no clean listed hedge |
=======
---
type: entity
category: watchlist
name: AfricaX Trading
source_count: 1
sources: ["HBC - IP & CT Overview_compressed.pdf"]
date: 2026-07-12
updated: 2026-07-12
status: monitoring
tags: [watchlist, commodities, hedging, basis, africax]
---

# AfricaX Trading — Watchlist

## Summary

The commodity-linked watchlist mirroring the Group's physical agricultural trade. Each symbol is tagged to a physical crop and a play-matrix row so securities positions hedge, basis-trade, or express views tied to real exposure. Governed by [[TradingPlan]] §3.3–§4.

## Key facts

**Physical basket → listed proxy**

| Physical crop | Proxy instrument | Hedge quality |
|---|---|---|
| Maize | CBOT Corn (ZC), CORN ETF | Good |
| Sorghum | Cross-hedge via CBOT Corn (ZC) | Moderate |
| Barley | Euronext Milling Wheat (EBM), CBOT Wheat (ZW) | Moderate |
| Beans (dry edible) | Weak macro proxy — Soybeans (ZS) | Poor / informational |
| Potatoes | No listed hedge (EEX potato future delisted Jun 2026) | None / basis |
| Sunflower seed | Soybean Oil (ZL), ICE Canola (RS), Euronext Rapeseed (ECO) | Moderate |
| Cashew nuts | No futures anywhere | None / informational |

**Support & overlay symbols**
- **Freight:** BDRY (dry bulk) — proxy for landed-cost moves on no-benchmark crops.
- **FX:** DXY, USD crosses (FXCM) — hedge the currency leg of physical margins (UGX/AED/USD).
- **Agribusiness equities:** ADM, Bunge (BG) — value-sleeve expression via [[Robinhood]].
- **Inputs:** fertiliser proxies — correlated macro for potato/beans/cashew.

**Rules**
- Hedge notional ≤ 100% of matched physical exposure (no over-hedging).
- Basis & proprietary trades draw only from the capped AfricaX risk budget.
- Cap aggregate soy-complex delta (sunflower + beans overlap).

## Cross-references
[[TradingPlan]] · [[HighlandVC]] · [[AfricaX Trading]] · [[Ai4Ag]] · [[MerchantX]] · [[RiskFramework]] · [[FXCM]] · [[Robinhood]]

## Open questions
- Which no-benchmark crops (potato, beans, cashew) warrant a proprietary local reference price via [[Ai4Ag]] / [[MerchantX]] first?
- Confirm liquid CFD availability for corn/wheat/soy-oil on the FXCM feed.

## Sources

| File | Date | Key takeaway |
|---|---|---|
| HBC - IP & CT Overview_compressed.pdf | 2026-01-26 | Group context; treasury vs proprietary mandate separation |
| Commodity instrument mapping (EEX, Euronext, oilseed cross-hedge) | 2026-07 | Most of the basket has no clean listed hedge |
>>>>>>> c4461662d3e0c9889d8bb1ae887650fcc7835c35
