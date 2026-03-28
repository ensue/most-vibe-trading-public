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
| `trades.json` | Recent closed orders |
| `transactions.json` | Fill-level history (when API returns) |
| `snapshot.md` | Human-readable roll-up of the above |
| **`funding.json`** | All-time USDT **deposits** and **withdrawals** (ccxt paginate) + summary |
| **`accounting.md`** | **Net external** vs **current swap equity** → **signed R** (÷ $40 rule unit vs `most/rules.md`) |
| **`balance_history.jsonl`** | Append-only **one line per sync** (timestamp + total/free/used) |

Full sync runs funding + accounting by default; use `--no-funding` to skip deposit/withdrawal API calls.

**Note:** `exchange/data/` is gitignored (secrets / live balances). **Ledger files exist on your machine**; they are not in git unless you change `.gitignore`.

## Multi-account or multi-venue later

A clean evolution (when you want it) is: one small **adapter module** per exchange + a config key `EXCHANGE_ID=bitget|binanceusdm|...` — still one sync entrypoint. That can ship as a follow-up PR without changing the product story.

## Contributing

If you add first-class support for another major futures venue, a PR that keeps **default behavior = current Bitget script** and documents env vars in `vault/*.env.example` is welcome.
