"""
Price loading for the 3:2:1 crack spread legs.

Primary source is yfinance continuous front-month futures:

    CL=F   WTI crude          $/bbl
    RB=F   RBOB gasoline      $/gal
    HO=F   NY Harbor ULSD     $/gal

Yahoo's `=F` series are *unadjusted* front-month continuations: on every roll
the series jumps to the next contract's price. Those jumps are not tradable
P&L. `spread.build_spread` detects and neutralises them; see `detect_rolls`.

Results are cached to disk so repeated notebook runs don't re-hit Yahoo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd

LEG_TICKERS = {"CL": "CL=F", "RB": "RB=F", "HO": "HO=F"}

# Repo-relative cache: <repo>/data/raw/crack_spread/
_DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data" / "raw" / "crack_spread"


def _cache_dir(cache: Optional[str | Path]) -> Path:
    d = Path(cache) if cache is not None else _DEFAULT_CACHE
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_legs(
    start: str = "2005-01-01",
    end: Optional[str] = None,
    cache: Optional[str | Path] = None,
    refresh: bool = False,
    tickers: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Download (or read from cache) daily closes for the three legs.

    Returns a DataFrame indexed by date with columns ``CL``, ``RB``, ``HO``.
    Only dates where all three legs traded are kept — a crack spread with a
    missing leg is not a crack spread.
    """
    tickers = tickers or LEG_TICKERS
    cdir = _cache_dir(cache)
    key = f"legs_{start}_{end or 'today'}.csv"
    path = cdir / key

    if path.exists() and not refresh:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return df[list(tickers)].dropna()

    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "yfinance is required for load_legs(). Install it with "
            "`pip install yfinance`, or use load_legs_csv() with your own file."
        ) from exc

    raw = yf.download(
        list(tickers.values()),
        start=start,
        end=end,
        progress=False,
        auto_adjust=False,
        group_by="column",
    )
    if raw is None or len(raw) == 0:
        raise RuntimeError("yfinance returned no data — check network and tickers.")

    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    close = close.rename(columns={v: k for k, v in tickers.items()})
    close = close[list(tickers)].dropna()
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close.index.name = "date"

    close.to_csv(path)
    return close


def load_legs_csv(path: str | Path, column_map: dict[str, str] | None = None) -> pd.DataFrame:
    """Load legs from your own CSV (IBKR export, EIA download, broker statement).

    The file needs a date index or a date column plus three price columns.
    ``column_map`` maps your column names onto ``CL`` / ``RB`` / ``HO``, e.g.
    ``{"WTI": "CL", "RBOB": "RB", "ULSD": "HO"}``.

    Units matter: ``CL`` must be $/bbl, ``RB`` and ``HO`` $/gal. If your
    gasoline and distillate columns are already $/bbl, divide by 42 first.
    """
    df = pd.read_csv(path)
    date_col = next(
        (c for c in df.columns if c.lower() in {"date", "datetime", "time", "period"}),
        None,
    )
    if date_col is not None:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
    else:
        df.index = pd.to_datetime(df.iloc[:, 0])
        df = df.iloc[:, 1:]

    if column_map:
        df = df.rename(columns=column_map)
    missing = [c for c in ("CL", "RB", "HO") if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing leg column(s): {missing}. Pass column_map=.")

    df.index.name = "date"
    return df[["CL", "RB", "HO"]].astype(float).dropna().sort_index()


def synthetic_legs(
    n: int = 3000,
    seed: int = 7,
    kind: str = "reverting",
    theta: float = 0.03,
    sigma_spread: float = 0.55,
    mu_spread: float = 18.0,
    drift: float = 0.004,
    start: str = "2012-01-02",
) -> pd.DataFrame:
    """Generate synthetic legs whose crack spread has known dynamics.

    Used by the test suite to prove the engine recovers a signal that is
    genuinely there, and rejects one that is not.

    kind
        ``"reverting"``  — spread follows an Ornstein-Uhlenbeck process
                           around ``mu_spread`` (mean reversion should win).
        ``"trending"``   — spread is a random walk with drift
                           (mean reversion should lose, trend should win).
        ``"random"``     — driftless random walk (nothing should work).

    The crude leg is an independent random walk; gasoline and distillate are
    then solved so the resulting 3:2:1 spread equals the simulated path
    exactly. Distillate carries a fixed differential to crude.
    """
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start=start, periods=n)

    # Crude: geometric random walk, ~30% annualised vol.
    cl = 70.0 * np.exp(np.cumsum(rng.normal(0, 0.019, n)) - 0.5 * 0.019**2 * np.arange(n))

    # Spread path.
    s = np.empty(n)
    s[0] = mu_spread
    shocks = rng.normal(0, sigma_spread, n)
    if kind == "reverting":
        for t in range(1, n):
            s[t] = s[t - 1] + theta * (mu_spread - s[t - 1]) + shocks[t]
    elif kind == "trending":
        s = mu_spread + np.cumsum(shocks + drift)
    elif kind == "random":
        s = mu_spread + np.cumsum(shocks)
    else:
        raise ValueError(f"unknown kind: {kind!r}")

    # Keep the excursion inside a band so the implied product prices stay
    # positive over long samples. A driftless walk left unbounded will
    # eventually imply negative gasoline, which is not a market.
    s = np.clip(s, mu_spread - 45.0, mu_spread + 90.0)

    # HO ($/gal) set from crude plus a wandering distillate differential.
    ho_diff = 12.0 + np.cumsum(rng.normal(0, 0.25, n))  # $/bbl over crude
    ho = (cl + ho_diff) / 42.0

    # Solve RB so that (2*42*RB + 42*HO - 3*CL)/3 == s
    rb = (3.0 * s + 3.0 * cl - 42.0 * ho) / (2.0 * 42.0)

    return pd.DataFrame({"CL": cl, "RB": rb, "HO": ho}, index=idx).rename_axis("date")


def detect_rolls(
    legs: pd.DataFrame,
    z_threshold: float = 6.0,
    abs_threshold: float = 0.07,
    window: int = 60,
) -> pd.Series:
    """Flag days where a leg gapped in a way that looks like a contract roll.

    A day is flagged when any leg's log change is both larger than
    ``abs_threshold`` in absolute terms and more than ``z_threshold`` rolling
    standard deviations — the signature of a continuous series switching
    contract months rather than the market moving.

    This is a heuristic. It cannot separate a roll from a genuine shock of the
    same size (5 March 2020, say), so it will occasionally neutralise a real
    move. That is the conservative direction: it removes P&L, never adds it.
    For roll-free history, load actual contract series via IBKR instead.
    """
    prices = legs.astype(float).where(legs.astype(float) > 0)
    logret = np.log(prices).diff()
    rolling_sd = logret.rolling(window, min_periods=20).std()
    big = logret.abs() > abs_threshold
    outlier = logret.abs() > (z_threshold * rolling_sd)
    return (big & outlier).any(axis=1).rename("is_roll")
