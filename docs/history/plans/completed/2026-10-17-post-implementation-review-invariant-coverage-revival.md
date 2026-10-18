# Plan: evidence-first post-implementation review correction from the finding-to-review matrix

Backlog origin: none

Driving force: reliability
(the plans-skill closed taxonomy tag; the co-motive is simplicity - the row demands the smallest correction and no new ceremony - recorded here because the taxonomy has no combined entry and the non-principle justification rule requires the motive on record)

Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-post-implementation-review-invariant-coverage-revival-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

Execution budget: 2h total, largest task 1h

## Terms

- Anonymized finding-to-review summary: the preferred operator-provided input artifact: one entry per reported post-implementation finding with its technical substance, owning review stage, reviewed implementation digests, related earlier records, and triage dispositions, stripped of source-project identifiers, code text, reviewer identities, and review-comment quotes; when it is absent, this plan may use user-authorized session-history evidence; without either input, unsupported concerns remain indeterminate under the repository-only fallback.
- Recovered session-history evidence: read-only evidence from a Codex session the user identifies or authorizes, limited to direct links between a finding, its reviewed digest, its stage, and its triage disposition; it supplements a missing anonymized summary without exposing source-project identifiers, code, reviewer identities, or review quotes in tracked files.
- Finding-to-review matrix: the investigation's working table in the run's gitignored record home: when a summary is supplied, one row per reported finding; when authorized session history is used, one row per recovered finding or source-described concern; otherwise, one row per tracked source-described concern. Each row records evidence locators, available and unavailable fields, and a bucket or indeterminate status; if exact finding count or mapping is unsupported, record coverage as indeterminate. The matrix never becomes a tracked artifact type.
- Classification buckets: (a) outside plan-review scope by design, (b) introduced or changed after an execution-review digest, (c) present but missed by the implementation panel, (d) surfaced earlier but underweighted during triage.
- Triage correction: a text-level edit inside the existing disposition or review-pass guidance in doing-code-review/SKILL.md, authorized only by direct bucket-d evidence.
- Consequence retention: the duty added to Step 5 Output under Triage outcomes and the after-triage instruction: a deferred or downgraded finding records its durable-invariant consequence and reopen condition, so a related later finding is dispositioned against that record rather than re-litigated from scratch.
- Deferred-finding recheck: the duty added to Step 4 Assessment Pass opening verification paragraph: when a review touches a path related to a previously deferred finding whose consequence record is reachable, the reviewer re-examines the deferred invariant against current bytes and applies existing finding and blocking criteria before passing the round.
- Vendored twin: the runtime-side path under `~/.agents/skills/` for a touched `agents/skills/` file; when that path resolves through a symlink to the primary checkout, verify byte equality after landing rather than editing a duplicate from a worktree.

## Why

Earlier plan-readiness and execution-review rounds passed, but a later review identified correctness defects and an earlier deferred progress invariant. Read-only session history recovered direct evidence for one earlier deferred progress invariant and a later matching finding. The other three concerns still lack finding-specific links to a reviewed digest, stage, changed path, or triage decision, so their classifications remain indeterminate. The session-derived matrix authorizes only the triage correction for the directly linked invariant; it authorizes no lens edit.

## Gist & Examples

TLDR: a recovered-evidence plan that uses the supplied summary when available and read-only session history when authorized, marks unsupported concerns indeterminate, and carries forward only the directly evidenced triage correction; reliability, because a deferred invariant resurfaced in a later review.

Before: later correctness findings followed earlier review stages, but missing evidence left the responsible gap unclear. After recovery, one deferred invariant is directly linked to a later matching finding and triage decision.

After: the matrix classifies the contiguous-watermark invariant as bucket d and leaves three concerns indeterminate. Only the bucket-d row authorizes existing triage guidance changes; the plan-review boundary, round structure, panel roster, and review-agent lenses stay unchanged.

Edge cases: the three concerns without finding-specific digest and triage links stay indeterminate and cause no edits; the exact number of later findings remains unknown; no source-project identifier, code text, or review quote may enter any tracked artifact.

## Outcome

- The plan-review/implementation-review boundary and all review-agent lenses remain byte-unchanged because no bucket-c miss is demonstrated.
- The existing triage and review-pass guidance gains the consequence-retention and deferred-finding-recheck duties, with the runtime vendored path byte-equal after landing and focused positive and negative samples.
- The matrix stays in the run's gitignored record home; three concerns remain indeterminate, and the exact count of later findings remains unknown.

