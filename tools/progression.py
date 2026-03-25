"""
MOST progression scoring.

Process-first scoring: compliance, analysis quality, and execution hygiene.
PnL is context only (not a primary XP source).

Usage:
    python tools/progression.py
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYSTEM_DIR = ROOT / "system"
EXCHANGE_DIR = ROOT / "exchange" / "data"
JOURNAL_POSITIONS_SUMMARY = ROOT / "journal" / "positions" / "_summary.md"
CONTEXT_PATH = ROOT / "context.md"

STATE_PATH = SYSTEM_DIR / "progression_state.json"
REPORT_PATH = Path(__file__).resolve().parent / "progression_report.md"


LEVEL_THRESHOLDS = [0, 120, 280, 480, 730, 1030, 1380, 1780, 2230, 2730]
LEVEL_TITLES = [
    "Initiate",
    "Initiate",
    "Structured Trader",
    "Structured Trader",
    "Process Guardian",
    "Process Guardian",
    "Edge Operator",
    "Edge Operator",
    "Discipline Architect",
    "Discipline Architect",
]


@dataclass
class ScoreEvent:
    key: str
    xp: int
    reason: str


def read_json(path: Path, default: dict | list) -> dict | list:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_int(pattern: str, text: str, default: int = 0) -> int:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return default
    try:
        return int(m.group(1))
    except ValueError:
        return default


def current_level(total_xp: int) -> int:
    if total_xp < 0:
        return 1
    if total_xp < LEVEL_THRESHOLDS[-1]:
        for i in range(len(LEVEL_THRESHOLDS) - 1):
            if LEVEL_THRESHOLDS[i] <= total_xp < LEVEL_THRESHOLDS[i + 1]:
                return i + 1
        return len(LEVEL_THRESHOLDS)
    extra = total_xp - LEVEL_THRESHOLDS[-1]
    return 10 + (extra // 550)


def next_level_threshold(level: int) -> int:
    if level < 10:
        return LEVEL_THRESHOLDS[level]
    return LEVEL_THRESHOLDS[-1] + (level - 9) * 550


def title_for_level(level: int) -> str:
    if level <= len(LEVEL_TITLES):
        return LEVEL_TITLES[level - 1]
    return "System Executor"


def clamp(n: int, low: int, high: int) -> int:
    return max(low, min(high, n))


def compute_analysis_xp(context_text: str) -> tuple[int, str]:
    score = 10
    reasons: list[str] = []
    lower = context_text.lower()

    if "thesis" in lower:
        score += 8
        reasons.append("thesis framing detected")
    if "entry" in lower and "sl" in lower:
        score += 8
        reasons.append("entry/SL precision discussed")
    if "tp" in lower:
        score += 6
        reasons.append("multi-target planning discussed")
    if "assumption disclosure" in lower or "assumed from chart" in lower:
        score += 6
        reasons.append("assumption discipline present")
    if "if " in lower and " then" in lower:
        score += 5
        reasons.append("conditional scenario thinking visible")
    if "post-entry verification" in lower or "verify" in lower:
        score += 5
        reasons.append("verification loop visible")

    score = clamp(score, 0, 40)
    reason = ", ".join(reasons) if reasons else "baseline structured discussion"
    return score, reason


def score_session(
    positions: list[dict],
    open_orders: list[dict],
    trades: list[dict],
    context_text: str,
    positions_summary_text: str,
    coach_adjustment: int,
) -> list[ScoreEvent]:
    events: list[ScoreEvent] = []

    if "pre-trade" in context_text.lower() or "follow-up" in context_text.lower():
        events.append(ScoreEvent("pre_trade_pause", 20, "pre-trade consultation loop active"))

    plan_fields = 0
    for token in ["entry", "stop", "tp", "size", "thesis"]:
        if token in context_text.lower():
            plan_fields += 1
    if plan_fields >= 4:
        events.append(ScoreEvent("plan_completeness", 25, "plan structure present in context/journal"))
    elif plan_fields >= 2:
        events.append(ScoreEvent("plan_partial", 12, "partial plan structure present"))

    if positions:
        events.append(ScoreEvent("live_position_tracking", 10, "live position tracked in workspace"))

    protective_count = 0
    for order in open_orders:
        trade_side = str(order.get("tradeSide", "")).lower()
        pos_side = str(order.get("posSide", "")).lower()
        if trade_side == "close" and pos_side in {"short", "long"}:
            protective_count += 1
    if protective_count > 0:
        events.append(
            ScoreEvent("protective_orders", 15, f"protective close intent detected on {protective_count} open orders")
        )

    if "compliance" in positions_summary_text.lower() and "pass" in positions_summary_text.lower():
        events.append(ScoreEvent("verification_pass", 20, "post-entry verification pass recorded"))

    analysis_xp, analysis_reason = compute_analysis_xp(context_text)
    events.append(ScoreEvent("analysis_quality", analysis_xp, analysis_reason))

    if "emotionally tired" in context_text.lower() and "readiness to end session" in context_text.lower():
        events.append(ScoreEvent("risk_state_honesty", 8, "honest state reporting under emotional load"))
        events.append(ScoreEvent("session_stop_discipline", 12, "explicit session stop discipline"))

    if "one trade only today" in context_text.lower() or "one trade only" in context_text.lower():
        events.append(ScoreEvent("one_trade_limit", 10, "one-trade discipline commitment captured"))

    if "sl widening" in context_text.lower() and "no" in context_text.lower():
        events.append(ScoreEvent("no_sl_widening_reaffirmed", 8, "rule 4 reaffirmed"))

    if trades:
        events.append(ScoreEvent("activity_logged", 5, "exchange activity data available for review"))

    coach_adjustment = clamp(coach_adjustment, -15, 15)
    if coach_adjustment != 0:
        direction = "bonus" if coach_adjustment > 0 else "penalty"
        events.append(
            ScoreEvent("coach_adjustment", coach_adjustment, f"{direction} applied within bounded coach lane")
        )

    return events


def summarize_scores(events: list[ScoreEvent]) -> tuple[int, float, float]:
    total_xp = sum(e.xp for e in events)

    compliance_keys = {
        "pre_trade_pause",
        "plan_completeness",
        "plan_partial",
        "live_position_tracking",
        "protective_orders",
        "verification_pass",
        "risk_state_honesty",
        "session_stop_discipline",
        "one_trade_limit",
        "no_sl_widening_reaffirmed",
    }
    analysis_keys = {"analysis_quality"}

    compliance_xp = sum(e.xp for e in events if e.key in compliance_keys)
    analysis_xp = sum(e.xp for e in events if e.key in analysis_keys)

    discipline_score = float(clamp(compliance_xp, 0, 100))
    analysis_score = float(clamp(analysis_xp * 2, 0, 100))
    return total_xp, discipline_score, analysis_score


def generate_report(
    ts: str,
    events: list[ScoreEvent],
    earned_xp: int,
    total_xp: int,
    level: int,
    title: str,
    xp_to_next: int,
    discipline_score: float,
    analysis_score: float,
) -> str:
    lines = [
        "# MOST Progression Report",
        "",
        f"Generated: {ts}",
        "",
        "## Session XP",
        "",
        f"**Earned this run** — {earned_xp} XP",
        "",
        "| Event | XP | Reason |",
        "|------|---:|--------|",
    ]
    for event in events:
        lines.append(f"| {event.key} | {event.xp:+d} | {event.reason} |")

    lines.extend(
        [
            "",
            "## Progress",
            "",
            f"**Total XP** — {total_xp}",
            f"**Level** — {level} ({title})",
            f"**XP to next level** — {xp_to_next}",
            f"**Discipline score** — {discipline_score:.0f}/100",
            f"**Analysis score** — {analysis_score:.0f}/100",
            "",
            "## Notes",
            "",
            "- PnL is informational context only; process quality drives XP.",
            "- Coach adjustment lane is bounded at +/-15 XP per run.",
            "",
            "*Run: `python tools/progression.py` after sync or material session updates.*",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%d %H:%M UTC")

    balances = read_json(EXCHANGE_DIR / "balances.json", {})
    positions = read_json(EXCHANGE_DIR / "positions.json", [])
    open_orders = read_json(EXCHANGE_DIR / "open_orders.json", [])
    trades = read_json(EXCHANGE_DIR / "trades.json", [])

    context_text = read_text(CONTEXT_PATH)
    positions_summary_text = read_text(JOURNAL_POSITIONS_SUMMARY)
    state = read_json(STATE_PATH, {})
    if not isinstance(state, dict):
        state = {}

    coach_adjustment = 0
    events = score_session(
        positions=positions if isinstance(positions, list) else [],
        open_orders=open_orders if isinstance(open_orders, list) else [],
        trades=trades if isinstance(trades, list) else [],
        context_text=context_text,
        positions_summary_text=positions_summary_text,
        coach_adjustment=coach_adjustment,
    )

    earned_xp, discipline_score, analysis_score = summarize_scores(events)
    previous_total = int(state.get("total_xp", 0))
    total_xp = max(0, previous_total + earned_xp)
    level = current_level(total_xp)
    next_threshold = next_level_threshold(level)
    xp_to_next = max(0, next_threshold - total_xp)
    title = title_for_level(level)

    old_discipline = float(state.get("discipline_score", 0.0))
    old_analysis = float(state.get("analysis_score", 0.0))
    blended_discipline = round(old_discipline * 0.7 + discipline_score * 0.3, 1)
    blended_analysis = round(old_analysis * 0.7 + analysis_score * 0.3, 1)

    history = state.get("history", [])
    if not isinstance(history, list):
        history = []
    history.append(
        {
            "timestamp": now.isoformat(),
            "earned_xp": earned_xp,
            "events": [{"key": e.key, "xp": e.xp, "reason": e.reason} for e in events],
            "discipline_score": discipline_score,
            "analysis_score": analysis_score,
            "balance_total": balances.get("total") if isinstance(balances, dict) else None,
        }
    )
    history = history[-50:]

    new_state = {
        "schema_version": 1,
        "updated_at": now.isoformat(),
        "total_xp": total_xp,
        "level": level,
        "title": title,
        "xp_to_next_level": xp_to_next,
        "discipline_score": blended_discipline,
        "analysis_score": blended_analysis,
        "compliance_streak": int(extract_int(r"\*\*Current streak\*\*\s*—\s*(\d+)", positions_summary_text, default=0)),
        "missions": state.get(
            "missions",
            {"window": "weekly", "completed_this_window": [], "last_reset": None},
        ),
        "badges": state.get("badges", []),
        "history": history,
    }

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(new_state, indent=2), encoding="utf-8")

    report = generate_report(
        ts=ts,
        events=events,
        earned_xp=earned_xp,
        total_xp=total_xp,
        level=level,
        title=title,
        xp_to_next=xp_to_next,
        discipline_score=blended_discipline,
        analysis_score=blended_analysis,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Progression state updated: {STATE_PATH}")
    print(f"Progression report saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
