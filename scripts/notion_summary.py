"""
notion_summary.py
─────────────────
Tanulytics Portfolio Aggregator — Notion Module

Pushes the daily portfolio summary to two Notion destinations:

  1. Portfolio page  (NOTION_PORTFOLIO_PAGE_ID in config/.env)
     Appends a dated callout block with P&L, position count, and broker
     breakdown.  This is the investor-reportable / external view.

  2. Daily Review database  (NOTION_DAILY_REVIEW_DB_ID in config/.env)
     Finds today's entry and appends a "Market Context" paragraph so it
     is ready for the morning "Good morning, check-in" Claude session.
     If no entry exists yet, creates one.
     Does NOT fall back to the Mindset Stack root (that page is for
     habits, not market data).

System of record
────────────────
  Airtable          Full structured data — positions, trades, balances
  Notion Portfolio  Daily P&L callout block (external/reporting layer)
  Notion DailyRev   One-line market context for morning check-in
  Obsidian journal  Headline metrics + YAML frontmatter + reflections

Requirements:
  pip install notion-client python-dotenv

Setup:
  1. Go to notion.so/my-integrations
  2. Create a new integration named "Tanulytics"
  3. Copy the Integration Token → add to config/.env as NOTION_API_KEY
  4. Open your Portfolio page in Notion → Share → Invite → select "Tanulytics"
  5. Do the same for the Mindset Stack page and Daily Review database
"""

import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "config" / ".env")
except ImportError:
    pass

NOTION_API_KEY      = os.getenv("NOTION_API_KEY", "")

# Notion page / database IDs — set these in config/.env
PORTFOLIO_PAGE_ID   = os.getenv("NOTION_PORTFOLIO_PAGE_ID", "")
MINDSET_STACK_ID    = os.getenv("NOTION_MINDSET_STACK_ID", "")
DAILY_REVIEW_DB_ID  = os.getenv("NOTION_DAILY_REVIEW_DB_ID", "")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _check_deps():
    try:
        import notion_client
        return True
    except ImportError:
        print("  ❌ notion-client not installed. Run: pip install notion-client")
        return False


def _client():
    from notion_client import Client
    return Client(auth=NOTION_API_KEY)


def _fmt_currency(v, symbol="$"):
    if v is None:
        return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{symbol}{v:,.2f}"


def _fmt_pct(v):
    if v is None:
        return ""
    sign = "+" if v >= 0 else ""
    return f" ({sign}{v:.1f}%)"


def _today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _today_display():
    return datetime.now(timezone.utc).strftime("%B %d, %Y")


# ── Block builders ─────────────────────────────────────────────────────────────

def _rich_text(text: str, bold: bool = False, color: str = "default") -> dict:
    return {
        "type": "text",
        "text": {"content": text},
        "annotations": {
            "bold":          bold,
            "italic":        False,
            "strikethrough": False,
            "underline":     False,
            "code":          False,
            "color":         color,
        },
    }


