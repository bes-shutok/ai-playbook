# Plan: no silent gate-satisfying rewrites of human-authored prose

Backlog origin: docs/history/backlog/2026-09-19-gate-driven-silent-prose-edits.md
Driving force: external (witnessed incident 2026-07-21 and the user correction captured in the backlog origin). Justification for a non-principle force: the incident produced real user-visible rework (58 silently rewritten lines restored by hand, plus a recurring correction family), so this closes an observed defect class rather than adding machinery; park-triage would not take it because the fix is a one-paragraph contract line, not process-cosmetic machinery growth.

## Terms

- **Gate**: an automated checker that must exit clean before a commit or handoff. In this repository: `check-no-em-dash.sh`, `scan-public-hygiene.sh`, `check-instruction-size.sh`, `plan_readiness.py`.
- **Human-authored prose**: prose a human wrote or approved as their own wording (plan bodies, documents, reports, messages). Agent-authored scaffolding (new files, comments, and logs a worker creates in the same run) is not human-authored. Witness for the boundary: the 58 lines of the user's plan prose rewritten on 2026-07-21.
- **The pin**: the worker-contract rule this plan inserts. It obliges the worker to satisfy a gate with the narrowly-scoped edit the gate actually requires, made only inside the lines the run's own change touches (the hunks this run edited, not merely the same file) and reported in the return or commit summary, or to stop and surface the conflict; wholesale rewording of human-authored prose is out of scope for any worker, always, and the pin never applies to text the worker authored in the same run. (The origin's word insertion became edit when the pin gained the touched-lines scope: a deletion or substitution can be the minimal edit.)
- **Returned-for-ask shape**: a stop-and-report that hands a blocked decision back to the user with the gate named, the failing lines identified, and the options listed, instead of improvising a resolution. Vocabulary borrowed from receiving-review triage; defined here so each contract is self-contained.
- **Implement worker**: the execute-plan sub-agent implementing one task (the Implement Task template) or one batch member (the Implement Task Batch template), both in `agents/skills/execute-plan/subagent-prompts.md`.

## Assumptions

- assume the pin lands in exactly the three contract surfaces named in the tasks (both implement worker templates and the done contract); basis: the backlog item names "the done and implement worker contracts", and those contracts' canonical files were verified on disk.
- assume prose contract text only, no new validator code; basis: the backlog Suggested fix describes a behavioral contract, and the mechanical insertion-scoped checker half is owned by docs/history/backlog/2026-09-16-em-dash-insertion-scope-check.md; the behavioral-versus-mechanical split is declared by the origin item itself.
- assume one canonical pin wording shared by all three surfaces; basis: identical wording keeps drift detectable by the validation span counts, and a single source sentence is simpler to review.
- assume the two live-behavior acceptance criteria from the backlog origin (a deliberate probe halts for ask; zero new rewrite corrections in the next corrections-mining pass) are observational, not repository implementation; basis: the plans checklist inclusion gate classifies live agent-behavior probes and post-hoc audit passes as not executable in-repo, so they land in Ship when prose.

- assume per-template pin duplication in the implement contracts is the intended transmission model: implement workers receive only the fenced template content, and the file's shared worker-and-result contract section is parent-facing, so the pin must ride inside each template fence; basis: the templates are self-contained copy-paste prompts and the launch steps reference only the named templates.
- assume the done-side pin appears twice (Step 2.76 paragraph and Rules bullet) deliberately: the in-place paragraph constrains the adjacent fix-every-reported-line instruction at the incident step, the Rules bullet is the whole-file contract surface, and drift between the copies is bounded by the prescribed verbatim wording and the validation count gates; the Step-2.76 paragraph additionally carries a Step-2.76-local annex sentence (per-location rendering, not a fourth pin clause), and the Rules bullet prescribes the shared body without it.
- assume three pin clauses extend beyond the origin's suggested fix deliberately: the report duty (the incident's sin was silence), the restore-outranks-green-gate clause, and the agent-authored carve-out with its never-excuses tail (the carve-out operationalizes the Human-authored prose Terms boundary rather than extending it); basis: the 2026-07-21 witness and the user's restore-the-pristine-text response.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: adds one no-silent-rewrite pin to the two execute-plan implement worker contracts and the done contract, so a failing gate is satisfied by the minimal edit it requires or by stopping for the user, never by rewording the user's prose; driving force: external (2026-07-21 witnessed rewrite incident, user correction in the backlog origin).

