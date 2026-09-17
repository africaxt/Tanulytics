<<<<<<< HEAD
#!/usr/bin/env python3
"""
notion_sync.py — Mirror canonical Notion entity content into Obsidian stub pages.

Part of the Tanulytics OS. Keeps the vault's entity *pointer stubs*
(`wiki/entities/*.md` carrying a `notion_url:` in their YAML frontmatter) in
sync with their canonical Notion pages. Notion stays the single source of
truth; this script only refreshes the mirrored body between sync markers and
never touches the frontmatter or the hand-written pointer/links above them.

Usage
-----
    python scripts/notion_sync.py                     # sync every stub under wiki/
    python scripts/notion_sync.py --dry-run           # report changes, write nothing
    python scripts/notion_sync.py --path wiki/entities/HBC.md   # one file
    python scripts/notion_sync.py --verbose

Wiring
------
Add one line to run_all.py (after notion_summary.py), or run it standalone /
on a schedule:

    subprocess.run([sys.executable, "scripts/notion_sync.py"], check=False)

Requirements (already in the project): notion-client, python-dotenv, pyyaml
Env (config/.env): NOTION_API_KEY

IMPORTANT: every Notion page mirrored here must be shared with the "Tanulytics"
integration (open the page → Share → Invite → Tanulytics), otherwise the API
returns 404 / unauthorized and that stub is skipped (its existing content is
left intact).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency: pyyaml  (pip install pyyaml)")

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency: notion-client  (pip install notion-client)")


# --------------------------------------------------------------------------- #
# Paths & config
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WIKI_ROOT = PROJECT_ROOT / "wiki"
ENV_PATH = PROJECT_ROOT / "config" / ".env"

START_MARKER = "<!-- NOTION-SYNC:START (auto-generated — do not edit below this line) -->"
END_MARKER = "<!-- NOTION-SYNC:END -->"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
UUID_RE = re.compile(r"([0-9a-fA-F]{32}|[0-9a-fA-F-]{36})")


def log(msg: str, *, verbose_only: bool = False, verbose: bool = False) -> None:
    if verbose_only and not verbose:
        return
    print(msg)


def load_env() -> str:
    if load_dotenv and ENV_PATH.exists():
        load_dotenv(ENV_PATH)
    key = os.getenv("NOTION_API_KEY")
    if not key:
        sys.exit(f"NOTION_API_KEY not set (looked in env and {ENV_PATH}).")
    return key


# --------------------------------------------------------------------------- #
# Stub discovery
# --------------------------------------------------------------------------- #
def read_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def extract_page_id(notion_url: str) -> str | None:
    """Pull the 32-hex (or dashed) page id from a Notion URL or bare id."""
    if not notion_url:
        return None
    # last path segment often is <slug>-<id> or just <id>
    tail = str(notion_url).rstrip("/").split("/")[-1].split("?")[0]
    candidates = UUID_RE.findall(tail) or UUID_RE.findall(str(notion_url))
    if not candidates:
        return None
    raw = candidates[-1].replace("-", "")
    if len(raw) != 32:
        return None
    return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


def find_stubs(paths: list[Path]) -> list[tuple[Path, str]]:
    """Return (path, page_id) for every markdown file with a notion_url."""
    out: list[tuple[Path, str]] = []
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.suffix == ".md":
            files.append(p)
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = read_frontmatter(text)
        page_id = extract_page_id(fm.get("notion_url", ""))
        if page_id:
            out.append((f, page_id))
    return out


# --------------------------------------------------------------------------- #
# Notion -> Markdown
# --------------------------------------------------------------------------- #
def rich_to_md(rich: list[dict]) -> str:
    parts: list[str] = []
    for r in rich or []:
        t = r.get("plain_text", "")
        if not t:
            continue
        ann = r.get("annotations", {})
        if ann.get("code"):
            t = f"`{t}`"
        if ann.get("bold"):
            t = f"**{t}**"
        if ann.get("italic"):
            t = f"*{t}*"
        if ann.get("strikethrough"):
            t = f"~~{t}~~"
        href = r.get("href")
        if href:
            t = f"[{t}]({href})"
        parts.append(t)
    return "".join(parts)


def _children(client: Client, block_id: str) -> list[dict]:
    blocks, cursor = [], None
    while True:
        resp = client.blocks.children.list(block_id=block_id, start_cursor=cursor, page_size=100)
        blocks.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return blocks


def blocks_to_md(client: Client, block_id: str, depth: int = 0) -> list[str]:
    lines: list[str] = []
    indent = "  " * depth
    for b in _children(client, block_id):
        bt = b.get("type", "")
        data = b.get(bt, {})
        rich = data.get("rich_text", [])
        text = rich_to_md(rich)

        if bt == "paragraph":
            lines.append(f"{indent}{text}" if text else "")
        elif bt in ("heading_1", "heading_2", "heading_3"):
            hashes = {"heading_1": "##", "heading_2": "###", "heading_3": "####"}[bt]
            lines.append(f"{hashes} {text}")
        elif bt == "bulleted_list_item":
            lines.append(f"{indent}- {text}")
        elif bt == "numbered_list_item":
            lines.append(f"{indent}1. {text}")
        elif bt == "to_do":
            box = "x" if data.get("checked") else " "
            lines.append(f"{indent}- [{box}] {text}")
        elif bt == "toggle":
            lines.append(f"{indent}- {text}")
        elif bt == "quote":
            lines.append(f"{indent}> {text}")
        elif bt == "callout":
            icon = (data.get("icon") or {}).get("emoji", "")
            lines.append(f"{indent}> {icon} {text}".rstrip())
        elif bt == "code":
            lang = data.get("language", "")
            lines.append(f"```{lang}\n{text}\n```")
        elif bt == "divider":
            lines.append("---")
        elif bt == "child_page":
            lines.append(f"{indent}- {b.get('child_page', {}).get('title', 'Untitled')} (sub-page)")
        elif bt in ("bookmark", "embed", "link_preview"):
            url = data.get("url", "")
            if url:
                lines.append(f"{indent}- <{url}>")
        elif bt == "image":
            f = data.get("file") or data.get("external") or {}
            url = f.get("url", "")
            if url:
                lines.append(f"{indent}![image]({url})")
        elif bt == "table":
            lines.extend(_render_table(client, b))
            continue
        else:
            if text:
                lines.append(f"{indent}{text}")

        # recurse (tables handled above)
        if b.get("has_children") and bt not in ("table", "child_page"):
            lines.extend(blocks_to_md(client, b["id"], depth + 1))
    return lines


def _render_table(client: Client, table_block: dict) -> list[str]:
    rows = _children(client, table_block["id"])
    out: list[str] = []
    for i, row in enumerate(rows):
        cells = row.get("table_row", {}).get("cells", [])
        rendered = [rich_to_md(c).replace("|", "\\|") or " " for c in cells]
        out.append("| " + " | ".join(rendered) + " |")
        if i == 0:
            out.append("|" + "|".join([" --- "] * len(rendered)) + "|")
    return out


def props_to_md(client: Client, page_id: str) -> str:
    """Render a database page's properties as a short bullet list (skips the title)."""
    try:
        page = client.pages.retrieve(page_id=page_id)
    except Exception:
        return ""
    lines: list[str] = []
    for name, p in (page.get("properties") or {}).items():
        t = p.get("type")
        val = ""
        if t == "title":
            continue
        elif t == "rich_text":
            val = "".join(r.get("plain_text", "") for r in p.get("rich_text", []))
        elif t == "select":
            val = ((p.get("select") or {}).get("name")) or ""
        elif t == "status":
            val = ((p.get("status") or {}).get("name")) or ""
        elif t == "multi_select":
            val = ", ".join(o.get("name", "") for o in p.get("multi_select", []))
        elif t == "url":
            val = p.get("url") or ""
        elif t == "number":
            n = p.get("number")
            val = "" if n is None else str(n)
        elif t == "checkbox":
            val = "yes" if p.get("checkbox") else ""
        elif t == "date":
            val = ((p.get("date") or {}).get("start")) or ""
        elif t == "people":
            val = ", ".join(u.get("name", "") for u in p.get("people", []))
        elif t == "email":
            val = p.get("email") or ""
        elif t == "phone_number":
            val = p.get("phone_number") or ""
        else:
            continue
        if val:
            lines.append(f"- **{name}:** {val}")
    return "\n".join(lines)


