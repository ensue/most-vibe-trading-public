# Cohort snapshot — template

Use this template to map cohorts at a single moment in time on a single chart. Save filled copies in `case-studies/` as `YYYY-MM-DD-symbol-tf-cohort-map.md`.

Read `methodology.md` Step 2 before filling.

---

## Header

- **Symbol:**
- **Timeframe:**
- **Snapshot date:** YYYY-MM-DD (the "now" point on the chart)
- **Chart range covered:** YYYY-MM to YYYY-MM
- **Chart file:** `journal/charts/YYYY-MM/YYYY-MM-DD-symbol-tf-context.png`
- **Current price:**
- **All-time high in covered range:**
- **All-time low in covered range:**
- **Typical leverage profile of this market:** (cash-only / 2x–5x / 10x–25x perp / 50x+ perp / mixed)

---

## Filtering events identified (left-to-right walk)

Repeat this card for each filtering event in the covered range.

### Event N — short label

- **Date / candle:**
- **Type:** wick / cascade / breakout / breakdown / news shock / grinding-trend
- **Range traversed:** from $X to $Y → **Z% move**
- **Probable trigger:** (news, mechanical liquidation, structure break, unknown)
- **Cohorts plausibly violated:** (list cohort labels from below)
- **Note:** anything else worth recording (e.g. timeframe of the move, whether it retraced)

---

## Cohorts present in the covered range

Repeat this card per cohort. Use ascending entry-price order so the result reads bottom-up like the chart.

### Cohort label — short, memorable, e.g. "2022-bear-lows-cash-buyers"

- **Entry price band:** $X — $Y
- **Approximate entry period:** YYYY-MM to YYYY-MM
- **Prevailing narrative when they entered:** (one sentence — what was the market story?)
- **Conviction class:** honest entry / confirmation entry / mixed
- **Probable leverage profile:** cash / low leverage (2x–5x) / mid leverage (10x–25x) / high leverage (50x+) / mixed
- **Estimated SL depth tolerance:** ±X% from average entry (psychological + mechanical)
- **What would invalidate this cohort?** Price level $Z (drawdown of W% from average entry)
- **Filtering events survived so far:** (list events from above)
- **Status as of snapshot date:** SURVIVING / PARTIALLY FILTERED / WIPED
- **Notes / caveats:**

---

## Survivor map (after applying all filtering events)

Top-down vertical ladder of cohorts that are **still in position** as of the snapshot date.

```
$ATH       ← cohort A — confirmation entry, shallow SL, first to liquidate on next correction
$..        ← cohort B — confirmation entry, deeper SL
$..        ← cohort C — honest entry, deep SL
$current   ← (mark current price relative to cohort levels)
$..        ← cohort D — honest entry from prior cycle
$LOW       ← cohort E — deep honest entry, very large SL tolerance (effectively the floor)
```

For each surviving cohort, note:

- **Entry band**
- **Remaining SL depth** (from snapshot price, not from their entry)
- **Estimated cohort weight / size** (small / medium / large — informal, based on duration of accumulation, volume profile if available)

---

## Liquidity gradient reading

- **Nearest liquidation pressure level (above current price):** $X — cohort __ (short stops cluster here if applicable)
- **Nearest liquidation pressure level (below current price):** $Y — cohort __ (long stops cluster here)
- **Liquidity vacuum zones:** ranges where no surviving cohort has entries, expect fast price action through these
- **Deep support layer:** $Z and below — honest-entry cohorts unlikely to capitulate above this

---

## Predictions derived from this map

State each as: "If [symbol] reaches [level] by [date], expect [cohort behavior] producing [magnitude] of [direction]."

Each prediction should be specific enough to falsify.

1. ...
2. ...
3. ...

If any prediction is **real-money testable** (you would actually act on it with capital), copy it into a call file in `most/journal/calls/` per `system/edge_verification.md`.

---

## Caveats and self-criticism

- Where am I most likely wrong about cohort sizes / SL depths?
- Which competing interpretation of the same chart is also plausible? Steel-man it in 1–2 sentences.
- What would I have to see to throw this map out?
- Is any part of this just confirmation of a pre-existing bias I had walking into the chart?
