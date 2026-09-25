# Plan: Returned-for-ask drift hygiene (archive record, sibling gate, r7 residuals)

Backlog origin: `docs/history/backlog/2026-09-07-plan-task3-returned-for-ask-wording-drift.md` (plan-body drift + sibling forward conflict)
Backlog origin: `docs/history/backlog/2026-09-07-returned-for-ask-drift-hygiene-residuals.md` (7 enumerated r7 residuals)

## Terms

- **returned-for-ask record**: the record triage leaves on a finding held `pending` for the fix-risk user decision; consists of the literal marker `returned-for-ask`, the fix-risk rationale, and the question to relay. Shape is owned by `review-staging`'s receiving-review consumer row.
- **discharge split**: the rule that a non-blocking ask is discharged by recording the returned-for-ask record, while a must-stay-blocking ask is never discharged by recording and stops for direction. Owned by `execute-plan` Step 3.3 verification gate item 6.
- **must-stay-blocking ask**: a fix-risk ask whose finding still meets a blocking condition after re-evaluation, so recording cannot discharge it.
- **stop class**: a loop stop whose user ask must relay outstanding or recorded-but-not-yet-surfaced returned-for-ask questions (cap stop, sixth-panel/escalation stop, fix-risk stop, re-entry mid-round stop, failure/timeout/interrupt stop).
- **reconciliation precedence**: the ordering rule that `review-reconciliation` runs before another direction (continuation, cap stop, or fix-risk stop) when both apply; stated exactly once per skill file.
- **Skill-gate marker; Session key**: per `ai-playbook/agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (plans class); refreshed before every plan-file write via `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker --session-id "$SID"` with `SID="$(python3 ~/.ai-playbook/scripts/session_channel.py)"`.

## Assumptions

- assume the residual backlog file's title count "8 deferred residuals" is stale; the 7 enumerated items are the scope of record; basis: the file's Items section enumerates exactly 7.
- assume `execute-plan` Step 3.3 verification gate item 6 is the canonical home of the discharge split; basis: `review-loop` orchestration rule 4 and the `receiving-review` Fix-risk closing already cite it as the authorized discharge.
- assume `review-staging` owns the returned-for-ask record-element definition; basis: it is the staging gold source and already hosts the receiving-review consumer row.
- assume the sibling plan `docs/plans/2026-09-04-review-pointer-wiring-polish.md` is handled by an execution-gate annotation (re-derive prescriptions before executing), not by rewriting its Task text in this plan; basis: the backlog item requires "do not execute it as authored", and rewriting its tasks would invalidate its certification digest and exceed this plan's drift-record scope.

Decision points requiring a grill: none remain.

## Gist & Examples

This plan closes the wording-drift debt left by the returned-for-ask semantics work (squash-merged to main as e754d33). Two kinds of drift remain. First, historical drift: the archived plan `docs/plans/completed/2026-09-04-returned-for-ask-semantics.md` still carries pre-r1/r2 prescriptions (its Terms definition of an outstanding presentation, its Gist item 3, and its Task 3 checkboxes) that contradict the shipped skill text; its validation pins are substrings of both variants, so no mechanical check can see the divergence. Second, live drift: the r7 exit round of the semantics execution deferred seven drift-hygiene residuals across five skill files, all about how the discharge split and the returned-for-ask record are restated, scoped, and named.

**Example (archive record):** the archived plan's Terms bullet says an outstanding presentation is one "whose question has not yet been relayed to the user (or returned to the orchestrator / turned into a stop for direction in a non-interactive run)". **After (this plan):** the shipped text governs and the archived plan carries an archive note saying exactly which spans are superseded and why the body stays frozen; the note is the durable record reviewers consult instead of trusting the Terms bullet.

**Example (sibling forward conflict):** the unexecuted sibling plan `docs/plans/2026-09-04-review-pointer-wiring-polish.md` prescribes replacements whose old-strings no longer exist (its Step 3.3 gate item 4 edit targets `is recorded as returned-for-ask, not backlogged.`, but the current item 4 reads `is recorded as returned-for-ask per review-staging's receiving-review consumer row, not backlogged.`), and executing its Task 2 probes would collapse the newer review-staging pointer wiring back to a `Backlog capture` pointer. **After (this plan):** the sibling plan carries an execution-gate note naming the superseded spans and requiring a fresh re-deriving review round before execution.

