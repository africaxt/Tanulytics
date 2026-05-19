"""
schwab_fetch.py
───────────────
Tanulytics Portfolio Aggregator — Schwab Module
Fetches positions, account balances, and trade history from Charles Schwab
via the schwabdev wrapper around the official Schwab Trader API.

Requirements:
    pip install schwabdev python-dotenv

Setup (one-time):
    1. Create account at developer.schwab.com (separate from your brokerage login)
    2. Create an "Individual Developer" app:
       - Add a callback URL (e.g. https://127.0.0.1)
       - Wait for app status to flip from "Approved - Pending" to "Ready For Use"
         (typically a few business days — this is a Schwab manual review step)
    3. Copy the App Key and App Secret into config/.env as SCHWAB_APP_KEY and
       SCHWAB_APP_SECRET. Set SCHWAB_CALLBACK_URL if it differs from the default.
    4. First run opens a browser for OAuth login → schwabdev caches tokens.
       Subsequent runs refresh the access token automatically.

Token storage:
    Refresh tokens are persisted to .schwab_tokens.json alongside this script.
    NEVER commit this file — it grants 7 days of trading API access.
    The refresh-token cycle: access token = 30 min, refresh token = 7 days.
    schwabdev rotates both transparently as long as you run at least weekly.

Read-only contract:
    This script never calls Schwab's order-placement endpoints. It only invokes:
      - account_linked()        — list account hashes
      - account_details_all()   — balances + positions
      - transactions()          — trade history
    No order, replace, or cancel endpoints are reachable from this module.

Status:
    Written to-spec (May 2026). Awaiting first live run to validate the exact
    response shape from Schwab — at which point we tune the field-extraction
    in fetch_account_summary() / fetch_positions() to match reality.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Config & credentials ──────────────────────────────────────────────────────

# Load .env from the same directory as this script. Falls back silently if
# python-dotenv isn't installed (the env vars may already be set in the shell).
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "config" / ".env")
except ImportError:
    pass

APP_KEY      = os.getenv("SCHWAB_APP_KEY")
APP_SECRET   = os.getenv("SCHWAB_APP_SECRET")
CALLBACK_URL = os.getenv("SCHWAB_CALLBACK_URL", "https://127.0.0.1")

# Where schwabdev stores the OAuth tokens. Co-located with the script so the
# whole config folder is self-contained.
TOKENS_FILE = str(Path(__file__).parent.parent / "config" / ".schwab_tokens.json")

DAYS_BACK   = 30  # Trade-history window. Schwab allows up to 60 days per call.


# ── Client construction ───────────────────────────────────────────────────────

def make_client():
    """
    Build a schwabdev.Client. Returns None if credentials are missing or
    schwabdev raises during construction (most often: invalid keys, app not
    yet approved, or first-run OAuth flow timed out).
    """
    if not APP_KEY or not APP_SECRET or APP_KEY.startswith("your_"):
        print("  ❌ SCHWAB_APP_KEY / SCHWAB_APP_SECRET missing or still set to")
        print("     the .env template placeholder. Fill them in and retry.")
        return None

    try:
        import schwabdev
    except ImportError:
        print("  ❌ schwabdev not installed. Run: pip install schwabdev")
        return None

    try:
        # On first run this opens a browser for OAuth login and writes tokens to
        # TOKENS_FILE. On subsequent runs it silently refreshes the access token.
        client = schwabdev.Client(
            app_key=APP_KEY,
            app_secret=APP_SECRET,
            callback_url=CALLBACK_URL,
            tokens_file=TOKENS_FILE,
        )
        return client
    except Exception as e:
        print(f"  ❌ schwabdev.Client construction failed: {e}")
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _json(response):
    """
    Unwrap a schwabdev response. schwabdev returns requests.Response objects;
    raise_for_status surfaces HTTP errors, then .json() gives the payload.
    """
    response.raise_for_status()
    return response.json()


# ── Fetch functions ───────────────────────────────────────────────────────────

def fetch_account_hashes(client) -> list:
    """
    Return a list of {accountNumber, hashValue} dicts.
    The hashValue is what every subsequent endpoint takes — never the raw number.
    """
    print("\n── Linked accounts ──────────────────────────────────────")
    accounts = _json(client.account_linked())
    for a in accounts:
        # Schwab returns full account numbers; mask all but the last 4 in print.
        num = a.get("accountNumber", "")
        masked = ("•" * max(0, len(num) - 4)) + num[-4:] if num else "?"
        print(f"  account={masked}  hash={a.get('hashValue', '')[:12]}…")
    return accounts


def fetch_account_summary(client) -> dict:
    """
    Pull balances and positions for every linked account in a single call.
    Returns the raw payload keyed by accountHash so we can inspect the full
    Schwab response shape before designing the normalised schema.
    """
    print("\n── Account summary + positions ──────────────────────────")
    # fields="positions" includes the positions array inline with balances.
    # Omit fields to get balances only.
    raw = _json(client.account_details_all(fields="positions"))

    summary = {}
    for entry in raw:
        # Schwab nests everything under "securitiesAccount". The exact key may
        # be "securitiesAccount" or "aggregatedBalance" depending on account
        # type — we capture the full entry so the aggregator can branch later.
        sa = entry.get("securitiesAccount", entry)
        hash_id = sa.get("accountNumber") or sa.get("hashValue") or "unknown"
        summary[hash_id] = entry

        # Print the headline numbers for human sanity-checking.
        current = sa.get("currentBalances", {})
        print(f"  account={str(hash_id)[-4:]:>4s}  "
              f"NLV={current.get('liquidationValue', '—'):>12}  "
              f"cash={current.get('cashBalance', '—'):>12}  "
              f"buying_power={current.get('buyingPower', '—'):>12}")

    return summary


def fetch_positions(account_summary: dict) -> list:
    """
    Flatten the positions array out of the per-account summary into a single
    list of position dicts. Each position is enriched with the account hash
    so we can attribute P&L back later.

    We deliberately preserve Schwab's field names (e.g. longQuantity,
    averagePrice, marketValue) rather than renaming here — normalisation
    happens in aggregator.py after we've seen real data from all 4 brokers.
    """
    print("\n── Open positions ───────────────────────────────────────")
    rows = []
    for hash_id, entry in account_summary.items():
        sa = entry.get("securitiesAccount", entry)
        positions = sa.get("positions", []) or []
        for pos in positions:
            instrument = pos.get("instrument", {}) or {}
            row = {
                "account":            hash_id,
                "symbol":             instrument.get("symbol"),
                "asset_type":         instrument.get("assetType"),    # EQUITY / OPTION / etc.
                "cusip":              instrument.get("cusip"),
                "description":        instrument.get("description"),
                "long_quantity":      pos.get("longQuantity"),
                "short_quantity":     pos.get("shortQuantity"),
                "average_price":      pos.get("averagePrice"),
                "market_value":       pos.get("marketValue"),
                "current_day_pnl":    pos.get("currentDayProfitLoss"),
                "current_day_pnl_pct": pos.get("currentDayProfitLossPercentage"),
                "long_open_pnl":      pos.get("longOpenProfitLoss"),
                "short_open_pnl":     pos.get("shortOpenProfitLoss"),
                # Keep the raw position dict around for fields we may have missed.
                "_raw":               pos,
            }
            rows.append(row)
            print(f"  {row['symbol'] or '?':10s} {row['asset_type'] or '':6s} "
                  f"qty={row['long_quantity'] or row['short_quantity']:>10} "
                  f"avg={row['average_price']:>10}  "
                  f"mv={row['market_value']:>12}  "
                  f"daily_pnl={row['current_day_pnl']:>10}")

    if not rows:
        print("  No open positions found.")
    return rows


def fetch_trade_history(client, account_hashes: list, days_back: int = DAYS_BACK) -> list:
    """
    Pull executed transactions of type TRADE for each account over the past
    N days. Schwab caps the window per call at ~60 days, so 30 is comfortable.
    """
    print(f"\n── Trade history (last {days_back} days) ────────────────────")

    # Schwab expects ISO-8601 with milliseconds. UTC is safest.
    end   = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)
    start_iso = start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_iso   = end.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    rows = []
    for acct in account_hashes:
        hash_value = acct.get("hashValue")
        if not hash_value:
            continue
        try:
            txns = _json(client.transactions(
                accountHash=hash_value,
                startDate=start_iso,
                endDate=end_iso,
                types="TRADE",
            ))
        except Exception as e:
            print(f"  ⚠️  transactions failed for "
                  f"{str(acct.get('accountNumber', ''))[-4:]}: {e}")
            continue

        for tx in txns:
            # Schwab transactions are deeply nested; the executed trade lives
            # under transferItems[]. We flatten one row per item.
            for item in (tx.get("transferItems") or [tx]):
                instrument = item.get("instrument", {}) or {}
                row = {
                    "activity_id":      tx.get("activityId"),
                    "time":             tx.get("time"),
                    "type":             tx.get("type"),               # TRADE / RECEIVE_AND_DELIVER / etc.
                    "status":           tx.get("status"),
                    "subAccount":       tx.get("subAccount"),
                    "trade_date":       tx.get("tradeDate"),
                    "settlement_date":  tx.get("settlementDate"),
                    "position_id":      tx.get("positionId"),
                    "order_id":         tx.get("orderId"),
                    "account":          str(acct.get("accountNumber", ""))[-4:],
                    "symbol":           instrument.get("symbol"),
                    "asset_type":       instrument.get("assetType"),
                    "amount":           item.get("amount"),
                    "cost":             item.get("cost"),
                    "price":            item.get("price"),
                    "fee_type":         item.get("feeType"),
                    "_raw":             tx,
                }
                rows.append(row)
                print(f"  {row['time']}  {row['symbol'] or '?':8s} "
                      f"amt={row['amount']:>10}  px={row['price']:>10}  "
                      f"cost={row['cost']:>12}")

    if not rows:
        print("  No trades found in window.")
    return rows


def derive_pnl(account_summary: dict) -> dict:
    """
    Schwab doesn't expose a real-time P&L subscription (unlike IBKR's reqPnL).
    Instead, we derive a per-account daily P&L by summing the
    currentDayProfitLoss field across each account's positions.
    """
    print("\n── Derived daily P&L ────────────────────────────────────")
    pnl = {}
    for hash_id, entry in account_summary.items():
        sa = entry.get("securitiesAccount", entry)
        positions = sa.get("positions", []) or []
        daily   = sum((p.get("currentDayProfitLoss") or 0)    for p in positions)
        long_op = sum((p.get("longOpenProfitLoss")   or 0)    for p in positions)
        short_op = sum((p.get("shortOpenProfitLoss") or 0)    for p in positions)
        pnl[hash_id] = {
            "daily_pnl":      round(daily, 2),
            "long_open_pnl":  round(long_op, 2),
            "short_open_pnl": round(short_op, 2),
        }
        print(f"  account={str(hash_id)[-4:]:>4s}  "
              f"daily={daily:>10.2f}  long_open={long_op:>10.2f}  "
              f"short_open={short_op:>10.2f}")
    return pnl


# ── Main ──────────────────────────────────────────────────────────────────────

def main(return_data: bool = False):
    """
    Fetch all Schwab data.

    Args:
        return_data: If True, return the output dict instead of writing it to
                     a timestamped JSON file. run_all.py sets this to True so
                     the master pipeline owns raw-data persistence.

    Returns:
        dict with the same top-level shape as ibkr_fetch.main():
        fetched_at, broker, account_summary_tags, position_fields,
        trade_fields, account_summary, positions, trades, pnl.
        On any auth/setup failure, returns a dict with an "error" key.
    """
    print("=" * 60)
    print("  Tanulytics — Schwab Data Fetch")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("\n── Authenticating with Schwab ───────────────────────────")

    client = make_client()
    if client is None:
        return {
            "fetched_at": datetime.now().isoformat(),
            "broker":     "Schwab",
            "error":      "auth_failed",
            "positions":  [],
            "trades":     [],
            "pnl":        {},
        }

    try:
        accounts        = fetch_account_hashes(client)
        account_summary = fetch_account_summary(client)
        position_data   = fetch_positions(account_summary)
        trade_data      = fetch_trade_history(client, accounts)
        pnl_data        = derive_pnl(account_summary)

        # ── Summary output ────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  Raw data summary")
        print("=" * 60)
        print(f"  Linked accounts:          {len(accounts)}")
        print(f"  Open positions:           {len(position_data)}")
        print(f"  Trades (last {DAYS_BACK}d):       {len(trade_data)}")
        print(f"  P&L accounts:             {len(pnl_data)}")

        output = {
            "fetched_at":            datetime.now().isoformat(),
            "broker":                "Schwab",
            "account_summary_tags":  list(account_summary.keys()),
            "position_fields":       list(position_data[0].keys()) if position_data else [],
            "trade_fields":          list(trade_data[0].keys()) if trade_data else [],
            "account_summary":       account_summary,
            "positions":             position_data,
            "trades":                trade_data,
            "pnl":                   pnl_data,
        }

        if return_data:
            return output

        outfile = f"schwab_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(outfile, "w") as f:
            json.dump(output, f, indent=2, default=str)

        print(f"\n  Raw data saved to: {outfile}")
        print("  Share this file and we'll tune fetch_positions / fetch_trade_history")
        print("  against the actual Schwab response shape.\n")
        return output

    except Exception as e:
        # Catch-all so one bad endpoint doesn't sink the whole pipeline.
        # run_all.py will log this and continue with the other brokers.
        print(f"\n❌ Unexpected error during Schwab fetch: {e}")
        return {
            "fetched_at": datetime.now().isoformat(),
            "broker":     "Schwab",
            "error":      f"fetch_failed: {e}",
            "positions":  [],
            "trades":     [],
            "pnl":        {},
        }


if __name__ == "__main__":
    main()
