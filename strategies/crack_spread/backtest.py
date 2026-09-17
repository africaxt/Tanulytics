"""
The backtest engine.

Deliberately simple and fully vectorised, with one stateful pass to build the
trade ledger. Three rules it never breaks:

1. **One-bar execution lag.** A position derived from date *t*'s close is
   applied to date *t+1*'s P&L. This is the single place a shift happens.
2. **Costs on turnover, not on time.** You pay when the position changes size
   or sign, plus a roll charge on flagged roll days while positioned.
3. **P&L in $/bbl first, dollars second.** The spread is quoted per barrel of
   crude, so that is the natural unit; dollars are a scaling at the end.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from .spread import CrackSpread


@dataclass
class CostModel:
    """Transaction costs, expressed per spread unit.

    Defaults are deliberately pessimistic retail-futures assumptions. Tighten
    them once you have measured your own fills — but tune the *strategy* on
    honest costs, not the other way round.

    slippage_per_bbl
        One-way slippage in $/bbl of spread. $0.05/bbl is $150 on a 3:2:1
        unit — roughly a tick of adverse fill on each of the six contracts.
    commission_per_unit
        One-way commission in dollars for all six contracts.
    roll_cost_per_bbl
        Charged on each detected roll day while positioned. Rolling a 3:2:1
        means six more fills; this is what continuous-series backtests
        usually forget entirely.
    """

    slippage_per_bbl: float = 0.05
    commission_per_unit: float = 15.0
    roll_cost_per_bbl: float = 0.03

    def per_unit_traded_bbl(self, dollars_per_unit: float) -> float:
        """Total one-way cost of a position change, in $/bbl of spread."""
        return self.slippage_per_bbl + self.commission_per_unit / dollars_per_unit


@dataclass
class BacktestResult:
    """Everything a backtest produced. Nothing here is rounded or prettified."""

    name: str
    position: pd.Series          # position actually held (already lagged)
    target: pd.Series            # signal as generated, before the lag
    gross_bbl: pd.Series         # daily P&L in $/bbl of spread, before costs
    cost_bbl: pd.Series          # daily costs in $/bbl
    pnl_bbl: pd.Series           # daily net P&L in $/bbl
    pnl_usd: pd.Series           # daily net P&L in dollars
    equity: pd.Series            # capital + cumulative dollar P&L
    returns: pd.Series           # daily return on capital
    trades: pd.DataFrame         # one row per round trip
    capital: float
    units: float
    spread: CrackSpread = field(repr=False)
    params: dict = field(default_factory=dict)

    @property
    def total_pnl_usd(self) -> float:
        return float(self.pnl_usd.sum())

    def summary(self) -> pd.Series:
        from .metrics import performance
        return performance(self)


def _split_turnover(position: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Split each bar's turnover into the part that closes and the part that opens.

    A flip from +1 to -1 is one unit closed and one unit opened, not two units
    of the same thing. Keeping them apart is what lets the trade ledger charge
    each trade its own entry and exit cost, and it is why trade P&L reconciles
    exactly with daily P&L.
    """
    prev = position.shift(1).fillna(0.0)
    a, b = prev.to_numpy(dtype=float), position.to_numpy(dtype=float)

    flipped = (a * b) < 0
    closing = np.where(flipped, np.abs(a), np.maximum(np.abs(a) - np.abs(b), 0.0))
    opening = np.where(flipped, np.abs(b), np.maximum(np.abs(b) - np.abs(a), 0.0))

    return (
        pd.Series(closing, index=position.index, name="closing"),
        pd.Series(opening, index=position.index, name="opening"),
    )


