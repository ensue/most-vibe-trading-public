"""
Exchange data sync (default: Bitget futures).

Pulls balances, open positions, and recent trade history via **ccxt**
and stores them as JSON + a human-readable snapshot.

MOST is not Bitget-only: ccxt supports many CEXes. To run on Binance USDM,
Bybit, OKX, etc., fork this file — swap the exchange class, constructor
options, and balance/position params. See `exchange/README.md`.

Usage:
    python exchange/sync.py              # sync everything
    python exchange/sync.py --balance    # balance only
    python exchange/sync.py --positions  # positions only
    python exchange/sync.py --orders     # open/pending orders only
    python exchange/sync.py --trades     # trade history only

Credentials (default): workspace `vault/bitget-api.env` (see VAULT_CANDIDATES in this file).
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


def generate_snapshot(balance: dict, positions: list, open_orders: list, trades: list) -> str:
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
    sync_all = not (args.balance or args.positions or args.orders or args.trades)

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

        if sync_all or args.balance:
            print("Fetching balance...")
            balance_data = await fetch_balance(exchange, mode)
            save("balances.json", balance_data)

        if sync_all or args.positions:
            print("Fetching positions...")
            positions_data = await fetch_positions(exchange, mode)
            save("positions.json", positions_data)

        if sync_all or args.orders:
            print("Fetching open/pending orders...")
            open_orders_data = await fetch_open_orders(exchange, mode, limit=100)
            save("open_orders.json", open_orders_data)

        if sync_all or args.trades:
            print("Fetching trade history...")
            trades_data = await fetch_trades(exchange, mode, limit=50)
            save("trades.json", trades_data)

        if sync_all:
            print("Generating snapshot...")
            snapshot = generate_snapshot(balance_data, positions_data, open_orders_data, trades_data)
            save("snapshot.md", snapshot)

        print("Sync complete.")

    finally:
        await exchange.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Bitget exchange data")
    parser.add_argument("--balance", action="store_true", help="Sync balance only")
    parser.add_argument("--positions", action="store_true", help="Sync positions only")
    parser.add_argument("--orders", action="store_true", help="Sync open/pending orders only")
    parser.add_argument("--trades", action="store_true", help="Sync trade history only")
    args = parser.parse_args()
    asyncio.run(main(args))
