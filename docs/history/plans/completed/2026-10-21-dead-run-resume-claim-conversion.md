# Plan: Restore dead-run claim conversion from canonical manifests

Backlog origin: docs/history/backlog/2026-10-20-dead-execution-run-resume-in-own-worktree-no-claim-conversion.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-dead-run-resume-claim-conversion-p65513e2d-r*.md
Authoring claim: docs/tmp/authoring-claims/2026-10-20-dead-execution-run-resume-in-own-worktree-no-claim-conversion.md (session 01a15484-176a-70a1-814d-785fd68e1975)

## Terms

- **Arm 3**: the execution-claim gateway path that recognizes a same-run resume from its registered worktree.
- **Phase 0**: execute-plan setup before task execution, when the run adopts or creates its worktree and records its session manifest and claim.
- **Branch-occupant gate**: the `take` check that preserves a stale claim and refuses takeover when another registered worktree occupies the claim's branch.
- **Claim conversion**: transferring an existing plan claim to a resuming session through the existing `take` command.
- **Run manifest**: `{tmp_dir}/execute-plan/<plan-slug>/manifest.md`, resolving `{tmp_dir}` from the `.ai-playbook/facts.md` in the specific registered worktree being inspected. Missing or unreadable facts refuse discovery; never substitute `docs/tmp`.
- **Canonical plan path**: the repository-relative value stored in `plan_path:` and compared literally with the normalized claim operand.
- **Manifest identity**: accept canonical `session_id:` plus exact `plan_path:`; legacy `Session:` plus `Plan:`; or legacy `session_id:` alone when the claim supplies exact `plan:`. `run_session_id:` is immutable origin identity, initialized from `session_id` and recovered from the verified prior owner when absent; `session_id` remains the mutable current owner. Stable identity is `run_session_id`, exact plan path, and registered worktree. Resolve each manifest at its facts-based canonical path. **Stale preservation** is independent of conversion eligibility: a manifest path present in a registered worktree protects the claim during stale `take` and `sweep` for both canonical and legacy forms, regardless of branch, owner, or plan mismatch; do not follow symlinks or mutate either file, and refuse conversion for operator reconciliation. Multiple matches or missing facts refuse unchanged; no matching registered manifest uses the branch-occupant rule. **Conversion** requires an attached exact registered target, exact prior-owner and plan matches, and the stable tuple; recorded `run_worktree:` and any recorded `run_branch:` must match. Every detached target refuses conversion unchanged, including legacy manifests without `run_branch:`. The facts-resolved location identifies a legacy manifest's worktree when it lacks `run_worktree:`. Conflicts refuse conversion unchanged.
- **Canonicalized manifest**: after successful conversion, set `session_id:` to the resumer, `plan_path:` to the exact claim operand, `run_worktree:` to the exact registered target, and `run_branch:` to its registered branch; remove legacy `Session:` and `Plan:` aliases and preserve unrelated manifest content.
- **Completed run boundary**: the stable evidence tuple is `run_session_id`, exact plan path, and exact registered worktree; mutable `session_id` and the claim identify the current owner. The manifest, each parent-owned `task_boundary:` row, `runtime_state.json`, every Phase 2/3 record, each referenced log, and `pre_archive_receipt` bind to the stable tuple. New records carry the tuple explicitly, so it remains unchanged across owner conversions. The gateway resolves all paths using that worktree's facts-resolved `tmp_dir`, checks containment and every identity field/pointer before conversion. For artifacts created before tuple support, apply the bounded legacy binding on every conversion, even after manifest/runtime-state migration, and never rewrite their bytes; every new appended pass or record carries the tuple. Legacy binding requires exact prior claim and manifest owner/plan, one registered worktree containing the manifest at its canonical plan-slug path, each old log at its unique contract path for a completed task/round listed in the manifest, Phase 2/3 files at exact receipt pointers, and matching plan/task/review metadata. Migration records the stable tuple only after all checks pass. Missing, duplicate, incomplete, conflicting, unreferenced, or ambiguous evidence refuses unchanged. Every task and review iteration has exactly one parent-owned boundary record, and all required terminal logs are complete. Phase 3 has either zero unresolved blocking findings or a valid residual-acceptance exit under a pre-recorded `residual_policy:`; its exit report binds to the tuple. The receipt's `declared_paths` must match the archive pathset, `plan_digest` must hash the active plan bytes before the move, `evidence` must point to this run's Phase 2 and Phase 3 records, and `recorded_at` must be present. The existing closeout gate later verifies the archived destination and digest against the commit tree. A residual-acceptance exit is valid only when its named set reaches fixed or dropped, every new out-of-set blocker has a durable backlog item with owner and trigger, and the exit report lists those backlog paths.
- **Session status provider**: the absolute executable named by `session_status_command` in the primary checkout's local facts file. It receives the prior session ID as its sole argument, exits zero, and writes exactly one JSON object to stdout with only two string fields: `session_id` equal to the argument and `status` equal to `terminal`, `live`, `paused`, or `unresolved`. The gateway caps stdout and stderr at 65,536 bytes each; on either overflow it terminates and reaps the process group, then refuses unchanged. Only `terminal` proceeds; nonzero exit, extra/missing fields, malformed JSON, mismatched ID, or another status refuses unchanged.
- **Provider smoke evidence**: before a runtime advertises conversion, write `docs/history/release-evidence/session-status-provider/<runtime-id>.md` with the runtime ID, facts source and configured executable path plus SHA-256, exact test session ID, exit status and full JSON response, check timestamp, and verifier. Exclude credentials and unrelated session data. The release owner verifies the record against live configuration.
- **Trusted session channel**: `scripts/session_channel.py` derives the active ID from the runtime's inherited session environment. Matching `--session` to that value prevents accidental mismatch; it is not authentication against a same-account caller who can forge those variables.
- **Prior owner**: the session named by the existing claim and manifest before atomic claim replacement.
- **Conversion lock**: the per-worktree done-lock acquired and owned by the gateway for the bounded Phase 0 claim conversion; done-mode locks are per-worktree.
- **Atomic claim replacement**: writing the new claim beside the old one and renaming it over the old claim in one filesystem operation after re-reading the exact prior claim under the worktree done-lock and repository merge-lock.
- **Replacement claim shape**: write `session:` and `plan:` for the resumer and exact operand, retain the prior `created:`, refresh `updated:`, and preserve any prior `branch:`, `start-commit:`, and `base:` values. When the manifest records the same branch, start commit, or base, require the prior claim value to match it before replacement; do not synthesize missing optional claim fields.
- **Claim mutation lock**: the existing repository-wide `merge-lock`, shared by linked worktrees and used to serialize claim reads and changes.
- **Current owner**: the session named by both the claim and manifest after a completed transition.
- `H`: the original manifest and claim holder.
- `R`: a resumer that atomically replaces the claim.