def fetch_page_markdown(client: Client, page_id: str) -> str:
    parts: list[str] = []
    props_md = props_to_md(client, page_id)
    if props_md:
        parts.append(props_md)
    body = blocks_to_md(client, page_id)
    body_md = re.sub(r"\n{3,}", "\n\n", "\n".join(body)).strip()
    if body_md:
        parts.append(body_md)
    md = "\n\n".join(parts).strip()
    return md or "_(Notion page is empty)_"


# --------------------------------------------------------------------------- #
# Stub writing
# --------------------------------------------------------------------------- #
def build_sync_block(md: str) -> str:
    stamp = _dt.date.today().isoformat()
    return (
        f"{START_MARKER}\n"
        f"_Synced from Notion on {stamp}. Edit the source in Notion, not here._\n\n"
        f"{md}\n"
        f"{END_MARKER}"
    )


def upsert_sync_block(original: str, md: str) -> str:
    block = build_sync_block(md)
    if START_MARKER in original and END_MARKER in original:
        pattern = re.compile(
            re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
            re.DOTALL,
        )
        return pattern.sub(lambda _m: block, original, count=1)
    # first run: append a synced section
    sep = "" if original.endswith("\n") else "\n"
    return f"{original}{sep}\n## From Notion (synced)\n\n{block}\n"


