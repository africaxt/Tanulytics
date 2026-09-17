"""
3:2:1 crack spread construction.

    spread_$/bbl = (2 * 42 * RB  +  1 * 42 * HO  -  3 * CL) / 3

The division by 3 expresses the refining margin per barrel of crude input,
which is how the trade is quoted and how EIA and refiners talk about it. It is
also what makes the number comparable across the 5:3:2 and 2:1:1 variants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from .data import detect_rolls

GAL_PER_BBL = 42.0

#: Barrel equivalent of one RB or HO contract (42,000 gal / 42).
BBL_PER_GAL_CONTRACT = 1_000.0

#: Dollar P&L per $1.00/bbl move on one 3:2:1 unit (3 CL + 2 RB + 1 HO,
#: each 1,000 bbl equivalent, spread quoted per barrel of crude).
DOLLARS_PER_BBL_PER_UNIT = 3_000.0


@dataclass
class CrackSpread:
    """A constructed crack spread and everything the backtester needs from it.

    Attributes
    ----------
    level
        Spread level in $/bbl.
    change
        Tradable day-on-day change in $/bbl. Roll-day gaps are zeroed here,
        so ``change`` does not equal ``level.diff()`` on those days.
    legs
        The underlying leg prices.
    is_roll
        Boolean flag per date, from :func:`crack_spread.data.detect_rolls`.
    ratio
        The (crude, gasoline, distillate) ratio used, default (3, 2, 1).
    """

    level: pd.Series
    change: pd.Series
    legs: pd.DataFrame
    is_roll: pd.Series
    ratio: tuple[int, int, int] = (3, 2, 1)

    @property
    def dollars_per_unit(self) -> float:
        """Dollar value of a $1/bbl move on one spread unit."""
        return BBL_PER_GAL_CONTRACT * self.ratio[0]

    def __len__(self) -> int:
        return len(self.level)

    def slice(self, start=None, end=None) -> "CrackSpread":
        """Return the same spread restricted to a date range."""
        sl = slice(start, end)
        return CrackSpread(
            level=self.level.loc[sl],
            change=self.change.loc[sl],
            legs=self.legs.loc[sl],
            is_roll=self.is_roll.loc[sl],
            ratio=self.ratio,
        )

    def to_frame(self) -> pd.DataFrame:
        out = self.legs.copy()
        out["spread"] = self.level
        out["spread_change"] = self.change
        out["is_roll"] = self.is_roll
        return out


def build_spread(
    legs: pd.DataFrame,
    ratio: tuple[int, int, int] = (3, 2, 1),
    neutralise_rolls: bool = True,
    roll_kwargs: Optional[dict] = None,
) -> CrackSpread:
    """Build the crack spread from leg prices.

    Parameters
    ----------
    legs
        DataFrame with ``CL`` ($/bbl), ``RB`` ($/gal), ``HO`` ($/gal).
    ratio
        (crude, gasoline, distillate). (3, 2, 1) is standard; (5, 3, 2) and
        (2, 1, 1) are the common alternatives and work here unchanged.
    neutralise_rolls
        Zero the day-on-day change on detected roll days. Leave this on for
        continuous Yahoo series; turn it off if you loaded genuine contract
        history where the gaps are real.

    Notes
    -----
    Neutralising a roll day is not free in reality — you pay the bid/ask on
    six legs to roll. Model that with ``CostModel.roll_cost_per_bbl``, which
    charges on exactly the days flagged here.
    """
    required = ("CL", "RB", "HO")
    missing = [c for c in required if c not in legs.columns]
    if missing:
        raise ValueError(f"legs is missing column(s): {missing}")

    legs = legs[list(required)].astype(float).sort_index().dropna()
    if legs.empty:
        raise ValueError("legs contains no complete rows")

    n_cl, n_rb, n_ho = ratio
    level = (
        n_rb * GAL_PER_BBL * legs["RB"]
        + n_ho * GAL_PER_BBL * legs["HO"]
        - n_cl * legs["CL"]
    ) / n_cl
    level.name = "spread"

    is_roll = detect_rolls(legs, **(roll_kwargs or {}))
    change = level.diff()
    if neutralise_rolls:
        change = change.mask(is_roll, 0.0)
    change = change.fillna(0.0)
    change.name = "spread_change"

    return CrackSpread(
        level=level, change=change, legs=legs, is_roll=is_roll, ratio=ratio
    )


def zscore(series: pd.Series, window: int, min_periods: Optional[int] = None) -> pd.Series:
    """Rolling z-score. Uses only data up to and including each date."""
    mp = min_periods if min_periods is not None else window
    mean = series.rolling(window, min_periods=mp).mean()
    sd = series.rolling(window, min_periods=mp).std()
    return ((series - mean) / sd.replace(0.0, np.nan)).rename("zscore")
