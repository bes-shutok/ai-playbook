# Deferred plans

Plans parked by the efficiency/token/simplicity triage (2026-09-11); amended 2026-09-12 when code quality became the fourth driving principle (guidelines section 64): the review-coverage and VRS-correctness plans were revived that day. Files are byte-identical to their certified state (nothing was edited), so their review digests stay valid if a plan is ever revived. Revival = `git mv` back to `docs/history/plans/`, re-verify target spans against the current tree (a drift check is mandatory after any park), and re-run one blind review round before execution.

Deferral rationale lives on each plan's backlog origin (parked with a "Priority: deferred" header in `docs/history/backlog/deferred/`); read that before reviving anything here.

## 2026-09-26 direction triage (standing rule)

The owner directed a simplification pass: skills favor simplicity, and extra blockers caused by excessive security go, while per-project sources of a requirement are respected (the priority-profiles machinery, guidelines rule 68, governs whose principles apply). Six plans and their eight origin items were routed to the rejected archives (`docs/history/plans/rejected/`, `docs/history/backlog/rejected/`) with registry rows: the 2d/2f archived-record wording plans, the straggler wording/pins plan, the returned-for-ask drift-hygiene plan, the execute-plan acceptance-witness plan (superseded by the landed machine-verifiable worker completion-evidence contract), and the check-lesson-scope evasion-classes plan (unwitnessed validator hardening). Rejected plans do not revive from here; revival from `rejected/` is a new owner decision per `docs/history/plans/rejected/README.md`.

Standing rule so these classes are not authored again on this repo: a plan whose edits land only in archived or historical records (completed plans, feature notes, review artifacts); a plan that adds gates, validators, or fail-closed checks to the working process without a witnessed failure; and a plan whose concern a landed contract already covers are rejected at triage, not parked. This is the repo profile (section 64 ordering; `deferred_classes: [formal-hardening, security-hardening]` per rule 68) applied at authoring time, not a new mechanism. Sources from other projects keep their own profiles: review-tooling correctness, personal-fork protection, and public-hygiene leaks are not deferral classes and stay actionable.

The same triage swept the deferred backlog on 2026-09-26: 54 items joined `docs/history/backlog/rejected/`, 4 done-record strays carrying committed conflict markers were removed, and 33 items remain parked under the keep classes. The maintenance skill will re-run this triage periodically (backlog item `2026-09-26-maintenance-deferred-corpus-retriage-lane`).

## What remains here and why

One 2026-09-26 promotion pass moved three certified plans back to `docs/history/plans/` with drift checks green (target spans verified live, bytes untouched so the review digests stay valid): `2026-09-08-run-start-marker-content-hash` (self-serving hygiene leak, top self-serving priority), `2026-09-04-review-doc-digest-scope-fix` (work-project review-tooling correctness), and `2026-09-09-grilling-fork-answer-state-rules` (fork protection). Per the revival protocol above, each still owes its fresh blind review round before execution.

- `2026-09-15-plan-readiness-legacy-verdict-grammar-deletion`: a simplification itself (deletes the legacy Summary verdict fallback); parked only on its external prerequisite, the pre-migration review-round archive sweep (~Oct-Nov 2026). Execution stands down until the corpus converges.
