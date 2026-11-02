# Plan: Staged-review head freshness and coverage-evidence floor

Backlog origin: docs/history/backlog/2026-11-02-review-freshness-and-code-coverage-gaps.md
Driving force: code-quality (the origin declares `reliability`, which is outside the closed taxonomy; code-quality is the recorded mapping, justified because the plan hardens review evidence quality in shared process guidance, a code-quality concern; park-triage would not take it: the witnessed stale-post is a reliability defect in consumer-facing review machinery, not a parked hardening class)
Plan review record: the staging series .ai-playbook/reviews/2026-11-02-plan-review-review-freshness-and-code-coverage-gaps-p5bcb951b-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.0h total, largest task 1.0h
Authoring claim: review-freshness-and-code-coverage-gaps.md (session sess_automation-ff265d03-1952-auth)

## Terms

- Staged review: a review record staged under review-staging that has not been posted yet.
- Reviewed head: the PR head identified by the head identity line; the record's `Source digest` covers the reviewed-scope diff bytes derived from the base and that head (per the canonical reviewed-scope derivation), never the commit's own tree bytes.
- Head identity line: the staging Metadata context line recording the reviewed PR head OID and its resolution time, written when the review source is a PR; its format home is review-staging's `Review context` family.
- Moved-head disposition line: the companion record line written when the pre-post head check finds the PR head no longer equal to the head identity line, or when the head comparison or the digest-comparison fallback cannot verify the record's freshness (a failed re-resolution, a mismatch, an unrecorded or unverifiable base, or non-recomputability); it names the old head, the new head, the delta scope evidence, and the chosen recovery arm. Its home is the successor record the chosen arm allocates, written at allocation before the arm executes.
- Pre-post head check: the read-only re-resolution of the PR head immediately before posting, compared against the head identity line; it is the only re-resolution point in the flow; a failed or unresolvable re-resolution is cannot-verify and never posts as current.
- Verified delta review: a bounded re-review whose scope is exactly the bytes the head move introduced (the delta range old head..new head), executed in a successor record whose `source_digest` covers the new head's reviewed-scope bytes.
- Delta scope evidence: the disposition's naming of the delta range and where the delta diff was materialized for the reviewers, so the record shows the reviewed surface equaled the moved bytes.
- Coverage citation: the testing worker's evidence row naming the test name and the assertion (or the explicit uncovered verdict) for each claimed input partition, in the shape testing.md's Evidence requirement defines.
- Metric trace: the correctness-completeness walk of a changed terminal outcome that feeds more than one emitted metric through each of those metrics, citing branch evidence for each leg.
- Cross-path identifier claim: a finding that compares or joins identifiers emitted by separate code paths (for example live vs baseline) or infers a deduplication consequence from them.

## Why

A five-worker review was staged against an earlier PR snapshot and later posted against a newer head without re-review: two behaviors already present in the snapshot (a blank business identifier bypassing the documented fallback, and a rejected result still incrementing a legacy success counter) were missed, and a retry hook added after the snapshot was never reviewed by anyone (origin row, 2026-11-02). The `Source digest` binds the reviewed bytes, but nothing re-checks at posting time that the PR still carries those bytes. Independently, the testing worker described mapping coverage in prose while the reviewed tests exercised only populated identifiers and asserted nothing about the rejected-result metric, so described coverage escaped without named evidence.

## Gist & Examples

TLDR: staged PR reviews now record the reviewed head identity and are re-checked against the live head before posting; changed mapping partitions must cite named tests and assertions or be marked uncovered, terminal outcomes feeding multiple metrics must carry branch-evidence metric traces, and cross-path identifier claims need a verified data relationship; driving force: code-quality (origin force reliability: hardening review evidence quality in shared process guidance).

Before (today): a review is staged against head H1. The PR advances to H2 (adding a retry hook). The orchestrator posts the staged findings as current; the H2 bytes were never reviewed. Separately, the testing worker reports "mapping is covered" without naming a test or assertion, and a reviewer infers a deduplication risk from identifiers emitted by separate paths because a README expectation mentions both.

