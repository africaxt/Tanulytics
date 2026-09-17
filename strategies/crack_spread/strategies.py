"""
Signal generators.

Every function takes a :class:`~crack_spread.spread.CrackSpread` and returns a
``pd.Series`` of *target positions* in spread units, indexed like the spread:

    +1  long the crack   (long 2 RB + 1 HO, short 3 CL — betting margins widen)
    -1  short the crack  (the reverse — betting margins compress)
     0  flat

The series is stated on the information available at that date's close. The
backtester applies a one-bar execution lag, so nothing here should shift for
look-ahead — do that once, in one place, or you will double-count it.
"""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np
import pandas as pd

from .spread import CrackSpread, zscore


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _threshold_state_machine(
    z: pd.Series,
    entry: float,
    exit_: float,
    max_hold: Optional[int] = None,
    stop_z: Optional[float] = None,
    enabled: Optional[pd.Series] = None,
) -> pd.Series:
    """Walk a z-score series and hold positions between entry and exit bands.

    Enters short when ``z >= entry`` (spread rich), long when ``z <= -entry``.
    Exits when the z-score has reverted inside ``exit_``, when ``max_hold``
    bars have passed, or when the z-score blows through ``stop_z`` against
    the position.

    ``enabled`` optionally gates *new* entries (used by the regime filter);
    existing positions are still managed to their normal exit.
    """
    pos = np.zeros(len(z))
    zv = z.to_numpy(dtype=float)
    gate = (
        np.ones(len(z), dtype=bool)
        if enabled is None
        else enabled.reindex(z.index).fillna(False).to_numpy(dtype=bool)
    )

    state = 0.0
    held = 0
    for i in range(len(zv)):
        zi = zv[i]
        if np.isnan(zi):
            pos[i] = 0.0
            state, held = 0.0, 0
            continue

        if state != 0.0:
            held += 1
            hit_stop = stop_z is not None and (
                (state < 0 and zi >= stop_z) or (state > 0 and zi <= -stop_z)
            )
            timed_out = max_hold is not None and held >= max_hold
            reverted = abs(zi) <= exit_
            crossed = (state < 0 and zi <= 0.0) or (state > 0 and zi >= 0.0)
            if hit_stop or timed_out or reverted or crossed:
                state, held = 0.0, 0

        if state == 0.0 and gate[i]:
            if zi >= entry:
                state, held = -1.0, 0
            elif zi <= -entry:
                state, held = 1.0, 0

        pos[i] = state

    return pd.Series(pos, index=z.index, name="position")


# --------------------------------------------------------------------------
# 1. mean reversion
# --------------------------------------------------------------------------

def zscore_reversion(
    spread: CrackSpread,
    lookback: int = 60,
    entry: float = 2.0,
    exit: float = 0.5,
    max_hold: Optional[int] = 60,
    stop_z: Optional[float] = 4.0,
) -> pd.Series:
    """Fade the spread when it is statistically stretched.

    The premise: refining margins are anchored by physical economics —
    refiners cut runs when the crack collapses and max out when it spikes —
    so extreme readings should decay back toward the recent mean.

    The premise's weakness: the "mean" itself moves with capacity, regulation
    and demand regimes. A rolling window tracks that drift; a static mean
    would not. ``max_hold`` and ``stop_z`` are what stop the strategy sitting
    in a losing fade through a genuine regime change.
    """
    z = zscore(spread.level, lookback)
    return _threshold_state_machine(z, entry, exit, max_hold, stop_z).rename("zscore_reversion")


# --------------------------------------------------------------------------
# 2. seasonality
# --------------------------------------------------------------------------

_DEFAULT_LONG_MONTHS = (1, 2, 3)     # build into driving season
_DEFAULT_SHORT_MONTHS = (8, 9, 10)   # post-Labour Day demand fade


def seasonality(
    spread: CrackSpread,
    long_months: tuple[int, ...] = _DEFAULT_LONG_MONTHS,
    short_months: tuple[int, ...] = _DEFAULT_SHORT_MONTHS,
    adaptive: bool = False,
    min_years: int = 5,
) -> pd.Series:
    """Trade the refining calendar.

    Gasoline cracks are structurally strongest into the northern-hemisphere
    summer driving season and weakest in the autumn shoulder, when refiners
    switch to winter blend and distillate takes over. This is the most
    documented seasonal pattern in the energy complex — which is also the
    reason to be suspicious of it, since a widely known calendar edge tends
    to get front-run into the futures curve.

    Parameters
    ----------
    adaptive
        If True, ignore ``long_months`` / ``short_months`` and learn the sign
        of each calendar month from an *expanding* window of prior data only
        (needs ``min_years`` of history before it trades). This is the honest
        version: it cannot peek at the seasonality it is about to trade.
    """
    idx = spread.level.index
    if not adaptive:
        month = idx.month
        pos = np.where(
            np.isin(month, long_months), 1.0,
            np.where(np.isin(month, short_months), -1.0, 0.0),
        )
        return pd.Series(pos, index=idx, name="seasonality")

    chg = spread.change
    months = pd.Series(idx.month, index=idx)
    years = pd.Series(idx.year, index=idx)

    # Monthly mean change, learned from strictly prior calendar years.
    by_year_month = chg.groupby([years, months]).mean()
    pos = pd.Series(0.0, index=idx, name="seasonality")
    first_year = int(years.iloc[0])
    for i, ts in enumerate(idx):
        y, m = ts.year, ts.month
        if y - first_year < min_years:
            continue
        prior = by_year_month.loc[
            (by_year_month.index.get_level_values(0) < y)
            & (by_year_month.index.get_level_values(1) == m)
        ]
        if len(prior) < min_years:
            continue
        pos.iloc[i] = float(np.sign(prior.mean()))
    return pos