def _build_trades(
    position: pd.Series,
    pnl_usd: pd.Series,
    close_cost_usd: pd.Series,
    spread_level: pd.Series,
) -> pd.DataFrame:
    """Collapse a position path into round trips.

    A trade runs from the first bar of a non-zero position to the last bar
    before it returns to zero or flips sign. Its P&L is the daily net P&L over
    those bars, plus the exit cost charged on the bar it closed, minus the
    exit cost of the *previous* trade that lands on its own opening bar.
    Every dollar of cost is therefore attributed to exactly one trade, and the
    ledger sums to the total — the test suite asserts this.
    """
    pos = position.to_numpy(dtype=float)
    pnl = pnl_usd.to_numpy(dtype=float)
    close_cost = close_cost_usd.reindex(position.index).fillna(0.0).to_numpy(dtype=float)
    lvl = spread_level.reindex(position.index).to_numpy(dtype=float)
    idx = position.index

    def _row(start: int, end_exclusive: int, open_at_end: bool) -> dict:
        # Costs: add back the previous trade's exit charged on our entry bar,
        # and take on our own exit charged on the bar after we finish.
        adj = close_cost[start]
        exit_cost = close_cost[end_exclusive] if end_exclusive < len(pos) else 0.0
        return {
            "entry_date": idx[start],
            "exit_date": idx[min(end_exclusive, len(pos)) - 1],
            "direction": "long" if pos[start] > 0 else "short",
            "size": abs(pos[start]),
            "entry_spread": lvl[start - 1] if start > 0 else lvl[start],
            "exit_spread": lvl[min(end_exclusive, len(pos)) - 1],
            "bars": min(end_exclusive, len(pos)) - start,
            "pnl_usd": float(np.nansum(pnl[start:end_exclusive]) + adj - exit_cost),
            "open_at_end": open_at_end,
        }

    rows: list[dict] = []
    start = None
    for i in range(len(pos)):
        changed = i == 0 or pos[i] != pos[i - 1]
        if changed and start is not None:
            rows.append(_row(start, i, False))
            start = None
        if changed and pos[i] != 0.0:
            start = i

    if start is not None:
        rows.append(_row(start, len(pos), True))

    df = pd.DataFrame(rows)
    if not df.empty:
        df["open_at_end"] = df["open_at_end"].astype(bool)
    return df


def backtest(
    spread: CrackSpread,
    target: pd.Series,
    name: str = "strategy",
    costs: Optional[CostModel] = None,
    capital_per_unit: float = 15_000.0,
    units: float = 1.0,
    lag: int = 1,
    params: Optional[dict] = None,
) -> BacktestResult:
    """Run a target-position series against the spread.

    Parameters
    ----------
    target
        Position signal in spread units, as generated (not shifted).
    capital_per_unit
        Dollars of capital allocated per spread unit. NYMEX initial margin on
        a 3:2:1 has historically sat in the $8k–12k range and moves with
        volatility, so $15,000 leaves headroom. Returns and Sharpe scale with
        this number — halve it and the Sharpe is unchanged but the CAGR
        doubles, which is exactly why Sharpe is the honest comparator.
    units
        Number of spread units held per unit of signal. Constant sizing keeps
        the strategy comparison clean; vary it only after you have picked a
        strategy.
    lag
        Bars between signal and execution. 1 is close-to-next-close. Set 2 if
        you generate signals after the close and place orders the following
        session.
    """
    costs = costs or CostModel()
    dollars_per_unit = spread.dollars_per_unit

    target = target.reindex(spread.level.index).fillna(0.0).astype(float)
    position = (target.shift(lag).fillna(0.0) * units).rename("position")

    gross_bbl = (position * spread.change).rename("gross_bbl")

    closing, opening = _split_turnover(position)
    unit_cost = costs.per_unit_traded_bbl(dollars_per_unit)
    trade_cost = (closing + opening) * unit_cost
    roll_cost = (
        spread.is_roll.reindex(position.index).fillna(False).astype(float)
        * position.abs()
        * costs.roll_cost_per_bbl
    )
    cost_bbl = (trade_cost + roll_cost).rename("cost_bbl")

    pnl_bbl = (gross_bbl - cost_bbl).rename("pnl_bbl")
    pnl_usd = (pnl_bbl * dollars_per_unit).rename("pnl_usd")

    capital = capital_per_unit * max(units, 1e-12)
    equity = (capital + pnl_usd.cumsum()).rename("equity")
    returns = (pnl_usd / capital).rename("returns")

    close_cost_usd = closing * unit_cost * dollars_per_unit
    trades = _build_trades(position, pnl_usd, close_cost_usd, spread.level)

    return BacktestResult(
        name=name,
        position=position,
        target=target,
        gross_bbl=gross_bbl,
        cost_bbl=cost_bbl,
        pnl_bbl=pnl_bbl,
        pnl_usd=pnl_usd,
        equity=equity,
        returns=returns,
        trades=trades,
        capital=capital,
        units=units,
        spread=spread,
        params=params or {},
    )
