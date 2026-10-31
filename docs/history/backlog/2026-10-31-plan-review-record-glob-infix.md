Status: open
Priority: low
Class: fix-class
Origin class: review-finding (execute-plan run session-channel-zcode-runtime-derivation-empty, focused plan-review round r5, 2026-10-31)
Cluster: docs/history/backlog/2026-10-31-plan-validation-grep-needles.md (plan-doc evidence pointers without discriminating power)

# Plan review-record header globs omit the run-id infix

Driving force: correctness

Several plan headers cite their review-record series as a literal glob without the producer's run-id infix, so the glob matches zero files on disk: `docs/history/plans/2026-10-30-session-channel-zcode-runtime-derivation-empty.md:4` names `.ai-playbook/reviews/2026-10-30-plan-review-<slug>-r*.md` while the actual records are `-plan-review-<slug>-p5f213296-r1..r4.md`. Sibling plans share the shape (`2026-10-30-session-status-facts-parse-shape-gap.md:5`, `2026-10-28-plan-prompts-stub-writer-forensics.md:6`); newer plans carry the infix. Witness refreshed 2026-10-31 (code-review r1 of the covering execution run): the witness plan's line landed corrected on the run branch (commit 515e98a4b, the run-id-infixed series), so the open scope is the two sibling plans plus the snapshot-exclusion shape below. The readiness gate locates records by slug logic, not the glob, so the defect is informational - a reader following the header pointer finds nothing. Second witness (2026-10-31, plan-review r6 on the same plan): the corrected dateless glob also matches the three `.backup-20261030T*` snapshot files beside the genuine records, so the header citation pulls snapshots alongside records; a house-style pass should settle both the infix and the snapshot-exclusion shape together.

**Ship when:** a house-style pass over plan headers normalizes the remaining cited globs (the two sibling plans) to the run-id-infixed series and settles the snapshot-exclusion shape (the landed infix glob still matches the `.backup-20261030T*` snapshots beside the genuine records), or the plans skill starts accepting dateless globs and resolving the infix itself; the witness plan's line landed corrected (515e98a4b) once its execution completed, so the mid-execution digest-churn concern that parked it here no longer applies to it.
