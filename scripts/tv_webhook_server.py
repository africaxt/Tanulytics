"""
tv_webhook_server.py
────────────────────
Tanulytics — Unified webhook receiver.

Handles two signal sources on the same Flask process:

  /fxcm-webhook/<secret>       TradingView Pine Script → FXCM trade events
                                → data/raw/tv_fxcm_events.jsonl

  /crypto-arb-webhook/<secret> africaxt/bitcoin-arbitrage TanulyticsHook
                                observer → arbitrage opportunity signals
                                → data/raw/crypto_arb_events.jsonl

Why /fxcm-webhook exists:
    fxcmpy hasn't shipped since May 2024 and FXCM REST tokens are hard
    to obtain in 2026. TradingView is already the execution layer for
    your FXCM strategies, so it's the natural source of truth for
    FXCM portfolio events too. No FXCM token required, ever.

Run locally:
    python tv_webhook_server.py

    The server listens on 0.0.0.0:<port> (default 8787, override via
    FXCM_WEBHOOK_PORT in .env). Expose over HTTPS via cloudflared:

        cloudflared tunnel --url http://localhost:8787

    Then set the public URL in:
      - TradingView alert → Webhook URL: https://<host>/fxcm-webhook/<SECRET>
      - bitcoin-arbitrage config/.env → TANULYTICS_WEBHOOK_URL=https://<host>/crypto-arb-webhook
                                        TANULYTICS_WEBHOOK_SECRET=<CRYPTO_ARB_WEBHOOK_SECRET>

Security:
    Each endpoint has its own secret in the URL path. Mismatched secrets
    return 401. TradingView does not support custom HTTP headers on
    webhooks (as of 2026), so URL-path secrets are the standard pattern.

Pine Script alert payload:
    {
      "secret_check": "ok",
      "action":      "{{strategy.order.action}}",
      "symbol":      "{{ticker}}",
      "qty":         "{{strategy.order.contracts}}",
      "price":       "{{close}}",
      "alert_time":  "{{timenow}}",
      "strategy":    "{{strategy.order.alert_message}}",
      "comment":     "{{strategy.order.comment}}"
    }

Dependencies:
    pip install flask python-dotenv
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Config & paths ────────────────────────────────────────────────────────────

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "config" / ".env")
except ImportError:
    pass

FXCM_SECRET     = os.getenv("FXCM_WEBHOOK_SECRET", "")
CRYPTO_SECRET   = os.getenv("CRYPTO_ARB_WEBHOOK_SECRET", "")
PORT            = int(os.getenv("FXCM_WEBHOOK_PORT", "8787"))
HOST            = os.getenv("FXCM_WEBHOOK_HOST", "0.0.0.0")

DATA_DIR = Path(os.getenv(
    "TANULYTICS_DATA_DIR",
    str(Path(__file__).resolve().parent.parent / "data" / "raw"),
))
DATA_DIR.mkdir(parents=True, exist_ok=True)
FXCM_LOG        = DATA_DIR / "tv_fxcm_events.jsonl"
CRYPTO_ARB_LOG  = DATA_DIR / "crypto_arb_events.jsonl"

# ── Flask app ─────────────────────────────────────────────────────────────────

try:
    from flask import Flask, request, jsonify, abort
except ImportError:
    print("❌ flask not installed. Run: pip install flask")
    sys.exit(1)

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok":                True,
        "fxcm_log":          str(FXCM_LOG),
        "crypto_arb_log":    str(CRYPTO_ARB_LOG),
        "fxcm_secret_set":   bool(FXCM_SECRET),
        "crypto_secret_set": bool(CRYPTO_SECRET),
        "time":              datetime.now(timezone.utc).isoformat(),
    })


def _write_event(log_file: Path, payload: dict, source: str) -> dict:
    event = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "remote_addr": request.remote_addr,
        "source":      source,
        **payload,
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")
    return event


@app.route("/fxcm-webhook/<secret>", methods=["POST"])
def fxcm_webhook(secret):
    if not FXCM_SECRET:
        app.logger.error("FXCM_WEBHOOK_SECRET not set; rejecting all requests.")
        abort(503, description="Server misconfigured: FXCM secret not set.")
    if secret != FXCM_SECRET:
        app.logger.warning(f"401 fxcm from {request.remote_addr}")
        abort(401)

    raw_body = request.get_data(as_text=True) or ""
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        payload = {"_raw_string_body": raw_body}

    event = _write_event(FXCM_LOG, payload, "tradingview")
    print(f"[FXCM {event['received_at']}] {payload.get('action','?'):4s} "
          f"{payload.get('symbol','?'):10s} qty={payload.get('qty','?'):>6} "
          f"px={payload.get('price','?'):>10}")
    return jsonify({"ok": True, "logged_to": str(FXCM_LOG)}), 200


@app.route("/crypto-arb-webhook/<secret>", methods=["POST"])
def crypto_arb_webhook(secret):
    """
    Receives arbitrage opportunity signals from africaxt/bitcoin-arbitrage
    via the TanulyticsHook observer. Set CRYPTO_ARB_WEBHOOK_SECRET in .env
    and point bitcoin-arbitrage's TANULYTICS_WEBHOOK_SECRET at the same value.
    """
    if not CRYPTO_SECRET:
        app.logger.error("CRYPTO_ARB_WEBHOOK_SECRET not set; rejecting all requests.")
        abort(503, description="Server misconfigured: crypto secret not set.")
    if secret != CRYPTO_SECRET:
        app.logger.warning(f"401 crypto-arb from {request.remote_addr}")
        abort(401)

    raw_body = request.get_data(as_text=True) or ""
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        payload = {"_raw_string_body": raw_body}

    event = _write_event(CRYPTO_ARB_LOG, payload, "bitcoin-arbitrage")
    profit  = payload.get("profit", "?")
    buy_ex  = payload.get("buy_exchange", "?")
    sell_ex = payload.get("sell_exchange", "?")
    vol     = payload.get("volume", "?")
    print(f"[ARB  {event['received_at']}] {buy_ex}→{sell_ex:10s} "
          f"vol={vol!s:>8} profit={profit!s:>8}")
    return jsonify({"ok": True, "logged_to": str(CRYPTO_ARB_LOG)}), 200


@app.errorhandler(401)
def _401(e):
    return jsonify({"error": "unauthorized"}), 401

@app.errorhandler(503)
def _503(e):
    return jsonify({"error": str(e.description)}), 503


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _gen = "python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    if not FXCM_SECRET:
        print(f"  FXCM_WEBHOOK_SECRET not set — generate one: {_gen}")
    if not CRYPTO_SECRET:
        print(f"  CRYPTO_ARB_WEBHOOK_SECRET not set — generate one: {_gen}")

    print("=" * 60)
    print("  Tanulytics — Unified webhook receiver")
    print(f"  Listening on:     http://{HOST}:{PORT}")
    print(f"  FXCM path:        /fxcm-webhook/<FXCM_WEBHOOK_SECRET>")
    print(f"  Crypto arb path:  /crypto-arb-webhook/<CRYPTO_ARB_WEBHOOK_SECRET>")
    print(f"  Health check:     http://{HOST}:{PORT}/health")
    print(f"  FXCM log:         {FXCM_LOG}")
    print(f"  Crypto arb log:   {CRYPTO_ARB_LOG}")
    print("=" * 60)
    print()
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
