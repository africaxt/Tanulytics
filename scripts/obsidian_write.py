"""
obsidian_write.py
─────────────────
Writes a dated pipeline summary note to the Obsidian vault at:
  <vault_root>/journal/YYYY-MM-DD.md

If the note already exists (e.g. from an earlier run today), the
Pipeline Summary section is updated in-place — manual edits in
other sections are preserved.

Called by run_all.py after notion_summary.  Also importable standalone:
    from obsidian_write import write_journal
    write_journal(combined_data)

Obsidian / Dataview note
────────────────────────
Each note is created with YAML frontmatter so Dataview can query across
journal entries.  Example query:

    ```dataview
    TABLE net_liq, daily_pnl, positions
    FROM "journal"
    SORT date DESC
    LIMIT 30
    ```
"""

from __future__ import annotations

import re
from datetime import datetime, date
from pathlib import Path

# ── Vault root ────────────────────────────────────────────────────────────────
# Two directories up from scripts/ → vault root
VAULT_ROOT = Path(__file__).parent.parent
JOURNAL_DIR = VAULT_ROOT / "journal"
JOURNAL_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt(value, prefix: str = "", suffix: str = "", decimals: int = 2) -> str:
    """Format a numeric value or return '—' if None/missing."""
    if value is None:
        return "—"
    try:
        return f"{prefix}{float(value):,.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_yaml(value) -> str:
    """Format a numeric value for YAML frontmatter (null if missing)."""
    if value is None:
        return "null"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "null"


def _broker_table(balances: list[dict]) -> str:
    if not balances:
        return "_No balance data._\n"
    lines = ["| Broker | Account | Net Liq | Daily P&L | Cash |",
             "|---|---|---|---|---|"]
    for b in balances:
        lines.append(
            f"| {b.get('broker', '—')} "
            f"| {b.get('account', '—')} "
            f"| {_fmt(b.get('net_liq'), '$')} "
            f"| {_fmt(b.get('daily_pnl'), '$')} "
            f"| {_fmt(b.get('cash'), '$')} |"
        )
    return "\n".join(lines) + "\n"


def _position_table(positions: list[dict]) -> str:
    if not positions:
        return "_No open positions._\n"
    lines = ["| Symbol | Broker | Direction | Qty | Entry | Current | Unreal P&L |",
             "|---|---|---|---|---|---|---|"]
    for p in sorted(positions, key=lambda x: x.get("broker", "")):
        lines.append(
            f"| {p.get('symbol', '—')} "
            f"| {p.get('broker', '—')} "
            f"| {p.get('direction', '—')} "
            f"| {_fmt(p.get('quantity'), decimals=4)} "
            f"| {_fmt(p.get('entry_price'), '$')} "
            f"| {_fmt(p.get('current_price'), '$')} "
            f"| {_fmt(p.get('unrealised_pnl'), '$')} |"
        )
    return "\n".join(lines) + "\n"


def _trades_table(trades: list[dict]) -> str:
    if not trades:
        return "_No trades today._\n"
    lines = ["| Symbol | Broker | Side | Qty | Price | Realised P&L |",
             "|---|---|---|---|---|---|"]
    for t in trades:
        lines.append(
            f"| {t.get('symbol', '—')} "
            f"| {t.get('broker', '—')} "
            f"| {t.get('side', '—')} "
            f"| {_fmt(t.get('quantity'), decimals=4)} "
            f"| {_fmt(t.get('price'), '$')} "
            f"| {_fmt(t.get('realised_pnl'), '$')} |"
        )
    return "\n".join(lines) + "\n"


# ── Pipeline summary block ────────────────────────────────────────────────────

def _build_summary_block(data: dict) -> str:
    summary   = data.get("summary", {})
    balances  = data.get("balances", [])
    positions = data.get("positions", [])
    trades    = data.get("trades", [])

    synced_at = summary.get("synced_at", datetime.now().isoformat())
    try:
        synced_str = datetime.fromisoformat(synced_at).strftime("%H:%M:%S")
    except Exception:
        synced_str = synced_at

    block = f"""## Pipeline Summary
> Last synced: {synced_str} · Brokers: {", ".join(summary.get("brokers_synced", []) or ["—"])}
> Full data: Airtable (positions/trades/balances) · Notion Portfolio (daily snapshot)

| Metric | Value |
|---|---|
| Net Liquidation | {_fmt(summary.get("total_net_liq"), "$")} |
| Daily P&L | {_fmt(summary.get("total_daily_pnl"), "$")} |
| Unrealised P&L | {_fmt(summary.get("total_unrealised_pnl"), "$")} |
| Open Positions | {summary.get("total_positions", "—")} |
| Trades Today | {summary.get("total_trades", "—")} |
| Brokers Failed | {", ".join(summary.get("brokers_failed", []) or ["None"])} |

### Broker Breakdown

{_broker_table(balances)}
### Open Positions

{_position_table(positions)}
### Trades Executed

{_trades_table(trades)}"""
    return block