**Before (today):** an implement or done worker hits a failing prose gate over user-authored text, for example the em-dash scan over a user's plan file. No contract line forbids wholesale rewording, so the worker "fixes" the gate by rewriting dozens of the user's lines (the 2026-07-21 witness: 58 lines turned from long dashes to semicolons, silently). The user must notice, restore the pristine text, and correct the agent; the backlog origin counts roughly eight correction prompts in this family.

**After (this plan):** the same worker hits the same gate, reads the pin in its own contract, and either applies the minimal edit the gate requires inside the lines the run itself touches (one long dash in a touched line, one missing character) and reports the edit, or stops and surfaces the conflict for the user to adjudicate, naming the gate, the failing lines, and the options. Whole-file rewording of user-authored text is contractually out of scope, so the user's wording survives every gate.

**Edge cases:**
- The gate fails only on agent-authored text (a comment or log line the worker itself just wrote): the worker edits or rewrites its own text freely; the pin never applies and never excuses stopping.
- The gate fails inside the lines this run's change touches: the worker makes the minimal edit the gate requires (for the em-dash case, one long dash in a touched line) and reports it in the return or commit summary.
- The failures reach untouched user prose (the 2026-07-21 shape: a 58-line sweep over a file the task never edited): the worker stops and surfaces the conflict; sweeping untouched lines is not narrowly scoped even when each single edit is tiny.
- No minimal edit can satisfy the gate (the gate and the user's wording are irreconcilable): the worker stops and surfaces the conflict (returned-for-ask shape); restoring the user's original text outranks a green gate.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every prescribed location carries the pin exactly once; the validation count gates prove line-granular presence and uniqueness per location.
- consistency: the pin sentence body is identical across the three surfaces, with per-location rendering exactly as the tasks prescribe; shared literal spans are grep-verified per location.
- fail-closed validation: every gate in the Validation Commands block aborts non-zero on miss or forbidden state; no gate relies on bare exit status propagation.

**Done when:**
- the pin appears exactly once in each of the four windows: the Implement Task Rules, the Implement Task Batch Rules, done Step 2.76, and the done Rules section;
- the full Validation Commands block exits 0 from the repository root;
- both task commits are attributable through the base sha recorded before the first task commit.

**Ship when:**
- A deliberate live probe (a gate satisfiable only by rewording human prose) halts for ask instead of editing; [class: OPERATIONS_FOLLOW_UP] evidence owner: the next real occurrence or a user-run probe session; closure condition: the surfaced conflict names the gate and the options and no wholesale rewrite lands.
- Zero new "why did you rewrite my text" corrections in the next corrections-mining pass; [class: OPERATIONS_FOLLOW_UP] evidence owner: the user's cross-session friction audit; closure condition: the next mining pass over typed prompts reports no new corrections in this family.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/done/SKILL.md`

**Tests:**
- none new; this is a prose-contract plan and the verification surface is this plan's Validation Commands block.

**Execution scratch (gitignored):**
- `docs/tmp/no-silent-rewrite-pin-base-sha.txt` *(new)*; written by Task 1 and read by the attribution gates

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production surfaces are the two skill contracts above; no other docs change.

**Out of scope; reject unless plan-related:**
- `scripts/check-no-em-dash.sh`; reason: the mechanical insertion-scoped checker mode is owned by docs/history/backlog/2026-09-16-em-dash-insertion-scope-check.md.
- `docs/history/backlog/2026-09-19-gate-driven-silent-prose-edits.md`; reason: the origin item stays in place under the backlog directory while this plan is open; the completion step moves it.
- `agents/skills/receiving-review/SKILL.md`; reason: the returned-for-ask vocabulary is consumed as-is, not edited.

## Validation Commands

RED-today proof, executed at authoring on 2026-09-19 against the current tree: the block's first failing gate is the Implement Task window pin-span count (exit 1, count 0 vs required 1); all four windows extract non-empty (54, 44, 14, and 17 lines), so no gate passes vacuously on an empty region; the em-dash and pins gates are GREEN-today regression gates (both exit 0 at authoring time). The gates flip GREEN exactly when Tasks 1 and 2 land. The attribution gates bind the recorded base to the task 1 commit through subject-scoped uniqueness, strict ancestry, and a five-commit distance bound that tolerates a small number of concurrent peer commits on a shared checkout; the primary staleness defense is Task 1's record-immediately-before-committing instruction, with the distance bound as the backstop.

```bash
#!/usr/bin/env bash
# Run from the repository root. Fails closed: every required check aborts non-zero.
set -u
fail() { echo "VALIDATION FAIL: $*" >&2; exit 1; }

SUB="agents/skills/execute-plan/subagent-prompts.md"
DONEF="agents/skills/done/SKILL.md"
S2='Whole-file rewording of user-authored text is out of scope for any worker'
S3='stop and surface the conflict for the user to adjudicate'
S4='Text you authored this run is yours to fix freely'

test -f "$SUB" || fail "missing $SUB"
test -f "$DONEF" || fail "missing $DONEF"

count_in() { printf '%s\n' "$2" | grep -cF "$1"; }

W1="$(awk '/^## Implement Task$/{f=1;next} /^## Implement Task Batch$/{f=0} f' "$SUB")"
test -n "$W1" || fail "Implement Task window extracted empty"
W2="$(awk '/^## Implement Task Batch$/{f=1;next} /^## Member checkpoint/{f=0} f' "$SUB")"
test -n "$W2" || fail "Implement Task Batch window extracted empty"
W3="$(awk '/^## Step 2\.76: No em dash scan/{f=1;next} /^## Step 2\.8:/{f=0} f' "$DONEF")"
test -n "$W3" || fail "done Step 2.76 window extracted empty"
W4="$(awk '/^## Rules$/{f=1;next} f' "$DONEF")"
test -n "$W4" || fail "done Rules window extracted empty"

for S in "$S2" "$S3" "$S4"; do
  for W in "$W1" "$W2" "$W3" "$W4"; do
    n="$(count_in "$S" "$W")"
    test "$n" -eq 1 || fail "pin span count $n != 1 for span: $S"
  done
done

test "$(printf '%s\n' "$W3" | grep -cF 'overrides the surrounding imperatives')" -eq 1 || fail "Step 2.76 annex sentence count != 1"

test "$(grep -cF "$S2" "$SUB")" -eq 2 || fail "subagent-prompts total pin count != 2"
test "$(grep -cF "$S2" "$DONEF")" -eq 2 || fail "done SKILL total pin count != 2"
test "$(grep -cF "$S3" "$SUB")" -eq 2 || fail "subagent-prompts total stop-surface count != 2"
test "$(grep -cF "$S3" "$DONEF")" -eq 2 || fail "done SKILL total stop-surface count != 2"
test "$(grep -cF "$S4" "$SUB")" -eq 2 || fail "subagent-prompts total carve-out count != 2"
test "$(grep -cF "$S4" "$DONEF")" -eq 2 || fail "done SKILL total carve-out count != 2"

bash scripts/check-no-em-dash.sh file "$SUB" "$DONEF" || fail "em dash present in an edited contract"

PINS_OUT="$(bash scripts/check_maintenance_pins.sh 2>&1)" || fail "maintenance pins suite regressed: $PINS_OUT"

BASE="$(cat docs/tmp/no-silent-rewrite-pin-base-sha.txt)" || fail "base sha file missing"
test -n "$BASE" || fail "base sha empty"
git rev-parse --verify "$BASE^{commit}" >/dev/null 2>&1 || fail "recorded base is not a commit"
T1S="skills: add no-silent-rewrite pin to execute-plan implement templates"
T2S="skills: add no-silent-rewrite pin to done contract"
require_unique_subject() {
  local label="$1" raw="$2" n
  n="$(printf '%s\n' "$raw" | grep -c .)"
  test "$n" -eq 1 || { test "$n" -eq 0 && fail "$label commit subject not found in history"; fail "$label commit subject not unique"; }
}
T1_RAW="$(git log --format='%H %s' HEAD | grep -F -- "$T1S")"
require_unique_subject "task 1" "$T1_RAW"
T1="$(printf '%s\n' "$T1_RAW" | awk '{print $1}')"
T2_RAW="$(git log --format='%H %s' HEAD | grep -F -- "$T2S")"
require_unique_subject "task 2" "$T2_RAW"
T2="$(printf '%s\n' "$T2_RAW" | awk '{print $1}')"
git merge-base --is-ancestor "$BASE" "$T1" || fail "recorded base is not an ancestor of the task 1 commit"
test "$(git rev-list --count "$BASE..$T1")" -ge 1 || fail "recorded base is not strictly before the task 1 commit (record it before committing)"
test "$(git rev-list --count "$BASE..$T1")" -le 5 || fail "recorded base sits more than five commits before the task 1 commit (stale or spoofed base)"
git merge-base --is-ancestor "$T1" "$T2" || fail "task 2 commit does not follow the task 1 commit"
git show --name-only --format= "$T1" | grep -Fx "$SUB" >/dev/null || fail "subagent-prompts.md not in the task 1 commit"
git show --name-only --format= "$T2" | grep -Fx "$DONEF" >/dev/null || fail "done SKILL.md not in the task 2 commit"
git show --name-only --format= "$T1" | grep -Fx "$DONEF" >/dev/null && fail "task 1 commit touches the done contract"
git show --name-only --format= "$T2" | grep -Fx "$SUB" >/dev/null && fail "task 2 commit touches the implement contract"
git show "$T1" -- "$SUB" | grep '^+' | grep -qF -- "$S2" || fail "task 1 commit does not add the pin into subagent-prompts.md"
git show "$T2" -- "$DONEF" | grep '^+' | grep -qF -- "$S2" || fail "task 2 commit does not add the pin into done SKILL.md"

echo "VALIDATION OK"
```

### Task 1: pin in the execute-plan implement worker contracts

Files:
- `agents/skills/execute-plan/subagent-prompts.md`
- `docs/tmp/no-silent-rewrite-pin-base-sha.txt` *(new; gitignored execution scratch)*

- [x] Immediately before the Task 1 commit (after the insertions are in place), create `docs/tmp/no-silent-rewrite-pin-base-sha.txt` containing the current HEAD sha (one line, no trailing text); no authoring-time copy exists, and the attribution gates read this file [class: IMPLEMENTATION_REQUIRED]
- [x] Insert as rule 9 in the Implement Task template's Rules section, exactly: `9. **No silent gate-satisfying rewrites of human-authored prose:** when a gate or validator fails on prose the user authored, do not rewrite the passage wholesale and do not silently substitute its wording, punctuation, or structure. Make only the narrowly-scoped edit the gate actually requires, only inside the lines this run's own change touches (the hunks this run edited, not merely the same file), and report the edit in the return or commit summary; when the failures reach untouched user prose, or no minimal edit exists, stop and surface the conflict for the user to adjudicate (returned-for-ask shape: name the gate, the failing lines, and the options). Whole-file rewording of user-authored text is out of scope for any worker, always. Restoring the user's original text outranks a green gate. Text you authored this run is yours to fix freely; this pin never applies to it and never excuses stopping for routine fixable failures.` [class: IMPLEMENTATION_REQUIRED]
- [x] Insert as rule 8 in the Implement Task Batch template's Rules section, the same sentence body with the list marker `8.` instead of `9.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run the em-dash scanner on the edited file and confirm exit 0 (the insertion introduces no long dashes) [class: REPOSITORY_TEST]
- [x] Commit: `skills: add no-silent-rewrite pin to execute-plan implement templates` [class: IMPLEMENTATION_REQUIRED]

### Task 2: pin in the done contract

Files:
- `agents/skills/done/SKILL.md`

- [x] Insert the pin as a plain paragraph in Step 2.76, between the numbered list (after "Re-run until exit code 0.") and the "Do not stage" line, exactly: `No silent gate-satisfying rewrites of human-authored prose: when a gate or validator fails on prose the user authored, do not rewrite the passage wholesale and do not silently substitute its wording, punctuation, or structure. Make only the narrowly-scoped edit the gate actually requires, only inside the lines this run's own change touches (the hunks this run edited, not merely the same file), and report the edit in the return or commit summary; when the failures reach untouched user prose, or no minimal edit exists, stop and surface the conflict for the user to adjudicate (returned-for-ask shape: name the gate, the failing lines, and the options). Whole-file rewording of user-authored text is out of scope for any worker, always. Restoring the user's original text outranks a green gate. Text you authored this run is yours to fix freely; this pin never applies to it and never excuses stopping for routine fixable failures. When the stop-and-surface clause of this paragraph fires, it overrides the surrounding imperatives: do not re-run the scan for exit code 0, leave the failing prose unstaged, and do not continue to Step 2.8 until the user adjudicates.` [class: IMPLEMENTATION_REQUIRED]
- [x] Add one bullet to the done `## Rules` section carrying the shared pin body prefixed with `- `: the paragraph text of the previous item WITHOUT its Step-2.76-specific annex sentence (the annex names Step 2.8 and the scan imperatives, so it is Step-2.76-local by design) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the em-dash scanner on the edited file and confirm exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `skills: add no-silent-rewrite pin to done contract` [class: IMPLEMENTATION_REQUIRED]

### Task 3: validation green

Files:
- none (verification only)

- [x] Run the full Validation Commands block from the repository root and confirm it prints `VALIDATION OK` with exit 0; every gate that was RED at authoring time is GREEN now [class: REPOSITORY_TEST]
- [x] If a uniqueness gate fails because a prescribed commit subject landed twice (a retried or non-amended task commit), squash or amend the duplicates so each prescribed subject appears exactly once and re-run the block; amend only this plan's own task commits, never a peer's [class: REPOSITORY_TEST]
