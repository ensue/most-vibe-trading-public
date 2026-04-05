"""
Set **isolated** margin and matching leverage on **long** and **short** for Bitget USDT-M perpetuals.

Uses the same vault credentials as `sync.py` (`vault/bitget-api.env`).
Uses the same aiohttp **ThreadedResolver** session wiring as `sync.py` so Windows
does not fail with `aiodns` / “Could not contact DNS servers”.

Per symbol (mix / non-UTA account):
  1. `set_margin_mode('isolated', symbol)`
  2. `set_leverage` with `holdSide: long`
  3. `set_leverage` with `holdSide: short`

UTA accounts: margin mode is skipped (ccxt Bitget `set_margin_mode` is mix-only); leverage uses
`uta=True` and `posSide` **long** / **short** per ccxt.

If Bitget returns **40014** “need future pos write permissions”, enable **Futures / position write**
on the API key in the Bitget console — this is not something the script can bypass.

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


async def configure_symbol(
    exchange: ccxt.bitget,
    leverage: int,
    symbol: str,
    *,
    uta: bool,
    dry_run: bool,
) -> tuple[str, str | None]:
    if dry_run:
        return symbol, None
    margin_warn: str | None = None
    if not uta:
        try:
            await exchange.set_margin_mode("isolated", symbol)
        except ccxt.BaseError as e:
            margin_warn = str(e)

    if uta:
        sides: tuple[tuple[str, dict], ...] = (
            ("long", {"uta": True, "posSide": "long"}),
            ("short", {"uta": True, "posSide": "short"}),
        )
    else:
        sides = (
            ("long", {"holdSide": "long"}),
            ("short", {"holdSide": "short"}),
        )
    lev_errs: list[str] = []
    for label, params in sides:
        try:
            await exchange.set_leverage(leverage, symbol, params)
        except ccxt.BaseError as e:
            lev_errs.append(f"{label}:{e}")
    if lev_errs:
        bits = ([f"margin_mode:{margin_warn}"] if margin_warn else []) + lev_errs
        return symbol, " | ".join(bits)
    if margin_warn:
        print(f"WARN {symbol} margin_mode: {margin_warn} (leverage long/short OK)", file=sys.stderr)
    return symbol, None


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
            print(
                f"Markets: {len(symbols)} USDT perpetuals — would set "
                f"isolated + {args.leverage}x long + {args.leverage}x short (dry-run)",
            )
            for s in symbols:
                print(f"  [dry-run] {s}")
            return 0
        mode = await detect_balance_mode(exchange)
        uta = mode == "uta"
        print(f"Account mode: {mode} (uta={uta})")
        if uta:
            print(
                "Note: UTA — ccxt cannot set isolated margin here; leverage uses posSide long/short. "
                "Set isolated in Bitget UI per contract if required.",
                file=sys.stderr,
            )
        print(
            f"Per symbol: isolated margin (mix) + {args.leverage}x long + {args.leverage}x short",
        )
        print(f"Markets to update: {len(symbols)} USDT perpetuals")
        ok = 0
        fail = 0
        for sym in symbols:
            _, err = await configure_symbol(exchange, args.leverage, sym, uta=uta, dry_run=False)
            if err is None:
                print(f"OK  {args.leverage}x L/S isolated {sym}")
                ok += 1
            else:
                print(f"ERR {sym}: {err}", file=sys.stderr)
                fail += 1
        print(f"Done. OK={ok} ERR={fail}")
        return 0 if fail == 0 else 2
    finally:
        await exchange.close()


def main() -> None:
    p = argparse.ArgumentParser(
        description="Set isolated margin and leverage on long+short for Bitget USDT perpetuals",
    )
    p.add_argument("--leverage", type=int, default=30, help="Leverage for both sides (default: 30)")
    p.add_argument("--dry-run", action="store_true", help="List symbols only, no API writes")
    p.add_argument("--symbol", type=str, default=None, help="Single symbol, e.g. NEAR/USDT:USDT")
    args = p.parse_args()
    if args.leverage < 1:
        print("ERROR: leverage must be >= 1", file=sys.stderr)
        sys.exit(1)
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
