# Continuous AI partner — infrastructure vision

Status: **idea / not implemented**. Describes what a 24/7 or near-24/7 monitoring layer could look like if you outgrow manual sync + Cursor sessions.

## Goals

- **Fresh truth:** exchange state (balances, positions, orders) available without manual copy-paste.
- **Lean context:** summaries and alerts, not raw firehoses into the LLM.
- **Fail fast:** if APIs or jobs break, you know immediately — no silent staleness.
- **Separation of concerns:** deterministic ingestion vs. interpretive AI — never mix "facts" and "opinions" in one opaque blob.

## Layer 1 — Data plane (no LLM)

| Component | Role |
|-----------|------|
| **Scheduler** | Cron, Windows Task Scheduler, or systemd timer — runs every N minutes when markets matter to you. |
| **Ingest worker** | Same logic as `exchange/sync.py` (ccxt): balances, positions, open orders, recent fills. Writes JSON + `snapshot.md`. |
| **Normalizers** | Stable schema: `positions[]`, `orders[]`, `account`, `last_sync_utc`, `source`. |
| **Diff engine** | Compare current snapshot to previous; emit `events.jsonl` or small `delta.md` (opened, closed, size changed, SL moved). |
| **Retention** | Rotate raw files daily/weekly; keep aggregates longer. |

LLM never calls the exchange directly in this design — only reads **already materialized** files.

## Layer 2 — Summary plane (still mostly deterministic)

| Artifact | Purpose |
|----------|---------|
| `rolling_summary.md` | 30-50 lines: open risk, symbols, time in trade, distance to SL/TP, deviations from last agreed plan. |
| `stats.json` | Win rate, streak, last N R — fed from your journal projections or from tagged closes. |
| **Alert rules** | e.g. "position opened with no SL", "size > X% of declared capital", "SL moved away from entry" — flag before any AI reads the file. |

Optional: tiny rule engine (Python) — no ML required.

## Layer 3 — AI plane (interpretation)

| Mode | When |
|------|------|
| **On-demand (current)** | Cursor + `context.md` + `snapshot.md` after sync. |
| **Scheduled digest** | Local LLM or API generates a 1-page brief from `rolling_summary.md` + `delta.md` only — not full history. |
| **Interrupt** | Only on alert conditions (Telegram, email, desktop notification) to avoid notification fatigue. |

**Context budget:** LLM input should be `context.md` + `rolling_summary.md` + last `delta.md` + active `journal/positions/<today>-plan.md` — not entire `exchange/data/` history.

## Incremental path (recommended)

1. **Now:** manual `python exchange/sync.py` + Cursor verification.
2. **Next:** Task Scheduler runs sync every 5-15 min during your trading window; optional `delta.md`.
3. **Later:** alert rules + optional local digest model.
