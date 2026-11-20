# Plan: PR review-scope freshness and coverage-evidence floor

Backlog origin: docs/history/backlog/2026-11-02-review-freshness-and-code-coverage-gaps.md
Additional backlog origin: docs/history/backlog/2026-11-02-machinery-inventory-regrowth-two-runtime-scripts.md
Driving force: code-quality (the origin declares `reliability`, which is outside the closed taxonomy; code-quality is the recorded mapping, justified because the plan hardens review evidence quality in shared process guidance, a code-quality concern; park-triage would not take it: the witnessed stale-post is a reliability defect in consumer-facing review machinery, not a parked hardening class)
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-review-freshness-and-code-coverage-gaps-p5bcb951b-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 4.5h total, largest task 1.5h
Authoring claim: review-freshness-and-code-coverage-gaps.md (session sess_automation-ff265d03-1952-auth)

## Terms

- Staged review: a review record staged under review-staging that has not been posted yet.
- Staged Mode: the PR-review path that writes and checks a staged review record before posting findings.
- Direct Mode: a PR review path that posts findings without first staging a review record.
- Legacy PR review record: a prior PR review record missing either the reviewed base OID or reviewed head OID, so its historical identity pair cannot be established from its record.
- Reviewed PR base identity: the base OID and resolution time for the PR diff, recorded in staging Metadata when the source is a PR; its format home is review-staging's `Review context` family.
- Reviewed PR head identity: the head OID and resolution time for the PR diff, recorded in staging Metadata when the source is a PR; its format home is review-staging's `Review context` family.
- Reviewed PR identity pair: the exact local base and head OIDs used to derive the reviewed-scope diff, each matched to the resolved PR `baseRefOid` and `headRefOid` before workers start.
- Captured PR scope baseline: the matched base/head OIDs and reviewed-scope digest fixed before workers start; Staged Mode records the tuple before posting, while Direct Mode keeps it as run state until its post-send record is written.
- Moved-scope disposition line: the companion record line written when the pre-post scope check finds either PR OID no longer matches its recorded identity, or when the identity or digest comparison cannot verify freshness. For a resolved comparison it records the old and new OID pairs, any applicable head-delta evidence, and the chosen recovery arm; for an unresolved comparison it records the reason and omits OID and delta fields, as defined by review-staging. Its home is the successor record, written at allocation before recovery runs.
- Pre-post scope check: the read-only re-resolution of both PR OIDs immediately before each PR posting path, compared against the captured PR scope baseline and recomputed reviewed-scope digest; when a staging record already exists, its pair and digest must also match that baseline. A failed or unresolvable comparison never posts as current.
- Verified delta review: a bounded re-review of the range old head..new head, allowed only when the PR base OID is unchanged; it runs in a successor record whose `source_digest` covers the new full reviewed scope.
- Delta scope evidence: the disposition's old and new base/head OIDs, range, and diff location; delta evidence is valid only for a head move with an unchanged base.
- Coverage citation: the testing worker's evidence row naming the test name and the assertion (or the explicit uncovered verdict) for each claimed input partition, in the shape testing.md's Evidence requirement defines.
- Application retry counter: `MQMessage.retryTimes`, incremented when the application creates a retry message; it is distinct from the broker's reconsume attempts.
- Metric trace: the correctness-completeness walk of a changed terminal outcome that feeds more than one emitted metric through each of those metrics, citing branch evidence for each leg.
- Cross-path identifier claim: a finding that compares values emitted by separate paths or infers a deduplication consequence; the review must trace whether they identify the same logical event or record and share the relevant time scope, because a README contract expectation alone does not prove that relationship in observed data.

## Why

The first five-worker review of this pull request was posted against a newer head than the head it reviewed, so two in-scope gaps and later code changes escaped timely review. This plan makes each review check that its scope still matches the pull request and requires evidence for test, metric, sensitive-data, and broker-retry claims. It also limits cross-path identifier and deduplication claims to relationships this project can verify.


## Gist & Examples

