# Plan: Keep quota evidence within its runtime

Backlog origin: docs/history/backlog/2026-11-01-quota-governor-cross-runtime-evidence.md
Driving force: code-quality + automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-01-plan-review-quota-governor-runtime-evidence-r*.md
Execution budget: 1.0h total, largest task 1.0h
Authoring claim: 2026-11-01-quota-governor-cross-runtime-evidence.md (session 01a19171-0584-7930-b1ad-434c88bba61d)

## Terms

- **Active runtime:** the agent runtime detected for the current quota refresh.
- **Codex:** the runtime whose maintenance turn observed the false quota stop.
- **Log-mined evidence:** quota events parsed from a runtime's local command log.
- **Primary window:** the active runtime's short-term quota window used for stop decisions.
- **Secondary window:** a longer-term quota window that provides context but does not by itself prove short-term exhaustion.
- **ZCode:** the runtime that owns the CLI log containing the observed provider 1308 event.
- **Unknown runtime:** a quota refresh where runtime detection does not identify an evidence owner.
- **1308 event:** a provider rate-limit record that the current miner treats as quota exhaustion evidence.

## Why

The quota governor probes the active runtime but also mines ZCode's log for every runtime. A recent ZCode 1308 event therefore made a continuing Codex turn look exhausted, stopping both maintenance lanes. The evidence source must stay tied to the runtime it describes so the existing stop policy acts on the right quota state.

## Gist & Examples

TLDR: scope mined quota events to their owning runtime, because code-quality and automation depend on maintenance acting on trustworthy quota evidence.

Before (today): Codex reports a continuing secondary window at 27% and no primary reading, while ZCode's log contains a recent 1308 event. The shared miner combines them and the governor defers both execution and authoring.

After (this plan): the Codex refresh does not consume ZCode log events, so the ZCode event cannot mark Codex exhausted. A ZCode refresh continues to use its own log, and a genuine active-runtime primary-window exhaustion still follows the existing stop policy.

Edge cases: missing primary data keeps current behavior when the active runtime is known; an unknown runtime without owned evidence remains unknown; a secondary-window value alone never proves primary-window exhaustion.

## Outcome

Maintenance quota decisions use evidence from the runtime that produced it, so one runtime's rate limit cannot stop another runtime's work.

- Codex maintenance continues when only ZCode's log records quota exhaustion.
- ZCode's own exhaustion evidence and genuine active-runtime primary exhaustion still trigger the existing policy.
- Missing primary data keeps existing behavior when the active runtime is known; an unknown runtime without evidence from an identified owner stays unknown under existing fail-open policy.

Gate delta: none. The plan corrects the evidence supplied to the existing classifier; it adds no refusal, check, gate, lock, schema field, or review duty and removes none.

## Assumptions

- The default log directory and the mined 1308 records belong to ZCode, based on `scripts/quota_governor.py`, `scripts/quota_pressure_stats.py`, and the investigation. An unknown runtime has no identified log owner and cannot use that evidence.
- The shared governor remains responsible for quota policy; this change scopes its existing log input and does not alter thresholds or probe parsing.
- The older account-identity mismatch remains a separate open issue because it does not share the runtime-source defect established here.
- Codex reset-time scheduling remains a separate backlog item because this runtime currently exposes no verified timed wake action.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the Codex-plus-ZCode-event case no longer becomes exhausted, while ZCode-owned and true active-runtime exhaustion retain their current results.
- Maintainability: runtime ownership is clear at the existing mining and classification boundary without a new quota state format or policy layer.
- Test coverage: focused regressions exercise Codex cross-runtime contamination, the ZCode control, genuine primary exhaustion, and unknown or missing inputs.

**Done when:** repository regression coverage passes and demonstrates each of the listed runtime-attribution outcomes without changing the governor's thresholds or lane policy.

**Ship when:** none; the local governor and its tests are the complete implementation boundary.

## Design Invariants

- A quota event may affect only the runtime whose evidence source produced it.
- Secondary-window data does not prove primary-window exhaustion.
- Existing exhaustion thresholds, per-lane policy, and probe parsing remain unchanged. An unknown runtime cannot consume ZCode evidence and stays under existing unknown/fail-open handling when no identified owner provides evidence.
- No scheduler, timer, host daemon, or new blocking machinery is introduced by this change.

## Review Scope

**Explicit must-fix:** runtime attribution at the quota governor's existing refresh and mining boundary, plus regressions that prove the observed false stop is gone and true stop behavior remains.

**Production code:**
- `scripts/quota_governor.py` (Task 1)

**Tests:**
- Regression test files and fixtures are selected during execution from the repository's current tests; no supporting test path is frozen here.

**Plan-related extension:** changes may extend beyond the named source only when execution evidence shows they are required to implement this plan or correct a regression it introduces.

**Out of scope; reject unless plan-related:**
- `scripts/quota_window_probe.py`; the investigation found that the probe already identifies the active runtime and is not where the foreign log event enters the decision.
- Codex reset-time wake scheduling; that capability is tracked separately in `docs/history/backlog/2026-11-01-codex-maintenance-quota-reset-wake.md`.
- Account-identity quota attribution; that remains tracked in `docs/history/backlog/2026-10-10-quota-wall-stop-account-mismatch.md`.

## Validation Commands

Execution will select the focused regression and related quota-governor suites from the current repository evidence, then record the exact commands and results in the execution manifest. No supporting test paths or task commands are frozen in this plan.

## Tasks

### Task 1: Scope mined quota evidence to the active runtime

Context surface: this plan's Terms and this task.

Files:
- `scripts/quota_governor.py`

Primary class anchors:
- `refresh` in `scripts/quota_governor.py`

- [x] Given Codex has no primary reading and ZCode alone has a recent 1308 event, expects Codex not exhausted and both lanes eligible under existing policy. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given ZCode has its own current exhaustion event or the active runtime's primary window is exhausted, expects the existing exhaustion pause. [class: IMPLEMENTATION_REQUIRED]
- [x] Unknown witness: given runtime detection is unrecognized and only ZCode has an exhaustion event, expects an unknown result under existing fail-open policy, not exhaustion. [class: IMPLEMENTATION_REQUIRED]
- [x] Add focused regression coverage for Codex contamination, the ZCode control, real primary exhaustion, and unknown input; select tests from repository evidence. [class: REPOSITORY_TEST]
- [x] Scope mined events to the runtime that owns their source without changing thresholds, probe parsing, classification, or lane policy. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the selected focused and related quota-governor checks; confirm all four scenarios above. [class: REPOSITORY_TEST]
- [x] Commit: `fix: scope quota evidence to its runtime`. [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-01-quota-governor-cross-runtime-evidence.md` was completed by this plan and is deleted in this archive transition.
