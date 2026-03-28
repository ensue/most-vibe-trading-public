# MOST — Vibe Trading

**Mental Operating System for Trading** — an AI accountability partner that lives in your IDE.

You trade with your charts, your exchange, your edge. MOST is the layer between your analysis and your execution — it **syncs live from the exchange**, **archives your charts**, **tracks your patterns over time**, and deploys **research-backed psychological tools** at the exact moment your brain tries to override your plan.

> **Vibe Trading** = data first, opinions when you ask, accountability always.

---

## The Problem This Solves

You know how to trade. You've proven it in simulation, in analysis, in hindsight. The failure is never the thesis — it's what happens between the thesis and the execution, and especially what happens in the 5 minutes after a stop-out.

MOST doesn't try to make you a better analyst. It's built for the gap between knowing and doing.

---

## What MOST Does

**Live exchange state** — Every new chat runs `sync.py` (Bitget default, any [ccxt](https://github.com/ccxt/ccxt)-supported exchange is a small fork). Balances, open positions, recent trades land in `exchange/data/`. No manual input to start a session.

**Structured plan-and-verify loop** — State your plan (entry, SL, TP, size, thesis). Lock it. Execute on the exchange. Sync. The AI compares what's on the exchange to what you agreed — PASS or MISMATCH. Not approval — verification.

**Psychological toolkit** — Not generic advice. Research-backed behavioral interventions deployed at trigger moments:

| Tool | What it does | When it fires |
|------|-------------|--------------|
| **Pre-mortem** (Klein, 2007) | "Describe the scenario where this trade leads to you breaking rules" | Before every plan lock |
| **AVE firewall** (Marlatt & Gordon, 1985) | Contains first violation before it cascades | Between rule break #1 and #2 |
| **Implementation intentions** (Gollwitzer, 1999) | Pre-committed if-then responses to triggers | When trigger pattern matches |
| **Urge surfing** (Marlatt, 1985) | 15-minute structured observation of the urge wave | When activation language detected |
| **Cognitive defusion** (Hayes, 2004) | Separates you from the rationalization | When plan corruption language appears |
| **Affect labeling** (Lieberman, 2007) | One-word emotion naming reduces amygdala ~30% | When user is clearly activated |
| **Behavioral chain analysis** (Linehan, 1993) | Maps full vulnerability-to-consequence sequence | After every rule violation |
| **Decision fatigue budget** (Baumeister, 1998) | Counts decisions per session, flags degradation | At 5 and 8 decisions |

**Chapter narratives** — Live trajectory analysis that predicts danger before it arrives, not post-mortems after the damage. The AI opens with where you're heading, not "how are you feeling?"

**Pattern memory** — Your `profile.md` accumulates behavioral patterns over time. The AI remembers what you forget — not market patterns, but *your* patterns.

**XP progression** — Gamified discipline tracking. Every compliant trade, every verification, every resisted urge earns XP. Every violation costs. Visible in every response, not buried in a file.

**Journal without the cringe** — Positions, mood, reflections, patterns. Structured markdown, not essays. The AI writes it for you from the conversation.

**Growth math** — Monte Carlo (5,000 paths) + deterministic projection. Context for variance and goals, not a lecture.

---

## Seven Rules (template — you customize)

1. **Pre-trade pause** — open workspace, state thesis, hear response
2. **Max risk per trade** — fixed %, absolute number, no "roughly"
3. **Plan before entry** — entry, SL, TP, size, thesis + pre-mortem + liq check
4. **No SL widening** — toward entry or stays. No exceptions.
5. **Cooldown after loss** — minimum time gaps, enforced from exchange timestamps
6. **Single position** (calibration phase) — one at a time until discipline is proven
7. **System accountability** — measured by losses prevented, not trades generated

---

## What Makes This Different

| Other tools | MOST |
|-------------|------|
| Manual position entry | Live sync from exchange |
| Generic risk warnings | Your own patterns, reflected back with your own history |
| "Don't be emotional" | Research-backed intervention at the exact trigger moment |
| Post-mortem only | Live trajectory prediction + post-mortem |
| Rules as text | Rules enforced through structured verification loop |
| Journal as chore | Journal written for you from conversation |
| Willpower-based | Engineering-based (friction, commitment devices, pre-commitment) |

---

## Who It's For

- You already know how markets work — execution and headspace are the hard part
- You've tried discipline before and it worked... until it didn't
- You want **memory + structure** without another app that nags you
- You use **Cursor** and want one workspace that feels like your command deck

---

## Quick Start

```bash
git clone https://github.com/ensue/most-vibe-trading-public.git
cd most-vibe-trading-public

pip install -r exchange/requirements.txt
cp vault/bitget-api.env.example vault/bitget-api.env
# Edit vault/bitget-api.env with your exchange API keys (read-only OK for sync)

python exchange/sync.py
```

Open the folder in **Cursor**. The `.cursor/rules/trading-partner.mdc` tells the AI how MOST works — sync on session start, screenshot archiving, plan verification, pattern detection, psychological interventions.

Optional — progression system:

```bash
python tools/progression.py
```

See [`SETUP.md`](SETUP.md) for full setup and exchange configuration.

---

## Layout

```
.cursor/rules/trading-partner.mdc   <- AI operating manual (Cursor loads automatically)
context.md                          <- rolling state — AI reads first every session
rules.md                            <- your rules (template — customize)
profile.md                          <- behavioral patterns (builds over time)
system/
  flow.md                           <- deterministic processing pipeline
  progression.md                    <- XP system design
  progression_state.json            <- current XP/level
exchange/
  sync.py                           <- exchange -> JSON + snapshot.md
  README.md                         <- how to connect your exchange
journal/
  positions/                        <- trade plans + outcomes
  chapters/                         <- live trajectory + postmortems
  reflections/                      <- ideas, analysis, implementation intentions
  mood/                             <- energy / headspace (AI logs implicitly)
  patterns/                         <- behavioral patterns + chain analyses
  charts/                           <- TradingView screenshots (archived)
tools/
  monte_carlo.py                    <- 5K path simulation
  projection.py                     <- deterministic compound growth
  progression.py                    <- XP calculator
vault/                              <- API keys (gitignored)
```

---

## Exchanges — Not Locked to Bitget

Ships with **Bitget** futures. Everything runs through **[ccxt](https://github.com/ccxt/ccxt)** — Binance, Bybit, OKX, and 100+ other exchanges are adapter-level work. See [`exchange/README.md`](exchange/README.md) for the swap checklist.

---

## Philosophy

MOST is not "AI that lets you trade." You trade. MOST is the accountability layer: it remembers your patterns when you forget them, deploys psychological tools when your brain is trying to override your plan, and makes the concrete cost of breaking rules viscerally clear — using your own numbers, your own history, your own words from when you were thinking clearly.

The vibe: your future self and your AI partner are looking at the same facts. Not the story you half-remember at 1 AM.

---

## License

[MIT](LICENSE)
