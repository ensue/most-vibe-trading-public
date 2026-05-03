"""
Liquidity Archeology — case file tool.

Stdlib-only Python CLI. Reads a JSON case file describing cohorts and filtering
events for a single chart, computes the survivor map and liquidity gradient,
and emits a markdown report.

Subcommands:
    validate   Validate a case JSON file against the schema.
    report     Compute and write a survivor-map markdown report next to the JSON.
    liq        Quick utility — % adverse move that liquidates at given leverage.
    init       Scaffold a new case JSON from the template.

Examples:
    python tool.py validate case-studies/2026-05-03-us100-monthly-cohort-map.json
    python tool.py report   case-studies/2026-05-03-us100-monthly-cohort-map.json
    python tool.py liq 50
    python tool.py init --symbol BTC --tf 1W --date 2026-05-15 --out case-studies/2026-05-15-btc-weekly.json

This tool is hypothesis-generating, not signal-generating. See README.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_VERSION = 1

REQUIRED_METADATA = ("symbol", "timeframe", "snapshot_date", "current_price")
REQUIRED_EVENT = ("id", "label", "date", "type", "from_price", "to_price")
REQUIRED_COHORT = (
    "id",
    "label",
    "entry_price_low",
    "entry_price_high",
    "entry_period_start",
    "conviction",
    "leverage_profile",
    "sl_depth_tolerance_pct",
)

VALID_CONVICTIONS = {"honest", "confirmation", "mixed"}
VALID_LEVERAGE = {
    "cash_only",
    "cash_dominant",
    "low_leverage",
    "mid_leverage",
    "high_leverage",
    "mixed",
}
VALID_DIRECTIONS = {"long", "short"}
VALID_EVENT_TYPES = {
    "wick",
    "cascade",
    "breakout",
    "breakdown",
    "news",
    "grinding-trend",
    "accumulation",
}


# --- Data classes -----------------------------------------------------------


@dataclass
class FilteringEvent:
    id: str
    label: str
    date: str
    type: str
    from_price: float
    to_price: float
    magnitude_pct: float = 0.0
    trigger: str = ""
    note: str = ""


@dataclass
class Cohort:
    id: str
    label: str
    entry_price_low: float
    entry_price_high: float
    entry_period_start: str
    entry_period_end: str
    narrative: str
    conviction: str
    leverage_profile: str
    sl_depth_tolerance_pct: float
    direction: str = "long"
    size_estimate: str = "medium"
    filtering_events_survived: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Prediction:
    id: str
    statement: str
    falsification: str
    real_money_testable: bool = False


@dataclass
class Case:
    metadata: dict
    filtering_events: list[FilteringEvent]
    cohorts: list[Cohort]
    predictions: list[Prediction]


# --- Loading + validation ---------------------------------------------------


class CaseValidationError(ValueError):
    """Raised when a case JSON file does not satisfy the schema."""


def _require_keys(name: str, obj: dict, keys: tuple[str, ...]) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise CaseValidationError(f"{name}: missing required keys {missing}")


def load_case(path: Path) -> Case:
    raw = json.loads(path.read_text(encoding="utf-8"))

    if raw.get("schema_version") != SCHEMA_VERSION:
        raise CaseValidationError(
            f"schema_version mismatch: file has {raw.get('schema_version')!r}, "
            f"tool expects {SCHEMA_VERSION}"
        )

    metadata = raw.get("metadata") or {}
    _require_keys("metadata", metadata, REQUIRED_METADATA)

    events_raw = raw.get("filtering_events") or []
    events: list[FilteringEvent] = []
    seen_event_ids: set[str] = set()
    for ev in events_raw:
        _require_keys(f"filtering_events[{ev.get('id')!r}]", ev, REQUIRED_EVENT)
        if ev["id"] in seen_event_ids:
            raise CaseValidationError(f"duplicate event id: {ev['id']!r}")
        if ev["type"] not in VALID_EVENT_TYPES:
            raise CaseValidationError(
                f"event {ev['id']!r}: type {ev['type']!r} not in {sorted(VALID_EVENT_TYPES)}"
            )
        seen_event_ids.add(ev["id"])
        magnitude = ev.get("magnitude_pct")
        if magnitude is None:
            magnitude = 100.0 * (ev["to_price"] - ev["from_price"]) / ev["from_price"]
        events.append(
            FilteringEvent(
                id=ev["id"],
                label=ev["label"],
                date=ev["date"],
                type=ev["type"],
                from_price=float(ev["from_price"]),
                to_price=float(ev["to_price"]),
                magnitude_pct=float(magnitude),
                trigger=ev.get("trigger", ""),
                note=ev.get("note", ""),
            )
        )

    cohorts_raw = raw.get("cohorts") or []
    if not cohorts_raw:
        raise CaseValidationError("cohorts: at least one cohort required")
    cohorts: list[Cohort] = []
    seen_cohort_ids: set[str] = set()
    for c in cohorts_raw:
        _require_keys(f"cohorts[{c.get('id')!r}]", c, REQUIRED_COHORT)
        if c["id"] in seen_cohort_ids:
            raise CaseValidationError(f"duplicate cohort id: {c['id']!r}")
        if c["conviction"] not in VALID_CONVICTIONS:
            raise CaseValidationError(
                f"cohort {c['id']!r}: conviction {c['conviction']!r} not in {sorted(VALID_CONVICTIONS)}"
            )
        if c["leverage_profile"] not in VALID_LEVERAGE:
            raise CaseValidationError(
                f"cohort {c['id']!r}: leverage_profile {c['leverage_profile']!r} not in {sorted(VALID_LEVERAGE)}"
            )
        direction = c.get("direction", "long")
        if direction not in VALID_DIRECTIONS:
            raise CaseValidationError(
                f"cohort {c['id']!r}: direction {direction!r} not in {sorted(VALID_DIRECTIONS)}"
            )
        if c["entry_price_low"] > c["entry_price_high"]:
            raise CaseValidationError(
                f"cohort {c['id']!r}: entry_price_low > entry_price_high"
            )
        for ev_id in c.get("filtering_events_survived", []):
            if ev_id not in seen_event_ids:
                raise CaseValidationError(
                    f"cohort {c['id']!r}: filtering_events_survived references "
                    f"unknown event id {ev_id!r}"
                )
        seen_cohort_ids.add(c["id"])
        cohorts.append(
            Cohort(
                id=c["id"],
                label=c["label"],
                entry_price_low=float(c["entry_price_low"]),
                entry_price_high=float(c["entry_price_high"]),
                entry_period_start=c["entry_period_start"],
                entry_period_end=c.get("entry_period_end", ""),
                narrative=c.get("narrative", ""),
                conviction=c["conviction"],
                leverage_profile=c["leverage_profile"],
                sl_depth_tolerance_pct=float(c["sl_depth_tolerance_pct"]),
                direction=direction,
                size_estimate=c.get("size_estimate", "medium"),
                filtering_events_survived=list(c.get("filtering_events_survived", [])),
                notes=c.get("notes", ""),
            )
        )

    predictions: list[Prediction] = []
    for p in raw.get("predictions") or []:
        _require_keys(
            f"predictions[{p.get('id')!r}]", p, ("id", "statement", "falsification")
        )
        predictions.append(
            Prediction(
                id=p["id"],
                statement=p["statement"],
                falsification=p["falsification"],
                real_money_testable=bool(p.get("real_money_testable", False)),
            )
        )

    return Case(
        metadata=metadata,
        filtering_events=events,
        cohorts=cohorts,
        predictions=predictions,
    )


# --- Computation ------------------------------------------------------------


def cohort_avg_entry(c: Cohort) -> float:
    return (c.entry_price_low + c.entry_price_high) / 2.0


def cohort_sl_floor_price(c: Cohort) -> float:
    """Price at which a long cohort is forced out (below their entry).

    For shorts the symmetry is inverted (price above entry forces them out)
    and the function returns the corresponding ceiling price.
    """
    avg = cohort_avg_entry(c)
    if c.direction == "long":
        return avg * (1.0 - c.sl_depth_tolerance_pct / 100.0)
    return avg * (1.0 + c.sl_depth_tolerance_pct / 100.0)


def cohort_filtered_by(c: Cohort, events: list[FilteringEvent]) -> list[FilteringEvent]:
    """Return list of events that filtered this cohort."""
    floor = cohort_sl_floor_price(c)
    out: list[FilteringEvent] = []
    for ev in events:
        if c.direction == "long":
            if ev.to_price < floor and _event_after_entry(c, ev):
                out.append(ev)
        else:
            if ev.to_price > floor and _event_after_entry(c, ev):
                out.append(ev)
    return out


def _event_after_entry(c: Cohort, ev: FilteringEvent) -> bool:
    """Heuristic: only events dated >= cohort entry start are filters for that cohort.

    Date comparison is lexical on YYYY[-MM[-DD]] strings, which is correct for
    ISO-style dates. If the operator uses non-ISO formats this returns True
    (assume relevant) rather than skip the event.
    """
    a = c.entry_period_start
    b = ev.date
    if not a or not b:
        return True
    common = min(len(a), len(b))
    return b[:common] >= a[:common]


def cohort_status(c: Cohort, events: list[FilteringEvent]) -> str:
    filtered = cohort_filtered_by(c, events)
    if not filtered:
        return "SURVIVING"
    if c.leverage_profile in {"cash_only", "cash_dominant"}:
        return "PARTIALLY_FILTERED"
    return "FILTERED"


def cohort_remaining_buffer_pct(c: Cohort, current_price: float) -> float:
    """How far current price is from the cohort's SL floor (positive = buffer)."""
    floor = cohort_sl_floor_price(c)
    if c.direction == "long":
        return 100.0 * (current_price - floor) / current_price
    return 100.0 * (floor - current_price) / current_price


