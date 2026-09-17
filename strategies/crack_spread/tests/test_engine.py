"""
Verification suite.

These tests do not check that the strategies make money. They check that the
machinery is honest: that the spread arithmetic matches the contract specs,
that no signal can see the future, that trade P&L reconciles with daily P&L,
that costs only ever subtract — and that on a series engineered to mean-revert
the reversion strategy wins while the trend strategy does not, with the
verdict reversing on a series engineered to trend.

Run with:  python -m pytest crack_spread/tests -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from crack_spread import (  # noqa: E402
    CostModel,
    backtest,
    build_spread,
    compare,
    ma_crossover,
    performance,
    run_all,
    synthetic_legs,
    zscore_reversion,
)
from crack_spread.spread import DOLLARS_PER_BBL_PER_UNIT  # noqa: E402


# --------------------------------------------------------------------------
# spread arithmetic
# --------------------------------------------------------------------------

def test_spread_matches_hand_calculation():
    legs = pd.DataFrame(
        {"CL": [80.0], "RB": [2.50], "HO": [2.80]},
        index=pd.to_datetime(["2024-01-02"]),
    )
    spread = build_spread(legs, neutralise_rolls=False)
    expected = (2 * 42 * 2.50 + 1 * 42 * 2.80 - 3 * 80.0) / 3
    assert spread.level.iloc[0] == pytest.approx(expected)
    # 2 gasoline barrels at $105.00 + 1 distillate barrel at $117.60
    # less 3 crude barrels at $80.00, divided by 3 barrels of crude input.
    assert spread.level.iloc[0] == pytest.approx(29.20, abs=1e-9)


def test_dollars_per_unit_is_three_thousand():
    legs = synthetic_legs(n=50)
    spread = build_spread(legs)
    assert spread.dollars_per_unit == DOLLARS_PER_BBL_PER_UNIT == 3_000.0


def test_five_three_two_ratio_supported():
    legs = pd.DataFrame(
        {"CL": [80.0], "RB": [2.50], "HO": [2.80]},
        index=pd.to_datetime(["2024-01-02"]),
    )
    s = build_spread(legs, ratio=(5, 3, 2), neutralise_rolls=False)
    expected = (3 * 42 * 2.50 + 2 * 42 * 2.80 - 5 * 80.0) / 5
    assert s.level.iloc[0] == pytest.approx(expected)
    assert s.dollars_per_unit == 5_000.0


def test_roll_gaps_are_neutralised():
    legs = synthetic_legs(n=400, seed=3)
    legs.iloc[200:, legs.columns.get_loc("CL")] *= 1.25   # a 25% contract gap
    spread = build_spread(legs)
    assert bool(spread.is_roll.iloc[200])
    assert spread.change.iloc[200] == 0.0
    # the raw level still shows the jump; only tradable change is zeroed
    assert abs(spread.level.diff().iloc[200]) > 10


# --------------------------------------------------------------------------
# engine integrity
# --------------------------------------------------------------------------

def test_execution_lag_prevents_lookahead():
    """Knowing today's move must be worth nothing; knowing tomorrow's, everything."""
    legs = synthetic_legs(n=2000, seed=11, kind="random")
    spread = build_spread(legs)
    free = CostModel(0.0, 0.0, 0.0)

    # A signal that knows TOMORROW's move, stated today. The one-bar lag puts
    # it to work on exactly the day it predicted, so it should mint money.
    oracle = np.sign(spread.change.shift(-1)).fillna(0.0)
    assert backtest(spread, oracle, costs=free).total_pnl_usd > 0

    # A signal that knows TODAY's move, stated today. After the lag it is
    # betting that today's direction repeats tomorrow — on a random walk,
    # worth nothing. If this earned anything, the engine would be leaking
    # same-bar information into P&L.
    same_bar = np.sign(spread.change).fillna(0.0)
    assert abs(performance(backtest(spread, same_bar, costs=free))["sharpe"]) < 0.35

    # And the P&L identity itself: nothing but position[t] × change[t].
    res = backtest(spread, oracle, costs=free)
    assert res.pnl_usd.sum() == pytest.approx(
        float((res.position * spread.change).sum()) * 3_000.0, rel=1e-9
    )


def test_position_is_exactly_target_shifted():
    legs = synthetic_legs(n=300, seed=5)
    spread = build_spread(legs)
    target = zscore_reversion(spread)
    res = backtest(spread, target)
    pd.testing.assert_series_equal(
        res.position, target.shift(1).fillna(0.0).rename("position"),
        check_names=False,
    )


def test_trade_pnl_reconciles_with_daily_pnl():
    legs = synthetic_legs(n=1500, seed=21)
    spread = build_spread(legs)
    res = backtest(spread, zscore_reversion(spread))
    assert not res.trades.empty
    assert res.trades["pnl_usd"].sum() == pytest.approx(res.total_pnl_usd, rel=1e-9)


def test_pnl_scales_linearly_with_units():
    legs = synthetic_legs(n=900, seed=13)
    spread = build_spread(legs)
    target = zscore_reversion(spread)
    one = backtest(spread, target, units=1.0)
    ten = backtest(spread, target, units=10.0)
    assert ten.total_pnl_usd == pytest.approx(10 * one.total_pnl_usd, rel=1e-9)
    # Sharpe is scale-invariant; that is the point of using it to compare.
    assert performance(ten)["sharpe"] == pytest.approx(performance(one)["sharpe"], rel=1e-9)


def test_costs_only_ever_reduce_pnl():
    legs = synthetic_legs(n=1200, seed=17)
    spread = build_spread(legs)
    target = zscore_reversion(spread)
    free = backtest(spread, target, costs=CostModel(0.0, 0.0, 0.0))
    cheap = backtest(spread, target, costs=CostModel(0.02, 5.0, 0.01))
    dear = backtest(spread, target, costs=CostModel(0.20, 50.0, 0.10))
    assert free.total_pnl_usd > cheap.total_pnl_usd > dear.total_pnl_usd
    assert (free.cost_bbl == 0).all()
    assert (dear.cost_bbl >= 0).all()


def test_flat_strategy_costs_nothing_and_earns_nothing():
    legs = synthetic_legs(n=500, seed=2)
    spread = build_spread(legs)
    flat = pd.Series(0.0, index=spread.level.index)
    res = backtest(spread, flat)
    assert res.total_pnl_usd == 0.0
    assert res.trades.empty
    assert performance(res)["exposure"] == 0.0


def test_long_only_pnl_equals_spread_change_times_multiplier():
    legs = synthetic_legs(n=600, seed=8)
    spread = build_spread(legs)
    always_long = pd.Series(1.0, index=spread.level.index)
    res = backtest(spread, always_long, costs=CostModel(0.0, 0.0, 0.0))
    expected = spread.change.iloc[1:].sum() * 3_000.0
    assert res.total_pnl_usd == pytest.approx(expected, rel=1e-9)


# --------------------------------------------------------------------------
# does the engine recover a known signal?
# --------------------------------------------------------------------------

def test_reversion_beats_trend_on_a_mean_reverting_spread():
    legs = synthetic_legs(n=3000, seed=42, kind="reverting", theta=0.04)
    spread = build_spread(legs)
    rev = backtest(spread, zscore_reversion(spread, lookback=40, entry=1.5, exit=0.25),
                   costs=CostModel(0.0, 0.0, 0.0))
    trend = backtest(spread, ma_crossover(spread), costs=CostModel(0.0, 0.0, 0.0))
    assert rev.total_pnl_usd > 0
    assert performance(rev)["sharpe"] > performance(trend)["sharpe"]


def test_trend_beats_reversion_on_a_trending_spread():
    legs = synthetic_legs(n=3000, seed=42, kind="trending", drift=0.02)
    spread = build_spread(legs)
    rev = backtest(spread, zscore_reversion(spread, lookback=40, entry=1.5, exit=0.25),
                   costs=CostModel(0.0, 0.0, 0.0))
    trend = backtest(spread, ma_crossover(spread), costs=CostModel(0.0, 0.0, 0.0))
    assert performance(trend)["sharpe"] > performance(rev)["sharpe"]


def test_nothing_works_on_a_driftless_random_walk():
    """Sanity floor: on pure noise, no strategy should post a real Sharpe."""
    legs = synthetic_legs(n=3000, seed=99, kind="random")
    spread = build_spread(legs)
    table = compare(run_all(spread, include_buy_and_hold=False))
    assert table["sharpe"].max() < 1.0


# --------------------------------------------------------------------------
# strategy sanity
# --------------------------------------------------------------------------

def test_positions_stay_within_bounds():
    legs = synthetic_legs(n=2000, seed=31)
    spread = build_spread(legs)
    for name, res in run_all(spread).items():
        assert res.target.abs().max() <= 1.0, name
        assert res.target.isin([-1.0, 0.0, 1.0]).all(), name


def test_adaptive_seasonality_has_a_warmup_with_no_trades():
    legs = synthetic_legs(n=2500, seed=4)
    spread = build_spread(legs)
    from crack_spread import seasonality
    pos = seasonality(spread, adaptive=True, min_years=5)
    first_five_years = pos.index < (pos.index[0] + pd.DateOffset(years=5))
    assert (pos[first_five_years] == 0).all()


def test_walk_forward_is_out_of_sample():
    legs = synthetic_legs(n=3000, seed=7, kind="reverting")
    spread = build_spread(legs)
    from crack_spread import walk_forward
    res, log = walk_forward(
        spread, zscore_reversion,
        grid={"lookback": [40, 80], "entry": [1.5, 2.5]},
        train_years=4, test_years=1,
    )
    assert not log.empty
    # every out-of-sample window starts after its training window ends
    assert (pd.to_datetime(log["test_start"]) > pd.to_datetime(log["train_end"])).all()
    # the stitched result covers only test periods
    assert res.position.index[0] >= pd.Timestamp(log["test_start"].iloc[0])
