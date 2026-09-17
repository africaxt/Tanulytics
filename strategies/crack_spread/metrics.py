"""
Performance measurement.

Return-based statistics (Sharpe, Sortino, CAGR, drawdown) sit on the daily
dollar P&L divided by allocated capital. Trade-based statistics (hit rate,
profit factor, expectancy) sit on the round-trip ledger. They answer different
questions and can disagree — a strategy can win 70% of trades and still lose
money, and the pair of tables is how you see that.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import numpy as np
import pandas as pd

if TYPE_CHECKING:  # pragma: no cover
    from .backtest import BacktestResult

TRADING_DAYS = 252


def sharpe(returns: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> float:
    """Annualised Sharpe ratio. ``rf`` is an annual rate."""
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    excess = r - rf / periods
    sd = excess.std(ddof=1)
    if sd == 0 or np.isnan(sd):
        return float("nan")
    return float(excess.mean() / sd * np.sqrt(periods))


def sortino(returns: pd.Series, rf: float = 0.0, periods: int = TRADING_DAYS) -> float:
    """Annualised Sortino ratio — Sharpe with only downside deviation."""
    r = returns.dropna()
    if len(r) < 2:
        return float("nan")
    excess = r - rf / periods
    downside = excess[excess < 0]
    if len(downside) < 2:
        return float("nan")
    dd = np.sqrt((downside**2).mean())
    if dd == 0:
        return float("nan")
    return float(excess.mean() / dd * np.sqrt(periods))


def max_drawdown(equity: pd.Series) -> tuple[float, Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    """Deepest peak-to-trough fall in equity, as a fraction, with its dates."""
    eq = equity.dropna()
    if eq.empty:
        return float("nan"), None, None

    # Once equity reaches zero the account is gone; a broker issues a margin
    # call long before that. Reporting "-1766%" would be arithmetic, not a
    # fact about the world, so ruin is capped at -100% and flagged separately.
    if (eq <= 0).any():
        trough = eq.idxmin()
        peak_date = eq.loc[:trough].idxmax()
        return -1.0, peak_date, eq.loc[eq <= 0].index[0]

    peak = eq.cummax()
    dd = eq / peak - 1.0
    trough = dd.idxmin()
    peak_date = eq.loc[:trough].idxmax() if trough is not None else None
    return float(dd.min()), peak_date, trough


def cagr(equity: pd.Series, periods: int = TRADING_DAYS) -> float:
    """Compound annual growth rate of the equity curve."""
    eq = equity.dropna()
    if len(eq) < 2 or eq.iloc[0] <= 0:
        return float("nan")
    years = len(eq) / periods
    if years <= 0:
        return float("nan")
    ratio = eq.iloc[-1] / eq.iloc[0]
    if ratio <= 0:
        return float("nan")  # account wiped out; CAGR is meaningless
    return float(ratio ** (1 / years) - 1)


def performance(result: "BacktestResult", rf: float = 0.0) -> pd.Series:
    """One-line summary of a backtest."""
    r = result.returns
    eq = result.equity
    mdd, mdd_peak, mdd_trough = max_drawdown(eq)
    ann_ret = cagr(eq)
    exposure = float((result.position != 0).mean())
    ts = trade_stats(result)

    return pd.Series(
        {
            "strategy": result.name,
            "start": r.index[0].date() if len(r) else None,
            "end": r.index[-1].date() if len(r) else None,
            "total_pnl_usd": result.total_pnl_usd,
            "total_pnl_bbl": float(result.pnl_bbl.sum()),
            "cagr": ann_ret,
            "ann_vol": float(r.std(ddof=1) * np.sqrt(TRADING_DAYS)) if len(r) > 1 else np.nan,
            "sharpe": sharpe(r, rf),
            "sortino": sortino(r, rf),
            "max_drawdown": mdd,
            "ruined": bool((eq <= 0).any()),
            "calmar": (ann_ret / abs(mdd)) if (mdd and not np.isnan(mdd) and mdd != 0) else np.nan,
            "mdd_peak": mdd_peak.date() if mdd_peak is not None else None,
            "mdd_trough": mdd_trough.date() if mdd_trough is not None else None,
            "exposure": exposure,
            "n_trades": ts["n_trades"],
            "hit_rate": ts["hit_rate"],
            "profit_factor": ts["profit_factor"],
            "avg_trade_usd": ts["avg_trade_usd"],
            "avg_bars_held": ts["avg_bars_held"],
            "cost_drag_usd": float(result.cost_bbl.sum() * result.spread.dollars_per_unit),
            "cost_share_of_gross": (
                float(
                    result.cost_bbl.sum()
                    / abs(result.gross_bbl.sum())
                )
                if result.gross_bbl.sum() != 0
                else np.nan
            ),
        },
        name=result.name,
    )


def trade_stats(result: "BacktestResult") -> dict:
    """Round-trip statistics from the trade ledger."""
    t = result.trades
    if t is None or t.empty:
        return {
            "n_trades": 0,
            "hit_rate": np.nan,
            "profit_factor": np.nan,
            "avg_trade_usd": np.nan,
            "avg_bars_held": np.nan,
            "best_usd": np.nan,
            "worst_usd": np.nan,
        }
    pnl = t["pnl_usd"]
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    gross_loss = abs(losses.sum())
    return {
        "n_trades": int(len(t)),
        "hit_rate": float((pnl > 0).mean()),
        "profit_factor": float(wins.sum() / gross_loss) if gross_loss > 0 else np.inf,
        "avg_trade_usd": float(pnl.mean()),
        "avg_bars_held": float(t["bars"].mean()),
        "best_usd": float(pnl.max()),
        "worst_usd": float(pnl.min()),
    }


def monthly_returns(result: "BacktestResult") -> pd.DataFrame:
    """Year × month table of returns, for eyeballing seasonality and clusters."""
    r = result.returns.dropna()
    if r.empty:
        return pd.DataFrame()
    m = (1 + r).groupby([r.index.year, r.index.month]).prod() - 1
    m.index.names = ["year", "month"]
    return m.unstack("month")


def deflated_sharpe_hint(observed_sharpe: float, n_trials: int, n_obs: int) -> float:
    """Roughly, the Sharpe you would expect from luck alone after N trials.

    Searching a parameter grid of ``n_trials`` combinations produces a best
    Sharpe well above zero even on pure noise. This returns that expected
    maximum, so you can check your winner clears it. It is a rule of thumb
    (the Bailey–López de Prado expected-maximum-Sharpe approximation), not a
    formal test — but a strategy that fails it is not worth a formal test.
    """
    if n_trials < 2 or n_obs < 2:
        return 0.0
    gamma = 0.5772156649
    e = np.e
    z = (1 - gamma) * _norm_ppf(1 - 1 / n_trials) + gamma * _norm_ppf(1 - 1 / (n_trials * e))
    return float(z * np.sqrt(1 / n_obs) * np.sqrt(TRADING_DAYS))


def _norm_ppf(p: float) -> float:
    """Inverse normal CDF (Acklam's rational approximation) — avoids SciPy."""
    if not 0 < p < 1:
        return float("nan")
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = np.sqrt(-2 * np.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = np.sqrt(-2 * np.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
