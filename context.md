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

## Progression

| Metric | Value |
|--------|-------|
| Total XP | See `system/progression_state.json` |
| Level | See `system/progression_state.json` |
| Session XP breakdown | `tools/progression_report.md` |

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

- Read `profile.md` when warning signs appear
- Read sphere summaries in `journal/*/` for deeper context
- Read `exchange/data/` for latest exchange state
- First 50 trades: fixed % risk — do NOT skip to Kelly early
- Watch for: escalation, serial entries after losses, moonshot attachment
- User prefers structured/visual logs over narrative text
- Laptop-only rule: all trading activity originates from this machine only
- The rules in `rules.md` are non-negotiable — verify compliance every conversation
- After each closed trade: update projection if stats changed materially
- Continuously capture notable info from conversations — don't ask, just log
