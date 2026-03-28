"""
Monte Carlo trade simulation.

Runs N random trade sequences to show the RANGE of possible outcomes,
not just the expected value. Answers questions like:
- "What's the probability I reach $10K from $2K?"
- "What's the worst realistic drawdown I should prepare for?"
- "How much variance should I expect even when trading well?"

Default parameters come from `journal/positions/trade_stats.json` when you have
compliant closed trades; otherwise the report states clearly that scenario
defaults are used (not measured edge).

Usage:
    python tools/monte_carlo.py
    python tools/monte_carlo.py --capital 2000 --goal 10000 --trades 100 --sims 5000
    python tools/monte_carlo.py --capital 2000 --goal 10000 --risk-pct 2 --winrate 55 --avg-r 3.5
    python tools/monte_carlo.py --ignore-stats-file

Output:
    tools/monte_carlo_report.md
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPORT_PATH = Path(__file__).resolve().parent / "monte_carlo_report.md"
STATS_PATH = Path(__file__).resolve().parent.parent / "journal" / "positions" / "trade_stats.json"
STATS_FILE_REL = "journal/positions/trade_stats.json"

DEFAULT_WINRATE = 55.0
DEFAULT_AVG_R_WIN = 3.5
DEFAULT_AVG_R_LOSS = 1.0
MIN_SAMPLE_TRADES_FOR_CONFIDENCE = 30


@dataclass
class SimResult:
    final_equity: float
    max_drawdown_pct: float
    peak_equity: float
    reached_goal: bool
    longest_losing_streak: int
    trade_count: int


@dataclass(frozen=True)
class ResolvedParams:
    """Win-rate / R inputs for the simulation after merging file + CLI."""

    win_rate: float
    avg_r_win: float
    avg_r_loss: float
    wins: int
    losses: int
    source_kind: str
    cli_override: bool


def load_trade_stats_from_file(path: Path) -> tuple[int, int, float, float]:
    if not path.exists():
        return 0, 0, 0.0, 0.0
    data = json.loads(path.read_text(encoding="utf-8"))
    ct = data.get("compliant_trades", {})
    return (
        int(ct.get("wins", 0)),
        int(ct.get("losses", 0)),
        float(ct.get("sum_r_wins", 0.0)),
        float(ct.get("sum_r_losses_abs", 0.0)),
    )


def resolve_monte_carlo_params(
    stats_path: Path,
    ignore_stats_file: bool,
    cli_winrate: float | None,
    cli_avg_r_win: float | None,
) -> ResolvedParams:
    wins, losses, sum_rw, sum_rl = 0, 0, 0.0, 0.0
    if not ignore_stats_file:
        wins, losses, sum_rw, sum_rl = load_trade_stats_from_file(stats_path)

    n = wins + losses
    measured = n > 0 and not ignore_stats_file

    if measured:
        win_rate = wins / n * 100
        avg_r_win = (sum_rw / wins) if wins > 0 else DEFAULT_AVG_R_WIN
        avg_r_loss = (sum_rl / losses) if losses > 0 else DEFAULT_AVG_R_LOSS
        source_kind = "measured"
    else:
        win_rate = DEFAULT_WINRATE
        avg_r_win = DEFAULT_AVG_R_WIN
        avg_r_loss = DEFAULT_AVG_R_LOSS
        if ignore_stats_file:
            source_kind = "defaults_ignore_file"
        else:
            source_kind = "defaults_no_compliant_trades"

    cli_override = cli_winrate is not None or cli_avg_r_win is not None
    if cli_winrate is not None:
        win_rate = float(cli_winrate)
    if cli_avg_r_win is not None:
        avg_r_win = float(cli_avg_r_win)

    if cli_override:
        if measured and source_kind == "measured":
            source_kind = "measured_cli_override"
        else:
            source_kind = "defaults_cli_override"

    return ResolvedParams(
        win_rate=win_rate,
        avg_r_win=avg_r_win,
        avg_r_loss=avg_r_loss,
        wins=wins,
        losses=losses,
        source_kind=source_kind,
        cli_override=cli_override,
    )


def simulate_one(
    capital: float,
    goal: float,
    risk_pct: float,
    win_rate: float,
    avg_r_win: float,
    avg_r_loss: float,
    r_win_std: float,
    num_trades: int,
) -> SimResult:
    equity = capital
    peak = capital
    max_dd_pct = 0.0
    reached_goal = False
    losing_streak = 0
    longest_losing = 0

    for _ in range(num_trades):
        risk_amount = equity * (risk_pct / 100.0)
        if random.random() * 100 < win_rate:
            r = max(0.1, random.gauss(avg_r_win, r_win_std))
            equity += risk_amount * r
            losing_streak = 0
        else:
            r = max(0.5, random.gauss(avg_r_loss, 0.2))
            equity -= risk_amount * r
            losing_streak += 1
            longest_losing = max(longest_losing, losing_streak)

        if equity <= 0:
            equity = 0.0
            break

        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100
        if dd > max_dd_pct:
            max_dd_pct = dd

        if equity >= goal and not reached_goal:
            reached_goal = True

    return SimResult(
        final_equity=round(equity, 2),
        max_drawdown_pct=round(max_dd_pct, 1),
        peak_equity=round(peak, 2),
        reached_goal=reached_goal,
        longest_losing_streak=longest_losing,
        trade_count=num_trades,
    )


def run_simulation(
    capital: float,
    goal: float,
    risk_pct: float,
    win_rate: float,
    avg_r_win: float,
    avg_r_loss: float = 1.0,
    r_win_std: float = 1.0,
    num_trades: int = 100,
    num_sims: int = 5000,
    seed: int | None = None,
) -> list[SimResult]:
    if seed is not None:
        random.seed(seed)
    return [
        simulate_one(capital, goal, risk_pct, win_rate, avg_r_win, avg_r_loss, r_win_std, num_trades)
        for _ in range(num_sims)
    ]


def percentile(values: list[float], pct: float) -> float:
    s = sorted(values)
    idx = int(len(s) * pct / 100)
    idx = min(idx, len(s) - 1)
    return s[idx]


def _data_source_section(resolved: ResolvedParams) -> list[str]:
    n = resolved.wins + resolved.losses
    lines: list[str] = [
        "## Data source",
        "",
    ]
    sk = resolved.source_kind
    if sk == "measured":
        lines.append(
            f"**Measured** from `{STATS_FILE_REL}`: **{n}** compliant closes "
            f"(**{resolved.wins}** W / **{resolved.losses}** L). Win rate and average R come from counts and stored R sums."
        )
        if n < MIN_SAMPLE_TRADES_FOR_CONFIDENCE:
            lines.append(
                f"**Low sample:** {n} < **{MIN_SAMPLE_TRADES_FOR_CONFIDENCE}** — treat headline percentages as **very noisy**."
            )
    elif sk == "measured_cli_override":
        lines.append(
            f"**Baseline from file:** **{n}** compliant closes (**{resolved.wins}** W / **{resolved.losses}** L). "
            "**CLI overrides** changed win rate and/or avg R — see Parameters below."
        )
    elif sk == "defaults_ignore_file":
        lines.append(
            "**Scenario defaults** (`--ignore-stats-file`). **Not** your measured edge."
        )
    elif sk in ("defaults_cli_override",):
        lines.append(
            "**Scenario defaults** with **CLI overrides** — still not measured edge unless your numbers match the story you intend to test."
        )
    else:
        lines.append(
            f"**No compliant sample** in `{STATS_FILE_REL}` (wins + losses = 0). "
            "The Parameters below are **illustrative defaults** only. They do **not** reflect recent rule breaks, cascades, or unlogged trades. "
            f"Update `{STATS_FILE_REL}` when compliant trades close."
        )
    lines.extend(["", "---", ""])
    return lines


def generate_report(
    capital: float,
    goal: float,
    risk_pct: float,
    resolved: ResolvedParams,
    num_trades: int,
    num_sims: int,
    results: list[SimResult],
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    win_rate = resolved.win_rate
    avg_r_win = resolved.avg_r_win
    avg_r_loss = resolved.avg_r_loss

    finals = [r.final_equity for r in results]
    drawdowns = [r.max_drawdown_pct for r in results]
    streaks = [r.longest_losing_streak for r in results]
    goal_reached = sum(1 for r in results if r.reached_goal)
    blown = sum(1 for r in results if r.final_equity <= 0)

    median_final = percentile(finals, 50)
    p10_final = percentile(finals, 10)
    p90_final = percentile(finals, 90)
    p5_final = percentile(finals, 5)
    p95_final = percentile(finals, 95)
    worst_final = min(finals)
    best_final = max(finals)
    avg_final = sum(finals) / len(finals)

    median_dd = percentile(drawdowns, 50)
    p90_dd = percentile(drawdowns, 90)
    p95_dd = percentile(drawdowns, 95)
    worst_dd = max(drawdowns)

    median_streak = percentile(streaks, 50)
    p90_streak = percentile(streaks, 90)
    worst_streak = max(streaks)

    lines = [
        "# Monte Carlo Simulation",
        "",
        f"Generated: {ts}  ",
        f"Simulations: {num_sims:,} random paths of {num_trades} trades each",
        "",
        *_data_source_section(resolved),
        "## Parameters",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Starting capital | ${capital:,.2f} |",
        f"| Goal | ${goal:,.2f} |",
        f"| Risk per trade | {risk_pct}% |",
        f"| Win rate | {win_rate:.2f}% |",
        f"| Avg R on wins | {avg_r_win:.2f}R (std: 1.0) |",
        f"| Avg R on losses | {avg_r_loss:.2f}R (std: 0.2) |",
        f"| Trades simulated | {num_trades} |",
        "",
        "## Probability of Reaching Goal",
        "",
        f"**{goal_reached / len(results) * 100:.1f}%** chance of reaching ${goal:,.0f} within {num_trades} trades.",
        "",
        f"({goal_reached:,} out of {num_sims:,} simulations)",
        "",
        "## Final Equity Distribution",
        "",
        "| Percentile | Equity |",
        "|------------|--------|",
        f"| Worst case | ${worst_final:,.2f} |",
        f"| 5th (bad luck) | ${p5_final:,.2f} |",
        f"| 10th | ${p10_final:,.2f} |",
        f"| **50th (median)** | **${median_final:,.2f}** |",
        f"| Average | ${avg_final:,.2f} |",
        f"| 90th | ${p90_final:,.2f} |",
        f"| 95th (good luck) | ${p95_final:,.2f} |",
        f"| Best case | ${best_final:,.2f} |",
        "",
        f"Accounts blown (equity ≤ $0): **{blown}** ({blown/len(results)*100:.1f}%)",
        "",
        "## Drawdown Risk",
        "",
        "Max drawdown from peak equity across each simulation:",
        "",
        "| Metric | Drawdown |",
        "|--------|----------|",
        f"| Median max drawdown | {median_dd:.1f}% |",
        f"| 90th percentile | {p90_dd:.1f}% |",
        f"| 95th percentile | {p95_dd:.1f}% |",
        f"| Worst observed | {worst_dd:.1f}% |",
        "",
        "**Translation:** Even trading with edge, expect to see your account drop",
        f"~{median_dd:.0f}% from its peak at some point. In unlucky runs, up to {p95_dd:.0f}%.",
        "This is normal variance, not a signal to change strategy.",
        "",
        "## Losing Streaks",
        "",
        "| Metric | Consecutive losses |",
        "|--------|--------------------|",
        f"| Median longest streak | {int(median_streak)} |",
        f"| 90th percentile | {int(p90_streak)} |",
        f"| Worst observed | {worst_streak} |",
        "",
        f"**Translation:** You WILL hit {int(median_streak)}-loss streaks routinely.",
        f"Occasionally {int(p90_streak)} in a row. This says nothing about your edge — it's math.",
        "The rules exist to prevent you from reacting to variance as if it were signal.",
        "",
        "---",
        "",
        f"*Inputs: `{STATS_FILE_REL}` (compliant trades). Optional CLI overrides. "
        "`--ignore-stats-file` forces scenario defaults.*",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Monte Carlo trade simulation")
    parser.add_argument("--capital", type=float, default=2000, help="Starting capital ($)")
    parser.add_argument("--goal", type=float, default=10000, help="Target capital ($)")
    parser.add_argument("--risk-pct", type=float, default=2, help="Risk per trade (%%)")
    parser.add_argument(
        "--winrate",
        type=float,
        default=None,
        help="Override win rate (%%); omit to use trade_stats.json or scenario defaults",
    )
    parser.add_argument(
        "--avg-r",
        type=float,
        default=None,
        help="Override avg R on wins; omit to use trade_stats.json or scenario defaults",
    )
    parser.add_argument(
        "--ignore-stats-file",
        action="store_true",
        help="Do not read journal/positions/trade_stats.json; use scenario defaults (unless CLI overrides)",
    )
    parser.add_argument("--trades", type=int, default=100, help="Trades per simulation")
    parser.add_argument("--sims", type=int, default=5000, help="Number of simulations")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (for reproducibility)")
    args = parser.parse_args()

    resolved = resolve_monte_carlo_params(
        STATS_PATH,
        args.ignore_stats_file,
        args.winrate,
        args.avg_r,
    )

    print(f"Running {args.sims:,} simulations of {args.trades} trades each...")
    results = run_simulation(
        capital=args.capital,
        goal=args.goal,
        risk_pct=args.risk_pct,
        win_rate=resolved.win_rate,
        avg_r_win=resolved.avg_r_win,
        avg_r_loss=resolved.avg_r_loss,
        num_trades=args.trades,
        num_sims=args.sims,
        seed=args.seed,
    )

    report = generate_report(
        capital=args.capital,
        goal=args.goal,
        risk_pct=args.risk_pct,
        resolved=resolved,
        num_trades=args.trades,
        num_sims=args.sims,
        results=results,
    )

    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
