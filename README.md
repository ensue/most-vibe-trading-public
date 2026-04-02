# MOST — Mental Operating System for Trading

You already know how to trade. You've proven it a hundred times — in hindsight, in simulation, in the first five minutes after opening the exchange when everything is clear and cold.

The problem is what happens next.

---

## The Pattern

You open the exchange. You see the balance. There's a brief, clean window — maybe five minutes — where your analysis is genuinely good. Cautious. Structural. The best version of you.

Then the position is open. For a while, you don't care. Days, maybe. Then the green numbers start ticking up, and your brain converts them to hourly wages, rent payments, months of freedom. That conversion is the beginning of the end, but it feels like winning.

The first correction hits a level your plan didn't account for. Because the plan assumed price would go straight to your target. It never does, but you never plan for that.

Now you're managing. Partial TP? Hedge? Move the stop? Each decision creates a new decision surface your plan didn't cover. Each decision costs cognitive energy. By the fifth micro-decision, your analytical system is exhausted and you're betting red or green like it's a slot machine.

Or maybe you got stopped out. Now the voice says: one more trade. Same pair. Bigger size. You know this voice. You've heard it a thousand times. You've obeyed it a thousand times. You know exactly how it ends, and you do it anyway.

The belief underneath: **"I'm skilled but undisciplined."** This belief must be true, because if it isn't, then the 10,000 hours of chart-staring were wasted, and there is no redemption story coming. So the belief survives. And the loop continues.

**If you read this and thought "that's me" — this system was built for that exact moment.**

---

## What This Is

