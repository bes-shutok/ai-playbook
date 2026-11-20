# Plan: Codex session-status provider reachability verdict

Language guidelines: `projects/.ai-playbook/python_guidelines.md` (the supported arm adds a Python script; plain `python3` for repo-local trusted scripts).

Backlog origin: docs/history/backlog/2026-11-19-codex-incomplete-run-owner-status-unavailable.md
Driving force: automation
Required agent type: codex
Plan review record: the staging series .ai-playbook/reviews/2026-11-19-plan-review-codex-incomplete-run-owner-status-unavailable-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 1h
Executed: c226f8acc093f8f4011e1afb97a0a3ad2bfbfa04
Authoring claim: 2026-11-19-codex-incomplete-run-owner-status-unavailable.md (session sess_726a635e-569b-4657-b30c-a4dc457b092c)

## Terms

- Session-status provider: the executable named by `session_status_command`, invoked by the gateway with the prior session ID as its sole argument; it must exit 0 and print exactly one JSON object with the string fields `session_id` and `status`.
- Provider contract: the response rules enforced by `query_session_status` in `scripts/session_status.py`: absolute executable from the primary facts document, controlled environment, 10-second bound, 64 KiB stream caps, closed status vocabulary `terminal|live|paused|unresolved`, exact-ID echo.
- `session_status_command`: the facts-document key the provider is configured under; read only from the primary checkout's facts document (`read_provider_command` in `scripts/session_status.py`); refusing when absent, relative, or malformed.
- Dead-run conversion: the claim gateway's arm that adopts a foreign run after the provider reports `terminal` for the exact prior owner; only `terminal` proceeds.
- Exact-ID terminal smoke check: running the provider against a test session whose ended state is independently corroborated and recording the exit status and full JSON response; a runtime may advertise conversion only after it (Recovery procedure, `agents/skills/maintenance/template-execution.md`).
- Provider smoke evidence record: `docs/history/release-evidence/session-status-provider/<runtime-id>.md`; the record the completed conversion plan's Terms pin (runtime ID, facts source, executable path plus SHA-256, exact test session ID, exit status, full JSON response, check timestamp, verifier).
- Rollout store: the Codex session transcript files on disk (`rollout-<timestamp>-<session-id>.jsonl` under the dated session directories of the Codex homes, for example `~/.codex/sessions/` and the `CODEX_HOME`-scoped home).
- Grouped agent-center status: the Codex agent command center's per-thread UI label; a grouped status, never provider evidence (rejected here: a grouped UI status, not the exact-ID JSON response the contract requires).
- Surface: a local Codex-provided capability able to answer an exact-ID session status query (a CLI subcommand, the app-server read API, the rollout stores, or a wrapper over one of them).
- Adapter: `scripts/codex_session_status_provider.py`, the thin executable the supported arm adds: session ID argument in, contract JSON out, nothing else.
- Verdict: the Task 2 decision `supported` or `unsupported`, recorded with probe evidence in the smoke evidence record.
- Facts document: the primary checkout's `.ai-playbook/facts.md`, machine-local and gitignored; configuration bound there is never committed.
- Gateway: `scripts/execution_claim.sh` plus `scripts/session_status.py`; byte-intact in this plan, read-only references.
- Witnessed run: the corrections-writer execution run (manifest identity block `run_session_id`, value `01a1f00b-aa83-7302-beb4-04360f9747d5` at authoring; re-derived from disk at execution).
- Peer-owned claim: the witnessed run's claim, taken over by another session (stale-claim takeover, 2026-11-19T17:20Z) after this plan's authoring started; read-only context, never converted or written here.
- Focused suite: the facts policy `test_suite_policy = "focused-never-full"`; per-plan validation runs named suites, never the full battery.

## Why

Dead-run conversion exists and is fail-closed, but this checkout's Codex runtime never configured its provider, so `scripts/session_status.py` refuses with `session_status_command not configured` and every cross-session recovery that needs conversion stops at the provider refusal (witnessed 2026-11-19 on the corrections-writer run; that recovery's merge-lock gate separately refused twice with an indeterminate holder). The provider contract, evidence shape, and release gate already exist; the missing piece is the Codex-side reachability decision: either a supported surface gets bound and smoke-verified, or the unsupported verdict gets recorded so the refusal is a documented posture instead of an unconfigured accident.

## Gist & Examples

TLDR: the Codex runtime's session-status provider gets configured and smoke-verified, or its unsupported verdict gets recorded with probe evidence, so dead-run claim conversion stops being silently unreachable in this checkout (automation).

