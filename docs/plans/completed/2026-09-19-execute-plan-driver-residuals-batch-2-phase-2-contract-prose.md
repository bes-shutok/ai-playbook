# Plan: execute-plan driver residuals batch 2 (contract prose), phase 2 of 2

Covers the five prose origins of the batch-2 family (runtime contract and
skill text, worktree bootstrap). The sibling plan
`docs/plans/2026-09-19-execute-plan-driver-residuals-batch-2-phase-1-state-machine.md`
covers the six driver-code origins and executes FIRST; this plan's drift gate
re-checks the hunks that sibling landed in
`agents/skills/execute-plan/runtime-contract.md`.

Origin files (scope of record, under `docs/history/backlog/`):

- `2026-09-18-execute-plan-archived-sidecar-claim-immutable-history.md`
- `2026-09-18-execute-plan-sidecar-boundary-sentence-dedup.md`
- `2026-09-18-execute-plan-contract-requiredness-wording.md`
- `2026-09-18-execute-plan-recurrence-relay-consumer-seam.md`
- `2026-09-18-execute-plan-worktree-gitignored-bootstrap-gap.md`

## Terms

- Sidecar boundary rule: the rule that the readiness operation never reads review sidecars and the terminal gate's clean-round sidecar read is the only documented extension.
- Canonical sentence: the readiness-section wording of the sidecar boundary rule, quoted verbatim by SKILL.md.
- Recurrence relay: the done sub-agent's required verbatim relay of the `recurrence_groups` trigger status to the parent.
- Linked worktree: a `git worktree` checkout whose `.git` is a file, lacking the primary checkout's gitignored files.
- Step 0.5 gate: the execute-plan plan readiness gate that fails on a missing facts file, missing resolved directories, or missing certified review artifacts.

## Assumptions

