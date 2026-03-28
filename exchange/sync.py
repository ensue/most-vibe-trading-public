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
    python exchange/sync.py --no-ledger  # full sync but skip swap ledger / balance timeline (faster)
    python exchange/sync.py --ledger-full-history  # ledger: all 90-day windows (slow; default = last 90d)
    python exchange/sync.py --closed-orders-full   # all closed swap orders (paginated)

Credentials (default): workspace `vault/bitget-api.env` (see VAULT_CANDIDATES in this file).

Accounting:
    Each successful sync appends `data/balance_history.jsonl`. Full sync also pulls all-time
    USDT `fetch_deposits` / `fetch_withdrawals` (ccxt paginate) and writes `data/funding.json`
    plus `data/accounting.md`. **R labels** are optional: set `exchange/accounting_config.json`
    (copy from `accounting_config.example.json`) or `MOST_R_UNIT_USD` / `MOST_MENTAL_BANKROLL_USD`
    in vault — no hardcoded dollar amounts in this script.

Balance timeline (swap USDT):
    Full sync fetches **futures account bills** (`fetch_ledger`, USDT-M), walks 90-day windows,
    reconciles **backward** from current swap balance so each row has **balance_after_usdt** for
    that bill (trade PnL, fees, funding, transfers). Writes `data/balance_timeline.jsonl` and
    `data/balance_timeline.md`. Not identical to “one row per order” if one order has multiple
    fills/bills — use `order_id` / `bill_id` from raw `info` when the API provides them.
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


def _parse_float_field(v) -> float | None:
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() == "null":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def realized_pnl_from_bitget_order_info(info: dict) -> float | None:
    """
    Bitget swap order history includes realized PnL on **close** fills in raw `info`.
    CCXT does not normalize this field; read common keys (mix + UTA).
    """
    if not info:
        return None
    for key in (
        "totalProfits",
        "totalprofits",
        "cumProfit",
        "cum_profit",
        "profit",
        "realizedPnl",
        "realizedPnl",
    ):
        p = _parse_float_field(info.get(key))
        if p is not None:
            return p
    return None


