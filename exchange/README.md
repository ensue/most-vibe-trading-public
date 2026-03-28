# Exchange sync

## Default: Bitget

The shipped `sync.py` is wired for **Bitget USDT-margined futures** (`defaultType: swap`). Credentials live in `vault/bitget-api.env` (workspace root in this layout).

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
| `balances.json` | Current swap USDT balance |
| `positions.json` | Open positions |
| `open_orders.json` | Pending / trigger orders |
| `trades.json` | Closed swap orders + **`realized_pnl`** (from Bitget raw `info`, e.g. `totalProfits`) |
| **`closed_orders_pnl.md`** | **One table** — same rows as `trades.json`, all columns including realized PnL |
| `transactions.json` | Fill-level history (when API returns) |
| `snapshot.md` | Human-readable roll-up of the above |
| **`funding.json`** | All-time USDT **deposits** and **withdrawals** (ccxt paginate) + summary |
| **`accounting.md`** | **Net external** vs **current swap equity**; **signed R** only if you configure a rule unit (see below) |
| **`balance_history.jsonl`** | Append-only **one line per sync** (timestamp + total/free/used) |
| **`ledger.json`** | Raw-normalized **mix account bills** (USDT-M) |
| **`balance_timeline.jsonl`** | **One line per bill** (chronological): `delta_usdt`, **`balance_after_usdt`**, `order_ref`, etc. |
| **`balance_timeline.md`** | Human-readable sample (last 500 rows) + reconciliation stats |
| **`balance_timeline_meta.json`** | Stats, `ledger_span` (`last_90d_only` default), API error if any |

**Ledger scope:** By default the timeline uses **the last 90 days** of bills (fast). Use `--ledger-full-history` to walk all 90-day windows (same depth as funding fetch; much slower). Bitget v2 requires a `businessType` filter — the script queries a fixed list of types and merges results (extend `_V2_BUSINESS_TYPES` in `sync.py` if you miss rows).

### Accounting calibration (no amounts in `sync.py`)

Copy `exchange/accounting_config.example.json` → **`exchange/accounting_config.json`** (gitignored) and set **`mental_bankroll_usd`** and **`r_unit_usd`** to match your `rules.md`. Alternatively set **`MOST_MENTAL_BANKROLL_USD`** and **`MOST_R_UNIT_USD`** in `vault/bitget-api.env` (overrides JSON). If unset, USD columns still populate; **signed R** is omitted.

Full sync runs funding + accounting by default; use `--no-funding` to skip deposit/withdrawal API calls.

**Closed orders:** Default is **one page** (`--closed-orders-limit`, default 100). Use **`--closed-orders-full`** to paginate through **all** closed swap orders (slower). Realized PnL is whatever Bitget attaches to each order row; opens often show `0` or `—`.

**Note:** `exchange/data/` is gitignored (secrets / live balances). **Ledger files exist on your machine**; they are not in git unless you change `.gitignore`.

## Multi-account or multi-venue later

A clean evolution (when you want it) is: one small **adapter module** per exchange + a config key `EXCHANGE_ID=bitget|binanceusdm|...` — still one sync entrypoint. That can ship as a follow-up PR without changing the product story.

## Contributing

If you add first-class support for another major futures venue, a PR that keeps **default behavior = current Bitget script** and documents env vars in `vault/*.env.example` is welcome.
