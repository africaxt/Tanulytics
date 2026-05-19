"""
aggregator.py
─────────────
Tanulytics Portfolio Aggregator — Normalisation Module

Takes raw data from all 4 broker fetchers and normalises it into a single
common schema so airtable_push.py and notion_summary.py can treat all
brokers uniformly.

Input shape (what run_all.py passes in):
    {
        "ibkr":      {fetched_at, broker, positions, trades, pnl, account_summary, ...},
        "fxcm":      {fetched_at, broker, positions, trades, pnl, ...},
        "schwab":    {fetched_at, broker, positions, trades, pnl, account_summary, ...},
        "robinhood": {fetched_at, broker, positions, trades, pnl, account_summary, ...},
    }

Output shape:
    {
        "positions": [...],   # normalised open positions
        "trades":    [...],   # normalised executed trades
        "balances":  [...],   # normalised account balances
        "summary":   {...},   # daily aggregate numbers
        "meta":      {...},   # run metadata
    }
"""

import hashlib
from datetime import datetime, timezone

# ── Strategy / Asset class lookups ─────────────────────────────────────────────

BROKER_STRATEGY = {
    "ibkr":       "Algorithmic",
    "fxcm":       "Forex",
    "schwab":     "Global Macro",
    "robinhood":  "Value Investing",
    "crypto_arb": "Crypto Arbitrage",
}

BROKER_CURRENCY = {
    "ibkr":       "USD",
    "fxcm":       "USD",
    "schwab":     "USD",
    "robinhood":  "USD",
    "crypto_arb": "USD",
}

# IBKR secType → normalised asset class
IBKR_SEC_TYPE = {
    "STK":  "Equity",
    "FUT":  "Futures",
    "CASH": "Forex",
    "OPT":  "Options",
    "CFD":  "CFD",
    "IND":  "Index",
    "FOP":  "Options",
    "WAR":  "Warrant",
    "BOND": "Fixed Income",
    "FUND": "ETF",
}

# Schwab assetType → normalised asset class
SCHWAB_ASSET_TYPE = {
    "EQUITY":        "Equity",
    "OPTION":        "Options",
    "INDEX":         "Index",
    "MUTUAL_FUND":   "ETF",
    "CASH_EQUIVALENT": "Cash",
    "FIXED_INCOME":  "Fixed Income",
    "CURRENCY":      "Forex",
    "COLLECTIVE_INVESTMENT": "ETF",
}

