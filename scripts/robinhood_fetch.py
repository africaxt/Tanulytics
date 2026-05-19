"""
robinhood_fetch.py
──────────────────
Tanulytics Portfolio Aggregator — Robinhood Module
Fetches positions, account profile, and stock/option order history from
Robinhood via the robin_stocks unofficial wrapper.

Requirements:
    pip install robin_stocks python-dotenv pyotp

Auth strategy (two supported paths):

    1. AUTOMATED — Recommended for daily pipeline runs.
       Enable 2FA in Robinhood app, choose "Authenticator app" → "Other",
       which surfaces an alphanumeric TOTP secret. Save that secret to
       config/.env as ROBINHOOD_TOTP_SECRET. This module will generate a
       fresh 6-digit code per login via pyotp — no human in the loop.

    2. INTERACTIVE — Fallback for one-off runs.
       If ROBINHOOD_TOTP_SECRET is empty/missing, robin_stocks will prompt
       on stdin for the SMS or email code. This path will block run_all.py
       in automated mode, so prefer path 1 for daily use.

Session caching:
    robin_stocks writes a pickle to ~/.tokens/robinhood.pickle so subsequent
    logins inside the token TTL skip the auth round trip entirely. This
    means the TOTP code is only actually consumed every ~24h.

Read-only contract:
    This script touches only profile/holdings/order-history endpoints:
      - r.profiles.load_account_profile()
      - r.profiles.load_portfolio_profile()
      - r.account.build_holdings()
      - r.account.get_open_stock_positions()
      - r.orders.get_all_stock_orders()
      - r.orders.get_all_option_orders()
    It never calls r.orders.order_buy_*, order_sell_*, or any place-order
    endpoint. Manual code review of this file is sufficient to verify.

⚠️  robin_stocks is an UNOFFICIAL reverse-engineered wrapper. Robinhood can
    change their private API without notice and break this module. The
    fallback is the weekly manual CSV export from the Robinhood website.

Status:
    Written to-spec (May 2026). First live run will be a smoke test against
    the actual account; field-extraction in fetch_positions / fetch_trade_history
    may need tuning based on what Robinhood actually returns.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Config & credentials ──────────────────────────────────────────────────────

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "config" / ".env")
except ImportError:
    pass

USERNAME     = os.getenv("ROBINHOOD_USERNAME")
PASSWORD     = os.getenv("ROBINHOOD_PASSWORD")
TOTP_SECRET  = os.getenv("ROBINHOOD_TOTP_SECRET")  # Optional but recommended.

DAYS_BACK    = 30  # Trade-history window. Robinhood returns ALL orders ever
                   # by default; we filter client-side to keep the payload sane.


# ── Auth ──────────────────────────────────────────────────────────────────────

def login():
    """
    Authenticate to Robinhood. Returns the robin_stocks.robinhood module on
    success (so the caller can use r.account.* etc.), or None on failure.

    Priority order:
        1. ROBINHOOD_TOTP_SECRET set → generate code via pyotp, non-interactive.
        2. Otherwise → robin_stocks will prompt stdin for SMS/email MFA code.
    """
    if (not USERNAME or not PASSWORD
            or USERNAME.startswith("your_") or PASSWORD.startswith("your_")):
        print("  ❌ ROBINHOOD_USERNAME / ROBINHOOD_PASSWORD missing or still set")
        print("     to the .env template placeholder. Fill them in and retry.")
        return None

    try:
        import robin_stocks.robinhood as r
    except ImportError:
        print("  ❌ robin_stocks not installed. Run: pip install robin_stocks")
        return None

    mfa_code = None
    if TOTP_SECRET and not TOTP_SECRET.startswith("your_"):
        try:
            import pyotp
            mfa_code = pyotp.TOTP(TOTP_SECRET).now()
            print(f"  Using TOTP-generated MFA code (expires in "
                  f"{30 - datetime.now().second % 30}s).")
        except ImportError:
            print("  ⚠️  pyotp not installed — will fall back to interactive prompt.")
            print("     Run: pip install pyotp")
        except Exception as e:
            print(f"  ⚠️  TOTP generation failed: {e} — falling back to prompt.")
    else:
        print("  No ROBINHOOD_TOTP_SECRET set — robin_stocks will prompt for MFA.")

    try:
        r.login(
            username=USERNAME,
            password=PASSWORD,
            mfa_code=mfa_code,
            store_session=True,   # Cache token to ~/.tokens/robinhood.pickle
            expiresIn=86400,      # 24h — re-auth daily, well within Robinhood's max.
            by_sms=False,         # Prefer email/authenticator over SMS when prompted.
        )
        print("  ✅ Logged in to Robinhood.")
        return r
    except Exception as e:
        print(f"  ❌ Login failed: {e}")
        return None


# ── Fetch functions ───────────────────────────────────────────────────────────

def fetch_account_summary(r) -> dict:
    """
    Pull both profiles: account_profile (cash, buying power, settled funds)
    and portfolio_profile (equity, market_value, extended_hours_equity).
    Returned as a single dict so the aggregator can flatten in one place.
    """
    print("\n── Account profiles ─────────────────────────────────────")
    try:
        account_profile   = r.profiles.load_account_profile()    or {}
        portfolio_profile = r.profiles.load_portfolio_profile()  or {}
    except Exception as e:
        print(f"  ⚠️  Profile fetch failed: {e}")
        return {}

    summary = {
        "account_profile":   account_profile,
        "portfolio_profile": portfolio_profile,
    }

    # Print the headline numbers for human sanity-checking.
    headline = {
        "equity":             portfolio_profile.get("equity"),
        "market_value":       portfolio_profile.get("market_value"),
        "extended_equity":    portfolio_profile.get("extended_hours_equity"),
        "cash":               account_profile.get("cash"),
        "buying_power":       account_profile.get("buying_power"),
        "withdrawable":       account_profile.get("cash_available_for_withdrawal"),
    }
    for k, v in headline.items():
        if v is not None:
            print(f"  {k:20s} {str(v):>18s}")

    return summary


def fetch_positions(r) -> list:
    """
    Pull holdings via two complementary endpoints:
      - build_holdings() returns the human-friendly per-symbol view
      - get_open_stock_positions() returns the raw Robinhood position objects
    We merge both so the aggregator has high-level and detailed fields.

    Returns one row per held symbol.
    """
    print("\n── Open positions ───────────────────────────────────────")

    try:
        holdings = r.account.build_holdings() or {}
    except Exception as e:
        print(f"  ⚠️  build_holdings failed: {e}")
        holdings = {}

    try:
        raw_positions = r.account.get_open_stock_positions() or []
    except Exception as e:
        print(f"  ⚠️  get_open_stock_positions failed: {e}")
        raw_positions = []

    # Index raw positions by instrument URL so we can look them up by symbol later.
    # Each raw position has an "instrument" URL; we don't resolve it to a symbol
    # here (would require an extra request per position) — we just keep the raw
    # object alongside each holding and let the aggregator decide if it needs more.
    rows = []
    for symbol, h in holdings.items():
        # Coerce numeric strings into floats where present.
        def _f(key):
            v = h.get(key)
            try:
                return float(v) if v not in (None, "") else None
            except (TypeError, ValueError):
                return v

        row = {
            "symbol":             symbol,
            "name":               h.get("name"),
            "type":               h.get("type"),                 # stock / etp / etc.
            "id":                 h.get("id"),
            "quantity":           _f("quantity"),
            "average_buy_price":  _f("average_buy_price"),
            "price":              _f("price"),
            "equity":             _f("equity"),
            "equity_change":      _f("equity_change"),           # $ change today
            "percent_change":     _f("percent_change"),          # % change today
            "percentage":         _f("percentage"),              # % of portfolio
            "pe_ratio":           _f("pe_ratio"),
            "_raw_holding":       h,
        }
        rows.append(row)
        print(f"  {symbol:8s} qty={row['quantity']:>10}  "
              f"avg={row['average_buy_price']:>10}  "
              f"px={row['price']:>10}  equity={row['equity']:>12}  "
              f"chg={row['equity_change']:>10}")

    if not rows:
        print("  No open positions found.")

    # Attach the raw position list as a separate top-level field of the output
    # via the closure trick won't work here — we'll surface it through main().
    fetch_positions._last_raw_positions = raw_positions   # noqa: side-channel
    return rows


def fetch_trade_history(r, days_back: int = DAYS_BACK) -> list:
    """
    Pull stock and option orders, filter client-side to the last N days,
    and flatten into a single trades list. Only filled orders are kept —
    cancelled/pending orders are noise for a portfolio aggregator.
    """
    print(f"\n── Trade history (last {days_back} days) ────────────────────")

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    try:
        stock_orders = r.orders.get_all_stock_orders() or []
    except Exception as e:
        print(f"  ⚠️  get_all_stock_orders failed: {e}")
        stock_orders = []

    try:
        option_orders = r.orders.get_all_option_orders() or []
    except Exception as e:
        # Account may not be options-approved; that's not a failure.
        print(f"  ℹ️  get_all_option_orders unavailable ({e}) — skipping options.")
        option_orders = []

    def _parse_dt(s):
        if not s:
            return None
        # Robinhood returns ISO-8601 with 'Z' suffix.
        return datetime.fromisoformat(s.replace("Z", "+00:00"))

    rows = []

    for o in stock_orders:
        if o.get("state") != "filled":
            continue
        created = _parse_dt(o.get("created_at"))
        if not created or created < cutoff:
            continue

        # Filled orders may have multiple executions at different prices —
        # we flatten one row per execution to mirror IBKR's fills() granularity.
        executions = o.get("executions") or [{}]
        for ex in executions:
            row = {
                "order_id":        o.get("id"),
                "execution_id":    ex.get("id"),
                "created_at":      o.get("created_at"),
                "executed_at":     ex.get("timestamp"),
                "instrument":      o.get("instrument"),       # URL — symbol resolved below if cached
                "symbol":          o.get("symbol") or o.get("instrument_symbol"),
                "side":            o.get("side"),             # buy / sell
                "type":            o.get("type"),             # market / limit
                "asset_type":      "stock",
                "quantity":        ex.get("quantity") or o.get("quantity"),
                "price":           ex.get("price") or o.get("price"),
                "average_price":   o.get("average_price"),
                "fees":            o.get("fees"),
                "state":           o.get("state"),
                "_raw":            o,
            }
            rows.append(row)

    for o in option_orders:
        if o.get("state") != "filled":
            continue
        created = _parse_dt(o.get("created_at"))
        if not created or created < cutoff:
            continue

        for leg in (o.get("legs") or [{}]):
            for ex in (leg.get("executions") or [{}]):
                row = {
                    "order_id":      o.get("id"),
                    "execution_id":  ex.get("id"),
                    "created_at":    o.get("created_at"),
                    "executed_at":   ex.get("timestamp"),
                    "instrument":    leg.get("option"),
                    "symbol":        o.get("chain_symbol"),
                    "side":          leg.get("side"),
                    "position_effect": leg.get("position_effect"),  # open / close
                    "type":          o.get("type"),
                    "asset_type":    "option",
                    "quantity":      ex.get("quantity"),
                    "price":         ex.get("price"),
                    "average_price": o.get("price"),
                    "premium":       o.get("premium"),
                    "state":         o.get("state"),
                    "_raw":          o,
                }
                rows.append(row)

    # Sort newest first for readability.
    rows.sort(key=lambda x: x.get("executed_at") or x.get("created_at") or "", reverse=True)

    for row in rows[:20]:   # Only print first 20 to keep console output bounded.
        print(f"  {row['executed_at'] or row['created_at']}  "
              f"{(row['symbol'] or '?'):8s} {(row['side'] or ''):5s} "
              f"qty={row['quantity']:>10}  px={row['price']:>10}  "
              f"({row['asset_type']})")
    if len(rows) > 20:
        print(f"  … and {len(rows) - 20} more (full list in returned data)")
    if not rows:
        print("  No filled trades in window.")

    return rows


def derive_pnl(account_summary: dict, positions: list) -> dict:
    """
    Robinhood doesn't expose a real-time P&L stream. We derive:
      - daily_pnl   = sum of equity_change across positions
      - total_pnl   = portfolio equity – sum of (avg_buy_price × quantity)
    All values are best-effort and assume single-currency USD account.
    """
    print("\n── Derived P&L ──────────────────────────────────────────")

    daily_pnl = sum((p.get("equity_change") or 0) for p in positions
                    if isinstance(p.get("equity_change"), (int, float)))

    # Total unrealised P&L: current equity minus cost basis (sum of avg × qty).
    cost_basis = 0.0
    for p in positions:
        q   = p.get("quantity")
        avg = p.get("average_buy_price")
        if isinstance(q, (int, float)) and isinstance(avg, (int, float)):
            cost_basis += q * avg

    portfolio_equity = None
    portfolio_profile = (account_summary or {}).get("portfolio_profile", {})
    try:
        portfolio_equity = float(portfolio_profile.get("equity"))
    except (TypeError, ValueError):
        portfolio_equity = None

    unrealised_pnl = (portfolio_equity - cost_basis) if portfolio_equity is not None else None

    pnl = {
        "daily_pnl":        round(daily_pnl, 2),
        "cost_basis":       round(cost_basis, 2),
        "portfolio_equity": portfolio_equity,
        "unrealised_pnl":   round(unrealised_pnl, 2) if unrealised_pnl is not None else None,
    }
    print(f"  daily_pnl:        {pnl['daily_pnl']}")
    print(f"  cost_basis:       {pnl['cost_basis']}")
    print(f"  portfolio_equity: {pnl['portfolio_equity']}")
    print(f"  unrealised_pnl:   {pnl['unrealised_pnl']}")
    return pnl


# ── Main ──────────────────────────────────────────────────────────────────────

def main(return_data: bool = False):
    """
    Fetch all Robinhood data.

    Args:
        return_data: If True, return the output dict instead of writing it to
                     a timestamped JSON file. run_all.py sets this to True.

    Returns:
        dict with the same top-level shape as ibkr_fetch.main() and
        schwab_fetch.main(). On auth/setup failure, returns a dict with
        an "error" key (and empty positions/trades/pnl) so callers can
        safely .get("positions", []) without AttributeError.
    """
    print("=" * 60)
    print("  Tanulytics — Robinhood Data Fetch")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("\n── Authenticating with Robinhood ────────────────────────")

    r = login()
    if r is None:
        return {
            "fetched_at": datetime.now().isoformat(),
            "broker":     "Robinhood",
            "error":      "auth_failed",
            "positions":  [],
            "trades":     [],
            "pnl":        {},
        }

    try:
        account_summary = fetch_account_summary(r)
        position_data   = fetch_positions(r)
        raw_positions   = getattr(fetch_positions, "_last_raw_positions", [])
        trade_data      = fetch_trade_history(r)
        pnl_data        = derive_pnl(account_summary, position_data)

        # ── Summary output ────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  Raw data summary")
        print("=" * 60)
        print(f"  Profile fields:           "
              f"{len(account_summary.get('account_profile', {})) + len(account_summary.get('portfolio_profile', {}))}")
        print(f"  Open positions:           {len(position_data)}")
        print(f"  Raw position objects:     {len(raw_positions)}")
        print(f"  Trades (last {DAYS_BACK}d):       {len(trade_data)}")

        output = {
            "fetched_at":            datetime.now().isoformat(),
            "broker":                "Robinhood",
            "account_summary_tags":  list(account_summary.keys()),
            "position_fields":       list(position_data[0].keys()) if position_data else [],
            "trade_fields":          list(trade_data[0].keys()) if trade_data else [],
            "account_summary":       account_summary,
            "positions":             position_data,
            "raw_positions":         raw_positions,
            "trades":                trade_data,
            "pnl":                   pnl_data,
        }

        if return_data:
            return output

        outfile = f"robinhood_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(outfile, "w") as f:
            json.dump(output, f, indent=2, default=str)

        print(f"\n  Raw data saved to: {outfile}")
        print("  Share this file and we'll tune the field-extraction in")
        print("  fetch_positions / fetch_trade_history against reality.\n")
        return output

    except Exception as e:
        print(f"\n❌ Unexpected error during Robinhood fetch: {e}")
        return {
            "fetched_at": datetime.now().isoformat(),
            "broker":     "Robinhood",
            "error":      f"fetch_failed: {e}",
            "positions":  [],
            "trades":     [],
            "pnl":        {},
        }
    finally:
        # Best-effort logout — doesn't matter if it fails. Keeps the local
        # session token rotated when the script is run interactively.
        try:
            r.logout()
        except Exception:
            pass


if __name__ == "__main__":
    main()
