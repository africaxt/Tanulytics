---
type: entity
category: broker
name: Charles Schwab
aliases: [Schwab]
strategy: GlobalMacro
asset_classes: [Equity, ETF, Options]
connection: schwabdev OAuth
updated: 2026-06-28
---

# Charles Schwab

## Role in Tanulytics
Primary broker for **global macro** positioning — broad market ETFs, sector rotations, macro thematic trades.

## Connection
- `schwabdev` wrapper around official Schwab Trader API
- OAuth token auto-refreshed; tokens cached at `config/.schwab_tokens.json`
- Access token: 30 min; Refresh token: 7 days (must run weekly to keep alive)
- Script: [[schwab_fetch.py]]

## Data provided
- Account balances (net liq, cash, buying power)
- Open positions with market value
- Recent transactions

## Known limitations
- First run requires browser OAuth login
- Refresh token expires if pipeline not run for >7 days

## Related
- [[GlobalMacro]], [[schwab_fetch.py]]
