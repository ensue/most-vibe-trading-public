"""
Exchange data sync (default: Bitget futures).

Pulls balances, open positions, open orders, closed orders, and fill-level
transaction history via **ccxt**
and stores them as JSON + a human-readable snapshot.

MOST is not Bitget-only: ccxt supports many CEXes. To run on Binance USDM,
Bybit, OKX, etc., fork this file — swap the exchange class, constructor
options, and balance/position params. See `exchange/README.md`.

Usage:
    python exchange/sync.py              # sync everything (+ USDT funding + accounting)
    python exchange/sync.py --balance    # balance only
    python exchange/sync.py --positions  # positions only
    python exchange/sync.py --orders     # open/pending orders only
    python exchange/sync.py --trades     # closed orders only
    python exchange/sync.py --tx         # fill-level transaction history only
    python exchange/sync.py --no-funding # full sync but skip deposit/withdrawal API (faster)

Credentials (default): workspace `vault/bitget-api.env` (see VAULT_CANDIDATES in this file).

Accounting:
    Each successful sync appends `data/balance_history.jsonl`. Full sync also pulls all-time
    USDT `fetch_deposits` / `fetch_withdrawals` (ccxt paginate) and writes `data/funding.json`
    plus `data/accounting.md`. **R labels** are optional: set `exchange/accounting_config.json`
    (copy from `accounting_config.example.json`) or `MOST_R_UNIT_USD` / `MOST_MENTAL_BANKROLL_USD`
    in vault — no hardcoded dollar amounts in this script.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import ccxt.async_support as ccxt
from aiohttp import ClientSession, TCPConnector
from aiohttp.resolver import ThreadedResolver
from dotenv import dotenv_values

VAULT_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "vault" / "bitget-api.env",
    Path(__file__).resolve().parent.parent.parent / "vault" / "bitget-api.env",
    Path.cwd() / "vault" / "bitget-api.env",
]

DATA_DIR = Path(__file__).resolve().parent / "data"
EXCHANGE_DIR = Path(__file__).resolve().parent
BALANCE_HISTORY_FILE = "balance_history.jsonl"


def load_accounting_config() -> dict[str, float | None]:
    """
    Optional risk calibration for R labels in accounting output (not exchange balances).
    Priority: vault env vars > accounting_config.json > example file (nulls).
    """
    example_path = EXCHANGE_DIR / "accounting_config.example.json"
    path = EXCHANGE_DIR / "accounting_config.json"
    raw: dict = {}
    if example_path.exists():
        raw = json.loads(example_path.read_text(encoding="utf-8"))
    if path.exists():
        raw = {**raw, **json.loads(path.read_text(encoding="utf-8"))}
    for k in list(raw.keys()):
        if k.startswith("_"):
            del raw[k]

    def _f(key: str) -> float | None:
        v = raw.get(key)
        if v is None or v == "":
            return None
        return float(v)

    mental = _f("mental_bankroll_usd")
    r_unit = _f("r_unit_usd")

    for vault in VAULT_CANDIDATES:
        if not vault.exists():
            continue
        env = dotenv_values(vault)
        if (env.get("MOST_R_UNIT_USD") or "").strip():
            r_unit = float(env["MOST_R_UNIT_USD"].strip())
        if (env.get("MOST_MENTAL_BANKROLL_USD") or "").strip():
            mental = float(env["MOST_MENTAL_BANKROLL_USD"].strip())
        break

    return {"mental_bankroll_usd": mental, "r_unit_usd": r_unit}


def load_credentials() -> dict[str, str]:
    for path in VAULT_CANDIDATES:
        if path.exists():
            env = dotenv_values(path)
            return {
                "api_key": (env.get("BITGET_API_KEY") or "").strip(),
                "api_secret": (env.get("BITGET_API_SECRET") or "").strip(),
                "passphrase": (env.get("BITGET_PASSPHRASE") or "").strip(),
            }
    print(f"ERROR: vault/bitget-api.env not found. Searched: {VAULT_CANDIDATES}")
    sys.exit(1)


def create_exchange(creds: dict[str, str]) -> ccxt.bitget:
    return ccxt.bitget({
        "apiKey": creds["api_key"],
        "secret": creds["api_secret"],
        "password": creds["passphrase"],
        "options": {"defaultType": "swap"},
        "enableRateLimit": True,
    })


async def detect_balance_mode(exchange: ccxt.bitget) -> str:
    try:
        await exchange.fetch_balance({"type": "swap"})
        return "mix"
    except (ccxt.AuthenticationError, ccxt.BaseError):
        pass
    try:
        await exchange.fetch_balance({"uta": True})
        return "uta"
    except (ccxt.AuthenticationError, ccxt.BaseError) as e:
        print(f"ERROR: Cannot connect to Bitget. Check API credentials. Details: {e}")
        sys.exit(1)


async def fetch_balance(exchange: ccxt.bitget, mode: str) -> dict:
    params = {"uta": True} if mode == "uta" else {"type": "swap"}
    balance = await exchange.fetch_balance(params)
    usdt = balance.get("USDT", {})
    return {
        "total": float(usdt.get("total") or 0.0),
        "free": float(usdt.get("free") or 0.0),
        "used": float(usdt.get("used") or 0.0),
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }


async def fetch_positions(exchange: ccxt.bitget, mode: str) -> list[dict]:
    params = {"uta": True} if mode == "uta" else {}
    positions = await exchange.fetch_positions(symbols=None, params=params)
    result = []
    for p in positions:
        if float(p.get("contracts") or 0) == 0:
            continue
        result.append({
            "symbol": p["symbol"],
            "side": p["side"],
            "size": abs(float(p["contracts"] or 0)),
            "notional": abs(float(p["notional"] or 0)),
            "entry_price": float(p["entryPrice"] or 0),
            "mark_price": float(p["markPrice"] or 0),
            "liquidation_price": float(p["liquidationPrice"] or 0)
            if p.get("liquidationPrice") else None,
            "unrealized_pnl": float(p["unrealizedPnl"] or 0),
            "stop_loss": float(p["stopLossPrice"] or 0)
            if p.get("stopLossPrice") else None,
            "take_profit": float(p["takeProfitPrice"] or 0)
            if p.get("takeProfitPrice") else None,
            "leverage": float(p["leverage"] or 1),
            "margin_mode": p.get("marginMode", "unknown"),
            "percentage": float(p["percentage"] or 0),
        })
    return result


async def fetch_trades(exchange: ccxt.bitget, mode: str, limit: int = 50) -> list[dict]:
    params = {"type": "swap"}
    if mode == "uta":
        params["uta"] = True

    try:
        orders = await exchange.fetch_closed_orders(None, None, limit, params)
    except ccxt.BaseError:
        return []

    result = []
    for o in orders:
        if o["status"] != "closed":
            continue
        result.append({
            "id": o["id"],
            "symbol": o["symbol"],
            "side": o["side"],
            "type": o["type"],
            "price": float(o["price"] or 0),
            "amount": float(o["amount"] or 0),
            "cost": float(o["cost"] or 0),
            "fee": float((o.get("fee") or {}).get("cost") or 0),
            "timestamp": o["timestamp"],
            "datetime": o["datetime"],
            "reduce_only": o.get("reduceOnly", False),
        })

    result.sort(key=lambda x: x["timestamp"] or 0, reverse=True)
    return result


async def fetch_open_orders(exchange: ccxt.bitget, mode: str, limit: int = 100) -> list[dict]:
    """
    Bitget can expose regular open orders and trigger/plan orders via different params.
    Query multiple known variants and de-duplicate by order id.
    """
    query_params = [
        {"type": "swap"},
        {"type": "swap", "stop": True},
        {"type": "swap", "planType": "normal_plan"},
        {"type": "swap", "planType": "profit_loss"},
    ]
    if mode == "uta":
        query_params = [{**p, "uta": True} for p in query_params]

    by_id: dict[str, dict] = {}
    for params in query_params:
        try:
            orders = await exchange.fetch_open_orders(None, None, limit, params)
        except ccxt.BaseError:
            continue

        for o in orders:
            order_id = str(o.get("id") or "")
            if not order_id:
                continue
            info = o.get("info") or {}
            # Bitget often encodes close/open intent in raw fields (tradeSide/posSide),
            # while normalized side/reduceOnly may be ambiguous for trigger orders.
            trade_side = (
                info.get("tradeSide")
                or info.get("trade_side")
                or info.get("planType")
                or "—"
            )
            pos_side = info.get("posSide") or info.get("holdSide") or "—"
            raw_reduce = info.get("reduceOnly")
            if raw_reduce is None:
                raw_reduce = info.get("reduce_only")
            if raw_reduce is None:
                raw_reduce = o.get("reduceOnly", False)
            raw_reduce_str = str(raw_reduce).strip().lower()
            reduce_only = raw_reduce_str in {"true", "1", "yes", "y"} or raw_reduce is True
            by_id[order_id] = {
                "id": order_id,
                "symbol": o.get("symbol", "—"),
                "side": o.get("side", "—"),
                "type": o.get("type", "—"),
                "status": o.get("status", "—"),
                "price": float(o.get("price") or 0),
                "stop_price": float(o.get("stopPrice") or 0) if o.get("stopPrice") else None,
                "amount": float(o.get("amount") or 0),
                "reduce_only": reduce_only,
                "trade_side": str(trade_side),
                "pos_side": str(pos_side),
                "timestamp": o.get("timestamp"),
                "datetime": o.get("datetime"),
            }

    result = list(by_id.values())
    result.sort(key=lambda x: x["timestamp"] or 0, reverse=True)
    return result


async def fetch_transactions(exchange: ccxt.bitget, mode: str, limit: int = 200) -> list[dict]:
    params = {"type": "swap"}
    if mode == "uta":
        params["uta"] = True

    try:
        trades = await exchange.fetch_my_trades(None, None, limit, params)
    except ccxt.BaseError:
        return []

    result = []
    for t in trades:
        result.append({
            "id": t.get("id"),
            "order_id": t.get("order"),
            "symbol": t.get("symbol"),
            "side": t.get("side"),
            "type": t.get("type"),
            "price": float(t.get("price") or 0),
            "amount": float(t.get("amount") or 0),
            "cost": float(t.get("cost") or 0),
            "fee": float((t.get("fee") or {}).get("cost") or 0),
            "timestamp": t.get("timestamp"),
            "datetime": t.get("datetime"),
            "reduce_only": t.get("reduceOnly", False),
        })

    result.sort(key=lambda x: x["timestamp"] or 0, reverse=True)
    return result


def _tx_confirmed_success(tx: dict) -> bool:
    s = (tx.get("status") or "").lower()
    return s in ("ok", "success", "completed")


def _serialize_funding_tx(tx: dict) -> dict:
    fee = tx.get("fee")
    if isinstance(fee, dict):
        fee_cost = float(fee.get("cost") or 0)
    else:
        fee_cost = float(fee or 0)
    return {
        "id": str(tx.get("id") or ""),
        "timestamp": tx.get("timestamp"),
        "datetime": tx.get("datetime"),
        "amount": float(tx.get("amount") or 0),
        "status": tx.get("status"),
        "fee": fee_cost,
    }


# Bitget rejects deposit/withdraw lists if startTime→endTime span > 90 days (API error 00001).
_NINETY_DAYS_MS = 90 * 24 * 60 * 60 * 1000
# Each window can trigger many paginated calls; cap how far back we walk (≈12 years).
_MAX_FUNDING_WINDOWS = 48


async def _fetch_usdt_tx_windowed(
    exchange: ccxt.bitget,
    method_name: str,
) -> tuple[list, str | None]:
    """
    Walk backward in <=90d windows until epoch or max windows. Deduplicate by id.
    """
    fetch_fn = (
        exchange.fetch_deposits if method_name == "deposits" else exchange.fetch_withdrawals
    )
    merged: list = []
    seen: set[str] = set()
    end_ms = exchange.milliseconds()
    last_err: str | None = None

    for _ in range(_MAX_FUNDING_WINDOWS):
        start_ms = max(1, end_ms - _NINETY_DAYS_MS)
        try:
            chunk = await fetch_fn(
                "USDT",
                since=start_ms,
                limit=100,
                params={"until": end_ms, "paginate": True},
            )
        except ccxt.BaseError as e:
            last_err = f"{method_name}: {e}"
            break
        for t in chunk:
            tid = str(t.get("id") or t.get("txid") or "")
            key = tid or f"{t.get('timestamp')}-{t.get('amount')}"
            if key in seen:
                continue
            seen.add(key)
            merged.append(t)
        if start_ms <= 1:
            break
        end_ms = start_ms - 1

    return merged, last_err


async def fetch_usdt_deposits_and_withdrawals(exchange: ccxt.bitget) -> tuple[list, list, str | None]:
    """
    All-time USDT deposits and withdrawals (Bitget spot wallet API).
    Bitget caps each query to a 90-day window; we page backward in chunks and merge.
    """
    deposits, err_d = await _fetch_usdt_tx_windowed(exchange, "deposits")
    withdrawals, err_w = await _fetch_usdt_tx_windowed(exchange, "withdrawals")
    err_parts = [x for x in (err_d, err_w) if x]
    err = "; ".join(err_parts) if err_parts else None
    return deposits, withdrawals, err


def build_funding_summary(
    deposits: list,
    withdrawals: list,
    swap_equity: float,
    mental_bankroll_usd: float | None,
    r_unit_usd: float | None,
) -> dict:
    d_sum = sum(
        float(x.get("amount") or 0) for x in deposits if _tx_confirmed_success(x)
    )
    w_sum = sum(
        float(x.get("amount") or 0) for x in withdrawals if _tx_confirmed_success(x)
    )
    net_ext = d_sum - w_sum
    signed_r = None
    if r_unit_usd is not None and r_unit_usd > 0:
        signed_r = round((swap_equity - net_ext) / r_unit_usd, 4)
    out: dict = {
        "deposits_usdt_counted": round(d_sum, 8),
        "withdrawals_usdt_counted": round(w_sum, 8),
        "net_external_usdt": round(net_ext, 8),
        "current_swap_equity_usd": round(swap_equity, 8),
        "equity_minus_net_external_usdt": round(swap_equity - net_ext, 8),
        "cumulative_r_signed_vs_rule_unit": signed_r,
        "mental_bankroll_usd": mental_bankroll_usd,
        "rule_r_unit_usd": r_unit_usd,
        "caveat": (
            "Net external uses completed on-chain (or internal) deposits/withdrawals from Bitget "
            "wallet API. If USDT was moved only inside Bitget (spot↔futures), totals can still "
            "reconcile with swap equity; if some history is outside API range, numbers drift."
        ),
    }
    return out


def append_balance_snapshot(balance: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / BALANCE_HISTORY_FILE
    row = {
        "synced_at": balance.get("synced_at"),
        "total": balance.get("total"),
        "free": balance.get("free"),
        "used": balance.get("used"),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  appended {path.relative_to(Path(__file__).resolve().parent.parent)}")


def generate_accounting_md(
    summary: dict | None,
    funding_error: str | None,
    mental_bankroll_usd: float | None,
    r_unit_usd: float | None,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Exchange accounting (USDT)",
        "",
        f"Generated: {ts}",
        "",
        "## Reference (risk calibration — optional)",
        "",
    ]
    if mental_bankroll_usd is not None:
        lines.append(
            f"- Declared **mental bankroll**: **${mental_bankroll_usd:,.0f}** (from `accounting_config` or vault)"
        )
    else:
        lines.append(
            "- Declared **mental bankroll**: **not set** — add `mental_bankroll_usd` to "
            "`exchange/accounting_config.json` or `MOST_MENTAL_BANKROLL_USD` in vault"
        )
    if r_unit_usd is not None:
        lines.append(
            f"- **1R** (rule unit for sizing) = **${r_unit_usd:,.0f}** (from `accounting_config` or vault)"
        )
    else:
        lines.append(
            "- **1R** (rule unit): **not set** — add `r_unit_usd` to `exchange/accounting_config.json` "
            "or `MOST_R_UNIT_USD` in vault to show signed R in the table below"
        )
    lines.append("")

    if funding_error:
        lines.extend([
            "## Funding API",
            "",
            f"**Error:** {funding_error}",
            "",
        ])
    if summary is None:
        lines.extend([
            "_Funding summary unavailable (see error above or run sync without `--no-funding`)._",
            "",
        ])
        return "\n".join(lines)

    lines.extend([
        "## Funding vs swap equity (Bitget API)",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Completed USDT **deposits** (sum) | ${summary['deposits_usdt_counted']:,.2f} |",
        f"| Completed USDT **withdrawals** (sum) | ${summary['withdrawals_usdt_counted']:,.2f} |",
        f"| **Net external** (deposits − withdrawals) | ${summary['net_external_usdt']:,.2f} |",
        f"| **Current swap USDT equity** (this sync) | ${summary['current_swap_equity_usd']:,.2f} |",
        f"| Equity − net external | ${summary['equity_minus_net_external_usdt']:,.2f} |",
    ])
    if summary["cumulative_r_signed_vs_rule_unit"] is not None and r_unit_usd is not None:
        lines.append(
            f"| **Signed R** (÷ ${r_unit_usd:,.0f} rule unit) | **{summary['cumulative_r_signed_vs_rule_unit']:.2f} R** |"
        )
    else:
        lines.append("| **Signed R** | — (configure `r_unit_usd` to compute) |")
    lines.extend(["",])

    if summary["cumulative_r_signed_vs_rule_unit"] is not None and r_unit_usd is not None:
        lines.extend([
            "### Reading signed R",
            "",
            "- **Positive:** swap equity **above** net external funding (cumulative trading outcome positive vs cash in/out).",
            "- **Negative:** swap equity **below** net external funding (cumulative loss vs cash in/out, in **R units** at your configured rule unit).",
            "",
        ])
    lines.extend([
        f"_{summary['caveat']}_",
        "",
    ])
    return "\n".join(lines)


def generate_snapshot(
    balance: dict,
    positions: list,
    open_orders: list,
    trades: list,
    transactions: list,
    accounting_md: str | None = None,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"# Exchange Snapshot",
        f"",
        f"Synced: {ts}",
        f"",
        f"## Balance",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total | ${balance['total']:,.2f} |",
        f"| Free | ${balance['free']:,.2f} |",
        f"| In positions | ${balance['used']:,.2f} |",
        f"",
    ]

    if positions:
        lines.extend([
            "## Open Positions",
            "",
            "| Symbol | Side | Size | Entry | Mark | uPNL | SL | TP | Lev |",
            "|--------|------|------|-------|------|------|----|----|-----|",
        ])
        for p in positions:
            sl = f"${p['stop_loss']:,.2f}" if p["stop_loss"] else "—"
            tp = f"${p['take_profit']:,.2f}" if p["take_profit"] else "—"
            pnl_sign = "+" if p["unrealized_pnl"] >= 0 else ""
            lines.append(
                f"| {p['symbol']} | {p['side']} | {p['size']} "
                f"| ${p['entry_price']:,.2f} | ${p['mark_price']:,.2f} "
                f"| {pnl_sign}${p['unrealized_pnl']:,.2f} "
                f"| {sl} | {tp} | {int(p['leverage'])}x |"
            )
        lines.append("")
    else:
        lines.extend(["## Open Positions", "", "None.", ""])

    if open_orders:
        lines.extend([
            "## Open / Pending Orders",
            "",
            "| Time | Symbol | Side | TradeSide | PosSide | Type | Status | Price | Stop | Amount | Reduce-only |",
            "|------|--------|------|-----------|---------|------|--------|-------|------|--------|-------------|",
        ])
        for o in open_orders[:100]:
            dt = o["datetime"] or "—"
            if len(dt) > 19:
                dt = dt[:19]
            stop = f"${o['stop_price']:,.4f}" if o["stop_price"] else "—"
            price = f"${o['price']:,.4f}" if o["price"] else "—"
            reduce_only = "yes" if o["reduce_only"] else "no"
            lines.append(
                f"| {dt} | {o['symbol']} | {o['side']} | {o['trade_side']} | {o['pos_side']} "
                f"| {o['type']} | {o['status']} | {price} | {stop} | {o['amount']} | {reduce_only} |"
            )
        lines.append("")
    else:
        lines.extend(["## Open / Pending Orders", "", "None.", ""])

    if trades:
        lines.extend([
            "## Recent Closed Orders (last 50)",
            "",
            "| Time | Symbol | Side | Type | Price | Amount | Cost | Fee |",
            "|------|--------|------|------|-------|--------|------|-----|",
        ])
        for t in trades[:50]:
            dt = t["datetime"] or "—"
            if len(dt) > 19:
                dt = dt[:19]
            lines.append(
                f"| {dt} | {t['symbol']} | {t['side']} | {t['type']} "
                f"| ${t['price']:,.4f} | {t['amount']} | ${t['cost']:,.2f} "
                f"| ${t['fee']:,.4f} |"
            )
        lines.append("")
    else:
        lines.extend(["## Recent Closed Orders", "", "No closed orders found.", ""])

    if transactions:
        lines.extend([
            "## Recent Transactions / Fills (last 100)",
            "",
            "| Time | Symbol | Side | Type | Price | Amount | Cost | Fee | Order ID |",
            "|------|--------|------|------|-------|--------|------|-----|----------|",
        ])
        for t in transactions[:100]:
            dt = t["datetime"] or "—"
            if len(dt) > 19:
                dt = dt[:19]
            lines.append(
                f"| {dt} | {t['symbol']} | {t['side']} | {t['type']} "
                f"| ${t['price']:,.4f} | {t['amount']} | ${t['cost']:,.2f} "
                f"| ${t['fee']:,.4f} | {t['order_id'] or '—'} |"
            )
        lines.append("")
    else:
        lines.extend(["## Recent Transactions / Fills", "", "No transactions found.", ""])

    if accounting_md:
        lines.extend(["", "---", "", accounting_md.strip(), ""])

    return "\n".join(lines)


def save(filename: str, data) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  saved {path.relative_to(Path(__file__).resolve().parent.parent)}")


async def main(args: argparse.Namespace) -> None:
    sync_all = not (args.balance or args.positions or args.orders or args.trades or args.tx)

    creds = load_credentials()
    exchange = create_exchange(creds)
    resolver = ThreadedResolver()
    connector = TCPConnector(resolver=resolver)
    session = ClientSession(connector=connector)
    exchange.session = session

    try:
        print("Connecting to Bitget...")
        mode = await detect_balance_mode(exchange)
        print(f"  balance mode: {mode}")

        balance_data = {}
        positions_data = []
        open_orders_data = []
        trades_data = []
        transactions_data = []
        accounting_md: str | None = None
        acc_cfg = load_accounting_config()

        if sync_all or args.balance:
            print("Fetching balance...")
            balance_data = await fetch_balance(exchange, mode)
            save("balances.json", balance_data)
            append_balance_snapshot(balance_data)

        if sync_all and balance_data and not args.no_funding:
            print("Fetching USDT deposits / withdrawals (paginated)...")
            deposits_raw, withdrawals_raw, funding_err = await fetch_usdt_deposits_and_withdrawals(
                exchange
            )
            summary = build_funding_summary(
                deposits_raw,
                withdrawals_raw,
                float(balance_data["total"]),
                acc_cfg["mental_bankroll_usd"],
                acc_cfg["r_unit_usd"],
            )
            funding_payload = {
                "updated_at": balance_data.get("synced_at"),
                "deposits": [_serialize_funding_tx(t) for t in deposits_raw],
                "withdrawals": [_serialize_funding_tx(t) for t in withdrawals_raw],
                "summary": summary,
                "api_error": funding_err,
            }
            save("funding.json", funding_payload)
            accounting_md = generate_accounting_md(
                summary,
                funding_err,
                acc_cfg["mental_bankroll_usd"],
                acc_cfg["r_unit_usd"],
            )
            save("accounting.md", accounting_md)

        if sync_all or args.positions:
            print("Fetching positions...")
            positions_data = await fetch_positions(exchange, mode)
            save("positions.json", positions_data)

        if sync_all or args.orders:
            print("Fetching open/pending orders...")
            open_orders_data = await fetch_open_orders(exchange, mode, limit=100)
            save("open_orders.json", open_orders_data)

        if sync_all or args.trades:
            print("Fetching closed-order history...")
            trades_data = await fetch_trades(exchange, mode, limit=50)
            save("trades.json", trades_data)

        if sync_all or args.tx:
            print("Fetching transaction history...")
            transactions_data = await fetch_transactions(exchange, mode, limit=200)
            save("transactions.json", transactions_data)

        if sync_all:
            print("Generating snapshot...")
            snapshot = generate_snapshot(
                balance_data,
                positions_data,
                open_orders_data,
                trades_data,
                transactions_data,
                accounting_md=accounting_md,
            )
            save("snapshot.md", snapshot)

        print("Sync complete.")

    finally:
        await exchange.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Bitget exchange data")
    parser.add_argument("--balance", action="store_true", help="Sync balance only")
    parser.add_argument("--positions", action="store_true", help="Sync positions only")
    parser.add_argument("--orders", action="store_true", help="Sync open/pending orders only")
    parser.add_argument("--trades", action="store_true", help="Sync closed-order history only")
    parser.add_argument("--tx", action="store_true", help="Sync fill-level transaction history only")
    parser.add_argument(
        "--no-funding",
        action="store_true",
        help="Skip USDT deposit/withdrawal fetch and accounting files (faster)",
    )
    args = parser.parse_args()
    asyncio.run(main(args))
