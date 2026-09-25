# Completed-archive fold-then-delete contradiction: six per-item archives violate standing policy

- **Created:** 2026-09-25
- **Priority:** high
- **Status:** open
- **Coverage (substantive):** the resolution's option 1 is already owned by the open plan `docs/plans/2026-09-25-docs-branch-shadow-candidate-inclusion-and-completed-corpus-deletion.md` Task 6 (fold-then-delete of exactly these six items with the registry audit note); do not author a duplicate plan; this item resolves when that plan executes
- **Driving force:** code-quality (queue integrity / corpus self-consistency)

## Finding

The done-sweep residuals execution (squash 997fc30d, plan archived 023e9706) routed its six origins into `docs/history/backlog/completed/` as per-item git-mv archives, as its certified plan bytes specified (Task 5, move-with-mutation). But the corpus's own standing policy forbids exactly that:

- `docs/history/backlog/completed/README.md`: the completed inbox "must stay empty of dated item files. ... Per-item archives are never kept here."
- `agents/skills/plans/SKILL.md` (~lines 31, 718-719, 824): "Do **not** move dated item files into `{backlog_completed_dir}/`" (fold-then-delete instead).
- `agents/skills/execute-plan/SKILL.md` (~line 1010): "Do not `git mv` dated items into `{backlog_completed_dir}/`" — names the exact operation performed.
- `agents/skills/doc-hierarchy/SKILL.md` (~81), `agents/skills/receiving-review/SKILL.md` (~381), `agents/skills/bootstrap-ai-playbook/SKILL.md` (~135): same rule.
- Precedent: executed plan `docs/plans/completed/2026-09-25-backlog-completed-archive-policy.md` (migration 74c05e43) folded and deleted 318 per-item archives on this policy; "The completed inbox keeps only its README stating the empty-inbox policy."

Consequence: the committed tree normatively instructs the opposite of what it contains. Any re-run of the archive-policy migration, or any consumer following the skills, will treat the six files as strays and fold/delete them. An auditor of the done-sweep routing finds it non-compliant with six standing rules. (Same shape existed in the archive-policy-landed `2026-09-22` disposition items filed by peer landings earlier the same day — the six done-sweep routes are the witness set.)

Secondary defects in the same routing (same change set):
- The six archived items retain `Status: open` headers (archived shape elsewhere is `Status: closed` + Disposition line; header-based consumers misread them).
- `docs/history/backlog/completed/2026-09-22-done-parallel-session-isolation.md` Disposition cites the r1-findings origin at its pre-move top-level path (dead reference).
- The r1-findings Disposition cites "the executed plan's r9 Low" in `docs/plans/completed/2026-09-22-done-session-isolation-shared-checkout-ownership.md`, which contains no "r9" label in committed bytes (the round label exists only in gitignored review staging); the verifiable needles are that plan's verify-only sibling-closure lines and commit 181af6cc.

## Suggested resolution (pick one, land it)

1. Fold-then-delete the six (and any other dated per-item archives in `completed/`) onto their covering completed plans as appended disposition sections, exactly as migration 74c05e43 did 318 times; or
2. Reroute them to backlog top level with `Status: closed` headers plus their Disposition lines (check_plan_origins_closed.py accepts Status-closed top-level items); or
3. Keep the moves and amend `completed/README.md` plus the five skill sites with an explicit dated carve-out, with a tracked landing path.

Plus: normalize the archived items' Status headers, and fix the two dead/mis-cited references above.

## Consumer urgency

Scope names shared skills under `agents/skills/` (plans, execute-plan, done routing policy); consumer projects inherit the contradictory instructions.