def liquidation_pct_at_leverage(leverage: float, maintenance_margin_pct: float = 0.5) -> float:
    """Approximate adverse % move that liquidates a position at given leverage.

    Formula (linear contracts, no fees / funding):
        liq_move_pct ≈ (100 / leverage) - maintenance_margin_pct

    Real exchanges add tiered margin, fees, and funding. This is a useful
    napkin estimate; not exact.
    """
    if leverage <= 0:
        raise ValueError("leverage must be > 0")
    return max(0.0, (100.0 / leverage) - maintenance_margin_pct)


# --- Report generation ------------------------------------------------------


def _fmt_price(p: float) -> str:
    if p >= 1000:
        return f"{p:,.0f}"
    if p >= 10:
        return f"{p:,.2f}"
    return f"{p:.4f}"


def _fmt_pct(p: float) -> str:
    return f"{p:+.1f}%" if p else "0%"


def render_report(case: Case) -> str:
    md = case.metadata
    current_price = float(md["current_price"])
    out: list[str] = []
    out.append(f"# Liquidity Archeology — auto-report for {md['symbol']} ({md['timeframe']})")
    out.append("")
    out.append(f"**Generated by** `tool.py` — do not hand-edit; re-run from JSON instead.")
    out.append(f"**Snapshot date** — {md['snapshot_date']}")
    out.append(f"**Current price** — {_fmt_price(current_price)}")
    if "ath_in_range" in md:
        out.append(f"**ATH in range** — {_fmt_price(float(md['ath_in_range']))}")
    if "atl_in_range" in md:
        out.append(f"**ATL in range** — {_fmt_price(float(md['atl_in_range']))}")
    if md.get("chart_path"):
        out.append(f"**Chart** — `{md['chart_path']}`")
    if md.get("leverage_profile_note"):
        out.append("")
        out.append(f"**Leverage profile note** — {md['leverage_profile_note']}")
    out.append("")
    out.append("> **This is a hypothesis-generating tool, not a signal-generating tool.** "
               "Outputs touching live capital must pass through `journal/calls/` per "
               "`system/edge_verification.md`.")
    out.append("")

    # Filtering events table
    out.append("## Filtering events")
    out.append("")
    if not case.filtering_events:
        out.append("*(none recorded)*")
    else:
        out.append("| Date | Label | Type | From | To | Magnitude | Trigger |")
        out.append("|------|-------|------|------|----|-----------|---------|")
        for ev in case.filtering_events:
            out.append(
                f"| {ev.date} | {ev.label} | {ev.type} | "
                f"{_fmt_price(ev.from_price)} | {_fmt_price(ev.to_price)} | "
                f"{_fmt_pct(ev.magnitude_pct)} | {ev.trigger} |"
            )
    out.append("")

    # Cohort table with computed status
    out.append("## Cohorts (with computed survival status)")
    out.append("")
    out.append(
        "| Cohort | Entry band | Conviction | Leverage | SL depth | "
        "Avg entry | SL floor | Status | Filtered by |"
    )
    out.append(
        "|--------|------------|------------|----------|----------|"
        "-----------|----------|--------|-------------|"
    )
    for c in case.cohorts:
        avg = cohort_avg_entry(c)
        floor = cohort_sl_floor_price(c)
        filtered = cohort_filtered_by(c, case.filtering_events)
        status = cohort_status(c, case.filtering_events)
        filtered_ids = ", ".join(ev.id for ev in filtered) if filtered else "—"
        out.append(
            f"| **{c.label}** ({c.id}) | "
            f"{_fmt_price(c.entry_price_low)}–{_fmt_price(c.entry_price_high)} | "
            f"{c.conviction} | {c.leverage_profile} | "
            f"±{c.sl_depth_tolerance_pct:.0f}% | "
            f"{_fmt_price(avg)} | {_fmt_price(floor)} | "
            f"{status} | {filtered_ids} |"
        )
    out.append("")

    # Survivor ladder (vertical)
    survivors = [
        c
        for c in case.cohorts
        if cohort_status(c, case.filtering_events) in {"SURVIVING", "PARTIALLY_FILTERED"}
    ]
    survivors.sort(key=lambda c: c.entry_price_high, reverse=True)

    out.append("## Survivor ladder (top → bottom)")
    out.append("")
    out.append("```text")
    if "ath_in_range" in md:
        out.append(f"{_fmt_price(float(md['ath_in_range'])):>12}  ← ATH in range")
    out.append(f"{_fmt_price(current_price):>12}  ← CURRENT PRICE")
    for c in survivors:
        avg = cohort_avg_entry(c)
        marker = "*" if c.entry_price_low <= current_price <= c.entry_price_high else " "
        out.append(
            f"{_fmt_price(avg):>12}  {marker} {c.label} "
            f"({_fmt_price(c.entry_price_low)}–{_fmt_price(c.entry_price_high)}, "
            f"{c.conviction}, status: {cohort_status(c, case.filtering_events)})"
        )
    if "atl_in_range" in md:
        out.append(f"{_fmt_price(float(md['atl_in_range'])):>12}  ← ATL in range")
    out.append("```")
    out.append("")

    # Liquidity gradient — sorted by SL floor distance to current
    out.append("## Liquidity gradient (where forced flow appears)")
    out.append("")
    if not survivors:
        out.append("*(no surviving cohorts — survivor map is empty)*")
    else:
        below_pressure: list[tuple[float, Cohort]] = []
        above_pressure: list[tuple[float, Cohort]] = []
        for c in survivors:
            floor = cohort_sl_floor_price(c)
            if c.direction == "long":
                if floor < current_price:
                    below_pressure.append((current_price - floor, c))
                else:
                    above_pressure.append((floor - current_price, c))
            else:
                if floor > current_price:
                    above_pressure.append((floor - current_price, c))
                else:
                    below_pressure.append((current_price - floor, c))
        below_pressure.sort(key=lambda x: x[0])
        above_pressure.sort(key=lambda x: x[0])

        if below_pressure:
            out.append("**Pressure below current price** (long stops if price drops):")
            out.append("")
            for dist, c in below_pressure:
                floor = cohort_sl_floor_price(c)
                pct = 100.0 * dist / current_price
                out.append(
                    f"- **{_fmt_price(floor)}** ({pct:.1f}% below) — {c.label} "
                    f"(direction: {c.direction}, leverage: {c.leverage_profile}, "
                    f"size: {c.size_estimate})"
                )
            out.append("")
        if above_pressure:
            out.append("**Pressure above current price** (short stops / forced buy-ins if price rises):")
            out.append("")
            for dist, c in above_pressure:
                floor = cohort_sl_floor_price(c)
                pct = 100.0 * dist / current_price
                out.append(
                    f"- **{_fmt_price(floor)}** ({pct:.1f}% above) — {c.label} "
                    f"(direction: {c.direction}, leverage: {c.leverage_profile}, "
                    f"size: {c.size_estimate})"
                )
            out.append("")

    # Vacuum zones — gaps in surviving cohort entry bands
    out.append("## Vacuum zones (no surviving cohort entries)")
    out.append("")
    bands = sorted(
        [(c.entry_price_low, c.entry_price_high, c) for c in survivors],
        key=lambda x: x[0],
    )
    if len(bands) < 2:
        out.append("*(not enough surviving cohorts to identify vacuum zones)*")
    else:
        gaps_found = False
        for (lo1, hi1, c1), (lo2, hi2, c2) in zip(bands, bands[1:]):
            if lo2 > hi1:
                gap_pct = 100.0 * (lo2 - hi1) / hi1
                gaps_found = True
                out.append(
                    f"- **{_fmt_price(hi1)} → {_fmt_price(lo2)}** "
                    f"(gap of {gap_pct:.1f}%) — between *{c1.label}* and *{c2.label}*. "
                    f"Expect fast price action through this range."
                )
        if not gaps_found:
            out.append("*(surviving cohort bands are contiguous — no vacuum zones)*")
    out.append("")

    # Predictions
    out.append("## Predictions logged in this case")
    out.append("")
    if not case.predictions:
        out.append("*(none yet — add to JSON `predictions` array, then re-run report)*")
    else:
        for p in case.predictions:
            tag = "**REAL-MONEY TESTABLE**" if p.real_money_testable else "(research-only)"
            out.append(f"### {p.id} — {tag}")
            out.append("")
            out.append(f"- **Claim:** {p.statement}")
            out.append(f"- **Falsified if:** {p.falsification}")
            out.append("")
        out.append(
            "Real-money-testable predictions should be copied into `journal/calls/` "
            "as separate call files per `system/edge_verification.md`."
        )
    out.append("")

    # Caveats
    out.append("## Caveats (always)")
    out.append("")
    out.append(
        "- All cohort sizes / leverage profiles are **inferred**, not measured. "
        "Real cohort distributions would require options open interest, futures positioning, "
        "ETF flows, and retail brokerage data."
    )
    out.append(
        "- The framework is a **hypothesis** about how price action records liquidity transfer. "
        "It is not a verified analytical edge. Every prediction here must be tested against "
        "an actual outcome to count toward edge."
    )
    out.append(
        "- **Articulation ≠ skill** (Pattern #9 — knowledge–identity split). Producing a "
        "well-structured cohort map is intellectual work; producing tradeable edge requires "
        "logged predictions with hit rates above random over a sample of 30+."
    )
    out.append("")

    return "\n".join(out)


