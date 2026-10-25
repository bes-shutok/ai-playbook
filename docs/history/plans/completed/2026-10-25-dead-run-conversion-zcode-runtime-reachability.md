# Plan: Clarify ZCode dead-run conversion limits and manifest scan results

Backlog origin: docs/history/backlog/2026-10-25-dead-run-conversion-zcode-runtime-gap.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-10-25-plan-review-dead-run-conversion-zcode-runtime-reachability-r*.md (the highest rN for this source-plan path is authoritative)
Authoring claim: docs/tmp/authoring-claims/2026-10-25-dead-run-conversion-zcode-runtime-gap.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)
Execution budget: 1.25h total, largest task 1.0h

## Terms

- **Dead-run conversion:** taking over an execution claim only after the recorded run identity and prior-owner status meet the completed conversion plan's checks.
- **Registered-manifest scan:** the stale-preservation scan that checks the facts-resolved manifest path in each registered worktree before claim conversion or sweeping.
- **Primary-side mirror:** a copy of a registered worktree's run manifest stored under the primary checkout's matching run path.
- **ZCode session channel:** the active session identifier exposed to `scripts/session_channel.py` by the ZCode runtime; the incident record says ZCode provides none of the currently supported environment variables.
- **Provider smoke evidence:** the exact-ID terminal response record required by the completed conversion plan before a runtime advertises conversion.

## Why

The 2026-10-25 ZCode resume attempt could not reach dead-run conversion because ZCode supplied no supported session identifier and the primary facts lacked the already-required status provider. The registered-manifest scan also reduced missing facts, a manifest symlink, and multiple manifests to generic results, causing separate diagnosis before the run could proceed.

## Gist & Examples

Title: Clarify ZCode dead-run conversion limits and manifest scan results
TLDR: State when ZCode conversion is unsupported and identify the worktree behind scan refusals, for efficiency.
Before: A ZCode conversion attempt can stop on an empty session channel or a generic inconclusive or multiple-manifest result, and the next operator must rediscover the failing worktree.
After: The ZCode overlay names the unsupported session-channel boundary, and scan results identify each refusal cause and worktree; one byte-identical primary-side mirror is recognized as the same manifest identity.
Edge cases: A different manifest copy or a second non-primary worktree remains ambiguous; conversion remains unsupported until the existing provider and session-channel release evidence is complete.

A ZCode operator should see the documented unsupported boundary instead of assuming Codex's `CODEX_SESSION_ID` source applies to ZCode. When a registered worktree lacks readable facts, the scan should name that worktree and preserve the claim. When the primary checkout contains an exact byte copy of the canonical manifest, the scan should count one identity; different bytes must still refuse as ambiguous.

## Outcome

Make the ZCode conversion boundary explicit and make registered-manifest scan results actionable while keeping the existing provider safety gate.

- The ZCode overlay states that conversion remains unsupported while no trusted session identifier source is available.
- Inconclusive scan results identify the registered worktree and refusal cause without following symlinks or falling back to a guessed manifest path.
- A byte-identical primary-side manifest mirror does not create a false duplicate, while conflicting or additional worktree manifests remain ambiguous.

Gate delta: no gate, validator, lock, protocol layer, state field, or review duty is added; remove the duplicate-manifest refusal only when the extra record is the exact byte copy in the primary checkout, while retaining the refusal for differing copies and additional registered worktrees.

## Assumptions

- The runtime in scope is ZCode, as recorded in the 2026-10-25 parked-run witness; the current Codex session's `CODEX_SESSION_ID` does not establish ZCode support.
- ZCode currently has no supported session-channel source; do not invent a source. Document the unsupported disposition until the runtime owner supplies one.
- The primary facts file has no `session_status_command`, and no provider smoke-evidence record exists. The completed conversion plan's existing release gate continues to control when conversion may be advertised.
- The identity exception is limited to one primary-side mirror whose bytes exactly match the canonical registered-worktree manifest. Any disagreement or additional non-primary copy still refuses.

Decision points requiring a grill: ZCode channel: record unsupported because the incident witness names no supported source and the selected entry permits this disposition; primary mirror: count an exact primary-side byte copy as the canonical run identity per the selected entry and lesson 218; provider: retain setup and smoke evidence as the existing external release gate in the completed conversion plan.
Scope extensions (grilled): none proposed.
Sources inspected: selected PLAN-PROMPTS entry; 2026-10-25 runtime-gap origin; 2026-10-23 coverage-residual sibling; completed 2026-10-21 conversion plan; scheduler-state incident witness; `scripts/session_channel.py`; `scripts/session_status.py`; `scripts/execution_claim.sh`; `scripts/test_execution_claim.py`; development lesson 218; current maintenance ZCode overlay.

## Standing constraints

- Do not infer ZCode support from the current Codex session's environment or from Codex's `CODEX_SESSION_ID` fallback.
- Keep conversion disabled for ZCode until a trusted session channel and the completed plan's provider evidence are verified.
- Preserve claim and manifest bytes on every refusal; never follow a symlink or replace missing facts with a default path.
- Keep the existing exact owner, run identity, registered worktree, provider response, and owned-lock requirements unchanged.

## Evaluation Criteria

**Quality dimensions:**
- Refusal clarity: every inconclusive registered-manifest result identifies the worktree and the specific discovery cause.
- Safety: exact primary-side mirrors are distinguished by byte equality, and conflicting or additional registered manifests remain fail-closed with claim and manifest bytes unchanged.
- Runtime accuracy: the ZCode overlay does not imply that an unsupported or unconfigured runtime can convert claims.

