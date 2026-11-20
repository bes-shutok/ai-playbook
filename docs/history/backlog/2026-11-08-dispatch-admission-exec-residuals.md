# Backlog: dispatch-admission execution residuals

Status: open
Priority: low
Cluster: docs/history/plans/2026-11-06-dispatch-admission-outstanding-manifest-recovery.md
Driving force: correctness

Origin: the execution run's Phase 3 full-panel review (r1, fresh adversarial, 2026-11-08; record pair `.ai-playbook/reviews/2026-11-08-dispatch-admission-outstanding-manifest-recovery-code-review-r1.md` + sidecar, verdict ready=yes zero blocking); valid non-blocking findings carried here as the durable copy.

Dispositions of the prior certification-residuals row (`2026-11-07-dispatch-admission-plan-certification-residuals.md`, items addressed at this execution): the multi-plan done boundary merges into every owned plan's record (`merge_admission_records_at_done_boundary` iterates `owned_plan_paths`); the sweep clearing gates on the swept claim itself (the record derives beside `$claim_file`, not the sweeping session); the take-failure orphan race is re-confirmed inherent (lockless cleanup cannot exclude a locked party) and stays an accepted residual; the wording nits closed with the landed text (the lockless carve-out is the plan's own stated order guarantee).

Resolve in a follow-up lane (each with its driving force; none blocks):

- Merge arm must refuse a malformed field VALUE (not just an unexpected key) instead of silently normalizing it, mirroring the consult's malformed-evidence refusal (driving force: correctness; review finding 1).
- Single-home the merge-lock identity: derive the lib merge arm's lock root through the gateway's account-home derivation (or warn when ambient `MERGE_LOCK_ROOT`/`HOME` is honored at a record mutation) and give the record writer a unique temp name (driving force: correctness; finding 8).
- Corrupt-record recovery arm or documented operator remedy for an unreadable record beside a live claim, which currently freezes the lane at D3 defer until claim retirement (driving force: efficiency; finding 9).
- Post-Ship-when adoption census: record-operand consults vs source-less consults from scheduler-state decision_reason lines, the feature's only effectiveness signal until a mechanical caller exists (driving force: efficiency; finding 10).
- Compare the merge arm's ownership re-check against the claim's session, not only its branch, so a predecessor's late done boundary cannot inflate a successor's fresh record (driving force: correctness; finding 11).
- Empty-seed warning should distinguish an unreadable covering plan from a genuinely `Files:`-less one (driving force: quality; finding 3).
- Pin the finalize-manifest merge hooks (both call sites) so the boundary's second half is not silently removable (driving force: regression safety; finding 5).
- Pin the conservative arms: the shell-out rc!=0 arm fails the take contradicting the docstring's never-fails claim, record-before-claim ordering, and the remaining warn arms (driving force: regression safety; finding 6).
- Uniform env scrub for the end-to-end gateway pin matching its sibling witness (driving force: testing uniformity; finding 7).
- Bound the sweep's walk-wide abort: one unremovable record stops every later claim's retirement; fix the comment and consider per-claim isolation (driving force: efficiency; finding 12).
- Move the seeding import out of the global merge-lock hold or shrink it (driving force: efficiency; finding 13).
- Update `--outstanding-with-manifest` help text and the execution_claim.sh header block to name the record operand and the replace-policy prior-record removal (driving force: documentation; finding 14).
- Cross-suite equality witnesses for the record-path derivation and the merge-lock meta.env field vocabulary consumed by independent bash and python parsers (driving force: quality; finding 15).
