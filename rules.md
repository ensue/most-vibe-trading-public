# Iron Rules

Non-negotiable. No exceptions. No "just this once."

---

## 1. Pre-Trade Pause

Before placing any trade, open this workspace and talk to AI.
State the thesis. Describe the setup. Hear the response.
Minimum 60 seconds between "I see a setup" and "I place the order."

**Why:** The compression of "I think" → "I see" → "I know" happens fast enough to evade self-monitoring. The pause breaks the chain.

---

## 2. Max Risk Per Trade

| Phase | Rule |
|-------|------|
| First 50 trades | Fixed **____%** of declared capital ($______) = **$____ max risk per trade** |
| After 50 compliant | Half Kelly on trailing 50-trade stats |

The number is absolute. Not "roughly" or "about." The exact dollar amount is stated before entry.

### Bankroll Model

| Parameter | Value |
|-----------|-------|
| Declared capital | $______ |
| Physical margin on exchange | $______ |
| Risk calculated against | Declared capital, NOT exchange margin |
| Top-up trigger | When margin drops below level needed for next trade |
| Top-up increment | $______ |
| Hard stop | If declared capital is fully drawn down, STOP. Re-evaluate before adding more. |

_Fill in during your first session with the AI partner._

**Why:** Escalation always starts with "just a bit more size." A hard number kills it at origin.

---

## 3. Plan Before Entry

Before placing the order, tell AI:
- **Entry** (price or market)
- **Stop loss** (exact price)
- **Take profit** (at least one level)
- **Position size** (exact amount)
- **Thesis** (one sentence: why this trade)

AI records it. This becomes the immutable reference for post-trade review.

### Position size (how to derive it)

Max **dollar risk** for this trade = the explicit amount from Rule 2 (fixed % of declared capital, or half-Kelly dollar risk once configured). State that number **before** entry.

**Linear instruments (spot / perp quoted in coin terms):**

1. **Risk per 1 unit** = `|entry price − stop price|` (use the actual fill assumption for entry).
2. **Raw size (units)** = `max_risk_dollars / risk_per_unit`.
3. **Round down** to the exchange’s **lot / contract step** so worst-case loss at the stop stays **≤** max risk (buffer for fees/slippage).

**One line to state in the plan:** “If stopped before any management, loss ≤ $___ at SL ___ with size ___.”

**Chart convention (same entry + same SL, different TPs):** Multiple overlays (e.g. position tools) with **identical entry and identical stop** and **only** different take-profit levels = **one** trade, **one** risk budget (**1R** to that SL), **partial exits** at each TP. Size once from |entry − SL|; state **% or units** per TP (total **100%**). **Different** entry or **different** SL between overlays ⇒ separate risk unless one explicit combined plan says otherwise.

### Multiple take-profit levels (partials)

- **One position, one risk budget.** Several TP lines mean **partial exits**, not multiple full positions at full size.
- The plan must state **percentage or units** at **each** TP (total **100%**).
- **Order of exits:** closest TP to entry along the profitable side first (long: **lowest** TP above entry; short: **highest** TP below entry), unless a different staged order is documented **before** entry.
- **Default templates** if not yet chosen: **33% / 33% / 34%** or **50% / 30% / 20%**. Avoid parking most size on the farthest target by default.
- After the **first** partial, stops may only move **toward entry or better** (Rule 4). Decide **before** entry when breakeven applies.

**Why:** A plan spoken out loud to another entity is harder to corrupt than a plan that exists only in your head.

---

## 4. No SL Widening

The stop loss moves toward entry or stays where it is.
Never away from entry. Moving SL to breakeven is always permitted and encouraged.

There is no scenario, no "new information," no market condition that justifies widening the stop.

**Why:** Widening SL is the single highest-damage behavioral failure. It converts controlled losses into catastrophic ones.

---

## 5. Cooldown After Loss

After a stop-out, return to this workspace before any new trade.
Report: what happened, how you feel, whether the plan was followed.
AI logs it. Then — and only then — consider the next entry.

After 2 consecutive losses in one session: session ends. Mandatory.

**Why:** Serial entry after losses is a consistent value-destruction pattern. Each subsequent entry is less analytical and more compulsive. The cooldown breaks the revenge cycle.

---

## 6. AI Accountability Cost

This system (Cursor + AI partner) has a monthly cost. That is a real expense.

The AI must demonstrably contribute to net-positive trading results. If after 3 months the system has not paid for itself through compliant, profitable trading, the approach must be re-evaluated.

**Metric:** Cumulative net PnL (after fees) must exceed cumulative AI cost within the first 3 months.

---

## Post-Entry Verification (mandatory procedure)

After a **pre-trade consultation** and **after you place the order on the exchange**, you complete the loop:

1. Run: `python exchange/sync.py` (from workspace root).
2. Tell AI: "Position opened — verify."
3. AI reads `exchange/data/positions.json` and `exchange/data/snapshot.md`, compares to the **locked plan** recorded in `journal/positions/` for that trade (symbol, side, size, entry zone, SL, TP).
4. AI responds with **PASS** or **MISMATCH** and a short checklist:
   - Side (long/short) matches plan
   - Size within agreed tolerance vs plan
   - Entry consistent with plan (market vs limit — acknowledge slippage)
   - SL and TP present on exchange if the plan required them

If **MISMATCH**: do not rationalize. Fix on exchange or close and re-plan — then log what happened.

**Why:** Execution errors are not "small mistakes" — they are the same pattern family as plan corruption. Verification makes errors visible immediately.

---

## Chart screenshots — assumption disclosure (AI)

When you paste a **screenshot**, the AI must **in the same reply** state explicitly:

- **Direction:** long, short, or not stated  
- **Price levels** it is using: entry, SL, TP(s), or zones — or **not readable**  
- **Source:** your words (**confirmed**) vs **inferred from the image** (may be wrong)

Screenshot reads can be wrong; the **locked trade plan** and journal follow **what you confirm**, not a misread chart.
