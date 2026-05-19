"""
fxcm_fetch.py
─────────────
Tanulytics Portfolio Aggregator — FXCM Module (TradingView-sourced).

Architecture note (May 2026):
    This module previously used fxcmpy to poll FXCM's REST API directly,
    but fxcmpy hasn't shipped since 2024 and FXCM access tokens are
    hard to obtain in 2026. Since TradingView is already the execution
    layer for the FXCM strategies (per project design: "TradingView
    handles FXCM execution"), this module now reads trade events that
    TradingView pushes to the local webhook receiver (tv_webhook_server.py),
    replays them into current positions, and emits the same output shape
    as ibkr_fetch, schwab_fetch, and robinhood_fetch — so the aggregator
    can treat all four brokers uniformly.

Data source:
    data/raw/tv_fxcm_events.jsonl  — one JSON object per line, appended by
    tv_webhook_server.py whenever TradingView fires a Pine Script alert
    on an FXCM strategy.

What this fetcher provides:
    ✓ Trades       — every event from the JSONL, filtered to the last N days
    ✓ Positions    — current open lots per symbol, reconstructed FIFO
    ✓ Realized PnL — per closing event, summed across the window
    ✗ Account balance, equity, buying power — NOT available from webhooks
    ✗ Unrealized PnL on open positions — needs a live price feed we don't have

    For the missing pieces, plan to periodically import an FXCM CSV
    statement and merge it in via aggregator.py. Tracked as the
    reconciliation step in the daily workflow.

Read-only contract:
    This module is file-IO only. It never opens a network socket to FXCM,
    TradingView, or anywhere else. The only risk surface is the JSONL log
    file, which is appended-to by the webhook server you control.

Status:
    Written May 2026. Awaiting first webhook event to validate the
    payload shape against real TradingView alerts.
"""

import json
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Config & paths ────────────────────────────────────────────────────────────

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "config" / ".env")
except ImportError:
    pass

DAYS_BACK = int(os.getenv("FXCM_LOOKBACK_DAYS", "30"))

# Same default path resolution as tv_webhook_server.py.
DATA_DIR = Path(os.getenv(
    "TANULYTICS_DATA_DIR",
    str(Path(__file__).resolve().parent.parent / "data" / "raw"),
))
LOG_FILE = DATA_DIR / "tv_fxcm_events.jsonl"


# ── Event reader ──────────────────────────────────────────────────────────────

def read_events() -> list:
    """
    Read the JSONL log into a list of event dicts, oldest-first.
    Missing log file returns []. Malformed lines are skipped with a warning.
    """
    if not LOG_FILE.exists():
        print(f"  ⚠️  No webhook log found at {LOG_FILE}")
        print(f"     Make sure tv_webhook_server.py has been running and has")
        print(f"     received at least one TradingView alert.")
        return []

    events = []
    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError as e:
                print(f"  ⚠️  Skipping malformed JSONL line {line_no}: {e}")
                continue

    # Sort by alert_time if present, falling back to received_at.
    def _sort_key(ev):
        return ev.get("alert_time") or ev.get("received_at") or ""
    events.sort(key=_sort_key)

    print(f"  Read {len(events)} events from {LOG_FILE.name}")
    return events


# ── Position reconstruction ───────────────────────────────────────────────────

