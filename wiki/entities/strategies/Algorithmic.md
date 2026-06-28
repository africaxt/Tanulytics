---
type: entity
category: strategy
name: Algorithmic
broker: IBKR
timeframe: Intraday to Swing
updated: 2026-06-28
---

# Algorithmic Strategy

## Overview
Rule-based systematic strategies executed via IBKR. Signal generation in TradingView (Pine Script), backtesting on QuantConnect (LEAN) and VectorBT locally, live execution via IBKR TWS.

## Stack
- Signal: TradingView Pine Script
- Backtest: QuantConnect LEAN (primary), VectorBT (local)
- Execution: IBKR TWS (read-only data extraction)
- Strategy code: [[]]

## Related
- [[IBKR]], [[PipelineArchitecture]]

## System context
- Signal generation and portfolio optimisation → [[LearnAI]]
- Order routing and execution → [[XeQT]]
- Strategy code path: `strategies/chit/XeQT/ibkr/`

## Sources

| File | Date | Key takeaway |
|---|---|---|
| [[TraderChit-by-Tanulytics-v2.pdf]] | 2026-06-28 | LearnAI + XeQT architecture; UCL trading components framework |