## Why

Arm 3 reads legacy claim fields while run manifests use different owner fields, so a dead run can be mistaken for a fresh conflicting claim. The observed dead run used `session_id:` without `Session:` and lacked `run_worktree`; recovery must preserve this in-use manifest compatibility while confirming owner and completion evidence before transferring the claim.

## Gist & Examples

TLDR: restore dead-run claim conversion with verified owner evidence, atomic replacement, and existing bounded repository locks.

Before: a real manifest with `session_id:` but no legacy `Session:` row fails arm 3. An interrupted unlink/create can leave no claim, and concurrent `take` calls can replace each other's claims.

After: the documented Phase 0 `take` route verifies the manifest identity tuple, binds the supplied resumer ID to the active session, acquires that worktree's done-lock, invokes the configured status provider for the manifest owner, and accepts only structured output naming the same session ID and state `terminal` within the bounded output contract. It verifies every item in the completed run evidence envelope, including its permitted residual-acceptance exit, and the closeout `pre_archive_receipt`. Missing provider configuration, mismatched run evidence, or incomplete coverage refuses unchanged. The existing repository-wide `merge-lock` serializes this transition with claim operations from every worktree; the gateway releases only lock tokens it acquired. Stale `take` and `sweep` preserve claims whenever either supported manifest form remains at its exact registered-worktree path, including split-owner state; conversion still refuses owner mismatch unchanged. Abrupt process death leaves the lock for later verified-dead-holder recovery.