Before: `python3 scripts/session_status.py .ai-playbook/facts.md <session-id>` prints `session-status refused: session_status_command not configured ...` and exits 1; the provider smoke evidence directory does not exist; recovery of an incomplete Codex run falls back to operator reconciliation or a stale-claim takeover.

After (supported): the provider answers the exact-ID query in the closed vocabulary, the smoke check's response sits in the evidence record, and the conversion advertisement path is open pending the release owner's verification. After (unsupported): the same record carries the verdict `unsupported` with the probe evidence, and the existing refusals stand as the documented, evidenced posture.

Edge cases: a contract-valid response of `live`, `paused`, or `unresolved` for the test ID is recorded, and conversion still refuses (only `terminal` proceeds); a surface that cannot decide exact-ID status at all takes the unsupported arm; the peer-owned claim is never converted by this plan's work regardless of the verdict.

## Outcome

The Codex runtime's dead-owner verification prerequisite is either satisfied and evidenced or recorded as unsupported, through the existing provider contract alone.

- The provider smoke evidence record exists at the pinned home with every pinned field, in the supported or unsupported shape.
- In the supported arm, `session_status_command` is bound in the primary facts document and the exact-ID smoke check has run, so a successor session's conversion attempt reaches a real provider verdict instead of a configuration refusal.
- The claim gateway's refusal classes, terminal check, and worktree adoption path stay byte-intact; nothing in this plan adds a second takeover path or weakens the check.

Gate delta: none. No gate, fence, refusal class, protocol layer, or schema field is added or removed; the plan binds an existing unconfigured prerequisite (the facts key), adds one evidence record and, in the supported arm, one adapter script with its selftest, and leaves the gateway's refusal semantics unchanged.

