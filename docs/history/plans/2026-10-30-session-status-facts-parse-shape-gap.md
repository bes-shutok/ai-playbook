# Plan: Parse the Fenced Facts Document for Session Status Provider Configuration

Backlog origin: docs/history/backlog/2026-10-30-session-status-facts-parse-shape-gap.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-10-30-plan-review-session-status-facts-parse-shape-gap-r*.md (the highest rN for this source-plan path is authoritative)
Authoring claim: docs/tmp/authoring-claims/2026-10-30-session-status-facts-parse-shape-gap.md (session 01a187b9-0f15-73d1-ad77-61ec1831ebcb)
Execution budget: 1.25h total, largest task 0.75h

## Terms

- **Facts TOML fence:** The first `toml`-labeled fenced block in the primary checkout's `.ai-playbook/facts.md` file.
- **Provider command:** The `session_status_command` string that names an absolute executable and optional arguments.
- **Provider facts input:** The first TOML fence when present, or the complete file as TOML when no TOML fence is present.
- **Conversion refusal:** The existing fail-closed result when provider configuration or its response cannot be trusted; claim and manifest state remain unchanged.
- **ZCode runtime:** The runtime targeted by the completed ZCode conversion plan.
- **Dead-run conversion:** Converting a stale execution claim only after the recorded run identity and prior-owner status pass the existing checks.
- **Exact-ID terminal smoke check:** Querying the configured provider with a session ID and verifying the response names that same ID with terminal status.
- **Supported session-channel source:** The runtime-approved source of a ZCode session ID, used to identify the session being queried.
- **Provider evidence:** The record containing the configured executable digest and exact-ID provider response produced by the smoke check.

## Why

The session-status provider parses the entire Markdown facts file as TOML, so its opening fence causes an unconditional parse refusal in this repository. Reading the TOML body in the repository's established fenced format lets the operator configure the provider while retaining the existing fail-closed checks.

## Gist & Examples

TLDR: Parse fenced facts configuration while retaining bare-TOML compatibility, for efficiency.

Before: `session_status.py` passes `.ai-playbook/facts.md` directly to `tomllib`, which refuses at the opening Markdown fence before looking up `session_status_command`.
After: The provider reads the first TOML-fenced block when present, or parses the full file as TOML when no TOML fence is present, then applies the same command validation and status-response checks.
Edge cases: Missing and unreadable files, malformed fenced or bare TOML, a missing key, a non-string or empty value, a relative executable, and every provider-response failure retain fail-closed behavior.

The existing `facts_paths.py` parser establishes the repository convention of reading TOML keys from the first TOML fence. Reusing the human-readable facts file avoids a second configuration source. Pointing at an executable that serves status directly changes the ownership and invocation contract, while requiring a separate plain-TOML file splits configuration from the established facts document.

## Outcome

Allow the configured session-status provider to be resolved from the repository's fenced facts document without changing conversion safety behavior.

- A configured absolute provider command in the first TOML fence can reach the existing provider query and response validation.
- Invalid or absent provider configuration continues to refuse without changing claim or manifest state.
- A regression test pins the fence-wrapped input shape.

Gate delta: no gate, validator, lock, refusal class, protocol layer, state field, or review duty is added or removed; existing conversion refusals and claim-preservation behavior remain unchanged.

## Assumptions

- The provider configuration owner selects the existing `.ai-playbook/facts.md` TOML fence as the source of `session_status_command`; the selected backlog item requires a shape decision, and the existing `facts_paths.py` parser demonstrates that convention.
- The parser should use standard TOML parsing on the extracted fenced body so the provider key retains TOML string semantics; the narrow `facts_paths.py` key reader is not reused because its documented supported string subset is narrower than general TOML parsing.
- The first TOML-labeled fence is authoritative when present, consistent with the existing facts parser; raw TOML remains accepted when no TOML fence is present to preserve current provider callers and fixtures.
- The completed dead-run conversion plan's provider release evidence and external gate remain unchanged.

Decision points requiring a grill: provider facts shape: select the first TOML-fenced block in `.ai-playbook/facts.md` because `scripts/facts_paths.py` establishes it as the repository convention, 2026-10-30, parser and configuration contract; simpler-design comparison: direct executable source changes the provider configuration owner and separate plain-TOML config splits the established facts source, so retain the existing file shape, 2026-10-30, scope and source resolution.
Scope extensions (grilled): none proposed.
Sources inspected: selected PLAN-PROMPTS entry and origin backlog row; `scripts/session_status.py`; `scripts/execution_claim.sh`; `scripts/facts_paths.py`; `scripts/test_execution_claim.py`; completed `docs/history/plans/completed/2026-10-25-dead-run-conversion-zcode-runtime-reachability.md`; `.ai-playbook/facts.md` and a live raw-TOML parse probe.

