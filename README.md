# Tanulytics

**Closed-loop portfolio aggregation and reporting system**

IBKR · FXCM · Schwab · Robinhood → Airtable → Notion

**GitHub:** https://github.com/africaxt/Tanulytics  
**Org:** https://github.com/africaxt

---

## Overview

Tanulytics is the trading technology platform for AfricaX Trading LLC — consolidating algorithmic research, strategy execution, and institutional fund management under one system.

Part of the Dbuntu LABS ecosystem:
- **Risk framework**: AfricaX Trading LLC (Wyoming/USA)
- **Execution arm**: MerchantX by Bunyonyi Distributors Ltd
- **Architecture**: Dbuntu LABS Ltd (KIFC/Rwanda)
- **Parent holding**: MBZ Global Management FZCO (ADGM/UAE)

Tanulytics consolidates:
- **AlgoXchange**: Algorithmic exchange strategies
- **AfricaX Trading**: African market focused trading systems
- **Research**: Market analysis, backtesting, strategy development
- **Institutional**: Managed fund strategies and risk management

---

## Structure

```
Tanulytics/
├── archive/
│   └── Unorganised Files/    ← legacy files pending cleanup
├── config/                   ← trading configuration
├── research/                 ← strategy research & analysis
│   ├── AlgoXchange/          ← exchange algorithms
│   ├── AfricaX-Trading/      ← regional trading strategies
│   └── Coved 19 Study/       ← special research
├── scripts/                  ← execution scripts
├── strategies/               ← production trading strategies
│   ├── chit/                 ← chit trading algorithms
│   └── temp/                 ← experimental strategies
├── institutional/            ← fund management
│   ├── Dbuntu AI Bond-ETF/
│   └── DIFC ADGM - PIC/
├── .gitignore
├── CLAUDE.md                 ← agent governance
├── README.md                 ← this file
└── requirements.txt
```

---

## Quick Start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Research
cd research
jupyter notebook

# Run strategy
python scripts/run_strategy.py --config config/strategy.yaml
```

---

## Connected Systems

| System | Role |
|---|---|
| Airtable — `Alvin Trade Log` | Personal trading journal |
| Airtable — `AfricaX Trading` | Trades, OTC, Financing, Settlements |
| Airtable — `Strategy` | Portfolio RTN/AMAT + 14 securities |
| Notion | Reporting & editorial |

---

## Risk Management

All trading strategies follow AfricaX Trading risk protocols:
- Daily loss limits
- Position size constraints
- Automatic circuit breakers
- Audit logging

---

## Institutional

Managed funds and institutional strategies segregated in `/institutional` with separate compliance tracking under MBZ Global Management FZCO (ADGM/UAE).
