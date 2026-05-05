# Call — [SYMBOL] [DIRECTION] [TIMEFRAME]

**Logged** — YYYY-MM-DD HH:MM UTC
**Symbol** — e.g. SOL/USDT
**Tier** — memecoin / midcap / highcap   <!-- one of three; see legend below -->
**Timeframe** — e.g. 4H
**Direction** — long / short
**Confidence** — 1-5

## Setup

**Entry zone** — $X.XX – $X.XX
**Stop loss** — $X.XX (structural reason: ___)
**Take profit** — TP1: $X.XX / TP2: $X.XX
**Planned R:R (max)** — X:1   <!-- max(TP - entry) / (entry - SL) across TPs; bucket below -->
**R:R bucket** — `<=1:1` / `1:1–1.5:1` / `1.5–2:1` / `2–3:1` / `3–5:1` / `>5:1`
**Entry method** — `market_wick` / `limit_at_level` / `close_confirmation` / `market_chase`
**Trigger condition** — explicit: e.g. "close of 1H candle below $X.XX with body, NOT just wick" or "limit fill at $X.XX" or "wick into zone $X.XX–$Y.YY then immediate reversion"
**Multi-TF context** — D1: ___ | H4: ___ | H1: ___   <!-- one short clause each; see legend -->
**Expiry** — YYYY-MM-DD HH:MM UTC (setup void after this)

## Thesis (one sentence)

___

## Outcome

**Status** — PENDING / HIT / MISS / EXPIRED / PARTIAL
**Triggered** — yes / no (did price enter entry zone?)
**Trigger time** — YYYY-MM-DD HH:MM UTC
**Result time** — YYYY-MM-DD HH:MM UTC
**Realized R** — (if triggered: distance to exit / distance entry-to-SL)

## Notes

_(optional: what the chart did, what you learned, screenshot link)_

---

## Field legend (do not delete — kept for reference)

### Tier (operator-defined buckets)

- **memecoin** — coins with no fundamental valuation anchor; price = pure narrative + meme cohort.
- **midcap** — top-100 utility / L1 / L2 with real but limited liquidity (e.g. NEAR, INJ, AVAX).
- **highcap** — top-10 by liquidity, deepest order book, lowest noise floor (BTC, ETH, SOL, BNB).

If the symbol genuinely doesn't fit, tag the closest bucket and note the ambiguity in **Notes**. Don't invent a fourth bucket — the point is to keep slices comparable.

### R:R bucket

Computed from the **plan**, before trigger. Use the **largest** TP distance over the SL distance (the "max R:R" the plan tries to harvest). Bucketing exists so we can see whether your edge is in tight scalps (≤1:1), moderate (1:1–2:1), or moonshots (>5:1). The R:R bucket question is: **for which planned-RRR slice is your detection actually paying off?**

### Entry method (data, not policy)

| Tag | Meaning | Why we track it |
|---|---|---|
| `market_wick` | Market order timed to a wick on a tested zone (Wick Protocol territory). | Hypothesis: operator believes there is edge in catching wicks. Data answers. |
| `limit_at_level` | Resting limit at a structural level — fills passively. | Lowest fee drag (maker). Lowest impulse risk. |
| `close_confirmation` | Wait for a candle close confirming the reaction in the new interval before entering. | Anti-impulse, anti-pico-top. Test whether waiting changes hit rate. |
| `market_chase` | Market order entered after the move has already started (FOMO, "I'll catch the runner"). | Self-flag for the worst entry mode. Expect lowest hit rate; data confirms. |

**This is a tag, not a constraint.** No method is "forbidden." After ≥ 30 calls the aggregate per-method hit rate decides what's actually working for the operator's detection style.

### Multi-TF context

Format: one short clause per timeframe. Examples:
- D1: "in 30-day range, near upper third"
- H4: "third lower-low after triangle break"
- H1: "stochastic %K crossing 80, no upper-band touch yet"

The point is **disclosed context**, not narrative essay. If the entry's thesis only depends on H1, you can write "—" on D1/H4 — but you must have *checked* and decided no higher-TF context is in conflict. The discipline value is in the check, not the prose.
