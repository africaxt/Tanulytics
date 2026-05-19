# Tanulytics Trading Platform

Algorithmic trading research and strategy execution combining quantitative analysis with market data.

**GitHub:** https://github.com/africaxt/tanulytics-trading

## Overview

Tanulytics is the trading technology platform consolidating:
- **AlgoXchange**: Algorithmic exchange strategies
- **AfricaX Trading**: African market focused trading systems
- **Research**: Market analysis, backtesting, strategy development
- **Institutional**: Managed fund strategies and risk management

## Structure

```
Tanulytics (Trading)/
├── research/              # Strategy research & analysis
│   ├── AlgoXchange/      # Exchange algorithms
│   ├── AfricaX-Trading/  # Regional trading strategies
│   └── Coved 19 Study/   # Special research
├── strategies/            # Production trading strategies
│   ├── chit/             # Chit trading algorithms
│   └── temp/             # Experimental strategies
├── institutional/         # Fund management
│   ├── Dbuntu AI Bond-ETF/
│   └── DIFC ADGM - PIC/
├── config/               # Trading configuration
├── scripts/              # Execution scripts
├── data/
│   ├── raw/
│   └── processed/
├── logs/                 # Trading logs
└── branding/             # Marketing materials
```

## Quick Start

### Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Research
```bash
cd research
jupyter notebook
```

### Run Strategies
```bash
python scripts/run_strategy.py --config config/strategy.yaml
```

## Connected Repos

- **africaxt/Tanulytics-Trading** - Legacy; being consolidated here
- **africaxt/AfricaX-Trading** - Regional trading (archival)

See GitHub organization: https://github.com/africaxt

## Risk Management

All trading strategies follow risk protocols:
- Daily loss limits
- Position size constraints
- Automatic circuit breakers
- Audit logging

## Institutional

Managed funds and institutional strategies segregated in `/institutional` with separate compliance tracking.
