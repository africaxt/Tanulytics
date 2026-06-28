# Tanulytics — System Instructions

Full reference for the Tanulytics trading operating system. For daily workflow and quick commands, see `README.md`.

> **Wiki:** [[index]] · [[LearnAI]] · [[XeQT]] · [[PipelineArchitecture]] · [[PortfolioOverview]] · [[RiskFramework]]



---

## System of Record

Each tool in the Tanulytics OS has a single clearly-defined role. Avoid duplicating data across layers; use each tool for its authoritative purpose.

| Layer | Owns | Do NOT use for |
|---|---|---|
| **Airtable** | Full structured data — positions, trades, balances (deduplicated, queryable) | Narrative, reflections, analysis |
| **Notion Portfolio page** | Daily P&L callout (external/reporting layer). Investor-presentable snapshot. | Personal journal, private reflections |
| **Notion Daily Review DB** | One-line Market Context for morning Claude check-in | Full trade logs, position tables |
| **Obsidian journal/** | Headline metrics (YAML frontmatter) + personal reflections (Market Context, Trade Rationale, Observations, Tomorrow, Mindset) | Investor reporting |
| **Obsidian wiki/** | Knowledge accumulation — broker pages, strategy pages, concept pages, trade theses | Live pipeline data |

Pipeline push order per run:
```
run_all.py → airtable_push.py → notion_summary.py → obsidian_write.py
              (source of truth)   (Portfolio + DailyReview)  (journal + wiki)
```


## What Tanulytics is

Tanulytics is a closed-loop portfolio aggregation and reporting system sitting at the Capital pillar of the AMB Mindset Stack. It pulls live position, balance, and trade data from 4 brokers, normalises everything into a common schema, pushes it to Airtable as the central data layer, and surfaces a daily summary on the Notion Portfolio page and Mindset Stack morning check-in.

```
SIGNAL GENERATION        BACKTESTING           EXECUTION            AGGREGATION
TradingView          →   QuantConnect      →   IBKR (Algo)      →
(Pine Script)            (LEAN, primary)       FXCM (Forex)         aggregator.py
                         VectorBT (local)      Schwab (Macro)   →   → Airtable
                                               Robinhood (Value)→   → Notion
```

---

## Architecture

### Pipeline flow

```
run_all.py
  ├── ibkr_fetch.py       → data/raw/ibkr_YYYYMMDD_HHMMSS.json
  ├── fxcm_fetch.py       → reads data/raw/tv_fxcm_events.jsonl
  ├── schwab_fetch.py     → data/raw/schwab_YYYYMMDD_HHMMSS.json
  ├── robinhood_fetch.py  → data/raw/robinhood_YYYYMMDD_HHMMSS.json
  ↓
  aggregator.py           → data/processed/combined_YYYYMMDD_HHMMSS.json
  ↓
  airtable_push.py        → Airtable: Positions / Balances / Trade History / Daily Summary
  ↓
  notion_summary.py       → Notion: Portfolio page + Mindset Stack
```

### Design principles

1. **Code owns the schema** — Airtable tables are created programmatically from real broker data, not designed manually. Run the pipeline once and the tables exist.
2. **Read-only everywhere** — scripts never place orders. IBKR uses `readonly=True`, no order endpoints are called on Schwab or Robinhood.
3. **Data first** — each broker script dumps raw JSON to `data/raw/` before any processing. If the aggregator fails, the raw data is safe to inspect and replay.
4. **Deduplication** — Trade History uses broker-native order/trade IDs (hashed where not available) to prevent double-importing on repeated runs.
5. **Graceful degradation** — if one broker fails, `run_all.py` logs the error and continues with the others.

---

## Broker setup

### IBKR

**Strategy:** Algorithmic + Global Macro

**Connection:** `ib_async` connects to TWS running locally on macOS. TWS must be open before running the script.

**TWS configuration:**
1. Edit → Global Configuration → API → Settings
2. Enable: `Enable ActiveX and Socket Clients`, `Read-Only API`, `Download open orders on connection`
3. Trusted IPs: `127.0.0.1`
4. Port: 7497 (TWS paper/live), 4001 (IB Gateway fallback)

**`.env` keys required:**
```
IBKR_HOST=127.0.0.1
IBKR_TWS_PORT=7497
IBKR_CLIENT_ID=99
```

**Notes:**
- The script tries port 7497 first, then 4001.
- Historical trades beyond today's session require a Flex Query export (CSV) — load in a future `aggregator.py` enrichment step.
- Never run scripts while strategies are live if concerned about API interference.

---

### FXCM (via TradingView webhooks)

**Strategy:** Forex / CFDs

**Architecture:** TradingView → cloudflared tunnel → `tv_webhook_server.py` → `data/raw/tv_fxcm_events.jsonl` → `fxcm_fetch.py`

`fxcmpy` is no longer used (stale since 2024, FXCM tokens hard to obtain). TradingView is already the execution layer, so this approach uses the existing TV connection.

**One-time setup:**

1. **Start the webhook server:**
   ```bash
   python scripts/tv_webhook_server.py
   ```

2. **Expose it via cloudflared:**
   ```bash
   brew install cloudflared
   cloudflared tunnel --url http://localhost:8787
   # Prints a public HTTPS URL — copy it
   ```
   For a stable URL across restarts, register a named tunnel at `one.dash.cloudflare.com`.

3. **Configure TradingView alerts.** For each FXCM Pine Script strategy:
   - Alert → Notifications → Webhook URL:
     ```
     https://<your-cloudflared-host>/fxcm-webhook/<FXCM_WEBHOOK_SECRET>
     ```
   - Alert message body (TradingView fills `{{...}}` at trigger time):
     ```json
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
     ```
   - Test by triggering a manual alert — confirm an event appears in `data/raw/tv_fxcm_events.jsonl`.

**`.env` keys required:**
```
FXCM_WEBHOOK_SECRET=<auto-generated on first setup>
FXCM_WEBHOOK_PORT=8787
FXCM_LOOKBACK_DAYS=30
```

**Known limitations:**
- No live account balance or equity from webhooks.
- No unrealised P&L on open positions (no live price feed).
- Mitigation: import weekly FXCM CSV statement via `aggregator.py` for reconciliation.

---

### Schwab

**Strategy:** Global Macro

**Connection:** `schwabdev` wrapper around the official Schwab Trader API. Handles OAuth token refresh automatically after first login.

**One-time setup:**
1. Create an account at `developer.schwab.com` (separate from brokerage login).
2. Create an "Individual Developer" app:
   - Add callback URL: `https://127.0.0.1`
   - Wait for status to flip from "Approved - Pending" to "Ready For Use" (Schwab manual review, typically a few business days).
3. Copy App Key and App Secret into `config/.env`.
4. First run opens a browser for OAuth login — `schwabdev` caches tokens to `config/.schwab_tokens.json`.

**Token lifecycle:**
- Access token: 30 minutes (auto-refreshed)
- Refresh token: 7 days — must run the pipeline at least weekly to keep it alive

**`.env` keys required:**
```
SCHWAB_APP_KEY=your_schwab_app_key
SCHWAB_APP_SECRET=your_schwab_app_secret
SCHWAB_CALLBACK_URL=https://127.0.0.1
```

**Important:** Never commit `config/.schwab_tokens.json` — it grants 7 days of trading API access.

---

### Robinhood

**Strategy:** Value Investing (US Equities + Options)

**Connection:** `robin_stocks` unofficial wrapper. Supports TOTP-automated and interactive MFA.

**Recommended auth setup (automated):**
1. Robinhood app → Settings → Security → Two-Factor Authentication → Authenticator App → "Other"
2. Robinhood shows an alphanumeric TOTP secret — copy it into `config/.env` as `ROBINHOOD_TOTP_SECRET`.
3. The script generates a fresh 6-digit code per login via `pyotp` — no human intervention needed.

**Without `ROBINHOOD_TOTP_SECRET`:** `robin_stocks` will prompt stdin for an SMS/email MFA code on every login, which blocks the automated pipeline.

**`.env` keys required:**
```
ROBINHOOD_USERNAME=your_email@example.com
ROBINHOOD_PASSWORD=your_password
ROBINHOOD_TOTP_SECRET=your_totp_secret
```

**Session caching:** `robin_stocks` writes `~/.tokens/robinhood.pickle` — the TOTP code is only consumed every ~24h while this token is valid.

**Warning:** `robin_stocks` is an unofficial reverse-engineered wrapper. Robinhood can change their private API without notice. Fallback: weekly manual CSV export from the Robinhood website.

---

## Airtable setup

1. Log in to `airtable.com` → click avatar → Developer Hub → Personal access tokens.
2. Create a token with scopes: `data.records:read`, `data.records:write`, `schema.bases:read`, `schema.bases:write`.
3. Copy token → `config/.env` as `AIRTABLE_API_KEY`.
4. Leave `AIRTABLE_BASE_ID` blank for the first run — `airtable_push.py` creates a base named "Tanulytics" automatically and prints the Base ID.
5. Copy the printed Base ID → `config/.env` as `AIRTABLE_BASE_ID` so subsequent runs reuse it.

**Tables created automatically:**

| Table | Upsert key | Contents |
|---|---|---|
| Positions | Symbol + Broker | Live open positions across all brokers |
| Balances | Broker + Account + Date | Daily account snapshots |
| Trade History | Trade ID | Every executed trade, deduplicated |
| Daily Summary | (insert only) | One row per pipeline run |

---

## Notion setup

1. Go to `notion.so/my-integrations` → Create new integration → name it "Tanulytics".
2. Copy the Integration Token → `config/.env` as `NOTION_API_KEY`.
3. Open your **Portfolio page** in Notion → Share → Invite → select "Tanulytics".
4. Open your **Mindset Stack page** → Share → Invite → select "Tanulytics".

**What gets pushed on each run:**

- **Portfolio page** — a dated callout block with daily P&L, unrealised P&L, net liquidation, open position count, and per-broker breakdown.
- **Mindset Stack** — a "Market Context" block appended to today's Daily Review entry (or to the Mindset Stack root if no entry exists yet).

**Notion IDs (hardcoded in `notion_summary.py`):**

| Resource | ID |
|---|---|
| Portfolio page | `a0124ec5-d4f1-48c0-ad65-e145efc8b519` |
| Mindset Stack | `35ec9f23-0499-81f8-b62c-c70de010364c` |
| Daily Review DB | `2c2c9f23-0499-8172-aced-000b3f33f85a` |

---

## Running the pipeline

### Full pipeline
```bash
python scripts/run_all.py
```

### Dry run (fetch only, no push)
```bash
python scripts/run_all.py --dry-run
```
Use this to verify broker connections without writing anything to Airtable or Notion.

### Single broker
```bash
python scripts/run_all.py --broker ibkr
python scripts/run_all.py --broker fxcm
python scripts/run_all.py --broker schwab
python scripts/run_all.py --broker robinhood
```

### Verbose output
```bash
python scripts/run_all.py --verbose
```

### Logs
Pipeline logs are written to `logs/pipeline_YYYYMMDD.log` on every run.

---

## Data files

| Path | Created by | Contents |
|---|---|---|
| `data/raw/ibkr_*.json` | `ibkr_fetch.py` | Raw IBKR positions, trades, P&L |
| `data/raw/fxcm_*.json` | `fxcm_fetch.py` | Reconstructed FXCM positions + trades from webhook log |
| `data/raw/tv_fxcm_events.jsonl` | `tv_webhook_server.py` | TradingView alert events (FXCM) |
| `data/raw/schwab_*.json` | `schwab_fetch.py` | Raw Schwab balances, positions, transactions |
| `data/raw/robinhood_*.json` | `robinhood_fetch.py` | Raw Robinhood holdings, orders |
| `data/processed/combined_*.json` | `aggregator.py` | Normalised combined schema |
| `logs/pipeline_YYYYMMDD.log` | `run_all.py` | Full pipeline run log |
| `config/.schwab_tokens.json` | `schwabdev` | Schwab OAuth tokens (never commit) |
| `~/.tokens/robinhood.pickle` | `robin_stocks` | Robinhood session cache (outside project folder) |

---

## Normalised data schema

`aggregator.py` outputs a single dict with these keys:

### positions
```python
{
    "symbol":         str,
    "broker":         str,    # IBKR | FXCM | Schwab | Robinhood
    "strategy":       str,    # Algorithmic | Forex | Global Macro | Value Investing
    "asset_class":    str,    # Equity | Forex | Futures | Options | CFD | ETF | ...
    "direction":      str,    # Long | Short
    "quantity":       float,
    "entry_price":    float,
    "current_price":  float | None,
    "market_value":   float | None,
    "unrealised_pnl": float | None,
    "unrealised_pct": float | None,
    "cost_basis":     float | None,
    "currency":       str,
    "open_date":      str | None,
    "account":        str,
    "last_synced":    str,    # ISO datetime
}
```

### trades
```python
{
    "trade_id":     str,    # broker-native ID or hash — dedup key
    "broker":       str,
    "symbol":       str,
    "asset_class":  str,
    "side":         str,    # Buy | Sell
    "quantity":     float,
    "price":        float,
    "realised_pnl": float | None,
    "commission":   float | None,
    "currency":     str,
    "executed_at":  str,
    "account":      str,
}
```

### balances
```python
{
    "broker":         str,
    "account":        str,
    "net_liq":        float | None,
    "cash":           float | None,
    "buying_power":   float | None,
    "daily_pnl":      float | None,
    "unrealised_pnl": float | None,
    "realised_pnl":   float | None,
    "equity":         float | None,
    "currency":       str,
    "as_of":          str,
}
```

### summary
```python
{
    "date":                 str,    # YYYY-MM-DD
    "total_positions":      int,
    "total_trades":         int,
    "total_daily_pnl":      float | None,
    "total_unrealised_pnl": float | None,
    "total_net_liq":        float | None,
    "brokers_synced":       list[str],
    "brokers_failed":       list[str],
    "synced_at":            str,    # ISO datetime
}
```

---

## Troubleshooting

**IBKR won't connect**
- Confirm TWS is running and logged in.
- Check Edit → Global Configuration → API → Settings: `Enable ActiveX and Socket Clients` must be ticked.
- If another client is using Client ID 99, change `IBKR_CLIENT_ID` in `.env`.

**Schwab `auth_failed`**
- First run opens a browser — complete the OAuth login within ~60 seconds.
- If the app is still "Approved - Pending" at `developer.schwab.com`, wait for Schwab's manual review to complete.
- If tokens expire (>7 days since last run), delete `config/.schwab_tokens.json` and re-auth.

**Robinhood `auth_failed`**
- Verify `ROBINHOOD_USERNAME` and `ROBINHOOD_PASSWORD` in `.env` are correct.
- If using `ROBINHOOD_TOTP_SECRET`, check it's the raw alphanumeric secret from the authenticator setup screen (not a 6-digit code).
- Delete `~/.tokens/robinhood.pickle` to force a fresh login.

**FXCM returns no positions**
- Confirm `tv_webhook_server.py` is running and has received at least one TradingView alert.
- Check `data/raw/tv_fxcm_events.jsonl` — it should have at least one line.
- Verify the TradingView webhook URL uses the correct cloudflared host and `FXCM_WEBHOOK_SECRET`.

**Airtable `AIRTABLE_BASE_ID` not set**
- On the very first run, leave `AIRTABLE_BASE_ID` blank — the script creates the base and prints the ID.
- Copy that ID into `config/.env` and all subsequent runs will reuse it.

**Notion push fails**
- Confirm the integration token is valid at `notion.so/my-integrations`.
- Confirm the Portfolio page and Mindset Stack are shared with the "Tanulytics" integration (Share → Invite).
- Notion push failures do not abort the pipeline — Airtable data is safe even if Notion fails.

---

## Python dependencies

```bash
pip install ib_async flask schwabdev robin_stocks pyotp pyairtable notion-client pandas python-dotenv pyyaml
```

| Package | Purpose |
|---|---|
| `ib_async` | IBKR TWS connection |
| `flask` | TradingView webhook receiver (`tv_webhook_server.py`) |
| `schwabdev` | Schwab Trader API (OAuth token handling included) |
| `robin_stocks` | Robinhood unofficial wrapper |
| `pyotp` | TOTP code generation for Robinhood 2FA |
| `pyairtable` | Airtable read/write + schema management |
| `notion-client` | Notion API (blocks, databases, pages) |
| `pandas` | Data normalisation utilities |
| `python-dotenv` | Loads `config/.env` |
| `pyyaml` | Config file parsing (future use) |

---

## Important notes

- **Never run scripts that place orders.** All scripts are read-only data extractors.
- **Never commit `config/.env`** — it contains live API credentials.
- **Never commit `config/.schwab_tokens.json`** — it grants 7-day trading API access.
- FXCM balance and unrealised P&L are not available from webhooks alone — reconcile weekly via FXCM CSV statement import.
- IBKR historical trades beyond the current session require a Flex Query CSV export — load via `aggregator.py` in a future enrichment step.

---

## Obsidian Vault & AI Context

The Tanulytics folder is also an Obsidian vault. Use the following folders as live context when answering questions about trading activity, performance, or strategy:

### Vault structure

| Folder | Contents |
|---|---|
| `journal/` | Daily trading journal notes (`YYYY-MM-DD.md`). Auto-written by `obsidian_write.py` on each pipeline run. Contains pipeline summary (P&L, positions, broker snapshots) + manual reflections. |
| `notes/theses/` | Trade thesis notes — per-symbol conviction, entry/exit plan, outcome. |
| `notes/watchlists/` | Active watchlists by theme or strategy. |
| `notes/research/` | Market research, macro notes, deeper analysis. |
| `inbox/` | Quick-capture notes pending filing. Check here for recent unprocessed thoughts. |
| `templates/` | Note templates (`daily-journal.md`, `trade-thesis.md`, `watchlist.md`). |

### How to use vault context

- **Before answering questions about recent performance or trades**, read the latest journal note at `journal/YYYY-MM-DD.md` (use today's date or the most recent file).
- **Before answering questions about a specific position or symbol**, check `notes/theses/` for a matching thesis note.
- **When the user mentions a watchlist or market theme**, check `notes/watchlists/`.
- **For macro or research questions**, check `notes/research/`.
- Always prefer fresh vault data over assumptions from training when discussing Tanulytics-specific activity.

### Pipeline → Obsidian flow

Each `run_all.py` run writes or updates `journal/YYYY-MM-DD.md` via `scripts/obsidian_write.py`. The Pipeline Summary section is auto-replaced on each run; all other sections (Market Context, Trade Rationale, Observations, Tomorrow, Mindset) are manual and preserved between runs.

---

## LLM Wiki — Operations

This vault implements [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Three layers:

- **`raw/`** — immutable source documents (articles, papers, reports). Never modify.
- **`wiki/`** — LLM-generated pages. Claude owns this layer entirely.
- **`CLAUDE.md`** (this file) — the schema. Defines structure, conventions, and workflows.

---

### Wiki structure conventions

Every wiki page must have YAML frontmatter with at minimum:
```yaml
---
type: entity | concept | comparison | synthesis | summary
name: <name>
updated: YYYY-MM-DD
tags: []
---
```

Use `[[wikilinks]]` for all cross-references. Never use bare URLs for internal links.

Directory layout:
```
wiki/
  index.md              ← catalog of all pages (update on every ingest)
  log.md                ← append-only operation log
  entities/
    brokers/            ← one page per broker
    strategies/         ← one page per strategy
  concepts/             ← market concepts, risk framework, architecture
  comparisons/          ← side-by-side comparisons across entities
  synthesis/            ← rolling cross-broker portfolio synthesis
raw/
  articles/             ← web articles (Obsidian Web Clipper output)
  papers/               ← research papers
  reports/              ← earnings, macro, broker research
  assets/               ← locally downloaded images
```

---

### Operation: Ingest

Triggered when user says: "Ingest [filename]" or "Process [source]"

1. Read the source file from `raw/`
2. Discuss key takeaways with user if interactive; summarise if batch
3. Write a summary page in the appropriate `wiki/` subdirectory using `templates/wiki-page.md`
4. Update `wiki/index.md` — add the new page to the correct section
5. Update all relevant entity and concept pages that the source touches (add to their Sources table, revise facts if needed, note contradictions)
6. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <source title>`
7. Update `raw/README.md` sources table if applicable

A single source may touch 5–15 wiki pages. Touch all of them.

---

### Operation: Query

Triggered when user asks a question about trading activity, markets, or portfolio.

1. Read `wiki/index.md` to identify relevant pages
2. Read those pages in full
3. Also check `journal/YYYY-MM-DD.md` (today's or most recent) for live pipeline data
4. Synthesise an answer with `[[wikilink]]` citations
5. If the answer is non-trivial and reusable, offer to file it back as a new wiki page or update an existing one
6. Append to `wiki/log.md`: `## [YYYY-MM-DD] query | <question summary>`

---

### Operation: Lint

Triggered when user says: "Lint the wiki" or "Health check"

Check for and report:
- **Broken wikilinks** — links that don't resolve to an existing file
- **Orphan pages** — pages with no inbound links
- **Stale claims** — facts that newer sources have superseded (check source dates)
- **Missing pages** — concepts mentioned in multiple places but lacking their own page
- **Missing cross-references** — pages that should link to each other but don't
- **Empty sections** — pages with placeholder text still in them
- **Index gaps** — pages in `wiki/` not listed in `index.md`
- **Log gaps** — operations that happened but weren't logged

After reporting, offer to fix each issue. Append to `wiki/log.md`: `## [YYYY-MM-DD] lint | <issues found>`

---

### Frontmatter conventions

| Field | Values |
|---|---|
| `type` | `entity`, `concept`, `comparison`, `synthesis`, `summary`, `journal`, `thesis`, `watchlist` |
| `category` | `broker`, `strategy`, `market`, `macro`, `risk` |
| `status` | `open`, `closed`, `monitoring`, `draft` |
| `updated` | `YYYY-MM-DD` — update on every edit |
| `source_count` | integer — increment when a new source updates this page |
| `tags` | array — use consistent tags for Dataview queries |

---

### Page quality standard

A good wiki page:
- Opens with a 1–2 sentence summary (scannable without reading the full page)
- Has outbound `[[wikilinks]]` to every related entity and concept it mentions
- Has a Sources table listing every raw document that informed it
- Has an "Open questions" section flagging what's still uncertain
- Has accurate `updated` frontmatter
