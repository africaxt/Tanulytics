"""
Diagnostics — is the mean-reversion premise even true on this sample?

Run these before you tune a single threshold. If the spread is not
mean-reverting over your holding horizon, a z-score strategy that backtests
well is fitting noise, and the parameter search will happily help it.

Implemented with numpy only (no statsmodels dependency), so this runs
anywhere the rest of the package runs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .spread import CrackSpread

# Dickey-Fuller τ critical values, constant-only model, large sample.
_ADF_CRIT = {"1%": -3.43, "5%": -2.86, "10%": -2.57}


def _ols(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Least squares with standard errors. Returns (beta, se)."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = max(len(y) - X.shape[1], 1)
    sigma2 = float(resid @ resid) / dof
    xtx_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.maximum(np.diag(xtx_inv) * sigma2, 0.0))
    return beta, se


def half_life(series: pd.Series) -> float:
    """Mean-reversion half-life in trading days, from an AR(1) fit.

    Regresses Δy on lagged y: Δy_t = α + λ·y_{t-1} + ε. A negative λ means
    reversion, and the half-life is ln(2)/−λ — the time for a deviation to
    decay by half.

    Read it against your intended holding period. A half-life of 200 days
    with a 20-day exit rule means you are exiting long before the reversion
    you are betting on has happened.
    """
    y = series.dropna().to_numpy(dtype=float)
    if len(y) < 30:
        return float("nan")
    dy, lag = np.diff(y), y[:-1]
    X = np.column_stack([np.ones(len(lag)), lag])
    beta, _ = _ols(dy, X)
    lam = beta[1]
    if lam >= 0:
        return float("inf")  # no reversion detected
    return float(np.log(2) / -lam)


def adf(series: pd.Series, max_lag: int = 10) -> dict:
    """Augmented Dickey-Fuller test for a unit root (constant, no trend).

    The null is "this is a random walk". A τ statistic below the critical
    value rejects that null in favour of stationarity — which is the
    statistical form of "this spread reverts".

    Returns the statistic, the critical values, and whether the null is
    rejected at 5%. Not a licence to trade: ADF on the full sample is itself
    in-sample, and a spread can be stationary over 15 years while trending
    ruinously for two of them.
    """
    y = series.dropna().to_numpy(dtype=float)
    if len(y) < 50:
        return {"stat": float("nan"), "n": len(y), "lags": 0,
                "critical": _ADF_CRIT, "reject_5pct": False}

    dy, lag = np.diff(y), y[:-1]
    n_lags = min(max_lag, max(int((len(y) - 1) ** (1 / 3)), 1))

    cols = [np.ones(len(dy)), lag]
    for k in range(1, n_lags + 1):
        cols.append(np.concatenate([np.zeros(k), dy[:-k]]))
    X = np.column_stack(cols)

    start = n_lags
    beta, se = _ols(dy[start:], X[start:])
    stat = float(beta[1] / se[1]) if se[1] > 0 else float("nan")

    return {
        "stat": stat,
        "n": len(y),
        "lags": n_lags,
        "critical": _ADF_CRIT,
        "reject_5pct": bool(stat < _ADF_CRIT["5%"]),
    }


def hurst(series: pd.Series, max_lag: int = 100) -> float:
    """Hurst exponent by rescaled-variance.

    < 0.5 mean-reverting · ≈ 0.5 random walk · > 0.5 trending.
    Noisy on short samples — treat 0.45 and 0.55 as the same answer.
    """
    y = series.dropna().to_numpy(dtype=float)
    if len(y) < max_lag * 2:
        max_lag = max(len(y) // 4, 5)
    lags = np.arange(2, max_lag)
    tau = [np.std(y[l:] - y[:-l]) for l in lags]
    tau = np.array(tau)
    ok = tau > 0
    if ok.sum() < 3:
        return float("nan")
    slope = np.polyfit(np.log(lags[ok]), np.log(tau[ok]), 1)[0]
    return float(slope)


def rolling_half_life(series: pd.Series, window: int = 504) -> pd.Series:
    """Half-life recomputed on a rolling window — does reversion persist?

    A half-life that is stable across the sample supports a fixed lookback.
    One that swings from 15 days to 300 is telling you the regime changed,
    and is the argument for the walk-forward test over a single fit.
    """
    out = series.rolling(window, min_periods=window).apply(
        lambda w: half_life(pd.Series(w)), raw=False
    )
    return out.rename("half_life")


def report(spread: CrackSpread) -> pd.Series:
    """One-line diagnostic summary of a spread."""
    lvl = spread.level
    a = adf(lvl)
    return pd.Series(
        {
            "n_obs": len(lvl),
            "start": lvl.index[0].date(),
            "end": lvl.index[-1].date(),
            "mean_usd_bbl": float(lvl.mean()),
            "sd_usd_bbl": float(lvl.std()),
            "min_usd_bbl": float(lvl.min()),
            "max_usd_bbl": float(lvl.max()),
            "pct_negative": float((lvl < 0).mean()),
            "half_life_days": half_life(lvl),
            "hurst": hurst(lvl),
            "adf_stat": a["stat"],
            "adf_reject_5pct": a["reject_5pct"],
            "roll_days_flagged": int(spread.is_roll.sum()),
            "daily_sd_usd_bbl": float(spread.change.std()),
        },
        name="diagnostics",
    )