TLDR: PR reviews record the exact base/head pair used for the diff and verify that pair and its digest before posting in every mode; changed mapping, representation, sensitive-data, and serialization partitions cite named tests and assertions or are marked uncovered; batch retry claims follow the actual broker/client failure semantics; terminal outcomes feeding multiple metrics carry branch-evidence traces; and cross-path identifier claims need a verified data relationship; driving force: code-quality (origin force reliability: hardening review evidence quality in shared process guidance).

Before (today): a review is derived from local base B1 and head H1. The PR advances to H2 (adding a retry hook), or its base moves while H1 stays fixed. The orchestrator can post findings without proving the reviewed diff still matches the PR. Direct Mode has the same stale-post path. Separately, the testing worker reports "mapping is covered" without naming a test or assertion, and a reviewer infers a deduplication risk from identifiers emitted by separate paths because a README expectation mentions both, without establishing that they identify the same event in the same time scope.

After (this plan): the run captures the exact local base/head OIDs and reviewed-scope digest, matched to the resolved remote pair before workers start. It resolves project scope from the target repository's facts, not the shared skill checkout. If local refs are stale, fetch `refs/heads/<baseRefName>` and `refs/pull/<PR>/head` into temporary review refs without changing the checked-out branch, HEAD, index, or working tree, re-resolve PR context, and derive the worker diff from refs matching the refreshed OIDs. Staged Mode records the baseline before posting; Direct Mode keeps the same tuple as run state for the pre-post check and writes it into the staging record afterward. Before every PR post, both modes re-resolve the OIDs and recompute the digest. Submit against the captured head OID and verify the response binding, then re-resolve both PR OIDs. Mark the review current only when the returned commit and both post-submission OIDs match the captured values. If either PR OID moved, record `STALE (scope moved after submission; successor required)`, keep findings pending, and allocate successor recovery; a later head-only move may use a verified delta, while a base move requires full re-review. If comments landed but either freshness check failed, they remain recorded as landed comments but do not make the review current. A legacy record missing either OID remains unverified even when today's digest matches, because a digest identifies diff bytes but cannot recover the historical base/head pair; it requires a full re-review in a successor before posting. The testing worker's coverage rows name test and assertion per contract-relevant partition, including runtime representations and sensitive-data paths, or mark it uncovered. Security traces protected values through transformation, failure, transport, and log paths; concurrency verifies batch retry and acknowledgement semantics against the actual broker/client contract; correctness-completeness traces terminal outcomes through every emitted metric with branch evidence; and cross-path identifier claims require evidence of a real data relationship.

Edge cases: the base or head moves between the final scope check and posting; bind the submission to the captured head and re-resolve after submission, without claiming the checks are atomic; a head-only move with the same base may use a verified delta, including a doc-only delta; a base move requires full review because the head delta does not represent the changed base; legacy records missing either OID identity remain unverified and require full re-review even if today's digest matches; Direct Mode has no staging record at pre-post time, so it compares against the captured in-run tuple and persists it afterward; unresolved identity or digest never posts; non-PR reviews do not use the PR identity check; a batch sibling's retry budget is judged from the pinned broker/client failure semantics, not inferred from batch size alone; and a possible PII-bearing error body remains conditional until its content and sink are evidenced.

## Outcome

A PR finding is marked current only when the captured reviewed base/head pair and reviewed-scope digest match before posting, the post response binds to the captured head, and both PR OIDs still match in the immediate post-submission check. Staged Mode verifies the record against that baseline before posting, and Direct Mode persists that baseline in its record afterward. If either post-submission OID differs, the record is `STALE (scope moved after submission; successor required)` and findings remain pending even if comments landed. Coverage claims cite real evidence or are explicitly uncovered.

