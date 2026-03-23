# MOST · **Vibe Trading**

**Mental Operating System for Trading** — *The Vibe Trading Partner*

Trade with your charts, your exchange, and an AI that **hangs out in Cursor** like a sharp friend: **pulls live account state when you open chat** (sync from the exchange — you are not manually inputting positions to start the session), **archives TradingView screenshots** into your journal, and helps you **consult** a plan or a read on the market — **without pretending to be your boss**.

> **Vibe Trading** = less gatekeeping, more flow. **Data from the exchange first.** Opinions when you ask.

---

## What MOST does

| Feature | How |
|--------|-----|
| **Live from the exchange** | On every new chat, the operating manual runs **sync** (Bitget via ccxt): balances, **open positions**, recent activity land in `exchange/data/`. No “type your size and side here” gate. |
| **Consultant, not compliance** | MOST is **not** your risk officer. It does **not** tell you whether you “correctly” opened a trade. It can **help you think** — HTF levels, scenario planning, headspace — when **you** invite that. |
| **Execution check (optional)** | If **you** want a mechanical compare (plan vs what’s on the exchange), you can ask; it’s **not** a mandatory PASS/FAIL boss screen. |
| **Charts on file** | Paste a **TradingView** screenshot in Cursor → MOST **logs and archives** it under `journal/charts/YYYY-MM/` with a consistent name and a link in the relevant journal note. |
| **Journal without the cringe** | Positions, mood, reflections, patterns — structured markdown, tables, not essays. |
| **Pattern language (optional)** | You can track behaviors you care about; the AI reflects **your** `rules.md` / `profile.md` — **not** a warden. |
| **Math when you want it** | Monte Carlo (5K paths) + deterministic projection — context for variance and goals, not a lecture. |
| **Behavioral context over time** | `profile.md` + journals build a **memory layer** for *your* triggers and what helps — still **you** trading. |

---

## What makes this different

| Vibe | What you get |
|------|----------------|
| **Live state, automatically** | Session start → sync. You are not re-typing positions to “unlock” the chat. |
| **Consultant, not compliance** | No default “you may not trade” / “you opened wrong” posture. Ask for a second read when you want it. |
| **Charts on file** | TradingView → `journal/charts/` + links. Built for how traders actually work. |
| **Your rules stay yours** | `rules.md` is *your* commitments. The AI can mirror them back — it does not play middle management. |
| **Journal without the cringe** | Structured markdown, tables, zero essay mode. |
| **Math when you want it** | Monte Carlo + projection when you want context, not a sermon. |

---

## Who it's for

- You already know how markets work — execution and headspace are the hard part.
- You want **memory + structure** without another app that nags you.
- You use **Cursor** and want **one workspace** that feels like *your* command deck.

---

## Quick start

```bash
git clone https://github.com/ensue/most-vibe-trading-public.git
cd most-vibe-trading-public

pip install -r exchange/requirements.txt
cp vault/bitget-api.env.example vault/bitget-api.env
# Edit vault/bitget-api.env with Bitget API keys (read-only OK for sync)

python exchange/sync.py
```

Open the folder in **Cursor**. The rule file under `.cursor/rules/` tells the AI how MOST runs — including **sync on session start** and **screenshot archiving**.

See [`SETUP.md`](SETUP.md) for full setup.

---

## Layout

```
├── .cursor/rules/trading-partner.mdc   ← MOST operating manual (Cursor loads it)
├── context.md                          ← rolling state the AI reads first
├── rules.md                            ← your personal commitments (template)
├── profile.md                          ← optional psychological / pattern context
├── exchange/sync.py                    ← Bitget → JSON + snapshot.md
├── journal/
│   ├── positions/                      ← optional plans / history
│   ├── reflections/                    ← ideas, HTF notes, narrative
│   ├── mood/                           ← energy / headspace
│   ├── patterns/                       ← behaviors you are tracking
│   └── charts/                         ← TradingView exports (archived here)
├── tools/                              ← monte_carlo.py, projection.py
├── vault/                              ← API keys (gitignored)
└── ideas/                              ← future experiments
```

---

## Exchange note

Default sync targets **Bitget** futures via ccxt. Other venues: adapt `exchange/sync.py` and credential file format.

---

## Philosophy (one paragraph)

MOST is **not** "AI that lets you trade." **You** trade. MOST is **the vibe layer**: it remembers, files, syncs, and consults — so your future self and your AI partner are often looking at the **same facts**, not the story you half-remember at 1 AM.

---

## License

[MIT](LICENSE)
