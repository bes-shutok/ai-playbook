# Backlog: the authoring lane starves indefinitely on stale foreign staged log bytes — the operator-gated remedy has no unattended decay arm

- **Filed:** 2026-11-10, interactive operator directive after the 12:47Z auth dispatch stand-down (session sess_2b51c910)
- **Status:** covered (docs/history/plans/completed/2026-11-10-loop-continuity-self-heal.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed availability defect (fifth incident of the class: 2026-11-02, 2026-11-04, 2026-11-07 ×2, 2026-11-10)
- **Class:** fence-class
- **Skill/step:** the `Write boundary rule` in `docs/history/backlog/PLAN-PROMPTS.md` Standing rules (the operator-gated foreign-staged remedy); `scripts/done_run.sh` two-path pre-stage guard; the freeze write consumers (`agents/skills/plans/SKILL.md` Entry freeze, the authoring blueprint's Phase 0)
- **Dedup probe:** searched open rows, plans, and the boundary rule text for `staged residue`, `self-heal`, `set-aside`, `decay`, `foreign staged`; `docs/history/backlog/2026-11-07-rolling-log-freeze-foreign-bytes-setaside-recipe.md` owns the remedy's discoverability and the unstaged-live-delta set-aside arm (its covering plan `docs/history/plans/2026-11-07-rolling-log-write-residue-recovery-recipe.md` is authored, execution pending); `docs/history/backlog/2026-11-04-land-worktree-staged-primary-desync.md` owns the producer-side landing guard; this row owns the missing unattended-decay arm — the freshness vocabulary that ages claims out after one cadence period has no counterpart for index residue
- **Cluster:** the set-aside recipe row above (same residue family, consumer-side recovery recipe); docs/history/backlog/2026-11-10-loop-no-dark-exit-successor-contract.md (same stand-down witness; that row owns the loop-continuity contract, this row owns the block itself)

## Observed versus expected

Observed (2026-11-10 arc): a session staged its `PLAN-PROMPTS.md` dispatch entry at 10:58Z, committed only its backlog rows (`356f55fdb`), and died. The staged hunk sat in the shared primary index for 2h10m. A quota-rich authoring dispatch (12:47Z) picked the first available entry, re-verified availability from disk, and stood down before writing anything: the Phase 0 entry freeze is a primary log write, the runner's two-path pre-stage guard refuses while any staged delta stands, and the `Write boundary rule` remedy is operator-gated without age or liveness qualification — so an unattended session with hours of allowance and no competing work stopped for a dead session's residue. The block was walk-invariant (every entry-keyed authoring run needs the same freeze write). Resolution required the operator's explicit direction (given ~13:15Z); a parallel operator-directed session committed the bytes verbatim (`55d7a3c9c`, recorded staged blob `56f7ef597` pre-staged, then `ed8b174ad` with a peer's staged freeze line) and a second sanctioned transaction verified byte-identity. The authoring lane lost the whole window.

Expected: an unattended session can resolve a STALE foreign staged log hunk autonomously, exactly as it takes over a stale foreign authoring claim: age past a threshold (at least one cadence period, 2 hours, matching the claim-freshness bound) AND no live attribution (no fresh claim, no live worktree or branch naming the residue's content, no live session record) AND blob preservation (record the staged blob sha before, verify the landed blob sha after, name both in the report and the state record). Fresh or attributable bytes keep the operator gate. The remedy stays the sanctioned record → restore-from-index → transaction → verify recipe; the unstaged-live-delta case stays refused until the recovery-recipe plan's arm lands.

## Evidence

- 2026-11-10 10:58Z: rows commit `356f55fdb` landed; the dispatch entry twin stayed staged (blob `56f7ef597` vs HEAD `a1ea91965`).
- 2026-11-10 12:47-12:58Z: the auth dispatch walked the log, picked `review-fold-output-prevalidation`, re-verified availability, and stood down without writing anything at the guaranteed freeze refusal; the stand-down report recorded the operator-gated class (sess_2b51c910).
- 2026-11-10 ~13:15Z: operator direction received; the parallel session's verbatim commit `55d7a3c9c` landed the bytes with the recorded-sha provenance in its message; a second done-locked transaction verified `HEAD:PLAN-PROMPTS.md == ed8b174ad` and correctly found nothing left to commit.
- Prior witnesses: the boundary rule acknowledgment arm's 2026-11-02 incident (autonomous unstage destroyed recoverability — the gate's origin), the 2026-11-04 land-worktree desync row, the set-aside recipe row's two 2026-11-07 witnesses.

## Suggested correction

Add the decay arm to the `Write boundary rule` (its canonical Standing rules home) and mirror the refusal message in `scripts/done_run.sh`: a foreign staged log hunk whose age resolves past the threshold through the recorded attribution checks may be set aside unattended through the existing blob-preserving recipe with both shas recorded; keep the operator gate for fresh or attributable bytes. Machinery admission: this demotes an existing blocker's reach for a bounded, incident-linked class (five witnessed incidents) — a net blocker reduction, not a new gate; the unstaged-delta arm stays owned by the recovery-recipe plan; review date one quarter after landing.
