# Iron Rules

Seven rules. Non-negotiable. No exceptions. No "just this once."

## Axiom: A Stopped Trade Is Dead

A trade that hit its stop loss is a **closed thesis**. The chart **invalidated** the idea. Re-entering the same direction on the same pair is a **new trade** — never a "continuation" of the original risk. "Equivalent risk" framing is a documented trap (recovery shortcut — treating a new entry as if it were the same trade).

There is no such thing as "I'm just re-entering where I was." You are opening a new position with a new risk budget, and you must go through the full Rule 3 lock + Rule 5 cooldown first.

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

### Mental Bankroll Model

| Parameter | Value |
|-----------|-------|
| Declared capital | $______ |
| Physical margin on exchange | $______ |
| Risk calculated against | Declared capital ($______), NOT exchange margin |
| Top-up trigger | When margin drops below level needed for next trade |
| Top-up increment | $______ |
| Hard stop | If declared capital ($______) is fully drawn down, STOP. Re-evaluate before adding more. |

Declared capital is money you own but keep off-exchange to avoid the temptation of oversizing. Only working margin lives on the exchange. Risk math always runs against the declared bankroll.

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

Max **dollar risk** for this trade = Rule 2 amount (fixed % of declared capital, or after the Kelly phase the dollar risk implied by half-Kelly and `journal/positions/_summary.md` — still one explicit number before entry).

**Linear instruments (spot / perp quoted in coin terms):**

1. **Risk per 1 unit** = `|entry price − stop price|` (use the actual fill assumption for entry).
2. **Raw size (units)** = `max_risk_dollars / risk_per_unit`.
3. **Round down** to the exchange’s **lot / contract step** so that worst-case loss at the stop stays **≤** max risk (leave a small buffer for fees and slippage).

**One line to state in the plan:** “If stopped, loss = [N]R at SL ___ with size ___.”

**Tight-SL warning:** If SL distance is **< 1%** of entry price, the stop is inside normal noise. That setup **maximizes position size**, not edge — escalation dressed as precision. The AI should flag this automatically.

**Liquidation check (leveraged positions):** State liquidation price at intended leverage before entry. Liquidation must be beyond the stop (further from entry). If liquidation sits between entry and SL: **invalid** plan. Reduce leverage or add margin.

**Pre-mortem (before locking plan):** Answer: “What is the scenario where this trade leads to me breaking rules — not just the stop, but what I do in the minutes after?” If you cannot articulate that cascade path, you are not seeing the full risk.

Multiple separate entries = multiple risk budgets unless a single combined stop defines **one** risk (advanced; default is **one entry, one stop, one max-risk budget**).

**Chart convention (same EP + same SL, different TPs):** If you draw **several** trade boxes (e.g. TradingView position tools) that share the **same entry** and the **same stop loss** and differ **only** in take-profit price, that means **one** trade, **one** risk budget (**1R** to that SL), and **multiple partial targets** — not several full positions. Size **once** from |entry − SL|; assign **percentage or exact units** to each TP (total **100%**). If entry or SL **differs** between boxes, treat each distinct (entry, SL) pair as a **separate** risk decision unless you explicitly document one combined plan.

### Multiple take-profit levels (partials)

- **One position, one risk budget.** Several TP lines on a chart mean **partial exits**, not three full independent positions. Opening the same idea three times at full size = **3× risk** → violates Rule 2.
- The plan must state **percentage or exact units** closed at **each** TP (totals **100%** of the intended position).
- **Order of exits:** take the **closest TP to entry first** along the profitable side (long: **lowest** TP price above entry first; short: **highest** TP price below entry first), unless you document a different staged order **before** entry.
- **Default templates** if you have not chosen yet (pick one and lock it): **33% / 33% / 34%**, or **50% / 30% / 20%** (front-loads profit; reduces giveback risk). Avoid defaulting most size to the farthest TP (**moonshot attachment**).
- After the **first** partial, Rule 4 allows moving the stop **toward entry or better** (e.g. breakeven). Decide **before** entry whether BE triggers after TP1 only or after TP2 as well.

**Why:** A plan spoken out loud to another entity is harder to corrupt than a plan that exists only in your head.

