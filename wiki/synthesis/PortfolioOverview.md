---
type: synthesis
name: Portfolio Overview
updated: 2026-06-28
---

# Portfolio Overview

> Maintained by Claude. Updated after each pipeline run or on request.
> For live numbers, check `journal/YYYY-MM-DD.md` or Airtable.

## Current portfolio structure

| Broker | Strategy | Asset Classes | Status |
|---|---|---|---|
| IBKR | Algorithmic / Global Macro | Equity, Futures, Options | Active |
| FXCM | Forex | Forex, CFD | Active (webhook) |
| Schwab | Global Macro | Equity, ETF | Active |
| Robinhood | Value Investing | US Equity, Options | Active |

## Institutional

| Entity | Fund | Jurisdiction |
|---|---|---|
| Dbuntu AI Bond-ETF | UG Portfolio | Dbuntu Data Uganda Ltd |
| Dbuntu AI Bond-ETF | RW Portfolio | Dbuntu Labs Ltd |
| DIFC ADGM - PIC | R&D | MBZ Global Management FZCO |

## Cross-broker themes
_Update this section when a macro theme spans multiple brokers._

## Risks to monitor
- FXCM balance/equity not available from webhook — reconcile weekly
- Robinhood unofficial API — check after Robinhood app updates
- Schwab refresh token expires if pipeline idle >7 days

## Related
- [[RiskFramework]], [[PipelineArchitecture]]
