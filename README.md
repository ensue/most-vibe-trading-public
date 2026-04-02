# MOST — Mental Operating System for Trading

An AI accountability partner that lives in your IDE. Not a trading bot. Not a signal service. Not a journal app.

MOST is the layer between your analysis and your execution — it **syncs live from the exchange**, **maps your psychological patterns**, **builds a personalized operating manual around your specific brain**, and deploys interventions at the exact moment your plan starts to corrupt.

> **The insight:** Most traders don't fail because of bad analysis. They fail because the market is being used to regulate an internal state — boredom, emptiness, identity wound, stimulation deficit. As long as that's true, any real edge gets hijacked. MOST makes the regulation visible so the edge can operate cleanly.

---

## What Makes This Different From Everything Else

| What you've tried | What MOST does differently |
|---|---|
| "I need more discipline" | Maps **why** discipline fails — the specific psychological mechanism, not the symptom |
| Generic trading journal | AI writes it from conversation. Structured. Positions, mood, patterns, charts — no essays |
| Risk management rules | Rules + **verification loop**: plan → execute → sync → AI compares → PASS/MISMATCH |
| Post-mortem after blowup | **Live trajectory prediction** — danger flagged before it arrives |
| "Don't be emotional" | Research-backed psychological interventions at exact trigger moments |
| Willpower | Engineering: friction, pre-commitment, decision surface minimization |
| One-size-fits-all method | **Personalized modus operandi** built from investigation of YOUR specific patterns |

---

## The Three Layers

### Layer 1: Exchange Sync + Verification

Every session starts with `sync.py` — live balances, positions, recent trades from your exchange (Bitget default, any [ccxt](https://github.com/ccxt/ccxt)-supported exchange). The AI compares what's on the exchange to what you agreed. Not opinion — facts.

### Layer 2: Psychological Investigation

MOST doesn't assume it knows your problem. It runs a structured investigation:

- **What does the market give you in the first 30 seconds?** (power? stimulation? escape?)
- **What state appears before the urge?** (boredom? emptiness? status injury?)
- **What is the full sequence from opening the exchange to blowing up?**
- **What real sources of aliveness exist outside the market?**

Findings accumulate in `synthesis/mechanism-map.md`. When they recur enough to be operational truth, they promote to `profile.md`. This is not therapy — it is mechanism-finding. The same approach that works for debugging code, applied to debugging behavior.

### Layer 3: Personalized Playbook

From the investigation, MOST builds `playbook/modus-operandi.md` — a trading operating manual designed around YOUR psychology:

- **Trade structure** chosen to match your decision-fatigue tolerance (not a generic "use partials")
- **Named traps** with recognition cards (your patterns, your trigger signs, your countermeasures)
- **Zero-decision position management** — everything pre-committed, nothing left to real-time judgment
- **Post-trade protocols** that specifically address YOUR post-trade failure modes
- **Between-trades menu** — what to do when flat and restless that isn't gambling
- **Progression path** — how to earn more freedom over time with compliance data

---

## Psychological Toolkit

Not generic advice. Research-backed interventions deployed at trigger moments:

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

---

## Edge Verification (Anti-Narrative Protocol)

The belief "I'm skilled but undisciplined" is the foundation of the gambling loop. If the skill is real, the problem is solvable. If it's illusory, the loop is eternal.

MOST includes a **prediction journal** (`journal/calls/`) — log chart predictions with timestamps BEFORE the move. No position required. After 30+ calls, the data answers whether edge exists or whether it's selective memory. This is the single most important question a trader can answer with data instead of belief.

---

## Seven Rules (template — customize)

1. **Pre-trade pause** — open workspace, state thesis, hear response
2. **Max risk per trade** — fixed %, absolute number, no "roughly"
3. **Plan before entry** — entry, SL, TP, size, thesis + pre-mortem + fee drag check
4. **No SL widening** — toward entry or stays. No exceptions.
5. **Cooldown after loss** — minimum time gaps, enforced from exchange timestamps
6. **Single position** (calibration phase) — one at a time until discipline is proven
7. **System accountability** — measured by losses prevented, not trades generated

---

## Who It's For

- You already know how markets work — execution and psychology are the hard part
- You've tried discipline before and it worked... until it didn't
- You suspect the problem is deeper than "just follow the rules" but you don't know what it is
- You want **memory + structure + investigation** without another app
- You use **Cursor** and want one workspace that is your trading command center

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
.cursor/rules/trading-partner.mdc   <- AI operating manual (loaded automatically)
context.md                          <- rolling state — AI reads first every session
rules.md                            <- your rules (template — customize)
profile.md                          <- behavioral patterns (builds over time)
synthesis/
  mechanism-map.md                  <- YOUR psychological mechanism map (built with AI)
playbook/
  modus-operandi.md                 <- YOUR personalized trading method (built from synthesis)
system/
  flow.md                           <- deterministic processing pipeline
  edge_verification.md              <- prediction journal protocol
  progression.md                    <- XP system design
  progression_state.json            <- current XP/level
exchange/
  sync.py                           <- exchange -> JSON + snapshot.md
  README.md                         <- how to connect your exchange
journal/
  positions/                        <- trade plans + outcomes
  chapters/                         <- live trajectory + postmortems
  calls/                            <- prediction journal (edge verification)
  investigations/                   <- psychological mechanism-finding
  reflections/                      <- ideas, analysis, implementation intentions
  mood/                             <- energy / headspace (AI logs implicitly)
  patterns/                         <- behavioral patterns + chain analyses
  speech/                           <- language pattern analysis
  charts/                           <- TradingView screenshots (archived)
tools/
  monte_carlo.py                    <- 5K path simulation
  projection.py                     <- deterministic compound growth
  progression.py                    <- XP calculator
vault/                              <- API keys (gitignored)
```

---

## Exchanges — Not Locked to Bitget

Ships with **Bitget** futures. Everything runs through **[ccxt](https://github.com/ccxt/ccxt)** — Binance, Bybit, OKX, and 100+ other exchanges are adapter-level work. See [`exchange/README.md`](exchange/README.md).

---

## Philosophy

MOST is built on one observation: **the gap between knowing and doing is not a discipline problem. It is a regulation problem.** The market provides something — stimulation, identity, escape, power — that ordinary life currently does not. Until you understand what that something is, rules will keep failing.

The system works in three stages:
1. **Investigate** — find the mechanism (what the market is actually doing for you)
2. **Engineer** — build a personalized operating manual that accounts for YOUR specific failure modes
3. **Verify** — prove edge exists with data, not belief; earn freedom with compliance, not promises

The vibe: your future self and your AI partner are looking at the same facts. Not the story you half-remember at 1 AM.

---

## License

[MIT](LICENSE)
