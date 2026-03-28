"""
Unified calibration: mental bankroll, R unit (dollar risk per R), optional extras.

Used by exchange sync (accounting) and any tool that needs the same numbers as the AI.
Priority: vault env > exchange/accounting_config.json > system/calibration.json > example files.

Import from repository root (parent of ``system/`` on ``sys.path``): ``from system.calibration import load_calibration``
"""

from __future__ import annotations

import json
from pathlib import Path

_MOST_ROOT = Path(__file__).resolve().parent.parent
EXCHANGE_DIR = _MOST_ROOT / "exchange"
SYSTEM_DIR = _MOST_ROOT / "system"
VAULT_CANDIDATES = [
    _MOST_ROOT / "vault" / "bitget-api.env",
    _MOST_ROOT.parent / "vault" / "bitget-api.env",
    Path.cwd() / "vault" / "bitget-api.env",
]


def _read_json_merged(example_path: Path, override_path: Path) -> dict:
    raw: dict = {}
    if example_path.exists():
        raw = json.loads(example_path.read_text(encoding="utf-8"))
    if override_path.exists():
        raw = {**raw, **json.loads(override_path.read_text(encoding="utf-8"))}
    for k in list(raw.keys()):
        if k.startswith("_"):
            del raw[k]
    return raw


def _f(raw: dict, key: str) -> float | None:
    v = raw.get(key)
    if v is None or v == "":
        return None
    return float(v)


def load_calibration() -> dict:
    """
    Returns at least: mental_bankroll_usd, r_unit_usd, currency,
    intervention_recovery_weeks_per_trade_estimate (optional).
    """
    try:
        from dotenv import dotenv_values
    except ImportError:
        dotenv_values = None  # type: ignore

    acc = _read_json_merged(
        EXCHANGE_DIR / "accounting_config.example.json",
        EXCHANGE_DIR / "accounting_config.json",
    )
    sys_cal = _read_json_merged(
        SYSTEM_DIR / "calibration.example.json",
        SYSTEM_DIR / "calibration.json",
    )

    mental = _f(acc, "mental_bankroll_usd")
    r_unit = _f(acc, "r_unit_usd")

    if sys_cal.get("mental_bankroll_usd") is not None:
        mental = _f(sys_cal, "mental_bankroll_usd")
    if sys_cal.get("r_unit_usd") is not None:
        r_unit = _f(sys_cal, "r_unit_usd")

    if dotenv_values:
        for vault in VAULT_CANDIDATES:
            if not vault.exists():
                continue
            env = dotenv_values(vault)
            if (env.get("MOST_R_UNIT_USD") or "").strip():
                r_unit = float(env["MOST_R_UNIT_USD"].strip())
            if (env.get("MOST_MENTAL_BANKROLL_USD") or "").strip():
                mental = float(env["MOST_MENTAL_BANKROLL_USD"].strip())
            break

    currency = sys_cal.get("currency") or "USD"
    if not isinstance(currency, str):
        currency = "USD"

    recovery_weeks = sys_cal.get("intervention_recovery_weeks_per_trade_estimate")
    if recovery_weeks is not None:
        try:
            recovery_weeks = float(recovery_weeks)
        except (TypeError, ValueError):
            recovery_weeks = None

    return {
        "mental_bankroll_usd": mental,
        "r_unit_usd": r_unit,
        "currency": currency,
        "intervention_recovery_weeks_per_trade_estimate": recovery_weeks,
    }


def load_accounting_config() -> dict[str, float | None]:
    """Backward-compatible subset for exchange/sync.py accounting blocks."""
    c = load_calibration()
    return {
        "mental_bankroll_usd": c["mental_bankroll_usd"],
        "r_unit_usd": c["r_unit_usd"],
    }
