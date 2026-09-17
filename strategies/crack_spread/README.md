---
type: concept
name: CrackSpread321
category: strategy
status: draft
updated: 2026-09-10
tags: [strategy, backtest, energy, crack-spread, futures]
---

# 3:2:1 Crack Spread — backtesting toolkit

Research code for the refiner's margin trade. Read-only: nothing here places orders.

Lives at `strategies/crack_spread/`. Driver notebook: `strategies/Crack Spread 321 Backtest.ipynb`.

---

## The spread

Take three barrels of crude, sell two barrels of gasoline and one of distillate. The
difference is what refining that crude was worth, quoted in **$ per barrel of crude input**:

```
crack_$/bbl = (2 × 42 × RB  +  1 × 42 × HO  -  3 × CL) / 3
```

| Leg | Contract | Size | Quote |
|---|---|---|---|
| `CL` | WTI crude | 1,000 bbl | $/bbl |
| `RB` | RBOB gasoline | 42,000 gal (= 1,000 bbl) | $/gal |
| `HO` | NY Harbor ULSD | 42,000 gal (= 1,000 bbl) | $/gal |

The 42s convert gallons to barrels. The division by three expresses the margin per barrel
of crude, which is how refiners and the EIA quote it, and what makes the number comparable
across the 5:3:2 and 2:1:1 variants (both supported via `ratio=`).

**One 3:2:1 unit = short 3 CL · long 2 RB · long 1 HO. A $1.00/bbl move is $3,000.**

---

## Quick start

```python
from crack_spread import load_legs, build_spread, run_all, compare, report

legs    = load_legs(start="2005-01-01")     # cached to data/raw/crack_spread/
spread  = build_spread(legs)

report(spread)                              # does it revert? check before fitting
compare(run_all(spread))                    # four strategies + long-only benchmark
```

```bash
pip install yfinance          # the only dependency beyond pandas/numpy/matplotlib
python -m pytest crack_spread/tests -q
```

---

## Modules

| Module | What it owns |
|---|---|
| `data.py` | yfinance loader with disk cache, CSV loader for IBKR/EIA exports, synthetic generator, roll detection |
| `spread.py` | Spread construction, contract arithmetic, rolling z-score |
| `diagnostics.py` | Half-life, ADF, Hurst, rolling half-life — the pre-fit screen |
| `strategies.py` | The four signal generators |
| `backtest.py` | Execution lag, cost model, trade ledger |
| `metrics.py` | Sharpe, Sortino, CAGR, drawdown, trade stats, luck threshold |
| `optimise.py` | Grid search and anchored walk-forward |
| `run.py` | `run_all` / `compare` convenience runners |

---

## Strategies

| Name | Premise | Where it breaks |
|---|---|---|
| `zscore_reversion` | Refiners cut runs when the crack collapses and max out when it spikes, so extremes decay | The mean moves with capacity and demand regimes |
| `seasonality` | Gasoline cracks build into summer driving season, fade after Labour Day | The best-known calendar effect in energy — so it should already be priced into the curve |
| `ma_crossover`, `breakout` | The spread trends | Controls. If these beat reversion, the reversion premise is wrong on that sample |
| `regime_filtered` | Fade extremes, but stand down when the margin is genuinely repricing | One more parameter, and the filter can be late |

`seasonality(adaptive=True)` learns month signs from an expanding window of **prior years
only**. A hardcoded month list scores better and means less.

---

## The three things this package is careful about

**1 · Roll gaps.** Yahoo's `=F` tickers are unadjusted front-month continuations: on every
expiry the series jumps to the next contract's price. That jump is not P&L. `build_spread`
detects those gaps and zeroes the tradable change on those days; `CostModel.roll_cost_per_bbl`
then charges for the six fills a real roll costs. It is a heuristic — it cannot tell a roll
from a genuine shock of the same size, and errs toward removing P&L rather than inventing
it. For roll-free history, pull dated contract series through `ibkr_fetch.py` and load them
with `load_legs_csv`.

**2 · Look-ahead.** Signals are stated on each date's close; the engine applies them to the
*next* bar. That shift happens in exactly one place (`backtest`), so it cannot be
double-counted or quietly skipped. `test_execution_lag_prevents_lookahead` proves a signal
that knows today's move earns nothing, while one that knows tomorrow's earns everything.

**3 · Overfitting.** `grid_search` reports a `luck_threshold`: the Sharpe the best of N
random trials reaches on pure noise. `walk_forward` never evaluates a parameter set on the
data that chose it, and logs in-sample against out-of-sample Sharpe window by window. The
gap between those two columns is the finding.

---

## Costs

Defaults are pessimistic retail-futures assumptions. Tune the *strategy* against honest
costs, not the reverse.

```python
CostModel(
    slippage_per_bbl=0.05,      # one-way; $150/unit ≈ a tick on each of six contracts
    commission_per_unit=15.0,   # one-way, all six contracts
    roll_cost_per_bbl=0.03,     # per flagged roll day while positioned
)
```

`cost_share_of_gross` in the results table is the fraction of gross P&L the costs ate.
Above ~40%, the strategy is a broker's business rather than yours.

---

## Verification

`crack_spread/tests/test_engine.py` — 17 tests, all passing. They do not check that the
strategies make money; they check the machinery is honest:

- spread arithmetic matches the contract specs by hand calculation
- roll gaps are detected and neutralised
- position is exactly the target shifted by the execution lag
- trade-ledger P&L reconciles to daily P&L to 1e-9 (entry and exit costs attributed to the
  right trade, including on a flip)
- costs only ever subtract, monotonically
- P&L scales linearly with size while Sharpe does not
- on a spread engineered to mean-revert, reversion beats trend; on one engineered to
  trend, the verdict reverses; on a driftless random walk, nothing clears Sharpe 1.0
- walk-forward test windows always start after their training window ends

---

## Known limitations

- **Continuous-series approximation.** See "roll gaps" above. This is the largest single
  source of error in the P&L.
- **Close-to-close only.** No intraday fills, no stop execution within the bar. A stop
  modelled on closes is optimistic about gaps and pessimistic about noise.
- **Constant sizing.** One unit per unit of signal, and margin is a fixed
  `capital_per_unit`. Real NYMEX crack margin moves with volatility — and it moves *up*
  precisely when the spread is doing the thing that would have made money.
- **No fundamental data.** Refinery outages, Gulf Coast hurricane season, and RIN/RVO
  policy move cracks in ways price history does not anticipate. A statistical edge here has
  a counterparty who knows about the outage first.

---

## Related

[[TradingPlan]] · [[PipelineArchitecture]] · [[RiskFramework]] · [[TransactionCostModel]] · [[IBKR]]

*Not investment advice. Backtested results are not a forecast.*