# --- CLI subcommands --------------------------------------------------------


def cmd_validate(args: argparse.Namespace) -> int:
    case = load_case(Path(args.path))
    print(
        f"OK — {len(case.cohorts)} cohorts, {len(case.filtering_events)} filtering events, "
        f"{len(case.predictions)} predictions."
    )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    src = Path(args.path)
    case = load_case(src)
    md = render_report(case)
    out_path = src.with_suffix(".report.md")
    if args.out:
        out_path = Path(args.out)
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


def cmd_liq(args: argparse.Namespace) -> int:
    pct = liquidation_pct_at_leverage(args.leverage, args.maint)
    print(
        f"At {args.leverage:g}x leverage with {args.maint:g}% maintenance margin, "
        f"liquidation ~{pct:.2f}% adverse move (before fees / funding)."
    )
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    template_path = Path(__file__).parent / "templates" / "case.template.json"
    template = json.loads(template_path.read_text(encoding="utf-8"))
    template["metadata"]["symbol"] = args.symbol
    template["metadata"]["timeframe"] = args.tf
    template["metadata"]["snapshot_date"] = args.date
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote scaffold to {out_path}")
    print("Edit the file to fill in cohorts, filtering events, and predictions.")
    print(f"Then: python {Path(__file__).name} report {out_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Liquidity Archeology — case file tool (research only).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate a case JSON file.")
    p_val.add_argument("path")
    p_val.set_defaults(func=cmd_validate)

    p_rep = sub.add_parser("report", help="Generate markdown survivor-map report.")
    p_rep.add_argument("path")
    p_rep.add_argument(
        "--out",
        help="Optional output path (defaults to <case>.report.md next to the JSON).",
    )
    p_rep.set_defaults(func=cmd_report)

    p_liq = sub.add_parser("liq", help="Approximate liquidation move at given leverage.")
    p_liq.add_argument("leverage", type=float)
    p_liq.add_argument(
        "--maint",
        type=float,
        default=0.5,
        help="Maintenance margin %% (default 0.5).",
    )
    p_liq.set_defaults(func=cmd_liq)

    p_init = sub.add_parser("init", help="Scaffold a new case JSON.")
    p_init.add_argument("--symbol", required=True)
    p_init.add_argument("--tf", required=True, help="Timeframe (e.g. 1M, 1W, 1D).")
    p_init.add_argument("--date", required=True, help="Snapshot date YYYY-MM-DD.")
    p_init.add_argument("--out", required=True, help="Output JSON path.")
    p_init.set_defaults(func=cmd_init)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CaseValidationError as e:
        print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"FILE NOT FOUND: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