- Before workers start, resolve target-project scope from the reviewed repository's facts; capture the local PR base/head pair and reviewed-scope digest, matched against remote `baseRefOid` and `headRefOid`; on stale local refs, fetch both PR refs into temporary review refs, re-resolve context, and recompute without changing the branch, HEAD, index, or working tree. Worker diffs use refs whose OIDs match the refreshed PR context.
- Staged Mode records the captured pair in Metadata before posting; Direct Mode keeps the same tuple as run state until the post-send staging record is written.
- Before every PR post, staged or Direct Mode, both OIDs and the recomputed reviewed-scope digest must match the captured baseline; when a staged record already exists, it must carry the same values. Submit against the captured head OID, verify the response `commit_id`, then re-resolve both PR OIDs. Mark current only if the response binding and both post-submission OIDs match; otherwise record stale, keep findings pending, and enter Task 2 recovery. A mismatch refreshes the local refs and context once, then enters recovery automatically.
- A head-only move with an unchanged base may use full or verified delta review in a successor; a base move uses full review only. A resolved moved-scope disposition records the old and new OID pairs and chosen arm; an unresolved disposition records its reason, omits OID and delta fields, and requires full re-review.
- A legacy record missing either identity line never posts as current based on a matching current digest; it enters full re-review in a successor whose current identity pair is captured before workers start.
- Testing worker prompts require named test/assertion evidence for each claimed contract-relevant partition, including runtime representation and sensitive-data transformation branches, or explicitly mark it uncovered; security and concurrency prompts trace sensitive data and exact broker/client batch retry semantics.
- Correctness-completeness worker prompts require metric traces for terminal outcomes feeding multiple metrics.
- Cross-path identifier comparisons and deduplication-consequence claims require evidence that the values identify the same logical record in the relevant time scope; if only an upstream contract expectation is available, record the relationship as unverified and withhold the defect or deduplication claim.
- Delta successors preserve coverage for unchanged scope through `coverage.inherited_coverage` and record fresh coverage for the delta; full re-reviews establish fresh coverage for the whole scope.
- No new gate, validator, worker, or operator-blocking pause is added; stale local refs trigger one fetch and recomputation, then automatic successor recovery, registered in the machinery registry.
- The deployment manifest admits `quota_sources.py` as a local sibling of the already-deployed `quota_window_probe.py`, and the machinery registry records both existing live scripts with their tests and introduction witnesses.

Gate delta: Adds a counted pre-post refusal: after one temp-ref refresh, a still-mismatched or unverifiable pair skips the old post and enters successor recovery. The `duty:doing-code-review-pre-post-scope-check` row records the incident, unknown frequency, false-positive cost, and 2026-12-02 review/removal-or-promotion. This adds no operator pause, validator, field, or worker. A post is current only if the response and both post-submit OIDs match; stale findings remain pending for recovery.

Machinery admission: matching and re-checking the PR base/head pair uses a bounded local fetch and automatic successor recovery, not an operator-blocking gate; witness: one staged review reused after the PR head advanced with a later retry-path change unreviewed (origin row); catch frequency unknown with one witnessed instance; false-positive cost is one ref refresh and, only for a moved scope, a full or verified-delta successor; review by 2026-12-02, tracked as a `duty:` row in `scripts/machinery_registry.json` added by Task 4 with a removal-or-promote commitment.

## Assumptions

- assume the local base/head OIDs used to derive the diff can be compared to `gh pr view --json baseRefOid,headRefOid`; basis: the local GitHub CLI help lists both JSON fields, and this adds no new PR workflow contract.
- assume the shared PR context query stays owned by `github-pr-workflow`; basis: `doing-code-review` directs GitHub PR operations to that skill's shared primitives.
- assume `github-pr-workflow` owns shared base/head and digest capture and rechecks; `doing-code-review` owns mode orchestration and moved-scope recovery, while `review-staging` owns the Metadata format; basis: those files own PR mechanics, consumer workflow, and record shape respectively.
- assume the OID lines remain unvalidated Metadata context and do not extend the sidecar schema; basis: the incident can be addressed through the existing `source_digest` and record format.
- assume the five-worker panel and the finding budget stay unchanged; basis: origin row and `review-agents/review-panel-selection.md`.
- assume `scripts/runtime-scripts.list` remains the deployment source of truth and the real-repository verifier is the acceptance witness for imported sibling closure; basis: `scripts/deploy_runtime_helpers.sh` and `scripts/test_deploy_runtime_helpers.py`.
- Decision receipts: stale-head recovery, the coverage-evidence floor, legacy-record identity handling, and the archive-backed Copilot/review finding inventory are recorded in the Decision points trailer below (single home).

