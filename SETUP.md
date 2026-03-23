# MOST — Setup (Vibe Trading)

## What you are installing

**MOST** = **Mental Operating System for Trading**. In Cursor, the AI acts as **The Vibe Trading Partner**: syncs your exchange when chat starts, archives chart screenshots, journals in structured markdown, and consults when you ask — **without** acting as trade approval software.

## Requirements

- [Cursor](https://cursor.sh) (AI-enabled plan)
- Python **3.10+**
- [Bitget](https://www.bitget.com) account + API keys (read-only is fine for sync-only use)

## Steps

### 1. Clone

```bash
git clone https://github.com/ensue/most-vibe-trading-public.git
cd most-vibe-trading-public
```

### 2. Dependencies

```bash
pip install -r exchange/requirements.txt
```

### 3. Credentials

```bash
cp vault/bitget-api.env.example vault/bitget-api.env
```

Edit `vault/bitget-api.env` with `BITGET_API_KEY`, `BITGET_API_SECRET`, `BITGET_PASSPHRASE`.  
`vault/` is gitignored — never commit keys.

### 4. First sync

```bash
python exchange/sync.py
```

Check `exchange/data/snapshot.md` — balance, open positions, recent orders.

### 5. Open in Cursor

Open this folder as a workspace. The file `.cursor/rules/trading-partner.mdc` is loaded automatically and defines MOST behavior: **startup sync**, **Monte Carlo refresh**, **screenshot archiving**, **consultant tone**.

### 6. Fill your numbers

Edit `rules.md` and `context.md` with your declared capital, risk %, goals, and any personal commitments. These are **yours** — the AI references them; it does not "enforce" them as an authority.

### 7. Git (your fork)

```bash
git checkout -b develop   # optional personal branch
git add .
git commit -m "My MOST setup"
```

---

## Daily use

1. Open Cursor → new chat in this workspace.  
2. AI runs sync — **positions and balance appear from the exchange**.  
3. Paste TradingView screenshots when you want them **logged and filed**.  
4. Ask for consultation (levels, risk framing, journal entry) when **you** want it.

---

## Adapting sync for another exchange

Replace `ccxt.bitget` in `exchange/sync.py` with your venue, adjust credential env names in `vault/bitget-api.env.example`, and verify field mappings for positions/orders.