- The five origin files listed above are the scope of record; quantities in this plan (sentence counts, line spans) were re-derived against the tree on 2026-09-19 and are re-derived by Task 1; basis: task constraint plus the three-executions caution.
- This plan executes after the phase-1 sibling plan; basis: the batch split rule in the authoring task, and both plans edit `runtime-contract.md`.
- Origin 3 closes as accept-as-immutable-history with a disposition note in the backlog item; the archived completed plan file is never edited; basis: the origin's own suggested direction and the document lifecycle.
- Origin 9 resolves by dropping the relay (the origin's direction (a)); no downstream consumer is added; basis: the origin's framing of the seam as pure redundancy, the simplicity principle, and the standing pre-authorization to accept recommended options.
- Origin 11 resolves as a skill-text bootstrap block whose follow-through a validation command executes verbatim (the origin's documentation variant of its completion evidence); basis: the origin's alternative evidence clause.
- Sentence-count calibration recorded at authoring: `never reads review sidecars` appears 2 times in `runtime-contract.md` and 1 time in `SKILL.md`; `the only optional field` appears 2 times in living surfaces (contract clause (4) and the `_pre_archive_gate` docstring in the driver); `recurrence status` (case-insensitive) appears 1 time in `SKILL.md` and 2 times in `subagent-prompts.md`; the literal `terminal-gate-only` appears exactly once in living surfaces (inside the sentence origin 5 deduplicates); Task 1 re-derives all of these.

Decision points requiring a grill: origin 9 direction: resolved by origin framing plus simplicity principle plus standing pre-authorization, 2026-09-19, Task 4; origin 11 variant: resolved by the origin evidence alternative, 2026-09-19, Task 5; origin 5 pointer form: resolved by the origin's suggested pointer wording, 2026-09-19, Task 3.

## Gist & Examples

Five deferred prose residuals close in one pass:

1. An archived completed plan carries an unqualified "the driver never reads
   review sidecars" claim made false by the staged-terminal work. Living
   surfaces are already amended; the archived copy is immutable history. The
   backlog item records the acceptance and closes without touching the
   archived file.
2. The sidecar boundary rule is stated twice in the runtime contract (the
   staged-terminal closing sentence and the readiness-section sentence) and
   drifts independently; SKILL.md quotes the readiness sentence verbatim.
   The staged-terminal sentence reduces to a pointer; the readiness sentence
   becomes the single canonical home. The literal `terminal-gate-only`
   dies with the deduplicated sentence (it appears nowhere else in living
   surfaces).
3. The staged-terminal contract says "the verdict is the only optional
   field", but `last_fix_commit` is equally tolerated absent or null (the
   ancestry check runs only when it is non-null). The clause is reworded to
   state both facts.
4. The done sub-agent's required verbatim recurrence relay has no consumer:
   Step 3.2 evaluates and writes the `recurrence_groups` line, and Step 3.5
   reads `manifest.md` directly. The relay requirement and the parent's
   recording clause are removed; the recurrence trigger machinery is
   untouched.
5. A fresh linked worktree lacks the gitignored inputs the Step 0.5 gate
   needs (facts file, reviews directory with the certified artifacts, tmp
   directory), so the gate fails for environment reasons the skill does not
   cover. Step 0.4 gains a worktree bootstrap block; a validation command
   executes the block verbatim inside a fresh worktree and asserts the gate
   inputs land.

## Evaluation Criteria

**Quality dimensions:**

- Single-source rule ownership: the sidecar boundary rule has exactly one canonical home after the dedup; every other mention points at it.
- Documentation truth: the requiredness clause matches the code's null handling field-for-field; the relay removal leaves the recurrence trigger machinery exactly as it was.
- Immutability: the archived completed plan is byte-identical before and after this plan.
- Verbatim executability: the worktree bootstrap block, copied verbatim from the skill text, produces a passing follow-through without improvisation.

**Done when:**

- `git diff --exit-code -- docs/plans/completed/2026-09-16-execute-plan-integrity-quad.md` is clean and the backlog item carries the disposition with a closed status.
- The canonical sidecar-boundary sentence appears exactly once in the runtime contract, the pointer once, and the SKILL.md quote is unchanged.
- The reworded requiredness clause names the verdict fall-through and the nullable `last_fix_commit`; the old phrase is gone.
- No recurrence relay requirement remains in `subagent-prompts.md` or `SKILL.md`; the Step 3.2 `recurrence_groups` machinery is intact.
- The Step 0.4 worktree bootstrap block exists and the follow-through validation passes in a fresh worktree.

**Ship when:** nothing external; all work is repository-verifiable.

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**

- `scripts/execute_plan_runtime.py` (Task 3 owns exactly one docstring span: the clause (4) twin parenthetical naming the optional-field and nullable `last_fix_commit` facts; every other span of the file is frozen)

**Tests:**

No test files are deliverables of this plan.

**Documentation:**

- `agents/skills/execute-plan/runtime-contract.md` (tasks own: the clause (4) requiredness sentence, the staged-terminal closing sidecar sentence; all other sections frozen)
- `agents/skills/execute-plan/SKILL.md` (tasks own: the Step 0.4 bootstrap block insertion, the Step 3.4 relay recording sentence removal; all other sections frozen)
- `agents/skills/execute-plan/subagent-prompts.md` (tasks own: the Done prompt's recurrence relay context bullet and required-output bullet)
- `docs/history/backlog/2026-09-18-execute-plan-archived-sidecar-claim-immutable-history.md` (task owns: the disposition note and status flip)

**Plan-related extension;** implementation and review may change files not
listed above when causally related. The Task 5 follow-through helper
`docs/tmp/b2-worktree-bootstrap-followthrough.sh` *(new, gitignored)* is
plan-related; everything else needs a causal link.

**Out of scope; reject unless plan-related:**

- `docs/plans/completed/2026-09-16-execute-plan-integrity-quad.md`; immutable history, verified untouched.
- `scripts/test_execute_plan_runtime.py`, `scripts/runtime_capabilities.py`; driver surfaces owned by the phase-1 sibling plan.
- `scripts/facts_paths.py`; the resolver stays as is; the bootstrap block fixes the inputs, not the resolver.
- `agents/skills/execute-plan/agent-logs.md` and other execute-plan sibling docs; no origin touches them.

## Design Invariants (CR Guard)

- Archived completed plans are frozen context; the phase-1 file's archive-safety machinery must never be edited to satisfy a wording finding.
- The Step 3.2 recurrence evaluation and the `recurrence_groups` line semantics are owned by the phase-3 reconciliation work; the relay removal must not touch them.
- The canonical sidecar-boundary sentence is quoted verbatim by SKILL.md; any rewording of the canonical home must move the quote in the same edit.
- The bootstrap block is a documented recipe, not new machinery: no script, no validator change, no facts-format change.

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from the repository root. Each gate fails loud; a subprocess error is
# not a pass.
set -u
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }
CONTRACT=agents/skills/execute-plan/runtime-contract.md
SKILL=agents/skills/execute-plan/SKILL.md
PROMPTS=agents/skills/execute-plan/subagent-prompts.md
ITEM=docs/history/backlog/2026-09-18-execute-plan-archived-sidecar-claim-immutable-history.md

# W1: the archived completed plan is untouched.
git diff --exit-code -- docs/plans/completed/2026-09-16-execute-plan-integrity-quad.md || fail "W1 archived plan modified"
grep -qF "accepted as immutable history" "$ITEM" || fail "W1 disposition missing"
grep -qF "Status: closed" "$ITEM" || fail "W1 status not closed"

# W2: requiredness clause states both facts; the old phrase is gone.
expect_contains() { grep -qF -- "$2" "$1" || fail "missing in $1: $2"; }
expect_contains "$CONTRACT" "the verdict is the only field whose absence falls through"
expect_contains "$CONTRACT" "absent or null skips the ancestry check"
test "$(grep -cF 'the only optional field' "$CONTRACT")" -eq 0 || fail "W2 old phrase remains"
DRIVER=scripts/execute_plan_runtime.py
expect_contains "$DRIVER" "the only field whose absence falls through"
test "$(grep -cF 'the only optional field' "$DRIVER")" -eq 0 || fail "W2b old docstring phrase remains"

# W3: the sidecar boundary rule has one canonical home plus one pointer.
test "$(grep -cF 'never reads review sidecars' "$CONTRACT")" -eq 1 || fail "W3 canonical sentence count"
expect_contains "$CONTRACT" "the sidecar boundary is owned by the readiness section's sentence above"
test "$(grep -cF 'never reads review sidecars' "$SKILL")" -eq 1 || fail "W3 SKILL quote count"
test "$(grep -cF 'terminal-gate-only' "$CONTRACT")" -eq 0 || fail "W3 dead label remains"

# W4: the relay is gone; the Step 3.2 machinery is intact.
test "$(grep -ciF 'recurrence status' "$PROMPTS")" -eq 0 || fail "W4 relay bullet remains in prompts"
test "$(grep -ciF 'recurrence status' "$SKILL")" -eq 0 || fail "W4 recording clause remains in SKILL"
test "$(grep -cF 'Update the `recurrence_groups` manifest line' "$SKILL")" -eq 1 || fail "W4 Step 3.2 machinery altered"

# W5: the worktree bootstrap block exists and its follow-through passes.
expect_contains "$SKILL" "Linked-worktree bootstrap"
bash docs/tmp/b2-worktree-bootstrap-followthrough.sh || fail "W5 follow-through"

# W6: hygiene over the plan file itself (existing prose files are frozen
# regions and are deliberately not swept).
if grep -q $'\xe2\x80\x94' docs/plans/2026-09-19-execute-plan-driver-residuals-batch-2-phase-2-contract-prose.md; then fail "W6 em-dash in plan"; fi
```

Authoring-time execution record (2026-09-19, post r1 folds): bash -n clean.
W1 red today (no disposition yet). W2 red today (new phrases absent; old
phrase count 1). W3 red today (canonical count 2, pointer absent, dead
label count 1). W4 red today (counts 2 and 1; Step 3.2 line green). W5 red
today (block and follow-through absent). W6 green today. Every red gate
maps to exactly one owning task. The W5 follow-through script is authored
by Task 5 and must exist at `docs/tmp/b2-worktree-bootstrap-followthrough.sh`
before the final sweep runs; `docs/tmp/` is gitignored, so the final sweep
re-authors it from the task text when absent. Review r1 verdict: ready=no
with one blocking finding (the Review Scope `none` bullets collided as
duplicate tokens in the readiness validator); folded together with the
three non-blocking findings (driver docstring twin now owned by Task 3,
follow-through ordering clarified with a facts-resolution smoke and the
evidence boundary stated, classification tags completed). Review r2
verdict: ready=no with one blocking finding (Review Scope path-kind and
inventory mismatches against the readiness validator's path rule, masked
in r1 by the early stale-digest return); folded together with the four
non-blocking r2 lows (driver old-phrase count gate W2b, follow-through
teardown trap, calibration line names both `the only optional field`
living occurrences, Task 5 commit bullet moved above its dependents);
this digest is the r3 input.

### Task 1: Phase 0 drift gate (re-derive spans, confirm phase-1 landings)

Files:
- none (read-only gate)

- [x] Re-read the five origin files; re-derive every count in the Assumptions calibration and every pinned sentence against the current tree; where a span drifted, update this plan in the same edit and record the drift; classification [class: REPOSITORY_TEST]
- [x] Confirm the phase-1 sibling plan landed (the clause (4) bounded-sidecar sentence and the checkpoint caller envelope section exist in the contract); when it did not, sequence after it; classification [class: REPOSITORY_TEST]
- [x] Stand down and report when a peer session holds any of the four target files dirty; classification [class: REPOSITORY_TEST]

### Task 2: Archived-history disposition (origin: archived sidecar claim)

Files:
- `docs/history/backlog/2026-09-18-execute-plan-archived-sidecar-claim-immutable-history.md`

- [x] Flip the item status to `Status: closed (accepted as immutable history)` and append a disposition note recording: acceptance date, the superseded-by owners (the readiness section sentence and the staged terminal section of `agents/skills/execute-plan/runtime-contract.md`), and that the archived file stays untouched per the document lifecycle; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Verify `git diff --exit-code -- docs/plans/completed/2026-09-16-execute-plan-integrity-quad.md` stays clean; classification [class: REPOSITORY_TEST]
- [x] Commit: `docs: record immutable-history disposition for the archived sidecar claim` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Requiredness wording and boundary dedup (origins: contract requiredness, sidecar boundary dedup)

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `scripts/execute_plan_runtime.py` (one docstring span only; see Review Scope)

- [x] Reword the clause (4) parenthetical to: the verdict is the only field whose absence falls through, and `last_fix_commit` is nullable (absent or null skips the ancestry check); keep the surrounding non-null ancestry requirement intact; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Twin the same reword in the `_pre_archive_gate` docstring's clause (4) parenthetical, which today carries the identical overstated claim (the `the only optional field` phrasing beside the sidecar-path sentence), so the docstring and the contract state the same facts in the same edit; prescribe the twin wording verbatim as: the verdict is the only field whose absence falls through, and `last_fix_commit` is nullable (absent or null skips the ancestry check); every other span of the driver file stays frozen; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Replace the staged-terminal closing sidecar sentence with the pointer: the sidecar boundary is owned by the readiness section's sentence above; the literal `terminal-gate-only` dies with this sentence; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the readiness-section canonical sentence and its verbatim SKILL.md quote are byte-unchanged by this task; classification [class: REPOSITORY_TEST]
- [x] Commit: `docs: dedup the sidecar boundary rule and correct requiredness wording` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Drop the recurrence relay (origin: recurrence relay consumer seam)

Files:
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] Remove the Done prompt context bullet `- Recurrence status: <verbatim recurrence_groups trigger status from manifest.md>` and the required-output bullet beginning `- Recurrence status: relay the recurrence status line verbatim`; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Remove the Step 3.4 recording sentence (the parent records the relayed recurrence status against the `recurrence_groups` line); leave the Step 3.2 evaluation, the trigger table, and Hard Gate 24 untouched; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Verify no case-insensitive `recurrence status` mention remains in either file and the Step 3.2 ledger sentence occurs exactly once; classification [class: REPOSITORY_TEST]
- [x] Commit: `docs: drop the consumer-less recurrence relay requirement` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Worktree bootstrap block (origin: worktree gitignored bootstrap gap)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `docs/tmp/b2-worktree-bootstrap-followthrough.sh` *(new, gitignored)*

- [x] Insert into Step 0.4, after the machine-manifest seeding paragraph, a block titled `**Linked-worktree bootstrap (before the Step 0.5 gate):**` prescribing exactly this recipe, fenced as bash: [class: IMPLEMENTATION_REQUIRED]

```bash
if [ -f .git ]; then
  PRIMARY="$(git worktree list --porcelain | sed -n 's/^worktree //p' | head -1)"
  mkdir -p .ai-playbook docs/reviews docs/tmp
  test -f .ai-playbook/facts.md || cp "$PRIMARY/.ai-playbook/facts.md" .ai-playbook/facts.md
  if [ -d "$PRIMARY/docs/reviews" ]; then
    cp -R "$PRIMARY/docs/reviews/." docs/reviews/
  fi
fi
```

  followed by one sentence: run this before the Step 0.5 readiness gate whenever the checkout is a linked worktree, resolve `reviews_dir`/`tmp_dir` from the facts TOML fence when it defines them instead of the defaults shown, and re-run the Step 0.5 gate after the bootstrap; classification [class: IMPLEMENTATION_REQUIRED]
- [x] Commit (SKILL.md only; the follow-through script lives under gitignored `docs/tmp/`): `docs: add the linked-worktree bootstrap to Step 0.4` [class: IMPLEMENTATION_REQUIRED]
- [x] Author `docs/tmp/b2-worktree-bootstrap-followthrough.sh` (after the commit bullet above has landed, so a worktree of HEAD carries the block): create a detached worktree of HEAD in a temp parent (`git worktree add --detach <path> HEAD`), assert the worktree `.git` is a file, assert `.ai-playbook/facts.md` and `docs/reviews` are absent, create a probe artifact `b2-bootstrap-probe-r1.md` in the primary checkout's `docs/reviews/`, execute the prescribed block verbatim inside the worktree (extracted from the committed SKILL.md text, not from this plan), assert `facts.md` arrived byte-identical, the probe artifact arrived, and `docs/tmp/` exists, resolve the facts keys inside the worktree as a gate-input smoke (`python3 scripts/facts_paths.py`-equivalent read of the TOML fence, asserting non-empty `reviews_dir` and `tmp_dir`), and exit 0; any assertion failure exits nonzero, and teardown (probe artifact removal plus `git worktree remove --force`) runs on the failure path too through a trap, so a failed assert never leaks the worktree or the probe artifact; evidence boundary: the full Step 0.5 gate additionally needs a certified plan-plus-sidecar pair, which the origin's documentation variant deliberately does not require; this follow-through proves the block lands every input the gate resolves; classification [class: REPOSITORY_TEST]
- [x] Run the follow-through → expect exit 0; classification [class: REPOSITORY_TEST]

### Task 6: Final validation sweep

Files:
- none (verification only)

- [x] Run the full Validation Commands block from the repository root → expect every gate green; re-author the W5 follow-through from the Task 5 text if `docs/tmp/` was cleaned between tasks; classification [class: REPOSITORY_TEST]
- [x] Run the pin-versus-prescribed-text audit: every pinned sentence in this plan occurs verbatim at its target or is an authored-today phrase recorded in the authoring execution record; all counts re-derived; classification [class: REPOSITORY_TEST]
- [x] Run the public hygiene scan from the repository root; expect exit 0; classification [class: REPOSITORY_TEST]
- [x] Commit (if anything moved): `chore: batch 2 phase 2 final sweep` [class: REPOSITORY_TEST]

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-19-schedule-vs-execute-verb-contract.md: disposition folded into 2026-09-19-execute-plan-driver-residuals-batch-2-phase-2-contract-prose.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-17-execute-plan-worker-deadline-contract.md: disposition folded into 2026-09-19-execute-plan-driver-residuals-batch-2-phase-2-contract-prose.md (2026-09-25); per-item file deleted.