Gate delta: no gate, panel, round, validator, ledger, or checklist is added or removed; the change is guidance text inside existing triage and review-pass sections plus a post-landing equality check of the runtime symlink (admission: no new blocking surface exists to admit; the origin row's machinery bar - no addition unless the matrix proves the existing final-diff review cannot catch the miss - is carried by Task 3's requirement to cite the bucket-d matrix row).

## Review Scope

- agents/skills/doing-code-review/SKILL.md (the only authorized edit surface); the runtime symlink is a post-landing read-only verification surface
- agents/skills/review-plan/SKILL.md and agents/skills/execute-plan/SKILL.md (implementation-review boundary, unchanged)
- docs/history/plans/completed/2026-10-15-post-implementation-review-invariant-coverage.md (covered origin; read-only)
- docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md (evidence-handoff decision record)
- scripts/check_maintenance_pins.sh, scripts/plan_readiness.py, and scripts/fix_plan_em_dashes.py (consumed validation and plan tools)
- .ai-playbook/reviews/ (gitignored supplemental context; cannot establish classification without direct finding-specific support)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/maintenance-pins-baseline.txt (ignored run artifact; validation input)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/task-3-positive-sample.md (ignored sample record)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/task-3-negative-sample.md (ignored sample record)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/session-evidence-matrix.md (ignored evidence record)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/manifest.md (ignored run and closeout record)
- Read-only Codex session history identified by the user (the recovered evidence locators are in the ignored run matrix)
- scripts/scan-public-hygiene.sh (hygiene surface; consumed, never changed)
- Out of review scope: every review-agent lens, review-loop machinery, review-panel-selection rosters, validators and gates, scheduler state, and the source checkout or remote state
## Assumptions

- the anonymized summary was not present in the prior run's recorded inputs; for this revival the user explicitly authorized read-only recovery from the relevant Codex session history; basis: the current user request and the ignored run matrix.
- assume only the directly demonstrated bucket-d row authorizes an edit; the other three concerns authorize none; basis: the ignored matrix's source locators and the origin's rejection of unsupported corrections.
- assume execution uses a supplied anonymized summary when available and the recovered ignored matrix for this run; if neither provides direct evidence, leave the concern indeterminate; never inspect the source checkout or remote state; basis: the user-directed recovery and the origin's capture-hygiene line.
- assume review-plan/SKILL.md and execute-plan/SKILL.md stay byte-unchanged; basis: the origin's boundary rows and the rejected alternatives.

Decision points requiring a grill: none; the origin pins the no-ceremony boundary and the recovered matrix limits this run to its demonstrated triage gap, so no material design decision is pending before review.

## Tasks

### Task 1: use the authorized evidence input and build the classification matrix
Files:
- docs/history/plans/completed/2026-10-15-post-implementation-review-invariant-coverage.md
- docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md
- scripts/check_maintenance_pins.sh (read-only pre-edit baseline source and consumed validation surface; never changed)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/maintenance-pins-baseline.txt (ignored baseline artifact)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/session-evidence-matrix.md (ignored task output)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/manifest.md (parent-maintained run record)
- .ai-playbook/reviews/ (gitignored supplemental review context; cannot establish incident classification)
Primary class anchors: the completed investigation plan and the current user-directed revival decision

