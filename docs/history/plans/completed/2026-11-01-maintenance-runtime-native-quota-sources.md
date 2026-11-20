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

TLDR: select the active runtime's adapter and bind quota evidence to its source.

Before: Codex could consume any session's rollout, the shared cache omitted runtime identity, and unsupported runtimes could use the Codex probe.

After: maintenance identifies the runtime and loads its separate adapter. Codex uses account rate limits; ZCode keeps its current source. For missing details, consult authoritative documentation or ask the runtime/operator, then persist verified details only in that adapter. Until verified, report unknown. Reports carry runtime, source, and observation time; cache mismatches return unknown.

Edge cases: invalid primary, timeout, or auth failure stays unknown; invalid secondary is omitted; retain each returned window's duration and reset.

## Outcome

Maintenance quota decisions use only current evidence from the active runtime's adapter.

- Codex reads `account/rateLimits/read` and keeps primary and secondary windows distinct.
- ZCode keeps its live endpoint and qualifying ZCode-owned log evidence.
- The shared entrypoint selects a separate adapter; missing or unverified details stay unknown until verified and stored in that adapter.
- Reports carry provenance; unknown or stale evidence never inherits another runtime's class.

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

**Explicit must-fix:** runtime routing, Codex windows, governor provenance, and maintenance-facing reports.

**Production code:**
- `scripts/quota_window_probe.py` (Task 1) (`detect_runtime`, `probe_codex`, `probe_zcode`, `run_probe`, and the report construction path)
- `scripts/harness_detection.py` (Task 1) (`detect_harness`)
- `scripts/quota_governor.py` (Task 2) (`refresh`, state write, and `consult`)
- `agents/skills/maintenance/quota-policy.md` (Task 3)
- `agents/skills/maintenance/SKILL.md` (Task 3)
- `agents/skills/maintenance/codex.md` (Task 3)
- `agents/skills/maintenance/zcode.md` (Task 3)

**Tests:**
- Task 1: `scripts/test_quota_window_probe.py`, `scripts/test_harness_detection.py`.
- Task 2: `scripts/test_quota_governor.py`.

**Plan-related extension:** extend another consumer only if execution evidence shows it reads the quota report or must identify the active runtime to satisfy this contract.

**Out of scope; reject unless plan-related:**
- Timed Codex reset wake scheduling; tracked separately in `docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md`.
- New adapters for runtimes without a verified native quota source; those runtimes stay unknown.
- Changes to account quota thresholds, lane policy, or ZCode's existing native quota endpoint.

## Validation Commands

Run the focused suites with the repository's configured test environment:

- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_quota_window_probe.py scripts/test_harness_detection.py -q`
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_quota_governor.py -q`

## Tasks

### Task 1: Fetch and parse Codex quota from its native account source

Context surface: this plan's Terms and Design Invariants.

Files:
- `scripts/quota_window_probe.py`
- `scripts/harness_detection.py`
- `scripts/test_quota_window_probe.py`
- `scripts/test_harness_detection.py`

Primary class anchors:
- `probe_codex` in `scripts/quota_window_probe.py`
- `probe_zcode` in `scripts/quota_window_probe.py`
- `run_probe` in `scripts/quota_window_probe.py`
- `detect_harness` in `scripts/harness_detection.py`

- [x] Given the Codex adapter's explicit runtime identity, expect `probe_codex` to issue the documented read-only account rate-limits JSON-RPC request, including initialize/initialized and a matching response ID. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an unavailable command, unsupported authentication, timeout, malformed response, or response over 1 MiB, expect the bounded request (10 seconds) to clean up its child and return unknown without reading or logging credentials. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a Codex response with a valid primary window, expect the primary usage, returned duration, and reset epoch to be preserved; given an absent or malformed primary with a valid secondary, expect unknown. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a valid primary with an absent or malformed secondary, expect primary to remain usable and secondary to be omitted with a diagnostic; given two valid windows, expect their snapshots to remain separate. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a ZCode response with valid secondary but absent or malformed primary data, expect unknown; given the same response with a valid primary, expect a usable primary. Quiet ZCode logs cannot turn unusable native data into abundant. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a runtime adapter's explicit identity, expect probe API and CLI `--runtime` to use its canonical source mapping; without an override, expect conflicting live signals to return unknown. [class: IMPLEMENTATION_REQUIRED]
- [x] Given each source response or source failure, expect the probe to attach canonical runtime, source identity, and `observed_at_epoch` at response arrival or failure observation; the probe report owns these fields. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an absent or unsupported runtime, expect unknown without calling either Codex or ZCode source code. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the repository caller audit, expect recorded evidence of zero supported runtime consumers before removing Codex rollout discovery, parsing, `--sessions-dir`, and superseded tests. [class: IMPLEMENTATION_REQUIRED]
- [x] Given Codex acquisition/protocol, window parsing, timeouts, auth failures, size limits, cleanup, unsupported routing, conflicting runtime signals, explicit overrides, and response/failure timestamps, expect focused regressions for each outcome; given ZCode secondary-only or invalid-primary data, expect an unknown case plus a valid-primary control. [class: REPOSITORY_TEST]
- [x] Given every Task 1 Codex test that can reach the native source, including protocol, CLI, and runtime-override tests, expect a fake app-server and isolated temporary `HOME`/`PATH`; expect the real Codex executable never to start and credentials never to be read. [class: REPOSITORY_TEST]
- [x] Commit: `fix: read Codex quota from native account limits`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Bind governor cache and consult to the active source