Decision points requiring a grill: head-only stale-scope recovery (full re-review vs verified delta vs orchestrator choice) resolved to orchestrator choice, with delta allowed only when the base is unchanged; any base move requires full re-review because the head delta does not cover it, source origin row Suggested direction 1 plus r1 panel adjudication, 2026-11-02, affected sections Gist & Examples, Outcome, Tasks 1-2; Coverage-evidence floor adjudicated to worker-prompt text and inherited coverage in delta successors, not a staging validator field, 2026-11-02, affected sections Outcome, Task 3; legacy records missing either historical OID remain unverified even when today's digest matches, because the digest cannot establish the historical identity pair, full successor review chosen, r7 plan-review finding F1, 2026-11-03, affected sections Terms, Gist & Examples, Outcome, Task 2; later PR finding inventory adjudicated from local archives and exact reviewed/submitted head comparison: r3 contains five staged findings covering numeric PII pass-through, conditional Feign body logging, raw deserialization logging, batch-wide sibling redelivery, and malformed gift metric tags; the PII, raw parse, and gift-tag behavior changed after the first reviewed snapshot, batch-wide redelivery was already in scope, and the Feign response-body sensitivity remains unverified; r2 combines two Copilot gift-tag comments and r1 separately records terminal-hook thread 4445741127, so do not assert an exact Copilot count or authorship beyond those records, local archives and source comparison, 2026-11-03, affected sections Why, Gist & Examples, Task 3; Direct Mode's pre-post baseline is the matched pair and digest captured before workers, kept as run state until the post-send staging record persists it; writing the record before posting would violate Direct Mode's defined order, r10 contract-docs finding F1 and existing Direct Mode flow, 2026-11-03, affected sections Terms, Gist & Examples, Outcome, Task 1, Validation Commands; the 4.5h estimate exceeds the 3.0h sizing advisory, but the scope stays one plan because the PR identity, recovery, record, and evidence updates form one review lifecycle with shared validation and no separately deployable safe-ship phase, plan author decision, 2026-11-03, affected sections Gist & Examples, Tasks 1-4.

## Standing constraints

- `agents/skills/doing-code-review/SKILL.md` and `agents/skills/review-staging/SKILL.md` are pinned by `scripts/check_maintenance_pins.sh`: an edit that moves or breaks a pinned span updates that span's mirror inside `scripts/check_maintenance_pins.sh` in the same commit, and each new operative span this plan adds to a pinned file gains its companion pin in the same edit.
- Skill text stays tool-agnostic and imperative, matching the surrounding file's density and idiom.
- No em dash (U+2014) in any added line.

## Evaluation Criteria

- Correctness: every edited location is real, verified by grep before certification (`github-pr-workflow` PR context query; `doing-code-review` PR diff preparation and both posting paths; `testing.md` Coverage Claim Audit; `quality.md` Correctness; `security.md` Sensitive Data Handling and Data Leakage; `concurrency.md` Ownership and decision matrix; review-staging Metadata Review context; the machinery registry rows; runtime sibling admission).
- Consistency: the new terms each have one definition home; greping the edited files shows no contradicting wording against the existing `Source digest` recompute rule, the review-panel-selection five-worker policy, or the rule that current diff bytes cannot establish missing historical OIDs.
- Gates: maintenance pins, hygiene, review-agent portability and doors pass; the venv-backed focused runtime tests and `python3 scripts/machinery_inventory.py --check` exit 0; added lines carry no em dash.

Done when: the edits are committed on the run branch, the gates above are green, the full repository-standard suite passes, and the branch diff contains exactly the Review Scope paths plus this plan document.

Ship when: none (repository-internal process text; no external release surface).

## Tasks

### Task 1: PR scope identity and pre-post check in doing-code-review

