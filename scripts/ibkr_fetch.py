"""
ibkr_fetch.py
─────────────
Tanulytics Portfolio Aggregator — IBKR Module
Fetches positions, account balances, and trade history from Interactive Brokers.

Requirements:
    pip install ib_async pandas

TWS/Gateway setup:
    Edit → Global Configuration → API → Settings
    ✅ Enable ActiveX and Socket Clients
    ✅ Read-Only API
    ✅ Download open orders on connection
    Trusted IPs: 127.0.0.1

Usage:
    python ibkr_fetch.py

Output:
    Prints raw data to console so you can inspect exactly what IBKR returns
    before we design the Airtable schema around it.
"""

import asyncio
import json
from datetime import datetime, timedelta
from ib_async import IB, util

# ── Config ────────────────────────────────────────────────────────────────────

PORTS_TO_TRY = [7497, 4001]   # TWS first, IB Gateway fallback
CLIENT_ID    = 99              # Unique client ID — change if 99 is already in use
TIMEOUT      = 10              # Seconds to wait for connection
READ_ONLY    = True            # Safety flag — never place orders from this script

# ── Connection ────────────────────────────────────────────────────────────────

def connect(ib: IB) -> bool:
    """Try TWS port then IB Gateway port. Return True if connected."""
    for port in PORTS_TO_TRY:
        try:
            print(f"  Trying port {port}...", end=" ")
            ib.connect(
                host="127.0.0.1",
                port=port,
                clientId=CLIENT_ID,
                readonly=READ_ONLY,
                timeout=TIMEOUT,
            )
            print(f"✅ Connected on port {port}")
            return True
        except Exception as e:
            print(f"❌ Failed ({e})")
    return False


# ── Fetch functions ───────────────────────────────────────────────────────────

def fetch_account_summary(ib: IB) -> dict:
    """Pull key account-level values: NLV, cash, buying power, P&L."""
    print("\n── Account summary ──────────────────────────────────────")
    summary = ib.accountSummary()
    
    # Group by tag for easy reading
    data = {}
    for item in summary:
        data[item.tag] = {
            "value":    item.value,
            "currency": item.currency,
            "account":  item.account,
        }
    
    # Print the tags most relevant to our schema
    key_tags = [
        "NetLiquidation",
        "TotalCashValue",
        "BuyingPower",
        "GrossPositionValue",
        "UnrealizedPnL",
        "RealizedPnL",
        "MaintMarginReq",
        "AvailableFunds",
        "Currency",
    ]
    for tag in key_tags:
        if tag in data:
            item = data[tag]
            print(f"  {tag:30s} {item['value']:>15s}  {item['currency']}")

    return data


def fetch_positions(ib: IB) -> list:
    """Pull all open positions with P&L."""
    print("\n── Open positions ───────────────────────────────────────")
    positions = ib.positions()
    
    if not positions:
        print("  No open positions found.")
        return []

    rows = []
    for pos in positions:
        contract  = pos.contract
        avg_cost  = pos.avgCost
        qty       = pos.position
        mkt_price = None
        mkt_value = None
        unreal_pnl = None

        # Request market price for the contract
        try:
            ticker = ib.reqMktData(contract, "", True, False)
            ib.sleep(2)  # Allow time for data to arrive
            mkt_price  = ticker.marketPrice()
            mkt_value  = round(mkt_price * qty, 2) if mkt_price else None
            unreal_pnl = round(mkt_value - (avg_cost * qty), 2) if mkt_value else None
        except Exception:
            pass

        row = {
            "symbol":       contract.symbol,
            "sec_type":     contract.secType,      # STK / FUT / CASH / OPT etc.
            "currency":     contract.currency,
            "exchange":     contract.exchange,
            "quantity":     qty,
            "avg_cost":     avg_cost,
            "mkt_price":    mkt_price,
            "mkt_value":    mkt_value,
            "unrealised_pnl": unreal_pnl,
            "account":      pos.account,
        }
        rows.append(row)

        print(
            f"  {contract.symbol:10s} {contract.secType:5s} "
            f"qty={qty:>10.2f}  avg={avg_cost:>10.4f}  "
            f"mkt={str(mkt_price):>10}  upnl={str(unreal_pnl):>12}"
        )

    return rows


