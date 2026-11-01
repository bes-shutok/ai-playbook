# Plan: Read maintenance quota from each runtime's native source

Backlog origin: docs/history/backlog/2026-11-01-maintenance-runtime-native-quota-sources.md
Required agent type: codex
Driving force: automation + code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-01-plan-review-maintenance-runtime-native-quota-sources-r*.md
Execution budget: 3.0h total, largest task 1.5h
Authoring claim: 2026-11-01-maintenance-runtime-native-quota-sources.md (session 01a19171-0584-7930-b1ad-434c88bba61d)

## Terms

- **Active runtime:** the agent runtime identified for the current maintenance turn.
- **Runtime adapter:** a separate runtime-owned maintenance document and probe mapping that supplies one agent's verified quota source and response contract.
- **Account governor:** the shared quota classifier and cache used by maintenance consumers.
- **Codex app-server:** the local JSON-RPC process that exposes Codex account rate limits.
- **Codex rollout:** a session transcript file that may contain rate-limit records but is not the current account quota source.
- **Native quota source:** the provider or agent runtime's own current quota interface.
- **Primary window:** the runtime's short-term window used by the existing stop threshold.
- **Secondary window:** a separate longer-term window that remains report-only under current policy.
- **Evidence provenance:** the runtime, source, and observation time attached to a quota result.
- **Source observation time:** the instant the quota source response arrives; distinct from the governor's existing classification time.
- **Unknown evidence:** a result with no verified runtime/source, or no usable primary window and no qualifying supplementary quota evidence.
- **Supplementary quota evidence:** a ZCode-owned event that still meets the existing constrained or exhausted threshold and cadence rule.
- **Fail-open lane default:** existing maintenance behavior when quota evidence is unknown or unusable; this plan leaves that behavior unchanged.

## Why

The governor reported ZCode's 97% exhaustion evidence during a Codex maintenance turn, while Codex's native account response showed a different primary window. Codex still reads an unrelated rollout file and the shared governor cache does not identify which runtime or source produced its class, so a prior result can stop the wrong maintenance run.

## Gist & Examples

TLDR: identify the active runtime, load its quota adapter, and validate cache ownership so automation uses trustworthy limits without putting agent-specific instructions in the shared maintenance entrypoint.

Before: a Codex turn can consume the newest rollout from any Codex session, a shared unlabelled cache can carry ZCode exhaustion into the Codex stop decision, and an unsupported runtime can fall through to the Codex probe.

After: the shared maintenance entrypoint identifies the active runtime and loads that runtime's separate adapter. Codex uses its structured account-rate response, ZCode keeps its current quota source, and a runtime without a verified adapter is researched through authoritative documentation or clarified with the runtime/operator before its details are added as a separate adapter. Until then its evidence stays unknown. The shared report and cache identify runtime, source, and observation time; a mismatch never borrows another runtime's class.

Edge cases: missing or malformed primary data stays unknown even if secondary data parses; a malformed secondary is omitted without discarding a valid primary; transport timeout or auth failure stays unknown; primary and secondary preserve their returned durations and reset epochs.

## Outcome

Maintenance quota decisions use the active runtime's current native quota evidence and never inherit another runtime's cached percentage or exhaustion event.

- Codex uses its current `account/rateLimits/read` response and keeps primary and secondary windows distinct.
- ZCode continues using its live quota endpoint and bounded ZCode-owned log evidence; ordinary or stale logs cannot turn missing native data into abundant.
- The top-level maintenance skill selects a separate adapter by runtime identity. Agent-specific quota details stay in their adapters; a missing source is researched in authoritative runtime documentation or requested, then persisted separately only after verification. Until then report unknown.
- Reports carry source provenance, and unknown or stale evidence never inherits another runtime's class.

