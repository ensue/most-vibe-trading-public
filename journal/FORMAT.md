# Journal format — readable logs

Rules for everything under `journal/**` (and AI-written entries). Optimized for **raw editor view** and preview: scannable, no ragged ASCII grids.

## Prefer

### Key–value lines

One fact per line. Use an em dash (—) between label and value (or a colon if you prefer).

**Time** — End of day, pre-sleep  
**Energy** — Tired (good day)

Leave a **blank line** before a new subsection.

### Section cards (indexes, rolling logs)

Use `###` headings as row substitutes. Newest-first is fine.

### YYYY-MM-DD · SYMBOL · TF

- **Observation:** …
- **Links:** [chart](../charts/…/….png) · [note](….md)

### Checklists

Use task list syntax:

- [ ] Margin deposited  
- [ ] Exchange sync run  

### Side-by-side ideas

**Asset A** — …  
**Asset B** — …

Or two short `##` subsections.

### Options (partials, scenarios)

A small `####` block per option instead of a multi-column table.

## Avoid

- Pipe tables for **two-column field dumps** — use label–value lines.
- Wide tables with long prose in cells — use bullets under a heading.

## Exceptions

- Workspace `context.md` (or equivalent) may use compact dashboard tables.
- Rare narrow numeric tables are OK if cards would be worse.

When in doubt, match the latest entry written to this format.
