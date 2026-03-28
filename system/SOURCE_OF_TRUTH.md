# Source of truth — money, risk, and intervention math

Universal layout: **no hardcoded dollar amounts in AI rules or `flow.md`**. Forks read their own `rules.md` and optional JSON; the public template stays anonymous.

## Priority (highest wins)

1. **Vault env** (`vault/bitget-api.env` or your CEX vault) — `MOST_R_UNIT_USD`, `MOST_MENTAL_BANKROLL_USD` when set.
2. **`exchange/accounting_config.json`** (gitignored) — copy from `exchange/accounting_config.example.json`; `r_unit_usd`, `mental_bankroll_usd`.
3. **`system/calibration.json`** (gitignored) — copy from `system/calibration.example.json`; optional `currency`, `intervention_recovery_weeks_per_trade_estimate`, etc.
4. **`rules.md`** — human-readable authority for **phase**, **% of capital**, and how dollar risk is defined (always read this; numbers here override nothing in JSON until you copy them into config).

## Machine-readable merge

`python` API (same merge as accounting + system extras):

```bash
python -c "from system.calibration import load_calibration; print(load_calibration())"
```

(From another working directory, add the repo root to `PYTHONPATH`.)

## What the AI must do

- **Sizing / Rule 2:** Read **`rules.md`** for the rule text; use **`r_unit_usd`** from `load_calibration()` when present for numeric work; if still `None`, derive from `rules.md` (e.g. fixed % × declared capital) or ask the user to set `accounting_config.json` / vault.
- **Intervention (damage report):** Use **only** figures from **exchange sync outputs** (`exchange/data/*`), **journal**, and **`load_calibration()`** — never invented round numbers. Placeholders in docs are `[$SESSION_LOSS]`, `[R_UNIT]`, `[N]` — never literal `$40` / `$86` in shared files.

## Duplication note

`r_unit_usd` / `mental_bankroll_usd` appear in both `exchange/accounting_config` and vault by design: one place for **accounting labels**, same values for **risk + intervention**. Optional `system/calibration.json` adds non-exchange fields without touching the exchange folder.
