# Backlog: lock-acquire export-capture discipline is prescribed per surface only after each field failure

Status: open
Priority: normal
Class: fix-class
Origin class: learn Step 1.9 project-issue capture (2026-11-04 24h session-pattern harvest, window 2026-11-03 07:13 to 2026-11-04 07:13)
Added: 2026-11-04
Cluster: docs/history/backlog/2026-11-04-merge-lock-acquire-exports-lost-across-tool-call-shells.md (same mechanism, the acquire-time export-capture discipline; that row owns the merge-landing lock arm, this row owns the family-wide census), docs/history/backlog/2026-11-04-parallel-execution-landing-serialization-blockers.md (same surface, the merge landing lock; different defect class - that row owns the lock's parallelism-admission scope, this row owns acquire-time export capture), docs/history/backlog/2026-11-05-merge-lock-held-after-wait-refusal-lacks-age-deferral-guidance.md (same surface, the merge landing lock; different defect class - that row owns the held-after-wait refusal's age-based deferral guidance, this row owns acquire-time export capture)

## Observed versus expected

The closeout lock family holds the export-capture discipline as corpus lessons (#35 exports die at the tool-call boundary, #109 lost-capture arm, #261 orphaned-arm recovery, #387 post-release completion, #389 acquire once per generation with a scratch capture) and prescribes it in skill text at exactly one acquire site (the done lock's Step 0 retain-plus-fingerprint prescription). Every other acquire and export-print surface received the discipline only after its own field failure: the merge landing lock stranded a fresh hold in a later shell (the cluster sibling row, first witnessed instance 2026-11-04), the done_run.sh setup acquisition mixed status lines into eval-able stdout until its plan landed (docs/history/plans/2026-11-03-done-run-setup-stdout-export-emission-split.md), and the same emission shape's earlier field failure is lesson #261. Three field failures in four days, each discovered at field-failure time, while lesson 391's probe rule (probe every surface an entry names, never one exemplar) has no family-level application pass.

Expected: one bounded ad-hoc pass enumerates every acquire and export-print surface in the closeout scripts and prescribing paragraphs, runs the measured probe per surface (lesson 391), and converts each to a pinning (characterization) arm or the sibling row's retain-and-fingerprint sentence, so the discipline is verified uniform instead of re-derived per failure.

## Suspected root area

The capture discipline lives in corpus lessons and one skill-site prescription; no surface owns the family-wide enumeration, so each new acquire site re-derives (or omits) the discipline until a field failure forces it.

## Fix shape

One ad-hoc census pass over the candidate surfaces: scripts/done-lock.sh verbs (done lock and merge lock acquire, wait-acquire, release), scripts/done_run.sh setup and lock consumption, scripts/land_squash.sh, scripts/release-authoring.sh, scripts/release-rewrite.sh, scripts/execution_claim.sh lock consumption, plus the prescribing paragraphs (agents/skills/done/SKILL.md Step 0, the maintenance overlay's Merge landing lock bullet and its runtime copy). Per surface: run the measured probe (blocked-run stdout zero bytes, success stdout exactly the export lines, diagnostics on stderr, capture at acquire retained durably), classify compliant (pinning arm) or not (the sibling row's sentence shape), and fold the cluster sibling's merge-lock arm into the same pass. Machinery admission: the pass adds no gate; its gate arm (a landing validator checking capture discipline) is pre-rejected with the missing-incident absence named; sunset when every named surface carries the discipline and the pinning arms are landed.