Follow-up disposition: a candidate surface whose capability depends on an upstream Codex CLI change (for example an app-server read API that does not expose per-thread exact-ID state today) leads to a durable backlog row naming the surface and its gap, filed through the run's own outputs; the merge-lock indeterminate-holder observation from the witnessed incident stays out of scope here and leads to the dead-run conversion residuals cluster if it recurs after the provider is reachable; the witnessed run's own completion is owned by its recovery path (the peer session's takeover), never by this plan.

## Assumptions

- assume the verdict work is configuration plus evidence, never machinery: no gate, validator, registry, or takeover path is added; basis: origin row suggested fix and the entry's machinery-admission note (no new gate, validator, lock, ledger, or ceremony recommended).
- assume the adapter (supported arm) is a thin executable translating one selected surface into the contract JSON, not a registry: it reads existing stores or surfaces and holds no state; basis: the plans skill's runnable-script rule and the origin row's ban on a new status/claim registry; simpler-design comparison recorded: binding a raw CLI surface directly was preferred first, but no verified subcommand emits the contract JSON (Codex CLI 0.170.0 subcommands probed 2026-11-19: `agents`, `exec`, `resume`, `queue`, `archive`, `delete`, `fork`, `app-server` among others; none prints exact-ID status), so the adapter is the smallest contract-conforming carrier.
- assume the facts binding is machine-local configuration in the primary checkout's gitignored facts document and never lands as a tracked change; basis: `read_provider_command` reads the primary facts file only, and the file is gitignored (verified 2026-11-19).
- assume the witnessed claim's ownership change mid-authoring (stale-claim takeover by another session, recorded in the claim file) does not change this plan's scope: the provider work is generic capability; the witnessed run's recovery is the peer session's lane; basis: the maintenance loop's peer-state invariant.
- assume the merge-lock indeterminate-holder observation stays out of scope; basis: the entry's prompt binds the refusal in force and forbids bypassing it; the scope arms name provider reachability, not lock behavior.
- assume no task infers why the original Codex session stopped; the evidence supports only the prerequisite gap; basis: origin row evidence section.
- assume execution belongs to the Codex runtime: the operator directed the runtime binding on 2026-11-19 after the first (ZCode) execution pass's Task 1 concluded `unsupported` on store-and-CLI probes without reaching the runtime-internal surfaces; basis: operator decision relayed in session sess_726a635e, the `Required agent type: codex` header line, and the preserved first-pass WIP evidence the amendment orders re-verified.
Decision points requiring a grill: none remain.

## Standing constraints

- The two gateway scripts (`scripts/execution_claim.sh`, `scripts/session_status.py`) stay byte-intact; every task treats them as read-only references.
- The provider query, smoke check, and all probes are read-only: no claim, manifest, lock, or worktree state is created, taken, converted, or written; the peer-owned claim and its worktree are never touched.
- No original-stop-cause inference enters any record this plan's execution writes.
- Facts-document configuration never commits; the evidence record is the only tracked artifact carrying configuration state.
- Focused suites only, per the facts `test_suite_policy`; no full-battery run is required by this plan.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every recorded provider response is contract-valid or the refusal is recorded verbatim; the verdict rule is applied exactly (supported requires contract-valid exact-ID responses with a corroborated `terminal`; anything else is unsupported).
- evidence completeness: the smoke evidence record carries every field the completed conversion plan's Terms pin, in whichever shape the verdict selects.
- safety: all probes and provider work are read-only; the gateway scripts stay byte-intact; the peer-owned claim and its worktree are untouched.
- regression: the provider-contract focused cells of the existing claim suite pass unchanged after the work.

**Done when:**
- The Task 2 verdict is recorded with per-surface probe evidence in the task log.
- `docs/history/release-evidence/session-status-provider/codex.md` exists with the outcome verdict line and the pinned fields (supported or unsupported shape).
- Supported arm: the adapter exists with its focused selftest green, `session_status_command` is bound in the primary facts document, and the smoke check's exit status, full JSON response, and timestamp are recorded in the evidence record.
- Unsupported arm: the evidence record's limitation and retained-refusal statement are complete, and the unconfigured-provider refusal was reproduced through the provider query CLI and recorded.
- The Validation Commands block passes per the executed arm, and no tracked file outside the Review Scope explicit list changed.

**Ship when:**
- The release owner verifies the evidence record against live configuration (runtime, executable digest, exact ID, response, timestamp) before any runtime advertises dead-run conversion; the gateway still checks the live response on every conversion. (release gate; evidence owner: the release owner's verification against the bound facts configuration; closure: the completed conversion plan's EXTERNAL_RELEASE_GATE, unchanged.)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/codex_session_status_provider.py` (Task 3) *(new, supported arm only)*

**Tests:**
- `scripts/test_codex_session_status_provider.py` (Task 3) *(new, supported arm only)*

**Documentation:**
- `docs/history/release-evidence/session-status-provider/codex.md` (Task 2) *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execution_claim.sh` and `scripts/session_status.py`; reason: byte-intact references, read-only in every task (findings there are tracked separately from the dead-run conversion coverage cluster)
- the peer-owned claim file, its execution-claim directory entries, and the witnessed run's worktree; reason: peer-session state, untouchable by this plan
- the repository merge-lock behavior; reason: the witnessed indeterminate-holder refusal stays in force and unmodified per the entry prompt
- the Codex CLI and its session stores; reason: upstream runtime surfaces, read-only probe targets
- `agents/skills/maintenance/template-execution.md` and the completed conversion plan; reason: the contract and evidence shape already exist there and stay uncited-but-unchanged

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execution_claim.py -q -k provider || exit 1
if [ -f scripts/test_codex_session_status_provider.py ]; then
  PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_codex_session_status_provider.py -q || exit 1
fi
test -f docs/history/release-evidence/session-status-provider/codex.md || exit 1
grep -qE '^Outcome: (supported|unsupported)' docs/history/release-evidence/session-status-provider/codex.md || exit 1
bash scripts/check-no-em-dash.sh added-lines --base main || exit 1
bash scripts/scan-public-hygiene.sh || exit 1
```

Validation preamble (authoring-time preflight record, 2026-11-19):

- Provider-contract selector `-k provider` on `scripts/test_execution_claim.py`: measured 2026-11-19 at the worktree base: the selector collects 5 tests, all passing (`5 passed, 99 deselected, 3 subtests passed`, exit 0); this line is an unchanged-green witness for the gateway confirmation, never a RED leg.
- Adapter suite line: `scripts/test_codex_session_status_provider.py` does not exist at authoring; the existence-guarded conditional keeps the block executable today and gates the suite once the supported arm lands it. In the unsupported arm the guard's false branch is the arm's own outcome and the line is skipped with a recorded disposition.
- Evidence-record gates: the record path and its `^Outcome:` verdict line do not exist at authoring, so both are RED today and GREEN exactly when Task 2 lands the record.
- Em-dash authoring-time self-check: the write-time fixer (`scripts/fix_plan_em_dashes.py`) runs in full mode over the new plan bytes before the first review round and in `--preserve-tasks` mode after every later write; the authoring write recorded 0 substitutions.
- Hygiene scan: `bash scripts/scan-public-hygiene.sh` measured pass at authoring over the worktree base.
- Block shape: the Validation Commands block passes `bash -n`; every fallible line carries `|| exit 1` or an explicit conditional exit.
- Pre-round gate (`python3 scripts/plan_readiness.py --pre-round` over this plan): run at authoring before round 1; the recorded result sits in the staging record of the first round.

### Task 1: Codex session-status surface probe inventory

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- none (all probe observations record in the session task log; no repository file changes)

- [x] Probe inventory, stores and CLI: enumerate the candidate exact-ID status surfaces in the dated rollout stores under both Codex homes and the CLI subcommand surface (`resume`, `queue`, `archive`/`delete`/`unarchive`, `fork`, `migrate-rollouts` inspect mode); mutating surfaces there are capability-inspection probes only (help text and listings are the raw observation, never execution against a real session), recording each probe's command and observation in the task log [class: IMPLEMENTATION_REQUIRED]
- [x] Probe inventory, app-server and transcript internals: probe the app-server JSON-RPC thread/session state read methods (launch `codex app-server`, enumerate its read methods, record one exact-ID query shape) and the rollout JSONL's session and terminal-event semantics (what a concluded transcript contains); a surface left unprobed without a recorded reason is a review blocker [class: IMPLEMENTATION_REQUIRED]
- [x] Probe inventory, auxiliary surfaces: probe `codex debug`, `codex features`, `codex cloud`, `codex exec-server`, and the config.toml session-status keys for exact-ID status capability, recording each probe's command and raw observation [class: IMPLEMENTATION_REQUIRED]
- [x] First-pass evidence re-verification, preserved access: the interrupted first pass (a ZCode session, stood down by operator direction 2026-11-19, its Task 1 verdict `unsupported` preserved as WIP on branch `2026-11-19-codex-incomplete-run-owner-status-unavailable`) is input evidence, never an accepted boundary: read it only via plain file reads in the preserved exec worktree or `git show` against the wip checkpoint, never checkout, stash, or branch mutation [class: IMPLEMENTATION_REQUIRED]
- [x] First-pass evidence re-verification, re-probe: re-run the preserved first pass's probes where the runtime-internal surfaces contradict or extend them, and record per-surface agreement or divergence beside its evidence in the task log [class: IMPLEMENTATION_REQUIRED]
- [x] Read-only witness: given every probe in this task, expects no claim, manifest, lock, or worktree state written, no codex session-store state written, and the peer-owned claim untouched [class: REPOSITORY_TEST]

### Task 2: Provider verdict and evidence record

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/release-evidence/session-status-provider/codex.md` *(new)*

- [x] Grouped-status exclusion: given the grouped agent-center status, expects it recorded as a rejected surface with the origin row's reason (a grouped UI status, not the exact-ID JSON response the contract requires), never as provider evidence [class: IMPLEMENTATION_REQUIRED]
- [x] Contract test per candidate: given one candidate surface, expects a recorded verdict per surface: either it produces a contract-valid exact-ID response (single JSON object, exact `session_id` echo, status in the closed vocabulary) or it does not; nothing in between; the exact-ID response leg applies only to pure-read surfaces (stores, app-server read methods, config inspection), a mutating CLI surface's verdict resting on its capability-inspection observation [class: IMPLEMENTATION_REQUIRED]
- [x] Test ID re-derivation: re-derive the witnessed run's exact session ID from disk at execution (the registered worktree's run manifest identity block `run_session_id`; the authoring-time value `01a1f00b-aa83-7302-beb4-04360f9747d5` is context, never the decision input) and, when its ended state cannot be corroborated, select an alternative exact test session with independently corroborated ended state, recording the selection and its corroboration [class: IMPLEMENTATION_REQUIRED]
- [x] Verdict rule: supported only when some surface yields contract-valid exact-ID responses for the test ID and its `terminal` verdict (when claimed) matches independently corroborated ended state (concluded rollout, no live Codex process attached); a surface unable to decide, or a `terminal` claim without corroboration, takes the unsupported arm [class: IMPLEMENTATION_REQUIRED]
- [x] Evidence record: write `docs/history/release-evidence/session-status-provider/codex.md` opening with the literal verdict line (`Outcome: supported` or `Outcome: unsupported`) and carrying the pinned fields: runtime ID, probed surfaces with per-surface evidence, the facts source's current state, the configured executable path with its SHA-256, exact test session ID, exit status and full JSON response, check timestamp, verifier (the executing session) [class: IMPLEMENTATION_REQUIRED]
- [x] Unsupported shape: when the verdict is `unsupported`, expects the record to state the limitation and that the current refusals stand as the documented posture; no original-stop-cause inference anywhere in the record [class: IMPLEMENTATION_REQUIRED]
- [x] Run the evidence-record gates from the Validation Commands block expecting GREEN; Commit: `docs: record codex session-status provider verdict evidence` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Provider enablement (supported arm), record completion (unsupported arm), and gateway confirmation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/codex_session_status_provider.py` *(new, supported arm only)*
- `scripts/test_codex_session_status_provider.py` *(new, supported arm only)*
- `docs/history/release-evidence/session-status-provider/codex.md`

Primary class anchors (supported arm):
- `codex_session_status` in `scripts/codex_session_status_provider.py`
- `read_provider_command` in `scripts/session_status.py`

- [x] Supported arm, adapter output contract: given a session ID as the sole argument, expects `codex_session_status` to resolve the exact-ID status from the Task 2 selected surface and print exactly one JSON object with the string fields `session_id` (exact echo) and `status` (closed vocabulary), exit 0; no claim, manifest, lock, or registry state read or written [class: IMPLEMENTATION_REQUIRED]
- [x] Supported arm, status derivation rule: the adapter's terminal decision carries the Task 2 verdict rule's corroboration semantics for every queried ID, never only the smoke target: `terminal` only on independently corroborated ended state (concluded rollout, no live Codex process attached), `live` or `paused` per the surface's evidence otherwise, `unresolved` for an ID the surface cannot decide [class: IMPLEMENTATION_REQUIRED]
- [x] Supported arm, selftest isolation: rollout fixtures live in a temp homes root under the test's control (an injectable homes root parameter), never the live user homes or `CODEX_HOME` store [class: IMPLEMENTATION_REQUIRED]
- [x] Supported arm, selftest cells: focused selftest over the adapter covering the contract boundaries (exact-ID echo, closed vocabulary, single-object stdout, nonzero or non-JSON surface output refuses rather than fabricating a status) and the non-ended direction (a live or unknown session ID must not produce `terminal`), RED at execution start, minimal implementation, GREEN [class: REPOSITORY_TEST]
- [x] Supported arm, facts binding: add `session_status_command` naming the adapter's absolute path to the primary checkout's facts document (machine-local configuration, never committed); given the bound document, expects `read_provider_command` to resolve it without refusal [class: IMPLEMENTATION_REQUIRED]
- [x] Supported arm, binding path lifetime: the bound path stays valid for the configuration's lifetime (the primary checkout's post-landing path); an execution-time worktree-path binding records its lifetime caveat beside the SHA-256 in the evidence record [class: IMPLEMENTATION_REQUIRED]
- [x] Supported arm, smoke check: run the provider query CLI against the primary facts document and the exact test session ID; record the command's exit status, the full JSON response, the timestamp, and the configured executable path in the evidence record beside the executable's SHA-256; the conversion refusal semantics stay (only `terminal` proceeds, whatever this response reads) [class: IMPLEMENTATION_REQUIRED]
- [x] Supported arm, verdict reconciliation: a smoke check that does not return contract-valid exact-ID JSON re-opens the verdict: the record completes in the unsupported shape with the refusal recorded verbatim (or the task stops for re-probe), so the Outcome line never contradicts the record's own provider response [class: IMPLEMENTATION_REQUIRED]
- [x] Unsupported arm completion: extend the evidence record's limitation statement with the reproduced refusal (the provider query CLI's unconfigured-provider refusal, run against the primary facts document and the exact test session ID); no adapter, no facts binding, no weakened check [class: IMPLEMENTATION_REQUIRED]
- [x] Gateway confirmation (both arms): the provider-contract focused cells of the existing claim gateway suite (the Validation Commands `-k provider` selector) pass unchanged, and a read-only wiring read confirms the gateway resolves the provider through `read_provider_command` against the primary facts path only; receipt recorded in the task log [class: REPOSITORY_TEST]
- [x] Safety witness (peer state): given the witnessed run's peer-owned claim and worktree, expects no task step to write, take, or convert them; provider queries are pure reads [class: REPOSITORY_TEST]
- [x] Run the Validation Commands block expecting GREEN per the executed arm; Commit: `feat: codex session-status provider enablement and gateway confirmation` (supported) or `docs: complete codex provider unsupported record and gateway confirmation` (unsupported) [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- The former origin `docs/history/backlog/2026-11-19-codex-incomplete-run-owner-status-unavailable.md` is completed by this plan; its disposition is recorded here and the origin is deleted in the archive transition.
