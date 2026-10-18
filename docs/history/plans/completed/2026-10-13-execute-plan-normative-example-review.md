# Plan: execute-plan normative-example review coverage

Backlog origins (scope of record):
- docs/history/backlog/2026-10-08-execute-plan-normative-example-review-coverage.md
- docs/history/backlog/2026-10-08-review-examples-carrier-context-replay.md

Driving force: code-quality

Plan review record: the staging series {reviews_dir}/2026-10-13-plan-review-execute-plan-normative-example-review-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

Execution budget: 1.5h total, largest task 0.5h

## Terms

- `normative example`: a changed documentation example that illustrates behavior a reader could reproduce (a command, a request sample, a mode-rule snippet).
- `runnable example`: a normative example presented with an invocation a reader is expected to execute.
- `Tier L`: the per-task intermediate review tier selecting one worker, defined in review-panel-selection.md's Per-task intermediate review selection table.
- `Boundary exception`: the focused-panel selection rule escalating a changed normative documentation example to `contract-docs` plus `correctness-completeness` without worker escalation.
- `invocation context`: the complete displayed command a reader would run, including the outer shell or wrapper around an embedded snippet.

## Why

The per-task Tier L row and the focused-panel Boundary rule give conflicting instructions for a docs-only change that contains a normative example, and their precedence is implicit, so a changed example can reach review without the correctness lens. Separately, the documentation replay duty accepts inner-language syntax checking and structured inventories where a runnable example needs replay through its displayed wrapper: the witnessed 2026-10-08 review found a snippet whose inner syntax passed while the shell argument would terminate before the embedded program started.

## Gist & Examples

TLDR: the per-task selection rules carry the normative-example lens exception at every tier and the documentation replay duty requires wrapper-level replay for runnable examples, so changed executable examples always reach both lenses and get replay evidence (code-quality).

Before (today): a docs-only task with a changed command example derives Tier L and launches one `contract-docs` worker, while the catalog's own Boundary rule says the same diff needs `contract-docs` plus `correctness-completeness`; and the replay duty treats a structured inventory or inner-syntax check as sufficient, which is exactly the shape that missed the 2026-10-08 shell-quoting break (witnessed finding: the shell argument would terminate at the path-label print line while the embedded syntax was valid).

After (this plan): the per-task selection rules carry the exception at every tier with prose-only docs keeping their own worker set, and the documentation replay duty requires replaying a runnable example through its complete displayed invocation with representative fixtures, recording the exact command and result, with a stated-limitation fallback when replay is unsafe or not meaningful.

Edge cases: a changed normative example in a docs-plus-scripts diff with no code-mutation signal takes the same exception; prose-only docs (no changed normative example) keep their own tier's worker set; an example that is not runnable keeps today's validate-or-inventory obligation; the focused-panel Boundary rule itself is unchanged.

## Outcome

Intermediate review selection and documentation replay agree on changed normative examples, and runnable examples carry wrapper-level replay evidence.

- A changed normative documentation example selects `contract-docs` plus `correctness-completeness` at every tier, with prose-only docs keeping their own tier's worker set.
- A runnable example is validated by replaying its complete displayed invocation with representative fixtures, and the review evidence records the exact command and result.
- When replay is unsafe or not meaningful, the limitation is stated and the wrapper gets a focused syntax or structure check.

