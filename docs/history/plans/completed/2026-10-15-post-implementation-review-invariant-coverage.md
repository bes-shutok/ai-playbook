# Plan: evidence-first post-implementation review correction from the finding-to-review matrix

Authoring claim: docs/tmp/authoring-claims/2026-10-14-post-implementation-review-invariant-coverage.md (session automation-f1c15500-resume-20261015)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-14-post-implementation-review-invariant-coverage.md

Driving force: reliability
(the plans-skill closed taxonomy tag; the co-motive is simplicity - the row demands the smallest correction and no new ceremony - recorded here because the taxonomy has no combined entry and the non-principle justification rule requires the motive on record)

Plan review record: the staging series .ai-playbook/reviews/2026-10-15-plan-review-post-implementation-review-invariant-coverage-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

Execution budget: 2h total, largest task 1h

## Terms

- Anonymized finding-to-review summary: the preferred operator-provided input artifact: one entry per reported post-implementation finding with its technical substance, owning review stage, reviewed implementation digests, related earlier records, and triage dispositions, stripped of source-project identifiers, code text, reviewer identities, and review-comment quotes; when it is absent, this plan may proceed only through the separately reviewed repository-only fallback.
- Repository-only fallback: the operator-directed, plan-reviewed path for this run when the summary is absent: use only tracked repository evidence, record unsupported stage, digest, path, or triage fields as unavailable, and classify the affected finding as indeterminate without inferring a bucket or changing its lens or triage rules.
- Finding-to-review matrix: the investigation's working table in the run's gitignored record home: when a summary is supplied, one row per reported finding; on the repository-only fallback, one row per source-described concern. Each row records evidence locators, available and unavailable fields, and a bucket or indeterminate status; if exact finding count or mapping is unsupported, record coverage as indeterminate. The matrix never becomes a tracked artifact type.
- Classification buckets: (a) outside plan-review scope by design, (b) introduced or changed after an execution-review digest, (c) present but missed by the implementation panel, (d) surfaced earlier but underweighted during triage.
- Lens sharpening: a text-level edit inside an existing section of the owning review lens, adding or tightening a review duty; the plan's only sanctioned lens-edit class. Candidate lenses are quality, testing, concurrency, and premortem; direct matrix evidence identifies the owner.
- Cross-transaction invariant trace: the sharpened duty that a reviewer follows a changed state transition across its transaction boundary (lock ordering, commit/rollback, worker and merge-lock interleavings) instead of reviewing each hunk locally.
- Test-oracle check: the sharpened duty that a reviewer verifies the changed tests' assumptions against the current persisted representation and fixture state, so a passing suite with stale identity or state assumptions is a finding, not a pass.
- Triage correction: a text-level edit inside the existing disposition or review-pass guidance in doing-code-review/SKILL.md, authorized only by direct bucket-d evidence; it is separate from lens sharpening.
- Consequence retention: the triage-side duty that a deferred or downgraded finding records its durable-invariant consequence and names the condition that would reopen it, so a related later finding is dispositioned against that record rather than re-litigated from scratch.
- Deferred-finding recheck: the review-side duty that, when a review touches a path related to a previously deferred finding whose consequence record is reachable, the reviewer re-examines the deferred invariant against the current bytes before passing the round.
- Vendored twin: the runtime-side copy under `~/.agents/skills/` of each touched `agents/skills/` file, synced byte-equal in the same change per the repository guidelines' Vendored Asset Sync Rules.

## Why

Earlier plan-readiness and execution-review rounds passed, but a later review identified correctness defects and an earlier deferred progress invariant. The available repository evidence does not bind each concern to its reviewed digest, owning stage, changed path, or triage disposition, so those links cannot be inferred. Use the supplied anonymized summary when available or the reviewed repository-only fallback, and leave unsupported classifications indeterminate.

## Gist & Examples

TLDR: an investigation plan that uses the anonymized summary when supplied or a fresh-review-approved repository-only fallback, marks unsupported classes indeterminate, and lands only directly demonstrated review-lens or triage corrections; reliability, because the witnessed post-implementation misses were correctness defects the existing surfaces should catch when their lenses trace invariants across transaction boundaries and verify test oracles.

Before: post-implementation correctness findings surface in a later PR review after plan-readiness and execution reviews passed; a related invariant sits in an earlier record as deferred-nonblocking; the shared review guidance cannot say which gap fired, so any correction would guess between boundary, timing, lens, and triage causes.

After: the run builds the matrix from the summary or the declared fallback; a finding without direct stage, digest, path, or triage evidence remains indeterminate and causes no associated lens or triage edit; demonstrated gap classes receive only their evidence-backed correction; the plan-review boundary, round structure, and panel roster stay unchanged.