**Example (live residual, happy path):** in a non-interactive execute-plan run today, the `receiving-review` Fix-risk closing lets the top-level loop agent apply the stop for user direction for ANY held ask, while the sibling parenthetical in the same paragraph says a discharged non-blocking ask needs no return. **Before (today):** the two halves of one sentence disagree on which ask stops. **After (this plan):** the stop branch is scoped to a must-stay-blocking ask, matching gate item 6.

**Example (single source per UL 304):** `review-loop` currently restates the full interactive/non-interactive discharge split twice in unlinked prose (its exit paragraph and orchestration rule 4). **After (this plan):** both become pointers at gate item 6 keeping only the pinned invariant spans ("the loop may not exit while a returned-for-ask presentation is outstanding"; "a must-stay-blocking ask is never discharged by recording and never reaches exit"; "the loop never increments its round with the ask outstanding").

Edge cases motivating the design: the record-element rename (marker + rationale + question) must not change any gate's semantics, only naming; the reconciliation-precedence dedup keeps each row's row-specific consequences and removes only the generic "runs first" clause; the Address Review template gains an interactivity slot with an `unknown` default that fails closed toward returning the question to the orchestrator.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: no semantic change to the discharge split, blocking re-evaluation, or triage counts; every new pointer cites a span that exists (Step 3.3 verification gate item 6; review-staging consumer row).
- Drift hygiene (UL 304): the discharge split is canonically owned by `execute-plan` Step 3.3 verification gate item 6 and this plan introduces no new full restatement: Task 4 replaces `review-loop`'s two restatements (exit paragraph and orchestration rule 4's split sentence) with pointers plus compact summaries, and Task 2's rewrite preserves the pre-existing `receiving-review` statement rather than adding a second copy. The record shape is fully stated once (review-staging consumer row); reconciliation precedence is stated exactly once per file (`execute-plan`: the Step 3.5 ordering sentence; `review-loop`: orchestration rule 5).
- Validation strength: the Validation Commands block is fail-closed, every check is RED-today against the pre-edit tree (evidence recorded in Task 7), and positive pins quote distinctive multi-word spans from the prescribed text.

**Done when:**
- The full Validation Commands block exits 0 on the post-edit tree.
- `bash -n` over the Validation Commands block passes and the pin-vs-prescription audit finds every pinned span exactly once in the prescribed task text.
- The public hygiene scan (from user facts `public_hygiene_scan_script`) exits 0.
- The pinned invariant spans that hold today still hold (characterization pins in Task 7).

