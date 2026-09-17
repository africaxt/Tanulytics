---
type: entity
category: strategy
name: Forex
broker: FXCM
timeframe: Intraday
asset_classes: [Forex, CFD]
pairs: [XAUUSD, crude oil, Brent/WTI spread]
updated: 2026-06-28
---

# Forex / CFD Strategy

## Overview
Intraday forex and CFD strategies executed via FXCM, signalled from TradingView Pine Script alerts.

## Active instruments
- XAUUSD (gold)
- Crude oil
- Brent/WTI spread

## Stack
- Signal + execution trigger: TradingView alerts → webhook
- Data capture: `tv_webhook_server.py`
- Strategy code: [[]]

## Related
- [[FXCM]]