## Evaluation Criteria

**Quality dimensions:**
- Configuration correctness: the first TOML fence is parsed as TOML and the configured key receives the existing type and absolute-executable validation.
- Safety: all current provider, response, timeout, and conversion refusal behavior remains fail-closed and preserves claim and manifest state.
- Regression coverage: a suite cell exercises fence-wrapped facts input and distinguishes successful key resolution from malformed or absent configuration.

**Done when:**
- `read_provider_command` resolves `session_status_command` from the first TOML-fenced block while preserving existing validation and refusal behavior.
- `scripts/test_execution_claim.py` pins successful fenced facts parsing and retains coverage for malformed and missing configuration.
- The focused execution-claim suite passes.

**Ship when:**
- Before ZCode advertises dead-run conversion, the runtime configuration owner supplies a supported session-channel source and an absolute `session_status_command` in the primary facts file, runs the exact-ID terminal smoke check, and records provider evidence with the configured executable digest and response; the release owner verifies the record against live configuration. Until then the existing refusal remains active. [class: EXTERNAL_RELEASE_GATE]

## Review Scope

**Explicit must-fix:** findings that weaken conversion refusal behavior, alter claim or manifest state on refusal, parse a different configuration source, or accept unsafe provider commands are always in scope. The completed conversion plan is read-only evidence.

**Production code:**
- `scripts/session_status.py` (Task 1)

**Tests:**
- `scripts/test_execution_claim.py` (Task 2)

**Read-only evidence:**
- `scripts/execution_claim.sh` (review-only)
- `scripts/facts_paths.py` (review-only)
- `docs/history/plans/completed/2026-10-25-dead-run-conversion-zcode-runtime-reachability.md` (review-only)

**Plan-related extension:** implementation and review may change files not listed above only when causally required by a task or a regression it creates. Drop weak or speculative links with a one-line reason.

**Out of scope; reject unless plan-related:**
- Changing conversion authorization, provider response validation, claim or manifest mutation rules, or the completed plan's external release gate.
- Adding a separate provider configuration file or making the configured executable itself the status provider.

## Validation Commands

```bash
python3 scripts/test_execution_claim.py
```

### Task 1: Read provider configuration from the fenced facts block

Context surface: Terms and this task.

Files:
- `scripts/session_status.py`

Primary class anchors:
- `read_provider_command` in `scripts/session_status.py`

Evidence:
- A live probe on `.ai-playbook/facts.md` raises `tomllib.TOMLDecodeError: Invalid statement (at line 1, column 1)` because byte 1 is a Markdown fence.
- `scripts/facts_paths.py` extracts the first TOML-fenced block before resolving a key.

- [ ] Extract the first TOML-fenced block from the configured facts path and parse that body with `tomllib`; when no TOML fence is present, parse the complete file as raw TOML. Retain current missing-file, unreadable-file, malformed-TOML, missing-key, type, empty-value, and absolute-executable refusal behavior. [class: IMPLEMENTATION_REQUIRED]
- [ ] Document in the provider-resolution docstring that configuration is read from the first TOML fence in the primary checkout's facts document; keep provider response validation and the conversion contract unchanged. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pin the fenced facts input and refusal behavior

Context surface: Terms and this task.

Files:
- `scripts/test_execution_claim.py`

Primary class anchors:
- `TestExecutionClaim` in `scripts/test_execution_claim.py`

Evidence:
- Existing provider tests configure the scratch repository's facts file as bare TOML and cover provider configuration and conversion refusal behavior.
- The origin witness shows the actual repository input is fence-wrapped Markdown.

- [ ] Keep existing bare-TOML conversion fixtures working. Add a suite cell with a TOML-fenced facts document that resolves an absolute provider command and exercises the provider gate through the existing conversion path. [class: REPOSITORY_TEST]
- [ ] Pin a fence-wrapped malformed or missing-key input to the existing fail-closed refusal, and assert the claim and manifest remain unchanged on refusal. [class: REPOSITORY_TEST]
- [ ] Run new conversion-path witnesses with `HOME` pinned to the scratch fixture home so provider behavior does not depend on the invoking user home. [class: REPOSITORY_TEST]
- [ ] Preserve all existing provider timeout, output-size, response-shape, and status checks; do not edit the conversion gateway or gate/validator behavior. [class: IMPLEMENTATION_REQUIRED]
