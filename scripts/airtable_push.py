"""
airtable_push.py
────────────────
Tanulytics Portfolio Aggregator — Airtable Module

Pushes normalised portfolio data from aggregator.py to Airtable.

Behaviour:
  · First run: creates the Tanulytics base and all 4 tables automatically.
  · Subsequent runs: upserts positions/balances, inserts new trades
    (deduplicated by trade_id so repeated pipeline runs are safe).

Tables created:
  1. Positions     — open positions across all brokers (upserted by symbol+broker)
  2. Balances      — daily account snapshots per broker (upserted by broker+account+date)
  3. Trade History — every executed trade (upserted by trade_id)
  4. Daily Summary — one row per pipeline run

Requirements:
  pip install pyairtable python-dotenv

Setup:
  1. Log in to airtable.com → click your avatar → Developer Hub → Personal access tokens
  2. Create a token with scopes: data.records:read, data.records:write,
     schema.bases:read, schema.bases:write
  3. Copy token → add to config/.env as AIRTABLE_API_KEY
  4. On first run this script creates a new base named "Tanulytics" in your
     default workspace. Copy the generated base ID → add to .env as AIRTABLE_BASE_ID
     so subsequent runs reuse the same base.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "config" / ".env")
except ImportError:
    pass

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")

# ── Table definitions ─────────────────────────────────────────────────────────

POSITIONS_FIELDS = [
    {"name": "Symbol",         "type": "singleLineText"},
    {"name": "Broker",         "type": "singleLineText"},
    {"name": "Strategy",       "type": "singleLineText"},
    {"name": "Asset Class",    "type": "singleLineText"},
    {"name": "Direction",      "type": "singleLineText"},
    {"name": "Quantity",       "type": "number",         "options": {"precision": 4}},
    {"name": "Entry Price",    "type": "currency",       "options": {"precision": 4, "symbol": "$"}},
    {"name": "Current Price",  "type": "currency",       "options": {"precision": 4, "symbol": "$"}},
    {"name": "Market Value",   "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Unrealised P&L", "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Unrealised %",   "type": "number",         "options": {"precision": 2}},
    {"name": "Cost Basis",     "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Currency",       "type": "singleLineText"},
    {"name": "Open Date",      "type": "singleLineText"},
    {"name": "Account",        "type": "singleLineText"},
    {"name": "Last Synced",    "type": "singleLineText"},
]

BALANCES_FIELDS = [
    {"name": "Broker",         "type": "singleLineText"},
    {"name": "Account",        "type": "singleLineText"},
    {"name": "Date",           "type": "singleLineText"},
    {"name": "Net Liq",        "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Cash",           "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Buying Power",   "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Daily P&L",      "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Unrealised P&L", "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Realised P&L",   "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Equity",         "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Currency",       "type": "singleLineText"},
    {"name": "As Of",          "type": "singleLineText"},
]

TRADES_FIELDS = [
    {"name": "Trade ID",       "type": "singleLineText"},
    {"name": "Broker",         "type": "singleLineText"},
    {"name": "Symbol",         "type": "singleLineText"},
    {"name": "Asset Class",    "type": "singleLineText"},
    {"name": "Side",           "type": "singleLineText"},
    {"name": "Quantity",       "type": "number",         "options": {"precision": 4}},
    {"name": "Price",          "type": "currency",       "options": {"precision": 4, "symbol": "$"}},
    {"name": "Realised P&L",   "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Commission",     "type": "currency",       "options": {"precision": 2, "symbol": "$"}},
    {"name": "Currency",       "type": "singleLineText"},
    {"name": "Executed At",    "type": "singleLineText"},
    {"name": "Account",        "type": "singleLineText"},
]

SUMMARY_FIELDS = [
    {"name": "Date",               "type": "singleLineText"},
    {"name": "Run At",             "type": "singleLineText"},
    {"name": "Total Positions",    "type": "number",   "options": {"precision": 0}},
    {"name": "Total Trades",       "type": "number",   "options": {"precision": 0}},
    {"name": "Daily P&L",          "type": "currency", "options": {"precision": 2, "symbol": "$"}},
    {"name": "Unrealised P&L",     "type": "currency", "options": {"precision": 2, "symbol": "$"}},
    {"name": "Net Liq",            "type": "currency", "options": {"precision": 2, "symbol": "$"}},
    {"name": "Brokers Synced",     "type": "singleLineText"},
    {"name": "Brokers Failed",     "type": "singleLineText"},
]

TABLE_SPECS = {
    "Positions":     POSITIONS_FIELDS,
    "Balances":      BALANCES_FIELDS,
    "Trade History": TRADES_FIELDS,
    "Daily Summary": SUMMARY_FIELDS,
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _check_deps():
    try:
        import pyairtable
        return True
    except ImportError:
        print("  ❌ pyairtable not installed. Run: pip install pyairtable")
        return False


def _clean(v):
    """Strip None values and empty strings from a record dict."""
    return {k: val for k, val in v.items() if val is not None and val != ""}


def _today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Base / table setup ────────────────────────────────────────────────────────

def _get_or_create_base(api):
    """
    Return the base ID to use. If AIRTABLE_BASE_ID is set in .env, use it.
    Otherwise create a new base named 'Tanulytics' and print the ID so the
    user can persist it in .env.
    """
    if AIRTABLE_BASE_ID and not AIRTABLE_BASE_ID.startswith("your_"):
        return AIRTABLE_BASE_ID

    # Create a new base (requires workspace ID — use the first available workspace)
    print("  ℹ️  AIRTABLE_BASE_ID not set — creating a new base 'Tanulytics'.")
    try:
        workspaces = api.workspaces()
        ws_id = workspaces[0].id if workspaces else None
        if not ws_id:
            raise ValueError("No Airtable workspace found. Create one at airtable.com first.")

        base = api.create_base(
            workspace_id=ws_id,
            name="Tanulytics",
            tables=[
                {"name": name, "fields": [
                    # Airtable requires at least one field in the create call;
                    # we pass the first field of each table.
                    {"name": fields[0]["name"], "type": fields[0]["type"]}
                ]}
                for name, fields in TABLE_SPECS.items()
            ],
        )
        new_id = base.id
        print(f"\n  ✅ Created Airtable base: {new_id}")
        print(f"     Add this to config/.env:  AIRTABLE_BASE_ID={new_id}\n")
        return new_id
    except Exception as e:
        raise RuntimeError(f"Could not create Airtable base: {e}") from e


def _ensure_tables(api, base_id: str) -> dict:
    """
    Return a dict of {table_name: Table} for all 4 tables.
    Creates any table that doesn't already exist, and adds any missing fields
    to tables that do exist.
    """
    from pyairtable import Api

    schema = api.base(base_id).schema()
    existing = {t.name: t for t in schema.tables}

    table_ids = {}
    for table_name, field_specs in TABLE_SPECS.items():
        if table_name not in existing:
            print(f"  Creating table '{table_name}'...")
            tbl = api.base(base_id).create_table(
                name=table_name,
                fields=field_specs,
            )
            table_ids[table_name] = tbl.id
        else:
            tbl = existing[table_name]
            table_ids[table_name] = tbl.id
            # Add any missing fields
            existing_field_names = {f.name for f in tbl.fields}
            for fspec in field_specs:
                if fspec["name"] not in existing_field_names:
                    print(f"  Adding field '{fspec['name']}' to '{table_name}'...")
                    try:
                        api.base(base_id).table(tbl.id).create_field(
                            name=fspec["name"],
                            field_type=fspec["type"],
                            options=fspec.get("options"),
                        )
                    except Exception as e:
                        print(f"  ⚠️  Could not add field '{fspec['name']}': {e}")

    return table_ids


# ── Upsert helpers ────────────────────────────────────────────────────────────

def _upsert_records(table, records: list, key_fields: list):
    """
    Upsert records using pyairtable's upsert() method.
    key_fields: list of field names that together form the unique key.

    Airtable's upsert endpoint handles create + update in one call.
    Batches automatically to respect the 10-record-per-request limit.
    """
    if not records:
        return 0

    created = 0
    updated = 0
    # pyairtable upsert() accepts key_fields as a parameter
    result = table.upsert(records, key_fields=key_fields)
    for r in result:
        if r.get("createdTime"):
            created += 1
        else:
            updated += 1
    return len(records)


def _batch_create(table, records: list) -> int:
    """Insert records in batches of 10. Returns count inserted."""
    if not records:
        return 0
    total = 0
    for i in range(0, len(records), 10):
        batch = records[i:i+10]
        table.batch_create(batch)
        total += len(batch)
    return total


# ── Record builders ───────────────────────────────────────────────────────────

def _position_record(p: dict) -> dict:
    return _clean({
        "Symbol":         p.get("symbol"),
        "Broker":         p.get("broker"),
        "Strategy":       p.get("strategy"),
        "Asset Class":    p.get("asset_class"),
        "Direction":      p.get("direction"),
        "Quantity":       p.get("quantity"),
        "Entry Price":    p.get("entry_price"),
        "Current Price":  p.get("current_price"),
        "Market Value":   p.get("market_value"),
        "Unrealised P&L": p.get("unrealised_pnl"),
        "Unrealised %":   p.get("unrealised_pct"),
        "Cost Basis":     p.get("cost_basis"),
        "Currency":       p.get("currency", "USD"),
        "Open Date":      p.get("open_date"),
        "Account":        p.get("account"),
        "Last Synced":    p.get("last_synced"),
    })


def _balance_record(b: dict) -> dict:
    return _clean({
        "Broker":         b.get("broker"),
        "Account":        b.get("account"),
        "Date":           _today(),
        "Net Liq":        b.get("net_liq"),
        "Cash":           b.get("cash"),
        "Buying Power":   b.get("buying_power"),
        "Daily P&L":      b.get("daily_pnl"),
        "Unrealised P&L": b.get("unrealised_pnl"),
        "Realised P&L":   b.get("realised_pnl"),
        "Equity":         b.get("equity"),
        "Currency":       b.get("currency", "USD"),
        "As Of":          b.get("as_of"),
    })


def _trade_record(t: dict) -> dict:
    return _clean({
        "Trade ID":     t.get("trade_id"),
        "Broker":       t.get("broker"),
        "Symbol":       t.get("symbol"),
        "Asset Class":  t.get("asset_class"),
        "Side":         t.get("side"),
        "Quantity":     t.get("quantity"),
        "Price":        t.get("price"),
        "Realised P&L": t.get("realised_pnl"),
        "Commission":   t.get("commission"),
        "Currency":     t.get("currency", "USD"),
        "Executed At":  t.get("executed_at"),
        "Account":      t.get("account"),
    })


def _summary_record(s: dict) -> dict:
    return _clean({
        "Date":             s.get("date"),
        "Run At":           s.get("synced_at"),
        "Total Positions":  s.get("total_positions"),
        "Total Trades":     s.get("total_trades"),
        "Daily P&L":        s.get("total_daily_pnl"),
        "Unrealised P&L":   s.get("total_unrealised_pnl"),
        "Net Liq":          s.get("total_net_liq"),
        "Brokers Synced":   ", ".join(s.get("brokers_synced", [])),
        "Brokers Failed":   ", ".join(s.get("brokers_failed", [])),
    })


# ── Main entry point ──────────────────────────────────────────────────────────

def push(combined_data: dict) -> dict:
    """
    Push normalised portfolio data to Airtable.

    Args:
        combined_data: dict returned by aggregator.aggregate().

    Returns:
        dict with counts: positions_upserted, balances_upserted,
        trades_inserted, summary_inserted.

    Raises:
        RuntimeError: if Airtable credentials are missing or the API call fails
        in a way that can't be recovered from.
    """
    if not _check_deps():
        raise RuntimeError("pyairtable not installed.")

    if not AIRTABLE_API_KEY or AIRTABLE_API_KEY.startswith("your_"):
        raise RuntimeError(
            "AIRTABLE_API_KEY not set. "
            "Add it to config/.env — see the module docstring for setup instructions."
        )

    from pyairtable import Api

    print("  Connecting to Airtable...")
    api     = Api(AIRTABLE_API_KEY)
    base_id = _get_or_create_base(api)
    print(f"  Base ID: {base_id}")

    # Ensure all tables and fields exist
    table_ids = _ensure_tables(api, base_id)

    positions  = combined_data.get("positions", [])
    balances   = combined_data.get("balances", [])
    trades     = combined_data.get("trades", [])
    summary    = combined_data.get("summary", {})

    results = {
        "positions_upserted": 0,
        "balances_upserted":  0,
        "trades_inserted":    0,
        "summary_inserted":   0,
    }

    # ── Positions (upsert by Symbol + Broker) ──────────────────────────────────
    print(f"  Upserting {len(positions)} positions...")
    if positions:
        pos_table = api.base(base_id).table(table_ids["Positions"])
        pos_records = [_position_record(p) for p in positions]
        try:
            pos_table.upsert(pos_records, key_fields=["Symbol", "Broker"])
            results["positions_upserted"] = len(pos_records)
        except Exception as e:
            print(f"  ⚠️  Positions upsert failed: {e}")

    # ── Balances (upsert by Broker + Account + Date) ───────────────────────────
    print(f"  Upserting {len(balances)} balance rows...")
    if balances:
        bal_table = api.base(base_id).table(table_ids["Balances"])
        bal_records = [_balance_record(b) for b in balances]
        try:
            bal_table.upsert(bal_records, key_fields=["Broker", "Account", "Date"])
            results["balances_upserted"] = len(bal_records)
        except Exception as e:
            print(f"  ⚠️  Balances upsert failed: {e}")

    # ── Trades (upsert by Trade ID — safe for repeated runs) ──────────────────
    print(f"  Inserting {len(trades)} trades (deduplicated by Trade ID)...")
    if trades:
        tr_table    = api.base(base_id).table(table_ids["Trade History"])
        tr_records  = [_trade_record(t) for t in trades if t.get("trade_id")]
        try:
            tr_table.upsert(tr_records, key_fields=["Trade ID"])
            results["trades_inserted"] = len(tr_records)
        except Exception as e:
            print(f"  ⚠️  Trades upsert failed: {e}")

    # ── Daily Summary (always insert a new row per run) ────────────────────────
    print("  Writing daily summary...")
    if summary:
        sum_table = api.base(base_id).table(table_ids["Daily Summary"])
        try:
            sum_table.create(_summary_record(summary))
            results["summary_inserted"] = 1
        except Exception as e:
            print(f"  ⚠️  Daily summary insert failed: {e}")

    print(f"  ✅ Airtable push complete: "
          f"{results['positions_upserted']} positions, "
          f"{results['trades_inserted']} trades, "
          f"{results['balances_upserted']} balances, "
          f"{results['summary_inserted']} summary row")

    return results
