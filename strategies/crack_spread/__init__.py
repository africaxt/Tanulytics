"""
crack_spread — 3:2:1 crack spread research and backtesting toolkit.

Tanulytics / AfricaX Trading. Read-only: nothing here places orders.

Quick start
-----------
    from crack_spread import load_legs, build_spread, run_all, compare

    legs   = load_legs(start="2010-01-01")          # CL=F, RB=F, HO=F via yfinance
    spread = build_spread(legs)                     # $/bbl, with roll days flagged
    results = run_all(spread)                       # four strategies
    print(compare(results))

Contract arithmetic
-------------------
    CL  WTI crude       1,000 bbl        quoted $/bbl
    RB  RBOB gasoline  42,000 gal        quoted $/gal   (= 1,000 bbl)
    HO  NY Harbor ULSD 42,000 gal        quoted $/gal   (= 1,000 bbl)

    spread_$/bbl = (2 * 42 * RB  +  1 * 42 * HO  -  3 * CL) / 3

    One 3:2:1 unit = short 3 CL / long 2 RB / long 1 HO.
    A $1.00/bbl move in the spread is $3,000 on that unit.
"""

from .data import load_legs, load_legs_csv, synthetic_legs
from .spread import build_spread, CrackSpread, BBL_PER_GAL_CONTRACT, DOLLARS_PER_BBL_PER_UNIT
from .strategies import (
    zscore_reversion,
    seasonality,
    ma_crossover,
    breakout,
    regime_filtered,
    STRATEGIES,
)
from .backtest import backtest, BacktestResult, CostModel
from .diagnostics import adf, half_life, hurst, rolling_half_life, report
from .metrics import performance, trade_stats, monthly_returns
from .optimise import grid_search, walk_forward
from .run import run_all, compare

__version__ = "1.0.0"

__all__ = [
    "load_legs",
    "load_legs_csv",
    "synthetic_legs",
    "build_spread",
    "CrackSpread",
    "BBL_PER_GAL_CONTRACT",
    "DOLLARS_PER_BBL_PER_UNIT",
    "zscore_reversion",
    "seasonality",
    "ma_crossover",
    "breakout",
    "regime_filtered",
    "STRATEGIES",
    "backtest",
    "BacktestResult",
    "CostModel",
    "performance",
    "trade_stats",
    "monthly_returns",
    "adf",
    "half_life",
    "hurst",
    "rolling_half_life",
    "report",
    "grid_search",
    "walk_forward",
    "run_all",
    "compare",
]