Files:
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/github-pr-workflow/SKILL.md`
- `scripts/check_maintenance_pins.sh` (companion pins beside any moved pinned span)

Context surfaces: the Terms dictionary (base/head identity lines and pair, pre-post scope check) and the Standing constraints section.

- [x] Given a PR diff ready for review, capture the exact local base/head OIDs and compare them with resolved PR `baseRefOid` and `headRefOid`; expect both pairs to match before workers start. [class: IMPLEMENTATION_REQUIRED]
- [x] Given differing local/PR OIDs, refresh both into temp refs and re-resolve once; launch on a match or recover in a successor. Explicit pet-target authorization permits only read-only PR queries and temp-ref fetches, never writes. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the shared PR context query, request `baseRefOid` beside `headRefOid`; expect the resolved pair to drive initial binding and pre-post comparison. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a staged PR review, record the captured matched OID pair and resolution times in Metadata before posting; given Direct Mode, retain that tuple as run state until its post-send record is written. Expect neither mode to post without a captured baseline or produce an unbound record. [class: IMPLEMENTATION_REQUIRED]
- [x] Given each PR posting call in staged or Direct Mode, re-resolve both OIDs and recompute the reviewed-scope digest; expect a match against the captured baseline, plus the staged record when it exists, before posting. Bind submission to the captured head and re-resolve both PR OIDs afterward; expect `POSTED` only when the response and pair match, otherwise `STALE` with findings pending. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a pre-post OID or digest mismatch, refresh the PR refs and context once; expect no old-scope post and automatic Task 2 successor recovery after a second mismatch. Given a post-submission or retry-time stale result, expect retries to stop immediately, all findings to remain pending under `STALE`, and successor recovery to begin without reposting old-scope comments onto the newer PR. [class: IMPLEMENTATION_REQUIRED]

### Task 2: moved-scope recovery and legacy identity handling in doing-code-review

Files:
- `agents/skills/doing-code-review/SKILL.md`
- `scripts/check_maintenance_pins.sh` (companion pins beside any moved pinned span)

Context surfaces: the Terms dictionary (verified delta review, delta scope evidence, moved-scope disposition line) and the record selection helper's new-round, mark-superseded, recover-orphan, and verify-digest surfaces.

- [x] Given a resolved moved-scope comparison, record at successor allocation the old/new base and head OIDs, chosen arm, and any applicable head delta range and materialized diff location; given unresolved identity or digest, record the reason, omit OID and delta fields, and require full re-review. Expect the recovery basis to be auditable before work begins. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a head-only move with unchanged base, allow full or verified delta review; given a moved or unverifiable base, expect full re-review because the head delta omits the base change. [class: IMPLEMENTATION_REQUIRED]
- [x] Given either recovery arm, allocate a new-round successor through the record selector, back up the predecessor and record the helper's printed path in successor Metadata, bind its digest to the full new reviewed scope, and write the moved-scope disposition before recovery work; after the successor is staged, mark the predecessor superseded. Expect the old record to remain immutable and never be posted as current. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a delta successor, carry prior findings with triage statuses, adjudicate delta-anchored findings as keep/revise/drop, and carry findings outside the delta unchanged; expect every prior finding to have an explicit disposition. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a delta successor, preserve unchanged-scope coverage in `coverage.inherited_coverage` with prior artifact and sidecar links and add fresh delta coverage; given a full review, expect no inherited coverage. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a full re-review, derive findings and coverage for the complete new scope; expect no prior finding or coverage to be carried forward. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a legacy PR record missing either OID identity line, recompute the current reviewed-scope digest using the canonical verify-digest derivation over `git diff <base>...<head>` and the reviewed-scope path filter; expect the digest to establish current bytes only, not historical OID identity. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a legacy digest matching today's reviewed scope, do not fill historical OID lines or post the old record; allocate a full-review successor with its current pair captured before workers start, then post only the successor if its pre-post check passes. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a missing legacy OID, unclassifiable OID change, or digest mismatch that cannot be resolved by a verified delta successor, record the failure and require full re-review; never post a legacy record as current. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a sidecar-less or orphan-half prior record, route it through the record selection helper's `recover-orphan` subcommand before new-round allocation; expect a valid successor allocation without treating missing provenance as verified. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a base or head move after the final check and before posting, document the bounded read-only residual window; expect no claim that the check is atomic with posting. [class: IMPLEMENTATION_REQUIRED]

### Task 3: data-flow, batch-retry, and coverage evidence in worker prompts

Files:
- `agents/skills/review-agents/testing.md`
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/security.md`
- `agents/skills/review-agents/concurrency.md`

