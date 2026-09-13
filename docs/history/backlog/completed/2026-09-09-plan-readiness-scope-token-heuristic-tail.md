# Plan-readiness Review Scope token heuristic tail

Status: done
Origin: r2 review F10/F11 (docs/reviews/2026-09-09-plan-authoring-tooling-polish-code-review-r2.md, overflow manifest; branch 2026-09-08-plan-authoring-tooling-polish). Extended with r3 findings F2/F3 and the r3 overflow manifest shapes (docs/reviews/2026-09-09-plan-authoring-tooling-polish-code-review-r3.md, 2026-09-09).

## Problem

Residual fail-open shapes in `_review_scope_path_token` and the `Files:` collection heuristic in `scripts/plan_readiness.py` (Review Scope category gate, `review_scope_problem`). All are off-convention authoring styles the current heuristic does not model, deferred as hardening rather than fixed in the fold rounds.

- **F10 (first-backtick-wins prose item)**: `_review_scope_path_token` takes the FIRST backticked span of a list item. A prose item with two backticked spans (e.g. `- see `docs/a.md` and also `docs/b.md``) yields the first span as the "path" even when the item is not a path entry at all; the extracted token can be a false path or mask the real one.
- **F11 (space paths + uppercase FILES:)**: an unbackticked path containing spaces takes only the first whitespace-delimited token (a space-bearing path is truncated), and a `FILES:` (uppercase) line does not match the `Files:` opener at all, so the block is never collected. Both shapes bypass the inventory coverage check silently.
- **r3 F2 (in-tick annotation)**: an annotation inside the backtick span (`- `src/service.py (new; this plan)``) extracts with the annotation attached; no suffix or duplicate match fires and only check (c) survives via the raw-text boundary fallback. Location: `_review_scope_path_token` (first-span branch), scripts/plan_readiness.py around the backtick search. Candidate fix: strip a trailing parenthesized annotation inside the extracted span, or require the span to look path-like (contains `/` or a known suffix) before it wins. Source: r3 review F2, deferred 2026-09-09.
- **r3 F3 (bare `Files:` echo re-opens collection)**: a second bare `Files:` line inside a task section (e.g. a `Notes:` echo followed by note bullets) re-opens collection and harvests one-word note tokens as phantom paths. Location: `_review_scope_task_files`, the `line.startswith("Files:")` branch (scripts/plan_readiness.py). Candidate fix: latch the first `Files:` block per task section (a `seen_files_block` flag). Source: r3 review F3, deferred 2026-09-09.
- **r3 overflow (task-heading variant scan)**: only `^### Task` headings are scanned for `Files:` blocks; `#### Task` or `### Step` variants silently skip their Files lists (fail-open on template deviation). Location: `_review_scope_task_files` heading regex. Candidate fix: broaden the heading pattern (`^#{3,4} (Task|Step)`). Source: r3 overflow manifest (implementation#task-heading-variant-scan), deferred 2026-09-09.
- **r3 overflow (Windows-separator coverage drift)**: `_scope_token_covers` and the boundary regex treat `\` and `/` inconsistently across surfaces, so a `\`-separated path can false-reject coverage (same notation-drift family as r3 F1, which fixed only the trailing-slash polarity). Location: `_scope_token_covers` and the path-boundary regex in check (c). Candidate fix: normalize separators to `/` at token-extraction time so all downstream comparisons see one form. Source: r3 overflow manifest (implementation#windows-separator-coverage-drift), deferred 2026-09-09.

## Locations

- `scripts/plan_readiness.py`, `_review_scope_path_token` (token extraction) and `_review_scope_task_files` (opener match `line.startswith("Files:")`; heading regex; per-task collection state), plus `_scope_token_covers` and the check-(c) boundary regex for the separator-drift shape.

## Possible fixes

- F10: require the backticked span to be the leading content of the item (or to look path-like: contains `/` or a known suffix) before it wins; else fall through to the delimited-token rule.
- F11: case-insensitive `Files:` opener match; consider quoted or backticked handling for space-bearing paths rather than accepting multi-token unbackticked payloads (which reintroduces annotation noise).

Each fix needs a dedicated fail-closed selftest arm in the `selftest#review_scope/` family naming the evasion shape.

## Severity and source

Low (off-convention fail-open tail; the gate is fail-closed for every conventioned shape and pinned by the selftest#review_scope/ family). Source: r2 review overflow manifest findings F10/F11; r3 review findings F2/F3 plus the r3 overflow manifest (task-heading variants, Windows-separator drift); all deferred by standing pre-authorization (heuristic-limit tail is backlog material per the fold-round instructions, 2026-09-09).

## r4 additions (2026-09-09, review r4 of the tooling-polish plan)

- F2: bare non-path Files items (`- none`, `- n/a`) tokenize to phantom paths and false-reject check (c); candidate fix: skip tokens with no path shape (no `/`, no known suffix, or a small stop-set) in `_review_scope_task_files`, plus an arm.
- Record note (r4 F3, third-generation drift, ADR-0002 regenerating class): the archived tooling-polish plan's Evaluation Criteria says "17 at record-fix time" while its pins/shipped arms count 19 (r3 added two arms without bumping the number). If the record is ever revised, drop the number and keep only "the pins are the count of record"; do not maintain a second count.
