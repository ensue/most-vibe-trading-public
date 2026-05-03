# Liquidity Archeology — methodology

**Read first:** `README.md` for terms (cohort, honest entry, filtering event, SL depth tolerance, passport hypothesis).

This document is the **procedure**. It tells you how to take a chart and produce a survivor map.

---

## 0. Inputs you need

- A chart with **enough history** that it contains at least one major filtering event (cascade, bear market, COVID-style flash crash, war shock, central bank surprise).
- An idea of the **typical leverage profile** of the market you are analyzing:
  - **US equity indices:** mostly cash, some 2x–3x ETFs, futures up to ~10–20x effective via margin.
  - **Crypto perp futures:** 5x–125x routinely. Median retail leverage on Bitget perps ≈ **20x–50x**.
  - **FX retail:** 30x–500x by jurisdiction.
- The **liquidation math** for that leverage:
  - At nominal `Lx` leverage, liquidation is approximately `100% / L` of price movement against entry, before fees / funding. So 50x ≈ **2%** move = wipeout. 10x ≈ **10%**. 5x ≈ **20%**. Cash-only ≈ **100%** (no liquidation, only psychological / capital exhaustion).

This matters because **leverage profile = SL depth tolerance distribution**. A market dominated by 50x perps cannot have a meaningful "honest entry" cohort surviving a 10% drawdown — they all got liquidated. A market dominated by cash equity buyers can survive a 50% drawdown.

---

## 1. Mark filtering events on the chart

Walk left-to-right through the chart and tag every candle / range that **plausibly violated some SL depth**. Examples:

- Single candle that retraces a recent multi-month range
- Cascade days (>5 std-dev moves in liquid markets, often news-triggered)
- ATH wicks (liquidate short stops AND trap long breakout buyers)
- Multi-week trends in either direction (slow grind that exhausts mean-revert positions)
- Range breakouts that fail back into range (trap both sides)

For each filtering event, write down:

| Field | Value |
|-------|-------|
| Date / candle | YYYY-MM(-DD) |
| Type | wick / cascade / breakout / breakdown / news / grinding-trend |
| Range traversed | from $X to $Y, **% move = Z%** |
| Probable trigger | (news, structural break, mechanical liquidation cascade, unknown) |
| Cohorts plausibly violated | (use Step 2 to identify) |

A filtering event is **not** something you guess at — it's a measurable price move. The hypothesis layer is "which cohort got hit", not "did something happen."

---

## 2. Reconstruct cohorts between filtering events

For each price band **between** two filtering events (or between a filtering event and "now"), describe the cohort that likely entered there.

Use this 5-question template (also in `templates/cohort-snapshot.md`):

1. **Entry price band** — what range did this cohort accumulate?
2. **What was the prevailing narrative when they entered?** — was the macro story bullish, bearish, mixed, doubt-filled?
3. **Conviction class** — honest entry (during doubt) vs confirmation entry (after a clear signal)?
4. **Probable leverage / SL depth** — given the typical participant in this market and timeframe, how deep can they go before forced exit?
5. **What would invalidate this cohort?** — what filtering event (price level + magnitude) would force them out?

This step is **inference**, not certainty. You are estimating distributions, not querying a database. The discipline is: **state the inference explicitly so it can be argued with later**.

---

## 3. Apply filtering events forward (the elimination round)

Now walk left-to-right through your tagged filtering events. For each event, strike out every cohort whose SL depth was violated by that event.

Practical example:

- Cohort A entered S&P 500 at 4,200 in late 2022 (honest entry — recession fears, lower highs).
- Cohort B entered at 4,800 in early 2024 (confirmation entry — ATH break, soft landing narrative).
- Filtering event: a 25% drawdown to 3,600 hits in 2026.
  - Cohort A: 4,200 → 3,600 = **−14% drawdown**. If their SL depth tolerance is 20%+ (cash buyers, no leverage), **survive**. If they are 10x ETF holders, **liquidated**.
  - Cohort B: 4,800 → 3,600 = **−25% drawdown**. Almost any leveraged cohort: **liquidated**. Even 5x: **liquidated**. Cash holders sitting on 25% loss: **probably capitulated** (psychological breakpoint usually sub-25% for confirmation entries).

What remains after applying every historical filtering event is your **survivor map**.

