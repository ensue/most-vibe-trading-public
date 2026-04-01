# Edge Verification Protocol

The system's fundamental assumption — "the user has analytical edge and just needs discipline" — must be treated as a **testable hypothesis**, not an article of faith.

## The hypothesis

> "I have a real, repeatable analytical edge in crypto markets that produces positive expected value when executed with discipline."

This is either true or false. **Feelings, rare wins, and self-assessment do not count as evidence.** Only a statistically significant sample of **pre-committed predictions** with tracked outcomes counts.

## Why this matters

The gambling loop requires the edge belief to persist:

1. Lose money → "I can't manage risk"
2. Recall precise wins → "I have skill, see?"
3. Can't profit → "I'm just undisciplined"
4. → Repeat forever

If the edge is illusory, then "discipline" is irrelevant — there's nothing to be disciplined ABOUT. The system must verify the premise before building on it.

## Edge status

Three states, stored in `journal/calls/_summary.md`:

| Status | Criteria | System behavior |
|--------|----------|-----------------|
| **UNCONFIRMED** | < 30 tracked calls | AI states "edge hypothesis unconfirmed — insufficient data" when user invokes edge belief. No claim of edge allowed in self-talk. |
| **NOT SUPPORTED** | ≥ 30 calls, but hit rate not statistically above random (p > 0.10 for one-tailed binomial test vs 50%) | AI states "data does not support edge hypothesis." User must continue collecting data or accept that edge may not exist. |
| **CONFIRMED** | ≥ 30 calls, hit rate statistically significant (p ≤ 0.10), AND expected R per call > 0 after fee drag | AI acknowledges confirmed edge. Discipline work proceeds on solid ground. Re-verified every 50 calls (rolling window). |

## The prediction journal (`journal/calls/`)

### What is a "call"

A call is a **pre-committed prediction** logged BEFORE price reaches the entry zone. It records:

- **Symbol, timeframe, direction** (long/short)
- **Entry zone** (price range where the setup triggers)
- **Stop loss** (structural invalidation)
- **Take profit** (at least one target)
- **Thesis** (one sentence: WHY this setup)
- **Confidence** (1-5 scale)
- **Expiry** (max time for setup to trigger — forces timeframe discipline)

### What is NOT a call

- Retroactive "I saw that move" — must be logged BEFORE trigger
- Vague directional bias ("I think BTC goes up") — needs specific levels
- Calls logged after entry zone was already hit — timestamped fraud check

### Outcomes

| Outcome | Definition |
|---------|-----------|
| **HIT** | Price entered zone, then reached TP before SL |
| **MISS** | Price entered zone, then hit SL before TP |
| **EXPIRED** | Price never entered zone within expiry window |
| **PARTIAL** | Price entered zone, reached TP1 but not TP2+ (count per-target) |

### Statistics (computed in `calls/_summary.md`)

- **Total calls logged**
- **Trigger rate** — % of calls where price entered the entry zone
- **Hit rate** (on triggered calls only) — the core edge metric
- **Average R on hits** / **Average R on misses**
- **Expected R per triggered call** = (hit_rate x avg_R_hit) - ((1 - hit_rate) x avg_R_miss)
- **Expected R after fees** = expected_R - fee_drag_per_R
- **Statistical significance** — binomial test: is hit rate significantly above 50%?
- **Confidence interval** — 90% CI on true hit rate
- **Calls by confidence level** — does higher confidence = higher hit rate?
- **Calls by timeframe** — edge may exist on some timeframes but not others

### Statistical significance — lookup table

AI does NOT need to compute p-values. Use this table. For N triggered calls with K hits, find the **minimum K needed** for edge to be significant (one-tailed binomial, p ≤ 0.10 vs null hypothesis of 50%):

| N (triggered) | Min K for CONFIRMED | Hit rate at threshold |
|---------------|--------------------|-----------------------|
| 30 | 19 | 63.3% |
| 40 | 25 | 62.5% |
| 50 | 30 | 60.0% |
| 60 | 36 | 60.0% |
| 75 | 44 | 58.7% |
| 100 | 57 | 57.0% |

**How to use:** Count K (hits) out of N (triggered calls). If K ≥ threshold for that N → **CONFIRMED**. If K < threshold and N ≥ 30 → **NOT SUPPORTED**. If N < 30 → **UNCONFIRMED**.

For N values not in the table, interpolate or use the nearest lower row.

### The 30-call minimum

Before 30 tracked calls with outcomes, the system treats edge as UNCONFIRMED. This is not punitive — it's statistical necessity. With fewer than 30 data points, you cannot distinguish skill from luck at any reasonable confidence level.

### No money required

Calls do not require position entry. This is the key insight: **the analytical work IS the valuable part.** Trading is just the boring mechanical execution of proven setups. If you can't demonstrate edge on paper, adding money makes it worse, not better.

## Integration with the rest of the system

### Progression (XP)
- Call logged with full structure: **+10 XP**
- Call outcome recorded honestly (regardless of hit/miss): **+5 XP**
- Weekly summary computed (≥ 5 calls that week): **+15 XP**
- Edge status advances from UNCONFIRMED → CONFIRMED: **+100 XP** (one-time)

### Trading rules
- During UNCONFIRMED status: real trades are allowed but AI explicitly states "this trade is being placed WITHOUT confirmed edge"
- During NOT SUPPORTED status: AI adds friction — "your last [N] calls show [X]% hit rate, which is not statistically different from coin flips"
- During CONFIRMED status: discipline framework operates on solid ground

### Anti-narrative protocol
When the user (or AI) invokes the "I have edge" belief:
1. AI reads `journal/calls/_summary.md`
2. If UNCONFIRMED/NOT SUPPORTED: challenges the belief with data
3. If CONFIRMED: acknowledges, and refocuses on discipline

## The deeper point

Many traders spend years in the loop: "I'm skilled but undisciplined." It's comfortable because it preserves identity ("I'm a skilled trader") while explaining failure ("I just need discipline"). If the skill is real, the loop is solvable. If the skill is illusory, the loop is eternal — and the only escape is collecting enough data to find out which one it is.

This protocol exists to answer that question with evidence, not feelings.
