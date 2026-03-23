# Trading Command Center — Current Context

Last updated: ___

## Quick Status

| Metric | Value |
|--------|-------|
| Active positions | 0 |
| Today's trades | 0 |
| Compliance streak | 0 |
| Phase | Calibration (first 50 trades, fixed %) |
| Mental state | Not assessed |
| Last session | N/A — system initialized |
| Next trade window | ___ |

## Risk Model

- **Current:** Fixed ___% of $___  declared capital = **$___ max risk per trade**
- **Physical margin on exchange:** $___
- **Top-up:** ___ if margin needs replenishing
- **Transition at:** 50 compliant trades with tracked stats
- **Target model:** Half Kelly on trailing 50-trade statistics

## Active Concerns

None — fresh start.

## Recent Activity

System initialized. No trading activity yet.

## Session Notes

_Updated by AI after each trading conversation._

## Growth Models

| Tool | Report | Regenerate |
|------|--------|------------|
| Projection (deterministic) | `tools/projection_report.md` | `python tools/projection.py` |
| Monte Carlo (5K sims) | `tools/monte_carlo_report.md` | `python tools/monte_carlo.py` |

_Run the tools after setting your parameters in `rules.md` to see projections._

## Reminders for AI

- **Vibe Trading Partner** — consultant; no trade approval / no PASS-FAIL on opens
- Startup **sync** = source of truth for positions; archive TradingView shots under `journal/charts/`
- Read `profile.md` when behavioral context matters
- Read `journal/*/_summary.md` for sphere context
- `rules.md` = user's commitments — reflect when helpful, do not police as authority
- Structured/visual logs over long narrative
- After closed trades: update projection if stats changed materially
- Continuously capture notable info — don't ask, just log