Gate delta: add runtime, source, `observed_at_epoch`, and separate primary/secondary window snapshots to the existing governor pressure record and report; the probe owns and timestamps source evidence at response arrival, while the governor preserves it and uses existing `computed_at_epoch` only for classification time. These data additions pay for the witnessed 97% cross-runtime misattribution, stale cache ownership, and the plan's requirement to report both native windows. Add no refusal class, gate, lock, validator, ledger, or required ceremony; unknown remains fail-open under the existing lane policy.

## Assumptions

- Codex app-server `account/rateLimits/read` is the automated Codex source. The probe uses the local `codex app-server` stdio JSON-RPC protocol under the existing Codex CLI installation and authentication; a missing command, unsupported authentication, or failed request reports unknown and never reads credentials. Basis: investigation source audit and [Codex App Server rate limits](https://learn.chatgpt.com/docs/app-server#rate-limits-chatgpt).
- ZCode's current quota endpoint and log-mining source remain owned by the ZCode runtime. Basis: `scripts/quota_window_probe.py`, `scripts/quota_governor.py`, and `agents/skills/maintenance/zcode.md`.
- Existing stop thresholds, lane policy, and fail-open behavior for unknown evidence remain unchanged. Quiet logs alone do not establish an abundant quota class. Basis: `agents/skills/maintenance/quota-policy.md` and the backlog acceptance criteria.
- The timed Codex reset wake is a separate backlog item and consumes only a validated Codex primary reset. Basis: `docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md`.
- The user-directed adapter boundary keeps the shared maintenance entrypoint runtime-neutral. A new runtime's source details are looked up or requested and then recorded in a separate adapter before use; an unverified source remains unknown.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each runtime reads only evidence owned by that runtime.
- Observability: usable and unknown reports identify runtime, source, observation time, window kind, duration, usage, and reset where available.
- Regression coverage: focused tests cover native parsing, source isolation, cache mismatch, and unknown evidence.

**Done when:** focused probe and governor regressions pass; the maintenance quota procedure explains runtime binding and native-source selection; unsupported or unusable evidence remains unknown without changing existing lane thresholds.

**Ship when:** none; implementation and verification are repository-local.

## Design Invariants

- Codex quota does not depend on the newest rollout anywhere in the sessions tree.
- `run_probe` routes only `codex` and `zcode` explicitly; every other runtime reports unknown without invoking either adapter.
- A usable Codex quota result requires a valid current primary window; a secondary-only response is unknown.
- A malformed secondary window is omitted with a diagnostic while a valid primary remains usable.
- A usable ZCode result also requires a valid current primary window; secondary-only data is unknown.
- ZCode log evidence cannot affect Codex, and Codex cache data cannot affect ZCode.
- Codex window names, durations, usage, and reset epochs come from the live native response and remain separate.
- Governor refresh and consult reports preserve the primary and secondary window details separately, including each returned duration, usage, and reset.
- An older observation cannot overwrite a newer governor observation; consult never returns a cached record whose runtime/source differs from the active runtime/source.
- If a ZCode native probe fails, return unknown unless a current ZCode-owned log event meets the existing constrained or exhausted rule.
- Unknown or failed evidence never becomes an all-clear and never inherits another runtime's cached class.
- The existing threshold and lane policy remains unchanged; timed reset scheduling remains out of scope.
- The top-level maintenance skill contains only runtime-neutral adapter selection and fallback; Codex and ZCode quota details live in separate runtime adapters.
- When a runtime's adapter or quota source is missing, the workflow can research authoritative documentation or ask for the missing details, then add a separate adapter only after verification; until then the runtime reports unknown.

## Review Scope

**Explicit must-fix:** runtime detection to native-source routing, Codex window parsing, governor refresh/cache consultation provenance, and maintenance-facing instructions and reports.

**Production code:**
- `scripts/quota_window_probe.py` (Task 1) (`detect_runtime`, `probe_codex`, `probe_zcode`, `run_probe`, and the report construction path)
- `scripts/harness_detection.py` (Task 1) (`detect_harness`)
- `scripts/quota_governor.py` (Task 2) (`refresh`, state write, and `consult`)
- `agents/skills/maintenance/quota-policy.md` (Task 3)
- `agents/skills/maintenance/SKILL.md` (Task 3)
- `agents/skills/maintenance/codex.md` (Task 3)
- `agents/skills/maintenance/zcode.md` (Task 3)

**Tests:**
- Select focused probe and governor tests from repository evidence during execution; do not freeze supporting test paths here.

**Plan-related extension:** extend another consumer only if execution evidence shows it reads the quota report or must identify the active runtime to satisfy this contract.

**Out of scope; reject unless plan-related:**
- Timed Codex reset wake scheduling; tracked separately in `docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md`.
- New adapters for runtimes without a verified native quota source; those runtimes stay unknown.
- Changes to account quota thresholds, lane policy, or ZCode's existing native quota endpoint.

## Validation Commands

Run the focused suites with the repository's configured test environment:

- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_quota_window_probe.py -q`
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_quota_governor.py -q`

## Tasks

### Task 1: Fetch and parse Codex quota from its native account source

Context surface: this plan's Terms, Design Invariants, and the native-source selection decision in `docs/history/backlog/PLAN-PROMPTS.md` under `maintenance-runtime-native-quota-sources`.

Files:
- `scripts/quota_window_probe.py`
- `scripts/harness_detection.py`

Primary class anchors:
- `probe_codex` in `scripts/quota_window_probe.py`
- `probe_zcode` in `scripts/quota_window_probe.py`
- `run_probe` in `scripts/quota_window_probe.py`
- `detect_harness` in `scripts/harness_detection.py`

- [ ] Given the Codex adapter's explicit runtime identity, expect `probe_codex` to issue the documented read-only account rate-limits JSON-RPC request, including initialize/initialized and a matching response ID. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an unavailable command, unsupported authentication, timeout, malformed response, or response over 1 MiB, expect the bounded request (10 seconds) to clean up its child and return unknown without reading or logging credentials. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a Codex response with a valid primary window, expect the primary usage, returned duration, and reset epoch to be preserved; given an absent or malformed primary with a valid secondary, expect unknown. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a valid primary with an absent or malformed secondary, expect primary to remain usable and secondary to be omitted with a diagnostic; given two valid windows, expect their snapshots to remain separate. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a ZCode response with valid secondary but absent or malformed primary data, expect unknown; given the same response with a valid primary, expect a usable primary. Quiet ZCode logs cannot turn unusable native data into abundant. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a runtime adapter's explicit identity, expect probe API and CLI `--runtime` to use its canonical source mapping; without an override, expect conflicting live signals to return unknown. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given each source response or source failure, expect the probe to attach canonical runtime, source identity, and `observed_at_epoch` at response arrival or failure observation; the probe report owns these fields. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an absent or unsupported runtime, expect unknown without calling either Codex or ZCode source code. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the repository caller audit, expect recorded evidence of zero supported runtime consumers before removing Codex rollout discovery, parsing, `--sessions-dir`, and superseded tests. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given Codex acquisition/protocol, window parsing, timeouts, auth failures, size limits, cleanup, unsupported routing, conflicting runtime signals, explicit overrides, and response/failure timestamps, expect focused regressions for each outcome; given ZCode secondary-only or invalid-primary data, expect an unknown case plus a valid-primary control. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: read Codex quota from native account limits`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Bind governor cache and consult to the active source

Context surface: this plan's Evidence provenance and Unknown evidence terms, and the cross-runtime cache decision in `docs/history/backlog/PLAN-PROMPTS.md` under `maintenance-runtime-native-quota-sources`.

Files:
- `scripts/quota_governor.py`

Primary class anchors:
- `refresh` in `scripts/quota_governor.py`
- `consult` in `scripts/quota_governor.py`

- [ ] Given a probe result with runtime, source, and response-arrival `observed_at_epoch`, expect refresh and stored state to preserve those probe-owned values unchanged, while retaining `computed_at_epoch` separately for classification time. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given primary and secondary probe windows, expect state and reports to preserve distinct snapshots with kind, usage, returned duration, reset, and remaining time; given unknown evidence, expect no windows. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an adapter-selected runtime, expect `refresh(..., runtime=...)`, `consult(..., runtime=...)`, and governor CLI `--runtime` (including `--consult`) to use that identity for source mapping and cache validation; auto-detect only without an override and return unknown on conflicting signals. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given an older observation competing under the state lock with a newer stored observation, expect the older write to lose; its caller receives the newer matching result or unknown when the stored runtime/source does not match. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a lock timeout, expect cached data only when it is newer and matches the active runtime/source; otherwise expect unknown, never the losing refresh's local class. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a ZCode refresh, expect log mining to remain ZCode-only and only currently qualifying events to support constrained or exhausted; given unusable probe data and no qualifying event, expect unknown while thresholds and lane policy remain unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given `--runtime codex --refresh` and `--runtime codex --consult` with inherited ZCODE signals, expect Codex routing and matching-cache validation; given other runtime/source and cache cases, expect isolated CLI regressions, using explicit identity or a patched detection seam for other paths. [class: REPOSITORY_TEST]
- [ ] Given an unusable ZCode probe and ordinary parseable logs or only out-of-window quota events, expect unknown; given current qualifying positive-event controls, expect constrained and exhausted outcomes respectively. [class: REPOSITORY_TEST]
- [ ] Given probe-owned runtime, source, observation time, separate primary and secondary windows, their durations, usage, and reset times, expect refresh and `--consult` to preserve every value while keeping `computed_at_epoch` distinct. [class: REPOSITORY_TEST]
- [ ] Given older-high/newer-low and older-low/newer-high interleavings, expect the older refresh not to overwrite the winner; given a matching winner, expect both callers to report it, and given a mismatched runtime/source, expect unknown. [class: REPOSITORY_TEST]
- [ ] Given a lock timeout with newer matching, stale, mismatched, or absent cache, expect only the newer matching result to be returned and all other cases to be unknown. [class: REPOSITORY_TEST]
- [ ] Commit: `fix: bind quota governor results to runtime`. [class: IMPLEMENTATION_REQUIRED]

### Task 3: Document quota policy and separate runtime adapters

Context surface: this plan's Design Invariants and the report contract in `docs/history/backlog/PLAN-PROMPTS.md` under `maintenance-runtime-native-quota-sources`.

Files:
- `agents/skills/maintenance/quota-policy.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/codex.md` *(new)*
- `agents/skills/maintenance/zcode.md`

Primary class anchors:
- `### Step 4: quota leg` in `agents/skills/maintenance/quota-policy.md`
- `This skill stays runtime-agnostic.` in `agents/skills/maintenance/SKILL.md`
- `Quota leg` in `agents/skills/maintenance/zcode.md`

- [ ] Given a maintenance turn on any runtime, expect the shared entrypoint to identify the runtime and load its separate adapter without including agent-specific quota commands, endpoints, or window details in the main body. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a selected adapter, expect the shared quota leg to pass its canonical runtime ID via `--runtime` to the probe and governor refresh/consult; keep source-specific acquisition details in that adapter. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a missing adapter or quota source, expect the shared workflow to discover requirements from authoritative runtime documentation or request details from the runtime/operator, then persist verified findings only in a separate runtime adapter; until verified, report unknown and never borrow another runtime's evidence. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given Codex and ZCode adapter documents, expect the Codex adapter to own its verified account-rate protocol and response contract, the ZCode adapter to own its current source and constrained log evidence, and the shared quota policy to contain no agent-specific details. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given usable quota evidence, expect reports to include provenance and separate Codex primary and secondary data while leaving the stop threshold unchanged. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the separate timed Codex reset-wake workflow, expect it to remain out of scope and use only validated Codex primary data. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `docs: explain runtime-native maintenance quota sources`. [class: IMPLEMENTATION_REQUIRED]
