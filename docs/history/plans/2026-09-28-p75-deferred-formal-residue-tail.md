# Plan: Deferred formal residue tail

Backlog origins (scope of record):
- docs/history/backlog/2026-09-26-docs-shadow-execution-residuals.md
- docs/history/backlog/2026-09-20-context-budget-plan-design-residues.md

Driving force: simplicity + code-quality
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-p75-deferred-formal-residue-tail-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The two recorded formal-residue tails land as small, pinned edits: inert text stops riding every dispatched child payload, the documented license path for deleting unregistered registered-history paths is pinned by a test, and the archived plan's stale review pointer tells the truth.

- Child payloads in the maintenance prompt templates no longer carry the scheduler-turn exemption sentence that is inert to the child reading it; the rationale lives in exactly one home (the checkpoint-duty register entries).
- The document-registry validator's licensing story covers the witnessed gap: deleting an unregistered registered-history path has a documented, test-pinned license path (register-and-note) instead of a bare HARD refusal.
- The archived context-budget plan's already-correct review pointer and residual wording are pinned by regression checks, so the origin's recorded deferral closes as discharged-on-disk.
- The remaining docs-shadow residuals (F1, F2, F4) carry recorded dispositions instead of open questions.

## Terms

- Register entries: the standing-duty bullet list at the top of `agents/skills/maintenance/prompt-templates.md` that defines the context-budget checkpoint duty once for both blueprints; the single home of the scheduler-turn exemption rationale.
- Payload bodies: the two dispatched child payloads in the same file (authoring body, execution inner block) that carry the exemption sentence today and must not.
- Register-and-note: the document-registry license flow for an otherwise-immutable write: register the path as a completed-history row carrying a dated `user-approved YYYY-MM-DD:` audit note, then perform the write; `audit_note_valid` enforces the token.
- Built-in selftest: `scripts/doc_registry_validator.py`'s internal named-case suite (`st.expect("test_...", ...)` cases), extended by this plan for the license flow.

## Assumptions

