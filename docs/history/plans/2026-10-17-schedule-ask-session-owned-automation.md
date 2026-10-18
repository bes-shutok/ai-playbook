# Plan: Schedule asks bind satisfaction to the asking session's own automation record

Backlog origin: docs/history/backlog/2026-10-17-schedule-ask-session-owned-automation.md

Grouping entry: docs/history/backlog/PLAN-PROMPTS.md, `## schedule-ask-session-owned-automation` (its Prompt, scope arms, and rejected alternatives are this plan's spec of record)

Driving force: code-quality

Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-schedule-ask-session-owned-automation-p285edaec-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 0.5h total, largest task 0.25h

Disposition (2026-10-18, executed by plan docs/history/plans/2026-10-17-croncreate-cap-delete-own-spawner-leg.md Task 2): this plan's Task 1 was satisfied by that landing, which carried the two declared satisfaction sentences into the AGENTS.md Scheduling asks section verbatim after verifying they were absent on disk (this plan's own landing 06eb1202f had not applied them); do not re-apply Task 1. The remainder of this plan is verify-only.

Authoring claim: docs/tmp/authoring-claims/schedule-ask-session-owned-automation.md (session no-session; pick 1 of 2 of the 2026-10-17 17:0x interactive auth mandate, 2026-10-17)

## Terms

- schedule-at ask: an operator request of the form "schedule at ... to <payload>" naming a future automation.
- scheduling-verb contract: the AGENTS.md "Scheduling asks (verb contract)" section, the single home of the scheduling-ask rules this plan edits.
- satisfaction: the state in which the ask's required scheduling act exists, and the automation id and next fire time reported to the operator are that act's record.
- session-owned record: an automation record the asking session itself created, or its own record that it patched, for this ask.
- foreign record: an automation record, or any other scheduled carrier such as a launchd job, owned by another session or mechanism.
- deconfliction context: information about existing carriers a session reads to avoid duplicate scheduling work; it never substitutes for the ask's own record.
- skip-if-done: payload semantics instructing a fired carrier to re-derive the needed work from disk and skip, and report, the parts a parallel carrier already completed.
- never-executes-inline clause: the existing contract sentence "it never executes the payload in the same turn".
- session-ownership satisfaction clause: the second bullet of Task 1's After block, the landed sentence binding satisfaction to a session-owned record.
- payload-side deconfliction duty: the third bullet of Task 1's After block, the landed sentence carrying deconfliction on the created record.
- runtime overlay: the agents/skills/maintenance/ skill text (zcode.md among it), where the loop's runtime-specific machinery lives.
- reduced-toolset terminal: the overlay's sanctioned park state for a session whose toolset lacks the automation primitives.
- mark-covered rider: the authoring closeout step that flips an origin row's Status to covered with the covering plan as witness, riding the landing commit.
- satisfied by reference: reporting a foreign record's id as an ask's answer without creating or patching a session-owned record.
- sibling dispatch-ladder surface: the runtime overlay's dispatch ladder, cap-refusal handling, delete-own-spawner leg, and launchd fallback, fenced to the sibling entry's plan.
- machinery arm: the rejected alternative that would add a gate or validator refusing a foreign-id report (see Standing constraints).
- span: the file-and-section range a plan or log entry claims as its only editable surface.

## Why

The scheduling-verb contract says what a session must do but never binds the created or patched record to the asking session, so a session holding matching foreign records can report them as the answer and create nothing. The operator corrected exactly this twice in twelve hours on the same surface. Binding satisfaction to a session-owned record puts the ask's accountability and lifecycle on the one session that may update or delete the record.

## Gist & Examples

TLDR: The scheduling-verb contract gains a session-ownership satisfaction clause and a payload-side deconfliction duty, so a foreign record can no longer be reported as an ask's answer, because accountability and lifecycle ride the session that owns the record.

Before: an operator asks a session to "schedule at 11 am"; the session finds another session's automation with similar payload text, creates nothing, and reports the foreign ids as the answer. The operator must correct by hand, and no record the asking session owns carries the ask forward.

After: the same session creates (or patches) its own automation record, reports that record's id and next fire time, and rides re-derive-from-disk and skip-if-done semantics in the created payload so parallel carriers stay duplicate-free; when the create cannot run, the session reports the ask as unscheduled instead of satisfied by reference.

## Outcome

An operator schedule-at ask always ends in a scheduled act the asking session owns, or an honest unscheduled report.

- A session holding matching foreign records still creates its own automation and reports that record's id and next fire time.
- A session whose create remains impossible after its available create paths are exhausted, or whose toolset lacks the create primitive, reports the ask as unscheduled, never satisfied by reference.
- Parallel carriers deconflict through payload semantics on the created record instead of through a create refusal or a foreign-id report.