Context surfaces: the Terms dictionary (coverage citation, metric trace, cross-path identifier claim); security's Sensitive Data Handling and Data Leakage; concurrency's Ownership and decision matrix.

- [x] Given changed mapping, fallback, identifier, sensitive-data transformation, or serialization behavior, extend `## Coverage Claim Audit` in `agents/skills/review-agents/testing.md` to name each contract-relevant input and runtime representation partition, including blank/absent values and non-string values when accepted by the contract; expect no coverage claim to rely on a single happy-path representation. [class: IMPLEMENTATION_REQUIRED]
- [x] Given each claimed partition, cite a test and its assertion in the Evidence requirement shape or mark it uncovered; expect prose-only coverage claims to remain unproven. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a test expecting recognized PII to pass unprotected or another outcome contrary to contract, compare assertion with the contract; flag unsafe output instead of counting it as evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] For sensitive-data changes, trace protected fields through conversion, serialization, outbound payloads, and failure/log sinks; inspect throwable rendering and name every reachable path. [class: IMPLEMENTATION_REQUIRED]
- [x] For a possible response-body leak, require evidence that sensitive content reaches a log; otherwise keep the concern conditional. [class: IMPLEMENTATION_REQUIRED]
- [x] For batched retries, distinguish `MQMessage.retryTimes` from broker attempts; cite pinned client behavior for callback failure, acknowledgement, replay, and retry budgets, or mark unknown. [class: IMPLEMENTATION_REQUIRED]
- [x] When batch failure follows sibling side effects, trace order and require replay evidence plus an idempotency guard, or mark replay/guard unknown. [class: IMPLEMENTATION_REQUIRED]
- [x] Extend `## Correctness` in `agents/skills/review-agents/quality.md`: given a changed terminal outcome feeding multiple metrics, trace every emitted metric and cite branch evidence for each leg; expect metric definitions alone not to prove an omission. [class: IMPLEMENTATION_REQUIRED]
- [x] Given malformed-message metric tags, extend `## Correctness` to trace tag hooks and fallback; require evidence of documented `unknown` tags or mark uncovered. [class: IMPLEMENTATION_REQUIRED]
- [x] Compare cross-path IDs only with evidence of the same record and time scope; otherwise withhold defect/dedup claims and mark the relationship unverified. [class: IMPLEMENTATION_REQUIRED]
- [x] Run changed prompts on numeric PII, pre-protection parse failure, an unverified Feign body, README-only ID equality, and batch callback failures; require citations, conditional wording, or explicit unknown/uncovered outcomes. [class: IMPLEMENTATION_REQUIRED]
- [x] Given each targeted worker prompt, compare new instructions with its nearest existing rule; merge into or replace overlapping text and remove wording that is redundant or superseded, keeping genuinely new text minimal. Expect no duplicate operative instruction. [class: IMPLEMENTATION_REQUIRED]
- [x] Given changes to skill files, run the focused panel selected by the existing panel-selection policy against the exact combined staged and unstaged diff before commit; expect the review to gate the commit only. [class: IMPLEMENTATION_REQUIRED]

### Task 4: review-staging Metadata and machinery registry

Files:
- `agents/skills/review-staging/SKILL.md`
- `scripts/check_maintenance_pins.sh` (companion pins beside any moved pinned span)
- `scripts/machinery_registry.json`

Context surfaces: the Terms dictionary (base/head identity lines, moved-scope disposition) and the registry's existing two-row convention (`duty:review-staging-series-sweep` precedent).

