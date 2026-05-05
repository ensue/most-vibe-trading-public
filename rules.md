# Iron Rules

Seven rules. Non-negotiable. No exceptions. No "just this once."

## Axiom: A Stopped Trade Is Dead

A trade that hit its stop loss is a **closed thesis**. The chart **invalidated** the idea. Re-entering the same direction on the same pair is a **new trade** — never a "continuation" of the original risk. "Equivalent risk" framing is a documented trap (recovery shortcut — treating a new entry as if it were the same trade).

There is no such thing as "I'm just re-entering where I was." You are opening a new position with a new risk budget, and you must go through the full Rule 3 lock + Rule 5 cooldown first.

---

## Journal and session contract (system — binding)

This is not an eighth iron rule; it governs **how** the workspace records behavior.

- **Default capture:** Anything the operator states here may be logged — including details that seem minor. The AI does **not** ask "should I log this?" unless the operator opts out.
- **Calm laptop session = success:** Opening the laptop and using this workspace deliberately and calmly — with or without a trade — counts as **behavioral success**. The AI records it in the journal spheres and may apply progression credit when material.
- **IDE chat = primary signal:** Text typed in the Cursor chat window is the highest-fidelity behavioral input — log substantively, without pre-filtering for “importance.” Use **`journal/speech/`** for verbatim utterance archives and language-level analysis (see `journal/speech/README.md` in a full install).

---

## 1. Pre-Trade Accountability

Two paths to a compliant entry. **Both require workspace involvement** — the difference is timing.

### Path A: Standard (preferred)
Before placing any trade, open this workspace and talk to AI.
State the thesis. Describe the setup. Hear the response.
Minimum 60 seconds between "I see a setup" and "I place the order."

### Path B: Wick Protocol (time-sensitive entries)
When a wick or momentum event creates a narrow entry window:

1. **Enter on the exchange** — but SL must be set AT THE MOMENT OF ENTRY.
2. **Come to workspace within 5 minutes** of the fill.
3. **State the full plan retroactively:** entry, SL, TP, size, thesis — same as Rule 3.
4. **AI runs post-entry verification** (sync → compare → PASS/MISMATCH).
5. **Fee Drag Check runs retroactively.** If BLOCKED → widen SL or close.
6. If the entry fails Rule 2/6 or has no SL on exchange → **MISMATCH**.

**What Wick Protocol is NOT:**
- A license to skip SL ("I'll set it later")
- A workaround for cooldown (Rule 5 still applies)
- An excuse for phone trading (laptop only)
- Serial entry in disguise (re-entering after a stop is NOT a wick)

**Edge verification:** "I'm good at wicks" is testable. Tag wick calls in `journal/calls/` with `wick: true`. Compare wick vs non-wick hit rates after 20+ entries.

**Why both paths exist:** The pre-trade pause catches impulsive entries. Legitimate wicks are real — the market does not wait. The Wick Protocol preserves accountability without penalizing speed. The constraint: **SL must exist from second zero.** An entry without SL is not a wick trade — it's gambling.

---

## 2. Max Risk Per Trade

| Phase | Rule |
|-------|------|
| First 50 trades | Fixed **____%** of declared capital ($______) = **$____ max risk per trade** |
| After 50 compliant | Half Kelly on trailing 50-trade stats |

The dollar amount is stated before entry. **Verification tolerance:** worst-case loss at the stop may land **within ±$3** of that figure after lot rounding, fees, and fill variance — **PASS** on Rule 2 for post-entry checks. Beyond **+$3** over max → review (oversize).

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
3. **Round down** to the exchange’s **lot / contract step** so that worst-case loss at the stop stays **≤** max risk + **$3 tolerance** (see Rule 2).

**One line to state in the plan:** “If stopped, loss = [N]R at SL ___ with size ___.”

**Fee drag check (mandatory):** AI computes `fee_drag = round_trip_fee_rate / SL_distance_%` in every sizing block:
- **OK** (SL > 3%): fee drag < 4% of R — proceed.
- **WARNING** (SL 1-3%): fee drag 4-12% of R — AI warns; consider wider SL or limit orders.
- **BLOCKED** (SL < 1%): fee drag > 12% of R — AI refuses to size. SL must move to structural level > 1% from entry.

Round-trip fee rates: **taker/taker 0.12%**, maker/taker 0.08%, **maker/maker 0.04%** (typical crypto futures). AI assumes taker/taker unless user specifies limit orders.

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

### R:R unlock ladder (gamification)

