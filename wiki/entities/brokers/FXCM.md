---
type: entity
category: broker
name: FXCM
aliases: [FXCM]
strategy: Forex
asset_classes: [Forex, CFD]
connection: TradingView webhook
updated: 2026-06-28
---

# FXCM

## Role in Tanulytics
Execution broker for **forex and CFD strategies** (XAUUSD, crude, spreads). Connected via TradingView Pine Script alerts — not via direct API.

## Connection
- TradingView → cloudflared tunnel → `tv_webhook_server.py` → `data/raw/tv_fxcm_events.jsonl`
- `fxcmpy` is deprecated; webhook approach replaces it
- Script: [[fxcm_fetch.py]]

## Data provided
- Reconstructed positions from webhook event log
- Executed trade records from alert payloads

## Known limitations
- No live account balance or equity (no API connection)
- No unrealised P&L on open positions
- Reconcile weekly via FXCM CSV statement import

## Related
- [[Forex]], [[fxcm_fetch.py]], [[tv_webhook_server.py]]
