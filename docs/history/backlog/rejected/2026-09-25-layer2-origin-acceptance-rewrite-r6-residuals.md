# Backlog: layer2-origin-acceptance-rewrite r6 deferred polish (digest-frozen residuals)

Status: rejected (2026-09-27; digest-frozen non-blocking polish findings on a certified plan)
Priority: low
Workflow: backlog
Date: 2026-09-25

## Context

The plan `2026-09-25-layer2-origin-acceptance-rewrite` certified ready=yes zero blocking at r6 (full five-worker panel over final bytes 74defec4). Nine non-blocking findings were deferred digest-frozen so the certified bytes would not change. This item carries them for the next natural edit of the touched surfaces.

## Deferred findings

1. Task 1 drift check: three origin-item needles (`assertion under the doc-hierarchy verify family`, `**Backlog authors:** when a completed-history item asks`, `rather than inventing per-repo scripts`) lack path operands; run from the repo root they recurse and multi-count against the plan file itself, spuriously aborting execution start. Fix: append the item path, mirroring the `Status: open` needle.
2. Inline code spans embedding the escaped-backtick command (`rc=0; rg -q -F '\`' ...`) render truncated under CommonMark (backslash escapes do not work in code spans); raw bytes and the fenced Validation-block copies are correct. Fix: double-backtick delimiters or point at the block lines.
3. Review Scope's Documentation bullet misattributes the keep-closed disposition to execute-plan's promoted-backlog keep-with-note form; reword to the straggler gate's PASS_STATES basis, widen the tracked follow-up to cover the letter's delete arm, and give the follow-ups a standing carrier (for example an item 4 line in the origin item's Remaining work, adjusting the 8/2 golden numstat and affected gates in the same change).
4. Golden blank-count gate for the origin item: numstat is shape-only, so a balanced two-line corruption (remove an unpinned blank line, add an unpinned content line) certifies green. Fix: pin the amended item's blank-line count.
5. The closed-header no-op basis for the status-blind maintenance survey is prose-only. Consider a mechanical discriminator (survey arm skipping headers in the straggler gate's PASS_STATES, or a recorded skip-reason token convention).
6. Triage taxonomy gap: a peer commit touching `agents/skills/doc-hierarchy-migrate/` in-window is unclassified; add the clause that it re-baselines like an unrelated peer (the invariant is plan-scoped).
7. Probe caveat correction: the witness intersection is line-level (measured), so a drifted dual-recipe copy sharing at least one recipe line still trips; only a fully diverged copy reads clean. Record the correct semantics beside the drift caveat and consider a capture-witness print (per-file column-0 fenced-block counts) for the future hook author.
8. Evaluation Criteria maintainability bullet says "exactly one statement"; the corpus holds one owning statement plus two pre-existing encoded surfaces. Reword to "exactly one owning statement".
9. The equality-gate triage taxonomy appears in full three times (Design Invariant CR, Task 3 scope bullet, Validation preamble); consolidate to one canonical copy with by-reference mentions.

Non-actionable recorded debt: the hygiene line's `$HOME`-ambient scanner dependency is repo-wide standing convention (fail-closed), not this plan's coupling.
