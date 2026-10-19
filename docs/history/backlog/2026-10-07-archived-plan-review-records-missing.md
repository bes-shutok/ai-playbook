# archived plan review records missing from the reviews corpus

Driving force: correctness
Date filed: 2026-10-07
Origin: Task 2 done boundary Step 3 item 0d reconstruction duty (execution-claim-write-enforcement run), report-only
Cluster: docs/history/backlog/2026-10-07-corrections-graded-freshness-post-squash.md
Cluster: docs/history/backlog/2026-10-19-fold-commit-staged-record-gap.md (same root area from the other side of the landing boundary: that row's records never surface mid-certification, these went missing after it)

## Finding

Six review records cited by archived plans under docs/history/plans/completed/ are absent from the reviews corpus (and from the docs refs that cite them):

- 2026-09-30 execute-plan-zero-allowed-path-refuse-at-create r3
- 2026-09-30 hygiene-residue-masked-ticket-sweep r2
- 2026-09-30 investigate-cluster-survey-anchored r1
- 2026-09-30 java-review-fqcn-coverage r1
- 2026-09-30 review-staging-sidecar-kind-validation r1
- 2026-10-01 baseline-age-bounded-session-cleanup r1

All are `-plan-review-` records. The reviews home is a gitignored run-artifact surface, so absence is expected after machine transitions, but the citing archived plans present the citations as landed evidence.

## Suggested direction

A corpus reconciliation pass: either restore the records from any surviving source (branch refs, other machines) or annotate the citing archived plans with a dated missing-record note so the citations stop presenting unverifiable evidence.

## Evidence

- Task 2 done run, 2026-10-07, wt-ecwe-exec (commit 327134a7 boundary)
