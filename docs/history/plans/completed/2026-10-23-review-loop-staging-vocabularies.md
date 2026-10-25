# Plan: Put Review-Staging's Closed Values in the Dispatch Recipe

Backlog origin: docs/history/backlog/2026-10-10-review-loop-dispatch-closed-vocabulary.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-23-plan-review-review-loop-staging-vocabularies-r*.md
Execution budget: 1h total, largest task 0.5h
Classification: [class: fix-class] documentation repair; authoring only
Authoring claim: docs/tmp/authoring-claims/2026-10-10-review-loop-dispatch-closed-vocabulary.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Closed value:** A value accepted from a finite set enforced by the staging validator.
- **Pattern ID:** A lens-prefixed label used to classify a finding in a review record.
- **Review record:** The Markdown staging document and its matching JSON sidecar for a review round.
- **Sidecar:** The JSON file paired with the Markdown review record; it stores structured round and finding data.
- **Zero-finding round:** A review round with no findings, which still has a required record structure.
- **Triage:** The finding disposition recorded during review, using the validator accepted states.
- **Blast radius:** The size of the area affected by a finding, using the validator accepted values.

## Why

Review workers and sidecar composers have invented values that the existing validator rejects, causing avoidable repair and revalidation. The validator already defines the accepted values, but the worker-facing recipe does not carry them consistently.

## Gist & Examples

TLDR: Carry the validator's closed staging values into review dispatch and composition, reducing review-record rework through code-quality.

**Before:** Worker prompts can omit allowed finding values, the shared calibration guide does not give the confidence values, and zero-finding records can omit severity headings.

**After:** The shared staging contract names the accepted values and required shape; every worker prompt and sidecar composition step carries the current values from the validator.

**Example:** A worker that would otherwise propose `likely` for confidence uses one of `hypothesis`, `strong-evidence`, or `verified`; findings use a blast radius of `global`, `multi-service`, `single-service`, or `local`; a zero-finding round still writes Critical, High, Medium, and Low groups.

**Edge cases:** Keep the four severity groups when they are empty. Refresh prompt values from the validator when its declarations change.

## Outcome

Review rounds have clear, current instructions for producing records that satisfy the existing staging validator on first write.

- Workers receive the accepted finding values and record shape before they start.
- Sidecar composition uses the same values and shape, including for zero-finding rounds.

Gate delta: No new refusal class, hard gate, fence, protocol layer, schema field, or dispatch pause. The added instruction is paid for by the repeated first-write validator refusals recorded in the backlog origin; no validator behavior is changed. No blocking review-layer duty is added.

## Assumptions

- assume the implementation reads the current allowed values from `scripts/validate_review_staging.py` and its schema descriptor; basis: those sources enforce the accepted values, and existing review-staging prose already mirrors some of them.
- assume documentation updates are the simplest viable fix; basis: the validator already catches invalid records, and adding extraction tooling or another enum owner would add maintenance cost without removing the witnessed refusal.
- assume this plan is documentation-only; basis: the origin asks to supply worker guidance, and the observed refusals show the validator is already rejecting invalid values as intended.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: documented and dispatched values match the current validator declarations.
- First-write quality: worker and composition guidance covers confidence, reachability, pattern ownership, triage, blast radius, and all four severity groups.

**Done when:** The review-loop dispatch recipe and shared record guidance carry the validator's current closed values and record shape; a representative staging record and the validator self-test confirm the existing contract still holds.

**Ship when:** None; repository documentation is the complete deliverable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid).

**Production code:** none.

**Documentation:**
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-agents/severity-calibration.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

**Tests:** none forecast; execution selects evidence-based validation from the repository.

**Plan-related extension:** A test, fixture, or adjacent instruction path may be added only when repository evidence shows it is required to verify the three explicit must-fix contracts above.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; reason: its current validation is the source of accepted values and this plan does not change validator behavior.
- `docs/history/backlog/2026-10-10-review-loop-budget-exec-residuals.md`; reason: it is a separate, low-priority formal-hardening sibling.

## Validation Commands

```bash
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-23-review-loop-staging-vocabularies.md
python3 scripts/validate_review_staging.py --selftest || exit
python3 scripts/check_review_agent_portability.py || exit
python3 scripts/test_review_agent_doors.py || exit
REPO_ROOT="$(git rev-parse --show-toplevel)" || exit
(cd "$REPO_ROOT" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh") || exit
```

### Task 1: Put the closed values and record shape in the shared reference

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/review-staging/SKILL.md`
- `agents/skills/review-agents/severity-calibration.md`

- [x] Given a finding with confidence, reachability, pattern ownership, and triage fields, expects the shared record guidance to state the same accepted pattern-owner, reachability, confidence, triage, and blast-radius values as the validator and to keep the validator as their authority. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a finding in the shared severity guide, expects the confidence field to name the accepted values `hypothesis`, `strong-evidence`, and `verified`. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a zero-finding round, expects the staging shape to require Critical, High, Medium, and Low headings even when each group is empty. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect RED: check the current shared instructions against these cases and record the omissions witnessed by the backlog origin. [class: REPOSITORY_TEST]
- [x] Write the minimum documentation changes. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: compare the updated guidance with the validator's current declarations and verify the zero-finding shape. [class: REPOSITORY_TEST]
- [x] Commit: `docs: document review staging closed values` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Carry the shared values into every review-loop dispatch

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-loop/SKILL.md`

- [x] Given review workers are dispatched and the sidecar is composed, expects the worker prompts and sidecar instructions in `doing-code-review` and the loop recipe in `review-loop` to carry the current pattern-owner, reachability, confidence, triage, and blast-radius values and the four required severity groups. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the validator declarations change, expects the prompt and sidecar owners to direct the author to refresh those values from the validator before workers launch, instead of preserving stale prompt copies. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect RED: follow the current dispatch recipe and show that it does not provide at least one value or required group named in this task. [class: REPOSITORY_TEST]
- [x] Write the minimum dispatch-recipe change. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect GREEN: trace the worker-prompt and sidecar-composition instructions and confirm each names the current values and zero-finding shape in both `doing-code-review` and `review-loop`. [class: REPOSITORY_TEST]
- [x] Commit: `docs: include closed values in review dispatch` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-10-review-loop-dispatch-closed-vocabulary.md` (filed 2026-10-10; surface the staging-record closed vocabularies in the review-loop dispatch recipe): implemented by this plan (Tasks 1 and 2); the row was flipped `Status: covered` at authoring, its disposition is folded here, and the file is deleted in this archive commit per the repository's fold-then-delete lifecycle. The one gap the execution's review surfaced (the pattern-owner and triage mirror segments have no vocabulary-equality guard in the validator selftest; a validator change is outside this plan's scope) continues as the open row `docs/history/backlog/2026-10-25-closed-enums-mirror-pattern-owner-triage-unguarded.md`, which also carries the pre-existing `softened-reaffirmed` discard-code drift.
