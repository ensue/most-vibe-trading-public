# MOST — First-Time Setup

## Prerequisites

- [Cursor IDE](https://cursor.sh) with an AI-enabled subscription
- Python 3.10+
- A Bitget exchange account (or another ccxt-supported exchange — see README for adaptation)

## Step 1 — Clone and open

```bash
git clone https://github.com/ensue/most-ai-trading-consultant.git
cd most-ai-trading-consultant
```

Open the folder as a workspace in Cursor IDE.

## Step 2 — Install Python dependencies

```bash
pip install -r exchange/requirements.txt
```

## Step 3 — Set up API credentials

1. Create a **read-only** API key on Bitget (no trade/withdraw permissions for safety during setup)
2. Copy the example env file and fill in your credentials:

```bash
cp vault/bitget-api.env.example vault/bitget-api.env
```

3. Edit `vault/bitget-api.env` with your actual API key, secret, and passphrase

## Step 4 — Test exchange sync

```bash
python exchange/sync.py
```

You should see balance, positions, and trade history fetched. Check `exchange/data/snapshot.md` for results.

## Step 5 — Start your first session

Open a conversation in Cursor. The AI will:
1. Run the exchange sync and Monte Carlo simulation automatically
2. Read your current state files
3. Present a status block
4. Guide you through initial configuration

In this first session, you'll agree on:

| Parameter | Description | Example |
|---|---|---|
| Declared capital | Total amount committed to trading (can be virtual/mental bankroll) | $2,000 |
| Physical margin | Amount deposited on exchange | $250 |
| Risk percentage | Fixed % of declared capital per trade | 2% |
| Goal | Target account value | $10,000 |

The AI fills in `rules.md` and `context.md` with your numbers and generates growth projections.

## Step 6 — Build your profile

`profile.md` starts blank. The AI builds it from conversations over time — your patterns, triggers, cognitive style, what works and what doesn't. You can also fill in the core facts section yourself during the first session.

Be honest. This file exists so the AI can catch your patterns, not judge you.

## Step 7 — Initialize your own git branch

The template ships on `main`. For your personal use:

```bash
git checkout -b develop
git add .
git commit -m "Personal MOST setup"
```

## What happens next

- **Before every trade:** open Cursor, talk to the AI, state your plan
- **After opening a position:** run `python exchange/sync.py` and say "verify"
- **After every session:** the AI updates your journal, context, and summaries automatically
- **After 50 compliant trades:** the system transitions from fixed % to Half Kelly sizing

## File structure

```
├── .cursor/rules/trading-partner.mdc  ← AI operating manual
├── context.md                         ← AI loads first every session
├── rules.md                           ← your iron rules
├── profile.md                         ← psychological profile (AI builds over time)
├── exchange/
│   ├── sync.py                        ← pulls live data from Bitget
│   └── data/                          ← JSON + snapshot (gitignored)
├── journal/
│   ├── positions/                     ← trade plans + outcomes
│   ├── reflections/                   ← market analysis, ideas
│   ├── mood/                          ← emotional state tracking
│   ├── patterns/                      ← behavioral pattern observations
│   └── charts/                        ← TradingView screenshots
├── tools/
│   ├── monte_carlo.py                 ← probability simulation
│   └── projection.py                  ← deterministic growth model
├── vault/                             ← API keys (gitignored)
└── ideas/                             ← future experiments
```
