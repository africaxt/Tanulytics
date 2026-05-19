"""
run_all.py
──────────
Tanulytics Portfolio Aggregator — Master Pipeline
Runs all broker fetches sequentially, aggregates data, and pushes to Airtable + Notion.

Usage:
    python scripts/run_all.py               # Full pipeline
    python scripts/run_all.py --broker ibkr # Single broker only
    python scripts/run_all.py --dry-run     # Fetch only, no Airtable/Notion push

Flags:
    --broker    ibkr | fxcm | schwab | robinhood  (default: all)
    --dry-run   Fetch data and save to /data/raw/ but skip Airtable and Notion push
    --verbose   Print full raw data to console
"""

import argparse
import logging
import sys
import json
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT     = Path(__file__).parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PRO = ROOT / "data" / "processed"
LOGS     = ROOT / "logs"

DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PRO.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────

log_file = LOGS / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("tanulytics")

# ── Broker runners ────────────────────────────────────────────────────────────

def _run_broker(label: str, import_fn) -> dict | None:
    """
    Common broker-runner wrapper. Handles:
      - ImportError if the broker library isn't installed
      - Any unexpected exception from the fetcher itself
      - The fetcher's own error-dict return shape (auth_failed,
        connection_failed, fetch_failed: ...) — surfaces it as a
        warning, not a success.
    Returns the data dict (even on auth/fetch failure) so downstream
    code can decide whether to ignore broker-with-error or include it.
    Returns None only when the broker module itself couldn't be loaded
    or imported (a developer-side failure, distinct from a runtime auth
    failure on the broker's side).
    """
    log.info(f"── {label} ─────────────────────────────────────────────")
    try:
        main_fn = import_fn()
        data = main_fn(return_data=True) or {}
    except Exception as e:
        log.error(f"  ❌ {label} module load/run failed: {e}")
        return None

    n_positions = len(data.get("positions", []))
    n_trades    = len(data.get("trades", []))
    err = data.get("error")

    if err:
        log.warning(f"  ⚠️  {label}: {err}  "
                    f"(positions={n_positions}, trades={n_trades})")
    else:
        log.info(f"  ✅ {label}: {n_positions} positions, {n_trades} trades")
    return data


def run_ibkr() -> dict | None:
    def _import():
        from ibkr_fetch import main
        return main
    return _run_broker("IBKR", _import)


def run_fxcm() -> dict | None:
    def _import():
        from fxcm_fetch import main
        return main
    return _run_broker("FXCM", _import)


def run_schwab() -> dict | None:
    def _import():
        from schwab_fetch import main
        return main
    return _run_broker("Schwab", _import)


def run_robinhood() -> dict | None:
    def _import():
        from robinhood_fetch import main
        return main
    return _run_broker("Robinhood", _import)


def run_crypto_arb() -> dict | None:
    def _import():
        from crypto_arb_fetch import main
        return main
    return _run_broker("CryptoArb", _import)


def run_bitmex() -> dict | None:
    def _import():
        from bitmex_fetch import main
        return main
    return _run_broker("BitMEX", _import)


# ── Main pipeline ─────────────────────────────────────────────────────────────

BROKERS = {
    "ibkr":       run_ibkr,
    "fxcm":       run_fxcm,
    "schwab":     run_schwab,
    "robinhood":  run_robinhood,
    "crypto_arb": run_crypto_arb,
    "bitmex":     run_bitmex,
}


def main():
    parser = argparse.ArgumentParser(description="Tanulytics pipeline")
    parser.add_argument("--broker",  choices=list(BROKERS.keys()), help="Run single broker only (e.g. crypto_arb)")
    parser.add_argument("--dry-run", action="store_true", help="Fetch only, skip push")
    parser.add_argument("--verbose", action="store_true", help="Print raw data")
    args = parser.parse_args()

    run_time = datetime.now()
    log.info("=" * 60)
    log.info(f"  Tanulytics Pipeline — {run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    # ── Step 1: Fetch from brokers ─────────────────────────────
    brokers_to_run = {args.broker: BROKERS[args.broker]} if args.broker else BROKERS
    all_data = {}

    for name, runner in brokers_to_run.items():
        data = runner()
        if data:
            all_data[name] = data
            # Save raw JSON
            raw_path = DATA_RAW / f"{name}_{run_time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(raw_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            log.info(f"  Raw data saved: {raw_path.name}")

    log.info(f"\n  Brokers fetched successfully: {list(all_data.keys())}")
    log.info(f"  Brokers failed:              "
             f"{[b for b in brokers_to_run if b not in all_data]}")

    if args.dry_run:
        log.info("\n  Dry run — skipping aggregation and push.")
        return

    if not all_data:
        log.error("  No broker data fetched. Aborting pipeline.")
        sys.exit(1)

    # ── Step 2: Aggregate ──────────────────────────────────────
    log.info("\n── Aggregating data ─────────────────────────────────")
    try:
        from aggregator import aggregate
        combined = aggregate(all_data)
        processed_path = DATA_PRO / f"combined_{run_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(processed_path, "w") as f:
            json.dump(combined, f, indent=2, default=str)
        log.info(f"  ✅ Aggregated: {processed_path.name}")
    except Exception as e:
        log.error(f"  ❌ Aggregation failed: {e}")
        sys.exit(1)

    # ── Step 3: Push to Airtable ───────────────────────────────
    log.info("\n── Pushing to Airtable ──────────────────────────────")
    try:
        from airtable_push import push
        result = push(combined)
        log.info(f"  ✅ Airtable: {result['positions_upserted']} positions, "
                 f"{result['trades_inserted']} trades, "
                 f"{result['balances_upserted']} balances")
    except Exception as e:
        log.error(f"  ❌ Airtable push failed: {e}")

    # ── Step 4: Push daily summary to Notion ──────────────────
    log.info("\n── Pushing summary to Notion ────────────────────────")
    try:
        from notion_summary import push_summary
        push_summary(combined)
        log.info("  ✅ Notion daily summary updated")
    except Exception as e:
        log.error(f"  ❌ Notion push failed: {e}")

    # ── Done ───────────────────────────────────────────────────
    duration = (datetime.now() - run_time).seconds
    log.info(f"\n{'=' * 60}")
    log.info(f"  Pipeline complete in {duration}s")
    log.info(f"  Log saved to: {log_file}")
    log.info(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
