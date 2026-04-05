# Exchange sync

## Default: Bitget

The shipped `sync.py` is wired for **Bitget USDT-margined futures** (`defaultType: swap`). Credentials live in `vault/bitget-api.env` (workspace root in this layout).

**Bulk leverage (optional):** `set_leverage_all.py` sets leverage on every **active USDT perpetual** via ccxt (`set_leverage` per symbol). Example: `python exchange/set_leverage_all.py --leverage 50` (use `--dry-run` first). Some symbols may cap below 50x or fail if you have open positions/orders; Bitget returns errors per market.

## Other CEXes — intentionally simple

MOST does **not** lock you to Bitget. Sync uses **[ccxt](https://github.com/ccxt/ccxt)** (`ccxt.async_support`), which implements a **unified API** for [100+ exchanges](https://docs.ccxt.com/#/README?id=exchanges). For most venues, adapting MOST is a **small, local change** — not a rewrite of the journal, rules, or Cursor layer.

Typical fork of `sync.py` for another exchange:

| Step | What to change |
|------|----------------|
| 1 | Swap `ccxt.bitget({...})` for e.g. `ccxt.binanceusdm`, `ccxt.bybit`, `ccxt.okx`, etc. (check ccxt docs for the exact class id for your market type: spot vs USDM swap vs coin-m). |
| 2 | Adjust **constructor options** (`defaultType`, `options`) to match that exchange’s futures/spot model. |
| 3 | Tune **`fetch_balance` / `fetch_positions` params** — some exchanges need `{'type': 'swap'}` or exchange-specific flags (Bitget’s `mix` vs `uta` detection in the current script is an example of that pattern). |
| 4 | If **`fetch_closed_orders`** behaves differently, narrow or replace with `fetch_my_trades` / `fetch_orders` per ccxt’s method table for that exchange. |
| 5 | Rename or duplicate **`vault/bitget-api.env`** → e.g. `vault/exchange.env` and map env var names to whatever that CEX expects (often still `apiKey`, `secret`, sometimes `password`). |

After that, **output shape stays the same**: JSON + `snapshot.md` under `exchange/data/`. The rest of MOST (Cursor rules, journal, tools) stays untouched.

## Outputs (Bitget, `exchange/data/`)

| File | Purpose |
|------|---------|
| **`snapshot.md`** | Starts with **`# Reconciliation & coverage`** — **read this first**: interpretation ladder, **warnings** (pagination, ledger span, fill gaps), and **recent ledger close bills** (`close_short` / `burst_*` / `force_*`). Then balance, positions, orders, closes, fills. |
| **`reconciliation.json`** | Machine-readable digest: same warnings, `closed_orders_paginated`, fill counts, `recent_close_bills` for stops/closes when order history is ambiguous. |
| `balances.json` | Current swap USDT balance |
| `positions.json` | Open positions |
| `open_orders.json` | Pending / trigger orders |
| `trades.json` | Closed swap orders + **`realized_pnl`** (from Bitget raw `info`, e.g. `totalProfits`) |
| **`closed_orders_pnl.md`** | **One table** — same rows as `trades.json`, all columns including realized PnL |
| `transactions.json` | **Fill-level** legs — Bitget requires **`fetch_my_trades(symbol)`** per symbol; sync merges symbols from **positions + open orders + recent closed orders** |
| **`funding.json`** | All-time USDT **deposits** and **withdrawals** (ccxt paginate) + summary |
| **`accounting.md`** | **Net external** vs **current swap equity**; **signed R** only if you configure a rule unit (see below) |
| **`balance_history.jsonl`** | Append-only **one line per sync** (timestamp + total/free/used) |
| **`ledger.json`** | Raw-normalized **mix account bills** (USDT-M) |
| **`balance_timeline.jsonl`** | **One line per bill** (chronological): `delta_usdt`, **`balance_after_usdt`**, `order_ref`, etc. |
| **`balance_timeline.md`** | Human-readable sample (last 500 rows) + reconciliation stats |
| **`balance_timeline_meta.json`** | Stats, `ledger_span` (`last_90d_only` default), API error if any |

### How to interpret (order of trust)

1. **Positions** — current net exposure.
2. **Open orders** — resting and **unfilled** triggers (stops not hit yet).
3. **Ledger / balance timeline** — **cashflow per bill**; best signal for **stop / force-close / burst** when labels differ in order history.
4. **Closed orders** — must be **fully paginated** or old rows disappear from the tail.
5. **Funding** — external cash in/out (not per-fill).
6. **Transactions** — aggregated **fills** per symbol (merged by sync).

The **`# Reconciliation & coverage`** block in `snapshot.md` repeats this ladder and surfaces **coverage gaps** so the AI does not treat an incomplete table as complete truth.

**Ledger scope:** By default the timeline uses **the last 90 days** of bills (fast). Use `--ledger-full-history` to walk all 90-day windows (same depth as funding fetch; much slower). Bitget v2 requires a `businessType` filter — the script queries a fixed list of types and merges results (extend `_V2_BUSINESS_TYPES` in `sync.py` if you miss rows).

### Accounting calibration (no amounts in `sync.py`)

Copy `exchange/accounting_config.example.json` → **`exchange/accounting_config.json`** (gitignored) and set **`mental_bankroll_usd`** and **`r_unit_usd`** to match your `rules.md`. Alternatively set **`MOST_MENTAL_BANKROLL_USD`** and **`MOST_R_UNIT_USD`** in `vault/bitget-api.env` (overrides JSON). If unset, USD columns still populate; **signed R** is omitted.

**Single merge for AI + tools:** `most/system/calibration.py` (`load_calibration()`, `load_accounting_config()`) reads the same files plus optional **`system/calibration.json`** — see **`most/system/SOURCE_OF_TRUTH.md`**. Sync imports `load_accounting_config` from there (no duplicated logic).

Full sync runs funding + accounting by default; use `--no-funding` to skip deposit/withdrawal API calls.

**Closed orders:** **Full sync** paginates **all** closed swap pages by default (may be slower). Use **`--closed-orders-fast`** to fetch **only the first page** (~100 rows) — **not** recommended for accountability work. With **`--trades` alone** (no full sync), default is still one page unless you pass **`--closed-orders-full`**. Realized PnL is whatever Bitget attaches to each order row; opens often show `0` or `—`.

**Fills (`transactions.json`):** Bitget’s API does **not** return `fetch_my_trades()` without a **symbol**. Sync collects symbols from open positions, open orders, and recent closed orders, then queries each. If you are flat and have no recent history, the fill list may be empty — use **ledger bills** instead.

**Note:** `exchange/data/` is gitignored (secrets / live balances). **Ledger files exist on your machine**; they are not in git unless you change `.gitignore`.

## Multi-account or multi-venue later

A clean evolution (when you want it) is: one small **adapter module** per exchange + a config key `EXCHANGE_ID=bitget|binanceusdm|...` — still one sync entrypoint. That can ship as a follow-up PR without changing the product story.

## Contributing

If you add first-class support for another major futures venue, a PR that keeps **default behavior = current Bitget script** and documents env vars in `vault/*.env.example` is welcome.
