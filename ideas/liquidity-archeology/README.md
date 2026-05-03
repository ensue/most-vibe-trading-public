# Liquidity Archeology — research framework

**Status:** **idea / parking lot** v0.1 (public template). Lives in `ideas/` — promote to a dedicated project folder when it has earned that status.
**Domain:** any liquid market with continuous price discovery — equity indices, crypto majors, FX, commodities
**Project home:** `ideas/liquidity-archeology/`

---

## The systemic claim

Visible price action is a **record of liquidity transfer between participant cohorts** that differ on four axes:

1. **Entry price** — where they took the position.
2. **Entry conviction** — entered **before** confirmation (during doubt) vs **after** confirmation (chasing a breakout, news, momentum).
3. **Pain tolerance** — how deep an SL they can absorb without forced exit (margin call, account size, psychology).
4. **Time horizon** — how long they planned to hold.

If you can **map** who is still in position at each price level **and** how much pain each cohort can absorb, you can predict **where forced selling / buying will appear next** — because cohorts under stress eventually capitulate, and that capitulation is the next visible candle.

---

## Why this project exists alongside the trading workspace

Many traders find that their **analytical skill** and their **execution discipline** are very different problems. Articulating "what should happen" is not the same as having edge that actually plays out, and certainly not the same as being able to execute on it without breaking risk rules.

This framework is a **separated analytical track**. It produces:

- A mental model of "who is stuck where, with how much pain tolerance"
- Testable hypotheses about future flow points (where forced exits cluster)
- Documentable predictions that feed `journal/calls/` for edge verification (see `system/edge_verification.md`)

It does **NOT** produce:

- Trade signals
- Entry / exit recommendations for live capital
- Permission to size up
- Any output that bypasses the iron rules

This is **research**, not trade planning. No position is ever opened from this framework alone. If a hypothesis from this framework justifies a paper call, that call goes through `journal/calls/` like any other call — same edge verification protocol applies.

---

## Core concepts (glossary)

| Term | Definition |
|------|-----------|
| **Cohort** | A group of participants who entered around the same price band, with similar conviction at entry and similar SL depth tolerance. Treated as one unit for the purpose of this framework. |
| **Honest entry** | A position taken **without macro / structural confirmation** — before the breakout, during the doubt phase. Implies high conviction (paid for with discomfort) and **deep** SL tolerance (because the price has already wandered against the thesis). |
| **Confirmation entry** | A position taken **after** a breakout, news catalyst, or momentum signal. Implies **low conviction** (depends on continuation) and **shallow** SL tolerance (any return into the prior range = invalidation). |
| **SL depth tolerance** | The maximum drawdown a cohort can absorb before being forced out — by margin call, margin maintenance, hard stop, or psychological breakpoint. Measured in **% from cohort's average entry**, not absolute dollars. |
| **Filtering event** | Any candle / wick / cascade that pushed price beyond one or more cohorts' SL depth, removing them from the survivor pool. |
| **Surviving cohort** | A cohort whose SL depth tolerance has **not** been violated by any filtering event since their entry. Still in position. Still has pain tolerance left. Still part of "who holds the bag" at current price. |
| **Liquidity gradient** | The current map of surviving cohorts ordered by entry price + remaining SL depth. Tells you **where the next forced-exit pressure begins** (closest unviolated stops to current price). |
| **Passport hypothesis** | The central claim: only **honest-entry cohorts** survive multi-year trends, because confirmation-entry cohorts get repeatedly liquidated by the trend's own routine volatility. The "long trend" is in fact the slow distribution from honest holders to confirmation chasers, **across** liquidation cycles. |
| **Recovery floor** | A price level whose bounce was **not** caused by new buyers but by **honest-entry holders refusing to sell** (or adding) at a level that was painful but inside their SL tolerance. Visible as a sharp wick or extended range without breakdown. |
| **Distribution wick** | A spike beyond ATH (or a major level) that liquidates short stops AND traps long entries that bought the breakout — both sides lose, smart distribution wins. |

---

## Files in this project

```
ideas/liquidity-archeology/
├── README.md                              ← this file (what + why + glossary)
├── methodology.md                         ← procedure: how to map cohorts on a chart
├── tool.py                                ← Python implementation: JSON case file → markdown report
├── case-studies/                          ← worked examples (you create these)
└── templates/
    ├── cohort-snapshot.md                 ← map cohorts at a moment in time (qualitative)
    ├── event-analysis.md                  ← analyze a specific filtering event (qualitative)
    └── case.template.json                 ← minimal JSON case for tool.py
```

## Tool — `tool.py`

Stdlib-only Python CLI. JSON in, markdown out.

```bash
python ideas/liquidity-archeology/tool.py validate case-studies/<your-case>.json
python ideas/liquidity-archeology/tool.py report   case-studies/<your-case>.json
python ideas/liquidity-archeology/tool.py liq 50                                    # % move that liquidates at 50x
python ideas/liquidity-archeology/tool.py init --symbol BTC --tf 1W --date 2026-05-15 --out case-studies/<new>.json
```

The tool computes:
- **Survivor map** — which cohorts survived which filtering events.
- **Liquidity gradient** — sorted ladder of surviving cohorts with nearest pressure prices.
- **Liquidation thresholds** — price level at which each cohort would be filtered.
- **Vacuum zones** — price ranges with no surviving cohort entries.

---

## Workflow (high level — full procedure in `methodology.md`)

1. **Select chart** — symbol + timeframe with enough history to contain at least one major filtering event. Default: monthly or weekly for indices, weekly or daily for crypto majors.
2. **Identify filtering events** — every cascade, wick, ATH break, news shock that plausibly violated some SL depth.
3. **Reconstruct cohorts** — for each major price band between filtering events, document who likely entered and what their SL tolerance looked like.
4. **Apply filtering events forward** — strike out cohorts whose SL depth was violated. What remains is the **survivor map**.
5. **Read the gradient** — where are surviving cohorts clustered? What level would force the next mass exit?
6. **State predictions** — concrete, dated, falsifiable. Log as call in `journal/calls/` if real-money testable.

---

## Status, limits, intellectual honesty

- This is a **draft framework**, not a verified theory. Every claim in `methodology.md` is a working hypothesis until repeated case studies show the framework produces falsifiable, hit-rate-better-than-random predictions.
- Per `system/edge_verification.md`: the "I'm good at TA" belief is the foundation of many gambling loops. This framework must be **tested**, not assumed. Each case study is supposed to either support or refute the passport hypothesis.
- **Knowledge–identity split warning:** being able to articulate this framework eloquently is **not the same** as being able to use it to make money. The first is intellectual; the second requires execution discipline. Keep the framework and the execution problem **separate**.
- Rename or restructure freely. "Liquidity archeology" is a working label, not a brand commitment.

---

## Attribution

Framework concept proposed by an operator using a personal MOST workspace, formalized into this generic public template (May 2026). Original phrasing: long-term trends are "carried" only by participants who entered without confirmation; everyone else is recurrent fuel for filtering events. The name "Liquidity Archeology" captures the analogy: reading current price action as a dig site that records who is still alive in each price stratum.
