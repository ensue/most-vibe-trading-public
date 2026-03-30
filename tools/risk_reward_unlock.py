"""
CLI for R:R unlock ladder (system/risk_reward_unlock.json).

Usage (repo root on PYTHONPATH, e.g. `most/` or template root):

  python tools/risk_reward_unlock.py status
  python tools/risk_reward_unlock.py record-win
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from system.rr_unlock import increment_win, load_rr_unlock, save_state  # noqa: E402


def _status() -> None:
    s = load_rr_unlock()
    cap = s.get("current_unlocked_max_rr", 1)
    wins = s.get("wins_toward_next_unlock", 0)
    req = s.get("promotion_wins_required", 5)
    ceiling = s.get("ceiling_max_rr", 20)
    print(json.dumps(s, indent=2, ensure_ascii=False))
    print(f"\nUnlock cap: {cap}:1 | Progress: {wins}/{req} wins toward next | Ceiling: {ceiling}:1")


def _record_win() -> None:
    s = load_rr_unlock()
    before = int(s.get("current_unlocked_max_rr", 1))
    s = increment_win(s)
    s["updated_at"] = datetime.now(timezone.utc).isoformat()
    after = int(s.get("current_unlocked_max_rr", 1))
    save_state(s)
    print(f"Recorded win. Tier: {before}:1 -> {after}:1. Progress: {s.get('wins_toward_next_unlock')}/{s.get('promotion_wins_required', 5)}")
    _status()


def main() -> None:
    p = argparse.ArgumentParser(description="R:R unlock ladder")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="Show ladder JSON summary")
    sub.add_parser("record-win", help="Increment promotion win counter (after compliant journal)")
    args = p.parse_args()
    if args.cmd == "status":
        _status()
    elif args.cmd == "record-win":
        _record_win()


if __name__ == "__main__":
    main()