- **State file:** `system/risk_reward_unlock.json` — read with **`load_rr_unlock()`** in `system/rr_unlock.py` or the CLI `python tools/risk_reward_unlock.py status`.
- **Before locking a plan:** Compute **planned max R:R** (farthest TP vs SL — see `risk_reward_unlock.md`). It must be **≤ `current_unlocked_max_rr`** or the plan is **invalid** until TPs are tightened or a tier is unlocked.
- **Promotion:** `promotion_wins_required` **compliant wins** with planned max R:R at lock ≤ current cap and realized **R > 0** → increment progress (`python tools/risk_reward_unlock.py record-win` after journal entry).
- **Ceiling:** Default **20:1** max (`ceiling_max_rr`).
- This **does not** relax Rule 2 dollar risk or Rule 4 SL discipline — it only caps how **far** your **reward** may be vs **1R** on the plan.

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

**Minimum cooldown times (single-event):**

| Event | Minimum wait |
|-------|-------------|
| Single stop-out (plan followed) | **60 minutes** from stop timestamp |
| Stop-out with any rule violation | **4 hours** |
| 2 consecutive losses in one session | **Session ends. Mandatory.** |
| Cascade / liquidation | **24 hours** from last close |

The AI tracks cooldown based on **exchange timestamps**, not user self-report. If you appear before cooldown expires, the AI engages with mood, analysis, and journal — **not** with trade ideas, sizing, or entry coaching.

### Cumulative drawdown timeouts (chapter-level)

Single-event cooldowns protect against revenge in minutes/hours; they do not protect against slow bleed. The asymmetry of recovery (a -10% drawdown takes ~+11.1% to undo, -20% takes +25%, -50% takes +100%, -90% takes +900%) means **every percentage past -10% costs more to recover than it cost to lose**. Hard chapter-level stops on cumulative DD vs **chapter-start equity**:

| Drawdown vs chapter-start equity | Mandatory action |
|---|---|
| **-10%** | Chapter auto-close. Postmortem before next session. New chapter starts only after a calm reflection entry. |
| **-20%** | Chapter auto-close **AND** **30-day no-trade** cooldown from last close. Analysis / calls / journal allowed; no new positions. |
| **-50%** | Era-level review. Cannot continue from same declared bankroll without re-declaring it (cold reflection, mandatory consultation of all prior `chapter-N-postmortem.md`). |

**Anchor:** chapter-start equity recorded in the opening line of `chapter-N-live.md`, NOT current high-water mark. This prevents "I had +30% so a -10% from peak is fine" rationalization.

**The AI must check this on every sync.** If `equity / chapter_start_equity ≤ 0.90`, the AI opens with: "Chapter auto-close triggered. Drawdown -[X]% from chapter start. No more risk coaching this chapter. Write the postmortem first."

**Why:** Without a tripwire that does not depend on operator energy, a chapter rides cumulative DD all the way to capitulation. Drawdown timeouts add the cumulative dimension single-event cooldowns miss. Serial entry breaks the revenge cycle in time; drawdown gates break it in capital.

---

## 6. Primary position + optional liquidity-zone hedge (calibration phase)

During calibration (e.g. first 50 compliant trades), run **one primary thesis** at a time: **one dominant size / one main invalidation (SL)** on the trade you are managing toward your targets.

### When a second leg is allowed: **liquidity-zone hedge** (documented)

A **hedge** is allowed when it is **not** a second independent bet — a **temporary, bounded** overlay to:

- Keep **primary size** because the primary has a **sound, tight SL** and a path to a **further TP**.
- Pass through a **liquidity / chop zone** with **limited giveback of uPNL** if price rejects: if price bounces, the hedge **protects or realizes** that uPNL per plan; if the **primary SL** hits, loss is **bounded** by what you defined (including uPNL through the zone) — not an open-ended resize game.

**Before opening the hedge** (in your journal / workspace):

- **Primary** — symbol, side, size, SL, TP(s).
- **Zone** — the structure you are hedging through.
- **Hedge** — instrument, side, **size cap**, **exit rule** for the hedge leg (price or time).
- **Combined worst case** — max loss if both legs move against you (in **R** and currency).
- **Unwind order** — how you flatten (hedge first vs primary) — **before** entry.

If you cannot write the above, treat it as a **second position** (not allowed as a “hedge”).

### Short **bridge** into a limit ladder

If the plan is a **short only until** resting **long bids** fill (or the short closes in the same zone), that is **sequential** — not a two-sided hedge. **Working limits are not a position** until filled. Log bridge short + pointer to the long ladder in one journal note.

### Still disallowed

- A **second full thesis** on another instrument for stimulation or “diversification.”
- **“Uncorrelated pair”** to scratch an itch.
- **“The other leg is at breakeven so it’s free.”**
- **Cross-trade financing** without one locked combined plan.

