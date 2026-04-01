# MOST Progression System v2

Tracks process quality across **three tracks**: Edge Verification, Trade Discipline, and Behavior. Designed so that **analysis without trading** is a first-class activity, penalties cannot be erased by moonshots, and the system verifies edge before assuming it.

## Philosophy

- **Edge must be proven, not assumed.** Until `journal/calls/_summary.md` shows CONFIRMED status, every real trade carries the label "unconfirmed edge."
- Process quality is the core signal. PnL is informational, not primary.
- **Analysis earns XP independently of trading.** Logging calls, doing chart work, and reviewing outcomes builds progression without risking money.
- **Penalties are sticky.** A single winning trade does not erase discipline debt. Penalties create a floor that can only be worked off through sustained compliance across multiple sessions.

## Session Types

Every session is classified (can be combined):

| Type | What happens | XP source |
|------|-------------|-----------|
| **ANALYSIS** | Chart work, prediction calls logged, structure discussion | Edge Verification + Analysis Quality |
| **TRADE** | Plan lock → execution → verification | Compliance + Analysis Quality |
| **REVIEW** | Postmortem, reflection, pattern review, call outcome tracking | Behavior + Edge Verification |

**ANALYSIS sessions are EQUAL to TRADE sessions for progression.** Not consolation prizes.

## XP Categories

### 1) Edge Verification XP (the foundation)

- Call logged with full structure (before trigger): **+10 XP**
- Call outcome recorded honestly (hit, miss, or expired): **+5 XP**
- Weekly call summary computed (≥ 5 calls that week): **+15 XP**
- Edge status advances UNCONFIRMED → CONFIRMED: **+100 XP** (one-time)
- Edge status advances CONFIRMED with ≥ 50 calls: **+50 XP** (one-time)

See `system/edge_verification.md` for full protocol.

### 2) Analysis Quality XP

Scored from 0 to 40 per meaningful setup review (call OR trade plan):

- Structure clarity (market context and setup map): 0-8
- Invalidation quality (structural, not convenience): 0-10
- Scenario quality (if/then branches): 0-8
- Assumption disclosure quality (confirmed vs inferred): 0-6
- Precision and coherence (clean, falsifiable, non-handwave): 0-8

**This applies to CALLS equally.** A well-structured call without a trade earns the same Analysis XP as a pre-trade plan.

### 3) Compliance XP (trade execution track)

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

### 4) Behavior XP

- Honest state reporting (mood/energy/fatigue): +8 XP
- Session stop discipline when yellow/red risk state: +12 XP
- One-trade limit honored after commitment: +10 XP
- **Analysis session completed without placing a trade: +15 XP** (rewarding restraint)
- **Call outcome tracked even when wrong: +5 XP** (rewarding honesty over ego)

## Penalties

- SL widening attempt or action: **-60 XP**
- New trade without pre-trade pause: **-40 XP**
- Serial re-entry after stop without cooldown: **-50 XP**
- Missing protective order after opening (if plan required): **-35 XP**
- Plan corruption language during open trade without plan lock update: **-25 XP**
- **Gambling session (random entries, no workspace involvement): -100 XP**
- **Mobile trading (phone execution): -75 XP**
- **Trading during UNCONFIRMED edge without workspace plan: -30 XP**

## Sticky Penalties (moonshot-proof)

**Problem:** The old system allowed a single large XP session to erase all penalties. This created a perverse incentive: gamble freely, then do one clean session to "reset."

**Definition — "session":** One chat thread (Cursor conversation) that touches trading, analysis, or review. Multiple messages in the same thread = one session. A new chat thread = a new session.

**Solution:** Penalties create a **discipline debt** that is worked off slowly:

1. **Penalty floor per chapter:** Sum all negative XP entries in the current chapter → `penalty_total` (negative number). To advance to the next level, the user must earn positive XP ≥ **2 × |penalty_total|** within the chapter, ON TOP of the level threshold.
2. **Single-session cap:** No single session can contribute more than **+80 XP** net. If a session yields +120 raw, log +80. Negative sessions have no floor.
3. **Penalty decay:** After each **consecutive compliant session** (zero penalty entries), reduce `|penalty_total|` by **10%**. A non-compliant session resets the consecutive count to 0.
4. **No retroactive erasure:** Reversed penalties are logged as separate positive entries with `key: penalty_reversal`, not deletion of the original.

## Coach Adjustment Lane (bounded)

- `coach_adjustment_xp` in range [-15, +15] per session
- Positive: novel self-correction, structural reasoning under pressure, honest postmortem
- Negative: soft process drift not captured by hard rules
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

### Analysis Track
- 5 calls logged with full structure: +25 XP
- 3 call outcomes recorded: +15 XP
- 1 analysis session without any trades: +20 XP

### Trade Track
- 3 complete plans with full risk line: +25 XP
- 2 post-entry verifications: +25 XP
- 0 SL widening violations: +25 XP
- At least 2 sessions ended intentionally due to fatigue/risk state: +25 XP

### Combined
- Week with ≥ 5 calls AND 0 gambling sessions: +50 XP bonus

## Data Sources

Primary:
- `exchange/data/balances.json`
- `exchange/data/positions.json`
- `exchange/data/open_orders.json`
- `exchange/data/trades.json`
- `journal/calls/_summary.md`

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
