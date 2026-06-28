---
type: entity
category: broker
name: Interactive Brokers
aliases: [IBKR, IB]
strategy: Algorithmic
asset_classes: [Equity, Futures, Options, ETF]
connection: ib_async
updated: 2026-06-28
---

# Interactive Brokers (IBKR)

## Role in Tanulytics
Primary broker for **algorithmic strategies** and **global macro** positioning. Connects via `ib_async` to TWS running locally.

## Connection
- Host: `127.0.0.1`, Port: `7497` (TWS) / `4001` (IB Gateway fallback)
- Read-only API mode — no order placement
- Script: [[ibkr_fetch.py]]

## Data provided
- Live open positions with entry price, market value, unrealised P&L
- Current session trades
- Account balances (net liq, cash, daily P&L)

## Known limitations
- Historical trades beyond current session require Flex Query CSV export
- TWS must be running and logged in before pipeline run

## Related
- [[GlobalMacro]], [[Algorithmic]]
- [[ibkr_fetch.py]]
