"""
bitmex_fetch.py
────────────────
Tanulytics — BitMEX Broker Fetcher

Fetches live positions, recent trades, and account balance from BitMEX
via ccxt. Replaces the direct-API approach in africaxtn/AfricaX-Trading
(ChitBitMEX) with the same normalised schema used by all Tanulytics fetchers.

Credentials:
    BITMEX_API_KEY    and    BITMEX_API_SECRET    in config/.env
    BITMEX_TESTNET=true to point at testnet.bitmex.com (default: false)

Dependencies:
    pip install ccxt python-dotenv
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "config" / ".env")
except ImportError:
    pass

try:
    import ccxt
except ImportError:
    print("ccxt not installed. Run: pip install ccxt")
    sys.exit(1)

API_KEY    = os.getenv("BITMEX_API_KEY", "")
API_SECRET = os.getenv("BITMEX_API_SECRET", "")
TESTNET    = os.getenv("BITMEX_TESTNET", "false").lower() == "true"
SYMBOL     = os.getenv("BITMEX_SYMBOL", "BTC/USD:BTC")   # ccxt unified symbol for XBTUSD perp
TRADE_LIMIT = int(os.getenv("BITMEX_TRADE_LIMIT", "50"))


def _build_exchange() -> ccxt.bitmex:
    exchange = ccxt.bitmex({
        "apiKey":          API_KEY,
        "secret":          API_SECRET,
        "enableRateLimit": True,
    })
    if TESTNET:
        exchange.set_sandbox_mode(True)
    return exchange


def _fetch_positions(exchange: ccxt.bitmex) -> list:
    try:
        raw = exchange.fetch_positions()
        return [p for p in raw if p.get("contracts") and p["contracts"] != 0]
    except Exception as e:
        return [{"error": str(e)}]


def _fetch_trades(exchange: ccxt.bitmex) -> list:
    try:
        return exchange.fetch_my_trades(SYMBOL, limit=TRADE_LIMIT)
    except Exception as e:
        return [{"error": str(e)}]


def _fetch_balance(exchange: ccxt.bitmex) -> dict:
    try:
        return exchange.fetch_balance()
    except Exception as e:
        return {"error": str(e)}


def main(return_data: bool = False):
    if not API_KEY or not API_SECRET:
        result = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "broker":     "BitMEX",
            "positions":  [],
            "trades":     [],
            "pnl":        {},
            "error":      "auth_failed: BITMEX_API_KEY or BITMEX_API_SECRET not set in config/.env",
        }
        if return_data:
            return result
        print(json.dumps(result, indent=2))
        return None

    exchange   = _build_exchange()
    fetched_at = datetime.now(timezone.utc).isoformat()

    raw_positions = _fetch_positions(exchange)
    raw_trades    = _fetch_trades(exchange)
    raw_balance   = _fetch_balance(exchange)

    # ── Normalise positions ────────────────────────────────────────────────────
    positions = []
    for p in raw_positions:
        if "error" in p:
            continue
        contracts  = p.get("contracts", 0) or 0
        entry      = p.get("entryPrice")
        mark       = p.get("markPrice")
        upnl       = p.get("unrealizedPnl")
        notional   = p.get("notional")
        upct       = round(upnl / abs(notional) * 100, 2) \
                     if (upnl is not None and notional) else None
        positions.append({
            "symbol":         p.get("symbol"),
            "broker":         "BitMEX",
            "strategy":       "Derivatives",
            "asset_class":    "Futures" if ":" in (p.get("symbol") or "") else "CFD",
            "direction":      "Long" if contracts > 0 else "Short",
            "quantity":       abs(contracts),
            "entry_price":    entry,
            "current_price":  mark,
            "market_value":   notional,
            "unrealised_pnl": upnl,
            "unrealised_pct": upct,
            "cost_basis":     None,
            "currency":       p.get("settleCurrency", "BTC"),
            "open_date":      None,
            "account":        "BitMEX",
            "last_synced":    fetched_at,
        })

    # ── Normalise trades ───────────────────────────────────────────────────────
    trades = []
    for t in raw_trades:
        if "error" in t:
            continue
        trades.append({
            "trade_id":     str(t.get("id") or ""),
            "broker":       "BitMEX",
            "symbol":       t.get("symbol"),
            "asset_class":  "Futures",
            "side":         "Buy" if t.get("side") == "buy" else "Sell",
            "quantity":     t.get("amount"),
            "price":        t.get("price"),
            "realised_pnl": t.get("info", {}).get("realisedPnl"),
            "commission":   t.get("fee", {}).get("cost"),
            "currency":     t.get("fee", {}).get("currency", "BTC"),
            "executed_at":  t.get("datetime", ""),
            "account":      "BitMEX",
        })

    # ── Balance / P&L ──────────────────────────────────────────────────────────
    XBT_TO_USD = None
    try:
        ticker     = exchange.fetch_ticker("BTC/USD:BTC")
        XBT_TO_USD = ticker.get("last")
    except Exception:
        pass

    btc_total = None
    btc_free  = None
    if "error" not in raw_balance:
        btc_total = raw_balance.get("total", {}).get("BTC") or \
                    raw_balance.get("total", {}).get("XBT")
        btc_free  = raw_balance.get("free", {}).get("BTC") or \
                    raw_balance.get("free", {}).get("XBT")

    net_liq_usd = round(btc_total * XBT_TO_USD, 2) \
                  if (btc_total and XBT_TO_USD) else None

    total_upnl = sum(
        p["unrealised_pnl"] for p in positions
        if p.get("unrealised_pnl") is not None
    ) or None

    pnl = {
        "btc_balance":    btc_total,
        "btc_available":  btc_free,
        "usd_equivalent": net_liq_usd,
        "unrealised_pnl": total_upnl,
        "btc_usd_rate":   XBT_TO_USD,
    }

    result = {
        "fetched_at":      fetched_at,
        "broker":          "BitMEX",
        "testnet":         TESTNET,
        "positions":       positions,
        "trades":          trades,
        "pnl":             pnl,
        "account_summary": raw_balance if "error" not in raw_balance else {},
        "error":           None,
    }

    if return_data:
        return result
    print(json.dumps(result, indent=2, default=str))
    return None


if __name__ == "__main__":
    main(return_data=False)
