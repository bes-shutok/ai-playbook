# Backlog: agent-resource-cleanup execution-review residuals (Tasks 1 and 3, plus Phase 3 r1)

- Status: open
- Priority: medium
- Origin class: review residuals (execution run of `docs/history/plans/2026-11-04-agent-resource-cleanup-disposition.md`)
- Dedup probe: `rg -l "agent-resource-cleanup" docs/history/backlog/` (this row is the single residuals home for the run; no sibling row overlaps the items below)
- Cluster: closeout-gate evidence proofs (`scripts/worktree_closeout_migrate.py`)
- Driving force: code-quality (test coverage pinning of landed protective arms)

Origin: intermediate task reviews (Step 1.2b) and the Phase 3 r1 panel of the execution run for `docs/history/plans/2026-11-04-agent-resource-cleanup-disposition.md`; Task rounds verdict backlogged-candidates zero blocking (mutation-probe-backed); Phase 3 r1 carried one blocking finding (quoted-path fail-open, fixed in-run) whose non-blocking siblings are recorded here.

Residuals (1-6 each survive a mutation probe with the suite green):

1. [pattern: quality#unpinned-protective-arm] Low — the "differs at the destination" arm of the recorded-landing blob proof (`scripts/worktree_closeout_migrate.py` recorded-landing scope) is unpinned: no fixture rewrites a recorded-touched path's bytes at the destination, so dropping the differs refusal keeps the suite green and a destination-side rewrite of landed content could authorize deletion.
2. [pattern: quality#unpinned-protective-arm] Low — the tip-tree equality guard (branch moved past its recorded landing) is unpinned: no fixture advances the branch after the recorded landing; dropping the guard lets a stale recorded touched set authorize deletion of post-landing unmerged work.
3. [pattern: quality#unpinned-protective-arm] Low — the legacy-scope recorded-start wiring (`_branch_landing_content_scope` `start_commit` parameter, reached for a record carrying a start commit without full landing identity, including its unresolvable-start retention fallback) is unpinned; a mutation always passing `start_commit=None` survives.
4. [pattern: quality#unpinned-protective-arm] Low — the append fail-closed contract of the authoring-strand identity row (failed append refuses the no-charter pass and keeps the worktree) is unpinned; a mutation demoting the refusal to WARN-and-continue survives.
5. [pattern: quality#append-row-duplication] Nit — re-running the no-charter gate-removal pass against the same worktree appends a second identical identity row to the shared slug-home manifest (append-only, harmless but grows on every re-run).
6. [pattern: documentation#overclaiming-report-line] Nit — for an authoring-strand identity row, a destination history rewrite that un-ancestors the start commit routes the zero-delta branch through the recorded-landing proof with a vacuous blob check and an over-claiming report line ("content is landed by exact tree match"); wording only, no resource-loss risk.

## Task 3 r1 rehearsal-review residuals (same run)

7. [pattern: quality#incomplete-inventory-source-coverage] Minor — the rehearsal's in-scope derivation reads only the run/claim records and manifests; a worktree carrying neither would not be caught as an inventory omission. A worktree-list cross-membership assert would close the seam.
8. [pattern: quality#unexercised-retention-path] Minor — the foreign resource is preserved by end-state asserts and rehearsal restraint, never fed through the gate; an optional strengthening expects the no-manifest retention/unbound path for it.
9. [pattern: quality#redundant-assert] Nit — redundant `len(inventory) == 3` assert after the set-equality assert.

## Phase 3 r1 non-blocking residuals (same run)

10. [pattern: concurrency#unlocked-shared-manifest-writer] Medium — the authoring-strand manifest append is an unlocked writer on the shared read-modify-write slug-home manifest (gate-removal holds no merge lock), so a concurrent migrate run's rows can be lost by last-writer-wins; needs a lock-scope decision before a pinning fixture.
11. [pattern: implementation#legacy-manifest-shadow] Low — the authoring append hardcodes `closeout-migration.json`, so a slug home holding only the legacy `migration-manifest.json` gains a second manifest whose derived-path adjudications can strand an execution worktree's removal (fail-closed, bounded repair via `--migration-manifest`).
12. [pattern: machinery#admission-record-gap] Low — the new fail-closed arms (append-failure refusal, branch-moved-past-start refusal) lack the Machinery admission protocol's expected-catch / false-positive-cost / review-date fields beside the comment that names the incident.
13. [pattern: implementation#mode-bit-delta-invisible] Nit — blob-OID equality makes a chmod-only authored delta invisible to the recorded-landing proof; a deleted ref could lose a mode bit only.
14. [pattern: skill-growth#uncapped-file-growth] Nit (advisory) — `agents/skills/self-heal/SKILL.md` has no byte-budget caps entry and grew ~700 bytes in this run; seed a caps entry before its next growth.

Expected: one focused test-plus-docs plan taking items 1-4 (and the cheap wording/seam items 5-9) RED-before/GREEN-after; items 10-13 need a design decision (lock scope, manifest resolution order, admission fields, tree-mode comparison) before any fix.

## Phase 3 r2 delta-confirmation residuals (same run)

15. [pattern: implementation#quote-delimited-filename-ambiguity] Medium — a real tracked file literally named with first-and-last quote chars (`"q.txt"`) is indistinguishable, after storage, from a legacy C-quoted form of `q.txt`; the unquote pass-through probes the wrong reading and the both-absent-equal arm can authorize deletion when the destination dropped it. Same authorization class as the fixed F1; trigger contrived (no quote-delimited tracked paths observed in this repo's surfaces). Bounded fix shape: when unquote changes the string, probe BOTH readings and retain if either shows a drop. Flagged for operator promotion if quote-delimited filenames are judged realistic.
16. [pattern: implementation#malformed-escape-crash] Low — a malformed quoted hex escape in a manifest entry (`"bad\xZZ.txt"`) raises uncaught ValueError through the proof, degrading a retention verdict into a rc=3 unexpected failure (fail-closed but crash-shaped); fallback to the raw string or unaccounted.
17. [pattern: implementation#non-utf8-transfer-decode] Nit — the `-z` transfer pipe uses strict text decode; on hosts permitting non-UTF-8 filenames (Linux ext4) recording raises UnicodeDecodeError (unreachable on this host; APFS rejects such names). Suggest errors="surrogateescape".
18. [pattern: documentation#unresolved-record-reference] Nit — this row's line 37 reference "see the run's r1 review record" names no path and the origin cites the plan's living path; the landing pass retargets both to the archived homes.

Covers the Phase 3 r1 fixed findings' durable references: F1 quoted-path fail-open fixed in-run (the run's r1 staged review record under `.ai-playbook/reviews/`, archived at landing), docs folds (row shape, conditional Integration-Points wording, title scope) applied in the same fix commit.
