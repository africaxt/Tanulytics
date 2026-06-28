---
type: entity
category: broker
name: Robinhood
aliases: [Robinhood, RH]
strategy: ValueInvesting
asset_classes: [Equity, Options]
connection: robin_stocks (unofficial)
updated: 2026-06-28
---

# Robinhood

## Role in Tanulytics
Broker for **value investing** — long-horizon US equities and options positions.

## Connection
- `robin_stocks` unofficial wrapper with TOTP-automated 2FA via `pyotp`
- Session cached at `~/.tokens/robinhood.pickle` (~24h)
- Script: [[robinhood_fetch.py]]

## Data provided
- Holdings with current value and cost basis
- Order history

## Known limitations
- Unofficial API — can break without notice if Robinhood changes endpoints
- Fallback: weekly CSV export from Robinhood website

## Related
- [[ValueInvesting]], [[robinhood_fetch.py]]