# ── Note template ────────────────────────────────────────────────────────────
# YAML frontmatter enables Dataview queries across journal entries:
#
#   ```dataview
#   TABLE net_liq, daily_pnl, positions
#   FROM "journal"
#   SORT date DESC
#   LIMIT 30
#   ```

_NOTE_TEMPLATE = """\
---
type: journal
date: {date}
net_liq: {net_liq}
daily_pnl: {daily_pnl}
unrealised_pnl: {unrealised_pnl}
positions: {positions}
trades_today: {trades_today}
brokers: [{brokers}]
tags: [journal, trading, {year}]
---

# {date} — Daily Trading Journal

{summary_block}

---

## Market Context

*What's the macro backdrop today? Key levels, events, sentiment.*

---

## Trade Rationale

*For any trades executed today — why did you enter/exit? Was it rule-based or discretionary?*

---

## Observations

*Patterns noticed, anomalies, anything worth remembering.*

---

## Tomorrow

*Setups to watch, actions to take, levels to monitor.*

---

## Mindset

*Brief reflection — discipline, focus, emotional state during session.*

"""

# Regex matches the YAML frontmatter block (--- ... ---)
_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)

# Regex matches the Pipeline Summary section
_SUMMARY_RE = re.compile(
    r"## Pipeline Summary.*?(?=\n## |\Z)", re.DOTALL
)


# ── Note writer ───────────────────────────────────────────────────────────────

def write_journal(data: dict, target_date: date | None = None) -> Path:
    """
    Write or update the journal note for *target_date* (defaults to today).
    Returns the path of the note written.

    On first run: creates a full note from template with YAML frontmatter.
    On repeat runs: updates frontmatter metrics AND Pipeline Summary block,
    preserving all manual sections.
    """
    target_date = target_date or date.today()
    date_str    = target_date.strftime("%Y-%m-%d")
    note_path   = JOURNAL_DIR / f"{date_str}.md"

    summary       = data.get("summary", {})
    summary_block = _build_summary_block(data)

    # Build frontmatter values
    net_liq       = _fmt_yaml(summary.get("total_net_liq"))
    daily_pnl     = _fmt_yaml(summary.get("total_daily_pnl"))
    unrealised_pnl = _fmt_yaml(summary.get("total_unrealised_pnl"))
    positions     = summary.get("total_positions", 0) or 0
    trades_today  = summary.get("total_trades", 0) or 0
    brokers_raw   = summary.get("brokers_synced", []) or []
    brokers       = ", ".join(f'"{b}"' for b in brokers_raw)

    new_frontmatter = (
        f"---\n"
        f"type: journal\n"
        f"date: {date_str}\n"
        f"net_liq: {net_liq}\n"
        f"daily_pnl: {daily_pnl}\n"
        f"unrealised_pnl: {unrealised_pnl}\n"
        f"positions: {positions}\n"
        f"trades_today: {trades_today}\n"
        f"brokers: [{brokers}]\n"
        f"tags: [journal, trading, {target_date.year}]\n"
        f"---\n"
    )

    if note_path.exists():
        existing = note_path.read_text(encoding="utf-8")

        # Update frontmatter
        if _FRONTMATTER_RE.match(existing):
            existing = _FRONTMATTER_RE.sub(new_frontmatter, existing, count=1)
        else:
            existing = new_frontmatter + "\n" + existing

        # Update Pipeline Summary section
        if _SUMMARY_RE.search(existing):
            updated = _SUMMARY_RE.sub(summary_block, existing, count=1)
        else:
            lines = existing.split("\n", 2)
            updated = lines[0] + "\n\n" + summary_block + "\n\n" + (lines[2] if len(lines) > 2 else "")

        note_path.write_text(updated, encoding="utf-8")
    else:
        content = _NOTE_TEMPLATE.format(
            date=date_str,
            year=target_date.year,
            summary_block=summary_block,
            net_liq=net_liq,
            daily_pnl=daily_pnl,
            unrealised_pnl=unrealised_pnl,
            positions=positions,
            trades_today=trades_today,
            brokers=brokers,
        )
        note_path.write_text(content, encoding="utf-8")

    return note_path


# ── Standalone entry point ────────────────────────────────────────────────────

def main(return_data: bool = False):
    """
    Standalone: loads the most recent processed JSON and writes the journal note.
    Usage: python scripts/obsidian_write.py
    """
    import json

    processed_dir = VAULT_ROOT / "data" / "processed"
    files = sorted(processed_dir.glob("combined_*.json"), reverse=True)
    if not files:
        print("No processed data found. Run the full pipeline first.")
        return

    latest = files[0]
    with open(latest) as f:
        data = json.load(f)

    path = write_journal(data)
    print(f"✅ Obsidian journal note written: {path}")


if __name__ == "__main__":
    main()
