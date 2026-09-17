---
type: entity
category: watchlist
name: Highland VC
source_count: 1
sources: ["HBC - IP & CT Overview_compressed.pdf"]
date: 2026-07-12
updated: 2026-07-12
status: monitoring
tags: [watchlist, treasury, ips, highland-vc]
---

# Highland VC — Watchlist

## Summary

The treasury/reserve watchlist for [[HBC]]'s IPS book. Tracks the permitted, capital-preservation-first instruments the Group holds as excess liquidity and long-term reserves. Governed by [[TradingPlan]] §3.2 — capital preservation → liquidity → risk-adjusted return → diversification, in that order.

## Key facts

| Sleeve | Watchlist members | Notes |
|---|---|---|
| DFM equity / REIT | Emaar Properties (EMAAR), Dubai Residential REIT (DUBAIRESI) | Held via MBZ Global Management FZCO / Emirates NBD (AED) |
| Fixed income | UG govt bonds (via XENO), global IG bond ETFs | XENO regulated by Uganda CMA (UGX) |
| Cash & equivalents | UGX/USD/AED money markets, T-bills | Liquidity buffer, ≥10% redeemable in 48h |
| Crypto sleeve | BTC, ETH (spot or regulated ETF) | 0–7% hard cap |
| Hedging overlay | Index puts, FX forwards | Tail protection only |

**Rules**
- No single non-cash position > 15% of the book.
- Rebalance to mid-band when a sleeve drifts > 5 pts.
- Book circuit breaker: −8% peak-to-trough → de-risk + escalate to HBC.

## Cross-references
[[TradingPlan]] · [[AfricaXTrading]] · [[RiskFramework]] · [[PortfolioOverview]]

## Open questions
- Which entity custodies the crypto sleeve, and spot vs regulated ETF given UAE/Uganda jurisdictions?
- Confirm current DFM holdings beyond EMAAR/DUBAIRESI.

## Sources

| File | Date | Key takeaway |
|---|---|---|
| HBC - IP & CT Overview_compressed.pdf | 2026-01-26 | Permitted assets, treasury statements (Emirates NBD DFM; XENO bonds/MMF) |
