# Plan: rolling-log write residue recovery recipe

Backlog origin: docs/history/backlog/2026-11-07-rolling-log-freeze-foreign-bytes-setaside-recipe.md
Driving force: correctness
Plan review record: the staging series .ai-playbook/reviews/2026-11-07-plan-review-rolling-log-write-residue-recovery-recipe-p29d8406e-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.5h total, largest task 0.5h
Authoring claim: 2026-11-07-rolling-log-freeze-foreign-bytes-setaside-recipe.md (session sess_dd27a4f2-4e4e-414e-96d7-66bc6f0e731f)
Executed: no

Design input (prose only, never a Backlog origin): the PLAN-PROMPTS entry `rolling-log-write-residue-recovery-recipe` in docs/history/backlog/PLAN-PROMPTS.md, which routes this item; its admission fields, scope arms, and rejected alternatives are adopted here.

## Terms

- Write boundary rule: the Standing rules bullet in `docs/history/backlog/PLAN-PROMPTS.md` that owns primary rolling-log writes and carries the operator-gated, blob-preserving remedy for a foreign staged path (steps (a) through (e), the ride-along precondition, the acknowledgment arm admission text).
- Two-path staged-delta check: `scripts/done_run.sh` `cmd_commit`'s refusal, before any staging, when either rolling-log path already carries a staged delta; its trigger and behavior are unchanged by this plan.
- Staged-set enumeration: the second `cmd_commit` pre-stage refusal, when a staged path sits outside the writer's declared owned log set (guard ordering means it names only non-rolling-log paths; the widened trigger names it for completeness, and its message keeps its existing text).
- Foreign staged path: a rolling-log path whose staged index bytes were staged by a session other than the writer, whether or not the writer declared that path.
- Unstaged live delta: worktree-only bytes on a rolling-log path that the index does not stage; a peer's live emission, whether or not the path also carries a foreign staged blob and whether or not the writer declared the path. The runner commits a declared log path's worktree bytes (project lesson 290), so unstaged peer bytes on a declared path ride the writer's commit unless dispositioned first.
- Unstaged-live-delta set-aside arm: the remedy clause this plan adds to the Write boundary rule, covering the unstaged-live-delta cases: record each preserved byte set into the object store, hold it out of the committed tree across the transaction, re-apply it after, verify byte identity.
- Staged blob sha / worktree blob id: the git blob object id of the path's staged index bytes / worktree bytes; a blob id that is not already in the object store is stored first with `git hash-object -w` so the id resolves for recovery.
- Lesson 290 construction: the own-hunk commit discipline (project `docs/maintenance/development_lessons.md` lesson 290): for the commit's duration the worktree file holds exactly HEAD plus the writer's own edit; foreign dirt is re-applied afterward.
- Ride-along precondition: the Write boundary rule clause re-verifying the foreign path's worktree bytes equal its staged blob immediately before and after the unstage/re-add window.
- Phase 0 freeze: the entry-keyed authoring run's Frozen: line write to the rolling log, owned by the plans skill's Entry freeze duty; the authoring-session blueprint orders it before worktree creation.
- Pre-plan authoring arm: the worktree-first standard's authoring-worktree creation arm (derive the branch name `authoring/<claim-file-stem>`, create the worktree, verify the branch).
- Rule 42: the plans authoring rules' filing-class consumption rule (`agents/skills/plans/validation-authoring-rules.md` rule 42).

## Why

Two authoring freeze writes were blocked by rolling-log residue in one day, and both blocked sessions had to choose between archaeology and improvisation: the refusal message says only "resolve it before any primary log write", and the standing remedy's re-add-and-verify step can never pass when the foreign staged path also carries an unstaged live delta, while an unstaged-only peer delta on the writer's own declared path fires no guard at all yet would ride the writer's commit. The remedy already exists in the log's own Standing rules and the plans skill's Entry freeze duty already routes recovery to it; what is missing is the pointer at the surfaces a blocked session reads at the moment of refusal, and the arm for the unstaged cases the remedy text does not yet cover.

