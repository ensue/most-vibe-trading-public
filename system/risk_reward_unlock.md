# R:R unlock ladder (MOST gamification)

Machine-readable state: **`risk_reward_unlock.json`** (same folder as this file). Template ships **`risk_reward_unlock.example.json`** as defaults; forks may copy or override.

## Intent

- Start at **max planned R:R = 1:1** (reward distance to stop distance).
- **Unlock** higher ratios **only** after **proving** the current tier: **N compliant wins** at or below that cap (default **N = 5**).
- **Ceiling:** **20:1** max tier (configurable in JSON as `ceiling_max_rr`).

This is **not** permission to widen stops or break Rule 2. It only caps **how ambitious** the **take-profit** side of a **locked** plan may be relative to **1R** risk.

## Definitions

- **Planned max R:R** — For a locked plan with **one** SL and **one or more** TPs, compute R:R for each TP leg as **distance(entry → TP) ÷ distance(entry → SL)** in **price space**. Use **max** over TPs as the plan’s **planned max R:R**.
- **Long:** risk per unit = `entry − stop` (stop below entry). Reward to TP = `tp − entry`.
- **Short:** risk per unit = `stop − entry` (stop above entry). Reward to TP = `entry − tp`.

## Unlock rules

| Field | Meaning |
|--------|---------|
| `current_unlocked_max_rr` | You may plan trades with **planned max R:R ≤ this number** |
| `promotion_wins_required` | Promotion wins needed to unlock **+1** to `current_unlocked_max_rr` |
| `wins_toward_next_unlock` | Progress counter toward next tier |

**Promotion win:** Compliant trade, **planned max R:R** at lock ≤ cap, **realized R > 0**. Losses and rule breaks do not count.

**On promotion:** When wins reach required count, increment `current_unlocked_max_rr` by **1** (cap at `ceiling_max_rr`), reset progress.

## Enforcement

- **Rule 3** plans must satisfy **planned max R:R** ≤ **`current_unlocked_max_rr`**.
- AI reads **`risk_reward_unlock.json`** with **`rules.md`** when discussing entries or sizing.

## CLI

```bash
python tools/risk_reward_unlock.py status
python tools/risk_reward_unlock.py record-win
```

(Run from repo root with the repo on `PYTHONPATH` so `system/` imports resolve.)