def _paragraph(text: str, bold: bool = False) -> dict:
    return {
        "object": "block",
        "type":   "paragraph",
        "paragraph": {
            "rich_text": [_rich_text(text, bold=bold)],
        },
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _heading_3(text: str) -> dict:
    return {
        "object": "block",
        "type":   "heading_3",
        "heading_3": {
            "rich_text": [_rich_text(text)],
            "is_toggleable": False,
        },
    }


def _callout(emoji: str, lines: list) -> dict:
    """
    lines: list of (text, bold, color) tuples or plain strings.
    """
    rich_text = []
    for line in lines:
        if isinstance(line, str):
            rich_text.append(_rich_text(line))
            rich_text.append(_rich_text("\n"))
        else:
            text, bold, color = line
            rich_text.append(_rich_text(text, bold=bold, color=color))
            rich_text.append(_rich_text("\n"))

    return {
        "object": "block",
        "type":   "callout",
        "callout": {
            "rich_text": rich_text,
            "icon":      {"type": "emoji", "emoji": emoji},
            "color":     "gray_background",
        },
    }


def _build_portfolio_callout(summary: dict, positions: list, balances: list) -> dict:
    """
    Build the daily snapshot callout block for the Portfolio page.
    """
    today      = _today_display()
    daily_pnl  = summary.get("total_daily_pnl")
    unreal_pnl = summary.get("total_unrealised_pnl")
    net_liq    = summary.get("total_net_liq")
    n_pos      = summary.get("total_positions", 0)
    synced     = ", ".join(summary.get("brokers_synced", [])).upper() or "None"
    failed     = ", ".join(summary.get("brokers_failed", [])).upper() or "None"
    synced_at  = summary.get("synced_at", "")[:19].replace("T", " ")

    lines = [
        (f"📊 Tanulytics Daily Summary — {today}", True, "default"),
        "",
        (f"Daily P&L:         {_fmt_currency(daily_pnl)}", False,
         "green" if daily_pnl and daily_pnl >= 0 else "red"),
        (f"Unrealised P&L:    {_fmt_currency(unreal_pnl)}", False, "default"),
        (f"Net Liquidation:   {_fmt_currency(net_liq)}", False, "default"),
        "",
        (f"Open Positions:    {n_pos}", False, "default"),
        (f"Brokers Synced:    {synced}", False, "default"),
        (f"Brokers Failed:    {failed}", False, "red" if failed != "None" else "default"),
        "",
        (f"Last synced: {synced_at} UTC", False, "gray"),
    ]

    # Per-broker breakdown
    if balances:
        lines.append("")
        lines.append(("Broker Breakdown:", True, "default"))
        for b in balances:
            broker   = b.get("broker", "")
            nliq     = b.get("net_liq")
            dpnl     = b.get("daily_pnl")
            broker_line = (
                f"  {broker:12s}  NLV: {_fmt_currency(nliq)}  "
                f"Daily: {_fmt_currency(dpnl)}"
            )
            lines.append((broker_line, False, "default"))

    return _callout("📈", lines)


def _build_market_context(summary: dict) -> list:
    """
    Build paragraph blocks for the Daily Review morning check-in.
    One concise line so it reads quickly at 07:00.
    """
    daily_pnl  = summary.get("total_daily_pnl")
    unreal_pnl = summary.get("total_unrealised_pnl")
    n_pos      = summary.get("total_positions", 0)
    synced     = ", ".join(summary.get("brokers_synced", [])).upper() or "—"

    return [
        _heading_3("📊 Market Context"),
        _paragraph(
            f"Daily P&L: {_fmt_currency(daily_pnl)}  |  "
            f"Unrealised: {_fmt_currency(unreal_pnl)}  |  "
            f"Positions: {n_pos}  |  Synced: {synced}"
        ),
    ]


# ── Push functions ─────────────────────────────────────────────────────────────

def _push_to_portfolio(notion, summary: dict, positions: list, balances: list):
    """
    Append a daily snapshot callout block to the Portfolio page.
    Prepends a divider so each day's entry is visually separated.
    """
    print("  Pushing to Portfolio page...")
    callout = _build_portfolio_callout(summary, positions, balances)
    try:
        notion.blocks.children.append(
            PORTFOLIO_PAGE_ID,
            children=[_divider(), callout],
        )
        print("  ✅ Portfolio page updated.")
    except Exception as e:
        print(f"  ⚠️  Portfolio page update failed: {e}")


def _push_to_daily_review(notion, summary: dict):
    """
    Find today's Daily Review entry and append the market context.

    Strategy:
      1. Query DAILY_REVIEW_DB_ID for a page whose title contains today's date.
      2. If found → append Market Context blocks.
      3. If not found → create a new Daily Review page for today,
         then append Market Context blocks.

    Never writes to the Mindset Stack root — that page is for habits,
    not market data.
    """
    print("  Pushing to Daily Review...")
    today     = _today_str()
    today_fmt = _today_display()

    if not DAILY_REVIEW_DB_ID or DAILY_REVIEW_DB_ID.startswith("your_"):
        print("  ⚠️  NOTION_DAILY_REVIEW_DB_ID not set — skipping Daily Review push.")
        return

    market_blocks = _build_market_context(summary)

    # ── 1. Search for today's entry ───────────────────────────────────────────
    try:
        results = notion.databases.query(
            database_id=DAILY_REVIEW_DB_ID,
            filter={
                "property": "title",
                "title": {"contains": today},
            },
        ).get("results", [])
    except Exception as e:
        print(f"  ⚠️  Could not query Daily Review DB: {e}")
        return

    # ── 2a. Entry exists → append ─────────────────────────────────────────────
    if results:
        page_id = results[0]["id"]
        try:
            notion.blocks.children.append(page_id, children=market_blocks)
            print(f"  ✅ Market context added to Daily Review ({today})")
        except Exception as e:
            print(f"  ⚠️  Could not append to Daily Review entry: {e}")
        return

    # ── 2b. No entry yet → create one ────────────────────────────────────────
    print(f"  ℹ️  No Daily Review entry found for {today} — creating one.")
    try:
        new_page = notion.pages.create(
            parent={"database_id": DAILY_REVIEW_DB_ID},
            properties={
                "title": {
                    "title": [{"type": "text", "text": {"content": today_fmt}}]
                }
            },
            children=market_blocks,
        )
        print(f"  ✅ Created Daily Review entry for {today} with market context.")
    except Exception as e:
        print(f"  ⚠️  Could not create Daily Review entry: {e}")


# ── Main entry point ──────────────────────────────────────────────────────────

def push_summary(combined_data: dict) -> None:
    """
    Push the daily portfolio summary to Notion.

    Args:
        combined_data: dict returned by aggregator.aggregate().

    Returns:
        None. Errors are printed as warnings but do not raise — a Notion
        failure should never abort the pipeline when Airtable already succeeded.

    Raises:
        RuntimeError: if notion-client is not installed or NOTION_API_KEY is missing.
    """
    if not _check_deps():
        raise RuntimeError("notion-client not installed.")

    if not NOTION_API_KEY or NOTION_API_KEY.startswith("your_"):
        raise RuntimeError(
            "NOTION_API_KEY not set. "
            "Add it to config/.env — see the module docstring for setup instructions."
        )

    notion    = _client()
    summary   = combined_data.get("summary", {})
    positions = combined_data.get("positions", [])
    balances  = combined_data.get("balances", [])

    _push_to_portfolio(notion, summary, positions, balances)
    _push_to_daily_review(notion, summary)

    print("  ✅ Notion summary push complete.")