## Gist & Examples

TLDR: the rolling-log pre-stage refusal message and the two pre-work procedures point at the Write boundary rule's operator-gated remedy, and the remedy gains the widened trigger plus the Unstaged-live-delta set-aside arm with stored blob ids and byte-identical re-apply verification, so a blocked freeze resolves without archaeology, naming correctness as the driving force.

Before (today): a freeze write meeting residue reads "resolve it before any primary log write" and stops; one session hand-rolled an unstaged set-aside without recording the blob id (the 2026-11-07 10:33 UTC anti-shape: a set-aside landed with no blob id recorded), another stood down when the operator-gated staged-path remedy dead-ended on its own re-add step (the 2026-11-07 15:50 UTC second witness, landing 1f5123f6a's residue); a peer's unstaged-only entry on the writer's declared path fires no refusal and would be swept into the writer's commit.

After (this plan): the same refusal names the Write boundary rule's remedy, its Standing rules home, its operator gate, and its declared-or-not coverage; the two pre-work procedures carry the same pointer; the remedy's widened trigger covers both pre-stage guards, and its new arm completes the witnessed cases with stored blob ids and a byte-identical re-apply verification that parks on mismatch.

Example: the next dispatch's Phase 0 freeze meets a foreign staged snapshot plus a peer's unstaged entry on `docs/history/backlog/PLAN-PROMPTS.md`, the path the freeze itself writes; the refusal message points at the Standing rules remedy; with operator direction the session records both byte sets into the object store, holds them out of the committed tree so the transaction commits exactly the writer's own edit (the lesson 290 construction), re-applies the peer's unstaged entry as worktree dirt after the commit, verifies its blob id, and reports the recorded staged snapshot's blob id for the operator's disposition.

Edge cases: the guard's refusal trigger stays byte-identical (only the message text gains the pointer); an unattended writer still stands down or parks (the operator gate is unchanged); a re-apply verification mismatch leaves the bytes unstaged and parks for the operator with every recorded blob id in the report; a declared foreign path's staged blob is never re-staged by the arm (its blob id stays recorded for the operator's disposition); the fold-deleted origin row's durable home `docs/history/plans/completed/2026-11-02-rolling-log-write-foreign-staged-remedy.md` keeps owning the producer-side guard, so no guard behavior changes here.

## Outcome

A blocked primary rolling-log write resolves through one named, operator-gated remedy instead of archaeology or improvisation.

- The refusal message and both pre-work procedures name the Write boundary rule's remedy, its Standing rules home, and its operator gate.
- The remedy completes for the witnessed cases: a foreign staged path with or without an unstaged live delta, whether or not the writer declared the path, and a declared log path carrying only an unstaged live peer delta; stored blob ids, exclusion across the transaction, byte-identical re-apply.
- No gate, validator, lock, ledger, or refusal class is added; the guard's trigger, the operator gate, and the stand-down default are unchanged.

Gate delta: none. Message text only in `scripts/done_run.sh`; prose pointers appended to two existing procedure paragraphs; the widened trigger and one remedy arm added to the existing Write boundary rule text (operator-gated prose guidance over the same refusals, priced by the origin row's scope arms). No new refusal class, hard gate, fence, protocol layer, or schema field; the guard's refusal trigger stays byte-identical, so the plan adds no refusal surface.

## Assumptions

- The origin row's declared `Class:` line (fix-class) matches its body: the plan removes a discoverability gap and a remedy-text gap, adds no refusal surface, and takes no refusal-path addition, so the Rule 42 no-exit justification is not needed.
- The Write boundary rule's Standing rules bullet is the remedy's single home; the widened trigger and the Unstaged-live-delta set-aside arm extend that existing remedy paragraph rather than adding a second rule or a new Standing rules entry.
- The wrapper suite asserts only the refusal message's unchanged leading text; the Task 3 replacement keeps that prefix byte-identical (the prefix `rolling-log pre-stage guard: a staged delta already exists on a rolling prompt log` is asserted by `scripts/test_done_run_wrapper.py`).

Decision points requiring a grill: none remain.

## Standing constraints

- The two-path staged-delta check's trigger and behavior stay byte-identical; only the refusal message text changes.
- The remedy's operator gate and the unattended stand-down-or-park default stay byte-identical in every surface this plan touches.
- Every prescribed insertion is quoted verbatim in the plan and lands byte-identical.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the refusal message and both procedure pointers name the same remedy, the same home, and the same operator gate, with no contradiction to the existing ride-along precondition, steps (a) through (e), or the acknowledgment arm.
- Completeness: the arm covers the witnessed cases (declared and undeclared foreign paths, with and without unstaged deltas, and the unstaged-only declared-path case), with the set-aside ordered before the ride-along precondition and the re-apply ordered after the re-add step.
- Minimalism: no surface other than the three must-fix files changes; no machinery is added.

**Done when:**
- The refusal message in `scripts/done_run.sh` names the Write boundary rule's operator-gated remedy and its Standing rules home, with the guard's trigger unchanged (`bash -n scripts/done_run.sh` passes).
- The Write boundary rule bullet carries the widened trigger and the Unstaged-live-delta set-aside arm with stored blob ids, the set-aside-before-precondition ordering, the re-apply-after-re-add ordering, and the declared-path steps exception.
- Both pre-work procedures carry the pointer sentence verbatim as prescribed.
- The repository gates pass: the pins suite over the touched pinned files, the em-dash added-lines gate over the landing range, and the public hygiene scan.

**Ship when:**
- Not applicable (repository-internal prose and message text; no deployment step).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_run.sh` (Task 3)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 1)
- `agents/skills/maintenance/template-authoring.md` (Task 2)
- `agents/skills/execute-plan/worktree-first.md` (Task 2)

**Tests:**
- none new; the existing wrapper suites are untouched and stay green

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates.sh` and `scripts/done_sweep_gates_lib.py`; reason: the sweep gates are not the refusing surface this plan points at
- `docs/history/backlog/EXEC-PROMPTS.md`; reason: the execution log's write discipline is unaffected by this plan
- `agents/skills/plans/SKILL.md` Entry freeze paragraph; reason: it already routes recovery to the Write boundary rule, and its span is pin-guarded (`prune_range_pin` in `scripts/check_maintenance_pins.sh`), so re-keying the pin for a redundant pointer is not warranted
- the two-path staged-delta check's trigger logic beyond the message string in `scripts/done_run.sh`; reason: the guard's behavior is unchanged by design

## Validation Commands

Preamble (authoring-time records, rule 29): the em-dash gate ran `bash scripts/check-no-em-dash.sh touched` over the plan bytes with `OUTCOME: pass` (re-run after the r1 and r2 folds, pass each time); the public hygiene scan ran over the plan bytes with `OUTCOME: pass` (re-run after each fold, pass); the pre-round readiness gate ran `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-07-rolling-log-write-residue-recovery-recipe.md` with `OUTCOME: pass` (re-run after each fold, pass); the RED-today evidence for the blocking greps was executed at authoring time and re-executed after the r1 and r2 folds (every new literal absent, recorded rc=1 each); the rule 22 mechanical audit (pinned-span exactly-once extraction plus `bash -n` over this block) ran at authoring and after each fold, pass each time.

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
fail() { echo "VALIDATION FAIL: $1"; exit 1; }

# 1. Task 3: the pre-stage refusal message names the remedy, its home, and the declared-or-not coverage.
#    RED today (2026-11-07, at 4e7efd196): the message lacks the pointer; recorded rc=1 (re-verified after the r1 fold).
grep -qF "resolve it through the Write boundary rule's operator-gated remedy" scripts/done_run.sh \
  || fail "refusal message missing the Write boundary rule remedy pointer"
grep -qF "docs/history/backlog/PLAN-PROMPTS.md Standing rules" scripts/done_run.sh \
  || fail "refusal message missing the remedy home pointer"
# 2. Task 3: the guard's trigger is unchanged: the refusal still precedes staging and still exits 1.
bash -n scripts/done_run.sh || fail "done_run.sh syntax"
grep -qF 'commit_die 1 "rolling-log pre-stage guard: a staged delta already exists on a rolling prompt log' scripts/done_run.sh \
  || fail "pre-stage guard refusal class changed"
# 3. Task 1: the widened trigger names both pre-stage guards (unique span; whole-file pin).
#    RED today: absent at authoring; recorded rc=1 (re-verified after each fold).
test "$(grep -oF 'either the two-path staged-delta check or the staged-set enumeration' docs/history/backlog/PLAN-PROMPTS.md | wc -l | tr -d ' ')" -eq 1 \
  || fail "Write boundary rule missing the widened trigger (or span duplicated)"
# 4. Task 1: the Unstaged-live-delta set-aside arm with stored blob ids and both orderings (unique spans).
#    RED today: absent at authoring; recorded rc=1 (re-verified after each fold).
test "$(grep -oF 'Unstaged-live-delta set-aside arm' docs/history/backlog/PLAN-PROMPTS.md | wc -l | tr -d ' ')" -eq 1 \
  || fail "Write boundary rule missing the set-aside arm label (or span duplicated)"
grep -qF "the stored blob id the only recovery source" docs/history/backlog/PLAN-PROMPTS.md \
  || fail "arm missing the hash-object -w storage clause"
grep -qF "evaluated after this set-aside, never before it" docs/history/backlog/PLAN-PROMPTS.md \
  || fail "arm missing the set-aside-before-precondition ordering"
grep -qF "the precondition's worktree-equals-staged-blob comparison does not apply" docs/history/backlog/PLAN-PROMPTS.md \
  || fail "arm missing the declared-path precondition scoping"
grep -qF "after the compare-and-swap on a path the writer declared" docs/history/backlog/PLAN-PROMPTS.md \
  || fail "arm missing the declared-path re-apply timing"
grep -qF "carries a foreign staged blob (with or without an unstaged live delta)" docs/history/backlog/PLAN-PROMPTS.md \
  || fail "arm trigger missing the declared-no-delta case"
grep -qF "steps (d) and (e) do not run for that path" docs/history/backlog/PLAN-PROMPTS.md \
  || fail "arm missing the declared-path steps exception"
grep -qF "verifies the re-applied bytes hash to their recorded blob ids" docs/history/backlog/PLAN-PROMPTS.md \
  || fail "arm missing the re-apply verification"
grep -qF "parks for the operator with every recorded blob id" docs/history/backlog/PLAN-PROMPTS.md \
  || fail "arm missing the mismatch park"
# 5. Task 1: the operator gate and stand-down default survive in the Write boundary rule.
grep -qF "the remedy runs only on the operator's explicit direction" docs/history/backlog/PLAN-PROMPTS.md \
  || fail "operator gate wording lost"
# 6. Task 2: both pre-work procedures carry the pointer (unique span per file).
#    RED today: absent at authoring; recorded rc=1 (re-verified after the r1 fold).
test "$(grep -cF "the Write boundary rule's operator-gated remedy" agents/skills/maintenance/template-authoring.md)" -eq 1 \
  || fail "template-authoring pre-work paragraph missing the remedy pointer"
test "$(grep -cF "the Write boundary rule's operator-gated remedy" agents/skills/execute-plan/worktree-first.md)" -eq 1 \
  || fail "worktree-first pre-plan arm missing the remedy pointer"
# 7. Repository gates over the touched set.
bash scripts/check_maintenance_pins.sh || fail "pins suite"
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base main HEAD)" || fail "em-dash added-lines gate"
```

### Task 1: widen the Write boundary rule trigger and add the Unstaged-live-delta set-aside arm

Context surface: the plan's Terms and Standing constraints; referenced, never restated.

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`

- [ ] The Write boundary rule delivers the widened trigger: given a pre-stage refusal naming a foreign staged path from either pre-stage guard, expects the remedy's opening clause to name both guards (the two-path staged-delta check and the staged-set enumeration) and to apply whether or not the writer declared the path [class: IMPLEMENTATION_REQUIRED]
- [ ] The Write boundary rule delivers the Unstaged-live-delta set-aside arm: given a foreign staged path whose worktree bytes carry an unstaged live delta, or a declared log path carrying an unstaged live peer delta with no staged residue, expects the arm to prescribe recording each preserved byte set into the object store (`git hash-object -w`), holding it out of the committed tree across the transaction, and re-applying it after with byte-identical verification [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness (ordering): given the same residue condition, expects the ride-along precondition to be evaluated after the set-aside, never before it, the re-apply on an undeclared foreign path to run after step (e) passes, and the re-apply on a declared path to run after the compare-and-swap, never before the transaction's commit [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness (declared path): given a foreign staged blob on the writer's own declared log path, with or without an unstaged delta, expects the arm to activate, steps (d) and (e) not to run for that path, the precondition comparison not to apply, the staged blob never re-staged, and its blob id reported for the operator's disposition [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness (mismatch): given a re-apply verification mismatch, expects the bytes left unstaged and the run parked for the operator with every recorded blob id in the report [class: IMPLEMENTATION_REQUIRED]
- [ ] Replace, in the Write boundary rule bullet, exactly the span `When the runner's pre-stage guard (the staged-set enumeration) refuses the transaction naming a foreign staged path (staged in the shared primary index by a session other than this writer, outside the writer's declared owned set), the remedy is operator-gated and blob-preserving` with the following span, keeping the following tail `: never stage, discard, or commit that path autonomously` byte-identical [class: IMPLEMENTATION_REQUIRED]:

```text
When the runner's pre-stage guard (either the two-path staged-delta check or the staged-set enumeration) refuses the transaction naming a foreign staged path (staged in the shared primary index by a session other than this writer, whether or not the writer declared that path), the remedy is operator-gated and blob-preserving
```

- [ ] Insert the following arm text into the Write boundary rule bullet immediately before the sentence beginning `Ride-along precondition:`, byte-identical [class: IMPLEMENTATION_REQUIRED]:

```text
Unstaged-live-delta set-aside arm: when the foreign staged path also carries an unstaged live delta, or the writer's declared log path carries a foreign staged blob (with or without an unstaged live delta) or an unstaged live peer delta with no staged residue, the plain steps cannot complete (the re-add stages the worktree bytes, the staged blob plus the delta, so the sha check can never match; and a declared path's transaction would commit foreign or peer bytes together with the writer's own). Under the same operator direction the writer first records each preserved byte set into the object store (`git hash-object -w`, the stored blob id the only recovery source) and then sets the path's worktree bytes so the transaction sees only the writer's own state: on a path the writer declared, exactly the writer's committed base plus the writer's own edit (the lesson 290 construction); on a foreign path the writer did not declare, the recorded staged blob. The ride-along precondition is evaluated after this set-aside, never before it; on a path the writer declared, the precondition's worktree-equals-staged-blob comparison does not apply (the set-aside construction carries the identity, and the recorded blob ids are the verification of record). The transaction then runs; the writer re-applies each recorded delta to the worktree only, never the index, after step (e) passes on a foreign path the writer did not declare, and after the compare-and-swap on a path the writer declared; the re-apply verifies the re-applied bytes hash to their recorded blob ids before reporting success; on a path the writer declared, steps (d) and (e) do not run for that path: the writer's own commit already carries the path, the recorded delta re-applies as unstaged worktree bytes verified against their blob ids, and the recorded foreign staged blob stays out of the index, its blob id reported for the operator's disposition; a verification mismatch, and any byte set the re-apply cannot verify, leaves the bytes unstaged and parks for the operator with every recorded blob id in the report.
```

- [ ] Run → expect RED: validation commands 3 and 4 fail on today's bytes (executed at authoring; recorded rc=1) [class: REPOSITORY_TEST]
- [ ] Write both prescribed spans byte-identical [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation commands 3, 4, and 5 pass [class: REPOSITORY_TEST]
- [ ] Commit: `docs: widen the Write boundary rule trigger and add the set-aside arm` [class: IMPLEMENTATION_REQUIRED]

### Task 2: point the pre-work procedures at the remedy

Context surface: the plan's Terms and Standing constraints; referenced, never restated.

Files:
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/execute-plan/worktree-first.md`

- [ ] Both pre-work procedures name the remedy: given a session reading either procedure's pre-work text, expects the text to name the Write boundary rule's operator-gated remedy and its Standing rules home, with the residue cases (foreign staged bytes, unstaged live deltas) and the unattended stand-down-or-park default named [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert the following sentence at the end of the paragraph in `agents/skills/maintenance/template-authoring.md` that opens "Before writing anything: verify no merge or rebase is in progress", byte-identical [class: IMPLEMENTATION_REQUIRED]:

```text
When the Phase 0 entry freeze (the plans skill's Entry freeze duty) or any other primary rolling-log write meets foreign staged bytes or an unstaged live delta on a rolling-log path, the Write boundary rule's operator-gated remedy (docs/history/backlog/PLAN-PROMPTS.md Standing rules) owns the resolution, and an unattended writer stands down or parks without operator direction.
```

- [ ] Insert the same sentence (byte-identical) at the end of the pre-plan authoring arm paragraph in `agents/skills/execute-plan/worktree-first.md` (the paragraph deriving the branch name `authoring/<claim-file-stem>` and creating the worktree) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: validation command 6 fails on today's bytes (executed at authoring; recorded rc=1) [class: REPOSITORY_TEST]
- [ ] Write both insertions byte-identical [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation command 6 passes for both files [class: REPOSITORY_TEST]
- [ ] Commit: `docs: point the pre-work procedures at the set-aside remedy` [class: IMPLEMENTATION_REQUIRED]

### Task 3: point the pre-stage refusal message at the remedy

Context surface: the plan's Terms and Standing constraints; referenced, never restated.

Files:
- `scripts/done_run.sh`

Primary class anchors:
- `cmd_commit` in `scripts/done_run.sh`

- [ ] The refusal message names the remedy: given the two-path staged-delta check refusing a staged delta on a rolling prompt log, expects the message to name the Write boundary rule's operator-gated remedy, its `docs/history/backlog/PLAN-PROMPTS.md Standing rules` home, the declared-or-not and unstaged-delta coverage, and the unattended stand-down-or-park default [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness: given the same staged-delta condition, expects the refusal to still precede any staging, still exit 1, and still leave residue untouched (message text is the only change) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect RED: validation command 1 fails on today's bytes (executed at authoring; recorded rc=1) [class: REPOSITORY_TEST]
- [ ] Replace, inside the refusal string at the `rl_residue` site of `cmd_commit`, exactly the middle clause `resolve it before any primary log write` with the following span, keeping the leading `rolling-log pre-stage guard: a staged delta already exists on a rolling prompt log; ` and the trailing `; residue left untouched: $(printf '%s' "$rl_residue" | tr '\n' ' ')` byte-identical [class: IMPLEMENTATION_REQUIRED]:

```text
resolve it through the Write boundary rule's operator-gated remedy (docs/history/backlog/PLAN-PROMPTS.md Standing rules; covers foreign staged bytes whether or not the writer declared the path, with or without an unstaged live delta; an unattended writer stands down or parks without operator direction)
```

- [ ] Run → expect GREEN: validation commands 1 and 2 pass [class: REPOSITORY_TEST]
- [ ] Commit: `fix: point the rolling-log pre-stage refusal at the operator-gated remedy` [class: IMPLEMENTATION_REQUIRED]

### Task 4: repository gates

Context surface: the plan's Validation Commands block; referenced, never restated.

Files: none (validation only)

- [ ] Run the full Validation Commands block from the repository root; every command exits zero [class: REPOSITORY_TEST]
- [ ] Run the public hygiene scan over the touched set; `OUTCOME: pass` [class: REPOSITORY_TEST]
- [ ] A gate-driven correction rides the owning task's next commit, never a separate silent edit [class: IMPLEMENTATION_REQUIRED]