**Ship when:**
- Downstream review loops and execute-plan runs consume the aligned wording; no deployment or cross-team condition applies.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill instruction files):**
- `agents/skills/receiving-review/SKILL.md` (Fix-risk closing paragraph only; all other sections frozen)
- `agents/skills/execute-plan/SKILL.md` (Step 3.3 verification gate item 6, the Step 3.3 Address-Review launch line, and Step 3.5 rows/intro only; all other steps frozen)
- `agents/skills/review-loop/SKILL.md` (exit-criteria "Before reporting loop exit" paragraph and orchestration rule 4's returned-for-ask sentence only; all other sections frozen)
- `agents/skills/review-staging/SKILL.md` (the receiving-review consumer row only; all other rows frozen)
- `agents/skills/execute-plan/subagent-prompts.md` (Address Review template only; all other templates frozen)

**Docs:**
- `docs/plans/completed/2026-09-04-returned-for-ask-semantics.md` *(append-only archive note; body frozen)*
- `docs/plans/2026-09-04-review-pointer-wiring-polish.md` *(execution-gate annotation; tasks and probes frozen)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py` and all other scripts; reason: no task changes executable code.
- `docs/plans/completed/2026-09-04-returned-for-ask-semantics.md` body and the sibling plan's Task text; reason: frozen historical record per the archive-note approach (assumption 4).
- `projects/.ai-playbook/development_lessons.md`; reason: no new lesson is captured by this plan (UL 304 already codifies the principle applied here).

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from the repo root. Fail-closed: every check aborts non-zero on miss or forbidden match.
set -u
fail() { echo "FAIL: $1"; exit 1; }

for f in \
  agents/skills/receiving-review/SKILL.md \
  agents/skills/execute-plan/SKILL.md \
  agents/skills/review-loop/SKILL.md \
  agents/skills/review-staging/SKILL.md \
  agents/skills/execute-plan/subagent-prompts.md \
  docs/plans/completed/2026-09-04-returned-for-ask-semantics.md \
  docs/plans/2026-09-04-review-pointer-wiring-polish.md; do
  test -f "$f" || fail "missing $f"
done

# T1: archive note records the superseded spans; sibling carries the execution gate.
grep -qF '## Archive note (drift record, 2026-09-08)' docs/plans/completed/2026-09-04-returned-for-ask-semantics.md \
  || fail "archive note missing"
grep -qF '## Execution gate' docs/plans/2026-09-04-review-pointer-wiring-polish.md \
  || fail "sibling execution gate missing"
# Invariant (GREEN-today): the newer review-staging wiring survives untouched.
grep -qF "review-staging's receiving-review consumer row" agents/skills/execute-plan/SKILL.md \
  || fail "review-staging pointer wiring lost from execute-plan"

# T2: receiving-review Fix-risk closing (R1 scope + R3 split).
grep -qF 'only a must-stay-blocking ask held by the top-level loop agent of a non-interactive run applies the stop' \
  agents/skills/receiving-review/SKILL.md || fail "R1 scoped stop branch missing"
grep -qF '**Presentation and discharge.**' agents/skills/receiving-review/SKILL.md \
  || fail "R3 rule 1 heading missing"
grep -qF '**Return when the executing agent lacks direct user access.**' agents/skills/receiving-review/SKILL.md \
  || fail "R3 rule 2 heading missing"
grep -qF '**Blocking re-evaluation and fix material.**' agents/skills/receiving-review/SKILL.md \
  || fail "R3 rule 3 heading missing"
FLAT="$(tr '\n' ' ' < agents/skills/receiving-review/SKILL.md | tr -s ' ')"
case "$FLAT" in
  *"or, when it is the top-level loop agent of a non-interactive run, it applies the stop"*)
    fail "R1: unscoped stop branch still present" ;;
  *) : ;;
esac

# T3: execute-plan gate item 6 + Step 3.5 (R7 deference, R7 precedence, R4 stop class, R2 row pointer).
case "$(tr '\n' ' ' < agents/skills/execute-plan/SKILL.md | tr -s ' ')" in
  *"per the Fix-ris[k] section:"*) fail "R7: gate item 6 deference still present" ;;
  *) : ;;
esac
grep -qF 'A non-interactive run discharges it: for a non-blocking ask' agents/skills/execute-plan/SKILL.md \
  || fail "R7: gate item 6 non-interactive leg not rewritten"
grep -qF 'the returned-for-ask record (marker, fix-risk rationale, question to relay) per review-staging' \
  agents/skills/execute-plan/SKILL.md || fail "R6: gate item 6 record naming not aligned"
grep -qF 'and any failure, timeout, or interrupt stop' agents/skills/execute-plan/SKILL.md \
  || fail "R4: stop-class enumeration not extended"
grep -qF 'review-reconciliation runs first; each row states only its row-specific consequences' \
  agents/skills/execute-plan/SKILL.md || fail "R7: canonical precedence sentence missing"
N_RUNS_FIRST="$(grep -c 'runs first' agents/skills/execute-plan/SKILL.md)"
test "$N_RUNS_FIRST" -eq 1 || fail "R7: expected exactly 1 'runs first' in execute-plan, got $N_RUNS_FIRST"
grep -qF 'the discharge split is canonical at Step 3.3 verification gate item 6' agents/skills/execute-plan/SKILL.md \
  || fail "R2: Step 3.5 row pointer missing"

# T4: review-loop exit paragraph points at gate item 6 (R2).
grep -qF 'both under the discharge split defined by `execute-plan` Step 3.3 verification gate item 6' \
  agents/skills/review-loop/SKILL.md || fail "R2: review-loop exit pointer missing"
# Invariant pins (GREEN-today): the load-bearing spans survive the pointer treatment.
grep -qF 'a must-stay-blocking ask is never discharged by recording and never reaches exit' \
  agents/skills/review-loop/SKILL.md || fail "invariant lost: blocking ask never reaches exit"
grep -qF 'the loop may not exit while a returned-for-ask presentation is outstanding' \
  agents/skills/review-loop/SKILL.md || fail "invariant lost: no exit with outstanding ask"
FLAT_RL="$(tr '\n' ' ' < agents/skills/review-loop/SKILL.md | tr -s ' ')"
case "$FLAT_RL" in
  *"an interactive run relays the ask and gets the answer before exit"*)
    fail "R2: review-loop exit restatement still present" ;;
  *) : ;;
esac
case "$FLAT_RL" in
  *"an interactive run relays the ask and gets the answer before the next fold"*)
    fail "R2/UL304: review-loop rule 4 restatement still present" ;;
  *) : ;;
esac
grep -qF "the loop never increments its round with the ask outstanding" \
  agents/skills/review-loop/SKILL.md || fail "invariant lost: no round increment with ask outstanding"

# T5: record-element naming owned by review-staging (R6).
grep -qF 'consisting of the literal marker `returned-for-ask`, the fix-risk rationale, and the question to relay' \
  agents/skills/review-staging/SKILL.md || fail "R6: record definition not expanded"
grep -qF '(with the question to relay)' agents/skills/review-staging/SKILL.md \
  && fail "R6: old parenthetical record form still in review-staging"
for f in agents/skills/receiving-review/SKILL.md agents/skills/execute-plan/SKILL.md; do
  FLAT_F="$(tr '\n' ' ' < "$f" | tr -s ' ')"
  case "$FLAT_F" in
    *"recording the fix-risk rationale and returned-for-ask marker"*)
      fail "R6: old record naming still in $f" ;;
    *) : ;;
  esac
done

# T6: Address Review template carries the interactivity input (R5).
grep -qF 'RUN_IS_INTERACTIVE' agents/skills/execute-plan/subagent-prompts.md \
  || fail "R5: interactivity slot missing from Address Review template"
grep -qF 'return the recorded question to the orchestrator rather than performing' \
  agents/skills/execute-plan/subagent-prompts.md || fail "R5: unknown-interactivity default missing"
grep -qF 'Convey the top-level run'"'"'s interactivity in the template' agents/skills/execute-plan/SKILL.md \
  || fail "R5: orchestrator launch line does not convey interactivity"

echo "ALL VALIDATION CHECKS PASS"
```

### Task 1: Archive note and sibling execution gate (backlog item 1)

Files:
- `docs/plans/completed/2026-09-04-returned-for-ask-semantics.md`
- `docs/plans/2026-09-04-review-pointer-wiring-polish.md`

- [ ] Append to the end of `docs/plans/completed/2026-09-04-returned-for-ask-semantics.md` an `## Archive note (drift record, 2026-09-08)` section stating: the Terms definition of **outstanding presentation**, Gist item 3, and Task 3's first two checkboxes predate the r1/r2 review fix rounds; the shipped skill text governs; a non-blocking ask is discharged by recording (recording IS the discharge per `execute-plan` Step 3.3 verification gate item 6), relaying and surfacing are separate exit-report obligations, and only a must-stay-blocking ask stops for direction. Name each of the four superseded spans (Terms bullet, Gist item 3, Task 3 checkbox 1 "the Step 3.5 counter update waits for the answer", Task 3 checkbox 2 blanket stop sentence) and state that the authoring-time validation pins are substrings of both variants so the drift was invisible to them; the body stays a frozen historical record.
- [ ] Insert immediately after the header lines of `docs/plans/2026-09-04-review-pointer-wiring-polish.md` (directly before its `## Terms` heading) an `## Execution gate (superseded prescriptions, 2026-09-08)` section stating: the Task text and probes predate the returned-for-ask r1/r2 wiring (main e754d33); the Step 3.3 gate item 4 replacement targets an old-string that no longer exists (today's item 4 ends `is recorded as returned-for-ask per review-staging's receiving-review consumer row, not backlogged.`), the subagent-prompts step 7 parenthetical it deletes now carries the review-staging pointer, and executing as authored would regress that wiring; do not execute as authored: first run a fresh `review-plan` round that re-derives the prescriptions against the current tree, or amend the Task text in a re-certifying pass.
- [ ] Commit: `docs: record returned-for-ask plan drift and gate sibling plan`

### Task 2: receiving-review Fix-risk closing (R1 scope, R3 split, R6 naming)

Files:
- `agents/skills/receiving-review/SKILL.md`

- [ ] Replace the single ~350-word paragraph beginning `This section also bounds the **Triage Decision Rule**:` with a lead-in line `This section also bounds the **Triage Decision Rule**:` followed by three named numbered rules preserving every existing obligation, in this order:
  1. `**Presentation and discharge.**` A Critical, High, or Medium finding moved to backlog under rules 2-3 is presented to the user when the session is interactive; in a non-interactive run, a non-blocking finding held for the fix-risk ask is discharged by recording the returned-for-ask record (marker, fix-risk rationale, question to relay) per review-staging's receiving-review consumer row, after which the loop may continue and the recorded question is surfaced in the loop exit report (the authorized discharge per `execute-plan` Step 3.3 verification gate item 6 and `review-loop` orchestration rule 4; surfaced per `execute-plan` Step 3.5 and `review-loop` exit criteria). A finding that must stay blocking is never discharged by recording and takes the stop for user direction in rule 2. Once the user decides on a surfaced returned-for-ask question after loop exit, the exit report's decision converts the finding through this section's normal rules (backlog item or fix).
  2. `**Return when the executing agent lacks direct user access.**` It does not perform the ask itself: it returns the presentation or stop-for-direction question to its orchestrator (a discharged non-blocking ask needs no return when the top-level run is non-interactive; in an interactive run, return the recorded question to the orchestrator so it can perform the fix-risk ask); only a must-stay-blocking ask held by the top-level loop agent of a non-interactive run applies the stop for user direction (rule 3 states when a must-stay-blocking finding is fix material instead). Until answered, the finding stays `pending` and carries the returned-for-ask record per review-staging's receiving-review consumer row.
  3. `**Blocking re-evaluation and fix material.**` A finding with `blocking: true` that triage moves to backlog under rules 2-3 has blocking re-evaluated per review-staging **Severity and ordering** (Triage presentation freeze): apply the severity-calibration **Blocking decision procedure** to the current digest, and flip to `blocking: false` only when leaving the finding unresolved no longer creates concrete risk; a finding that still meets a blocking condition must stay blocking and takes the stop for user direction in rule 2. The Triage outcomes counts change only through the finding's disposition (deferred when backlogged), never through the blocking flag itself. A blocking finding that must stay blocking, including a rule-3 hardening defect, is fix material via the minimal additive change or a user decision, never silent backlog; with neither path available in a non-interactive run, the loop stops for user direction rather than exiting or silently backlogging.
- [ ] Verify no other section of `agents/skills/receiving-review/SKILL.md` repeats the unscoped stop branch or the old record naming (grep that file for `it applies the stop` and `rationale and returned-for-ask marker`; both must return no hits after this task).
- [ ] Commit: `skills: scope receiving-review stop branch to must-stay-blocking asks, split Fix-risk closing into named rules`

### Task 3: execute-plan gate item 6 and Step 3.5 (R7 deference and precedence, R4 stop class, R2 row pointer, R6 naming)

Files:
- `agents/skills/execute-plan/SKILL.md`

- [ ] In Step 3.3 verification gate item 6, delete the deference `per the Fix-risk section:` so the sentence reads `A non-interactive run discharges it: for a non-blocking ask, recording ...`, and rename the record elements: `recording the fix-risk rationale and returned-for-ask marker per review-staging's receiving-review consumer row IS the discharge` becomes `recording the returned-for-ask record (marker, fix-risk rationale, question to relay) per review-staging's receiving-review consumer row IS the discharge`. Everything else in item 6 is unchanged.
- [ ] In Step 3.5, insert one canonical ordering sentence immediately after the paragraph `Update \`manifest.md\` with ...` and before the condition table: `Ordering: where a reconciliation trigger co-occurs with any other direction in the table below (a clean-round continuation, a cap stop, or a fix-risk stop), review-reconciliation runs first; each row states only its row-specific consequences of that ordering.`
- [ ] Trim the duplicated generic precedence clauses, keeping each row's row-specific consequences:
  - Row 1: `where a reconciliation trigger also holds, review-reconciliation runs first, and if it changes the digest or staged artifacts` becomes `where a reconciliation trigger also holds and reconciliation changes the digest or staged artifacts` (the rest of the row, including the standing_continue consequence, is unchanged).
  - Row 2: `where a reconciliation trigger also holds, review-reconciliation runs first, then a short session note` becomes `where a reconciliation trigger also holds, then a short session note (ordering per the sentence above)`; and inside the fix-risk parenthetical, `(their direction is taken whether or not a reconciliation trigger holds, but any such reconciliation still runs first)` becomes `(their direction is taken whether or not a reconciliation trigger holds; ordering per the sentence above)`.
  - Row 3 (the reconciliation row): `where fix-risk stop conditions also hold, take the Fix-risk direction per Hard Gate 23 (any such reconciliation still runs first)` becomes `where fix-risk stop conditions also hold, take the Fix-risk direction per Hard Gate 23 (reconciliation first per the sentence above)`.
  - Row 5 (the Fix-risk stop row) is unchanged.
- [ ] In the relay paragraph beginning `Any stop for user direction from the rows above ...`, extend the stop-class enumeration: `(the cap row, the sixth-panel/escalation row, the Fix-risk stop row, and the re-entry mid-round stop)` becomes `(the cap row, the sixth-panel/escalation row, the Fix-risk stop row, the re-entry mid-round stop, and any failure, timeout, or interrupt stop)`; the trailing `alongside the other ask content and any failure, timeout, or interrupt user ask` stays as written.
- [ ] In the Step 3.5 clean-round row, append to the non-interactive leg's parenthetical: `... (the recording discharged it for a non-blocking ask; not treated as backlogged; the discharge split is canonical at Step 3.3 verification gate item 6)`.
- [ ] Verify after the trims that exactly one `runs first` occurrence remains in this file (the canonical sentence).
- [ ] Commit: `skills: single reconciliation precedence and stop-class enumeration in execute-plan returned-for-ask wiring`

### Task 4: review-loop exit paragraph pointer treatment (R2)

Files:
- `agents/skills/review-loop/SKILL.md`

- [ ] In the `**Before reporting loop exit:**` paragraph, replace the restated split (from `Two separate returned-for-ask obligations apply at exit.` through `... not treated as backlogged).`) with: `Two separate returned-for-ask obligations apply at exit, both under the discharge split defined by \`execute-plan\` Step 3.3 verification gate item 6. First, the loop may not exit while a returned-for-ask presentation is outstanding (undischarged): gate item 6 decides whether an interactive run answers the ask before exit or a non-interactive run discharges a non-blocking ask by recording; a must-stay-blocking ask is never discharged by recording and never reaches exit. Second, any recorded returned-for-ask question that has not yet been surfaced must be surfaced in the exit report (not treated as backlogged).` The surrounding sentences (backlog duty before, relay duty and tally after) are unchanged.
- [ ] In orchestration rule 4, collapse the restated split sentence `A returned-for-ask presentation outstanding takes the discharge/stop split defined by execute-plan Step 3.3 verification gate item 6 and receiving-review's Fix-risk section: an interactive run relays the ask and gets the answer before the next fold or iteration; a non-interactive run discharges a non-blocking ask by recording per review-staging's receiving-review consumer row and stops for direction on a must-stay-blocking ask (the fix-risk stop above; execute-plan Step 3.5 Fix-risk stop row when running under execute-plan); the loop never increments its round with the ask outstanding.` to the compact form `A returned-for-ask presentation outstanding takes the discharge/stop split defined by \`execute-plan\` Step 3.3 verification gate item 6 (and \`receiving-review\`'s Fix-risk section) before the next fold or iteration; the loop never increments its round with the ask outstanding.` (UL 304 compact-summary form; the pinned invariant span survives verbatim).
- [ ] Verify the two pinned invariant spans still hold verbatim after the edit (`the loop may not exit while a returned-for-ask presentation is outstanding`; `a must-stay-blocking ask is never discharged by recording and never reaches exit`).
- [ ] Commit: `skills: review-loop exit cites the canonical discharge split instead of restating it`

### Task 5: review-staging record-element definition (R6)

Files:
- `agents/skills/review-staging/SKILL.md`

- [ ] In the `receiving-review` consumer row, expand the record shape: `record the literal marker \`returned-for-ask\` on the finding's Analysis section (with the question to relay)` becomes `record the returned-for-ask record on the finding's Analysis section, consisting of the literal marker \`returned-for-ask\`, the fix-risk rationale, and the question to relay`. The rest of the row (NOT a Status or Triage value; Status and Triage stay `pending`; Blocking unchanged until the user decides) is unchanged.
- [ ] Verify no other review-staging row restates the record elements with different naming (grep `question to relay`; the only remaining occurrences are this row and, if any, plain prose references that use the same three-element naming).
- [ ] Commit: `skills: review-staging owns the returned-for-ask record element definition`

### Task 6: Address Review interactivity input (R5)

Files:
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/SKILL.md`

- [ ] In the Address Review template, add a line `Top-level run interactivity: <RUN_IS_INTERACTIVE (yes|no|unknown)>` directly below the `Review doc: <REVIEW_DOC_PATH>` line of the Address Review template's header block (the `## Address Review` fenced template; not the same-named line in the Done template), and append to step 7: `If <RUN_IS_INTERACTIVE> is unknown or missing, return the recorded question to the orchestrator rather than performing, answering, or discharging the fix-risk ask yourself.`
- [ ] In `execute-plan/SKILL.md`, on the Step 3.3 launch line that introduces the Address Review template (`Use the **Address Review** template from [subagent-prompts.md](subagent-prompts.md).`), append the sentence: `Convey the top-level run's interactivity in the template's <RUN_IS_INTERACTIVE> slot.`
- [ ] Commit: `skills: convey top-level run interactivity to the address-review sub-agent`

### Task 7: Full validation, RED-today evidence, and certification commit

Files: none new.

- [ ] RED-today baseline (measured at authoring time 2026-09-08 and re-measured after the r1 folds; execution accepts this recorded baseline as the pre-edit evidence and re-measures only if it starts from an older tree): every R1-R7 positive pin fails today and every forbidden sweep fires today on the pre-edit tree (`runs first` matches 3 lines / 4 occurrences in execute-plan with `grep -c`, the count the validation check uses; `per the Fix-risk section:`=1, old stop branch=1, both review-loop restatements=1 each, old record naming=1+1, `(with the question to relay)`=1, archive-note heading=0, execution-gate heading=0, `RUN_IS_INTERACTIVE`=0), and the four GREEN-today invariant pins pass today. After Tasks 1-6 land, re-run the full block and expect exit 0 (`ALL VALIDATION CHECKS PASS`).
- [ ] Land Tasks 1-6, then run the full Validation Commands block; expect exit 0 (`ALL VALIDATION CHECKS PASS`).
- [ ] Run `bash -n` over the Validation Commands block and a pin-vs-prescription audit: extract every pinned span from the block and verify each occurs in the prescribed task text above (checker self-literals inside the block do not count toward the audit, and invariant pins that Task 4's checkboxes quote or prescribe verbatim are audited against the task text, not penalized for appearing on both sides of a replace prescription or in the verify checkbox).
- [ ] Run the public hygiene scan (user facts `public_hygiene_scan_script`); expect exit 0.
- [ ] Commit any remaining validation-block fixes: `test: returned-for-ask drift hygiene validation green`
