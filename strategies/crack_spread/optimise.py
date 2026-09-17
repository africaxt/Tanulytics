"""
Parameter search — and the guardrails that make it mean something.

A grid search over a 4,000-day sample will always find a parameter set with a
flattering Sharpe. Two things here exist to stop you believing it:

* :func:`walk_forward` never evaluates a parameter set on the data that chose
  it. The reported curve is stitched out-of-sample segments only.
* :func:`grid_search` reports the expected best-Sharpe-from-luck for the grid
  size you ran, so you can see how much of your winner is selection.
"""

from __future__ import annotations

import itertools
from typing import Callable, Iterable, Optional

import numpy as np
import pandas as pd

from .backtest import BacktestResult, CostModel, backtest
from .metrics import deflated_sharpe_hint, performance
from .spread import CrackSpread


def _param_grid(grid: dict[str, Iterable]) -> list[dict]:
    keys = list(grid)
    return [dict(zip(keys, combo)) for combo in itertools.product(*(grid[k] for k in keys))]


def grid_search(
    spread: CrackSpread,
    strategy: Callable[..., pd.Series],
    grid: dict[str, Iterable],
    costs: Optional[CostModel] = None,
    metric: str = "sharpe",
    capital_per_unit: float = 15_000.0,
    quiet: bool = True,
) -> pd.DataFrame:
    """Evaluate every parameter combination in ``grid`` on the full sample.

    Returns a DataFrame of parameters and performance, sorted by ``metric``,
    with a ``luck_threshold`` column: the Sharpe you would expect the best of
    this many random trials to reach on noise. Rows whose Sharpe sits below
    it are not evidence of anything.

    In-sample only. Use :func:`walk_forward` before believing a number.
    """
    combos = _param_grid(grid)
    rows = []
    for params in combos:
        try:
            target = strategy(spread, **params)
            res = backtest(
                spread, target, name=getattr(strategy, "__name__", "strategy"),
                costs=costs, capital_per_unit=capital_per_unit, params=params,
            )
            perf = performance(res)
        except Exception as exc:  # a bad combination should not kill the sweep
            if not quiet:
                print(f"  skipped {params}: {exc}")
            continue
        rows.append({**params, **{k: perf[k] for k in
                                  ("sharpe", "sortino", "cagr", "max_drawdown",
                                   "total_pnl_usd", "n_trades", "hit_rate",
                                   "profit_factor", "exposure")}})

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["luck_threshold"] = deflated_sharpe_hint(
        observed_sharpe=float(df["sharpe"].max()),
        n_trials=len(df),
        n_obs=len(spread.level),
    )
    df["beats_luck"] = df["sharpe"] > df["luck_threshold"]
    return df.sort_values(metric, ascending=False).reset_index(drop=True)


def walk_forward(
    spread: CrackSpread,
    strategy: Callable[..., pd.Series],
    grid: dict[str, Iterable],
    train_years: float = 4.0,
    test_years: float = 1.0,
    costs: Optional[CostModel] = None,
    metric: str = "sharpe",
    capital_per_unit: float = 15_000.0,
    min_train_obs: int = 500,
) -> tuple[BacktestResult, pd.DataFrame]:
    """Anchored-window walk-forward: fit on the past, trade the next slice.

    For each window, the grid is searched on the training slice, the best
    parameter set by ``metric`` is frozen, and that set alone is run on the
    following test slice. The stitched test positions become a single
    out-of-sample result.

    Returns
    -------
    (result, log)
        ``result`` is the out-of-sample backtest. ``log`` has one row per
        window: its dates, the chosen parameters, and in- vs out-of-sample
        Sharpe. A large, systematic gap between those two columns is the
        overfitting you were looking for.

    Note
    ----
    Signals are regenerated on the *full* spread for the chosen parameters and
    then masked to the test window, so rolling windows keep their warm-up
    history. That is realistic — on the day you trade, you do have the prior
    data — but it means a strategy is never penalised for a cold start it
    would not actually face.
    """
    idx = spread.level.index
    train_bars = int(train_years * 252)
    test_bars = int(test_years * 252)
    if len(idx) < train_bars + test_bars:
        raise ValueError(
            f"need at least {train_bars + test_bars} bars for "
            f"{train_years}y train + {test_years}y test; got {len(idx)}"
        )

    stitched = pd.Series(0.0, index=idx)
    log_rows = []
    start = train_bars

    while start + test_bars <= len(idx):
        train = spread.slice(idx[0], idx[start - 1])
        test_start, test_end = idx[start], idx[min(start + test_bars - 1, len(idx) - 1)]

        if len(train.level) < min_train_obs:
            start += test_bars
            continue

        scores = grid_search(
            train, strategy, grid, costs=costs, metric=metric,
            capital_per_unit=capital_per_unit,
        )
        if scores.empty:
            start += test_bars
            continue

        param_names = list(grid)
        best = scores.iloc[0]
        best_params = {k: best[k] for k in param_names}
        best_params = {
            k: (int(v) if isinstance(v, (int, np.integer)) or float(v).is_integer() else float(v))
            if isinstance(v, (int, float, np.integer, np.floating)) else v
            for k, v in best_params.items()
        }

        full_signal = strategy(spread, **best_params)
        window = (idx >= test_start) & (idx <= test_end)
        stitched.loc[window] = full_signal.loc[window].fillna(0.0).to_numpy()

        oos = backtest(
            spread.slice(test_start, test_end),
            full_signal.loc[test_start:test_end],
            costs=costs, capital_per_unit=capital_per_unit,
        )
        log_rows.append(
            {
                "train_start": idx[0].date(),
                "train_end": idx[start - 1].date(),
                "test_start": test_start.date(),
                "test_end": test_end.date(),
                **best_params,
                "is_sharpe": float(best["sharpe"]),
                "oos_sharpe": float(performance(oos)["sharpe"]),
                "oos_pnl_usd": oos.total_pnl_usd,
            }
        )
        start += test_bars

    log = pd.DataFrame(log_rows)
    first_test = pd.Timestamp(log["test_start"].iloc[0]) if not log.empty else idx[0]
    oos_spread = spread.slice(first_test, idx[-1])
    result = backtest(
        oos_spread,
        stitched.loc[first_test:],
        name=f"{getattr(strategy, '__name__', 'strategy')}_walkforward",
        costs=costs,
        capital_per_unit=capital_per_unit,
    )
    return result, log
