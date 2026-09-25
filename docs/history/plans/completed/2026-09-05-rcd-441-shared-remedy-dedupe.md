# Plan: review-confluence-doc 4.4.1 shared-remedy dedupe

Backlog origin (scope of record):
- `docs/history/backlog/2026-09-04-reviewconfluence-doc-441-shared-remedy-tail.md`

## Terms

- **Shared remedy tail**: the near-verbatim closing clause duplicated between `review-confluence-doc` 4.4.1 bullet 1 and the `documentation.md` Living-doc gates "Consolidation finding shape" sentence; the two differ only by a replace/replaces inflection.
- **Canonical home**: `agents/skills/review-agents/documentation.md`, its "Living-doc gates" subsection; the one file allowed to carry the consolidation remedy phrasing after this plan.
- **Consolidation finding**: the single staged finding for duplicated normative prose, shaped by the Living-doc gates "Consolidation finding shape" check.
- **Pinned span**: a fixed string this plan's Validation Commands assert occurs exactly once (`expect_span_once`) or zero times (`expect_forbidden_absent`) in its target file.
- **RED-today**: a probe that fails against the current tree and passes only after the task that fixes it lands; the proof is executed at authoring time and recorded below the Validation Commands block.

## Assumptions

- assume `documentation.md` needs no wording change; basis: its "Consolidation finding shape" sentence (line 202) already carries the fuller remedy phrasing, and the backlog item's fix centers on the consumer copy in 4.4.1.
- assume the archived sot-unification plan's pin on the old tail (`docs/plans/completed/2026-09-04-sot-unification-living-docs-and-grill-escalation.md`, validation line pinning `replace peer copies with audience-specific pointers or deltas` against the consumer file) is not a live gate; basis: plan validation blocks run during that plan's execution only, and a repo-wide search finds the exact span pinned by no script; the mentions outside the consumer file are prose only (the backlog item, the archived origin plan, and this plan), while the canonical file carries only the "replaces" inflection.
- assume the deferral constraints recorded in the backlog item ("Why not fixed now": receiving-review fix-risk triage rule 2 plus the sibling-doc-restatement backlog-by-default bound, both scoped to the origin plan's lifetime) are cleared now that the origin plan is archived; basis: the item's own wording.
- assume the replacement bullet must keep the trigger ("same normative workflow or contract rule appears in several sections or child pages") and the action ("stage one consolidation finding"); basis: the bullet is the section's only trigger statement, and bullet 2 already directs the reviewer to the full lens gates.

Scope extensions (grilled): none proposed.

## Gist & Examples

One duplicated sentence, one pointer, one plan.

**Before (today).** A `review-confluence-doc` reviewer reaches section 4.4.1 ("Duplicated normative prose (SOT consolidation)") and reads bullet 1: it tells them to stage one consolidation finding per the Living-doc gates and then restates the remedy inline ("name the canonical owner and replace peer copies with audience-specific pointers or deltas"). That restated clause mirrors, nearly word for word, the closing clause of the "Consolidation finding shape" check in `agents/skills/review-agents/documentation.md` ("names the proposed canonical owner from the documentation hierarchy and replaces peer copies with audience-specific pointers or deltas"). The copies differ only by the replace/replaces inflection, so a future reword of the canonical sentence silently diverges from the consumer copy. The item is a regenerating defect: it was found and deferred in the sot-unification plan's code review rounds r1 through r3 (as F5/F7, then F2, then F3), because fixing it inside that plan would have re-pinned a validation span in a plan about to be archived. The asymmetry that made the drift dangerous: only the consumer copy was pinned vocabulary; the canonical sentence in `documentation.md` had no pin at all.

**After (this plan).** The same reviewer reads a bullet that keeps the trigger and the action and ends at a file-qualified pointer: "When the same normative workflow or contract rule appears in several sections or child pages, stage one consolidation finding per `review-agents/documentation.md` Living-doc gates." The remedy wording now exists exactly once across the two skills, in the canonical home. Bullet 2 ("Full lens gates: `review-agents/documentation.md` (Living-doc gates: authority roles, wire SOT, consolidation finding shape)") is unchanged and keeps pointing at the complete gate set. The validation block in this plan re-pins both sides of the contract: the canonical remedy tail is pinned in `documentation.md` for the first time, the new pointer bullet and the retained bullet-2 pointer are pinned in `review-confluence-doc`, and two negative sweeps prove the restated remedy is gone from `review-confluence-doc`.

**Why no other file changes.** `review-panel-selection.md` already carries a pointer-style sentence ("the living-doc patterns are canonically defined in `documentation.md` Living-doc gates"), so the fan-out rule needs nothing. `documentation.md` already holds the canonical phrasing; editing it would churn a sentence the fix is trying to stabilize. The archived origin plan is history and stays untouched.

**Edge cases.**
- A future editor re-expands bullet 1 with the remedy wording: a negative sweep fails the validation block and names the exact forbidden span.
- A future reword of the canonical sentence in `documentation.md`: the canonical pin fails with a span count of 0, forcing a conscious re-pin in whatever plan makes that change.
- The inflection pair ("replace" versus "replaces") means the forbidden spans cannot accidentally match the canonical sentence; the sweeps are additionally scoped to `review-confluence-doc` only, so the canonical copy can never trip them.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the new bullet 1 text lands verbatim as prescribed in Task 1; every pinned span occurs exactly once in its target file; both negative sweeps report zero occurrences; the whole validation block exits 0 against the post-task tree.
- maintainability (dedupe): the consolidation remedy phrasing ("peer copies with audience-specific pointers or deltas") exists in exactly one skill file after the change.
- review-scope hygiene: no file outside `agents/skills/review-confluence-doc/SKILL.md` is modified by execution; `documentation.md` stays byte-identical.
- mechanical soundness: the Validation Commands block passes `bash -n`, aborts explicitly on every miss or forbidden match, and every probe was executed against the tree at authoring time with the RED-today result recorded.

**Done when:**
- Task 1 is committed and the full Validation Commands block exits 0 against the post-task tree (Task 2).

**Ship when:**
- Nothing external: this is a repo-local skill-prose change with no deploy, cross-team, or human-owned release condition.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-confluence-doc/SKILL.md` (partially in scope: only section "#### 4.4.1 Duplicated normative prose (SOT consolidation)" bullet 1; every other section, bullet, and line in the file is frozen; reject any review finding that touches them)

**Tests:**
- (none; skill-prose change validated by the grep-based probes in this plan's Validation Commands)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-agents/documentation.md`; reason: canonical home, intentionally unchanged and byte-frozen; this plan only pins its existing sentence.
- `agents/skills/review-agents/review-panel-selection.md`; reason: its fan-out sentence already points at the Living-doc gates canonically; no change planned.
- `docs/plans/completed/2026-09-04-sot-unification-living-docs-and-grill-escalation.md`; reason: archived plan, immutable history; its validation pins are not live gates.

## Validation Commands

Sweep scoping note: the negative sweeps below target only `agents/skills/review-confluence-doc/SKILL.md`. This plan file itself quotes the forbidden spans (in Gist and Task 1) as prescribed text, not as stale references; never widen the sweeps to the plan file or the repo. Both helpers flatten newlines before matching, so a wrapped remnant cannot hide from a line-based miss; the target file's bullets are single-line by file style, so the prescribed one-line replacement cannot wrap.

```bash
#!/usr/bin/env bash
set -u
REPO="$(git rev-parse --show-toplevel)" || { echo "FATAL: not inside a git repo"; exit 1; }
cd "$REPO" || exit 1

expect_span_once() { # <file> <fixed-string span pinned from the task prescription>
  local f="$1" s="$2" n
  if ! test -f "$f"; then echo "MISSING FILE: $f"; exit 1; fi
  n="$(tr '\n' ' ' < "$f" | grep -oF -- "$s" | wc -l | tr -d ' ')"
  if [ "$n" -ne 1 ]; then echo "SPAN COUNT $n (want 1) in $f: $s"; exit 1; fi
}

expect_forbidden_absent() { # <file> <fixed-string span that must not appear anywhere in the file>
  local f="$1" s="$2" n
  if ! test -f "$f"; then echo "MISSING FILE: $f"; exit 1; fi
  n="$(tr '\n' ' ' < "$f" | grep -oF -- "$s" | wc -l | tr -d ' ')"
  if [ "$n" -ne 0 ]; then echo "FORBIDDEN SPAN PRESENT (count $n) in $f: $s"; exit 1; fi
}

RCD=agents/skills/review-confluence-doc/SKILL.md
DG=agents/skills/review-agents/documentation.md

# Task 1 pins (consumer copy): new pointer bullet plus retained lens-gates pointer
expect_span_once "$RCD" 'stage one consolidation finding per `review-agents/documentation.md` Living-doc gates'
expect_span_once "$RCD" 'Full lens gates: `review-agents/documentation.md`'

# Canonical-home pin (first pin on the documentation.md remedy tail)
expect_span_once "$DG" 'names the proposed canonical owner from the documentation hierarchy and replaces peer copies with audience-specific pointers or deltas'

# Dedupe negative sweeps (consumer copy only): the restated remedy must be gone
expect_forbidden_absent "$RCD" 'replace peer copies with audience-specific pointers or deltas'
expect_forbidden_absent "$RCD" 'name the canonical owner'

echo "rcd-441-shared-remedy-dedupe: all probes green"
```

Authoring-time RED-today proof (executed 2026-09-05 against the pre-task tree): both forbidden spans occur exactly once in the consumer file (the 4.4.1 bullet, line 126); the new pointer pin occurs zero times there; the canonical pin occurs exactly once in `documentation.md` (line 202, unique). The block therefore exits non-zero today (the first consumer pin misses with SPAN COUNT 0, and both negative sweeps would fire) and flips green only when Task 1 lands.

### Task 1: Point 4.4.1 bullet 1 at the canonical gates

Files:
- `agents/skills/review-confluence-doc/SKILL.md`

- [x] In section "#### 4.4.1 Duplicated normative prose (SOT consolidation)", replace bullet 1 (the single-line bullet beginning `When the same normative workflow or contract rule appears in several sections or child pages`) verbatim with:

```
- When the same normative workflow or contract rule appears in several sections or child pages, stage one consolidation finding per `review-agents/documentation.md` Living-doc gates.
```

- [x] Leave bullet 2 (`Full lens gates: `review-agents/documentation.md` (Living-doc gates: authority roles, wire SOT, consolidation finding shape)`) and every other line of the file unchanged
- [x] Run the Validation Commands block from the repo root → expect GREEN: both consumer pins match exactly once, the canonical pin matches exactly once, both negative sweeps report zero occurrences, exit code 0
- [x] Run the repo's public hygiene scan from the repo root: `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` → expect exit code 0 (mandated before committing skill or instruction changes)
- [x] Commit: `skills: dedupe review-confluence-doc 4.4.1 remedy tail into documentation.md`

### Task 2: Final validation

- [x] Run the full Validation Commands block from the repo root against the post-task tree → expect exit code 0 (no commit; validation only)

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-04-reviewconfluence-doc-441-shared-remedy-tail.md: disposition folded into 2026-09-05-rcd-441-shared-remedy-dedupe.md (2026-09-25); per-item file deleted.
