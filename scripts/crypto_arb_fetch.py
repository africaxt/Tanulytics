"""
crypto_arb_fetch.py
────────────────────
Tanulytics — Crypto Arbitrage Signal Fetcher

Reads opportunity events logged by the africaxt/bitcoin-arbitrage
TanulyticsHook observer (data/raw/crypto_arb_events.jsonl) and returns
them in the standard Tanulytics broker schema.

Integration flow:
    bitcoin-arbitrage  →  TanulyticsHook observer
        → POST /crypto-arb-webhook/<secret>
        → tv_webhook_server.py appends to crypto_arb_events.jsonl
        → crypto_arb_fetch.py reads + reconstructs
        → aggregator.py normalises → Airtable / Notion
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "config" / ".env")
except ImportError:
    pass

ROOT       = Path(__file__).parent.parent
DATA_DIR   = ROOT / "data" / "raw"
EVENT_LOG  = DATA_DIR / "crypto_arb_events.jsonl"
LOOKBACK_H = int(os.getenv("CRYPTO_ARB_LOOKBACK_HOURS", "24"))


def _load_events(since: datetime) -> list:
    if not EVENT_LOG.exists():
        return []
    events = []
    with EVENT_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                ts_str = ev.get("received_at", "")
                # Python 3.10 fromisoformat rejects 'Z' suffix — normalise to +00:00.
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= since:
                    events.append(ev)
            except (json.JSONDecodeError, ValueError):
                continue
    return events


def main(return_data: bool = False):
    fetched_at = datetime.now(timezone.utc).isoformat()
    since      = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_H)
    events     = _load_events(since)

    if not events:
        result = {
            "fetched_at": fetched_at,
            "broker":     "CryptoArb",
            "positions":  [],
            "trades":     [],
            "pnl":        {},
            "error":      None if EVENT_LOG.exists() else
                          "No event log found — is africaxt/bitcoin-arbitrage running?",
        }
        if return_data:
            return result
        print(json.dumps(result, indent=2, default=str))
        return None

    # Each event is a detected opportunity. Represent as a pair of signals:
    # Buy on kask + Sell on kbid at the observed prices.
    total_profit = sum(ev.get("profit", 0) for ev in events)
    trades = []
    for ev in events:
        base = f"arb_{ev.get('buy_exchange')}_{ev.get('sell_exchange')}_{ev.get('received_at', '')}"
        for side, exchange, price_key in [
            ("Buy",  "buy_exchange",  "weighted_buy_price"),
            ("Sell", "sell_exchange", "weighted_sell_price"),
        ]:
            exchange_name = ev.get(exchange, "CryptoArb")
            trades.append({
                "trade_id":     f"{base}_{side.lower()}",
                "broker":       "CryptoArb",
                "symbol":       "BTC/USD",
                "asset_class":  "Crypto",
                "side":         side,
                "quantity":     ev.get("volume"),
                "price":        ev.get(price_key) or ev.get(price_key.replace("weighted_", "")),
                "realised_pnl": ev.get("profit") if side == "Sell" else None,
                "commission":   None,
                "currency":     "USD",
                "executed_at":  ev.get("received_at", ""),
                "account":      exchange_name,
                "meta": {
                    "profit":         ev.get("profit"),
                    "profit_pct":     ev.get("profit_pct"),
                    "buy_exchange":   ev.get("buy_exchange"),
                    "sell_exchange":  ev.get("sell_exchange"),
                },
            })

    result = {
        "fetched_at": fetched_at,
        "broker":     "CryptoArb",
        "positions":  [],
        "trades":     trades,
        "pnl": {
            "estimated_profit_period": round(total_profit, 4),
            "signal_count":            len(events),
            "lookback_hours":          LOOKBACK_H,
        },
        "error": None,
    }

    if return_data:
        return result
    print(json.dumps(result, indent=2, default=str))
    return None


if __name__ == "__main__":
    main(return_data=False)