- [x] [class: IMPLEMENTATION_REQUIRED] Check the run's gitignored input home for the anonymized summary. If present, verify one entry per reported finding, required technical substance, stage, digest, related-record, and triage fields, and no identifying or quoted source material. If technical substance or another required field is missing, mark the affected row indeterminate and do not classify it from partial evidence.
- [x] [class: IMPLEMENTATION_REQUIRED] The summary was absent. Use the user-authorized Codex session history as read-only supplemental evidence, and do not inspect the consumer checkout or remote state. Local review artifacts remain supplemental and cannot establish a classification without direct finding-specific support.
- [x] [class: IMPLEMENTATION_REQUIRED] No summary was present, so this conditional rejection path was not triggered; no summary content was copied. If any anonymization check fails, reject the summary without copying its contents into the matrix or tracked files. Record only a generic rejection reason and stop for a sanitized replacement; use session history only when the user authorizes it, otherwise use the repository-only fallback and classify unsupported concerns as indeterminate.
- [x] [class: IMPLEMENTATION_REQUIRED] Inventory separately the source-described concerns: lock-ordering cycle; duplicate range jobs after terminal completion or failure; stale test assumptions about job identity and fixture state; earlier deferred progress invariant. Do not equate this inventory with the exact finding count or mappings unless the summary proves them.
- [x] [class: IMPLEMENTATION_REQUIRED] Build the matrix in the run's gitignored record home. Record four source-described concerns, the recovered finding-to-digest and triage evidence for the contiguous-watermark invariant, and unavailable fields for the other three concerns. The exact later finding count remains indeterminate.
- [x] [class: IMPLEMENTATION_REQUIRED] Assign bucket d only to the contiguous-watermark invariant. The ignored matrix names the execution-review records, follow-up disposition, later PR review thread and comment, and session-local locators.
- [x] [class: IMPLEMENTATION_REQUIRED] Those locators support the same invariant across digests `137b987a0909c8c664f685b5d5456fe9dcc644cc` and `46b697522d934e2c07d969a7de998d55a102ac07`. Keep the other three concerns indeterminate; do not infer their stage, lens, path, or triage class. Indeterminate rows authorize no edit.
- [x] [class: IMPLEMENTATION_REQUIRED] Before any lens or triage edit, run the maintenance-pins command and record its exact output at `docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/maintenance-pins-baseline.txt` in the ignored execution record. This run captured it before the Task 3 edit; it exits 0 with all four pin families holding, plus advisory-only byte-budget notices.
- [x] [class: IMPLEMENTATION_REQUIRED] Keep the already-covered origin closed under the completed 2026-10-15 plan; this follow-up was explicitly revived by the user on 2026-10-17 and does not reopen or duplicate that origin. Record recovered session-history evidence in the ignored matrix and leave the separate delivery-contract handoff item open until the durable summary handoff is resolved.

### Task 2: close lens classification without edits
Files:
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/session-evidence-matrix.md (read-only evidence input)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/manifest.md (parent-maintained run record)
Primary class anchors: the finding-to-review matrix in the ignored run record

- [x] [class: IMPLEMENTATION_REQUIRED] The recovered matrix has no bucket-c row, so it authorizes no lens edit. Record that lock ordering, terminal dedupe, and test-oracle concerns remain indeterminate; the bucket-d watermark row routes only to Task 3.
- [x] [class: REPOSITORY_TEST] No review-agent lens file was changed; therefore no lens pin, lens twin sync, or lens trigger sample applies.

### Task 3: the triage-side consequence and recheck duties
Files:
- agents/skills/doing-code-review/SKILL.md
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/manifest.md (parent-maintained run record)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/session-evidence-matrix.md (read-only evidence input)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/task-3-positive-sample.md
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/task-3-negative-sample.md
Primary class anchors: the triage and disposition sections in agents/skills/doing-code-review/SKILL.md

- [x] [class: IMPLEMENTATION_REQUIRED] For the demonstrated bucket-d row, add consequence retention to the existing Step 5 Output Triage outcomes and after-triage instructions. Add deferred-finding recheck to the opening verification paragraph in Step 4 Assessment Pass. These are the exact existing workflow paragraphs; add no new section or process. Cite the bucket-d matrix row in the change record. Indeterminate rows do not qualify.
- [x] [class: REPOSITORY_TEST] Do not edit a duplicate runtime copy from the worktree; runtime equality is a plan-level Phase 5 closeout gate outside task scope.
- [x] [class: REPOSITORY_TEST] Presence pins when touched: verify the retention and recheck phrases in the canonical skill.
- [x] [class: REPOSITORY_TEST] Positive sample: provide a reachable deferred finding whose invariant is still violated by current bytes, with a recheck result that meets existing blocking criteria; require the review pass to block. The recheck alone does not make a finding blocking.
- [x] [class: REPOSITORY_TEST] In the positive sample, record the durable consequence, reopen condition, violated invariant, expected block disposition, and observed output in the ignored run record; a pass fails this sample.
- [x] [class: REPOSITORY_TEST] Negative sample: with no reachable deferred record, verify that the guidance invents no recheck. Record the sample input, expected output, and observed output in the ignored run record.