# --------------------------------------------------------------------------
# 3. trend
# --------------------------------------------------------------------------

def ma_crossover(spread: CrackSpread, fast: int = 20, slow: int = 100) -> pd.Series:
    """Follow the spread's own trend.

    Included largely as a control. If trend-following beats mean reversion on
    the same series, the reversion premise is wrong for that sample and no
    amount of threshold tuning will fix it.
    """
    if fast >= slow:
        raise ValueError("fast must be shorter than slow")
    f = spread.level.rolling(fast, min_periods=fast).mean()
    s = spread.level.rolling(slow, min_periods=slow).mean()
    pos = np.sign(f - s)
    return pd.Series(pos, index=spread.level.index).fillna(0.0).rename("ma_crossover")


def breakout(spread: CrackSpread, window: int = 60, exit_window: Optional[int] = None) -> pd.Series:
    """Donchian channel breakout on the spread — the other trend control."""
    exit_window = exit_window or max(5, window // 2)
    lvl = spread.level
    hi = lvl.rolling(window, min_periods=window).max()
    lo = lvl.rolling(window, min_periods=window).min()
    exit_hi = lvl.rolling(exit_window, min_periods=exit_window).max()
    exit_lo = lvl.rolling(exit_window, min_periods=exit_window).min()

    pos = np.zeros(len(lvl))
    state = 0.0
    v, h, l, eh, el = (
        lvl.to_numpy(), hi.to_numpy(), lo.to_numpy(),
        exit_hi.to_numpy(), exit_lo.to_numpy(),
    )
    for i in range(len(v)):
        if np.isnan(h[i]) or np.isnan(l[i]):
            pos[i] = 0.0
            continue
        if state == 0.0:
            if v[i] >= h[i]:
                state = 1.0
            elif v[i] <= l[i]:
                state = -1.0
        elif state > 0 and v[i] <= el[i]:
            state = 0.0
        elif state < 0 and v[i] >= eh[i]:
            state = 0.0
        pos[i] = state
    return pd.Series(pos, index=lvl.index, name="breakout")


# --------------------------------------------------------------------------
# 4. regime-filtered combination
# --------------------------------------------------------------------------

def regime_filtered(
    spread: CrackSpread,
    lookback: int = 60,
    entry: float = 2.0,
    exit: float = 0.5,
    trend_window: int = 200,
    trend_strength: float = 1.0,
    max_hold: Optional[int] = 60,
    stop_z: Optional[float] = 4.0,
    follow_trend: bool = False,
) -> pd.Series:
    """Mean reversion that stands down when the spread is genuinely trending.

    The filter measures the slope of a long moving average, scaled by the
    spread's own volatility, so ``trend_strength`` is in comparable units
    across samples. When |scaled slope| exceeds the threshold the market is
    repricing the margin rather than oscillating around it, and fading it is
    how a mean-reversion book dies.

    Parameters
    ----------
    trend_strength
        Slope threshold in daily standard deviations per ``trend_window``.
        Higher = the filter intervenes less often.
    follow_trend
        If True, take the trend direction while reversion is stood down,
        instead of sitting flat. Turns the strategy into a regime switcher.
    """
    lvl = spread.level
    z = zscore(lvl, lookback)

    ma = lvl.rolling(trend_window, min_periods=trend_window).mean()
    slope = ma.diff(trend_window) / trend_window          # $/bbl per day
    vol = lvl.diff().rolling(trend_window, min_periods=trend_window).std()
    scaled = (slope / vol.replace(0.0, np.nan)) * np.sqrt(trend_window)

    trending = scaled.abs() > trend_strength
    calm = (~trending).fillna(False)

    pos = _threshold_state_machine(z, entry, exit, max_hold, stop_z, enabled=calm)

    if follow_trend:
        trend_dir = np.sign(scaled).fillna(0.0)
        pos = pos.where(~(trending.fillna(False) & (pos == 0.0)), trend_dir)

    return pos.rename("regime_filtered")


STRATEGIES: dict[str, Callable[..., pd.Series]] = {
    "zscore_reversion": zscore_reversion,
    "seasonality": seasonality,
    "ma_crossover": ma_crossover,
    "breakout": breakout,
    "regime_filtered": regime_filtered,
}