After (this plan): the staged record carries the head identity line (H1, resolved-at). Before posting, the orchestrator re-resolves the head: unchanged, post as current; moved, the staged review is not posted as current, and the orchestrator chooses a full re-review or a verified delta review, executed in a successor record covering the new bytes, with the disposition recording old head, new head, delta range, and chosen arm. When no head identity line exists (records staged before this change), the check compares the recomputed reviewed-scope digest against the sidecar's `source_digest` instead of posting blind; a mismatch cannot-verify routes to the full re-review arm only. The testing worker's coverage rows name test and assertion per partition (including blank or absent identifiers when the contract covers them) in the Evidence requirement's shape, and correctness-completeness traces terminal outcomes through every emitted metric with branch evidence; a cross-path identifier claim needs a verified data relationship, and a README expectation alone does not supply one.

Edge cases: the head moves between the pre-post check and the posting call itself (bounded residual window, accepted: the check is read-only and cannot lock the head); the head is force-pushed repeatedly during review (the posting-time check is the only re-resolution point; posting simply waits for its own check's verdict); the moved bytes are doc-only (the verified delta review may be a bounded doc-scope pass, still recorded); no head identity line exists on an older record (the digest-comparison fallback applies; a mismatch or cannot-verify takes the full re-review arm only); the review source is not a PR (plan or local diff: the head identity line and pre-post check do not apply).

## Outcome

A staged review cannot be posted as current after the PR head moved without the new bytes being reviewed, and coverage claims cite real assertions or are explicitly uncovered.

- The reviewed head identity is recorded in the staging record when the source is a PR, regardless of diff size.
- Posting after a head move forces a full re-review or a verified delta review in a successor record, recorded via the moved-head disposition line before posting.
- A record without a head identity line posts only after a recomputed reviewed-scope digest matches the sidecar's `source_digest`, or enters the moved-head recovery path (full re-review only; no delta arm without a baseline head).
- Testing and correctness-completeness worker prompts require named test/assertion evidence for claimed partitions and metric traces for terminal outcomes feeding multiple metrics.
- Cross-path identifier comparisons and deduplication-consequence claims require a verified data relationship; a README expectation alone is not evidence.
- No new gate, validator, worker, or automated blocker is added; the pre-post head check is a required ceremony (a step in the posting flow, not a gate), registered in the machinery registry.

Gate delta: none across refusal classes, hard gates, fences, protocol layers, and schema fields; one prose-only task condition that pauses later work is added (the posting flow pauses until the chosen recovery arm's review completes), declared and priced in the Machinery admission paragraph below.

Machinery admission: the pre-post head comparison is a required ceremony (a step in the posting flow, not a gate); witness: one staged review reused after the PR head advanced with a later retry-path change unreviewed (origin row); catch frequency unknown with one witnessed instance; false-positive cost is a redundant delta or full re-review after a benign head move, mitigated by the check being read-only and the delta-review arm bounded; review by 2026-12-02, tracked as a `duty:` row in `scripts/machinery_registry.json` added by Task 4 with a removal-or-promote commitment.

## Assumptions

- assume the head identity line and the pre-post check live in `doing-code-review` (Step 1 staging metadata and the Posting Staged Findings flow); basis: that skill owns review orchestration and posting, and the record shape already carries a recomputed `Source digest` beside which the head OID naturally sits.
- assume the head identity line is an unvalidated Metadata context line (the `Review context` family, present when applicable), not a sidecar schema extension; basis: the origin row asks for the smallest shared-guidance change, and a schema/validator change would touch the gold-source descriptor for one witnessed incident.
- assume `github-pr-workflow` needs no edit: its `gh pr view --json headRefOid` resolution is already the canonical head read; basis: the skill's Shared GitHub PR Operations section.
- assume the five-worker panel and the finding budget stay unchanged; basis: origin row and `review-agents/review-panel-selection.md`.
- Decision receipts: stale-head recovery adjudication and the coverage-evidence floor adjudication are recorded in the Decision points trailer below (single home).

Decision points requiring a grill: stale-head recovery arm (full re-review vs verified delta vs orchestrator choice) resolved to orchestrator choice with a recorded disposition executed in a successor record, source origin row Suggested direction 1 plus r1 panel adjudication (successor-record semantics), 2026-11-02, affected sections Gist & Examples, Outcome, Tasks; Coverage-evidence floor adjudicated to worker-prompt text (testing.md, quality.md), not a staging validator field (machinery admission, one witness), 2026-11-02, affected sections Outcome, Tasks.

## Standing constraints

- `agents/skills/doing-code-review/SKILL.md` and `agents/skills/review-staging/SKILL.md` are pinned by `scripts/check_maintenance_pins.sh`: an edit that moves or breaks a pinned span updates that span's mirror inside `scripts/check_maintenance_pins.sh` in the same commit, and each new operative span this plan adds to a pinned file gains its companion pin in the same edit.
- Skill text stays tool-agnostic and imperative, matching the surrounding file's density and idiom.
- No em dash (U+2014) in any added line.

## Evaluation Criteria

- Correctness: every edited location is real, verified by grep before certification (doing-code-review Step 1 comparison-basis resolution and Posting Staged Findings flow; testing.md Coverage Claim Audit; quality.md Correctness; review-staging Metadata Review context; the machinery registry row).
- Consistency: the new terms each have one definition home; greping the edited files shows no contradicting wording against the existing `Source digest` recompute rule or the review-panel-selection five-worker policy.
- Gates: `bash scripts/check_maintenance_pins.sh` exits 0, `bash scripts/scan-public-hygiene.sh` exits 0, `python3 scripts/check_review_agent_portability.py` exits 0, `python3 scripts/test_review_agent_doors.py` exits 0, `python3 scripts/machinery_inventory.py --check` exits 0 or fails only on the two pre-existing regrowth rows it already reports at this branch's base (unregistered `scripts/quota_sources.py` and `scripts/reconcile_execute_plan_handoff.py`; their registration is tracked by the machinery-inventory-regrowth EXEC-PROMPTS entry), and the added lines carry no em dash.

Done when: the edits are committed on the run branch, the gates above are green, and the branch diff contains exactly the Review Scope paths plus this plan document.

Ship when: none (repository-internal process text; no external release surface).

## Tasks

### Task 1: head identity capture in doing-code-review

Files:
- `agents/skills/doing-code-review/SKILL.md`
- `scripts/check_maintenance_pins.sh` (companion pins beside any moved pinned span)

Context surfaces: the Terms dictionary (head identity line) and the Standing constraints section.

- [ ] Add an unconditional head identity capture in the Step 1 comparison-basis resolution: its own PR-source bullet beside the magnitude check, independent of the magnitude outcome, ordered after the pull-latest-commits block (or refreshed after the pull) before workers see the diff. [class: IMPLEMENTATION_REQUIRED]
- [ ] Define the captured content: for a GitHub PR source, record the resolved PR head OID (`gh pr view --json headRefOid` per `github-pr-workflow`) and its resolution time in staging Metadata as the head identity line, whose format home is review-staging's `Review context` family (cite, never restate the literal); the capture applies to every mode that stages a record, Direct Mode included. [class: IMPLEMENTATION_REQUIRED]

### Task 2: pre-post head check outcomes in doing-code-review

Files:
- `agents/skills/doing-code-review/SKILL.md`

Context surfaces: the Terms dictionary (pre-post head check, moved-head disposition line).

- [ ] Add the pre-post head check to the Posting Staged Findings flow before any posting call (the flow's only head re-resolution point): given a staged record whose recorded head equals the re-resolved PR head, expects the posting proceeds as current. [class: IMPLEMENTATION_REQUIRED]
- [ ] Define the moved-head outcome: given a record whose head moved, expects no posting as current and the recovery arms below execute before any posting. [class: IMPLEMENTATION_REQUIRED]
- [ ] Define the cannot-verify outcome: given a failed or unresolvable re-resolution at posting time, expects no posting as current; the orchestrator re-runs the check once or routes to the full re-review arm, the disposition recording the failed comparison, mirroring the fallback's non-recomputability clause. [class: IMPLEMENTATION_REQUIRED]
- [ ] Wire the moved-head recovery: the orchestrator chooses a full re-review or a verified delta review; either arm runs in a successor record allocated through the record selection helper's new-round path (backup, then mark-superseded on the prior record) with `source_digest` re-bound to the new head's reviewed-scope bytes and the Selection reason naming the review scope. [class: IMPLEMENTATION_REQUIRED]

### Task 3: moved-head recovery arms and the no-baseline fallback in doing-code-review

Files:
- `agents/skills/doing-code-review/SKILL.md`
- `scripts/check_maintenance_pins.sh` (companion pins beside any moved pinned span)

Context surfaces: the Terms dictionary (verified delta review, delta scope evidence, moved-head disposition line) and the record selection helper's new-round, mark-superseded, recover-orphan, and verify-digest surfaces.

- [ ] Record the moved-head disposition line in that successor record at allocation, before the arm executes, carrying the delta scope evidence: old head, new head, the delta range (old head..new head), where the delta diff was materialized, and the chosen arm. [class: IMPLEMENTATION_REQUIRED]
- [ ] Preserve reviewed findings across the delta arm: the successor record incorporates the prior record's still-valid staged findings beside the arm's own delta findings, carried with their triage statuses, so reviewed findings on unchanged bytes reach the posted review. [class: IMPLEMENTATION_REQUIRED]
- [ ] Adjudicate carried findings: the delta arm's reviewers adjudicate each carried finding whose anchor intersects the delta range (keep, revise, or drop, recorded in the successor's triage outcomes); findings outside the delta range carry unchanged; the full re-review arm re-derives all findings and carries none over. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the no-baseline fallback for records with no head identity line (records staged before this change; never a non-PR source, whose edge case excludes the check): the check re-resolves the head and recomputes the current head's reviewed-scope digest through the canonical derivation the record selection helper's verify-digest mode uses (`corrections_record.reviewed_scope_bytes` over `git diff <base>...<head>` with its reviewed-scope path filtering). [class: IMPLEMENTATION_REQUIRED]
- [ ] Define the fallback's inputs and comparison: the base comes from the resolved base the record's Metadata records (the magnitude check or the non-interactive resolution note), when one is present and verifiable; absence is the expected legacy shape. The comparison targets the sidecar's `source_digest` (the canonical helper's own comparison value). [class: IMPLEMENTATION_REQUIRED]
- [ ] Define the fallback's match arm: given a recomputed digest equal to the sidecar's `source_digest`, expects the head identity line is recorded and the posting proceeds as current. [class: IMPLEMENTATION_REQUIRED]
- [ ] Define the fallback's cannot-verify arm: given a mismatch, an unrecorded or unverifiable base, or any other non-recomputability, expects the full re-review arm only (no delta arm exists for a baseline-less record), run in a successor record per the moved-head wiring, the disposition's old-head and delta fields filled as `unknown (no baseline)` and the firing comparison recorded in their place; never post a legacy PR record without this comparison. [class: IMPLEMENTATION_REQUIRED]
- [ ] Route a sidecar-less or orphan-half prior record through the record selection helper's `recover-orphan` subcommand before the new-round allocation. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the residual-window note: the check is read-only and does not lock the head; a move landing between the check and the posting call is accepted residual risk. [class: IMPLEMENTATION_REQUIRED]

### Task 4: coverage-evidence floor in the worker prompts

Files:
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/quality.md`

Context surfaces: the Terms dictionary (coverage citation, metric trace, cross-path identifier claim).

- [ ] Extend the `## Coverage Claim Audit` section of `agents/skills/review-agents/testing.md` with the coverage-citation requirement: when the diff changes mapping, fallback, or identifier-handling behavior, the worker names each contract-relevant input partition, including the blank or absent identifier case when the contract covers one. [class: IMPLEMENTATION_REQUIRED]
- [ ] Require the citation shape: each named partition cites the test name and the assertion exercising it in the shape the Evidence requirement section defines, or records the partition as uncovered; prose-only coverage descriptions do not satisfy the requirement. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the `## Correctness` section of `agents/skills/review-agents/quality.md` with the metric-trace requirement: when a changed terminal outcome feeds more than one emitted metric, correctness-completeness traces the outcome through every emitted metric and cites the branch evidence for each leg; a metric omission is not inferred from a metric definition alone. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the cross-path evidence threshold to the same `## Correctness` section: a finding comparing identifiers from separate paths or claiming a deduplication consequence requires evidence of a real data relationship between the values; a README expectation alone establishes intended behavior, not a same-record relationship, and such a claim without it is dropped or downgraded to a question. [class: IMPLEMENTATION_REQUIRED]

### Task 5: review-staging Metadata documentation

Files:
- `agents/skills/review-staging/SKILL.md`
- `scripts/check_maintenance_pins.sh` (companion pins beside any moved pinned span)

Context surfaces: the Terms dictionary (head identity line, moved-head disposition line).

- [ ] Document in the Metadata `Review context` family of `agents/skills/review-staging/SKILL.md` the optional head identity line for PR-sourced reviews (`Reviewed PR head: <oid> (resolved <iso time>)`) and the moved-head disposition line; this file is the single format home for both lines, and doing-code-review cites it. Both lines are present-when-applicable and unvalidated. [class: IMPLEMENTATION_REQUIRED]

### Task 6: machinery registry duty row

Files:
- `scripts/machinery_registry.json`

Context surfaces: the Machinery admission paragraph and the registry's existing two-row convention (`duty:review-staging-series-sweep` precedent).

- [ ] Add the `entries` duty row `duty:doing-code-review-pre-post-head-check` carrying the incident witness, catch frequency (unknown, one witnessed instance), false-positive cost (redundant delta or full re-review after a benign head move), the 2026-12-02 review date, and the removal-or-promote commitment. [class: IMPLEMENTATION_REQUIRED]
- [ ] Set the duty row's witness ref at add time to this plan's living path (`docs/history/plans/2026-11-02-review-freshness-and-code-coverage-gaps.md`, tracked and gate-green); the completion pass re-points it to this plan's completed twin under `docs/history/plans/completed/` in the same change that deletes the origin row (the registry's claim-fence precedent, `duty:review-staging-series-sweep`). [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the paired `removals` row pre-registering the co-removal set (the Task 2-3 check and fallback spans in doing-code-review, the Task 5 line documentation in review-staging, the companion pins added beside them, and both registry rows), the 2026-12-02 sunset, and the promote-on-true-catch criteria. [class: IMPLEMENTATION_REQUIRED]

## Validation Commands

- `bash scripts/check_maintenance_pins.sh`
- `bash scripts/scan-public-hygiene.sh`
- `python3 scripts/check_review_agent_portability.py`
- `python3 scripts/test_review_agent_doors.py`
- `python3 scripts/machinery_inventory.py --check` (scoped: no new failures beyond the two pre-existing regrowth rows the base already reports)
- `git diff main...HEAD --name-only | xargs grep -l "$(printf '\u2014')"` (added-lines em-dash scan; zero files expected)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/doing-code-review/SKILL.md` (Task 1) (Task 2) (Task 3)
- `agents/skills/review-agents/testing.md` (Task 4)
- `agents/skills/review-agents/quality.md` (Task 4)
- `agents/skills/review-staging/SKILL.md` (Task 5)
- `scripts/machinery_registry.json` (Task 6)
- `scripts/check_maintenance_pins.sh` (companion-pin additions only) (Task 1) (Task 3) (Task 5)

**Tests:** none (documentation-only plan; the gates are the pins suite, the hygiene scan, and the review-agents portability and doors suites).

**Non-goals (out of scope, findings here are not blocking):**
- `agents/skills/github-pr-workflow/SKILL.md` (orientation only; no edit)
- `agents/skills/review-agents/review-panel-selection.md` (panel composition unchanged)
- any validator schema or descriptor change in `scripts/validate_review_staging.py`
- any automated blocking gate, new worker, or finding-budget change
- Direct Mode (skip staging) PR postings: the Step 1 head capture applies to every mode that stages a record (Direct included, since Direct also writes the staging record), but the pre-post head check is scoped to the staged Posting Staged Findings flow; the Direct-mode posting call's residual risk is accepted and recorded here rather than guarded

**Expected diffusion:** only the Review Scope paths; a pins-suite failure naming a pinned span moved by these edits is fixed by updating the span's mirror in the same commit.
