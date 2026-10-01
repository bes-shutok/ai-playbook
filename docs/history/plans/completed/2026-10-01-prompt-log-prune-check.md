# Plan: Prompt-log origin checker and the stale-entry prune

Backlog origin (scope of record): `docs/history/backlog/2026-09-30-plan-prompts-prune-at-landing.md`
Driving force: efficiency
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-prompt-log-prune-check-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The registry's prune clause gains a mechanical home and the current drift is pruned, so the covered-origin wedge the origin witnessed becomes a suite failure instead of an operator question.

- `scripts/check_prompt_log_origins.py` reads `docs/history/backlog/PLAN-PROMPTS.md` (sections after the entry-template fence), collects each entry's `Origins:` lines, and classifies every origin: served when the origin's header Status reads `done` or `covered`, or when the origin file is absent because it sits in a backlog archive state directory (`completed/`, `rejected/`, `deferred/` - resolved by basename and reported with the resolved path); unserved otherwise (including a present file with no or novel status, and an absent file that resolves nowhere). An entry is STALE only when EVERY origin is served; its report prints one line per origin (`SERVED: <slug> -> <origin basename> [<status or resolved path>]` / `LIVE: <slug> -> <origin basename>`), exits 1 for a stale entry, exits 0 otherwise (a mixed entry is dispatchable and stays), and `--selftest` exercises both verdicts in a fixture. Frozen entries are checked like any other (a frozen entry whose origins are all served is exactly the wedge the origin witnessed; the freeze rule itself already orders its prune).
- The log state is verified at execution and any drift the checker flags is pruned: main's 2026-10-01 re-prune already cleared the witnessed drift, so the expected state is checker-green with the prune leg conditional (checker-keyed, rebased onto current bytes, mixed entries never pruned); the checker-green landing validation holds either way.
- `scripts/check_maintenance_pins.sh` gains one pin that runs the checker, so the next drift is caught by a suite instead of by an operator question. Deliberately NOT claimed: consult-time prevention. Nothing in the corpus runs the pins sweep on a dispatch cadence, so the checker converts the wedge into a suite failure (the origin's own ask 2), not a consult-time block; wiring the checker into the dispatch slice is a named follow-up outside this plan.

Gate delta: one new standalone checker script plus its suite and registry entry, one pin line, and the removal of stale registry entries (content deletions in a tracking log the prune rule already orders); no existing gate, field, or refusal surface changes and no skill wording changes.

## Terms

- Served origin: a `done`/`covered` status, or an origin file resolved in a backlog archive state directory (moved to `completed/`, `rejected/`, or `deferred/`; the moved-done case is the measured majority).
- Stale entry: every origin served; the only prune-compatible shape, since an entry with any live origin still carries unlanded work.
- Entry template fence: the fenced `Entry template` block in the log header; its placeholder lines are never parsed as an entry.

## Assumptions

- The log's own write rules govern the prune: targeted section edits, re-read before every write, drift retry once then append fallback, commit in the same turn; this plan performs no skill-wording changes because the prune and freeze rules already order everything the checker reports.
- The status parse mirrors the backlog corpus convention (a `Status:` line, bullet or bare, at any header depth) and reads only the FIRST such line per origin file; a missing or unparseable status is `?` and is not a finding (only `done` and `covered` prefixes and absent files are findings), keeping the checker fail-open for novel statuses and fail-closed only for the witnessed drift classes.
- The machinery inventory is registry-backed (`scripts/machinery_registry.json`, dict with `entries`), so the checker registers there; the inventory's pre-existing failures on main are neither caused nor repaired by this plan, and the validation line asserts only that no inventory failure names the new script.
- The checker's done/covered proxy differs from the log's own prune key (the prune rule fires when the plan file lands): a frozen entry whose origins get covered mid-authoring would be checker-stale before its plan lands. No live claim sits on an all-served entry at authoring time; the executor records the divergence in the task log, and a landing that the new pin aborts on fresh drift is the check's intended forcing function (the witnessed drift persisted for hours precisely because nothing forced a read), not a defect to tolerate away.
- The pins script gains exactly one `pin` invocation (its existing helper shape) executing the checker, inserted BEFORE the failure gate `[ "$fail" -eq 1 ] && exit 1` that precedes the script's final `exit 0` (the script has no `set -e`; `pin` only sets `fail=1`, so a pin added after that gate prints PIN FAIL yet the sweep exits 0 - the wedge would survive every landing), with the repo-anchored command `python3 "$repo/scripts/check_prompt_log_origins.py"` (the pins script promises run-from-anywhere and never cds); the checker resolves its default log path against its own repo root, not the caller's cwd. A validation line asserts the invocation appears before the failure-gate line.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: a checker turns the registry's all-served-entry drift into a failing suite, the currently stale entries are pruned, and a maintenance pin keeps it that way; force: efficiency.

Today a stale entry sits live in the registry after its plan lands, executes, and archives: the p98 entry carried nine done origins for hours past its plan's full lifecycle. After this plan the checker exits 1 on any all-served entry, the pin runs it in every pins sweep, and the landed log carries none of the witnessed drift.

## Evaluation Criteria

**Quality dimensions:**
- Detection fidelity: both witnessed classes (covered origins, vanished origin files) are findings; novel statuses fail open; the template fence is never parsed.
- Drift repaired, not just detected: the landed log is checker-green.
- Surface fidelity: the suite drives the real script via `subprocess` against fixture logs, not imported helpers.

**Done when:**
- Every Validation Commands line exits 0, the new suite passes under the repo test venv, and the pins script passes with the new pin.

**Ship when:**
- The next dispatch consult reads a checker-green log (operator-observed; external condition, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_prompt_log_origins.py`
- `scripts/machinery_registry.json` (one registration entry)
- `scripts/check_maintenance_pins.sh` (one pin line)
- `docs/history/backlog/PLAN-PROMPTS.md` (stale-entry removals only)

**Tests:**
- `scripts/test_check_prompt_log_origins.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the maintenance skill's Rolling prompt log duties wording; reason: the rules already order everything; this plan lands the enforcement, not new prose.
- the done sweep's pre-docs gate wiring; reason: the origin offered it as one alternative home; the standalone checker plus pin is the lighter mechanical home and the gate surface is under active peer churn.
- repairing the machinery inventory's pre-existing failures; reason: pre-existing on main, unrelated to this registration.

## Validation Commands

```bash
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_check_prompt_log_origins.py -q || { echo FAIL: checker suite; exit 1; }
python3 scripts/check_prompt_log_origins.py || { echo FAIL: log is checker-stale; exit 1; }
python3 scripts/check_prompt_log_origins.py --selftest || { echo FAIL: checker selftest; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo FAIL: pins baseline; exit 1; }
python3 -c "import json; r=json.load(open('scripts/machinery_registry.json')); assert any('check_prompt_log_origins' in str(e.get('paths',[])) for e in r.get('entries',[])), 'unregistered'" || { echo FAIL: registry entry; exit 1; }
if python3 scripts/machinery_inventory.py --check 2>&1 | grep -q "check_prompt_log_origins"; then echo FAIL: inventory names the checker; exit 1; fi
bash scripts/check-no-em-dash.sh file scripts/check_prompt_log_origins.py scripts/test_check_prompt_log_origins.py scripts/check_maintenance_pins.sh docs/history/plans/2026-10-01-prompt-log-prune-check.md || { echo FAIL: em-dash; exit 1; }
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh || { echo FAIL: hygiene; exit 1; }
GATE_LINE=$(grep -n "\[ \"\$fail\" -eq 1 \]" scripts/check_maintenance_pins.sh | tail -1 | cut -d: -f1); CHECKER_LINE=$(grep -n "check_prompt_log_origins" scripts/check_maintenance_pins.sh | tail -1 | cut -d: -f1); [ -n "$GATE_LINE" ] && [ -n "$CHECKER_LINE" ] && [ "$CHECKER_LINE" -lt "$GATE_LINE" ] || { echo FAIL: pin sits at or after the failure gate; exit 1; }
```

### Task 1: the origin checker

Files:
- *(new)* `scripts/check_prompt_log_origins.py`
- `scripts/machinery_registry.json`

Evidence:
- `python3 scripts/check_prompt_log_origins.py --selftest` (fails until the script exists); covers the task boundary

- [ ] Run → expect RED: `ls scripts/check_prompt_log_origins.py` fails (the script does not exist) [class: REPOSITORY_TEST]
- [ ] Implement `scripts/check_prompt_log_origins.py` per the Outcome bullet: argparse with the log path defaulting to `docs/history/backlog/PLAN-PROMPTS.md` (resolved against the script's own repo root) and `--selftest`; section parsing that skips the entry-template fence; per-origin classification into served (`done`/`covered` status, or the file resolved by basename in a backlog archive state directory, reported with the resolved path) and live (anything else, including a present file with no or novel status); the entry verdict is STALE only when every origin is served, with one report line per origin and exit 1 only for a stale entry; register the script in `scripts/machinery_registry.json` (entry shape per the sibling script entries, witness naming this plan) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `python3 scripts/check_prompt_log_origins.py --selftest` exits 0 [class: REPOSITORY_TEST]
- [ ] Commit: `scripts: prompt-log origin checker for stale registry entries` [class: IMPLEMENTATION_REQUIRED]

### Task 2: suite pins through the real script

Files:
- *(new)* `scripts/test_check_prompt_log_origins.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_check_prompt_log_origins.py -q`; covers the full family

- [ ] Add `scripts/test_check_prompt_log_origins.py` driving the script via `subprocess` against fixture logs, each test named with the `prompt_log_origins` substring so the family selector collects it: `test_prompt_log_origins_flags_done_origin`, `test_prompt_log_origins_flags_covered_origin`, `test_prompt_log_origins_flags_missing_origin`, `test_prompt_log_origins_skips_template_block`, `test_prompt_log_origins_clean_log_exits_zero`, `test_prompt_log_origins_frozen_entry_still_checked`, and `test_prompt_log_origins_mixed_entry_stays` [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [ ] Commit: `tests: prompt-log origin checker fixture suite` [class: REPOSITORY_TEST]

### Task 3: verify the log state and pin the checker

Files:
- `docs/history/backlog/PLAN-PROMPTS.md` (only if the conditional prune below fires)
- `scripts/check_maintenance_pins.sh`

Evidence:
- `python3 scripts/check_prompt_log_origins.py`; covers the log-state verification

- [ ] Run → expect GREEN on main's current bytes: `python3 scripts/check_prompt_log_origins.py` exits 0 (the witnessed drift was already cleared by main's 2026-10-01 re-prune commit a0a335e6; the authoring-time measurement under the all-served rule had flagged six entries; re-derive at execution) [class: REPOSITORY_TEST]
- [ ] Conditional prune: ONLY if the checker flags any entry at execution time, remove those STALE entries (all origins served) by targeted section edits per the log's write rules, rebased onto the then-current main bytes (never prune from stale log bytes; a mixed entry with any live origin is never pruned by this task); when the checker is green, record that fact in the task log and skip this item [class: IMPLEMENTATION_REQUIRED]
- [ ] Add one `pin` invocation to `scripts/check_maintenance_pins.sh`, inserted immediately BEFORE the failure-gate line matching `[ "$fail" -eq 1 ] && exit 1`, running `python3 "$repo/scripts/check_prompt_log_origins.py"` so the pins sweep carries the check [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]
- [ ] Commit: `pins: run the prompt-log origin checker in the maintenance pins sweep` (plus the prune commit `log: prune all-served entries the origin checker flags` first, only when the conditional prune fired) [class: IMPLEMENTATION_REQUIRED]