Edge cases: missing or mismatched owner, active resumer, and plan identity; malformed or symlinked evidence; missing claim or provider; relative provider path; caller-controlled PATH or status variables; nonterminal or mismatched provider response; incomplete task or review boundary; missing or in-progress log; absent or invalid closeout receipt; foreign active or ambiguous done-lock holder; lock token or worktree mismatch; ambiguous legacy-manifest worktree; and interrupted claim/manifest owner mismatch all refuse without changing claim or manifest bytes.

## Outcome

Restore dead-run recovery by transferring only a verified, completed run to its resuming session.

- A run may resume only when its saved records identify the same prior session, plan, and registered worktree, a status check confirms that session has ended, and all required work and review evidence is complete.
- The ownership change is protected and happens as one file replacement. A failure before that replacement leaves the saved files unchanged. An interruption after replacement can leave complete files naming different owners; the next attempt refuses without changing them.
- The saved claim keeps its original branch, starting commit, and base when present, so later checks can still detect a worktree occupying that branch.
- Saved claims remain protected while their matching worktree is registered, including after that worktree changes branches or becomes detached. Conversion requires an attached target; any recorded branch must match it.

Gate delta: allow exact registered-worktree recovery through the existing stale-claim refusal only after owner, completed-run, and gateway-owned lock evidence pass. Preserve claims for registered canonical and supported legacy manifests during stale `take` and `sweep`, while keeping branch-occupant behavior when a manifest worktree path is absent. Claim operations reuse the existing repository merge-lock; this adds no lock family and refuses once with the holder when it is busy. Before the planned pre-registration rows, the current `execution-claim-gateway` ratio is 0 catches to 1 incident (0:1), from `python3 scripts/gate_liveness_ledger.py show`. The ledger pre-registration names the 2026-10-19 and 2026-10-20 dead-owner incidents and the R21 review catch for the reachable cross-worktree release race (`.ai-playbook/reviews/2026-10-21-plan-review-dead-run-resume-claim-conversion-p65513e2d-r21.md`). Expected catches: two in two days of resume activity. False-positive cost: one bounded retry for a claim operation that overlaps repository merge work. Review date: 2027-04-21. If no further true catch occurs by review, restore the prior stale-claim refusal and claim-mutation behavior.

## Assumptions

- Initial setup obtains the non-empty current session ID through `scripts/session_channel.py`, writes `session_id:` and exact repository-relative `plan_path:`, and passes the same plan operand to `take`. This session channel is trusted runtime context, not an authentication boundary against forged environment values.
- Recovery reads `session_status_command` from the primary checkout's facts file, requires an absolute executable path, and invokes it in a controlled environment under the verified target-worktree done-lock with a 10-second timeout. Its response must match the Session status provider shape in Terms; otherwise conversion refuses unchanged. The completed run boundary is defined once in Terms; no worker-authored claim or manifest receipts are introduced.
- The documented workflow invokes conversion through `take` in Phase 0 from the exact registered run worktree. Phase is not an authorization input. The gateway derives both lock roots from the OS account record, clears caller `HOME`, `DONE_LOCK_*`, and `MERGE_LOCK_*`, acquires worktree then repository locks before claim lookup, and verifies both tokens and paths before provider invocation.
- If the run worktree already has a done-lock, the gateway attempts `release-orphaned` first. It removes only a holder verified dead and past the grace period; live or ambiguous foreign holders, unknown holders, and too-young locks remain untouched. The gateway verifies its own token and exact worktree path; only that token may be released by cleanup.
- For a legacy manifest without `run_worktree`, stale takeover scans registered worktrees for the canonical manifest location and matches its prior owner and exact plan. An ambiguous match preserves the claim and refuses; conversion requires one exact registered target.
- The test harness injects a fixture account-home record through the trusted lock-root resolver seam; production still reads the OS account record. Caller `HOME` and `DONE_LOCK_*` values cannot select the fixture or production root.
- Claim replacement writes a complete new claim to a temporary sibling and atomically renames it over the existing claim under the gateway-owned verified target-worktree lock. A crash leaves either the old complete claim or the replacement; it never creates an unlink gap.
- After claim replacement, the manifest is atomically canonicalized as defined in Terms. If interrupted between those writes, the next call sees mismatched owners and refuses without changing either file; there is no automatic transition recovery.
- A handled interruption runs token-fenced cleanup for the gateway-owned lock. Abrupt process death leaves that lock in place; a later call may clear it only after the existing holder-death and grace-period checks pass.
- An absent or malformed claim remains unsupported and refuses without creating a claim. A surviving worktree is adopted after conversion; no second worktree is created.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: recovery recognizes only literal matching active-resumer and run-evidence identity; stale preservation is branch-independent, while conversion requires an attached exact target and enforces any recorded branch; legacy manifests without `run_worktree` resolve through registered manifest location or refuse unchanged when ambiguous.
- safety: gateway token, worktree, provider, locking, and refusal behavior meet the Outcome contract; the completed run boundary is defined once in Terms.
- compatibility: canonical and supported legacy manifest forms in Terms retain exact plan-path and run-evidence binding and qualify only when the completed run boundary holds.