Gate delta: none

## Assumptions

- The AGENTS.md "Scheduling asks (verb contract)" section is the contract's single operative home; a corpus grep at authoring time finds no second operative copy of the scheduling-verb sentence outside history quotation records (the backlog row and the completed introduction plan quote it), so one section edit lands the clause.
- Named collision, assigned: the runtime overlay currently contradicts the landed clause on two surfaces - its Delivery-channel intent rule sanctions declining to arm by asking the operator when coverage is believed to exist, and its reduced-toolset arms report a launchd or parked carrier for a session that cannot create. This plan's span is the AGENTS.md section only, so it does not reconcile them; the sibling entry's plan (PLAN-PROMPTS `## croncreate-cap-delete-own-spawner-leg`, whose scope arms own the overlay's operator-ordered schedule surface) owns that reconciliation, with this plan's landed clause as its satisfaction-side input.
- Reading of cannot-create, receipt: "cannot create" means the create remains impossible after the session's own available create and remediation paths are exhausted; a first refusal with a live remediation leg is not cannot-create; a reduced toolset with no deletion mechanism is the sanctioned cannot-create case.
- Origin-row disposition, receipt: the origin row's lifecycle closes through the authoring closeout's mark-covered rider (Status: covered with the covering-plan witness), outside Task 1's commit; no task edits or deletes the row.
- The contract section is read by sessions at dispatch time from the guidelines home, so a wording-only change needs no rollout or migration surface.

Decision points requiring a grill: none remain.

## Standing constraints

- Text-only change: no new gate, validator, lock, ledger, or state-schema field; the machinery arm was rejected for want of an admission incident.
- Anti-growth: the operative section gains exactly the two declared sentences; the incident story stays in the origin row, cited here in one line.
- Sibling-span fence: this plan never rewrites the dispatch ladder, the cap-refusal handling, the delete-own-spawner leg, or the launchd fallback; those live in the runtime overlay and the sibling entry's plan.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the landed text makes a foreign record unable to read as satisfaction under both witnessed corrections.
- Minimality: the section grows by exactly two sentences; the never-executes-inline clause is byte-unchanged.
- Containment: every changed byte sits inside the AGENTS.md section; no ladder, cap-refusal, or overlay text moves.

**Done when:**
- The section carries the session-ownership satisfaction clause, the foreign-record deconfliction-context rule, and the payload-side deconfliction duty, in the exact declared wording.
- The Validation Commands block exits 0 end to end.

**Ship when:**
- Nothing external; the contract text is the deliverable: the clause binds sessions whose checkout holds the landed bytes, a worktree branched before the landing reads the prior wording until it rebases, and no migration surface exists for in-flight asks.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `AGENTS.md` (the "Scheduling asks (verb contract)" section only)

**Tests:**
- none (text-only plan; the Validation Commands block is the verification surface)

**Plan-related extension:** implementation and review may change files not listed above when causally related to this plan: a wording correction inside the declared section, or a validation-command fix that keeps the declared checks honest. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-10-17-schedule-ask-session-owned-automation.md`; reason: the origin row's lifecycle is owned by the authoring closeout's mark-covered rider, never by a task edit.
- `agents/skills/maintenance/zcode.md`; reason: dispatch-ladder and cap-refusal text is the sibling entry's span, and the Delivery-channel collision there is assigned to the sibling plan (see Assumptions).
- `agents/skills/maintenance/decisions.md`, `agents/skills/maintenance/guards.md`; reason: loop lane machinery is untouched by a satisfaction-semantics wording change.
- `docs/history/backlog/2026-10-17-croncreate-cap-delete-own-spawner-leg.md`; reason: the sibling origin row belongs to the sibling plan.

## Validation Commands

```bash
S=$(sed -n '/^## Scheduling asks/,/^## Commit/p' AGENTS.md)
occ() { printf '%s\n' "$S" | grep -oF "$1" | wc -l; }
# 1. session-ownership satisfaction clause landed exactly once (fail on miss or duplicate)
test "$(occ 'satisfied only by an automation record the asking session itself created, or its own record that it patched')" -eq 1 \
  || { echo "FAIL: session-ownership satisfaction clause missing or duplicated"; exit 1; }
# 2. foreign-record deconfliction-context rule landed exactly once (fail on miss or duplicate)
test "$(occ 'deconfliction context, never satisfaction')" -eq 1 \
  || { echo "FAIL: foreign-record deconfliction-context rule missing or duplicated"; exit 1; }
# 3. payload-side deconfliction duty landed exactly once (fail on miss or duplicate)
test "$(occ 'skip-if-done, and report, when a parallel carrier already did the work')" -eq 1 \
  || { echo "FAIL: payload-side deconfliction duty missing or duplicated"; exit 1; }
# 4. cannot-create honest-report duty landed exactly once (fail on miss or duplicate)
test "$(occ 'reports the ask as unscheduled, never satisfied by reference')" -eq 1 \
  || { echo "FAIL: cannot-create honest-report duty missing or duplicated"; exit 1; }
# 5. never-executes-inline clause present exactly once, counted by occurrence not line (fail on drift or duplicate)
test "$(occ 'it never executes the payload in the same turn')" -eq 1 \
  || { echo "FAIL: never-executes-inline clause missing or duplicated"; exit 1; }
# 6. bullet 1 pinned whole, framing prefix through the scheduling act (fail on drift or duplicate)
test "$(occ 'A "schedule at ..." ask schedules: create or patch the automation, then report the automation id and its next fire time')" -eq 1 \
  || { echo "FAIL: bullet 1 framing or scheduling-act drift"; exit 1; }
# 7. non-derivable-payload arm pinned (fail on miss or duplicate)
test "$(occ "when the payload's work is not re-derivable from disk, the report names the overlapping carrier and the shared fire time")" -eq 1 \
  || { echo "FAIL: non-derivable-payload arm missing or duplicated"; exit 1; }
# 8. sibling-span fence: no ladder or cap-refusal text inside the section (forbidden match; rc 1 passes, 0 fails, >=2 aborts)
set +e
printf '%s\n' "$S" | grep -Ein 'dispatch ladder|cap-refus|delete-own-spawner|delete-plus-create|pending_rearm|re-arm' >/dev/null
rc=$?
set -e
test "$rc" -eq 1 || { echo "FAIL: forbidden-match sweep rc=$rc (0 = encroachment, >=2 = tool error)"; exit 1; }
echo "schedule-ask contract checks: all pass"
```

### Task 1: Land the two-sentence satisfaction clause in the scheduling-verb contract

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `AGENTS.md`

- [ ] Apply the exact section text below to the AGENTS.md "Scheduling asks (verb contract)" section, appending the two new bullets after the existing bullet and changing nothing else in the file [class: IMPLEMENTATION_REQUIRED]

Before (the whole section, today):

```markdown
## Scheduling asks (verb contract)
- A "schedule at ..." ask schedules: create or patch the automation, then report the automation id and its next fire time; it never executes the payload in the same turn.
```

After (the whole section; the first bullet is byte-identical, the two new bullets are the only growth):

```markdown
## Scheduling asks (verb contract)
- A "schedule at ..." ask schedules: create or patch the automation, then report the automation id and its next fire time; it never executes the payload in the same turn.
- Satisfaction is session-owned: an ask is satisfied only by an automation record the asking session itself created, or its own record that it patched, whose id and next fire time the report carries; an automation record from another session (or any other carrier, such as a launchd job) is deconfliction context, never satisfaction.
- Deconfliction rides the created payload (re-derive from disk; skip-if-done, and report, when a parallel carrier already did the work; when the payload's work is not re-derivable from disk, the report names the overlapping carrier and the shared fire time), never a create refusal, and a session that cannot create after exhausting the scheduling fallback its runtime overlay sanctions reports the ask as unscheduled, never satisfied by reference.
```

- [ ] Commit the section edit as one commit scoped to `AGENTS.md` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Validate both witnessed corrections against the landed text

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `AGENTS.md`

- [ ] Run the Validation Commands block from the repository root; every check passes and the block exits 0, which verifies the satisfaction clause, the deconfliction-context rule, the payload-side duty, the honest-report duty, the once-only never-executes-inline clause, the pinned whole bullet 1, the pinned non-derivable arm, and the sibling-span fence in one run [class: REPOSITORY_TEST]
- [ ] Read the landed section against the witnessed corrections as a first human-readable check: given a session holding a matching foreign record, the text still orders it to create its own record and report that record's id; given a cap-refused session whose runtime overlay sanctions a scheduling fallback, the text orders exhausting that fallback before any unscheduled report [class: REPOSITORY_TEST]
- [ ] Read the landed section against the patch and cannot-create corrections as a second human-readable check: given a session patching a foreign record, the patch never converts the record into satisfaction; given a session whose create remains impossible after its available paths are exhausted, the text orders an unscheduled report, never a foreign-id citation [class: REPOSITORY_TEST]