### Task 4: preserve boundaries and validate the triage change
Files:
- agents/skills/doing-code-review/SKILL.md
- agents/skills/review-plan/SKILL.md
- agents/skills/execute-plan/SKILL.md
- scripts/check_maintenance_pins.sh
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/maintenance-pins-baseline.txt (ignored comparison artifact)
- scripts/scan-public-hygiene.sh (consumed read-only hygiene check)
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/session-evidence-matrix.md
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/task-3-positive-sample.md
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/task-3-negative-sample.md
- docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/manifest.md (run and closeout record)
- scripts/plan_readiness.py and scripts/fix_plan_em_dashes.py (consumed plan tooling)
Primary class anchors: the implementation-readiness boundary in agents/skills/review-plan/SKILL.md

- [x] [class: REPOSITORY_TEST] Pre-landing boundary-file pin: read the recorded `run_base` from the session manifest, extract its commit after `@`, assign it to `RUN_BASE`, and require the boundary-file command under Validation Commands to exit 0. It compares only review-plan/SKILL.md and execute-plan/SKILL.md with their pre-change bytes; runtime equality is the separate Phase 5 closeout gate.
- [x] [class: REPOSITORY_TEST] After the triage edit, rerun the maintenance-pins command and compare its exact failing set with the ignored baseline artifact listed above. Require equality; investigate any added or removed failure.
- [x] [class: REPOSITORY_TEST] Hygiene: the public-hygiene check listed under Validation Commands exits 0 and the repository no-em-dash scanner reports no new finding in touched files.
- [x] [class: REPOSITORY_TEST] The run record carries the matrix locators, per-concern dispositions, and both sample inputs with expected and observed outcomes; the closeout report names unavailable evidence and remaining conditions.

## Evaluation Criteria

Done when: the recovered matrix records one directly demonstrated bucket-d triage case with stable session and review-record locators and keeps the other three concerns indeterminate. The existing triage guidance is updated and pinned; the runtime vendored path is byte-equal after Phase 5 transfer-out and is checked before worktree cleanup; the sample whose recheck meets existing blocking criteria requires a block, while the no-record sample requires no invented recheck; no review-agent lens changes land; boundary files remain unchanged; and maintenance-pin failures match the captured baseline.
Ship when: all tasks' validation lines pass on the landed tree, the ignored run record names each concern disposition and sample outcome, and after Phase 5 transfers the landed result to the primary checkout, `diff agents/skills/doing-code-review/SKILL.md "$HOME/.agents/skills/doing-code-review/SKILL.md"` exits 0 before worktree cleanup.

## Validation Commands

Validation preamble: the rule-29 pre-round gates run before every review round (`python3 scripts/plan_readiness.py <plan> --pre-round`, outcomes in the round records); the pins command below is compared against the captured pre-change failing set, not a green set.

```bash
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
RUN_BASE=$(sed -n 's/^run_base: .*@//p' docs/tmp/execute-plan/2026-10-15-post-implementation-review-invariant-coverage/manifest.md)
git diff --exit-code "$RUN_BASE" -- agents/skills/review-plan/SKILL.md agents/skills/execute-plan/SKILL.md
diff agents/skills/review-plan/SKILL.md "$HOME/.agents/skills/review-plan/SKILL.md"
diff agents/skills/execute-plan/SKILL.md "$HOME/.agents/skills/execute-plan/SKILL.md"
```

Phase 5 post-transfer closeout, after Phase 5 transfers the landed result to the primary checkout and before worktree cleanup:

```bash
diff agents/skills/doing-code-review/SKILL.md "$HOME/.agents/skills/doing-code-review/SKILL.md"
```

## Out of scope

- No new review round, panel, gate, validator, ledger, checklist, or tracked artifact type; no roster or round-budget change; no review-loop machinery edit.
- No plan-review boundary change: review-plan/SKILL.md and execute-plan/SKILL.md stay byte-unchanged.
- No source checkout or remote inspection: this recovery used read-only Codex session history authorized by the user. No source-project identifier, code text, reviewer identity, or review quote enters a tracked artifact.
- No bucket-a or bucket-b correction: out-of-scope-by-design and post-digest timing evidence are recorded, not patched with guidance.

## Disposition of migrated backlog items

- No backlog origin is promoted by this follow-up. The original origin remains covered by the completed 2026-10-15 plan; the separate 2026-10-17 summary-handoff item remains open.