Context surface: this plan's Evidence provenance term and Design Invariants.

Files:
- `scripts/quota_governor.py`
- `scripts/test_quota_governor.py`

Primary class anchors:
- `refresh` in `scripts/quota_governor.py`
- `consult` in `scripts/quota_governor.py`

- [x] Given a probe result with runtime, source, and response-arrival `observed_at_epoch`, expect refresh and stored state to preserve those probe-owned values unchanged, while retaining `computed_at_epoch` separately for classification time. [class: IMPLEMENTATION_REQUIRED]
- [x] Given primary and secondary probe windows, expect state and reports to preserve distinct snapshots with kind, usage, returned duration, reset, and remaining time; given unknown evidence, expect no windows. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an adapter-selected runtime, expect `refresh(..., runtime=...)`, `consult(..., runtime=...)`, and governor CLI `--runtime` (including `--consult`) to use that identity for source mapping and cache validation; auto-detect only without an override and return unknown on conflicting signals. [class: IMPLEMENTATION_REQUIRED]
- [x] Given an older observation competing under the state lock with a newer stored observation, expect the older write to lose; its caller receives the newer matching result or unknown when the stored runtime/source does not match. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a lock timeout, expect cached data only when it is newer and matches the active runtime/source; otherwise expect unknown, never the losing refresh's local class. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a ZCode refresh, expect log mining to remain ZCode-only and only currently qualifying events to support constrained or exhausted; given unusable probe data and no qualifying event, expect unknown while thresholds and lane policy remain unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Given `--runtime codex --refresh` and `--runtime codex --consult` with inherited ZCODE signals, expect Codex routing and matching-cache validation; given other runtime/source and cache cases, expect isolated CLI regressions, using explicit identity or a patched detection seam for other paths. [class: REPOSITORY_TEST]
- [x] Given Codex CLI tests, expect a fake app-server executable and isolated temporary `HOME`/`PATH`; expect the real Codex executable never to start and credentials never to be read. [class: REPOSITORY_TEST]
- [x] Given an unusable ZCode probe and ordinary parseable logs or only out-of-window quota events, expect unknown; given current qualifying positive-event controls, expect constrained and exhausted outcomes respectively. [class: REPOSITORY_TEST]
- [x] Given probe-owned runtime, source, observation time, separate primary and secondary windows, their durations, usage, and reset times, expect refresh and `--consult` to preserve every value while keeping `computed_at_epoch` distinct. [class: REPOSITORY_TEST]
- [x] Given older-high/newer-low and older-low/newer-high interleavings, expect the older refresh not to overwrite the winner; given a matching winner, expect both callers to report it, and given a mismatched runtime/source, expect unknown. [class: REPOSITORY_TEST]
- [x] Given a lock timeout with newer matching, stale, mismatched, or absent cache, expect only the newer matching result to be returned and all other cases to be unknown. [class: REPOSITORY_TEST]
- [x] Commit: `fix: bind quota governor results to runtime`. [class: IMPLEMENTATION_REQUIRED]

### Task 3: Document quota policy and separate runtime adapters

Context surface: this plan's runtime adapter invariant and report contract in Outcome.

Files:
- `agents/skills/maintenance/quota-policy.md`
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/codex.md` *(new)*
- `agents/skills/maintenance/zcode.md`

Primary class anchors:
- `### Step 4: quota leg` in `agents/skills/maintenance/quota-policy.md`
- `### Step 0: context load` in `agents/skills/maintenance/SKILL.md`
- `Quota leg` in `agents/skills/maintenance/zcode.md`

- [x] Given a maintenance turn on any runtime, expect the shared entrypoint to identify the runtime and load its separate adapter without including agent-specific quota commands, endpoints, or window details in the main body. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a selected adapter, expect the shared quota leg to pass its canonical runtime ID via `--runtime` to the probe and governor refresh/consult; keep source-specific acquisition details in that adapter. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a missing adapter or quota source, expect the shared workflow to discover requirements from authoritative runtime documentation or request details from the runtime/operator, then persist verified findings only in a separate runtime adapter; until verified, report unknown and never borrow another runtime's evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] Given realistic maintenance contexts for a missing adapter, an unverified source, and a verified adapter, expect source discovery or request, separate-adapter-only persistence after verification, and unknown evidence until then; record the contexts and observed outputs in the Task 3 log. [class: IMPLEMENTATION_REQUIRED]
- [x] Given Codex and ZCode adapter documents, expect the Codex adapter to own its verified account-rate protocol and response contract, the ZCode adapter to own its current source and constrained log evidence, and the shared quota policy to contain no agent-specific details. [class: IMPLEMENTATION_REQUIRED]
- [x] Given usable quota evidence, expect reports to include provenance and separate Codex primary and secondary data while leaving the stop threshold unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the separate timed Codex reset-wake workflow, expect it to remain out of scope and use only validated Codex primary data. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: explain runtime-native maintenance quota sources`. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-01-maintenance-runtime-native-quota-sources.md` is covered by this completed runtime-native quota implementation. Its durable disposition is this archived plan and the completed ownership-registry row for the origin.