**Done when:**
- The ZCode overlay states the unsupported boundary and its release condition without changing gateway behavior.
- Scan diagnostics identify missing or unusable per-worktree facts and symlinked manifest paths.
- An exact primary-side mirror is treated as the same identity, while different or additional worktree manifests remain ambiguous.
- The focused execution-claim suite and repository guard checks pass.

**Ship when:**
- Before ZCode advertises dead-run conversion, the runtime configuration owner supplies a supported session-channel source and an absolute `session_status_command` in the primary facts, runs the exact-ID terminal smoke check, and records the provider evidence with the configured executable digest and response; the release owner verifies the record against live configuration. Until then the existing refusal remains active. [class: EXTERNAL_RELEASE_GATE]

## Review Scope

**Explicit must-fix:** findings that weaken refusal behavior, misidentify the canonical manifest, treat the current Codex channel as ZCode evidence, or overstate runtime readiness are always in scope.

**Documentation:**
- `agents/skills/maintenance/zcode.md` (Task 1)

**Production code:**
- `scripts/execution_claim.sh` (Task 2)

**Tests:**
- `scripts/test_execution_claim.py` (Task 2)

**Read-only evidence:**
- `docs/history/plans/completed/2026-10-21-dead-run-resume-claim-conversion.md` (review-only)
- `docs/history/backlog/2026-10-25-dead-run-conversion-zcode-runtime-gap.md` (review-only)
- `docs/maintenance/development_lessons.md` (review-only)
- `scripts/session_channel.py` (review-only)
- `scripts/session_status.py` (review-only)

**Plan-related extension:** implementation and review may change files not listed above only when causally required by a task or a regression it creates. Drop weak or speculative links with a one-line reason.

**Out of scope; reject unless plan-related:**
- Adding an unverified ZCode session environment source.
- Configuring the machine-specific provider or fabricating provider smoke evidence.
- Changing claim conversion, completed-run verification, lock acquisition, or release semantics.
- Implementing the coverage-residual sibling's broader refusal-path test inventory.

## Validation Commands

```bash
python3 scripts/test_execution_claim.py
bash scripts/check_maintenance_pins.sh
python3 scripts/machinery_inventory.py --check
bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-25-dead-run-conversion-zcode-runtime-reachability.md
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh added-lines --base main -- scripts/execution_claim.sh scripts/test_execution_claim.py
PUBLIC_HYGIENE_REPO_ROOT="$(git rev-parse --show-toplevel)" bash scripts/scan-public-hygiene.sh --files docs/history/plans/2026-10-25-dead-run-conversion-zcode-runtime-reachability.md scripts/execution_claim.sh scripts/test_execution_claim.py
```

## Design Invariants (CR Guard)

- The completed conversion plan's trust boundary stays intact: only a provider response naming the exact requested prior session and `terminal` permits conversion; missing configuration or unsupported session identity keeps the existing refusal.
- The completed conversion plan's manifest identity remains bound to the exact plan and registered worktree. The new mirror rule admits only a byte-identical primary-side copy of the canonical manifest; it does not admit a differing or second peer-worktree manifest.
- Conversion continues to preserve claims and manifests on refusal and releases only locks owned by the conversion gateway. This plan changes scan evidence only.

### Task 1: Record the ZCode unsupported conversion boundary

Context surface: the plan's Terms, this task, `## Design Invariants (CR Guard)`, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/maintenance/zcode.md`

- [x] Given ZCode exposes none of the supported session-channel environment variables, document that dead-run conversion remains unsupported and refuses until a trusted source is provided. [class: IMPLEMENTATION_REQUIRED]
- [x] State that Codex's `CODEX_SESSION_ID` fallback is not evidence of ZCode support, and name the existing provider smoke evidence as the enablement condition. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: clarify ZCode dead-run conversion support` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Attribute registered-manifest scan outcomes

Context surface: the plan's Terms, this task, `## Design Invariants (CR Guard)`, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/execution_claim.sh`
- `scripts/test_execution_claim.py`

Primary class anchors:
- `scan_registered_manifest` in `scripts/execution_claim.sh`

- [x] Given registered-worktree facts are missing, unreadable, or lack `tmp_dir`, return an inconclusive result that names the worktree and the specific discovery failure, with no guessed fallback path. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a manifest path is a symlink, name that registered worktree and path, refuse without following it, and preserve the claim and manifest bytes. [class: IMPLEMENTATION_REQUIRED]
- [x] Given exactly one canonical manifest plus its byte-identical primary-side mirror, report one identity and retain the canonical worktree; given differing bytes or an additional non-primary manifest, preserve the multiple-manifest refusal. [class: IMPLEMENTATION_REQUIRED]
- [x] Propagate each inconclusive scan's worktree and discovery cause through both the `take` refusal and stale-sweep reason; assert both caller-visible outputs in focused regressions, including unchanged bytes on refusal. [class: REPOSITORY_TEST]
- [x] Commit: `fix: attribute dead-run manifest scan refusals` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-25-dead-run-conversion-zcode-runtime-gap.md: covered by this plan; the origin row left the backlog top level at the authoring landing and sits archived with its `Status: covered` flip at docs/history/backlog/completed/2026-10-25-dead-run-conversion-zcode-runtime-gap.md. The ZCode conversion boundary (session channel and status provider) stays the external release gate recorded under Ship when; the r2 review residuals ride docs/history/backlog/2026-10-25-manifest-scan-cause-derivation-and-primary-symlink-coverage.md.
