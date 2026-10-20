# Backlog: done-run authorized-restoration hardening candidates (exec review r1)

- **Filed:** 2026-10-20 (execution review of docs/history/plans/2026-10-19-done-cached-diff-authorized-reversal.md)
- **Status:** open (candidates 1-3 superseded: fixed by the fix-and-fold round and owned durably by docs/history/backlog/2026-10-20-authorized-restoration-revert-formatting-blob-substitution.md; this row now carries the remaining minor candidates)
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review-minor hardening candidates (non-blocking, no unauthorized-content path)
- **Class:** fix-class
- **Driving force:** reliability (each candidate closes a silent or narrow-failure window on the authorized landing without widening the guard)
- **Skill/step:** `scripts/done_run.sh` authorized landing; `scripts/test_done_run_wrapper.py`

## Candidates

Fixed by the fix-and-fold round (exec review handoff R1/R2/R3/T1/C1 from docs/history/backlog/2026-10-20-authorized-restoration-revert-formatting-blob-substitution.md):

1. ~~Symbolic-target TOCTOU~~ - fixed: last-instant HEAD identity re-check immediately before the ref transaction (`authorized_landing` step 8b) plus the new-OID landed line.
2. ~~`--revert-formatting` neutralization~~ - fixed: tree-capture re-binding (declared-set membership and staged-blob equality re-checked at `authorized_landing` entry) and the empty-staged-set refusal for an authorized invocation whose index emptied.
3. ~~Usage sed range~~ - fixed: `sed -n '2,123p'` tracks the header's true end.

Still open (round-1 minor candidates from both panels, durable capture):

4. **No explicit non-persistence witness in tests.** No test compares the run manifest bytes before/after an authorized landing; a one-line byte-equality witness would pin the promise against drift.
5. **Hook environment parity (F3).** `run_commit_hook` inherits env/stdin; git sets `GIT_INDEX_FILE` and closes stdin for pre-commit. Export `GIT_INDEX_FILE`, redirect stdin from /dev/null.
6. **Marker content revalidation window (F4).** The tuple revalidation re-derives the newest marker by path and the manifest by digest; a mid-hook same-path marker rewrite that still classifies root-confirmed passes. Stash and recompare the marker content digest.
7. **Ledger gap between swap and append (R4).** A crash after the ref swap and before the ledger append leaves a landed-but-unrecorded commit; a re-run's skip arm does not backfill. On the skip arm with `AUTH_PATH` set, append HEAD if absent.
8. **commit-tree message fidelity (R5, cf. the pinned ride-through).** `commit-tree -F` skips git's message cleanup and encoding header; either apply `git stripspace --strip-comments` or record the divergence beside the existing test.
9. **Test-coverage minors (T2-T7).** Unwitnessed arms: `--run-id` mismatch arm (done_run.sh vs test), attached-to-detached transition arm, the tuple-comparison arm never firing in-suite, lock-dir removal/swap (token-sed only), manifest-absent arms, and a tautological assertion near the detached positive test.
10. **Duplication minors (D1-D3).** Newest-marker scan duplicated against `classify_partial`; ledger path derived twice on the authorized path; a third copy of the repo-root digest expression (`repo_root_digest` vs marker write).
11. **Skill landing-mechanism drift (D4/C2).** `agents/skills/done/SKILL.md` Step 3 pins the `git commit ... && git rev-parse HEAD >> ledger` form while the authorized path lands via commit-tree + CAS with its own ledger append; the ladder parenthetical should name the authorized shape.

## Evidence

- `.ai-playbook/reviews/2026-10-20-plan-review-done-cached-diff-authorized-reversal-exec-r1.md` (execution review r1, five-lens pass, zero blocking; candidates 1-3 from the intermediate task review and re-confirmed fresh, candidate 4 recorded as a coverage suggestion).
- `scripts/done_run.sh` `authorized_landing` steps 6-9; the guard lift's blob re-check at the cached-diff stage; `main()` usage range.
- Plan-priced residual: catch frequency low (authorized restoration with stale run, hook index mutation, or branch/run ownership movement), review by 2027-01-19.

## Suggested direction

Land candidates 1-2 as one small hardening change with their refusal witnesses; fix the usage range in the same change; add the manifest byte-equality witness. Keep every refusal pre-ref-update and unrelated-path behavior unchanged.