# Robinhood type → normalised asset class
ROBINHOOD_ASSET_TYPE = {
    "stock":  "Equity",
    "etp":    "ETF",
    "option": "Options",
    "crypto": "Crypto",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _safe_float(v, default=None):
    if v is None:
        return default
    try:
        f = float(v)
        return None if (f != f) else f   # nan → None
    except (TypeError, ValueError):
        return default


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _dedup_key(*parts):
    """Stable hash of concatenated string parts — used as trade_id."""
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Per-broker position normalisers ────────────────────────────────────────────

def _norm_ibkr_positions(positions: list, fetched_at: str) -> list:
    out = []
    for p in positions:
        qty = _safe_float(p.get("quantity"), 0.0)
        if qty == 0:
            continue
        avg   = _safe_float(p.get("avg_cost"))
        mval  = _safe_float(p.get("mkt_value"))
        upnl  = _safe_float(p.get("unrealised_pnl"))
        upct  = round(upnl / (avg * abs(qty)) * 100, 2) \
                if (upnl is not None and avg and avg != 0 and qty != 0) else None
        out.append({
            "symbol":         p.get("symbol"),
            "broker":         "IBKR",
            "strategy":       "Algorithmic",
            "asset_class":    IBKR_SEC_TYPE.get(p.get("sec_type", ""), p.get("sec_type", "Unknown")),
            "direction":      "Long" if qty > 0 else "Short",
            "quantity":       abs(qty),
            "entry_price":    avg,
            "current_price":  _safe_float(p.get("mkt_price")),
            "market_value":   mval,
            "unrealised_pnl": upnl,
            "unrealised_pct": upct,
            "cost_basis":     round(avg * abs(qty), 4) if avg else None,
            "currency":       p.get("currency", "USD"),
            "open_date":      None,   # IBKR fills() doesn't return open date
            "account":        p.get("account"),
            "last_synced":    fetched_at,
        })
    return out


def _norm_fxcm_positions(positions: list, fetched_at: str) -> list:
    out = []
    for p in positions:
        qty = _safe_float(p.get("qty"), 0.0)
        if qty == 0:
            continue
        out.append({
            "symbol":         p.get("symbol"),
            "broker":         "FXCM",
            "strategy":       "Forex",
            "asset_class":    "Forex",
            "direction":      "Long" if p.get("side") == "long" else "Short",
            "quantity":       qty,
            "entry_price":    _safe_float(p.get("entry_price")),
            "current_price":  None,   # No live feed from webhooks
            "market_value":   None,
            "unrealised_pnl": None,
            "unrealised_pct": None,
            "cost_basis":     None,
            "currency":       "USD",
            "open_date":      p.get("opened_at"),
            "account":        "FXCM",
            "last_synced":    fetched_at,
        })
    return out


def _norm_schwab_positions(positions: list, fetched_at: str) -> list:
    out = []
    for p in positions:
        long_qty  = _safe_float(p.get("long_quantity"), 0.0)
        short_qty = _safe_float(p.get("short_quantity"), 0.0)
        qty       = long_qty if long_qty else short_qty
        if not qty:
            continue
        direction = "Long" if long_qty else "Short"
        avg       = _safe_float(p.get("average_price"))
        mval      = _safe_float(p.get("market_value"))
        raw_pnl   = _safe_float(p.get("long_open_pnl")) or _safe_float(p.get("short_open_pnl"))
        upct      = round(raw_pnl / (avg * qty) * 100, 2) \
                    if (raw_pnl is not None and avg and qty) else None
        out.append({
            "symbol":         p.get("symbol"),
            "broker":         "Schwab",
            "strategy":       "Global Macro",
            "asset_class":    SCHWAB_ASSET_TYPE.get(p.get("asset_type", ""), p.get("asset_type", "Unknown")),
            "direction":      direction,
            "quantity":       qty,
            "entry_price":    avg,
            "current_price":  round(mval / qty, 4) if (mval and qty) else None,
            "market_value":   mval,
            "unrealised_pnl": raw_pnl,
            "unrealised_pct": upct,
            "cost_basis":     round(avg * qty, 4) if avg else None,
            "currency":       "USD",
            "open_date":      None,
            "account":        str(p.get("account", ""))[-4:],
            "last_synced":    fetched_at,
        })
    return out


def _norm_robinhood_positions(positions: list, fetched_at: str) -> list:
    out = []
    for p in positions:
        qty = _safe_float(p.get("quantity"), 0.0)
        if not qty:
            continue
        avg   = _safe_float(p.get("average_buy_price"))
        mval  = _safe_float(p.get("equity"))
        upnl  = _safe_float(p.get("equity_change"))
        upct  = _safe_float(p.get("percent_change"))
        out.append({
            "symbol":         p.get("symbol"),
            "broker":         "Robinhood",
            "strategy":       "Value Investing",
            "asset_class":    ROBINHOOD_ASSET_TYPE.get(p.get("type", ""), "Equity"),
            "direction":      "Long",   # Robinhood does not support short selling
            "quantity":       qty,
            "entry_price":    avg,
            "current_price":  _safe_float(p.get("price")),
            "market_value":   mval,
            "unrealised_pnl": upnl,
            "unrealised_pct": upct,
            "cost_basis":     round(avg * qty, 4) if avg else None,
            "currency":       "USD",
            "open_date":      None,
            "account":        "Robinhood",
            "last_synced":    fetched_at,
        })
    return out


# ── Per-broker trade normalisers ───────────────────────────────────────────────

def _norm_ibkr_trades(trades: list) -> list:
    out = []
    for t in trades:
        out.append({
            "trade_id":     str(t.get("exec_id") or t.get("perm_id") or
                               _dedup_key("ibkr", t.get("symbol"), t.get("datetime"), t.get("price"))),
            "broker":       "IBKR",
            "symbol":       t.get("symbol"),
            "asset_class":  IBKR_SEC_TYPE.get(t.get("sec_type", ""), "Unknown"),
            "side":         "Buy" if (t.get("side") or "").upper() == "BOT" else "Sell",
            "quantity":     _safe_float(t.get("quantity")),
            "price":        _safe_float(t.get("price")),
            "realised_pnl": _safe_float(t.get("realised_pnl")),
            "commission":   _safe_float(t.get("commission")),
            "currency":     t.get("currency", "USD"),
            "executed_at":  str(t.get("datetime") or ""),
            "account":      t.get("account"),
        })
    return out


def _norm_fxcm_trades(trades: list) -> list:
    out = []
    for t in trades:
        action = (t.get("action") or "").lower()
        raw    = t.get("_raw", {})
        key    = _dedup_key("fxcm", t.get("symbol"), t.get("qty"), t.get("price"), t.get("alert_time"))
        out.append({
            "trade_id":     key,
            "broker":       "FXCM",
            "symbol":       t.get("symbol"),
            "asset_class":  "Forex",
            "side":         "Buy" if action.startswith("buy") else "Sell",
            "quantity":     _safe_float(t.get("qty")),
            "price":        _safe_float(t.get("price")),
            "realised_pnl": _safe_float(t.get("realized_pnl")),
            "commission":   None,
            "currency":     "USD",
            "executed_at":  str(t.get("alert_time") or t.get("received_at") or ""),
            "account":      "FXCM",
            "kind":         t.get("kind"),   # open / close — FXCM-specific
        })
    return out


def _norm_schwab_trades(trades: list) -> list:
    out = []
    for t in trades:
        out.append({
            "trade_id":     str(t.get("activity_id") or
                               _dedup_key("schwab", t.get("symbol"), t.get("time"), t.get("price"))),
            "broker":       "Schwab",
            "symbol":       t.get("symbol"),
            "asset_class":  SCHWAB_ASSET_TYPE.get(t.get("asset_type", ""), "Unknown"),
            "side":         "Buy" if _safe_float(t.get("amount"), 0) > 0 else "Sell",
            "quantity":     abs(_safe_float(t.get("amount"), 0)),
            "price":        _safe_float(t.get("price")),
            "realised_pnl": None,   # Schwab doesn't return P&L per trade
            "commission":   _safe_float(t.get("cost")),
            "currency":     "USD",
            "executed_at":  str(t.get("time") or t.get("trade_date") or ""),
            "account":      str(t.get("account", "")),
        })
    return out


def _norm_crypto_arb_trades(trades: list) -> list:
    out = []
    for t in trades:
        out.append({
            "trade_id":     t.get("trade_id") or _dedup_key(
                "crypto_arb", t.get("symbol"), t.get("executed_at"), t.get("price")),
            "broker":       "CryptoArb",
            "symbol":       t.get("symbol", "BTC/USD"),
            "asset_class":  "Crypto",
            "side":         t.get("side", "Buy"),
            "quantity":     _safe_float(t.get("quantity")),
            "price":        _safe_float(t.get("price")),
            "realised_pnl": _safe_float(t.get("realised_pnl")),
            "commission":   None,
            "currency":     "USD",
            "executed_at":  str(t.get("executed_at") or ""),
            "account":      t.get("account", "CryptoArb"),
        })
    return out


def _norm_robinhood_trades(trades: list) -> list:
    out = []
    for t in trades:
        eid = t.get("execution_id") or t.get("order_id")
        out.append({
            "trade_id":     str(eid) if eid else _dedup_key(
                "robinhood", t.get("symbol"), t.get("executed_at"), t.get("price")),
            "broker":       "Robinhood",
            "symbol":       t.get("symbol"),
            "asset_class":  ROBINHOOD_ASSET_TYPE.get(t.get("asset_type", ""), "Equity"),
            "side":         "Buy" if (t.get("side") or "").lower() == "buy" else "Sell",
            "quantity":     _safe_float(t.get("quantity")),
            "price":        _safe_float(t.get("price")),
            "realised_pnl": None,
            "commission":   _safe_float(t.get("fees")),
            "currency":     "USD",
            "executed_at":  str(t.get("executed_at") or t.get("created_at") or ""),
            "account":      "Robinhood",
        })
    return out


# ── Per-broker balance normalisers ─────────────────────────────────────────────

def _norm_ibkr_balance(broker_data: dict) -> list:
    summary = broker_data.get("account_summary", {})
    pnl     = broker_data.get("pnl", {})
    fa      = broker_data.get("fetched_at", _now_iso())

    def _tag(tag):
        v = summary.get(tag, {})
        return _safe_float(v.get("value")) if isinstance(v, dict) else None

    rows = []
    for acct, p in pnl.items():
        rows.append({
            "broker":         "IBKR",
            "account":        acct,
            "net_liq":        _tag("NetLiquidation"),
            "cash":           _tag("TotalCashValue"),
            "buying_power":   _tag("BuyingPower"),
            "daily_pnl":      _safe_float(p.get("daily_pnl")),
            "unrealised_pnl": _safe_float(p.get("unrealised_pnl")),
            "realised_pnl":   _safe_float(p.get("realised_pnl")),
            "equity":         _tag("GrossPositionValue"),
            "currency":       summary.get("Currency", {}).get("currency", "USD")
                              if isinstance(summary.get("Currency"), dict) else "USD",
            "as_of":          fa,
        })
    # If no P&L subscription data, still emit a balance row from account summary
    if not rows and summary:
        rows.append({
            "broker":         "IBKR",
            "account":        "IBKR",
            "net_liq":        _tag("NetLiquidation"),
            "cash":           _tag("TotalCashValue"),
            "buying_power":   _tag("BuyingPower"),
            "daily_pnl":      None,
            "unrealised_pnl": _tag("UnrealizedPnL"),
            "realised_pnl":   _tag("RealizedPnL"),
            "equity":         _tag("GrossPositionValue"),
            "currency":       "USD",
            "as_of":          fa,
        })
    return rows


def _norm_crypto_arb_balance(broker_data: dict) -> list:
    pnl = broker_data.get("pnl", {})
    fa  = broker_data.get("fetched_at", _now_iso())
    return [{
        "broker":         "CryptoArb",
        "account":        "bitcoin-arbitrage",
        "net_liq":        None,
        "cash":           None,
        "buying_power":   None,
        "daily_pnl":      _safe_float(pnl.get("estimated_profit_period")),
        "unrealised_pnl": None,
        "realised_pnl":   _safe_float(pnl.get("estimated_profit_period")),
        "equity":         None,
        "currency":       "USD",
        "as_of":          fa,
    }]


def _norm_fxcm_balance(broker_data: dict) -> list:
    pnl = broker_data.get("pnl", {})
    fa  = broker_data.get("fetched_at", _now_iso())
    return [{
        "broker":         "FXCM",
        "account":        "FXCM",
        "net_liq":        None,   # Not available from webhook log
        "cash":           None,
        "buying_power":   _safe_float(pnl.get("buying_power")),
        "daily_pnl":      None,
        "unrealised_pnl": _safe_float(pnl.get("unrealised_pnl")),
        "realised_pnl":   _safe_float(pnl.get("realized_pnl_all_time")),
        "equity":         None,
        "currency":       "USD",
        "as_of":          fa,
    }]


def _norm_schwab_balance(broker_data: dict) -> list:
    summary = broker_data.get("account_summary", {})
    pnl     = broker_data.get("pnl", {})
    fa      = broker_data.get("fetched_at", _now_iso())
    rows    = []
    for hash_id, entry in summary.items():
        sa      = entry.get("securitiesAccount", entry)
        bal     = sa.get("currentBalances", {}) or {}
        p       = pnl.get(hash_id, {})
        rows.append({
            "broker":         "Schwab",
            "account":        str(hash_id)[-4:],
            "net_liq":        _safe_float(bal.get("liquidationValue")),
            "cash":           _safe_float(bal.get("cashBalance")),
            "buying_power":   _safe_float(bal.get("buyingPower")),
            "daily_pnl":      _safe_float(p.get("daily_pnl")),
            "unrealised_pnl": _safe_float(p.get("long_open_pnl")),
            "realised_pnl":   None,
            "equity":         _safe_float(bal.get("equity")),
            "currency":       "USD",
            "as_of":          fa,
        })
    return rows


def _norm_robinhood_balance(broker_data: dict) -> list:
    summary  = broker_data.get("account_summary", {})
    pnl      = broker_data.get("pnl", {})
    fa       = broker_data.get("fetched_at", _now_iso())
    port     = summary.get("portfolio_profile", {}) or {}
    acct     = summary.get("account_profile", {}) or {}
    return [{
        "broker":         "Robinhood",
        "account":        "Robinhood",
        "net_liq":        _safe_float(port.get("equity")),
        "cash":           _safe_float(acct.get("cash")),
        "buying_power":   _safe_float(acct.get("buying_power")),
        "daily_pnl":      _safe_float(pnl.get("daily_pnl")),
        "unrealised_pnl": _safe_float(pnl.get("unrealised_pnl")),
        "realised_pnl":   None,
        "equity":         _safe_float(port.get("market_value")),
        "currency":       "USD",
        "as_of":          fa,
    }]


# ── Summary builder ────────────────────────────────────────────────────────────

def _build_summary(positions: list, trades: list, balances: list,
                   broker_data: dict) -> dict:
    synced  = list(broker_data.keys())
    failed  = [k for k, v in broker_data.items() if v.get("error")]
    ok      = [k for k in synced if k not in failed]

    total_daily_pnl    = None
    total_unrealised   = None
    total_net_liq      = None

    for b in balances:
        d = b.get("daily_pnl")
        u = b.get("unrealised_pnl")
        n = b.get("net_liq")
        if d is not None:
            total_daily_pnl = (total_daily_pnl or 0) + d
        if u is not None:
            total_unrealised = (total_unrealised or 0) + u
        if n is not None:
            total_net_liq = (total_net_liq or 0) + n

    return {
        "date":                  datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total_positions":       len(positions),
        "total_trades":          len(trades),
        "total_daily_pnl":       round(total_daily_pnl, 2)  if total_daily_pnl  is not None else None,
        "total_unrealised_pnl":  round(total_unrealised, 2) if total_unrealised is not None else None,
        "total_net_liq":         round(total_net_liq, 2)    if total_net_liq    is not None else None,
        "brokers_synced":        ok,
        "brokers_failed":        failed,
        "synced_at":             _now_iso(),
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def aggregate(broker_data: dict) -> dict:
    """
    Normalise raw broker data into a unified portfolio snapshot.

    Args:
        broker_data: dict keyed by broker name ("ibkr", "fxcm", "schwab",
                     "robinhood"). Each value is the dict returned by the
                     corresponding fetch script's main(return_data=True).

    Returns:
        dict with keys: positions, trades, balances, summary, meta.

    Design notes:
        · Brokers with an "error" key still pass through — their positions/
          trades/balances will be empty lists but the error is surfaced in
          summary.brokers_failed.
        · Trade deduplication is by trade_id (broker-native ID or a hash of
          stable fields). run_all.py relies on this to prevent double-inserts
          on repeated runs.
        · No enrichment (FX conversion, sector tags, etc.) is done here —
          that belongs in a separate enrichment step so this script stays fast.
    """
    positions = []
    trades    = []
    balances  = []

    NORM_POSITIONS = {
        "ibkr":       _norm_ibkr_positions,
        "fxcm":       _norm_fxcm_positions,
        "schwab":     _norm_schwab_positions,
        "robinhood":  _norm_robinhood_positions,
        "crypto_arb": lambda pos, fa: [],   # arb has no persistent positions
    }
    NORM_TRADES = {
        "ibkr":       _norm_ibkr_trades,
        "fxcm":       _norm_fxcm_trades,
        "schwab":     _norm_schwab_trades,
        "robinhood":  _norm_robinhood_trades,
        "crypto_arb": _norm_crypto_arb_trades,
    }
    NORM_BALANCES = {
        "ibkr":       _norm_ibkr_balance,
        "fxcm":       _norm_fxcm_balance,
        "schwab":     _norm_schwab_balance,
        "robinhood":  _norm_robinhood_balance,
        "crypto_arb": _norm_crypto_arb_balance,
    }

    for broker_key, data in broker_data.items():
        fa = data.get("fetched_at", _now_iso())

        # Positions
        norm_pos = NORM_POSITIONS.get(broker_key)
        if norm_pos:
            try:
                positions.extend(norm_pos(data.get("positions", []), fa))
            except Exception as e:
                print(f"  ⚠️  {broker_key} position normalisation failed: {e}")

        # Trades
        norm_tr = NORM_TRADES.get(broker_key)
        if norm_tr:
            try:
                trades.extend(norm_tr(data.get("trades", [])))
            except Exception as e:
                print(f"  ⚠️  {broker_key} trade normalisation failed: {e}")

        # Balances
        norm_bal = NORM_BALANCES.get(broker_key)
        if norm_bal:
            try:
                balances.extend(norm_bal(data))
            except Exception as e:
                print(f"  ⚠️  {broker_key} balance normalisation failed: {e}")

    # Deduplicate trades by trade_id (safety net for retried pipeline runs)
    seen_ids = set()
    unique_trades = []
    for t in trades:
        tid = t.get("trade_id")
        if tid and tid in seen_ids:
            continue
        seen_ids.add(tid)
        unique_trades.append(t)

    summary = _build_summary(positions, unique_trades, balances, broker_data)

    print(f"  Normalised: {len(positions)} positions, {len(unique_trades)} trades, "
          f"{len(balances)} balance rows")
    print(f"  Daily P&L: {summary['total_daily_pnl']}  "
          f"Unrealised: {summary['total_unrealised_pnl']}  "
          f"Net Liq: {summary['total_net_liq']}")

    return {
        "positions": positions,
        "trades":    unique_trades,
        "balances":  balances,
        "summary":   summary,
        "meta": {
            "aggregated_at":  _now_iso(),
            "brokers_in":     list(broker_data.keys()),
            "position_count": len(positions),
            "trade_count":    len(unique_trades),
            "balance_count":  len(balances),
        },
    }