**Why:** Undocumented second legs multiply rationalization. Documented liquidity hedges are risk engineering; undocumented ones are often permission-seeking.

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

## Compliant Trade — binary definition

The system counts toward the Kelly threshold and toward edge verification only with **compliant trades**. "Compliant" must be **operational, binary, and achievable** — not a vibe. A trade is **COMPLIANT** if and only if **every** condition below is **YES**. A single NO makes the trade **NON-COMPLIANT** and excluded from the compliant counter (it still goes to the journal — exclusion is from progression, not from the record).

**Critical: compliance is independent of PnL.** A losing trade can be COMPLIANT. A winning trade can be NON-COMPLIANT. The point is to measure *process quality* across enough samples to reveal whether the process produces edge — not to reward winners or punish losers.

### The 10-point checklist (paste into every position entry under `## Compliance check`)

```
- [ ]  1. Pre-trade lock OR Wick Protocol PASS — Rule 1
       Path A: full plan stated in workspace BEFORE order placed.
       Path B: order placed first, but SL set at moment of entry AND workspace visit within 5 min AND post-entry verify PASS.
- [ ]  2. Cooldown respected — Rule 5
       Single-event cooldown elapsed (60 min / 4h / 24h depending on prior event).
       Cumulative drawdown gates not violated (chapter not in -10% auto-close state).
- [ ]  3. Plan complete BEFORE entry — Rule 3
       Entry, SL, TP (≥1 level), size, one-sentence thesis ALL stated before the order.
- [ ]  4. Risk within Rule 2 — Rule 2
       Worst-case loss at SL within calibration tolerance (e.g. fixed-2% phase) OR Half-Kelly (after the calibration gate).
- [ ]  5. Fee Drag Check NOT BLOCKED — Rule 3
       SL distance ≥ 1% of entry price. (WARNING is allowed; BLOCKED is not.)
- [ ]  6. Liquidation check passed — Rule 3
       For leveraged positions: liq price beyond SL (further from entry). Stated before entry.
- [ ]  7. SL set ON exchange before any other action — Rules 1 & 4
       Protective order is live on the exchange, not "I'll set it later".
- [ ]  8. SL not widened during life of trade — Rule 4
       SL moved toward entry / BE only. Never away. No exception.
- [ ]  9. Single primary thesis — Rule 6
       One primary position. Any second leg is a documented liquidity-zone hedge per Rule 6 OR sequential bridge into limit ladder, NOT a second discretionary thesis.
- [ ] 10. Post-entry verification PASS — verification procedure
       Sync ran, AI compared exchange to locked plan, result PASS. Any MISMATCH = NON-COMPLIANT regardless of outcome.
```

A trade is **COMPLIANT** when all 10 boxes are ticked. PnL is not in the list.

### How it gets recorded

Each `journal/positions/YYYY-MM-DD-<symbol>-<slug>.md` entry ends with:

```
## Compliance check
[paste the 10-point checklist with [x] / [ ] filled]

## Compliance verdict
COMPLIANT | NON-COMPLIANT
First failed condition (if any): #N — <which rule, what happened>
```

The AI fills this section after post-entry verification (item 10). After the trade closes, the AI re-checks items 8–10 against the closing record and updates the verdict if anything changed (e.g. SL widened mid-trade → flips to NON-COMPLIANT).

`journal/positions/_summary.md` then maintains `compliant_trades_total` and `compliant_trades_streak` (current run, broken by any NON-COMPLIANT or by a chapter close).

### Soft-compliant tier (optional, future)

A second tier may be introduced after the first **5 fully compliant trades**: **SOFT-COMPLIANT** = items 1, 3, 4, 7, 8, 10 met but minor process issues on 2/5/6/9. Soft-compliant trades count toward edge verification (`journal/calls/`) but **not** toward the calibration→Kelly gate. This tier is **not active** by default — it activates only after 5 fully compliant trades are on the record. Do not pre-emptively rationalize toward it.

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

- **Order context:** Is the image **structure-only markup**, or does it show **pending / resting exchange intent** (position tool, order/bracket lines, resting limit ladder, operator-confirmed open order)? If unclear, the AI **asks** once; it does **not** default to “analysis-only.”
- **Direction:** long, short, or not stated  
- **Price levels** it is using: entry, SL, TP(s), or zones — or **not readable**  
- **Source:** your words (**confirmed**) vs **inferred from the image** (may be wrong)  
- **TradingView (binding for AI):** If the screenshot shows **EP / SL / TP price labels on the right-hand price axis**, the AI must use those numbers — **not** “eyeball” levels from candles or grid. If labels are not legible, say **not readable** and ask; do not guess.

Screenshot interpretation errors happen; the **locked trade plan** and journal must follow **what you confirm**, not a misread chart.
