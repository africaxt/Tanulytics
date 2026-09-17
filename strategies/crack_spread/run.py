"""
Convenience runners — the two-line path from data to a comparison table.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from .backtest import BacktestResult, CostModel, backtest
from .metrics import performance
from .spread import CrackSpread
from .strategies import (
    breakout,
    ma_crossover,
    regime_filtered,
    seasonality,
    zscore_reversion,
)

DEFAULT_CONFIG: dict[str, dict] = {
    "zscore_reversion": dict(lookback=60, entry=2.0, exit=0.5, max_hold=60, stop_z=4.0),
    "seasonality": dict(adaptive=True, min_years=5),
    "ma_crossover": dict(fast=20, slow=100),
    "breakout": dict(window=60),
    "regime_filtered": dict(
        lookback=60, entry=2.0, exit=0.5, trend_window=200,
        trend_strength=1.0, max_hold=60, stop_z=4.0,
    ),
}

_FUNCS = {
    "zscore_reversion": zscore_reversion,
    "seasonality": seasonality,
    "ma_crossover": ma_crossover,
    "breakout": breakout,
    "regime_filtered": regime_filtered,
}


def run_all(
    spread: CrackSpread,
    config: Optional[dict[str, dict]] = None,
    costs: Optional[CostModel] = None,
    capital_per_unit: float = 15_000.0,
    include_buy_and_hold: bool = True,
) -> dict[str, BacktestResult]:
    """Backtest every strategy on one spread and return the results by name.

    A permanently long spread is included as the benchmark. If a strategy
    cannot beat holding the crack outright, it is adding turnover and cost in
    exchange for nothing.
    """
    config = {**DEFAULT_CONFIG, **(config or {})}
    results: dict[str, BacktestResult] = {}

    for name, fn in _FUNCS.items():
        params = config.get(name, {})
        target = fn(spread, **params)
        results[name] = backtest(
            spread, target, name=name, costs=costs,
            capital_per_unit=capital_per_unit, params=params,
        )

    if include_buy_and_hold:
        bh = pd.Series(1.0, index=spread.level.index)
        results["long_only_benchmark"] = backtest(
            spread, bh, name="long_only_benchmark", costs=costs,
            capital_per_unit=capital_per_unit,
        )

    return results


def compare(results: dict[str, BacktestResult]) -> pd.DataFrame:
    """Stack the per-strategy summaries into one comparison table."""
    if not results:
        return pd.DataFrame()
    df = pd.DataFrame([performance(r) for r in results.values()])
    cols = [
        "strategy", "sharpe", "sortino", "cagr", "ann_vol", "max_drawdown",
        "ruined", "calmar", "total_pnl_usd", "n_trades", "hit_rate",
        "profit_factor", "avg_trade_usd", "exposure", "cost_drag_usd",
        "cost_share_of_gross",
    ]
    df = df[[c for c in cols if c in df.columns]]
    return df.sort_values("sharpe", ascending=False).reset_index(drop=True)
