# Filtering event analysis — template

Use this template to analyze a **single** filtering event in detail — a wick, cascade, breakout, or news shock that you suspect filtered cohorts. Save filled copies in `case-studies/` as `YYYY-MM-DD-symbol-event-name.md`.

Read `methodology.md` Step 1 and `README.md` glossary before filling.

---

## Header

- **Symbol:**
- **Timeframe of analysis:** (1H, 4H, 1D, 1W, 1M)
- **Event date / candle:** YYYY-MM-DD (or candle close timestamp)
- **Chart file:** `journal/charts/YYYY-MM/YYYY-MM-DD-symbol-tf-event.png`

---

## Event summary

| Field | Value |
|-------|-------|
| Event type | wick / cascade / breakout / breakdown / news shock / grinding move |
| Pre-event price | $X |
| Event extreme price | $Y (high if wick up / cascade up; low if wick down / cascade down) |
| Post-event close | $Z |
| Range traversed (extreme − pre) | $A = W% of pre-event price |
| Duration | seconds / minutes / hours / days |
| Probable trigger | (news event, mechanical liquidation cascade, structural break, unknown) |
| Volume signature | normal / elevated / extreme |

---

## Both-sides analysis (at the moment of the event)

### Side that won

- **Who:** what kind of participant was positioned correctly going into this event?
- **Entry profile:** when did they enter, at what price band, with what conviction?
- **What they earned:** approximate R-multiple / % gain on the position, **assuming** typical sizing for that participant class
- **What they probably did next:** held / partial / fully closed / re-entered (each is a separate hypothesis)

### Side that lost

- **Who:** what kind of participant was positioned incorrectly?
- **Entry profile:** entry price band, when, conviction
- **What they lost:** approximate R-multiple / % loss; was this within or beyond their SL depth tolerance?
- **Were they forced out?** (mechanical liquidation / hit SL / capitulated psychologically / still holding through pain)
- **If still holding, what is their remaining SL depth?**

---

## Cohort filter map for this event

For each cohort that existed before the event, did the event push price beyond their SL depth tolerance?

| Cohort (label) | Entry band | SL depth tolerance | Drawdown caused by event | Filtered? |
|----------------|-----------|--------------------|-------------------------|-----------|
| ... | $X–$Y | W% | Z% | YES / NO / PARTIAL |

A "PARTIAL" entry means: the event filtered the high-leverage / shallow-SL slice of the cohort but not the cash / deep-SL slice. Note this explicitly.

---

## Order book / liquidity hypothesis

If you have evidence (volume profile, footprint, on-chain liquidations data, news), state it. Otherwise state your **hypothesis** about what the event mechanically was:

- Was this a **liquidity raid** — price pushed beyond a known stop cluster, then rejected?
- Was this a **forced liquidation cascade** — one cohort's stops triggered the next cohort's stops in a chain?
- Was this **organic flow** — gradual accumulation / distribution producing the move?
- Was this a **distribution wick** — designed to liquidate shorts AND trap longs?

State which hypothesis you favor, and what evidence would support / refute each.

---

## Aftermath observation

Look at the candles **after** the event. The post-event price action is the ground truth for who survived:

- **If price recovers quickly** to a level the event "swept" — somebody was buying that level. Identify the probable buyer cohort. This is a **recovery floor**.
- **If price stays at the new level** — the move was structural; the prior cohort is gone, replaced by new entries at the new range.
- **If price continues in the event direction** — the event was the **start** of a larger filtering, not a single one. Other cohorts will be filtered in subsequent candles.

Document the post-event behavior for at least 5–10 candles after the event on the chosen timeframe.

---

## Predictions derived from this event

- Which cohorts that existed **before** this event are now the dominant survivors?
- Which **new** cohorts likely entered during or just after the event (and what is their SL depth)?
- What level / time / news would force the next filtering event for the surviving cohorts?

State each prediction in a falsifiable form. Log to `journal/calls/` if real-money testable.

---

## Self-criticism

- Am I confusing **rationalizing** the event after the fact with **predicting** the cohort dynamics?
- What is the simplest explanation that does **not** require my framework? (e.g. "It was just a news headline, no cohort theory needed.")
- If this event happened to a cohort I was **not** rooting for, would I describe it the same way? (Bias check.)