Edge cases: a summary or repository record without a covering digest makes the row class indeterminate and the correction for that class does not land; a matrix proving every miss was post-digest (bucket b) lands no lens edit and records the timing evidence instead; a finding the matrix shows was correctly out-of-scope-by-design (bucket a) changes nothing and closes the question for that class; new findings re-enter Task 1 for the added rows only; no source-project identifier, code text, or review quote may enter any tracked artifact.

## Outcome

- The plan-review/implementation-review boundary survives byte-unchanged where the matrix shows bucket-a misses; the demonstrated gap classes get sharpened duties inside existing lens files and triage text, never new ceremony.
- The matrix and its classification evidence live in the run's gitignored record home; the landed guidance carries the conclusions without any new tracked artifact type.
- The original stop-for-operator response remains the default for plans without a declared fallback; this run's reviewed fallback preserves that protection by recording unsupported classes as indeterminate and making no unsupported correction.

Gate delta: no gate, panel, round, validator, ledger, or checklist is added or removed; the change is guidance text inside existing review-agent lenses and triage sections plus byte-equal vendored twins (admission: no new blocking surface exists to admit; the origin row's machinery bar - no addition unless the matrix proves the existing final-diff review cannot catch the miss - is carried by Task 2's precondition that each edit cites its matrix rows).

## Review Scope