**Done when:**
- the gateway handles canonical/legacy keys, exact plan mismatches, registered/unregistered worktrees, and H/claim H to R; mismatched claim and manifest owners after interruption refuse byte-identically.
- an interrupted replacement leaves the old or new complete claim; if claim and manifest owners disagree, a later conversion refuses byte-identically without inferring lineage.
- recovery refuses when the provider is absent, configured from a non-primary facts file, relative, caller-overridden, or does not return the exact owner terminal status, or when the completed run boundary is missing or invalid; a residual-acceptance fixture succeeds only with the pre-recorded named policy, fixed-or-dropped named findings, and backlog paths for every new out-of-set blocker.
- Competing conversions of the same registered worktree serialize on its done-lock. Other-worktree `take` and `sweep` preserve claims while the exact canonical or supported legacy manifest location remains registered, including detached and branch-switched fixtures. Ambiguous legacy matches refuse unchanged; no matching registered legacy manifest falls back to branch occupancy. A mismatched active `--session` refuses before lock acquisition or provider invocation. Foreign-owner refresh/release leave the claim unchanged. Missing, wrong, or foreign-worktree lock tokens or paths refuse before provider invocation and never release a foreign lock. Poisoned caller `HOME` and `DONE_LOCK_*` values cannot change the root; all lock tests use an injected fixture account home without an environment override. Timeout kills and settles the full provider process group before token release; handled interruption releases only the gateway token, while abrupt process death leaves it for verified-dead-holder recovery.
- direct gateway calls reject a mismatched active resumer ID, owner, plan, branch, worktree, symlink, and empty session ID before lock acquisition, provider invocation, or claim/manifest mutation.
- `python3 scripts/test_execution_claim.py`, `bash scripts/check_maintenance_pins.sh`, and `python3 scripts/machinery_inventory.py --check` pass.

**Ship when:**
- the plan is executed and lands through the standard review and closeout gates. Before a runtime advertises dead-run conversion, its configuration owner adds an absolute `session_status_command` to the primary facts file, runs the exact-ID terminal smoke check, and completes the Provider smoke evidence record from Terms; the release owner verifies its runtime, executable digest, exact ID, response, and timestamp against configuration. The gateway still checks the live response on every conversion. Without valid configuration and verified evidence, the existing branch-occupant refusal remains active. [class: EXTERNAL_RELEASE_GATE]

## Review Scope

**Explicit must-fix:**

**Production code:**
- `scripts/execution_claim.sh`
- `scripts/session_status.py` *(new)*
- `scripts/gate_liveness_ledger.json`
**Tests:**
- `scripts/test_execution_claim.py`

**Documentation and registry:**
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/maintenance/template-execution.md`

**Supporting interface:**
- `scripts/session_channel.py` (read-only environment-key and current session ID source)
- `scripts/done-lock.sh` (existing per-worktree dead-holder recovery, acquire, and token-fenced release interface)
- `.ai-playbook/facts.md` (primary-checkout provider configuration; no default provider)

**Out of scope; reject unless plan-related:**
- Removing the branch-occupant gate outside the exact registered-worktree recovery arm, or adding a new claim mode; existing-claim recovery uses the existing `take` command and exact registered worktree.
- Adding a new lock family; claim commands reuse the existing repository-wide merge-lock, with one-shot contention refusal. The Phase 0 gateway also keeps its exact-worktree done-lock for run recovery, and the existing stale-takeover occupancy gate checks the branch recorded in the claim even when the requested branch differs.
- Resuming when the exact prior owner is live, paused, or unresolved, or when the run is incomplete.
- Other worktree or claim cleanup behavior not required by this resume path.

## Validation Commands

```bash
python3 scripts/test_execution_claim.py
bash scripts/check_maintenance_pins.sh
python3 scripts/machinery_inventory.py --check
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: Implement serialized claim conversion and trusted owner checks