- [x] Given the staging Metadata `Review context`, document optional base/head identity lines and moved-scope disposition as the single format home for PR records; expect the lines to remain unvalidated and be cited by `doing-code-review`. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the witnessed stale-post incident, add `entries` duty row `duty:doing-code-review-pre-post-scope-check` with unknown frequency (one witnessed instance), false-positive cost, 2026-12-02 review date, and removal-or-promote commitment; expect the row to satisfy the existing registry schema. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the duty witness, point it to this plan's living path and at completion re-point it to the archived twin when deleting the origin row; expect no dangling witness after archival. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the new duty, add the paired `removals` row naming Task 1-2 scope checks and fallback, Metadata lines, companion pins, and both registry rows; expect the 2026-12-02 sunset and promote-on-true-catch criteria to remain aligned. [class: IMPLEMENTATION_REQUIRED]

### Task 5: close runtime registration gaps found by Phase 2

Files:
- `scripts/runtime-scripts.list`
- `scripts/machinery_registry.json`

Context: quota probe imports `quota_sources.py`; the inventory gap has two live modules. Introduction commits: `44f9499a545a5efb7bf84d2383b06d927b23d4b3` and `137c50ebda8f568e5a677a55e29df53fe887a97f`, respectively.

- [x] Given the two live unregistered modules, add keep entries with consumer tests, the existing backlog as incident witness, and each introduction commit in its note; when the origin is deleted, repoint both witnesses to the archived plan twin and retain the origin path and commits in notes. Inventory check passes before and after archival. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the deployed quota probe imports its local source module identified above, admit that sibling in `scripts/runtime-scripts.list`; expect the real-repository deployment and verification test to report no closure gap or probe failure. [class: IMPLEMENTATION_REQUIRED]

## Validation Commands

- Run the executable checks from the repository root:

```bash
bash scripts/check_maintenance_pins.sh || exit 1
bash scripts/scan-public-hygiene.sh || exit 1
python3 scripts/check_review_agent_portability.py || exit 1
python3 scripts/test_review_agent_doors.py || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_deploy_runtime_helpers.py::DeployRuntimeHelpersTest::test_real_repo_deploys_and_verifies_clean scripts/test_machinery_inventory.py::RealTreeCheck::test_real_tree_checks_green -q || exit 1
~/.ai-playbook/scripts/check-no-em-dash.sh added-lines --base main -- docs/history/plans/2026-11-02-review-freshness-and-code-coverage-gaps.md agents/skills/doing-code-review/SKILL.md agents/skills/github-pr-workflow/SKILL.md agents/skills/review-agents/testing.md agents/skills/review-agents/quality.md agents/skills/review-agents/security.md agents/skills/review-agents/concurrency.md agents/skills/review-staging/SKILL.md scripts/machinery_registry.json scripts/check_maintenance_pins.sh || exit 1
```

Separately run `python3 scripts/machinery_inventory.py --check`; it must exit 0 after Task 5 registers both live scripts.

Run each changed worker prompt against the sample contexts below. A sample passes only when the response meets its stated observable checks; an omitted branch or unsupported conclusion fails the sample.

### Sample-response checks