def fetch_trade_history(ib: IB, days_back: int = 30) -> list:
    """Pull completed trades from the last N days via Flex Query fallback."""
    print(f"\n── Trade history (last {days_back} days) ────────────────────")

    # Method 1: executions() — returns today's fills in the current session
    fills = ib.fills()
    rows  = []

    if fills:
        for fill in fills:
            contract   = fill.contract
            execution  = fill.execution
            commission = fill.commissionReport

            row = {
                "exec_id":        execution.execId,
                "datetime":       execution.time,
                "symbol":         contract.symbol,
                "sec_type":       contract.secType,
                "currency":       contract.currency,
                "side":           execution.side,      # BOT / SLD
                "quantity":       execution.shares,
                "price":          execution.price,
                "commission":     commission.commission if commission else None,
                "realised_pnl":   commission.realizedPNL if commission else None,
                "account":        execution.acctNumber,
                "order_id":       execution.orderId,
                "perm_id":        execution.permId,
            }
            rows.append(row)
            print(
                f"  {execution.time}  {contract.symbol:8s} {execution.side:4s} "
                f"qty={execution.shares}  px={execution.price}  "
                f"comm={commission.commission if commission else 'N/A'}"
            )
    else:
        print("  No fills found in current session.")
        print("  Note: For historical trades beyond today, use IBKR Flex Query.")
        print("  → Reports → Flex Queries → Activity Flex Query")
        print("  → Export as CSV, then load with pandas in Phase 2.")

    return rows


def fetch_pnl(ib: IB) -> dict:
    """Request real-time P&L subscription for the account."""
    print("\n── Real-time P&L ─────────────────────────────────────────")
    accounts = ib.managedAccounts()
    
    pnl_data = {}
    for account in accounts:
        try:
            pnl = ib.reqPnL(account)
            ib.sleep(1)
            pnl_data[account] = {
                "daily_pnl":      pnl.dailyPnL,
                "unrealised_pnl": pnl.unrealizedPnL,
                "realised_pnl":   pnl.realizedPnL,
            }
            print(f"  Account: {account}")
            print(f"    Daily P&L:      {pnl.dailyPnL}")
            print(f"    Unrealised P&L: {pnl.unrealizedPnL}")
            print(f"    Realised P&L:   {pnl.realizedPnL}")
        except Exception as e:
            print(f"  P&L request failed for {account}: {e}")

    return pnl_data


# ── Main ──────────────────────────────────────────────────────────────────────

def main(return_data: bool = False):
    """
    Fetch all IBKR data.

    Args:
        return_data: If True, return the output dict instead of writing it to a
                     timestamped JSON file. run_all.py sets this to True so the
                     master pipeline can own raw-data persistence in /data/raw/.

    Returns:
        dict with keys: fetched_at, broker, account_summary, account_summary_tags,
        position_fields, trade_fields, positions, trades, pnl.
        On connection failure, returns a dict with an "error" key (so callers
        can safely .get("positions", []) without AttributeError).
    """
    print("=" * 60)
    print("  Tanulytics — IBKR Data Fetch")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("\n── Connecting to TWS/Gateway ────────────────────────────")

    ib = IB()

    if not connect(ib):
        print("\n❌ Could not connect to TWS or IB Gateway.")
        print("   Make sure TWS is open and API access is enabled:")
        print("   Edit → Global Configuration → API → Settings")
        return {
            "fetched_at": datetime.now().isoformat(),
            "broker":     "IBKR",
            "error":      "connection_failed",
            "positions":  [],
            "trades":     [],
            "pnl":        {},
        }

    try:
        # Pull all data
        account_data   = fetch_account_summary(ib)
        position_data  = fetch_positions(ib)
        trade_data     = fetch_trade_history(ib)
        pnl_data       = fetch_pnl(ib)

        # ── Summary output ────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  Raw data summary")
        print("=" * 60)
        print(f"  Account fields returned:  {len(account_data)}")
        print(f"  Open positions:           {len(position_data)}")
        print(f"  Trades (today):           {len(trade_data)}")
        print(f"  P&L accounts:             {len(pnl_data)}")

        # ── Build output dict ─────────────────────────────────────
        output = {
            "fetched_at": datetime.now().isoformat(),
            "broker":     "IBKR",
            "account_summary_tags": list(account_data.keys()),
            "position_fields":      list(position_data[0].keys()) if position_data else [],
            "trade_fields":         list(trade_data[0].keys()) if trade_data else [],
            "account_summary":      account_data,
            "positions":            position_data,
            "trades":               trade_data,
            "pnl":                  pnl_data,
        }

        # When called from run_all.py, hand the dict back so the master
        # pipeline can persist it in /data/raw/ alongside the other brokers.
        # When run directly, write a local timestamped JSON for inspection.
        if return_data:
            return output

        outfile = f"ibkr_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(outfile, "w") as f:
            json.dump(output, f, indent=2, default=str)

        print(f"\n  Raw data saved to: {outfile}")
        print("  Share this file and we'll design the Airtable schema")
        print("  around exactly what IBKR returns.\n")
        return output

    finally:
        ib.disconnect()
        print("  Disconnected from TWS/Gateway.")


if __name__ == "__main__":
    util.startLoop()
    main()