def _to_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def reconstruct(events: list, window_cutoff: datetime) -> tuple:
    """
    Walk the events oldest-first and replay them through a FIFO matching
    engine. Returns (open_positions, trades_in_window, realized_pnl_total).

    Position model:
        For each symbol, maintain a deque of open lots. Each lot is
        {side: "long"|"short", qty, price, opened_at, source_event}.

        - An event with the same side as the queue head (or an empty queue)
          opens or adds to a position: append a new lot.
        - An event with the opposite side closes lots FIFO. Realized P&L
          per closed lot:
              long  closed: (exit_price - entry_price) * qty
              short closed: (entry_price - exit_price) * qty
        - If the closing event exceeds the existing lots, the surplus flips
          direction and opens a new lot.

    Notes:
        - "qty" is taken at face value from the alert. For FX micro-lots or
          contracts, the user's Pine Script should standardise units before
          alerting.
        - "side" is inferred from action: buy/long, sell/short. Pine Script's
          {{strategy.order.action}} emits "buy" or "sell".
        - Events are deduplicated on (symbol, action, qty, price, alert_time)
          so a TradingView retry doesn't double-count.
    """
    # Dedupe.
    seen = set()
    unique_events = []
    for ev in events:
        key = (
            ev.get("symbol"),
            (ev.get("action") or "").lower(),
            ev.get("qty"),
            ev.get("price"),
            ev.get("alert_time"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_events.append(ev)
    if len(unique_events) < len(events):
        print(f"  Deduplicated {len(events) - len(unique_events)} retry events.")

    # FIFO state per symbol.
    book = defaultdict(deque)   # symbol → deque of open lots
    trades_window = []          # closing events that fell inside the window
    realized_total = 0.0
    realized_in_window = 0.0

    def _parse_dt(s):
        if not s:
            return None
        s = str(s)
        # Try common TradingView formats: ms epoch, ISO 8601 with/without Z.
        if s.isdigit() and len(s) >= 10:
            try:
                return datetime.fromtimestamp(int(s) / 1000, tz=timezone.utc) \
                       if len(s) > 10 else datetime.fromtimestamp(int(s), tz=timezone.utc)
            except (ValueError, OSError):
                return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None

    for ev in unique_events:
        symbol = ev.get("symbol") or "UNKNOWN"
        action = (ev.get("action") or "").lower()
        qty    = _to_float(ev.get("qty"))
        price  = _to_float(ev.get("price"))
        ev_dt  = _parse_dt(ev.get("alert_time") or ev.get("received_at"))

        if qty <= 0 or not action:
            continue
        side = "long" if action.startswith("buy") else "short"

        lots = book[symbol]
        in_window = (ev_dt is not None and ev_dt >= window_cutoff)

        # Opening / adding to existing side, or starting a fresh position.
        if not lots or lots[0]["side"] == side:
            lots.append({
                "side":         side,
                "qty":          qty,
                "price":        price,
                "opened_at":    ev.get("alert_time") or ev.get("received_at"),
                "source_event": ev,
            })
            if in_window:
                trades_window.append({
                    "symbol":         symbol,
                    "action":         action,
                    "side":           side,
                    "qty":            qty,
                    "price":          price,
                    "alert_time":     ev.get("alert_time"),
                    "received_at":    ev.get("received_at"),
                    "kind":           "open",
                    "realized_pnl":   None,
                    "_raw":           ev,
                })
            continue

        # Closing — match FIFO against opposite-side lots.
        remaining = qty
        realized_for_this_event = 0.0
        while remaining > 0 and lots and lots[0]["side"] != side:
            lot = lots[0]
            close_qty = min(remaining, lot["qty"])
            if lot["side"] == "long":
                pnl = (price - lot["price"]) * close_qty   # long closed by sell
            else:
                pnl = (lot["price"] - price) * close_qty   # short closed by buy
            realized_for_this_event += pnl
            lot["qty"] -= close_qty
            remaining  -= close_qty
            if lot["qty"] <= 1e-9:
                lots.popleft()

        realized_total += realized_for_this_event
        if in_window:
            realized_in_window += realized_for_this_event

        if in_window:
            trades_window.append({
                "symbol":         symbol,
                "action":         action,
                "side":           side,
                "qty":            qty,
                "price":          price,
                "alert_time":     ev.get("alert_time"),
                "received_at":    ev.get("received_at"),
                "kind":           "close",
                "realized_pnl":   round(realized_for_this_event, 5),
                "_raw":           ev,
            })

        # Surplus → opens a new position in the opposite direction.
        if remaining > 0:
            lots.append({
                "side":         side,
                "qty":          remaining,
                "price":        price,
                "opened_at":    ev.get("alert_time") or ev.get("received_at"),
                "source_event": ev,
            })

    # Materialise open positions from the remaining lots.
    open_positions = []
    for symbol, lots in book.items():
        for lot in lots:
            if lot["qty"] > 1e-9:
                open_positions.append({
                    "symbol":         symbol,
                    "side":           lot["side"],
                    "qty":            round(lot["qty"], 5),
                    "entry_price":    lot["price"],
                    "opened_at":      lot["opened_at"],
                    "unrealised_pnl": None,   # No live price feed available.
                })

    return open_positions, trades_window, realized_total, realized_in_window


# ── Pretty-print helpers ──────────────────────────────────────────────────────

def _print_positions(positions):
    print("\n── Open positions (reconstructed) ───────────────────────")
    if not positions:
        print("  No open positions.")
        return
    for p in positions:
        print(f"  {p['symbol']:10s} {p['side']:5s} "
              f"qty={p['qty']:>10}  entry={p['entry_price']:>10}  "
              f"opened={p['opened_at']}")


def _print_trades(trades):
    print(f"\n── Trades in window ─────────────────────────────────────")
    if not trades:
        print("  No trades in window.")
        return
    for t in trades[:20]:
        rpnl = t.get("realized_pnl")
        rpnl_s = f"pnl={rpnl:>10.4f}" if rpnl is not None else "pnl=         -"
        print(f"  {t.get('alert_time') or t.get('received_at'):>28s}  "
              f"{t['symbol']:10s} {t['action']:5s} "
              f"qty={t['qty']:>8}  px={t['price']:>10}  "
              f"{t['kind']:>5s}  {rpnl_s}")
    if len(trades) > 20:
        print(f"  … and {len(trades) - 20} more (full list in returned data)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main(return_data: bool = False):
    """
    Read FXCM trade events from the local TradingView webhook log, replay
    them into current positions, and emit the standard fetcher output dict.

    Args:
        return_data: If True, return the output dict instead of writing
                     a timestamped JSON file. run_all.py sets this to True.

    Returns:
        dict with the same top-level shape as the other fetchers. On any
        unexpected failure, returns a dict with an "error" key.
    """
    print("=" * 60)
    print("  Tanulytics — FXCM (via TradingView webhooks)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"\n── Reading webhook log ──────────────────────────────────")

    try:
        events = read_events()
    except Exception as e:
        print(f"\n❌ Failed to read webhook log: {e}")
        return {
            "fetched_at": datetime.now().isoformat(),
            "broker":     "TV-FXCM",
            "error":      f"log_read_failed: {e}",
            "positions":  [],
            "trades":     [],
            "pnl":        {},
        }

    window_cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)

    try:
        positions, trades, realized_total, realized_in_window = reconstruct(
            events, window_cutoff,
        )
    except Exception as e:
        print(f"\n❌ Reconstruction failed: {e}")
        return {
            "fetched_at": datetime.now().isoformat(),
            "broker":     "TV-FXCM",
            "error":      f"reconstruct_failed: {e}",
            "positions":  [],
            "trades":     [],
            "pnl":        {},
        }

    _print_positions(positions)
    _print_trades(trades)

    pnl = {
        "realized_pnl_all_time":   round(realized_total, 5),
        f"realized_pnl_{DAYS_BACK}d": round(realized_in_window, 5),
        "open_positions_count":    len(positions),
        "events_processed":        len(events),
        # Cannot compute unrealised P&L without a live price feed; aggregator
        # will fill this in if/when an FXCM CSV statement is merged.
        "unrealised_pnl":          None,
        "equity":                  None,
        "buying_power":            None,
    }

    print("\n" + "=" * 60)
    print("  Raw data summary")
    print("=" * 60)
    print(f"  Events processed:         {len(events)}")
    print(f"  Open positions:           {len(positions)}")
    print(f"  Trades in window:         {len(trades)}")
    print(f"  Realized P&L (all-time):  {realized_total:.4f}")
    print(f"  Realized P&L ({DAYS_BACK}d):     {realized_in_window:.4f}")

    output = {
        "fetched_at":            datetime.now().isoformat(),
        "broker":                "TV-FXCM",
        "account_summary_tags":  [],
        "position_fields":       list(positions[0].keys()) if positions else [],
        "trade_fields":          list(trades[0].keys())   if trades else [],
        "account_summary":       {},   # Not available from webhooks alone.
        "positions":             positions,
        "trades":                trades,
        "pnl":                   pnl,
        "_source":               "tradingview_webhook",
        "_log_file":             str(LOG_FILE),
    }

    if return_data:
        return output

    outfile = f"fxcm_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(outfile, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Raw data saved to: {outfile}\n")
    return output


if __name__ == "__main__":
    main()
