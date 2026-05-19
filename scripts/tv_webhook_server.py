"""
tv_webhook_server.py
────────────────────
Tanulytics — TradingView webhook receiver for FXCM trade events.

Listens for POSTs from TradingView Pine Script alerts and appends each
event as a single JSON line to data/raw/tv_fxcm_events.jsonl. The
fxcm_fetch.py module reads that log and reconstructs positions + trades.

Why this exists:
    fxcmpy hasn't shipped since May 2024 and FXCM REST tokens are hard
    to obtain in 2026. TradingView is already the execution layer for
    your FXCM strategies, so it's the natural source of truth for
    FXCM portfolio events too. No FXCM token required, ever.

Run locally:
    python tv_webhook_server.py

    The server listens on 0.0.0.0:<port> (default 8787, override via
    FXCM_WEBHOOK_PORT in .env). For TradingView to reach it, expose
    the local port over HTTPS via cloudflared:

        cloudflared tunnel --url http://localhost:8787

    cloudflared prints a public HTTPS URL like
    https://<random>.trycloudflare.com. Append the webhook path:

        https://<random>.trycloudflare.com/fxcm-webhook/<SECRET>

    Paste that into your TradingView alert's webhook URL field.

Security:
    The webhook secret is the last URL path segment. Any request to
    a mismatched secret returns 401 and is logged. TradingView does
    not let you set custom HTTP headers on webhooks (as of 2026), so
    a URL-path shared secret is the standard pattern.

Pine Script alert payload (copy-paste into TradingView):
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

SECRET = os.getenv("FXCM_WEBHOOK_SECRET", "")
PORT   = int(os.getenv("FXCM_WEBHOOK_PORT", "8787"))
HOST   = os.getenv("FXCM_WEBHOOK_HOST", "0.0.0.0")

# Default data path matches run_all.py's layout: ROOT/data/raw/.
# ROOT = the directory that contains the scripts (config/), so its parent.
DATA_DIR = Path(os.getenv(
    "TANULYTICS_DATA_DIR",
    str(Path(__file__).resolve().parent.parent / "data" / "raw"),
))
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = DATA_DIR / "tv_fxcm_events.jsonl"

# ── Flask app ─────────────────────────────────────────────────────────────────

try:
    from flask import Flask, request, jsonify, abort
except ImportError:
    print("❌ flask not installed. Run: pip install flask")
    sys.exit(1)

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Liveness probe — useful for testing cloudflared tunnel + DNS."""
    return jsonify({
        "ok":         True,
        "log_file":   str(LOG_FILE),
        "secret_set": bool(SECRET),
        "time":       datetime.now(timezone.utc).isoformat(),
    })


@app.route("/fxcm-webhook/<secret>", methods=["POST"])
def fxcm_webhook(secret):
    """
    Receive a TradingView alert POST. Validates the URL-path secret,
    appends the payload to the JSONL log with a server-side timestamp.
    Returns 200 on success, 401 on bad secret, 400 on malformed body.
    """
    if not SECRET:
        # Server started without a configured secret — refuse all requests
        # so accidental exposure can't leak events.
        app.logger.error("FXCM_WEBHOOK_SECRET not set; rejecting all requests.")
        abort(503, description="Server misconfigured: no secret set.")

    if secret != SECRET:
        app.logger.warning(
            f"401 from {request.remote_addr} — bad secret "
            f"(got '{secret[:6]}…' of len {len(secret)})"
        )
        abort(401)

    # TradingView sometimes sends Content-Type: text/plain. Be lenient.
    raw_body = request.get_data(as_text=True) or ""
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        # Fall back to treating the body as an opaque string so we don't
        # lose data on misconfigured alerts.
        payload = {"_raw_string_body": raw_body}

    event = {
        "received_at":   datetime.now(timezone.utc).isoformat(),
        "remote_addr":   request.remote_addr,
        "user_agent":    request.headers.get("User-Agent", ""),
        **payload,
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")

    # Human-readable confirmation in the server's terminal.
    print(f"[{event['received_at']}] {payload.get('action', '?'):4s} "
          f"{payload.get('symbol', '?'):10s} "
          f"qty={payload.get('qty', '?'):>6} "
          f"px={payload.get('price', '?'):>10}")

    return jsonify({"ok": True, "logged_to": str(LOG_FILE)}), 200


@app.errorhandler(401)
def _401(e):
    return jsonify({"error": "unauthorized"}), 401

@app.errorhandler(503)
def _503(e):
    return jsonify({"error": str(e.description)}), 503


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not SECRET:
        print("⚠️  FXCM_WEBHOOK_SECRET is empty in .env — server will refuse")
        print("   all POSTs until you set one. Generate one with:")
        print("     python -c 'import secrets; print(secrets.token_urlsafe(32))'")
        print("   Then paste it into config/.env as FXCM_WEBHOOK_SECRET=...")
        print()

    print("=" * 60)
    print("  Tanulytics — TradingView FXCM webhook receiver")
    print(f"  Listening on:  http://{HOST}:{PORT}")
    print(f"  Webhook path:  /fxcm-webhook/<your-secret>")
    print(f"  Health check:  http://{HOST}:{PORT}/health")
    print(f"  Logging to:    {LOG_FILE}")
    print("=" * 60)
    print()
    # Disable Flask's reloader so the JSONL log isn't written to twice.
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