Files:
- `scripts/execution_claim.sh`
- `scripts/session_channel.py` (read-only active session ID source)
- `scripts/session_status.py` *(new)*
- `scripts/gate_liveness_ledger.json`

Primary class anchors:
- `resume_evidence_matches` in `scripts/execution_claim.sh`
- `query_session_status` in `scripts/session_status.py`
- `Live-session discovery ladder` in `agents/skills/execute-plan/SKILL.md`

- [x] Parse only manifest identity forms in Terms; resolve `tmp_dir` from each target worktree's facts; bind prior owner, stable run ID, exact plan, and registered worktree; refuse conflicts; canonicalize successful conversions. [class: IMPLEMENTATION_REQUIRED]
- [x] Before lock acquisition or mutation, derive the active ID through `scripts/session_channel.py` and require exact `--session` equality; empty or mismatched IDs refuse unchanged within the trusted session-channel boundary in Terms. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify one exact registered run worktree; recover only verified-dead holders. Derive roots from the OS account, clear caller lock variables, and verify tokens and paths. [class: IMPLEMENTATION_REQUIRED]
- [x] After active-session validation, acquire target done-lock then repository merge-lock before claim reads; hold through provider lookup, replacement, and manifest refresh. [class: IMPLEMENTATION_REQUIRED]
- [x] All five claim commands acquire merge-lock before claim access. Pin it to the command PID; reuse only this session's verified token, else try once and refuse with holder. [class: IMPLEMENTATION_REQUIRED]
- [x] On handled success or refusal, release every owned lock in reverse acquisition order: merge-lock for all commands and target done-lock for conversion. Only abrupt death leaves locks for verified-dead recovery. [class: IMPLEMENTATION_REQUIRED]
- [x] Pin locks to the live gateway PID; verify records and never use a command-substitution parent. [class: IMPLEMENTATION_REQUIRED]
- [x] Bound provider to 10 seconds and each output stream to 65,536 bytes; on timeout or overflow terminate and reap the process group, then refuse unchanged and release only owned locks. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify exact worktree registration, contained plan/manifest paths, and non-symlink evidence; a recorded branch must match the attached target. [class: IMPLEMENTATION_REQUIRED]
- [x] Read provider config only from primary facts; require an absolute executable and controlled environment. Enforce Terms' exact JSON: only matching-ID terminal proceeds; all other results refuse unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Enforce the stable evidence tuple in Terms across runtime state, task/review boundaries, logs, Phase 2/3 records, and receipt; validate current owner separately and accept legacy artifacts only through the bounded legacy binding. Refuse incomplete or ambiguous evidence unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Add no claim lineage for interrupted replacement. If claim and manifest owners differ after a crash, refuse unchanged for operator reconciliation. [class: IMPLEMENTATION_REQUIRED]
- [x] Under both locks, re-read the claim; if owner or bytes changed, refuse. Otherwise atomically replace it and canonicalize the manifest per Terms. [class: IMPLEMENTATION_REQUIRED]
- [x] Build the replacement per Terms: preserve prior branch, start commit, and base; refuse before replacement if any recorded value conflicts with the manifest. [class: IMPLEMENTATION_REQUIRED]
- [x] Pre-register recovery removal in `scripts/gate_liveness_ledger.json` with 2026-10-19/20 incidents and R21 race, two catches per two days, one delayed retry, 2027-04-21 review, and restore prior refusals if no further catch occurs. [class: IMPLEMENTATION_REQUIRED]
- [x] For stale `take`/`sweep`, resolve each worktree's `tmp_dir` from its facts and preserve a claim whenever either supported manifest form remains at its exact registered-worktree path, regardless of owner/plan mismatch or branch state. Never follow symlinks; ambiguity or missing facts refuses unchanged, with no default-path fallback. [class: IMPLEMENTATION_REQUIRED]
- [x] Conversion requires one exact registered, attached target; detached, missing, or ambiguous targets refuse unchanged, even when a legacy manifest has no `run_branch:`. [class: IMPLEMENTATION_REQUIRED]
- [x] After replacement and manifest refresh, verify the registered target, report success, disarm cleanup, and return before the occupant refusal or `git worktree add`. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `fix: recover dead-run claim ownership safely` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Exercise claim conversion and gateway-lock ordering

