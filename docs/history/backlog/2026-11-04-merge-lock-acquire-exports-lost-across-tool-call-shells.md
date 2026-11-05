# Backlog: merge-lock acquire exports are lost across tool-call shells, stranding a fresh hold until the orphaned arm

- **Filed:** 2026-11-04, investigate over the 2026-11-03 23:14 auth carrier session (its authoring self-landing)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** skill-usage issue capture (session investigate, first witnessed instance)
Class: fix-class
Cluster: docs/history/backlog/2026-11-04-lock-acquire-export-capture-census.md (same mechanism, the acquire-time export-capture discipline; this row owns the merge-landing lock arm, that row owns the family-wide census), docs/history/backlog/2026-11-05-merge-lock-held-after-wait-refusal-lacks-age-deferral-guidance.md (same surface, the merge landing lock; different defect class - that row owns the held-after-wait refusal's age-based deferral guidance, this row owns acquire-to-release capture discipline across tool-call shells)

## Observed versus expected

Observed: the authoring self-landing acquired the merge landing lock in one tool-call shell (`merge-wait-acquire` printing the `MERGE_LOCK_DIR` / `MERGE_LOCK_TOKEN` exports, consumed by an in-shell `eval`) and ran the landing helper in the same call, but the prescribed failure path (release the hold on a landing refusal) fired in a LATER tool-call shell whose environment no longer carried the exports. `merge-release-repo` refused (`OUTCOME: tool_error`, token-fenced from the environment by design), leaving the session's own 85-second-old hold stranded while the rebase remedy ran. Recovery worked exactly per the standing lessons (the orphaned arm with the recorded holder verified dead released the hold), but the recorded holder is the already-exited acquire shell, so a LIVE session's fresh hold always classifies as orphaned under this shape - the verified-dead gate is doing recovery work the capture discipline should have made unnecessary.

Expected: the acquire-time capture discipline surfaces the exports durably at capture time, the way the done lock's Step 0 already prescribes for the project done lock (retain `DONE_LOCK_DIR` plus a token fingerprint in session context): the merge-acquire caller echoes the lock directory and a fingerprint of the token into the session's visible record at acquire time, so a later shell can either re-export from that record or name the orphaned arm knowingly, and the report states which recovery leg ran and why.

## Suspected root area

The maintenance overlay's Merge landing lock bullet (`agents/skills/maintenance/zcode.md`, `agents/skills/maintenance/SKILL.md` runtime copy) and the Worktree-first standard's landing step: one sentence naming the retain-and-fingerprint capture discipline for the merge acquire beside the existing done-lock witness prescription. No lock semantics change: `merge-release-repo` stays token-fenced from the environment, and the orphaned arm stays the verified-dead-gated recovery of record.

## Environment

Playbook repo; witnessed 2026-11-04 in the done-run-setup-stdout-export-emission-split authoring self-landing (one release refusal, one orphaned reclaim, holder pid verified dead at age 85s).

Second witness, 2026-11-04 ~12:20Z, interactive auth session (agent-resource-cleanup-disposition self-landing): acquire and landing ran in one tool-call shell whose exit took the exports; the release fired in a later shell and was recovered by the orphaned arm (holder pid verified dead, token re-exported from the hold's own meta.env, release pass, merge-status free). The meta.env token readability is what made the later-shell release possible without waiting out the stale threshold; the capture-discipline sentence should name that record as the recovery input of record.
