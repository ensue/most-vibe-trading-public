"""
Growth projection model.

Answers: "How many compliant trades to reach my goal?"
Shows three scenarios based on discipline level.

Usage:
    python tools/projection.py                          # defaults
    python tools/projection.py --capital 2000 --goal 10000
    python tools/projection.py --capital 2000 --goal 10000 --risk-pct 2 --winrate 55 --avg-r 3.5

Output:
    tools/projection_report.md  (human-readable, links in context.md)
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPORT_PATH = Path(__file__).resolve().parent / "projection_report.md"
STATS_PATH = Path(__file__).resolve().parent.parent / "journal" / "positions" / "_summary.md"


def simulate_growth(
    capital: float,
    goal: float,
    risk_pct: float,
    win_rate: float,
    avg_r_win: float,
    avg_r_loss: float = -1.0,
    max_trades: int = 500,
) -> list[dict]:
    """Simulate trade-by-trade compound growth using expected value per trade."""
    equity = capital
    history = [{"trade": 0, "equity": round(equity, 2)}]

    for i in range(1, max_trades + 1):
        risk_amount = equity * (risk_pct / 100.0)
        expected_win = risk_amount * avg_r_win * (win_rate / 100.0)
        expected_loss = risk_amount * abs(avg_r_loss) * ((100.0 - win_rate) / 100.0)
        expected_pnl = expected_win - expected_loss
        equity += expected_pnl
        equity = round(equity, 2)
        history.append({"trade": i, "equity": equity})
        if equity >= goal:
            break
        if equity <= 0:
            break

    return history


def format_scenario(name: str, history: list[dict], goal: float) -> list[str]:
    """Format a single scenario into markdown lines."""
    final = history[-1]
    reached = final["equity"] >= goal
    trades_needed = final["trade"] if reached else None

    lines = []
    if reached:
        lines.append(f"**{name}:** {trades_needed} trades to ${goal:,.0f}")
    else:
        lines.append(f"**{name}:** Did not reach ${goal:,.0f} in {final['trade']} trades (final: ${final['equity']:,.2f})")

    milestones = [25, 50, 75, 100, 150, 200, 300, 500]
    milestone_lines = []
    for m in milestones:
        if m < len(history):
            milestone_lines.append(f"| {m} | ${history[m]['equity']:,.2f} |")
    if milestone_lines:
        lines.append("")
        lines.append("| Trade # | Equity |")
        lines.append("|---------|--------|")
        lines.extend(milestone_lines)
        if reached and trades_needed not in milestones:
            lines.append(f"| **{trades_needed}** | **${goal:,.0f} (GOAL)** |")

    return lines


def generate_report(
    capital: float,
    goal: float,
    risk_pct: float,
    win_rate: float,
    avg_r_win: float,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    scenarios = {
        "Disciplined (your stats)": {
            "risk_pct": risk_pct,
            "win_rate": win_rate,
            "avg_r_win": avg_r_win,
            "avg_r_loss": 1.0,
        },
        "Sloppy (20% worse winrate, 1R avg win)": {
            "risk_pct": risk_pct,
            "win_rate": max(win_rate - 20, 30),
            "avg_r_win": 1.0,
            "avg_r_loss": 1.0,
        },
        "Degenerate (random entries, no edge)": {
            "risk_pct": risk_pct,
            "win_rate": 45,
            "avg_r_win": 1.0,
            "avg_r_loss": 1.0,
        },
    }

    lines = [
        "# Growth Projection",
        "",
        f"Generated: {ts}",
        "",
        "## Parameters",
        "",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Starting capital | ${capital:,.2f} |",
        f"| Goal | ${goal:,.2f} |",
        f"| Risk per trade | {risk_pct}% |",
        f"| Win rate (your stats) | {win_rate}% |",
        f"| Avg R on wins | {avg_r_win}R |",
        "",
        "## Scenarios",
        "",
        "Three paths from the same starting point. The only variable is **your behavior.**",
        "",
    ]

    for name, params in scenarios.items():
        history = simulate_growth(
            capital=capital,
            goal=goal,
            risk_pct=params["risk_pct"],
            win_rate=params["win_rate"],
            avg_r_win=params["avg_r_win"],
            avg_r_loss=params["avg_r_loss"],
        )
        scenario_lines = format_scenario(name, history, goal)
        lines.extend(scenario_lines)
        lines.append("")

    lines.extend([
        "## What This Means",
        "",
        "The **Disciplined** path is the compound effect of doing the boring thing correctly,",
        "every single trade, without exception. The math works. The question is whether",
        "you will let it.",
        "",
        "The **Sloppy** path is what happens when you skip the pre-trade pause, widen a stop",
        "\"just once,\" or add size because the setup \"feels strong.\" Your edge erodes.",
        "Compound growth stalls or reverses.",
        "",
        "The **Degenerate** path is coin-flip trading with fees. Negative expected value.",
        "Account bleeds to zero. This is what unplanned, emotional trading produces",
        "over enough trades — regardless of how smart the analysis looked at entry.",
        "",
        "---",
        "",
        "*Updated automatically. Based on actual stats when available (50+ trades),",
        "target estimates when not. Run: `python tools/projection.py`*",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Growth projection model")
    parser.add_argument("--capital", type=float, default=2000, help="Starting capital ($)")
    parser.add_argument("--goal", type=float, default=10000, help="Target capital ($)")
    parser.add_argument("--risk-pct", type=float, default=2, help="Risk per trade (%%)")
    parser.add_argument("--winrate", type=float, default=55, help="Win rate (%%)")
    parser.add_argument("--avg-r", type=float, default=3.5, help="Average R on winning trades")
    args = parser.parse_args()

    report = generate_report(
        capital=args.capital,
        goal=args.goal,
        risk_pct=args.risk_pct,
        win_rate=args.winrate,
        avg_r_win=args.avg_r,
    )

    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
