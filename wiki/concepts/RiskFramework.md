---
type: concept
name: Risk Framework
owner: AfricaX Trading LLC
updated: 2026-06-28
---

# Risk Framework

## Overview
All Tanulytics strategies follow AfricaX Trading risk protocols enforced at the portfolio level.

## Rules
- **Daily loss limit**: Hard stop on net daily P&L — if breached, no new positions
- **Position size constraints**: Max % of portfolio per position, per broker, per asset class
- **Automatic circuit breakers**: Pipeline flags if any broker reports unusual drawdown
- **Audit logging**: Every pipeline run logged to `logs/pipeline_YYYYMMDD.log`

## Monitoring
- Daily P&L tracked via `total_daily_pnl` in pipeline summary
- Broker-level breakdown in Airtable `Balances` table and Notion Portfolio page

## Related
- [[PipelineArchitecture]], [[PortfolioOverview]]
