# MOST Progression System

This system tracks quality trading progress in a tangible way.
It rewards discipline, analysis quality, and execution hygiene.
It does not reward random short-term PnL noise.

## Philosophy

- Process quality is the core signal.
- Rule compliance has highest weight.
- PnL is informational context, not primary XP driver.
- Exceptional learning and exceptional discipline get extra credit.

## XP Categories

### 1) Compliance XP (highest weight)

- Pre-trade pause respected and plan discussed: +20 XP
- Plan completeness:
  - Entry present: +5 XP
  - SL present: +8 XP
  - TP ladder present: +8 XP
  - Size + risk line present: +10 XP
  - One-sentence thesis present: +5 XP
- Post-entry verification performed: +20 XP
- Protective logic detected on exchange after entry (SL/TP close intent): +15 XP
- Cooldown respected after a loss (when applicable): +15 XP

### 2) Analysis Quality XP

Scored from 0 to 40 per meaningful setup review:

- Structure clarity (market context and setup map): 0-8
- Invalidation quality (structural, not convenience): 0-10
- Scenario quality (if/then branches): 0-8
- Assumption disclosure quality (confirmed vs inferred): 0-6
- Precision and coherence (clean, falsifiable, non-handwave): 0-8

### 3) Behavior XP

- Honest state reporting (mood/energy/fatigue): +8 XP
- Session stop discipline when yellow/red risk state: +12 XP
- One-trade limit honored after commitment: +10 XP

## Penalties

- SL widening attempt or action: -60 XP
- New trade without pre-trade pause: -40 XP
- Serial re-entry after stop without cooldown: -50 XP
- Missing protective order after opening (if plan required): -35 XP
- Plan corruption language during open trade without plan lock update: -25 XP

## Coach Adjustment Lane (bounded)

The coach may apply a small bounded adjustment:

- `coach_adjustment_xp` in range [-15, +15] per session
- Use positive adjustment for objectively exceptional progress:
  - novel high-quality self-correction
  - unusually clear structural reasoning
  - repeated discipline under emotional pressure
- Use negative adjustment for soft but visible process drift not captured by hard rules.
- Every adjustment must include a short reason in the report.

## Level Curve

Non-linear progression (harder over time):

- Level 1: 0 XP
- Level 2: 120 XP
- Level 3: 280 XP
- Level 4: 480 XP
- Level 5: 730 XP
- Level 6: 1,030 XP
- Level 7: 1,380 XP
- Level 8: 1,780 XP
- Level 9: 2,230 XP
- Level 10: 2,730 XP

Above level 10, each new level requires +550 XP.

## Titles and Milestones

- Level 1-2: Initiate
- Level 3-4: Structured Trader
- Level 5-6: Process Guardian
- Level 7-8: Edge Operator
- Level 9-10: Discipline Architect
- Level 11+: System Executor

## Weekly Missions (process-first)

- 3 complete plans with full risk line
- 2 post-entry verifications
- 0 SL widening violations
- At least 2 sessions ended intentionally due to fatigue/risk state

Each completed mission: +25 XP.

## Data Sources

Primary:
- `exchange/data/balances.json`
- `exchange/data/positions.json`
- `exchange/data/open_orders.json`
- `exchange/data/trades.json`

Secondary:
- `context.md`
- `journal/positions/_summary.md`

Outputs:
- `system/progression_state.json`
- `tools/progression_report.md`

## Operating Notes

- This is a quality tracking system, not trade permission.
- XP should reflect repeatable behavior, not luck.
- If scoring feels noisy, tighten evidence thresholds before changing weights.
- **AI accountability:** The Cursor partner must **update** `progression_state.json` on substantive sessions — **not** leave totals frozen while `journal/` records incidents. Run `tools/progression.py` for baseline scoring, then **append manual penalty/bonus lines** when `progression.md` hard penalties apply and the script cannot infer them.