Gate delta: adds no gate, refusal class, hard gate, fence, protocol layer, or schema field. Two prose-rule duty growths in shared review-agent catalogs, each priced by its origin's cited completed failure: the per-task selection rules gain the normative-example exception (origin one's witnessed miss: a malformed shell-wrapped example passed the initial skill review), and the documentation replay duty gains the runnable-example wrapper-replay requirement with its fallback (origin two's witnessed wrapper-level quoting break). Nothing is removed; the focused-panel Boundary rule and the validate-or-inventory boundary are preserved.

## Assumptions

- assume the selection fix lands only in review-panel-selection.md: Step 1.2b defers worker selection to the catalog ("resolve the complexity tier per review-panel-selection.md Per-task intermediate review selection") and the completed intermediate-review plan's single-source invariant keeps tier policy out of the execute-plan skill, so no execute-plan SKILL.md edit is made; basis: reads of both surfaces at authoring, 2026-10-13.
- assume no review-stage causality claim: the recoverable run record (docs/history/reviews/2026-10-08-code-review-passive-review-reply-state-visibility-r1.md, finding F1, pattern quality#invalid-command-quoting, triage fixed) shows the shell-quoting miss caught and verified by a code-review replay executing the exact fenced command with representative data; the record does not identify which earlier stage (if any) handled the example, so this plan claims no Step 1.2b causality and fixes only the rule conflict and the replay duty; basis: the record read 2026-10-13 in the untracked reviews corpus.
- assume the driving force: both origins declare reliability, outside the closed taxonomy; declared here as code-quality; basis: the closed taxonomy in the plans skill.
- assume the fence-class arms are priced: each origin cites its completed failure (the missed malformed quoting corrected in follow-up; the wrapper-level break invisible to inner-syntax checks), satisfying the plans skill's fence rule for duty growth; basis: the origins' Evidence sections.
- assume catalog rules are witnessed mechanically by text-contract pins in the doors-registry style (lens pins over pattern sections) rather than by an example-execution framework; basis: scripts/test_review_agent_doors.py structure, read at authoring.
- assume the prescribed catalog wording passes the portability checker: no framework-product, language-name, build-tool, test-suffix, repo-path, or ticket-prefix tokens appear in the prescribed inserts; basis: the denylist read at authoring.

Decision points requiring a grill: none remain.

## Standing constraints

- Plan scripts and validators run under python3; all commands stay repo-relative with no machine-specific absolute paths, and committed text carries no em dashes.
- The pins suite is load-bearing and currently exits 1 with the 21 recorded baseline failures (docs/history/backlog/2026-10-12-pins-suite-main-baseline-21-failures.md); no task may add a new failing pin description; the Validation block's subset guard is the regression fence, not a repair duty.
- Any change under agents/skills/review-agents/ must keep scripts/check_review_agent_portability.py and scripts/test_review_agent_doors.py green (exit 0 each).
- Git history is immutable: no task rewrites or amends commits; plan bytes after review move only through the classifier-gated fold path.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the per-task selection rules and the Boundary rule agree on changed normative examples, with precedence stated and the prose-only path preserved; the replay duty covers the runnable case end to end, wrapper included.
- auditability: the replay duty requires the exact command and its result in the review evidence, and the fallback requires the stated limitation.
- compatibility: the existing single-worker arm, the Boundary rule, and the validate-or-inventory obligation are unchanged; the doors registry and the portability checker stay green.

**Done when:**
- scripts/test_review_agent_normative_example_selection.py passes with the five focused witnesses (every-tier exception, prose-only retention, frozen Boundary and table integrity, wrapper-replay duty, evidence-and-fallback duty).
- review-panel-selection.md's per-task selection section carries the every-tier exception sentence and retention tail; documentation.md's replay section carries the runnable-example duty and fallback.
- the doors registry, the portability checker, and the pins subset guard pass with no new failing descriptions.

**Ship when:**
- consumer projects running the shared skills checkout pick up the aligned selection and replay rules at their next vendored sync; no external release action is owned by this plan.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-agents/review-panel-selection.md` (the Per-task intermediate review selection section; the rest of the file is frozen)
- `agents/skills/review-agents/documentation.md` (the Normative example replay section; the rest of the file is frozen)

**Tests:**
- `scripts/test_review_agent_normative_example_selection.py` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`; reason: the single-source invariant keeps tier policy in the catalog, and Step 1.2b already defers to it.
- `scripts/test_review_agent_doors.py`; reason: the doors registry is a compatibility surface this plan keeps green, not a surface to extend.
- Other review-agent lens files; reason: the conflicts are scoped to the two named sections.

## Validation Commands

The pins suite baseline below was recorded at authoring time (2026-10-13, worktree base 9a34ae55b): the suite exits 1 printing exactly these 21 failing descriptions; the guard fails on any description not in the baseline and treats rc 2 or higher as a tool error.

RED-today record (rule 19, executed pre-implementation against the base tree on 2026-10-13): the block was run as extracted bytes (`bash -n` clean) and aborted fail-closed at its FIRST failing gate, gate 1, block rc 1 (the witness suite does not exist yet). The remaining gates were probed individually and observed: gate 2 green (doors registry), gate 3 green (portability), gate 4 green (pins rc 1 with exactly 21 failing descriptions, the set byte-identical to the captured baseline), gate 5 green (hygiene), gate 6 vacuous on the empty base range with the firing proof executed in a scratch repository (an added em-dash line, rc 1 naming the file and line).

Export `PLAN_BASE=<merge-base of the execution branch with main>` before running the block; the em-dash gate is never run argless (argless prints usage and exits 0 scanning nothing).

```bash
set -u
repo="$(git rev-parse --show-toplevel)" || exit 1
cd "$repo" || exit 1
fail() { echo "VALIDATION FAIL: $*" >&2; exit 1; }

# 1. Focused witness suite (owner: Tasks 1-2)
python3 scripts/test_review_agent_normative_example_selection.py >/dev/null 2>&1 || fail "focused normative-example witness suite"

# 2. Review-agent doors registry (compatibility surface)
python3 scripts/test_review_agent_doors.py >/dev/null 2>&1 || fail "review-agent doors registry"

# 3. Review-agent portability (shared-catalog token gate)
python3 scripts/check_review_agent_portability.py >/dev/null 2>&1 || fail "review-agent portability"

# 4. Pins regression subset guard (baseline recorded 2026-10-13 at 9a34ae55b)
PINS_OUT="$(bash scripts/check_maintenance_pins.sh 2>&1)"; PINS_RC=$?
[ "$PINS_RC" -le 1 ] || fail "pins suite tool error (rc $PINS_RC)"
CURRENT_PINS="$(printf '%s\n' "$PINS_OUT" | grep '^PIN FAIL' | sed 's/^PIN FAIL: //' | sort -u)"
BASELINE_PINS="$(cat <<'PIN_BASELINE'
resume-fit --fire-at check at resume-scheduling boundaries
resume-pricing defers to the reported defer_to
preservation: canonical lineage-cap branch span count 0 != 1
preservation: Resume carrier fallback ordering heading span count 0 != 1
preservation: OffPeakCreate pause rung span count 0 != 1
preservation: launchd wired mark span count 0 != 1
preservation: OffPeakCreate prompt contract span count 0 != 1
preservation: canonical carrier-aware record span count 0 != 1
rate-limited end resolves its open claim
claim-less end derives from stop lines
post-backoff success writes a recovery marker
state table derives the claim-less case
contract mirrors the claim boundary
contract derives the claim-less case from stop lines
resume backoff carries a floor
serialized cap doubles the intermediate-panel bound
serialized cap doubles the Step 3.1 bound
serialized cap doubles the omnibus bound
stop line token format pinned
dispatch_failed record literal
dispatch_failed tracking-list entry head
PIN_BASELINE
)"
NEW_FAILS="$(comm -23 <(printf '%s\n' "$CURRENT_PINS" | sort -u) <(printf '%s\n' "$BASELINE_PINS" | sort -u))"
[ -z "$NEW_FAILS" ] || { echo "NEW PIN FAILURES:" >&2; printf '%s\n' "$NEW_FAILS" >&2; fail "pins regression: new failing descriptions"; }
echo "pins subset guard: no new failing descriptions"

# 5. Public hygiene scan (anchored to the repo root)
( cd "$repo" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" >/dev/null 2>&1 ) || fail "public hygiene scan"

# 6. Em-dash residue over the landing range (never argless; PLAN_BASE exported by the caller)
bash scripts/check-no-em-dash.sh added-lines --base "$PLAN_BASE" >/dev/null 2>&1 || fail "em-dash residue in added lines"

echo "VALIDATION: all gates green"
```

### Task 1: the selection rules carry the every-tier normative-example exception

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/review-agents/review-panel-selection.md`
- `scripts/test_review_agent_normative_example_selection.py` *(new)*

Primary class anchors:
- `Per-task intermediate review selection` in `agents/skills/review-agents/review-panel-selection.md`

- [x] add scripts/test_review_agent_normative_example_selection.py (unittest, doors-registry lens-pin style) with three failing witnesses: the Per-task intermediate review selection section carries the every-tier normative-example exception sentence with both lens names, the prose-only retention tail, and the tier table's original rows survive with the Boundary rule paragraph untouched (frozen-span pin including its pipe structure) [class: REPOSITORY_TEST]
- [x] Run → expect RED: two witness tests fail against today's section (the exception and retention spans are absent) while the frozen-span witness passes at base and must stay green, and the doors registry and the portability checker stay green [class: REPOSITORY_TEST]
- [x] insert below the tier table in review-panel-selection.md, immediately before the sentence beginning `The plan's Review tier hint`, the exception sentence opening: `Exception at every tier: a diff carrying a changed normative documentation example and no code-mutation signal selects `contract-docs` plus `correctness-completeness` coverage in addition to the tier's own workers,` [class: IMPLEMENTATION_REQUIRED]
- [x] continue the same sentence with the tail text: ` never triggering the risk-signal floor's escalation; prose-only documentation without a changed normative example keeps the tier's own worker set.` so the sentence ends with a period before the next paragraph [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the witness suite passes with its three tests, and the doors registry and portability checker stay green [class: REPOSITORY_TEST]
- [x] Commit: `feat: per-task selection carries the normative-example exception at every tier` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the replay duty covers runnable examples at the wrapper

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/review-agents/documentation.md`

Primary class anchors:
- `Normative example replay` in `agents/skills/review-agents/documentation.md`

- [x] extend the witness suite with two failing tests over the Normative example replay section (the section containing the `documentation#missing-example-replay` pattern declaration): the runnable-example replay duty with its wrapper rationale, and the evidence-and-fallback duty including the untrusted-content trigger [class: REPOSITORY_TEST]
- [x] Run → expect RED: the two new tests fail (the runnable and fallback spans are absent), while Task 1's tests stay green [class: REPOSITORY_TEST]
- [x] insert into the section, after the existing Boundary bullet and before the `Use pattern` paragraph, the bullet opening: `- A changed example is **runnable** when it is presented with an invocation a reader is expected to execute (a fenced command, a shell-wrapped snippet, a documented CLI call). A runnable example is validated by replaying the complete displayed invocation context, outer shell or wrapper included, with representative fixtures,` [class: IMPLEMENTATION_REQUIRED]
- [x] continue the same bullet with the tail text: `and the review evidence records the exact command and its result; checking only the inner language's syntax never satisfies the duty, because quoting, substitution, and heredoc boundaries fail at the wrapper before the inner program starts.` [class: IMPLEMENTATION_REQUIRED]
- [x] insert after it the fallback bullet: `- When replaying a runnable example is unsafe (including content from untrusted or unreviewed sources) or not meaningful in the review context, state that limitation in the review evidence and verify the wrapper's syntax or structure with a focused check; the validate-or-inventory obligation above stays for examples that are not runnable.` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the full witness suite passes with five tests, and the doors registry and portability checker stay green [class: REPOSITORY_TEST]
- [x] Commit: `docs: replay runnable examples through their displayed invocation` [class: IMPLEMENTATION_REQUIRED]

### Task 3: validation pass

Context surface: the plan's `## Validation Commands` and `## Standing constraints`; referenced, never restated.

- [x] run the whole Validation Commands block with `PLAN_BASE` exported; expect every gate green with the pins subset guard reporting no new failing descriptions against the recorded baseline [class: REPOSITORY_TEST]

Evidence: the Validation block's final `VALIDATION: all gates green` line, the pins subset guard line, and the witness suite's pass count recorded in the run log.
