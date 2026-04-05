"""
Set leverage on Bitget USDT-M perpetual (swap) markets.

Uses the same vault credentials as `sync.py` (`vault/bitget-api.env`).
Uses the same aiohttp **ThreadedResolver** session wiring as `sync.py` so Windows
does not fail with `aiodns` / “Could not contact DNS servers”.

Calls ccxt `set_leverage` per symbol. Bitget does not expose a single
“all symbols” call in ccxt; some pairs may reject the target leverage (max tier) or fail if
you have open positions/orders on that symbol.

Usage:
    python exchange/set_leverage_all.py
    python exchange/set_leverage_all.py --dry-run
    python exchange/set_leverage_all.py --leverage 25 --symbol NEAR/USDT:USDT
"""

from __future__ import annotations

import argparse
import asyncio
import sys
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


def load_credentials() -> dict[str, str]:
    for path in VAULT_CANDIDATES:
        if path.exists():
            env = dotenv_values(path)
            return {
                "api_key": (env.get("BITGET_API_KEY") or "").strip(),
                "api_secret": (env.get("BITGET_API_SECRET") or "").strip(),
                "passphrase": (env.get("BITGET_PASSPHRASE") or "").strip(),
            }
    print(f"ERROR: vault/bitget-api.env not found. Searched: {VAULT_CANDIDATES}", file=sys.stderr)
    sys.exit(1)


def create_exchange(creds: dict[str, str]) -> ccxt.bitget:
    return ccxt.bitget(
        {
            "apiKey": creds["api_key"],
            "secret": creds["api_secret"],
            "password": creds["passphrase"],
            "options": {"defaultType": "swap"},
            "enableRateLimit": True,
        }
    )


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
        print(f"ERROR: Cannot connect to Bitget. Check API credentials. Details: {e}", file=sys.stderr)
        sys.exit(1)


def usdt_swap_symbols(markets: dict) -> list[str]:
    out: list[str] = []
    for symbol, m in markets.items():
        if not m.get("active"):
            continue
        if m.get("type") != "swap":
            continue
        if m.get("quote") != "USDT":
            continue
        if not m.get("linear", True):
            continue
        out.append(symbol)
    return sorted(out)


async def set_one(
    exchange: ccxt.bitget,
    leverage: int,
    symbol: str,
    *,
    uta: bool,
    dry_run: bool,
) -> tuple[str, str | None]:
    params = {"uta": True} if uta else {}
    if dry_run:
        return symbol, None
    try:
        await exchange.set_leverage(leverage, symbol, params)
        return symbol, None
    except ccxt.BaseError as e:
        return symbol, str(e)


async def run(args: argparse.Namespace) -> int:
    creds = load_credentials()
    exchange = create_exchange(creds)
    resolver = ThreadedResolver()
    connector = TCPConnector(resolver=resolver)
    session = ClientSession(connector=connector)
    exchange.session = session
    try:
        await exchange.load_markets()
        symbols = usdt_swap_symbols(exchange.markets)
        if args.symbol:
            if args.symbol not in exchange.markets:
                print(f"ERROR: Unknown symbol {args.symbol!r}", file=sys.stderr)
                return 1
            symbols = [args.symbol]
        if args.dry_run:
            print(f"Markets to update: {len(symbols)} USDT perpetuals (dry-run, no writes)")
            for s in symbols:
                print(f"  [dry-run] would set {args.leverage}x {s}")
            return 0
        mode = await detect_balance_mode(exchange)
        uta = mode == "uta"
        print(f"Account mode: {mode} (uta={uta})")
        print(f"Markets to update: {len(symbols)} USDT perpetuals")
        ok = 0
        fail = 0
        for sym in symbols:
            _, err = await set_one(exchange, args.leverage, sym, uta=uta, dry_run=False)
            if err is None:
                print(f"OK  {args.leverage}x {sym}")
                ok += 1
            else:
                print(f"ERR {sym}: {err}", file=sys.stderr)
                fail += 1
        print(f"Done. OK={ok} ERR={fail}")
        return 0 if fail == 0 else 2
    finally:
        await exchange.close()


def main() -> None:
    p = argparse.ArgumentParser(description="Set leverage on all Bitget USDT perpetuals")
    p.add_argument("--leverage", type=int, default=30, help="Leverage (default: 30)")
    p.add_argument("--dry-run", action="store_true", help="List symbols only, no API writes")
    p.add_argument("--symbol", type=str, default=None, help="Single symbol, e.g. NEAR/USDT:USDT")
    args = p.parse_args()
    if args.leverage < 1:
        print("ERROR: leverage must be >= 1", file=sys.stderr)
        sys.exit(1)
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
