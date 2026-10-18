# Plan: execute-plan review wave contract gaps

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-execute-plan-review-wave-budget-gate-order.md`
- `docs/history/backlog/2026-10-05-execute-plan-review-ignores-recorded-scope-deferral.md`
- `docs/history/backlog/2026-10-05-execute-plan-stale-review-digest-after-closeout.md`

Driving force: reliability (three witnessed 2026-10-05 review-wave failures across one live execution's Phase 3: a five-worker panel and its address wave launched after the boundary commit without their own Budget gate receipt, a risk worker's blocking finding against a capability the plan explicitly defers to an owning backlog item had to be reconciled by the parent after the panel returned because the panel input carried no scope summary, and a closeout commit changed reviewed-scope bytes leaving the saved review record implying freshness it no longer had until an independent recomputation caught it; every Phase 3 review wave in every execution crosses these three duties, so each gap taxes every reviewed run)

Plan review record: the staging series docs/reviews/2026-10-05-plan-review-execute-plan-review-wave-contract-gaps-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Review wave: one launch cohort of a Phase 3 review round (the lens panel, or the receiving-review address wave that follows it); a round may contain several waves, each an independent launch boundary.
- Budget gate: the execute-plan skill's quota-window pause protocol (its Budget gate section); a gate run at a boundary prints a probe decision (`continue` or a pause) that is the boundary's admission evidence.
- Wave-budget receipt: the per-wave session-manifest line this plan defines (superseding the existing `wave_boundary_probes` outcome line), recording the wave boundary's own probe decision beside the review digest and the wave's pre-launch identifiers, which the launch record echoes forward to close the probe-to-launch link.
- Session manifest: the run's `manifest.md` under `{tmp_dir}/execute-plan/<PLAN_SLUG>/`, the orchestrator-maintained run record the heartbeat and closeout duties already read.
- Scope summary: the per-round must-fix versus out-of-scope list the parent assembles from the plan's scope declarations, recorded user decisions, and the backlog origins the plan cites as owners of deferred work; carried in the panel input.
- Out-of-scope adjudication: the triage disposition for a staged finding whose subject the plan explicitly defers: recorded with the owning backlog reference, never promoted to a blocking gate for this execution, never duplicated as a new backlog row.
- Reviewed-scope digest: the digest of the reviewed bytes a round's sidecar records as `source_digest`; for execute-plan code-review rounds it is derived from the run's diff over the recorded base commit.
- Digest freshness check: the continuation-and-terminal-boundary recomputation that compares the current reviewed-scope digest against the latest round's sidecar `source_digest` before any synthesis or terminal evaluation reads that record.
- Stale record: a review record whose sidecar `source_digest` differs from the freshly recomputed reviewed-scope digest at a boundary; it is not current evidence until re-bound through the supported corrections arm or superseded by a fresh round.

## Why

One live execution launched review waves the way the skill text read, and the skill text had three holes the run fell through: the Budget gate was read as a per-run formality rather than a per-wave admission receipt, the panel input named the plan path without carrying what the plan actually defers, and nothing between rounds re-checked that the reviewed bytes were still the reviewed bytes after a closeout commit. Each row's refused path already fails safe (the missing probe left no false evidence, the parent's after-the-fact reconciliation discharged the finding, the stale digest was caught before triage); what is missing is the contract that makes the failure shapes impossible to enter silently: an admission receipt per wave, a scope summary in every panel input, and a mechanical digest check at every boundary that reads a review record. The three rows share the execute-plan review-orchestration seam and one session manifest, so one plan lands the contract coherently.

## Outcome

- Every review wave launches only behind its own recorded Budget gate receipt: the session manifest carries a per-wave receipt line binding the probe decision to the review digest and the wave's pre-launch identifiers, which the launch record echoes forward, a prior round's probe never authorizes a later wave, and a wave discovered to lack its receipt stops before workers launch.
- Every panel input carries the scope summary: the parent assembles the must-fix versus out-of-scope list from the plan's own declarations and cited backlog owners, the lens-worker template carries it as a first-class input block, out-of-scope findings triage with the owning reference instead of blocking this execution or duplicating backlog rows, and the adjudication is visible in the run's records.
- Every boundary that reads a review record verifies its digest first: a mechanical `verify-digest` operation recomputes the reviewed-scope digest from the recorded base and compares it to the sidecar, refusing stale with both digests named; the orchestrator runs it at every continuation and terminal boundary, records the check, and the terminal gate refuses completion over a stale latest record.

Gate delta: one new session-manifest line format (the wave-budget receipt), one new panel-input placeholder block, one triage rule (out-of-scope adjudication with the owning reference), and one new selector subcommand with its refusal set (absent record, orphaned record without its sidecar, sidecar without a `source_digest` string, digest mismatch, HEAD movement past the recorded head, and the named accepted-stale pass outcome for corrections-carried records). All are report-and-refuse duties over artifacts the orchestrator already maintains; no existing gate weakens: the Budget gate's pause protocol, the graded Phase 3 exit, the five-round budget, and the selector's existing subcommands keep their semantics, and the digest check reuses the selector's source_digest reading and the canonical corrections-graded diff derivation rather than inventing a second freshness notion.

## Assumptions

- assume authoring runs unattended under the standing operator directive, so Step 1.4 confirmation is satisfied by the rows' validated records rather than a live interview; basis: the maintenance loop's authoring blueprint (loop_mode dual, continuous pacing amendment 2026-09-30).
- assume the wave-budget receipt lives as a line in the session manifest rather than a new state file; basis: the session manifest is the orchestrator-maintained run record the heartbeat, closeout, and budget-pause duties already read, and a per-wave line extends it without new machinery.
- assume the receipt's probe decision comes from `scripts/quota_window_probe.py` (the Budget gate's own probe), and the receipt binds the probe's decision plus timestamp, the selected review digest (the round's sidecar `source_digest` or the pre-round digest at selection), and the wave's pre-launch identifiers (review round, wave ordinal, re-entry count) because no attempt id exists before workers launch; basis: the origin row's Expected names the probe-to-digest-to-attempt link, and the attempt identifier is a post-launch artifact, so the pre-launch identifiers are the binding's attempt-side value with the launch record echoing them forward.
- assume the scope summary is assembled by the parent from the plan text alone (its scope declarations, recorded decisions, and cited backlog origins), stated once per round in the session manifest beside the round entry, and carried into every lens prompt of that round; basis: the witnessed gap was the panel input, the plan is the scope-of-record, and the briefing file already carries decisions but is advisory context, not the adjudication witness.
- assume out-of-scope adjudication triages as the existing `dropped` disposition with the owning backlog reference recorded in the finding's consequence and the round's synthesis, reusing the closed triage vocabulary rather than adding a new value; basis: the review-plan skill's cap-closure region pins the resolved vocabulary and the finding-conservation arms, and a new value would be a schema migration the row does not ask for.
- assume the digest freshness check is a selector subcommand because the selector already owns source_digest reading, sidecar pairing, and the fail-closed posture for exactly these records; basis: `_read_sidecar_source_digest`-shaped helpers exist in `scripts/review_record_selection.py` and the origin row's recomputation recipe (current diff over the recorded base) matches the derivation the run used at round start.
- assume the terminal gate's refusal rides the existing Phase 5 checklist and the terminal-response gate's freshness arm rather than a new driver operation; basis: the execute-plan skill already refuses completion when review freshness is invalid, and this plan gives that refusal its mechanical instrument.
- assume Task 3's `verify-digest` accepts the base commit and record path as caller inputs and never derives them from context; basis: cycle-2's review-record plan pinned the same explicit-input shape for `recover-orphan` after its reviewer caught the stem-derivation ambiguity.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: every Phase 3 review wave launches behind its own recorded Budget gate receipt, every panel input carries the plan's must-fix versus out-of-scope summary, and every boundary that reads a review record verifies its digest mechanically first.

Before (today): a panel launches at a wave boundary whose last Budget gate run belongs to an earlier round, so no evidence ties the launch to an admission decision. A lens worker stages a blocking finding against a capability the plan defers to a cited backlog item, and the parent reconciles after the fact. A closeout commit changes reviewed-scope bytes, and the saved round record implies freshness until someone independently recomputes the digest.

After (this plan): the wave's receipt line lands in the session manifest before the first worker of that wave launches, naming the probe decision, the review digest, and the wave's pre-launch identifiers that the launch record echoes forward. The panel input opens with the scope summary, and out-of-scope findings triage as dropped-with-reference instead of blocking. `verify-digest` recomputes and compares at every continuation and terminal boundary, refusing stale with both digests named, and the check is recorded before synthesis or terminal evaluation reads the record.

Edge cases pinned: a wave receipt recorded after workers launched is a recorded miss, not retroactive admission; a pause decision at a wave boundary stops the wave per the Budget gate's pause protocol; a round with no out-of-scope content carries an empty scope summary rather than omitting the block; a finding whose subject is out of scope but whose fix would touch in-scope bytes adjudicates on the plan text and records the residual risk; verify-digest on an unreadable or unpaired record refuses; verify-digest after a genuinely fresh round passes and the pass is recorded; a stale latest record at the terminal boundary refuses completion naming the stale digest pair.

## Tasks

### Task 1: Per-wave Budget gate receipts in the session manifest

Files:
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the pinned-span criterion for reworded skill spans (a pinned span reworded by this task records a pin-rekey follow-up receipt in the session notes instead of a same-edit pins change when the pins file is outside this task's Files list)
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-05-execute-plan-review-wave-contract-gaps.md`; structural gate