The survivor map for an asset that has run multi-year is typically a small handful of cohorts:

- A few **honest entry** cohorts from doubt phases (the "passport" group).
- A wide layer of **recent confirmation entries** that have not yet been tested by a filtering event.
- Possibly a **distribution wick survivor** layer that bought the dip just below ATH — testable by the next major correction.

---

## 4. Read the liquidity gradient

Once you have the survivor map, plot it as a vertical price ladder:

```
ATH   28,000  ← confirmation buyers, very shallow SL (1–5%) — first to liquidate
      27,000  ← confirmation buyers, slightly deeper SL — second to liquidate
      ...
      24,000  ← post-breakout buyers, ~10% SL tolerance
      ...
      19,000  ← honest buyers from 2023 doubt period, ~30% SL tolerance from here
      ...
      15,000  ← deep honest buyers from 2022 bear lows, ~50%+ SL tolerance
```

Read this top-down to find:

- The **first liquidation pressure level** (highest cluster of shallow SLs) — where the next forced-exit cascade begins
- The **liquidity vacuum zones** — price ranges with few surviving cohorts and therefore little organic support, where price can move fast in either direction
- The **deep support layer** — honest-entry cohorts whose SL is so far away they will not capitulate easily; the floor of the current market regime

---

## 5. Apply the passport hypothesis

The operator's central claim: **only honest-entry cohorts survive multi-year trends.**

Test this on each completed case study:

- Take a chart with 5+ years of history.
- Identify the cohorts present at the **earliest** point.
- Apply all subsequent filtering events.
- See which cohorts remain at the **latest** point.

If the passport hypothesis is correct, the survivors at the end of any multi-year trend are **dominantly** honest-entry cohorts. Confirmation-entry cohorts repeatedly enter and exit through filtering events; honest-entry cohorts enter once and stay.

If the hypothesis is **wrong**, you should see at least some confirmation-entry cohorts surviving without being filtered. Document those cases — they are the falsifying evidence.

---

## 6. State predictions and log them

Liquidity archeology produces predictions of the form:

> "If [symbol] reaches [level], cohort [X] (entered around [Y], SL depth ≈ [Z%]) will be forced to exit, contributing to additional [magnitude] of selling pressure."

Or:

> "The current price action between [A] and [B] is being held by cohort [X] (honest entry from [period]). They will not capitulate until price reaches [C]. Above [B], the next cohort layer is [Y] (confirmation entry, shallow SL); their forced selling pressure starts there."

A useful prediction is:

- **Specific** — names the level, the cohort, the direction.
- **Dated / time-bounded** — happens by [date] or invalidates.
- **Falsifiable** — there is a clear price action that would refute it.
- **Independent of news** — you should be able to state the prediction before the news that "explains" it appears.

Log meaningful predictions as **calls** in `most/journal/calls/` (see `system/edge_verification.md`). The framework is only valuable if its predictions beat random over a sample of 30+.

---

## 7. Operating limits

This framework is hypothesis-generating, not signal-generating. Specifically:

- It tells you **where forced flow probably is**, not **when** it triggers.
- It does **not** replace risk management. Even a perfect cohort map gives no position size — that comes from `most/rules.md`.
- It does **not** override the iron rules. A "high conviction liquidity archeology read" is not a permission structure to bypass Rule 3 plan locking, Rule 5 cooldown, or anything else.
- It is **subject to recency bias**. Reconstructing cohorts from past charts is much easier than reconstructing them in real-time at the right edge of the chart. Always document the **right-edge cohort map** explicitly — that is the test, not the historical part.

---

## 8. Skill development checklist

To validate that this framework is producing real skill (vs. confirmation-bias narratives), maintain these counters:

- **Number of completed case studies:** target ≥ 10 before judging value.
- **Number of falsifiable predictions logged as calls:** target ≥ 30 with outcomes.
- **Hit rate of predictions vs random:** the framework is "real" only if hit rate is meaningfully above random for the prediction class.
- **Number of cases where the hypothesis was falsified:** if zero, you are not seeing what disconfirms — bias suspect. Healthy ratio: at least some falsified hypotheses per cohort generation.

When edge is `UNCONFIRMED` (current state per `journal/calls/_summary.md`), this framework is **a skill experiment**, not a confirmed analytical advantage. Treat its output accordingly.