---

## 4. No SL Widening

The stop loss moves toward entry or stays where it is.
Never away from entry. Moving SL to breakeven is always permitted and encouraged.

There is no scenario, no "new information," no market condition that justifies widening the stop.

**Why:** This is the one rule that survives every iteration of every serious trading system. Widening SL is the single highest-damage behavioral failure. It converts controlled losses into catastrophic ones.

---

## 5. Cooldown After Loss

After a stop-out, return to this workspace before any new trade.
AI logs it. Then — and only then — consider the next entry.

**Minimum cooldown times:**

| Event | Minimum wait |
|-------|-------------|
| Single stop-out (plan followed) | **60 minutes** from stop timestamp |
| Stop-out with any rule violation | **4 hours** |
| 2 consecutive losses in one session | **Session ends. Mandatory.** |
| Cascade / liquidation | **24 hours** from last close |

The AI tracks cooldown based on **exchange timestamps**, not user self-report. If you appear before cooldown expires, the AI engages with mood, analysis, and journal — **not** with trade ideas, sizing, or entry coaching.

**Why:** Serial entry after losses is a consistent value-destruction pattern. Each subsequent entry is less analytical and more compulsive. The cooldown breaks the revenge cycle. A one-minute rule does not replace real time gaps when the pattern is activated — explicit minimum waits are required.

---

## 6. Single Position (recommended for calibration phase)

During the calibration phase (e.g. first 50 compliant trades), **one open position at a time** is **strongly recommended**. Treat “hedges,” “uncorrelated pairs,” or “the other one is at breakeven so it’s free” as extra risk and cognitive load unless you have explicitly graduated this rule.

After enough compliant trades with demonstrated single-position discipline, you may revisit this constraint in your rules and journal.

**Why:** Every additional open position multiplies decision surface, monitoring load, and cross-position rationalization. Framing a second position as a “hedge” is a common permission structure at portfolio level.

---

## 7. AI Accountability Cost

This system (Cursor + AI partner) has a **real monthly cost**. Budget for it explicitly.

The AI must demonstrably contribute to trading results. This means:
- **Preventing losses** that would have occurred without the system (interventions, pattern catches, cooldown enforcement)
- **Maintaining compliance** (verification PASS rate, streak length)
- **Reducing cascade frequency** (the most expensive failure mode)

**Metric:** The system pays for itself primarily through **losses prevented**, not trades generated. Track: interventions fired, cascades averted, compliant trade count. If you are trading less but losing less, the system is working.

This is not a joke rule. But it must **not** create pressure to trade. The optimal action is often to **not** trade. A month with zero trades and zero losses is a successful month — the subscription bought survival.

---

## Post-Entry Verification (mandatory procedure)

After a **pre-trade consultation** and **after you place the order on the exchange**, you complete the loop:

1. Run: `python exchange/sync.py` (from workspace root).
2. Tell AI: "Position opened — verify."
3. AI reads `exchange/data/positions.json` and `exchange/data/snapshot.md`, compares to the **locked plan** recorded in `journal/positions/` for that trade (symbol, side, size, entry zone, SL, TP).
4. AI responds with **PASS** or **MISMATCH** and a short checklist:
   - Side (long/short) matches plan
   - Size within agreed tolerance vs plan (e.g. same contracts / notional band)
   - Entry consistent with plan (market vs limit — acknowledge slippage)
   - SL and TP present on exchange if the plan required them

If **MISMATCH**: do not rationalize. Fix on exchange or close and re-plan — then log what happened.

**Why:** Execution errors (wrong side, wrong size, missing protective orders) are not "small mistakes" — they are the same pattern family as plan corruption. Verification makes errors visible immediately.

---

## Chart screenshots — assumption disclosure (AI)

When you paste a **screenshot**, the AI must **in the same reply** state explicitly:

- **Direction:** long, short, or not stated  
- **Price levels** it is using: entry, SL, TP(s), or zones — or **not readable**  
- **Source:** your words (**confirmed**) vs **inferred from the image** (may be wrong)

Screenshot interpretation errors happen; the **locked trade plan** and journal must follow **what you confirm**, not a misread chart.
