"""
Bitget exchange data sync.

Pulls balances, open positions, and recent trade history from Bitget
via ccxt and stores them as JSON + a human-readable snapshot.

Usage:
    python exchange/sync.py              # sync everything
    python exchange/sync.py --balance    # balance only
    python exchange/sync.py --positions  # positions only
    python exchange/sync.py --trades     # trade history only

Credentials loaded from ../vault/bitget-api.env
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import ccxt.async_support as ccxt
from dotenv import dotenv_values

VAULT_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "vault" / "bitget-api.env",
    Path.cwd().parent / "vault" / "bitget-api.env",
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


def generate_snapshot(balance: dict, positions: list, trades: list) -> str:
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
    sync_all = not (args.balance or args.positions or args.trades)

    creds = load_credentials()
    exchange = create_exchange(creds)

    try:
        print("Connecting to Bitget...")
        mode = await detect_balance_mode(exchange)
        print(f"  balance mode: {mode}")

        balance_data = {}
        positions_data = []
        trades_data = []

        if sync_all or args.balance:
            print("Fetching balance...")
            balance_data = await fetch_balance(exchange, mode)
            save("balances.json", balance_data)

        if sync_all or args.positions:
            print("Fetching positions...")
            positions_data = await fetch_positions(exchange, mode)
            save("positions.json", positions_data)

        if sync_all or args.trades:
            print("Fetching trade history...")
            trades_data = await fetch_trades(exchange, mode, limit=50)
            save("trades.json", trades_data)

        if sync_all:
            print("Generating snapshot...")
            snapshot = generate_snapshot(balance_data, positions_data, trades_data)
            save("snapshot.md", snapshot)

        print("Sync complete.")

    finally:
        await exchange.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Bitget exchange data")
    parser.add_argument("--balance", action="store_true", help="Sync balance only")
    parser.add_argument("--positions", action="store_true", help="Sync positions only")
    parser.add_argument("--trades", action="store_true", help="Sync trade history only")
    args = parser.parse_args()
    asyncio.run(main(args))
