- Status: open
Priority: Low
Urgency remark: deferred findings from the r10 focused re-cert of the release-skill plan (backlog-deferral default); plan file was out of the execution run's scope
- Workflow: backlog
- Priority: Low
- Created: 2026-09-27

# Release-skill plan: post-sweep stale citations and lineage nit

Four Low, non-blocking findings from the r10 focused re-cert (docs/reviews/2026-09-27-plan-review-release-skill-r10.md) over docs/history/plans/2026-09-26-release-skill.md, all plan-file-side:

1. Ship-when evidence statement (line 83) cites the three measured PII hit files under the dead `docs/plans/completed/` prefix; live at `docs/history/plans/completed/` with identical names.
2. Assumptions basis (line 41) cites `doc_registry_validator.py` scope as "docs/plans and docs/history"; post-P65-sweep it is docs/history-based. Conclusion holds under both scopes.
3. Plan lineage metadata (lines 6, 19) cites r1-r8 and omits the final r9 round whose folds are present in the bytes.
4. Outcome wording "compare-and-swap push" compresses the design (CAS is the local ref update; the push is a verified plain fast-forward).

Fix at the next plan touch; no execution impact (verified by the r10 worker).

Origin: docs/history/plans/2026-09-26-release-skill.md execution run 2026-09-27.

## Addendum (2026-09-27, Task 2/3 intermediate reviews)

5. (Low, Task-2-rooted) release-authoring.sh: silent `set -e` exits on unguarded commands after lock acquisition (mv, git add, git commit) bypass die()'s stdout lock-exports relay, so the calling shell cannot release the lock on those paths; recovery exists via done-lock status/stale-clean. Candidate fix: EXIT-trap relay of the lock exports post-acquire.
6. (Trivial) SKILL.md Step 2 draft `rm -f` sits after the abort check, so an aborted step leaves `release-draft.*` in TMPDIR (outside the repo tree; harmless).
