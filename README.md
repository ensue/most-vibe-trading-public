# MOST · **Vibe Trading**

**Mental Operating System for Trading** — *The Vibe Trading Partner*

Trade with your charts, your exchange, and an AI that **hangs out in Cursor** like a sharp friend: pulls **live account state when you open chat**, **archives TradingView screenshots** into your journal, and helps you **think** — without pretending to be your boss.

> **Vibe Trading** = less gatekeeping, more flow. Data from the exchange first. Opinions when you ask.

---

## What makes this different

| Vibe | What you get |
|------|----------------|
| **Live state, automatically** | On every session start, sync pulls balances, open positions, and recent activity from Bitget (ccxt). You are not re-typing positions to "unlock" the chat. |
| **Consultant, not compliance** | MOST does **not** approve or reject your trades. No "PASS/FAIL" on whether you *should* have opened. Ask for a second read when you want it. |
| **Charts on file** | Paste a TradingView screenshot → it lands in `journal/charts/` with a clean name and a link in your notes. Built for how traders actually work. |
| **Your rules stay yours** | `rules.md` is *your* commitments. The AI can reflect them back — it does not play warden. |
| **Journal without the cringe** | Positions, mood, reflections, patterns — structured markdown, tables, zero essay mode. |
| **Math when you want it** | Monte Carlo (5K paths) + deterministic projection — context for variance and goals, not a lecture. |

---

## Who it's for

- You already know how markets work — execution and headspace are the hard part.
- You want **memory + structure** without another app that nags you like middle management.
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

Open the folder in **Cursor**. The rule file under `.cursor/rules/` tells the AI how MOST runs — including **sync-on-open** and **screenshot archiving**.

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

MOST is **not** "AI that lets you trade." **You** trade. MOST is **the vibe layer**: it remembers, files, syncs, and consults — so your future self and your AI partner are always looking at the **same facts**, not the story you half-remember at 1 AM.

---

## License

[MIT](LICENSE)
