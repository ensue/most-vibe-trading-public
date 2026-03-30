"""
R:R unlock ladder — planned reward:risk ceiling by promotion tier.

State file: system/risk_reward_unlock.json
Docs: system/risk_reward_unlock.md
"""

from __future__ import annotations

import json
from pathlib import Path

_SYSTEM_DIR = Path(__file__).resolve().parent
_STATE_PATH = _SYSTEM_DIR / "risk_reward_unlock.json"
_EXAMPLE_PATH = _SYSTEM_DIR / "risk_reward_unlock.example.json"


def _read_state() -> dict:
    if _STATE_PATH.exists():
        return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    if _EXAMPLE_PATH.exists():
        return json.loads(_EXAMPLE_PATH.read_text(encoding="utf-8"))
    return {}


def load_rr_unlock() -> dict:
    """Return merged ladder state (see risk_reward_unlock.md)."""
    return _read_state()


def planned_max_rr(*, entry: float, stop: float, take_profits: list[float], side: str) -> float:
    """
    Max planned R:R across TP legs. Long: risk = entry - stop. Short: risk = stop - entry.
    """
    side_l = side.lower()
    if side_l not in ("long", "short"):
        raise ValueError("side must be 'long' or 'short'")
    if not take_profits:
        raise ValueError("take_profits must be non-empty")

    if side_l == "long":
        risk = entry - stop
        if risk <= 0:
            raise ValueError("long: need stop < entry")
        ratios = [(tp - entry) / risk for tp in take_profits]
    else:
        risk = stop - entry
        if risk <= 0:
            raise ValueError("short: need stop > entry")
        ratios = [(entry - tp) / risk for tp in take_profits]

    return max(ratios)


def max_unlocked_rr(state: dict | None = None) -> float:
    """Current ceiling for planned max R:R (e.g. 1.0 means 1:1)."""
    s = state if state is not None else load_rr_unlock()
    return float(s.get("current_unlocked_max_rr", 1))


def validate_plan_rr(planned_max_rr: float, state: dict | None = None) -> tuple[bool, str]:
    """Returns (ok, message)."""
    cap = max_unlocked_rr(state)
    if planned_max_rr <= cap + 1e-9:
        return True, f"Planned max R:R {planned_max_rr:.4g} within unlock cap {cap:.4g}"
    return (
        False,
        f"Planned max R:R {planned_max_rr:.4g} exceeds unlock cap {cap:.4g} — revise TP(s) or unlock tier",
    )


def apply_promotion_if_ready(state: dict) -> dict:
    """When wins >= required, promote tier (may repeat if wins carry over)."""
    out = dict(state)
    req = int(out.get("promotion_wins_required", 5))
    wins = int(out.get("wins_toward_next_unlock", 0))
    ceiling = int(out.get("ceiling_max_rr", 20))
    cur = int(out.get("current_unlocked_max_rr", 1))
    while wins >= req and cur < ceiling:
        wins -= req
        cur += 1
    out["wins_toward_next_unlock"] = wins
    out["current_unlocked_max_rr"] = cur
    return out


def increment_win(state: dict) -> dict:
    """Add one promotion win and apply promotion rules."""
    out = dict(state)
    out["wins_toward_next_unlock"] = int(out.get("wins_toward_next_unlock", 0)) + 1
    return apply_promotion_if_ready(out)


def save_state(state: dict) -> None:
    path = _STATE_PATH
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
