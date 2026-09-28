Status: open
Priority: low
Workflow: backlog
Class: doc structure (a vacated numbering gap plus a double indirection where one reference would do)
Driving force: simplicity

# execute-plan Phase 0 carries vacated step numbers (0.2/0.3) and a double transfer-in indirection

**Exact location:** `agents/skills/execute-plan/SKILL.md`, Phase 0 headings (`### Step 0.1: Worktree-first run setup`, then `### Step 0.4: Session bootstrap`, `### Step 0.4b: Stale plan-path checkpoint`, `### Step 0.5` beyond it; no 0.2 or 0.3 headings exist), and Step 0.1's opening sentence, which routes transfer-in through the Step 0.4 paragraph ("transfer the run's gitignored inputs in per the Step 0.4 transfer-in paragraph") that itself routes to the canonical section ("per the canonical section's **Transfer-in implementation**").

## Problem

Two independent structure debts from the consolidation:

1. The heading numbering jumps 0.1 to 0.4. The 0.2/0.3 slots are vacated (the same plan's Task 2 deleted Step 0.3 and earlier consolidation work removed the 0.2 surface) and are referenced nowhere in the skill's live prose (the only corpus hits for "Step 0.3" are the maintenance changelog's historical entries describing the deletion), so a reader cannot tell whether steps are missing or the numbering is intentionally gapped.
2. Step 0.1's transfer-in obligation is stated by indirection to an intermediate paragraph that restates the indirection: Step 0.1 points at the Step 0.4 transfer-in paragraph, which points at the canonical **Transfer-in implementation**. One hop carries the phase-specific literal (the facts transfer-in runs before the Step 0.5 gate); the extra hop adds a name that can drift.

Neither shape breaks a run; both cost reader attention on a hot path (Phase 0 is the first thing every execution runs).

## Observed versus expected

- Observed: Phase 0's headings skip two numbers silently, and Step 0.1 names Step 0.4's paragraph as the transfer-in owner instead of the canonical implementation directly.
- Expected: either the Phase 0 steps are renumbered to a gapless sequence (with any pinned anchors re-keyed in the same change) or the gap is documented once where the numbering starts (for example a one-line note that 0.2/0.3 were removed by the consolidation and the numbers are retired); and Step 0.1 points directly at the canonical **Transfer-in implementation**, keeping only its phase-specific literal.

## Suggested fix

Renumber Phase 0 (0.1, 0.2 session bootstrap, 0.3 stale plan-path checkpoint, 0.5 stays per its downstream references or is renumbered with a grep for its citation sites) or add the one-line gap note; then replace Step 0.1's "per the Step 0.4 transfer-in paragraph" with "per the canonical section's **Transfer-in implementation** (the Step 0.4 paragraph carries the gate-ordering duty)". Re-key any pin or cross-skill reference (plans SKILL.md Phase 0 references, prompt-templates changelog history entries stay as history) in the same edit.

## Source reference

docs/reviews/2026-09-28-worktree-first-standard-only-mode-code-review-r3.md (round 3 address pass; staged finding set item "vacated step numbers"). Capture hygiene: scan-public-hygiene --files pass (rc 0, recorded in the execution log review-r3-receiving-review.log.md). Why not fixed now: renumbering touches headings referenced across skills and the pins suite late in a review loop, a blast radius the narrowly-scoped r3 pass must not open; the pointer dedup alone would still leave the numbering gap undecided (a presentation choice), so both halves ride one backlog item. Severity: Low.

Dedup probe: searched the open backlog corpus (filenames plus Problem bodies) for "Step 0.2", "Step 0.3", "renumber", "vacated": nearest open items are docs/history/backlog/2026-09-28-plans-phase-0-restates-canonical-rationale.md (owns plans-skill Phase 0 restatement, a different file and defect shape) and docs/history/backlog/2026-09-28-lesson-147-stale-step-0-1a-citation.md (owns a stale lesson citation, not the numbering); this item is distinct from both; no merge.

Origin class: self-serving