- agents/skills/review-agents/concurrency.md and its vendored twin (conditional concurrency lens)
- agents/skills/review-agents/quality.md and its vendored twin
- agents/skills/review-agents/testing.md and its vendored twin
- agents/skills/review-agents/premortem.md (the risk lens) and its vendored twin
- agents/skills/doing-code-review/SKILL.md (triage and disposition text; unchanged unless a matrix row demonstrates the triage gap) and its vendored twin
- agents/skills/review-plan/SKILL.md (the implementation-readiness boundary; byte-unchanged, presence-pinned)
- agents/skills/execute-plan/SKILL.md (Phase 3 review references; unchanged, presence-pinned)
- docs/history/backlog/2026-10-14-post-implementation-review-invariant-coverage.md (the evidence contract of record)
- docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md (the run's evidence-handoff decision record)
- docs/history/backlog/PLAN-PROMPTS.md (existing investigation entry; routing context only)
- scripts/check_maintenance_pins.sh (read-only pre-edit baseline source and consumed validation surface; never changed)
- .ai-playbook/reviews/ (gitignored supplemental review context; cannot establish incident classification)
- scripts/check_review_agent_portability.py and scripts/test_review_agent_doors.py (validation surfaces; consumed, never changed)
- scripts/plan_readiness.py and scripts/fix_plan_em_dashes.py (plan authoring and readiness surfaces; consumed, never changed)
- ~/.ai-playbook/scripts/scan-public-hygiene.sh (hygiene surface; consumed, never changed)
- Out of review scope: review-loop round machinery, review-panel-selection rosters, any validator or gate script, the scheduler state, all other lens files

## Assumptions

- the anonymized summary was not present in the run's recorded inputs; on 2026-10-17 the operator directed the repository-only fallback with indeterminate outcomes, subject to this fresh plan review; basis: the run's input-gate record and the handoff entry's scope arm for repository-only evidence.
- assume every landed lens edit cites matrix rows (the demonstrated-gap precondition); a bucket with no demonstrated rows lands no edit; basis: the origin's rejection of ceremony without evidence and the machinery bar in the same row.
- assume the conditional concurrency and premortem lenses are candidate owners for the lock-ordering concern; select the owner only from direct matrix evidence. Triage rules, if authorized, land in doing-code-review's existing disposition text; basis: the review-agents catalog and origin's Skill/step row.
- assume execution uses the anonymized summary when supplied, otherwise only Task 1's declared repository-only fallback; never inspect the consumer checkout; basis: the user-directed plan revision and the origin's capture-hygiene line.
- assume review-plan/SKILL.md and execute-plan/SKILL.md stay byte-unchanged; basis: the origin's boundary rows and the rejected alternatives.

Decision points requiring a grill: none; the mechanism shape (summary-then-matrix-then-smallest-lens-edit, ceremony rejection, boundary preservation) is pinned by the origin's Expected, Suggested investigation, and Rejected directions sections, and no operator decision is pending before review.

## Tasks

### Task 1: use the authorized evidence input and build the classification matrix
Files:
- docs/history/backlog/2026-10-14-post-implementation-review-invariant-coverage.md
- docs/history/backlog/2026-10-17-post-implementation-review-summary-handoff.md
- docs/history/backlog/PLAN-PROMPTS.md (existing investigation entry; routing context only)
- scripts/check_maintenance_pins.sh (read-only pre-edit baseline source and consumed validation surface; never changed)
- .ai-playbook/reviews/ (gitignored supplemental review context; cannot establish incident classification)
Primary class anchors: the Suggested investigation section in docs/history/backlog/2026-10-14-post-implementation-review-invariant-coverage.md

- [x] [class: IMPLEMENTATION_REQUIRED] Check the run's gitignored input home for the anonymized summary. If present, verify one entry per reported finding, required technical substance, stage, digest, related-record, and triage fields, and no identifying or quoted source material. If technical substance or another required field is missing, mark the affected row indeterminate and do not classify it from partial evidence.
- [x] [class: IMPLEMENTATION_REQUIRED] If the summary is absent, use only the tracked origin and handoff rows. Treat plan-review records under `.ai-playbook/reviews/` as gitignored supplemental context that cannot establish an incident classification; do not inspect the consumer repository or reconstruct missing details.
- [x] [class: IMPLEMENTATION_REQUIRED] No summary was present, so this conditional rejection path was not triggered; no summary content was copied. If any anonymization check fails, reject the summary without copying its contents into the matrix or tracked files. Record only a generic rejection reason and stop for a sanitized replacement; use the repository-only fallback only when the summary is absent.
- [x] [class: IMPLEMENTATION_REQUIRED] Inventory separately the source-described concerns: lock-ordering cycle; duplicate range jobs after terminal completion or failure; stale test assumptions about job identity and fixture state; earlier deferred progress invariant. Do not equate this inventory with the exact finding count or mappings unless the summary proves them.
- [x] [class: IMPLEMENTATION_REQUIRED] Build the matrix in the run's gitignored record home. For each finding or concern, record exact repo-relative locators, available and unavailable fields, bucket or indeterminate status, and reason. If the mapping or count cannot be proven, mark the relationship and overall coverage indeterminate.
- [x] [class: IMPLEMENTATION_REQUIRED] Assign a to d only where direct source evidence binds the finding to its reviewed digest and disposition. Verify that each cited locator directly supports the bucket. Otherwise record indeterminate and leave the owning stage, lens, changed path, and triage class unknown; do not infer from the origin's technical summary. Indeterminate rows authorize no lens or triage edit.
- [x] [class: IMPLEMENTATION_REQUIRED] Before any lens or triage edit, run the maintenance-pins command and capture its exact failing set in the run record.
- [x] [class: IMPLEMENTATION_REQUIRED] Update the summary-handoff backlog row with the investigated remove-or-keep disposition: preserve the original review-gap origin, use this reviewed fallback only for the current run, and leave the delivery-contract item open until the durable summary handoff is resolved.

### Task 2: land only the demonstrated lens sharpening
Files:
- agents/skills/review-agents/concurrency.md
- agents/skills/review-agents/quality.md
- agents/skills/review-agents/testing.md
- agents/skills/review-agents/premortem.md
Primary class anchors: the concurrency duties in agents/skills/review-agents/concurrency.md and the review duties in agents/skills/review-agents/quality.md

- [x] [class: IMPLEMENTATION_REQUIRED] For each bucket-c row that directly demonstrates a panel miss, sharpen only its owning lens inside an existing section. Cite the supporting matrix rows in the commit message.
- [x] [class: IMPLEMENTATION_REQUIRED] Add the cross-transaction invariant trace to concurrency.md only when direct evidence shows a bucket-c concurrency-panel miss. Use another lens only when the matrix proves that lens owns the miss.
- [x] [class: IMPLEMENTATION_REQUIRED] Add the test-oracle check only when direct evidence shows a bucket-c panel miss involving stale test assumptions. Bucket-d evidence routes to Task 3.
- [x] [class: IMPLEMENTATION_REQUIRED] Bucket-d rows prove a triage gap and route to Task 3. They do not authorize lens edits unless independent evidence also proves a bucket-c miss.
- [x] [class: IMPLEMENTATION_REQUIRED] Indeterminate rows land no lens edit; bucket-b and bucket-a rows also land no lens edit, with their direct timing or boundary evidence recorded in the run record.
- [x] [class: IMPLEMENTATION_REQUIRED] Sync every touched lens file's vendored twin byte-equal in the same change.
- [x] [class: REPOSITORY_TEST] Presence pins (fail before, pass after): require each trace or oracle phrase only when its corresponding duty is authorized and touched; verify it in that lens and its twin, with `diff` exiting 0. Record when a duty has no authorized pin.
- [x] [class: REPOSITORY_TEST] For every authorized duty or distinct lens edit in each changed lens, provide a trigger witness using separate samples or one sample that explicitly asserts every duty; record the covered matrix rows and each outcome. Skip only when no lens duty is authorized or changed.

### Task 3: the triage-side consequence and recheck duties
Files:
- agents/skills/doing-code-review/SKILL.md
Primary class anchors: the triage and disposition sections in agents/skills/doing-code-review/SKILL.md

- [x] [class: IMPLEMENTATION_REQUIRED] If any bucket-d row is demonstrated: add the consequence-retention duty to the existing disposition text (a deferred or downgraded finding records its durable-invariant consequence and its reopen condition) and the deferred-finding-recheck duty to the existing review-pass text, each citing its matrix rows in the commit message; indeterminate rows do not qualify, and a matrix with no demonstrated bucket-d row changes this file not at all.
- [x] [class: IMPLEMENTATION_REQUIRED] Sync the vendored twin byte-equal in the same change when touched.
- [x] [class: REPOSITORY_TEST] Presence pins when touched (the retention and recheck phrases in the skill and its twin, `diff` exits 0), plus realistic sample context that triggers both consequence-retention and deferred-finding-recheck, or separate samples for each; record both covered duties and outcomes. When untouched, record the no-demonstrated-row basis in the run record.

### Task 4: boundary preservation pins and validation
Files:
- agents/skills/review-plan/SKILL.md
- agents/skills/execute-plan/SKILL.md
- scripts/check_maintenance_pins.sh
- scripts/check_review_agent_portability.py (consumed validation surface)
- scripts/test_review_agent_doors.py (consumed validation surface)
- scripts/plan_readiness.py and scripts/fix_plan_em_dashes.py (consumed plan tooling)
Primary class anchors: the implementation-readiness boundary in agents/skills/review-plan/SKILL.md

- [x] [class: REPOSITORY_TEST] Byte-unchanged pins: compare review-plan/SKILL.md and execute-plan/SKILL.md with pre-change copies and require zero byte differences; verify the landing diff also has zero hunks in both files. Their vendored twins remain byte-equal to the pre-change copies (`diff` exits 0).
- [x] [class: REPOSITORY_TEST] After lens or triage edits, rerun `bash scripts/check_maintenance_pins.sh` and compare its exact failing set with the baseline captured in Task 1. Require equality; investigate any added or removed failure.
- [x] [class: REPOSITORY_TEST] Review-agents gates (mandated for any review-agents change): `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/check_review_agent_portability.py` exits 0 and `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/test_review_agent_doors.py` exits 0.
- [x] [class: REPOSITORY_TEST] Hygiene: `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0 and the repository no-em-dash scanner reports no new finding in touched files.
- [x] [class: REPOSITORY_TEST] Validation: the run record carries the matrix, the per-bucket and indeterminate disposition lines, and the landed-edit-to-row citations; the closeout report names each outcome, unavailable evidence, and any remaining stop-for-operator condition.

## Evaluation Criteria

Done when: with a supplied summary, every reported finding has a matrix row; on fallback, every source-described concern has a row and unsupported total finding coverage is marked indeterminate. Only demonstrated-gap lens and triage edits land, each with byte-equal twins and presence pins; indeterminate findings have no associated edits; boundary files carry zero hunks; pins failures match the captured baseline.
Ship when: all tasks' validation lines pass on the landed tree and the run record names the per-bucket outcomes.

## Validation Commands

Validation preamble: the rule-29 pre-round gates run before every review round (`python3 scripts/plan_readiness.py <plan> --pre-round`, outcomes in the round records); the pins command below is compared against the captured pre-change failing set, not a green set.

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/check_review_agent_portability.py
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 scripts/test_review_agent_doors.py
bash scripts/check_maintenance_pins.sh
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
git diff --stat <merge-base> HEAD -- agents/skills/review-plan/SKILL.md agents/skills/execute-plan/SKILL.md
diff agents/skills/review-agents/quality.md "$HOME/.agents/skills/review-agents/quality.md"
diff agents/skills/review-agents/testing.md "$HOME/.agents/skills/review-agents/testing.md"
diff agents/skills/review-agents/premortem.md "$HOME/.agents/skills/review-agents/premortem.md"
diff agents/skills/doing-code-review/SKILL.md "$HOME/.agents/skills/doing-code-review/SKILL.md"
diff agents/skills/review-plan/SKILL.md "$HOME/.agents/skills/review-plan/SKILL.md"
diff agents/skills/execute-plan/SKILL.md "$HOME/.agents/skills/execute-plan/SKILL.md"
```

## Out of scope

- No new review round, panel, gate, validator, ledger, checklist, or tracked artifact type; no roster or round-budget change; no review-loop machinery edit.
- No plan-review boundary change: review-plan/SKILL.md and execute-plan/SKILL.md stay byte-unchanged.
- No source-project access: execution consumes the operator-provided anonymized summary when supplied, otherwise the declared repository-only fallback; gitignored review records are supplemental only and cannot establish classification; no identifier, code text, or review quote enters any tracked artifact.
- No bucket-a or bucket-b correction: out-of-scope-by-design and post-digest timing evidence are recorded, not patched with guidance.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-14-post-implementation-review-invariant-coverage.md`: the repository-only investigation found the review-gap origin remains valid, and this plan recorded the evidence-bound fallback and left unsupported classifications indeterminate; the covered origin is deleted in this archive pass.