- [x] Skill text, wave-receipt duty: the Budget gate section and the Phase 3 round procedure in agents/skills/execute-plan/SKILL.md upgrade the existing per-wave probe record into the admission receipt: the `wave_boundary_probes` manifest line contract is superseded by the wave-budget-receipt line carrying the decision, the watcher id, the review digest, the pre-launch wave identifiers, and the timestamp, and the Budget gate section's probe-only sentence (a continue needs no additional bookkeeping beyond the outcome line) is amended in the same edit so one contract remains: each review wave (lens panel and receiving-review address wave alike) runs the Budget gate at its own boundary and records the receipt in the session manifest BEFORE any worker of that wave launches; a prior round's probe never authorizes a later wave, a receipt recorded after workers launched is recorded as a miss with the remediation (stop, probe, record, relaunch), a pause decision at a wave boundary stops the wave per the existing pause protocol, and the Step 3.1 launch record echoes the receipt's pre-launch identifiers forward so the probe-to-launch link is closed on both sides [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text, manifest format: the session-manifest region of agents/skills/execute-plan/SKILL.md (which owns the manifest's existing line contracts) documents the wave-budget-receipt line beside its other record formats, and the Phase 5 checklist gains the completeness arm: the terminal gate refuses completion when any launched wave lacks its receipt line or its recorded miss [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: review waves record their own budget receipts before launch` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Scope summary in panel input and out-of-scope triage

Files:
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-05-execute-plan-review-wave-contract-gaps.md`; structural gate

- [x] Prompt template, scope block: the Review lens worker template in agents/skills/execute-plan/subagent-prompts.md gains the `<SCOPE_SUMMARY>` input block beside the run-briefing citation, and the shared placeholder table gains the matching `<SCOPE_SUMMARY>` row in the same edit: the parent-assembled must-fix versus out-of-scope list with the owning backlog reference per deferred capability, and the worker instruction that a finding whose subject the summary marks out of scope is reported as out-of-scope-adjudicated (naming the owning reference and the residual risk) rather than as blocking for this execution [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text, summary assembly: the Phase 3 round procedure in agents/skills/execute-plan/SKILL.md gains the assembly duty: per round, before the first lens launches, the parent assembles the scope summary from the plan's scope declarations, recorded user decisions, and cited backlog origins, records it in the session manifest beside the round entry, and states it once per round; a round with no deferred content records an empty summary rather than omitting the block [class: IMPLEMENTATION_REQUIRED]
- [x] Triage rule: the Phase 3 triage step of agents/skills/execute-plan/SKILL.md (Step 3.2, the surface that owns code-review triage for this loop) gains the out-of-scope adjudication rule: a staged finding whose subject the scope summary marks out of scope triages as `dropped` in the sidecar triage field (the staging Status token spells the same disposition `drop`) with the owning backlog reference in the finding's consequence and the round's synthesis, is never promoted to a blocking gate for this execution, and never creates a duplicate backlog row where the cited owner exists (the owning reference recorded in the finding's consequence satisfies the Step 3.2 backlog-capture requirement of the not-fixed table row and the skip-path sentence; only a finding whose out-of-scope subject has no cited owner takes the ordinary durable-backlog-item path); residual risk stays recorded in the consequence; review-plan's own loop is out of this plan's scope (it governs plan-review rounds, which receive the full plan and no scope summary) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: review panels carry the scope summary and triage deferrals with references` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Mechanical digest freshness check at record-reading boundaries

Files:
- `scripts/review_record_selection.py`
- `scripts/test_review_record_selection.py`
- `agents/skills/execute-plan/SKILL.md`

Evidence:
- `python3 scripts/test_review_record_selection.py`; covers every criterion below at the task boundary (main-shim suite)
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks

- [x] `test_verify_digest_match_and_mismatch` (given a record pair whose sidecar `source_digest` equals the freshly recomputed reviewed-scope digest over the recorded base and whose HEAD matches the round's recorded head, expects `verify-digest` to exit 0 printing the pass receipt with the digest values and the verified HEAD; given a base whose recomputed digest differs, expects exit 1 with the named stale refusal carrying the recorded and recomputed digests and the record path; given a HEAD move past the round's recorded head that leaves the reviewed-scope bytes identical, expects the HEAD-movement refusal the origin row's binding asks for) [class: REPOSITORY_TEST]
- [x] `test_verify_digest_refusals` (arms: an absent record refuses; a canonical Markdown without its sidecar refuses per the existing orphan posture; a sidecar without a `source_digest` string refuses per the existing read helper's failure mode; every refusal is a named one-line error mutating nothing) [class: REPOSITORY_TEST]
- [x] Implement the `verify-digest` subcommand in scripts/review_record_selection.py taking `--record <staging md>`, `--dir <reviews dir>`, `--base <commit>`, and `--expect-head <commit>` (all explicit caller inputs, never derived), recording the verified HEAD beside the digest comparison in the outcome so a HEAD move past the round's recorded head refuses even when the reviewed-scope bytes are unchanged, with the precedence pinned: a verified corrections chain terminating at the current bytes supersedes the HEAD-movement refusal (the accepted-stale pass names both heads, the chain's after-head being the movement), and the caller passes as `--expect-head` the latest recorded verified head from the session manifest or the chain's after-head; recompute the reviewed-scope digest over the base commit with the canonical diff-bytes derivation (`git diff <base>...<head>` bytes hashed with SHA-256, the same shape `scripts/corrections_record.py`'s diff_bytes plus sha256 helpers produce and the seal validator grades against, invoked identically or imported), compare against the sidecar's `source_digest` through the existing read helper, and print the named pass or stale-refusal outcome; the subcommand mutates nothing [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text, boundary checks: agents/skills/execute-plan/SKILL.md's Phase 3 round procedure and the Phase 5 checklist gain the freshness duty: at every continuation boundary (resume, post-closeout-commit) and before terminal evaluation, the orchestrator runs `verify-digest` against the latest round's record, records the pass or refusal in the session manifest, and on stale treats the record as not current evidence (a fresh round on the recomputed digest, or the supported corrections arm where the staging validator owns it); verify-digest consults that corrections ownership rather than raw exact-match only: when the record carries a verified corrections chain that terminates at the current bytes, the outcome is a named accepted-stale pass instead of a refusal, so corrections-carried records do not verify permanently stale; the terminal gate refuses completion over a stale latest record without such a chain, naming the digest pair [class: IMPLEMENTATION_REQUIRED]
- [x] Round-close cross-reference: the execute-plan round-close seal region of agents/skills/execute-plan/SKILL.md cites `verify-digest` as the boundary freshness instrument for code-review records beside its existing seal duties (one sentence scoped explicitly to code-review records; plan-review record freshness stays owned by the review-plan mechanical gate's `--source-plan` check, and the procedure is not restated) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full suite, the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: verify-digest recomputes review freshness at record-reading boundaries` [class: IMPLEMENTATION_REQUIRED]

## Review Scope

Files in scope (the union of the task Files lists): `agents/skills/execute-plan/SKILL.md`, `agents/skills/execute-plan/subagent-prompts.md`, `scripts/review_record_selection.py`, `scripts/test_review_record_selection.py`.

Reviewers judge: fail-closed preservation (the Budget gate's pause protocol, the graded Phase 3 exit, the five-round budget, and the selector's existing subcommands keep their semantics), the receipt and digest mechanisms' auditability (per-wave not per-round, recorded before launch, both digests named on stale), the scope-summary assembly's determinism (plan-derived, stated once per round, empty over omitted), the triage rule's coherence with the closed vocabulary and the finding-conservation arms, scope discipline (no task reaches beyond its Files list), and test reality (every criterion has a named test runnable in this repository).

## Validation Commands

```bash
python3 scripts/test_review_record_selection.py
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-execute-plan-review-wave-contract-gaps.md
```