def generate_closed_orders_pnl_md(trades: list[dict]) -> str:
    """One markdown table: every closed swap order row with realized PnL when the API provides it."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Closed swap orders (realized PnL)",
        "",
        f"Generated: {ts}",
        "",
        "Source: Bitget **closed order history** via ccxt `fetch_closed_orders` (`type=swap`). "
        "**Realized PnL** is read from raw order `info` (e.g. `totalProfits`) when present — "
        "typically **non-zero on closes** (`tradeSide=close` / reduce-only); opens often show `0` or empty.",
        "",
        "| Time | Order ID | Symbol | Side | tradeSide | posSide | Type | Price | Amount | Fee (USDT) | Realized PnL (USDT) |",
        "|------|----------|--------|------|-----------|---------|------|-------|--------|------------|---------------------|",
    ]
    for t in trades:
        dt = t.get("datetime") or "—"
        if isinstance(dt, str) and len(dt) > 19:
            dt = dt[:19]
        oid = str(t.get("id") or "—")
        pnl = t.get("realized_pnl")
        pnl_s = f"{pnl:,.4f}" if isinstance(pnl, (int, float)) else "—"
        lines.append(
            f"| {dt} | {oid} | {t.get('symbol', '—')} | {t.get('side', '—')} | "
            f"{t.get('trade_side', '—')} | {t.get('pos_side', '—')} | {t.get('type', '—')} | "
            f"${t.get('price', 0):,.4f} | {t.get('amount', 0)} | ${t.get('fee', 0):,.4f} | {pnl_s} |"
        )
    lines.append("")
    return "\n".join(lines)


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


async def fetch_trades(
    exchange: ccxt.bitget,
    mode: str,
    limit: int = 100,
    paginate: bool = False,
) -> list[dict]:
    params: dict = {"type": "swap"}
    if mode == "uta":
        params["uta"] = True
    if paginate:
        params["paginate"] = True

    try:
        orders = await exchange.fetch_closed_orders(None, None, limit, params)
    except ccxt.BaseError as e:
        print(f"  WARNING: fetch_closed_orders failed: {e}")
        return []

    result = []
    for o in orders:
        if o["status"] != "closed":
            continue
        info = o.get("info") or {}
        rp = realized_pnl_from_bitget_order_info(info)
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
            "realized_pnl": rp,
            "trade_side": str(info.get("tradeSide") or info.get("trade_side") or "—"),
            "pos_side": str(info.get("posSide") or info.get("holdSide") or "—"),
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
    except ccxt.BaseError as e:
        print(f"  WARNING: fetch_my_trades failed: {e}")
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


def _bill_to_ledger_entry_v2(b: dict) -> dict:
    """Bitget v2 `data.bills[]` row (mix account bill)."""
    ts = int(b.get("cTime") or 0)
    dt = None
    if ts:
        dt = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    bal_raw = b.get("balance")
    after = float(bal_raw) if bal_raw not in (None, "") else None
    return {
        "id": str(b.get("billId") or ""),
        "timestamp": ts,
        "datetime": dt,
        "type": b.get("businessType"),
        "direction": None,
        "amount": None,
        "after": after,
        "fee": {"cost": float(b.get("fee") or 0)},
        "info": b,
    }


# v2 `/api/v2/mix/account/bill` requires a valid `businessType` filter (bare request → 40020).
# Query each category and merge (dedupe by billId). Extend if you need niche types.
_V2_BUSINESS_TYPES: tuple[str, ...] = (
    "open_long",
    "close_long",
    "open_short",
    "close_short",
    "force_close_long",
    "force_close_short",
    "burst_long_loss_query",
    "burst_short_loss_query",
    "trans_to_exchange",
    "trans_from_exchange",
    "trans_to_cross",
    "trans_from_cross",
    "transfer_in",
    "transfer_out",
    "contract_settle_fee",
    "buy",
    "sell",
    "append_margin",
    "reduce_margin",
    "auto_append_margin",
)


async def _fetch_ledger_pages_in_window(
    exchange: ccxt.bitget,
    start_ms: int,
    end_ms: int,
) -> list:
    """
    Bitget v2 `GET /api/v2/mix/account/bill` — one query per `businessType`, paginate `idLessThan`.
    """
    window_rows: list = []
    seen_local: set[str] = set()
    for biz in _V2_BUSINESS_TYPES:
        cursor: str | None = None
        while True:
            request: dict = {
                "coin": "USDT",
                "productType": "USDT-FUTURES",
                "startTime": start_ms,
                "endTime": end_ms,
                "limit": 100,
                "businessType": biz,
            }
            if cursor:
                request["idLessThan"] = cursor
            try:
                response = await exchange.privateMixGetV2MixAccountBill(request)
            except ccxt.BaseError:
                break
            code = response.get("code")
            if code and str(code) != "00000":
                break
            bills = (response.get("data") or {}).get("bills") or []
            if not bills:
                break
            for b in bills:
                bid = str(b.get("billId") or "")
                if bid and bid in seen_local:
                    continue
                if bid:
                    seen_local.add(bid)
                window_rows.append(_bill_to_ledger_entry_v2(b))
            if len(bills) < 100:
                break
            cursor = str(bills[-1].get("billId") or "")
            if not cursor:
                break
    return window_rows


async def fetch_swap_usdt_ledger_windowed(
    exchange: ccxt.bitget,
    full_history: bool = False,
) -> tuple[list, str | None]:
    """
    USDT-M futures account bills. Default: **last 90 days** only (fast).
    With `full_history`, walk backward in 90-day windows (same cap as funding).
    """
    merged: list = []
    seen: set[str] = set()
    end_ms = exchange.milliseconds()
    last_err: str | None = None
    max_windows = _MAX_FUNDING_WINDOWS if full_history else 1
    for _ in range(max_windows):
        start_ms = max(1, end_ms - _NINETY_DAYS_MS)
        try:
            chunk = await _fetch_ledger_pages_in_window(exchange, start_ms, end_ms)
        except ccxt.BaseError as e:
            last_err = str(e)
            break
        for t in chunk:
            tid = str(t.get("id") or "")
            if tid and tid in seen:
                continue
            if tid:
                seen.add(tid)
            merged.append(t)
        if not full_history:
            break
        if start_ms <= 1:
            break
        end_ms = start_ms - 1
    merged.sort(key=lambda x: x.get("timestamp") or 0)
    return merged, last_err


def ledger_net_usdt_delta(entry: dict) -> float:
    """Signed USDT change from one v2 bill (`amount` in raw info; fee separate)."""
    info = entry.get("info") or {}
    raw = info.get("amount")
    if raw is None:
        raw = info.get("size")
    if raw is not None:
        return float(raw)
    amt = float(entry.get("amount") or 0)
    fee_d = entry.get("fee") or {}
    fee = float(fee_d.get("cost") if isinstance(fee_d, dict) else fee_d or 0)
    if entry.get("direction") == "in":
        return amt - fee
    return -(amt + fee)


def extract_bill_meta(entry: dict) -> dict:
    info = entry.get("info") or {}
    sym = (
        info.get("symbol")
        or info.get("symbolName")
        or ""
    )
    biz = info.get("businessType") or ""
    oid = (
        info.get("orderId")
        or info.get("order_id")
        or info.get("tradeId")
        or info.get("trade_id")
        or ""
    )
    return {"symbol": sym, "business_type": biz, "order_ref": str(oid) if oid else ""}


def serialize_ledger_entry(entry: dict) -> dict:
    fee = entry.get("fee")
    fee_cost = float(fee.get("cost") if isinstance(fee, dict) else fee or 0)
    return {
        "id": entry.get("id"),
        "timestamp": entry.get("timestamp"),
        "datetime": entry.get("datetime"),
        "type": entry.get("type"),
        "direction": entry.get("direction"),
        "amount": entry.get("amount"),
        "after": entry.get("after"),
        "fee": fee_cost,
        "info": entry.get("info"),
    }


def build_balance_timeline_rows(
    ledger_entries: list,
    current_swap_usdt_total: float,
) -> tuple[list[dict], dict]:
    """
    Prefer Bitget `balance` on each bill when present; else reconcile backward from current
    swap total. Rows are chronological (oldest first).
    """
    ct = float(current_swap_usdt_total)
    if not ledger_entries:
        return [], {
            "rows": 0,
            "sum_delta": 0.0,
            "implied_balance_before_oldest": ct,
            "current_swap_usdt_total": ct,
            "balance_source": "none",
        }

    sorted_e = sorted(ledger_entries, key=lambda x: x.get("timestamp") or 0)
    use_api_balance = all(e.get("after") is not None for e in sorted_e)

    rows: list[dict] = []
    if use_api_balance:
        for e in sorted_e:
            delta = ledger_net_usdt_delta(e)
            meta = extract_bill_meta(e)
            rows.append({
                "bill_id": str(e.get("id") or ""),
                "timestamp": e.get("timestamp"),
                "datetime": e.get("datetime"),
                "type": e.get("type"),
                "delta_usdt": round(delta, 8),
                "balance_after_usdt": round(float(e["after"]), 8),
                "symbol": meta["symbol"],
                "business_type": meta["business_type"],
                "order_ref": meta["order_ref"],
            })
        sum_delta = sum(float(r["delta_usdt"]) for r in rows)
        return rows, {
            "rows": len(rows),
            "sum_delta": round(sum_delta, 8),
            "implied_balance_before_oldest": None,
            "current_swap_usdt_total": round(ct, 8),
            "balance_source": "api_bill_balance",
        }

    running_after = ct
    for i in range(len(sorted_e) - 1, -1, -1):
        e = sorted_e[i]
        delta = ledger_net_usdt_delta(e)
        meta = extract_bill_meta(e)
        rows.append({
            "bill_id": str(e.get("id") or ""),
            "timestamp": e.get("timestamp"),
            "datetime": e.get("datetime"),
            "type": e.get("type"),
            "delta_usdt": round(delta, 8),
            "balance_after_usdt": round(running_after, 8),
            "symbol": meta["symbol"],
            "business_type": meta["business_type"],
            "order_ref": meta["order_ref"],
        })
        running_after = running_after - delta
    rows.reverse()
    sum_delta = sum(float(r["delta_usdt"]) for r in rows)
    return rows, {
        "rows": len(rows),
        "sum_delta": round(sum_delta, 8),
        "implied_balance_before_oldest": round(running_after, 8),
        "current_swap_usdt_total": round(ct, 8),
        "balance_source": "reconciled_backward",
    }


def build_balance_timeline_md(rows: list[dict], stats: dict, ledger_err: str | None) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Balance timeline (USDT swap wallet)",
        "",
        f"Generated: {ts}",
        "",
        "Source: Bitget **mix account `/v2/mix/account/bill`** (USDT-M). Each row is one **account bill** "
        "(not always 1:1 with a single parent order — see `order_ref`). "
        "`balance_after_usdt` uses **exchange `balance`** on the bill when present; otherwise it is "
        "**reconciled backward** from current swap `fetch_balance`.",
        "",
    ]
    if ledger_err:
        lines.extend(["**Ledger / bill API error:** " + ledger_err, ""])
    imb = stats.get("implied_balance_before_oldest")
    imb_line = f"${imb:,.2f}" if imb is not None else "— (API balance on each bill)"
    lines.extend([
        "## Reconciliation",
        "",
        f"- **Rows (bills):** {stats.get('rows', 0)}",
        f"- **Balance column source:** `{stats.get('balance_source', '—')}`",
        f"- **Sum of `delta_usdt`:** {stats.get('sum_delta', 0)}",
        f"- **Implied balance before oldest bill** (reconciled mode only): {imb_line}",
        f"- **Current swap total (this sync):** ${stats.get('current_swap_usdt_total', 0):,.2f}",
        "",
        "_Reconciled mode: if “before oldest” looks wrong, the bill chain may be incomplete in the "
        "fetched time windows._",
        "",
        "## Rows (chronological, oldest → newest)",
        "",
    ])
    show = rows[-500:] if len(rows) > 500 else rows
    if len(rows) > 500:
        lines.append(f"_Showing last **500** of **{len(rows)}** rows. Full list: `balance_timeline.jsonl`._")
        lines.append("")
    lines.extend([
        "| Time | Bill ID | Δ USDT | Balance after | Type | Symbol | businessType | Order ref |",
        "|------|---------|--------|---------------|------|--------|--------------|-----------|",
    ])
    for r in show:
        dt = (r.get("datetime") or "")[:19]
        lines.append(
            f"| {dt} | {r.get('bill_id', '')[:12]}… | {r['delta_usdt']:.4f} | {r['balance_after_usdt']:.2f} "
            f"| {r.get('type', '')} | {r.get('symbol', '') or '—'} | {r.get('business_type', '') or '—'} | {r.get('order_ref', '') or '—'} |"
        )
    lines.append("")
    return "\n".join(lines)


def save_balance_timeline_jsonl(rows: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "balance_timeline.jsonl"
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )
    print(f"  saved {path.relative_to(Path(__file__).resolve().parent.parent)}")


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
    balance_timeline_md: str | None = None,
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
            "## Recent Closed Orders",
            "",
            "_Full table with the same rows: `data/closed_orders_pnl.md`._",
            "",
            "| Time | Symbol | Side | tradeSide | posSide | Type | Price | Amount | Fee | Realized PnL |",
            "|------|--------|------|-----------|---------|------|-------|--------|-----|--------------|",
        ])
        for t in trades[:50]:
            dt = t["datetime"] or "—"
            if len(dt) > 19:
                dt = dt[:19]
            pnl = t.get("realized_pnl")
            pnl_s = f"${pnl:,.4f}" if isinstance(pnl, (int, float)) else "—"
            lines.append(
                f"| {dt} | {t['symbol']} | {t['side']} | {t.get('trade_side', '—')} | {t.get('pos_side', '—')} "
                f"| {t['type']} | ${t['price']:,.4f} | {t['amount']} | ${t['fee']:,.4f} | {pnl_s} |"
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

    if balance_timeline_md:
        lines.extend(["", "---", "", balance_timeline_md.strip(), ""])

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
        balance_timeline_md: str | None = None
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

        if sync_all and balance_data and not args.no_ledger:
            print("Fetching swap USDT ledger (balance timeline)...")
            ledger_raw, ledger_err = await fetch_swap_usdt_ledger_windowed(
                exchange, full_history=args.ledger_full_history
            )
            save("ledger.json", [serialize_ledger_entry(x) for x in ledger_raw])
            t_rows, t_stats = build_balance_timeline_rows(
                ledger_raw, float(balance_data["total"])
            )
            save_balance_timeline_jsonl(t_rows)
            save(
                "balance_timeline_meta.json",
                {
                    "stats": t_stats,
                    "ledger_error": ledger_err,
                    "ledger_span": (
                        "full_90d_windows" if args.ledger_full_history else "last_90d_only"
                    ),
                },
            )
            balance_timeline_md = build_balance_timeline_md(t_rows, t_stats, ledger_err)
            save("balance_timeline.md", balance_timeline_md)

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
            trades_data = await fetch_trades(
                exchange,
                mode,
                limit=args.closed_orders_limit,
                paginate=args.closed_orders_full,
            )
            save("trades.json", trades_data)
            save("closed_orders_pnl.md", generate_closed_orders_pnl_md(trades_data))

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
                balance_timeline_md=balance_timeline_md,
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
    parser.add_argument(
        "--no-ledger",
        action="store_true",
        help="Skip futures ledger fetch and balance timeline files (faster)",
    )
    parser.add_argument(
        "--ledger-full-history",
        action="store_true",
        help="Ledger: walk all 90-day windows (slow); default is last 90 days only",
    )
    parser.add_argument(
        "--closed-orders-full",
        action="store_true",
        help="Closed swap orders: paginate until all history is fetched (more API calls)",
    )
    parser.add_argument(
        "--closed-orders-limit",
        type=int,
        default=100,
        metavar="N",
        help="Page size for closed orders (default 100; used as page size when --closed-orders-full)",
    )
    args = parser.parse_args()
    asyncio.run(main(args))