Files:
- `scripts/test_execution_claim.py`

Primary class anchors:
- `test_restored_worktree_takeover_on_verifiable_same_run_state` in `scripts/test_execution_claim.py`

- [x] Across canonical and legacy forms, verify exact identity, conflicts, symlink/copy cases, and active-owner match/refusal; successful conversions preserve unrelated fields, canonicalize, and pass later stale-take. [class: REPOSITORY_TEST]
- [x] Across H-to-R-to-S with tupleless legacy evidence, validate it on both conversions: invalid R-to-S binding after migration refuses byte-identically; valid R-to-S succeeds, leaves old logs/Phase 2 bytes unchanged, and keeps new records tuple-bound. [class: REPOSITORY_TEST]
- [x] Convert H/claim H to R only with matching owner/worktree; interrupted owner mismatch refuses byte-identically. [class: REPOSITORY_TEST]
- [x] Provider schema/ID errors, malformed output, timeout, and 65,536-byte stream overflow refuse closed; timeout, overflow, and interruption reap the process group and release only gateway-owned locks. [class: REPOSITORY_TEST]
- [x] Bind every completion artifact to the stable tuple: mismatched, incomplete, duplicate, copied, or ambiguous evidence refuses byte-identically; valid legacy evidence migrates only after all checks. Require a valid Phase 3/receipt; missing `recorded_at` or mismatched archive paths, digest, or pointers refuse unchanged. [class: REPOSITORY_TEST]
- [x] Preserve `created`, `branch`, `start-commit`, and `base`; refresh `updated`; refuse recorded claim/manifest conflicts; a later `take` on another branch still sees the saved branch occupancy. [class: REPOSITORY_TEST]
- [x] Acquire target done-lock then repository merge-lock before claim access; interleave `claim`, `take`, `refresh`, `release`, and `sweep` across worktrees to verify serialization. [class: REPOSITORY_TEST]
- [x] With a live merge-lock held by another session, each claim command refuses once, names the holder, and preserves claim and manifest. [class: REPOSITORY_TEST]
- [x] During a long provider call, both locks identify the live gateway process; another worktree cannot reclaim them through ordinary acquire or dead-holder recovery. [class: REPOSITORY_TEST]
- [x] Exercise both serialized release/conversion orders; neither reads ownership before locking or unlinks R's claim from a pre-lock read. [class: REPOSITORY_TEST]
- [x] Stale `take`/`sweep` preserve canonical/legacy claims byte-identically across branch switch/detach and default/overridden `tmp_dir`, including H-claim/R-manifest split owners. Missing/ambiguous facts or conflicts refuse; absent manifests use branch occupancy; foreign refresh/release refuse. [class: REPOSITORY_TEST]
- [x] A mismatched active `--session` refuses before recovery, acquisition, or provider call; assert lock, claim, and manifest unchanged. [class: REPOSITORY_TEST]
- [x] Provider invocation requires the gateway's verified token and exact worktree path; wrong or foreign tokens refuse before invocation and are never released. [class: REPOSITORY_TEST]
- [x] Use fixture account-home resolution; poisoned caller `HOME` and `DONE_LOCK_*` cannot redirect lock roots. [class: REPOSITORY_TEST]
- [x] Run subprocesses in a clean environment; poison caller HOME, lock variables, PATH, status, and worktree facts; verify trusted roots/provider and session-channel matching. [class: REPOSITORY_TEST]
- [x] Successful conversion adopts the exact registered worktree without `git worktree add` or post-acquisition occupant refusal. [class: REPOSITORY_TEST]
- [x] Live, ambiguous, unknown, and too-young foreign holders preserve lock, claim, and manifest. [class: REPOSITORY_TEST]
- [x] Inject rename/refresh failures and pre/post-write interrupts; files stay complete and retries refuse owner mismatch. Success/refusal release owned locks, foreign locks remain, and abrupt death requires verified recovery. [class: REPOSITORY_TEST]
- [x] Commit: `test: cover dead-run claim recovery evidence` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Document the recovery procedure

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/maintenance/template-execution.md`

- [x] Make `agents/skills/maintenance/template-execution.md` the sole recovery procedure for H/claim H to R; other listed documents link here. Resolve live-resume and dead-run manifests from the relevant worktree's facts-based `tmp_dir`. [class: IMPLEMENTATION_REQUIRED]
- [x] During Phase 0, invoke `take` before saved-manifest refresh, other run mutation, work, or closeout, with `--session` equal to the active ID returned by the shared session-channel helper. Verified live same-session resume still refreshes first. [class: IMPLEMENTATION_REQUIRED]
- [x] Document the worktree done-lock and repository merge-lock lifetimes: token-release after every handled success/refusal, reverse acquisition order, and abrupt-death recovery only after verified holder death. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep live same-session resume behavior unchanged, route dead-run conversion through the gateway once, and remove duplicated route-level liveness checks. The run log records the exact owner transition and gateway-owned lock disposition but never authorizes conversion. [class: IMPLEMENTATION_REQUIRED]
- [x] State that missing claim, live/paused/unresolved owner, incomplete run boundary, a foreign or unverifiable live/ambiguous done-lock holder, lock token/worktree mismatch, and mismatched claim/manifest owner refuse without claim or manifest mutation; the gateway accepts only its own verified lock. [class: IMPLEMENTATION_REQUIRED]
- [x] Document `session_status_command` and the exact JSON response shape in Terms, its primary-checkout facts source, absolute executable requirement, controlled environment, and fail-closed default when absent; also document the closed task/review boundary and refusal when evidence is incomplete. [class: IMPLEMENTATION_REQUIRED]
- [x] Align the runtime contract: the Phase 0 gateway owns the exact registered worktree's done-lock only around conversion. `take` and `sweep` preserve a claim while its manifest's exact worktree path remains registered, regardless of branch state. [class: IMPLEMENTATION_REQUIRED]
- [x] State that the gateway queries the configured provider for the literal prior-owner ID with a 10-second bound, treats paused or unresolved as nonterminal, and allows conversion only after the parent-owned final review and archive-preparation boundary. [class: IMPLEMENTATION_REQUIRED]
- [x] Document that successful dead-run conversion adopts the exact registered worktree, releases its own conversion-lock token, and returns before the post-acquisition occupant refusal or worktree creation. [class: IMPLEMENTATION_REQUIRED]
- [x] Document canonical/legacy identity, stable `run_session_id`, mutable `session_id`, mixed old/new evidence, runtime-state/receipt binding, and facts-resolved `tmp_dir` discovery in the single recovery procedure; document the smoke check and search for obsolete recovery instructions. [class: IMPLEMENTATION_REQUIRED]
- [x] Update Phase 0 to initialize canonical `run_session_id`, current `session_id`, exact repository-relative `plan_path:`, and `run_worktree:` before logs or runtime state; bind task-boundary rows, logs, runtime state, and receipt to the stable tuple. Update those contracts accordingly; migrate verified legacy tuples only after successful checks, retaining branch fields. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: document dead-run claim recovery` [class: IMPLEMENTATION_REQUIRED]

## Origin disposition

- `docs/history/backlog/2026-10-20-dead-execution-run-resume-in-own-worktree-no-claim-conversion.md`: implement canonical manifest recognition, exact prior-owner status verification from the configured primary-runtime provider, completed-boundary validation, and serialized atomic recovery through the existing `take` gateway; delete the row at landing.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-20-dead-execution-run-resume-in-own-worktree-no-claim-conversion.md`: folded into this plan's Terms and Task list at authoring; the per-item file is deleted at landing per the plan's own origin disposition (this section is the fold-then-delete consult anchor).
