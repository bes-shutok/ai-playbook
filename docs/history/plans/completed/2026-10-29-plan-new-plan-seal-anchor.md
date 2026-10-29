# Plan: New Plan First Review Seal Anchor

Backlog origin: docs/history/backlog/2026-10-29-review-plan-new-plan-seal-anchor.md
Driving force: code-quality; secondary: simplicity
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-plan-new-plan-seal-anchor-r*.md
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/review-plan-new-plan-seal-anchor.md (session 01a187b9-0f15-73d1-ad77-61ec1831ebcb)

## Terms

- Round-start anchor: the commit and SHA-256 digest naming the exact plan bytes a review round certifies.
- WIP checkpoint: the existing `wip:` commit made on the authoring branch after each plan-file write.
- Round-close seal: the plan-review certification record that binds the reviewed plan bytes to their round-start commit and digest.

## Why

A new plan is untracked when its first review starts, so the round-close seal can name a commit without a blob for the plan. The review verifier correctly refuses that anchor; the authoring and review instructions need to connect the existing plan checkpoint to the first round.

## Gist & Examples

TLDR: connect the existing plan checkpoint to the first review seal, because code quality requires the seal to prove which exact plan bytes were certified.

Before: a plan's first review may name the worktree base even though the plan path is absent from that commit.
After: the authoring flow checkpoints the plan before review, and the seal records that commit and the matching plan digest.
For a later plan edit, the authoring flow makes a fresh checkpoint and the next review anchors to those changed bytes.

## Outcome

A newly authored plan can receive its first certification seal using the repository's existing exact-blob verification.

- The first review starts from a checkpoint commit containing the plan's exact reviewed bytes.
- Each later plan edit receives its own checkpoint and a fresh review anchor.
- Existing hard readiness and source-plan verification remain required, with no degraded exact-match certification.

Gate delta: hard gates, refusal classes, fences, protocol layers, schema fields, and dispatch-pausing conditions: none added or removed; review duties: documentation clarifies the existing round-start evidence requirement; no runtime machinery changes.

## Assumptions

- The plan-authoring checkpoint rule already commits each authored plan write as a `wip:` commit on the authoring branch; this is confirmed in `agents/skills/plans/SKILL.md`, Phase 0, Step 0.2.
- `scripts/corrections_record.py` resolves the plan-family anchor by reading the plan blob at `round_start_commit` and hashing those bytes against `round_start_digest`; an absent blob or digest mismatch refuses the anchor.
- Round-close seals continue to require the existing `--hard --source-plan` and plan-readiness gates; degraded exact-match grading is not certification.

Decision points requiring a grill: none remain.

## Standing constraints

- Keep the authoring sequence canonical in `agents/skills/plans/SKILL.md`; `agents/skills/review-plan/SKILL.md` adds only its concise pointer and round-close requirement.
- Follow the skill text anti-growth rule: delete equivalent bytes in each edited skill file to pay for any net growth.
- Do not change validators or add a new record, gate, or ceremony; current authoring checkpoint evidence shows the existing mechanism can supply the plan blob.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each round-start commit contains the plan bytes whose digest the seal records.
- Maintainability: authoring sequence has one home and review-plan points to it without duplicating it.

**Done when:**
- Both skill instructions specify the initial checkpoint, the exact round-start anchor, and a fresh checkpoint and review anchor after every later plan edit.
- The hard source-plan and readiness gates remain explicit, and no validator or machinery is added.

**Ship when:** No external or human-owned release condition.

## Review Scope

**Explicit must-fix:** findings on these documentation paths are always in scope and must be fixed if valid:
- `agents/skills/plans/SKILL.md` (Task 1)
- `agents/skills/review-plan/SKILL.md` (Task 1)

**Production code:** none.

**Tests:** none.

**Plan-related extension:** implementation and review may change files not listed above only when causally required by this plan; otherwise reject as out of scope.

**Out of scope; reject unless plan-related:**
- `scripts/corrections_record.py` and validator behavior; the existing checkpoint rule supplies a plan blob and no implementation change is justified.
- New draft-baseline records, locks, ledgers, gates, or other required ceremony; no incident establishes their need.

## Validation Commands

```bash
set -eu
PLAN=docs/history/plans/2026-10-29-plan-new-plan-seal-anchor.md
DIGEST=$(python3 -c 'import hashlib; print(hashlib.sha256(open("docs/history/plans/2026-10-29-plan-new-plan-seal-anchor.md", "rb").read()).hexdigest())')
SELECTION=$(python3 scripts/review_record_selection.py select --dir .ai-playbook/reviews --slug plan-new-plan-seal-anchor --kind plan-review --source-plan "$PLAN" --source-digest "$DIGEST")
RECORD=$(printf '%s' "$SELECTION" | python3 -c 'import json,sys; print(json.load(sys.stdin)["markdown"])')
python3 scripts/validate_review_staging.py --hard --source-plan "$PLAN" "$RECORD"
python3 scripts/plan_readiness.py "$PLAN"
```

The hard source-plan run must pass without degraded exact-match grading after the final seal is written. Use the origin backlog row's recorded missing-blob `OUTCOME: indeterminate` as the negative witness; do not add a validator or a new test fixture.

### Task 1: Document the exact-byte first-review sequence

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [x] In `agents/skills/plans/SKILL.md`, connect the existing post-write `wip:` checkpoint to review start: before the first review, verify the checkpoint commit contains the plan path and its bytes match the digest used as `round_start_digest`; use that commit as `round_start_commit`. [class: IMPLEMENTATION_REQUIRED]
- [x] In the same authoring instruction, require every later plan-file edit to be followed by a new `wip:` checkpoint, a fresh review round, and a new exact-byte anchor for the changed plan. [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/review-plan/SKILL.md`, require the round-close seal's start commit to resolve the exact plan blob whose bytes match the recorded digest, and point to the canonical authoring sequence in `agents/skills/plans/SKILL.md`. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve `--hard --source-plan`, plan-readiness, and the existing round-close seal contract; degraded exact-match grading does not certify a round. [class: IMPLEMENTATION_REQUIRED]
- [x] Delete equivalent existing text in each edited skill file for any bytes added, and leave validators and machinery unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a first-round checkpoint containing the exact plan bytes, expect the selector-resolved hard source-plan command above to pass without degraded grading; use the origin backlog row's recorded missing-blob `OUTCOME: indeterminate` as the negative witness. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a plan edit after a checkpoint, expect the next review anchor to name the fresh checkpoint and changed-byte digest. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: document new-plan review seal anchor sequence` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

Origin `docs/history/backlog/2026-10-29-review-plan-new-plan-seal-anchor.md` deleted in this landing: its single concern (connecting the authoring checkpoint to the first review seal) is fully covered by Task 1 (landed commit b1b0becd3); no other rows migrated.