- assume the exemption-sentence deletion is a pure removal from the two payload bodies with no re-home needed, because the register entries at the top of the same file already carry the rationale in two wordings (the authoring entry continues `no checkpoints, because the turn is a fresh short session each cadence`, the execution entry paraphrases `for the same fresh-short-session and final-compaction-step reasons`, sharing the prefix `the scheduler turn itself gets no checkpoints`); basis: disk reads of `agents/skills/maintenance/prompt-templates.md`, 2026-09-28 (register entries at lines 35-36, body sentences at lines 81 and 159).
- assume the register-and-note flow already licenses an unregistered-path deletion today and needs documentation plus a test witness, not matcher changes; basis: the validator's own licensing prose ("audit note in the registry row for the path is the corruption override") and the `audit_note_valid` contract; Task 2 probes the flow first and only widens the matcher if the probe refuses (the origin offers both arms).
- assume the sibling deferral (the archived plan's r6 pointer and must-pass wording) is already discharged on disk: the archived plan's `Plan review:` line already names the r7 artifact with the `(latest, ready` tail, and the residual paragraph carries no `must pass` wording; basis: disk reads of the archived plan, 2026-09-28 (the origin's sibling-deferral paragraph predates the fix); Task 4 verifies and records the discharge instead of editing, keeping the regression pins against a re-introduction.
- assume F1 needs no edit: nothing outside completed history cites docs-branch commit 89261aaa's provenance claim (authoring sweep over tracked surfaces found zero live citations); basis: grep over `agents/`, `projects/.ai-playbook/`, `docs/maintenance/`, and `README.md`, 2026-09-28.
- assume F2 and F4 stay deferred dispositions, not edits: F2's stance-clause fix is reserved for the next extras-copy-semantics touch by the origin's own trigger, and F4's hardening notes are optional notes for future fences; this plan records their dispositions in the landing report instead of touching their reserved surfaces.

Decision points requiring a grill: F3 resolves via the register-and-note license path with matcher widening only on a failed probe (user direction recorded in the origin's fix line offering both arms, with the narrower arm selected under the origin prompt's standing pre-authorization, 2026-09-28; Task 2); the exemption sentence drops from the payload bodies with the rationale single-homed in the register entries (user direction recorded in the design-residues origin's fix paragraph, 2026-09-20; Task 1); the sibling deferral's discharge is verified and recorded rather than re-edited (author verification against the origin's recorded reservation, 2026-09-28: both recorded spots are already correct on disk; Task 4).

## Gist & Examples

TLDR: two recorded residue tails land as pinned edits (inert payload sentence dropped, register-and-note license path documented and test-pinned) plus the archived plan's stale review pointer fixed, for simplicity (removing permanently-dispatched inert text) plus code-quality (the licensing story matches the witnessed failure).

Every scheduler cadence dispatches two child payloads that each carry a sentence explaining an exemption for a session the child neither is nor controls. After Task 1 that sentence exists only in the register entries that define the duty. The docs-registry reconcile that turned six covering-row-licensed deletions into HARD errors gets a documented license path: register the path with a dated audit note first, and a new selftest case proves the flow end to end.

Examples:

- A future reconcile deletes an unregistered completed-history file. Today: a bare HARD with no named remedy. After Task 2: the validator's prose names register-and-note, and the selftest case `test_register_and_note_licenses_unregistered_deletion` demonstrates the exact flow passing `check-writes`.
- The origin's sibling deferral closes without an edit: the archived plan already names r7 (latest, ready) and carries no must-pass wording; the plan's checks pin that state against regression.

## Evaluation Criteria

**Quality dimensions:**

- single-homing: after Task 1 the shared prefix `the scheduler turn itself gets no checkpoints` appears exactly twice (once per register entry) and never in a payload body.
- witness precision: the new selftest case drives the real `check-writes` path on a scratch fixture (unregistered deletion HARD; registered-with-note deletion licensed), not a mocked predicate.
- pin compatibility: the maintenance pins suite (`scripts/check_maintenance_pins.sh`) passes unchanged after the prompt-templates edit; if a pin pins a removed span, that pin is stale by definition and the finding is a blocking plan defect, not an executor judgment call.
- archived-bytes discipline: Task 4 edits nothing; its regression pins guard the already-correct archived bytes against re-introduced staleness.

**Done when:**

- the payload bodies carry no scheduler-turn exemption sentence and the register entries still carry the rationale.
- the validator's licensing prose names register-and-note for unregistered-path deletions and the built-in selftest carries the flow case.
- the archived context-budget plan's review pointer and residual wording are pinned correct (regression checks green).
- the dispositions for F1, F2, and F4 are recorded in the execution landing report.
- the Validation Commands block passes end to end.

**Ship when:**

- the next extras-copy-semantics touch applies F2's stance-clause fix on its reserved surface (human-owned sequencing; recorded disposition, not this plan's checklist).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/maintenance/prompt-templates.md`
- `scripts/doc_registry_validator.py`
- `docs/history/plans/completed/2026-09-19-context-budget-and-telemetry-long-running-skills.md` *(no edit; validation command 4 pins its already-correct state as regression guards)*

**Tests:**

- none as separate files; the flow witness is the built-in selftest inside `scripts/doc_registry_validator.py` (already listed above), extended by Task 2

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- the docs-branch extras copy semantics (F2's reserved surface) and the docs-branch commit provenance (F1: no live citation, disposition only); reason: the origin's own triggers reserve those surfaces for their next planned touch.
- the maintenance skill bodies beyond `prompt-templates.md`; reason: no task touches them.
- the registry data file itself (`docs/maintenance/document-registry.md`); reason: no task adds or edits registry rows; Task 2's fixture rows live in scratch temp fixtures only.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"

# 1. The exemption sentence is gone from the payload bodies and single-homed in the register entries (Task 1).
test -f "$REPO/agents/skills/maintenance/prompt-templates.md" || { echo "FAIL: prompt-templates missing"; exit 1; }
test "$(grep -cF 'The scheduler turn itself gets no checkpoints: the turn is a fresh short session each cadence, and this blueprint' "$REPO/agents/skills/maintenance/prompt-templates.md")" -eq 0 || { echo "FAIL: exemption sentence still in payload bodies"; exit 1; }
test "$(grep -cF 'the scheduler turn itself gets no checkpoints' "$REPO/agents/skills/maintenance/prompt-templates.md")" -eq 2 || { echo "FAIL: register-entry rationale not exactly twice"; exit 1; }

# 2. The maintenance pins suite passes unchanged over the edited templates (Task 1).
( cd "$REPO" && bash scripts/check_maintenance_pins.sh ) || { echo "FAIL: maintenance pins failed"; exit 1; }

# 3. The validator names the license path and its selftest witnesses the flow (Task 2).
grep -qF "register-and-note" "$REPO/scripts/doc_registry_validator.py" || { echo "FAIL: license path unnamed"; exit 1; }
( cd "$REPO" && python3 scripts/doc_registry_validator.py --selftest ) || { echo "FAIL: validator selftest failed"; exit 1; }
grep -qF "test_register_and_note_licenses_unregistered_deletion" "$REPO/scripts/doc_registry_validator.py" || { echo "FAIL: flow case missing"; exit 1; }

# 4. The archived plan's review pointer and residual wording stay correct (regression
# guards; both already hold on today's tree, verified 2026-09-28, so the origin's
# sibling deferral closes as discharged-on-disk rather than re-edited).
grep -qF '2026-09-20-plan-review-context-budget-and-telemetry-long-running-skills-r7.md (latest, ready' "$REPO/docs/history/plans/completed/2026-09-19-context-budget-and-telemetry-long-running-skills.md" || { echo "FAIL: archived header no longer names r7"; exit 1; }
if grep -qF "must pass" "$REPO/docs/history/plans/completed/2026-09-19-context-budget-and-telemetry-long-running-skills.md"; then echo "FAIL: must-pass wording re-introduced in archived plan"; exit 1; fi

# 5. Em-dash cleanliness, scoped to what this plan creates and adds (rule 28). BASE is
# recorded by Task 1's first item before any task commit; the unset guard keeps a
# missing base from silently scanning nothing.
( cd "$REPO" && bash scripts/check-no-em-dash.sh file docs/history/plans/2026-09-28-p75-deferred-formal-residue-tail.md ) || { echo "FAIL: em-dash in plan file"; exit 1; }
test -n "$BASE" || { echo "FAIL: BASE not recorded (Task 1 first item)"; exit 1; }
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base "$BASE" ) || { echo "FAIL: em-dash in added lines"; exit 1; }
```

### Task 1: Drop the inert exemption sentence from the payload bodies

Files:

- `agents/skills/maintenance/prompt-templates.md`

- [ ] Record the base revision for validation command 5 in the run notes: `BASE="$(git rev-parse HEAD)"`, executed before any task commit of this run. [class: REPOSITORY_TEST]
- [ ] In `agents/skills/maintenance/prompt-templates.md`, delete the sentence `The scheduler turn itself gets no checkpoints: the turn is a fresh short session each cadence, and this blueprint's final compaction step keeps payload transcripts short.` from both payload bodies (the authoring body's CONTEXT CHECKPOINTS paragraph and the execution inner block's CONTEXT CHECKPOINTS paragraph; exactly two occurrences today), leaving both paragraphs ending at the threshold-ladder sentence; do not touch the register entries at the top of the file, which keep the rationale (their two wordings differ: the authoring entry continues `no checkpoints, because`, the execution entry paraphrases `for the same fresh-short-session and final-compaction-step reasons`; the shared prefix is what the gate counts). [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: validation commands 1 (sentence gone, rationale exactly twice) and 2 (pins suite unchanged-green) [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: drop the inert scheduler-turn exemption sentence from child payloads` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pin the register-and-note license path for unregistered-path deletions

Files:

- `scripts/doc_registry_validator.py`

- [ ] Probe first: in a scratch temp fixture (a minimal registry file plus an unregistered completed-history file), run `check-writes` against the unregistered path's deletion and record the finding; then add a completed-history row for that path carrying a `user-approved YYYY-MM-DD:` audit note and re-run, recording whether the deletion is now licensed. Teardown the fixture. [class: REPOSITORY_TEST]
- [ ] Either probe arm lands the same two artifacts, so validation command 3 passes under both: extend the validator's module docstring licensing paragraph (the sentence `audit note in the registry row for the path is the corruption override; the note must be removed after the licensed write lands.`) with the register-and-note sentence for unregistered paths (an unregistered path's deletion is licensed by registering it as a completed-history row with the dated audit note first, so the covering-row license has a row to live on), and land the named selftest case. When the probe licenses (expected) the docstring records the existing behavior and the case witnesses it; when the probe refuses, the override matcher is widened for the covering-row-licensed deletion case (the origin's first arm), the same sentence documents the widened behavior, and the same case witnesses the widened flow end to end. Record which arm fired in the run notes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the built-in selftest with the named case `test_register_and_note_licenses_unregistered_deletion`: scratch fixture, unregistered deletion reports the HARD finding, then the registered-with-note row licenses the same deletion; mirrors the existing `st.expect` case style. [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: validation command 3 (license named, selftest green including the new case) [class: REPOSITORY_TEST]
- [ ] Commit: `registry: pin register-and-note as the unregistered-deletion license path` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Record the F1, F2, and F4 dispositions

Files:

- none (record-only task; the dispositions land in the execution run log and the final landing report)

- [ ] Record in the run log: F1, no live citation of docs-branch commit 89261aaa's provenance claim outside completed history (sweep `agents/`, `projects/.ai-playbook/`, `docs/maintenance/`, `README.md`), disposition no-edit; F2, deferred to the next extras-copy-semantics touch per the origin's own trigger; F4, the pipefail-interaction and call-site-context notes recorded as accepted hardening notes for future fences. [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: validation command 5 (both em-dash scans; no bytes changed by this task, the added-lines scan stays clean) [class: REPOSITORY_TEST]

### Task 4: Verify the discharged sibling deferral and run the full block

Files:

- none (verification and record-only task; no bytes change)

- [ ] Verify on disk and record in the run log: the archived context-budget plan's `Plan review:` line names the r7 artifact with the `(latest, ready` tail, and the residual paragraph carries no `must pass` pending-gate wording; the design-residues origin's sibling deferral is therefore discharged-on-disk and closes without an edit (the origin's recorded reservation predates the fix). [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: validation command 4 (both regression guards) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the full Validation Commands block (rule 21 interim expectation: every command passes at this point) [class: REPOSITORY_TEST]
