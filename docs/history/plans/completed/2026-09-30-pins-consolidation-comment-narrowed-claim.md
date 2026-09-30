# Plan: Pins-suite consolidation comment narrowed claim

Backlog origin: docs/history/backlog/2026-09-28-maintenance-pins-consolidation-comment-stale-claim.md
Driving force: code quality
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-pins-consolidation-comment-narrowed-claim-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The comment block above the worktree-first consolidation pin group in `scripts/check_maintenance_pins.sh` states the consolidation's actual transformation - the per-execution worktree paragraphs replaced by references, the per-run pre-work gate paragraph rewritten to post-transfer-in scope and NOT retired - so a future pin author re-keying spans reads ground truth instead of the over-broad retirement claim review round r4 already corrected.

- After this plan, the block's opening sentence carries only the narrowed claim, mirroring the canonical wording the consolidation's own deviation entry carries in `agents/skills/maintenance/prompt-templates.md` ("its per-run pre-work gate paragraph is rewritten to post-transfer-in scope, not retired with it"); the block's per-span detail (S13/S14/S15) already states the accurate per-pin fate and stays byte-untouched.
- Comment-only edit: no pin keys on the comment text, and the suite stays green before and after.

Gate delta: rewords one comment sentence in the pins script; adds no pin, removes no pin, changes no pin's assertion; priced by the propagation risk the origin names - the stale claim is the kind of prose a future pin author reads as ground truth when re-keying spans, and the block's own S15 line already contradicts its opening sentence.

## Terms

- **Consolidation**: the 2026-09-28 worktree-first standard consolidation (plan `docs/history/plans/2026-09-28-worktree-first-standard-only-mode.md` Task 4) that replaced the blueprint worktree paragraphs with references to the Worktree-first standard section in `agents/skills/execute-plan/SKILL.md`.
- **The narrowed claim**: the per-execution worktree paragraphs were replaced by references; the per-run pre-work gate paragraph was rewritten to post-transfer-in scope in the same consolidation, not retired with them; its span pin (S15) is re-keyed on the rewritten gate sentence.
- **The over-broad claim**: the current opening sentence's conjunction, which folds the pre-work gate paragraph into the replaced-with-references set and reads as its retirement.

## Assumptions

- assume the canonical narrowed wording is the consolidation entry's own parenthetical in `agents/skills/maintenance/prompt-templates.md` ("its per-run pre-work gate paragraph is rewritten to post-transfer-in scope, not retired with it"), so the comment mirrors an already-landed surface instead of coining a third phrasing; basis: probed current bytes on 2026-09-30, the entry's line 5.
- assume the block's per-span sentences (S13 freeze-absent fate, S14 drop with its successor-guard naming, S15 re-key on the rewritten gate sentence) are accurate and stay untouched; basis: probed current bytes - the origin's complaint is the opening sentence's conjunction only, and the block's S15 line already contradicts it in the correct direction.
- assume no pin keys on the comment text and the suite is green with the stale comment present; basis: the origin's own verification, re-probed at authoring time (the suite runs in the Validation block).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: one stale comment sentence in the pins suite now matches the transformation the consolidation actually made, removing the wrong-ground-truth hazard for future pin authors - the code-quality force removes a documented misdirection, not a behavior.

**Before (today):** The block opens "the consolidation replaced the blueprint's per-execution worktree paragraph and its per-run pre-work gate paragraph with references ... retiring the P57 payload spans", then its own S15 sentence says the gate span was rewritten and re-keyed - a reader cannot hold both claims at once, and the opening one is false.

**After (this plan):** The opening sentence names the replaced set (the per-execution worktree paragraphs) and states the gate paragraph's distinct fate (rewritten to post-transfer-in scope, re-keyed, not retired) before the per-span list, which then reads as the detail it already was.

## Evaluation Criteria

**Quality dimensions:**

- claim fidelity: the reworded sentence asserts exactly the narrowed claim and no more; the per-span sentences are byte-untouched; the suite's exit code is unchanged (0 before, 0 after).

**Done when:**

- The reworded sentence is present and the over-broad conjunction is absent from `scripts/check_maintenance_pins.sh`.
- `bash scripts/check_maintenance_pins.sh` exits 0.
- The em-dash gate exits 0 on the changed tree, and the hygiene scan named by `public_hygiene_scan_script` in the user facts exits 0.

**Ship when:**

- None; comment prose only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/check_maintenance_pins.sh` (the one comment block only)

**Tests:**

- the pins suite invocation is the regression surface; no separate test file

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- Any pin assertion, count, or helper; the plan rewords comment prose only.
- `agents/skills/maintenance/prompt-templates.md`; byte-pinned and already carrying the canonical wording.

## Validation Commands

```bash
# Task 1: the narrowed claim landed and the over-broad conjunction is gone (RED-today tokens: the new sentence is absent today, the old conjunction present)
grep -qF 'rewritten to post-transfer-in scope in that same consolidation' scripts/check_maintenance_pins.sh || { echo "FAIL: narrowed claim missing"; exit 1; }
if grep -qF 'worktree paragraph and its per-run pre-work gate paragraph with references' scripts/check_maintenance_pins.sh; then echo "FAIL: over-broad conjunction still present"; exit 1; fi

# Task 1: the per-span detail survived byte-untouched (spot anchor)
grep -qF 'S15 is' scripts/check_maintenance_pins.sh || { echo "FAIL: per-span detail altered"; exit 1; }

# Regression: the suite stays green (comment-only edit)
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite"; exit 1; }

# Em-dash gate on the changed tree
bash scripts/check-no-em-dash.sh touched || { echo "FAIL: em dash in changed tree"; exit 1; }
```

### Task 1: Reword the consolidation comment's opening sentence

Files:

- `scripts/check_maintenance_pins.sh`

Evidence:

- The Validation Commands block; covers every Done-when criterion.

- [x] Replace the block's opening clause "The 2026-09-28 consolidation replaced the blueprint's per-execution / # worktree paragraph and its per-run pre-work gate paragraph with references / # to the Worktree-first standard section in the execute-plan skill, retiring / # the P57 payload spans:" with the narrowed form: "The 2026-09-28 consolidation replaced the blueprint's per-execution / # worktree paragraphs with references to the Worktree-first standard section / # in the execute-plan skill; the blueprint's per-run pre-work gate paragraph / # was rewritten to post-transfer-in scope in that same consolidation, not / # retired with them (S15 below is re-keyed on the rewritten gate sentence), / # retiring the P57 payload spans the replacement retired:" - preserving the comment's `# ` prefix and the block's remaining sentences byte-untouched [class: IMPLEMENTATION_REQUIRED]
- [ ] Verify the suite exits 0 after the edit and the changed tree passes the em-dash gate and the hygiene scan named by `public_hygiene_scan_script` in the user facts [class: REPOSITORY_TEST]