- Posting lifecycle: record branch/HEAD/index/worktree. Target facts override skill-checkout facts; on a pet target, explicit user permission allows read-only PR queries and temp-ref fetches, never writes. Exercise matching/stale/unresolved refs; one refresh then a second failed pre-post check; head/base moves during submission; complete/partial comments despite scope failure; retry-time movement. Refresh preserves checkout; workers use matching refs. A second failed pre-post check means no post, no `STALE`, and successor recovery. Bind to captured head; after sending compare response `commit_id` and both OIDs. Only full match permits `POSTED`; post-submit/retry movement stops retries, keeps findings pending under `STALE`, and enters successor recovery despite landed comments. Current-scope missing comments after bounded retries are `INCOMPLETE`. Never retry on newer head. Staged uses record; Direct uses then persists its tuple.
- Legacy and delta records: give the prompt a legacy record missing an OID but with a matching current digest, then a verified head-only delta with prior coverage. Expect the old record never to post, the legacy case to use a full successor, and the delta successor to preserve unchanged-scope coverage through `coverage.inherited_coverage` while adding fresh delta coverage.
- Testing evidence: enable PII protection and provide a test that expects a recognized numeric PII value in plaintext. Expect the worker to call the assertion unsafe and refuse to count it as evidence. Provide blank, absent, and populated business IDs with a fixed trace ID. Expect the populated ID to produce `<eventName>:<businessId>` and blank or absent IDs to produce `<eventName>:<traceId>`; require each case's assertion or mark it uncovered, and reject any other expected value.
- Metric evidence: provide a rejected-result branch that emits both its rejected-result metric and the legacy success counter, with a test asserting only one emission. Expect the response to name both metric branches, cite evidence for each, and flag the missing assertion; a response that names only one metric fails.
- Metric-tag evidence: provide malformed gift payloads whose fixed event/activity hooks produce ordinary gift tags although the operational guide requires `unknown` on parse failure. Expect the response to cite the tag hook and safe-wrapper branches plus a test assertion for `unknown`, or mark the behavior uncovered; outcome-counter coverage alone does not pass.
- Security and identifier evidence: trace a numeric protected value through transformation, serialization, transport failure, and logger rendering; include a parse failure before protection, a raw deserialization throwable reaching a logger, a Feign response body whose sensitivity is unverified, and separate live and baseline identifiers where only the README states their relationship. Expect the worker to trace the throwable sink, keep the response-body concern conditional without sensitivity evidence, and withhold the cross-path deduplication claim unless the same-record and time-scope relationship is established.
- Batch retry evidence: pin the first sample to submitted head `be5124fa59dad476a31ea9da84f810bbcc898ecc`. At `retryTimes = 4`, require the response to trace the terminal hook throwing, `onMessage` routing the exception to `handleException`, `handleException` rethrowing, and the concurrent batch adapter returning `RECONSUME_LATER`; reject a normal-return or acknowledgement claim for these bytes. A separately labeled post-fix case may show a returning terminal hook being acknowledged. In the second batch, one item has `retryTimes = 3` and throws after an earlier sibling emitted an external side effect; require evidence from the pinned RocketMQ client contract for whether that sibling is replayed, an idempotency guard for each replayable side effect, or an explicit unknown/uncovered result. Distinguish broker reconsume attempts from application retry counts. Inferring either path from batch size or retry threshold alone fails.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Review machinery:**
- `agents/skills/doing-code-review/SKILL.md` (Task 1) (Task 2)
- `agents/skills/github-pr-workflow/SKILL.md` (Task 1)
- `agents/skills/review-agents/testing.md` (Task 3)
- `agents/skills/review-agents/quality.md` (Task 3)
- `agents/skills/review-agents/security.md` (Task 3)
- `agents/skills/review-agents/concurrency.md` (Task 3)
- `agents/skills/review-staging/SKILL.md` (Task 4)
- `scripts/machinery_registry.json` (Task 4) (Task 5)
- `scripts/runtime-scripts.list` (Task 5)
- `scripts/check_maintenance_pins.sh` (companion-pin additions only) (Task 1) (Task 2) (Task 4)

**Tests:** no new automated test files; `scripts/test_deploy_runtime_helpers.py` and `scripts/test_machinery_inventory.py` are review-only witnesses for Task 5. Use the bounded realistic-context scenarios in Validation Commands alongside the existing gates.

**Non-goals (out of scope, findings here are not blocking):**
- `agents/skills/review-agents/review-panel-selection.md` (panel composition unchanged)
- any validator schema or descriptor change in `scripts/validate_review_staging.py`
- any automated blocking gate, new worker, or finding-budget change

**Expected diffusion:** only the Review Scope paths; a pins-suite failure naming a pinned span moved by these edits is fixed by updating the span's mirror in the same commit.
## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-02-review-freshness-and-code-coverage-gaps.md`: covered by this plan; the origin row is deleted in this completion pass. The implementation landing is recorded under the plan history for 2026-11-04.
- `docs/history/backlog/2026-11-02-machinery-inventory-regrowth-two-runtime-scripts.md`: covered by Task 5, which registered both live runtime scripts and pinned the green inventory check; the origin row is deleted in this completion pass.