MOST is an AI accountability partner that lives in [Cursor](https://cursor.com) (AI-native IDE). Not a bot. Not signals. Not another journal app you'll abandon in a week.

It syncs live from your exchange. It remembers your patterns when you forget them. It deploys research-backed psychological interventions at the exact moment your plan starts to corrupt — using your own numbers, your own history, your own words from when you were thinking clearly.

And it does one thing no other trading tool has ever attempted: it investigates **why you actually trade** — not the story you tell yourself, but the mechanism underneath — and builds a personalized operating manual around YOUR specific brain.

```bash
git clone https://github.com/ensue/most-vibe-trading-public.git
```

Free. Open source. MIT licensed. Your data stays on your machine.

---

## Why Everything Else Failed

You've tried rules. You've tried journals. You've tried position size calculators and risk management frameworks and accountability groups and "just be disciplined."

Here's why none of it worked:

**Rules without investigation are noise.** "Don't move your stop" is a rule. But when you're staring at unrealized profit that equals two months of rent, the rule doesn't exist anymore. It was written by a different person in a different state. The activated version of you has access to a sophisticated rationalization engine that can justify anything — and you're too smart for your own rules to contain you.

**The discipline problem is not a discipline problem. It is a regulation problem.** The market provides something your life currently doesn't — stimulation, aliveness, felt power, identity confirmation, proof of earned worth. As long as the market is the primary supplier of that thing, your edge (real or imagined) will always get hijacked by the supply function. You're not trading the market. You're trading your internal state.

**Until you know what that thing is, for you specifically, rules will keep failing.** MOST is built to find it.

---

## The Three Layers

### Layer 1: Live Exchange Sync + Mechanical Verification

Every session starts with a sync — your real balances, positions, and trades pulled directly from the exchange via [ccxt](https://github.com/ccxt/ccxt) (Bitget default, 100+ exchanges supported).

You state a plan. Entry, stop, target, size, thesis. The AI locks it. You execute on the exchange. You sync again. The AI compares what's on the exchange to what you agreed:

**PASS** or **MISMATCH.**

Not opinion. Not approval. Verification. Did the human do what the human said it would do? If not, the mismatch is named, logged, and tracked. No soft language.

### Layer 2: Psychological Investigation

This is where MOST diverges from every other tool.

The AI runs a structured investigation — not generic personality typing, but operational mechanism-finding:

- **What happens in the first 30 seconds after you open the exchange?**
- **What internal state precedes the urge to trade?**
- **What is the full phase sequence from opening to blowup?**
- **What does the market give you that nothing else currently does?**
- **What are the real, non-market sources of aliveness in your life?**

Findings accumulate in `synthesis/mechanism-map.md`. The same approach that works for debugging code — isolate the mechanism, name it, make it reproducible, then engineer around it — applied to debugging behavior.

This is not therapy. This is root cause analysis.

### Layer 3: Personalized Playbook

From the investigation, the system builds `playbook/modus-operandi.md` — a trading method designed around your failure modes:

- **Trade structure** matched to your decision-fatigue profile (not generic "use partials")
- **Named traps** — your patterns, given names, with recognition cards you can spot in real-time
- **Zero-decision position management** — every action pre-committed before entry; nothing left to real-time judgment when you're activated
- **Post-trade protocols** that specifically counter YOUR post-trade failure modes
- **State regulation map** — which internal states are dangerous, which are safe, what helps in each

The playbook isn't written from a textbook. It's written from YOUR investigation. Two traders using MOST will have different playbooks because they have different mechanisms.

---

## Named Traps (examples from real investigation)

These aren't hypothetical. They were surfaced through actual investigation sessions and given names so they can be recognized in real-time:

| Trap | What the brain says | What's actually happening |
|------|--------------------| -------------------------|
| **Recovery shortcut** | "One big trade fixes everything" | Every cascade you've ever had started with this sentence |
| **Small-position revulsion** | "This $3 profit isn't worth my time" | The root cause of all oversizing — disciplined size doesn't produce the feeling you're looking for |
| **Reversal-after-close** | "If I closed, I should reverse, otherwise closing was pointless" | Every exit becomes a new unplanned entry |
| **Post-partial vacuum** | "This small runner is boring, let me find something else" | Context-switching mid-position leads to hedges, cross-financing, chaos |
| **uPNL-to-wages conversion** | "That's three days of salary sitting there" | Converts abstract R into emotional possession; locks moonshot attachment |
| **Tight-SL size maximization** | "I see the exact bottom, SL can be tight" | Escalation wearing risk-management clothes. Fees eat 12%+ of each R |
| **Edge identity shield** | "I'm skilled, I just need discipline" | Untested hypothesis protecting a sunk-cost identity. The prediction journal exists to test it with data, not belief |
| **Decision fatigue roulette** | "I'll just take a quick position" | Analysis exhausted. Trading has become random betting |

Your traps will be different. The framework for finding and naming them is the same.

---

## Edge Verification

The most dangerous belief in trading is "I have edge but lack discipline."

If the edge is real, discipline is the whole game. If the edge is illusory, discipline is irrelevant — you're optimizing the execution of a losing strategy.

MOST includes a **prediction journal** — log chart calls with timestamps BEFORE the move. No position required. No risk. After 30+ logged predictions, the data answers whether your analytical skill is real or whether it's selective memory dressed as competence.

This is the single most important question you can answer with data instead of belief. Most traders never ask it because the answer might end the story they're telling themselves.

---

## Psychological Toolkit

Not affirmations. Not "don't be emotional." Research-backed behavioral interventions deployed at specific trigger moments:

| Intervention | Source | When it fires |
|---|---|---|
| **Pre-mortem** | Klein, 2007 | Before every plan lock — "describe how this trade leads to rule-breaking" |
| **Abstinence Violation Effect firewall** | Marlatt & Gordon, 1985 | After first rule break — contains the cascade before it multiplies |
| **Implementation intentions** | Gollwitzer, 1999 | Pre-committed if-then responses to known triggers |
| **Urge surfing** | Marlatt, 1985 | When activation language detected — 15min structured observation |
| **Cognitive defusion** | Hayes, 2004 | When rationalization patterns appear in speech |
| **Behavioral chain analysis** | Linehan, 1993 | After every rule violation — full vulnerability-to-consequence map |
| **Decision fatigue budget** | Baumeister, 1998 | Tracks decisions per session; flags degradation at 5 and 8 |

---

## XP + Progression

Discipline is boring. The system must feel like something or it gets abandoned.

Every compliant trade, every resisted urge, every pre-mortem completed, every prediction logged earns XP. Every violation costs XP. Visible in every response, not buried in a config file.

The progression isn't cosmetic — it gates real operational freedom. Start with one position, fixed size, full handholding. Earn your way to partial takes, runners, Kelly sizing. Prove discipline with data, not promises.

---

## Who This Is For

- You've been trading for years and your net P&L is negative despite "knowing what you're doing"
- You've tried rules, journals, accountability — all of it worked for a week
- You suspect the problem is deeper than discipline but you've never had a framework to investigate it
- You're technical enough to work in an IDE and you'd rather `git clone` than sign up for another SaaS
- You're honest enough to let a system track your actual behavior, not the behavior you wish you had

## Who This Is NOT For

- Beginners looking for trading education
- People who want signals, bots, or automated trading
- Anyone looking for permission to trade ("the AI confirmed my thesis" will never happen here)

---

## Quick Start

```bash
git clone https://github.com/ensue/most-vibe-trading-public.git
cd most-vibe-trading-public

pip install -r exchange/requirements.txt
cp vault/bitget-api.env.example vault/bitget-api.env
# Add your exchange API keys (read-only is fine for sync)

python exchange/sync.py
```

Open in [Cursor](https://cursor.com). The `.cursor/rules/trading-partner.mdc` is the AI's operating manual — loaded automatically. First conversation, it syncs your exchange, reads your state, and starts working.

See [`SETUP.md`](SETUP.md) for full configuration.

---

## Layout

```
.cursor/rules/trading-partner.mdc   <- AI operating manual (auto-loaded by Cursor)
context.md                          <- current state — AI reads first, every session
rules.md                            <- your rules (template — customize to your life)
profile.md                          <- your patterns (accumulates over time)
synthesis/
  mechanism-map.md                  <- your psychological mechanism map
playbook/
  modus-operandi.md                 <- your personalized trading method
system/
  flow.md                           <- deterministic processing pipeline
  edge_verification.md              <- prediction journal protocol
  progression.md                    <- XP system design
exchange/
  sync.py                           <- exchange data -> workspace
journal/
  positions/                        <- trade plans + outcomes
  chapters/                         <- live trajectory + postmortems
  calls/                            <- prediction journal (edge verification)
  investigations/                   <- psychological mechanism-finding
  mood/                             <- state tracking (AI logs from conversation)
  patterns/                         <- behavioral patterns + chain analyses
  charts/                           <- TradingView screenshots (archived)
tools/
  monte_carlo.py                    <- 5,000-path probability simulation
  projection.py                     <- deterministic compound growth model
  progression.py                    <- XP calculator
```

---

## Not Locked to Bitget

Ships with Bitget futures. Runs on [ccxt](https://github.com/ccxt/ccxt) — Binance, Bybit, OKX, and 100+ exchanges are adapter-level work. See [`exchange/README.md`](exchange/README.md).

---

## Philosophy

The gap between knowing and doing is not a willpower gap. It is a **regulation gap**.

The market is the fastest universal source of felt aliveness. Seen a balance? Power. Green numbers ticking? Ecstasy. Getting stopped? Pain so sharp it proves you exist. For someone whose baseline state is flat — bored, under-stimulated, identity-wounded, alone — the market is not a financial instrument. It is a nervous system regulator.

Rules fail because they were written by the calm version of you for the activated version of you, and the activated version has administrative access to override everything. The only thing that survives activation is **pre-committed structure** — decisions made before the trigger, engineering that doesn't require willpower in the moment.

MOST is that engineering. Investigate the mechanism. Name the traps. Pre-commit every decision. Verify execution mechanically. Earn freedom with data.

Your future self and your AI partner looking at the same facts. Not the story you half-remember at 1 AM with your finger on the buy button.

---

## License

[MIT](LICENSE)