def sync_file(client: Client, path: Path, page_id: str, *, dry_run: bool, verbose: bool) -> str:
    try:
        md = fetch_page_markdown(client, page_id)
    except APIResponseError as e:
        return f"SKIP  {path.name}: Notion API error ({e.code}). Is the page shared with the integration?"
    except Exception as e:  # noqa: BLE001
        return f"SKIP  {path.name}: {e}"

    original = path.read_text(encoding="utf-8")
    updated = upsert_sync_block(original, md)
    if updated == original:
        return f"OK    {path.name}: already up to date"
    if dry_run:
        return f"DIFF  {path.name}: would update ({len(md)} chars from Notion)"
    path.write_text(updated, encoding="utf-8")
    return f"SYNC  {path.name}: updated ({len(md)} chars)"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Sync Notion pages into Obsidian entity stubs.")
    ap.add_argument("--path", help="Sync a single .md file or a directory (default: wiki/).")
    ap.add_argument("--dry-run", action="store_true", help="Report changes without writing.")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    key = load_env()
    client = Client(auth=key)

    targets = [Path(args.path) if args.path else WIKI_ROOT]
    targets = [t if t.is_absolute() else (PROJECT_ROOT / t) for t in targets]

    stubs = find_stubs(targets)
    if not stubs:
        log("No stubs with a `notion_url:` frontmatter found.")
        return 0

    log(f"Found {len(stubs)} Notion-linked stub(s).", verbose_only=True, verbose=args.verbose)
    changed = 0
    for path, page_id in stubs:
        result = sync_file(client, path, page_id, dry_run=args.dry_run, verbose=args.verbose)
        if result.startswith(("SYNC", "DIFF")):
            changed += 1
        log(result)

    log(f"\nDone. {changed} file(s) {'would change' if args.dry_run else 'updated'}, "
        f"{len(stubs) - changed} unchanged/skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
=======
#!/usr/bin/env python3
"""
notion_sync.py — Mirror canonical Notion entity content into Obsidian stub pages.

Part of the Tanulytics OS. Keeps the vault's entity *pointer stubs*
(`wiki/entities/*.md` carrying a `notion_url:` in their YAML frontmatter) in
sync with their canonical Notion pages. Notion stays the single source of
truth; this script only refreshes the mirrored body between sync markers and
never touches the frontmatter or the hand-written pointer/links above them.

Usage
-----
    python scripts/notion_sync.py                     # sync every stub under wiki/
    python scripts/notion_sync.py --dry-run           # report changes, write nothing
    python scripts/notion_sync.py --path wiki/entities/HBC.md   # one file
    python scripts/notion_sync.py --verbose

Wiring
------
Add one line to run_all.py (after notion_summary.py), or run it standalone /
on a schedule:

    subprocess.run([sys.executable, "scripts/notion_sync.py"], check=False)

Requirements (already in the project): notion-client, python-dotenv, pyyaml
Env (config/.env): NOTION_API_KEY

IMPORTANT: every Notion page mirrored here must be shared with the "Tanulytics"
integration (open the page → Share → Invite → Tanulytics), otherwise the API
returns 404 / unauthorized and that stub is skipped (its existing content is
left intact).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency: pyyaml  (pip install pyyaml)")

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError
except ImportError:  # pragma: no cover
    sys.exit("Missing dependency: notion-client  (pip install notion-client)")


# --------------------------------------------------------------------------- #
# Paths & config
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WIKI_ROOT = PROJECT_ROOT / "wiki"
ENV_PATH = PROJECT_ROOT / "config" / ".env"

START_MARKER = "<!-- NOTION-SYNC:START (auto-generated — do not edit below this line) -->"
END_MARKER = "<!-- NOTION-SYNC:END -->"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
UUID_RE = re.compile(r"([0-9a-fA-F]{32}|[0-9a-fA-F-]{36})")


def log(msg: str, *, verbose_only: bool = False, verbose: bool = False) -> None:
    if verbose_only and not verbose:
        return
    print(msg)


def load_env() -> str:
    if load_dotenv and ENV_PATH.exists():
        load_dotenv(ENV_PATH)
    key = os.getenv("NOTION_API_KEY")
    if not key:
        sys.exit(f"NOTION_API_KEY not set (looked in env and {ENV_PATH}).")
    return key


# --------------------------------------------------------------------------- #
# Stub discovery
# --------------------------------------------------------------------------- #
def read_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def extract_page_id(notion_url: str) -> str | None:
    """Pull the 32-hex (or dashed) page id from a Notion URL or bare id."""
    if not notion_url:
        return None
    # last path segment often is <slug>-<id> or just <id>
    tail = str(notion_url).rstrip("/").split("/")[-1].split("?")[0]
    candidates = UUID_RE.findall(tail) or UUID_RE.findall(str(notion_url))
    if not candidates:
        return None
    raw = candidates[-1].replace("-", "")
    if len(raw) != 32:
        return None
    return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


def find_stubs(paths: list[Path]) -> list[tuple[Path, str]]:
    """Return (path, page_id) for every markdown file with a notion_url."""
    out: list[tuple[Path, str]] = []
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.suffix == ".md":
            files.append(p)
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = read_frontmatter(text)
        page_id = extract_page_id(fm.get("notion_url", ""))
        if page_id:
            out.append((f, page_id))
    return out


# --------------------------------------------------------------------------- #
# Notion -> Markdown
# --------------------------------------------------------------------------- #
def rich_to_md(rich: list[dict]) -> str:
    parts: list[str] = []
    for r in rich or []:
        t = r.get("plain_text", "")
        if not t:
            continue
        ann = r.get("annotations", {})
        if ann.get("code"):
            t = f"`{t}`"
        if ann.get("bold"):
            t = f"**{t}**"
        if ann.get("italic"):
            t = f"*{t}*"
        if ann.get("strikethrough"):
            t = f"~~{t}~~"
        href = r.get("href")
        if href:
            t = f"[{t}]({href})"
        parts.append(t)
    return "".join(parts)


def _children(client: Client, block_id: str) -> list[dict]:
    blocks, cursor = [], None
    while True:
        resp = client.blocks.children.list(block_id=block_id, start_cursor=cursor, page_size=100)
        blocks.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return blocks


def blocks_to_md(client: Client, block_id: str, depth: int = 0) -> list[str]:
    lines: list[str] = []
    indent = "  " * depth
    for b in _children(client, block_id):
        bt = b.get("type", "")
        data = b.get(bt, {})
        rich = data.get("rich_text", [])
        text = rich_to_md(rich)

        if bt == "paragraph":
            lines.append(f"{indent}{text}" if text else "")
        elif bt in ("heading_1", "heading_2", "heading_3"):
            hashes = {"heading_1": "##", "heading_2": "###", "heading_3": "####"}[bt]
            lines.append(f"{hashes} {text}")
        elif bt == "bulleted_list_item":
            lines.append(f"{indent}- {text}")
        elif bt == "numbered_list_item":
            lines.append(f"{indent}1. {text}")
        elif bt == "to_do":
            box = "x" if data.get("checked") else " "
            lines.append(f"{indent}- [{box}] {text}")
        elif bt == "toggle":
            lines.append(f"{indent}- {text}")
        elif bt == "quote":
            lines.append(f"{indent}> {text}")
        elif bt == "callout":
            icon = (data.get("icon") or {}).get("emoji", "")
            lines.append(f"{indent}> {icon} {text}".rstrip())
        elif bt == "code":
            lang = data.get("language", "")
            lines.append(f"```{lang}\n{text}\n```")
        elif bt == "divider":
            lines.append("---")
        elif bt == "child_page":
            lines.append(f"{indent}- {b.get('child_page', {}).get('title', 'Untitled')} (sub-page)")
        elif bt in ("bookmark", "embed", "link_preview"):
            url = data.get("url", "")
            if url:
                lines.append(f"{indent}- <{url}>")
        elif bt == "image":
            f = data.get("file") or data.get("external") or {}
            url = f.get("url", "")
            if url:
                lines.append(f"{indent}![image]({url})")
        elif bt == "table":
            lines.extend(_render_table(client, b))
            continue
        else:
            if text:
                lines.append(f"{indent}{text}")

        # recurse (tables handled above)
        if b.get("has_children") and bt not in ("table", "child_page"):
            lines.extend(blocks_to_md(client, b["id"], depth + 1))
    return lines


def _render_table(client: Client, table_block: dict) -> list[str]:
    rows = _children(client, table_block["id"])
    out: list[str] = []
    for i, row in enumerate(rows):
        cells = row.get("table_row", {}).get("cells", [])
        rendered = [rich_to_md(c).replace("|", "\\|") or " " for c in cells]
        out.append("| " + " | ".join(rendered) + " |")
        if i == 0:
            out.append("|" + "|".join([" --- "] * len(rendered)) + "|")
    return out


def props_to_md(client: Client, page_id: str) -> str:
    """Render a database page's properties as a short bullet list (skips the title)."""
    try:
        page = client.pages.retrieve(page_id=page_id)
    except Exception:
        return ""
    lines: list[str] = []
    for name, p in (page.get("properties") or {}).items():
        t = p.get("type")
        val = ""
        if t == "title":
            continue
        elif t == "rich_text":
            val = "".join(r.get("plain_text", "") for r in p.get("rich_text", []))
        elif t == "select":
            val = ((p.get("select") or {}).get("name")) or ""
        elif t == "status":
            val = ((p.get("status") or {}).get("name")) or ""
        elif t == "multi_select":
            val = ", ".join(o.get("name", "") for o in p.get("multi_select", []))
        elif t == "url":
            val = p.get("url") or ""
        elif t == "number":
            n = p.get("number")
            val = "" if n is None else str(n)
        elif t == "checkbox":
            val = "yes" if p.get("checkbox") else ""
        elif t == "date":
            val = ((p.get("date") or {}).get("start")) or ""
        elif t == "people":
            val = ", ".join(u.get("name", "") for u in p.get("people", []))
        elif t == "email":
            val = p.get("email") or ""
        elif t == "phone_number":
            val = p.get("phone_number") or ""
        else:
            continue
        if val:
            lines.append(f"- **{name}:** {val}")
    return "\n".join(lines)


def fetch_page_markdown(client: Client, page_id: str) -> str:
    parts: list[str] = []
    props_md = props_to_md(client, page_id)
    if props_md:
        parts.append(props_md)
    body = blocks_to_md(client, page_id)
    body_md = re.sub(r"\n{3,}", "\n\n", "\n".join(body)).strip()
    if body_md:
        parts.append(body_md)
    md = "\n\n".join(parts).strip()
    return md or "_(Notion page is empty)_"


# --------------------------------------------------------------------------- #
# Stub writing
# --------------------------------------------------------------------------- #
def build_sync_block(md: str) -> str:
    stamp = _dt.date.today().isoformat()
    return (
        f"{START_MARKER}\n"
        f"_Synced from Notion on {stamp}. Edit the source in Notion, not here._\n\n"
        f"{md}\n"
        f"{END_MARKER}"
    )


def upsert_sync_block(original: str, md: str) -> str:
    block = build_sync_block(md)
    if START_MARKER in original and END_MARKER in original:
        pattern = re.compile(
            re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
            re.DOTALL,
        )
        return pattern.sub(lambda _m: block, original, count=1)
    # first run: append a synced section
    sep = "" if original.endswith("\n") else "\n"
    return f"{original}{sep}\n## From Notion (synced)\n\n{block}\n"


def sync_file(client: Client, path: Path, page_id: str, *, dry_run: bool, verbose: bool) -> str:
    try:
        md = fetch_page_markdown(client, page_id)
    except APIResponseError as e:
        return f"SKIP  {path.name}: Notion API error ({e.code}). Is the page shared with the integration?"
    except Exception as e:  # noqa: BLE001
        return f"SKIP  {path.name}: {e}"

    original = path.read_text(encoding="utf-8")
    updated = upsert_sync_block(original, md)
    if updated == original:
        return f"OK    {path.name}: already up to date"
    if dry_run:
        return f"DIFF  {path.name}: would update ({len(md)} chars from Notion)"
    path.write_text(updated, encoding="utf-8")
    return f"SYNC  {path.name}: updated ({len(md)} chars)"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Sync Notion pages into Obsidian entity stubs.")
    ap.add_argument("--path", help="Sync a single .md file or a directory (default: wiki/).")
    ap.add_argument("--dry-run", action="store_true", help="Report changes without writing.")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    key = load_env()
    client = Client(auth=key)

    targets = [Path(args.path) if args.path else WIKI_ROOT]
    targets = [t if t.is_absolute() else (PROJECT_ROOT / t) for t in targets]

    stubs = find_stubs(targets)
    if not stubs:
        log("No stubs with a `notion_url:` frontmatter found.")
        return 0

    log(f"Found {len(stubs)} Notion-linked stub(s).", verbose_only=True, verbose=args.verbose)
    changed = 0
    for path, page_id in stubs:
        result = sync_file(client, path, page_id, dry_run=args.dry_run, verbose=args.verbose)
        if result.startswith(("SYNC", "DIFF")):
            changed += 1
        log(result)

    log(f"\nDone. {changed} file(s) {'would change' if args.dry_run else 'updated'}, "
        f"{len(stubs) - changed} unchanged/skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
>>>>>>> c4461662d3e0c9889d8bb1ae887650fcc7835c35
