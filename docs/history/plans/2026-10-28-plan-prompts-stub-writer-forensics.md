# Plan: Identify the PLAN-PROMPTS Stub Writer

Backlog origin: docs/history/backlog/2026-10-28-plan-prompts-stub-rewrite-origin.md
Driving force: correctness
Authoring claim: docs/tmp/authoring-claims/2026-10-28-plan-prompts-stub-rewrite-origin.md (session 01a17c5b-bdc9-7781-86f5-38e0cd2c16dd)
Plan review record: .ai-playbook/reviews/2026-10-28-plan-review-plan-prompts-stub-writer-forensics-r*.md
Execution budget: 1.5h total, largest task 1.5h

## Terms

- **Stub rewrite:** the witnessed replacement of the tracked prompt log with the three-line fixture-style content recorded in the backlog origin.
- **Writer channel:** the test, script, session, or tool that wrote the stub bytes to the tracked prompt log.

## Why

The tracked prompt log was restored after an unexplained wholesale rewrite, but the write source is still unknown. Identifying it can close the witnessed incident and, if a fixture leaked to the live path, fix that specific path error.

## Gist & Examples

TLDR: Identify the prompt-log writer and record its disposition, preserving the existing non-blocking write protections.

Before, a 407-line tracked ledger was replaced in the primary checkout by a three-line fixture-style stub and restored from HEAD without identifying the writer. After, the matching fixture or session evidence is recorded; a confirmed fixture leak gets its smallest path correction and a fixture-path pin. If the bounded search cannot attribute the write, the disposition records the searched sources and leaves attribution unresolved without inventing a cause.

**Gate delta:** no new gate, refusal, check, lock, ledger, protocol layer, or pause condition; no existing gate or refusal is removed or simplified. The conditional fixture-path pin is a regression test in the existing suite, not a workflow blocker.

## Outcome

Identify the writer channel from the recorded byte fingerprint, correct a confirmed fixture path leak when one exists, and close the origin with an evidence-backed disposition.

- Search the repository fixture/script sources and all named durable history channels; skip a history source only when direct evidence already ties a fixture execution to the observed rewrite.
- The result distinguishes a fixture writer, a session/tool writer, and an unresolved search without unsupported attribution.
- The work ends in one disposition commit and adds no prompt-log machinery.

## Assumptions

- The backlog row and its 2026-10-28 window are the scope of record; this plan does not widen the search to unrelated prompt-log incidents.
- The tracked prompt log was already restored from HEAD; the investigation reads history and fixtures and does not reproduce writes against the primary log.
- A search source that is absent or inaccessible is recorded as unavailable, and the remaining sources are still searched.
- A confirmed session or tool writer is recorded with only the minimum attribution needed to explain the write; private conversation content is excluded.

Decision points requiring a grill: none remain.

## Evaluation Criteria

- **Attribution:** the disposition attributes the incident only when direct execution or history evidence ties a writer to the observed bytes; a matching literal, a source's presence, or timing alone is insufficient. An inconclusive result names searched and unavailable sources.
- **Scope:** any code change is limited to the confirmed writer path, and any test pin proves the fixture writes only to its isolated temporary location.
- **Continuity:** no new human approval, stop, refusal, or recovery procedure is introduced for prompt-log writes.
- **Closure:** the origin row's covered disposition is folded into the completed plan and removed under the existing plan lifecycle.

**Quality dimensions:**
- Correctness: every attribution is supported by direct execution or history evidence tying the writer to the observed bytes; a byte fingerprint match alone is insufficient.
- Simplicity: the fix changes only the confirmed path resolution and uses the existing test suite.

**Done when:** the source sweep and conditional fix are complete, the disposition is durable, and the origin is closed through the plan lifecycle.

**Ship when:** any session owner action that is outside this repository is reported with the exact supported evidence and owner, without blocking the repository disposition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/land_squash.sh` (Task 1) - conditional correction only if direct evidence confirms a live-path leak
- `scripts/check_prompt_log_origins.py` (Task 1) - conditional correction only if direct evidence confirms a live-path leak

**Tests:**
- `scripts/test_check_prompt_log_origins.py` (Task 1) - conditional pin when its fixture can write to the live path
- `scripts/test_done_run_wrapper.py` (Task 1) - inspect historical fixture revisions; read-only unless direct evidence confirms a current live-path leak

**Documentation and records:**
- `docs/history/backlog/2026-10-28-plan-prompts-stub-rewrite-origin.md` (Task 1)
- `docs/history/backlog/PLAN-PROMPTS.md` (review-only)
- `docs/maintenance/development_lessons.md` (review-only)

**Plan-related extension:** an exact additional writer/test path identified by current or historical search is in scope for attribution. It may be edited only for the smallest path-resolution correction and its pin when direct evidence confirms it can write to the live path, even if historical attribution remains unresolved.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/SKILL.md` and scheduler guards; reason: the incident does not establish a scheduler defect.
- New gates, locks, validators, ledgers, state fields, or ceremonies; reason: the origin's evidence supports one bounded investigation and a possible fixture-path repair only.
- Unrelated prompt-log history or private session content; reason: outside the origin's narrow attribution scope.

## Validation Commands

```bash
python3 scripts/check_prompt_log_origins.py docs/history/backlog/PLAN-PROMPTS.md
python3 scripts/check_plan_origins_closed.py --plan docs/history/plans/2026-10-28-plan-prompts-stub-writer-forensics.md
```

### Task 1: Identify the writer and close the witnessed origin

Files:
- `docs/history/backlog/2026-10-28-plan-prompts-stub-rewrite-origin.md`
- `scripts/land_squash.sh` (conditional writer correction)
- `scripts/check_prompt_log_origins.py` (conditional writer correction)
- `scripts/test_check_prompt_log_origins.py` (conditional regression pin)
- `scripts/test_done_run_wrapper.py` (historical fixture revisions)

Primary class anchors:
- `Write boundary rule` in `docs/history/backlog/PLAN-PROMPTS.md`
- `check_prompt_log_origins.py` in `scripts/check_prompt_log_origins.py`

**Evidence:** the origin records the stub literals (`# PLAN prompts` and `- entry one`), the observed 2026-10-28 16:30Z-19:10Z search window, the restoration from HEAD, and the existing prevention rules in lesson 292 and the prompt-log write boundary.

- [ ] [class: IMPLEMENTATION_REQUIRED] Search repository scripts, fixtures, and tests for both exact stub literals and for writes resolving to the tracked prompt log; distinguish fixture-only output paths from writes to the repository path.
- [ ] [class: IMPLEMENTATION_REQUIRED] Read the matching writer implementation and relevant test setup. If a fixture path can write to the live repository log, reproduce the path calculation only in a temporary repository, correct that path at its source, and add one pin in the existing test suite that proves the output stays isolated.
- [ ] [class: IMPLEMENTATION_REQUIRED] Inspect available durable session logs, the ZCode session store, Git reflog/stash evidence, and relevant Git commits in the incident window for candidate writer or fixture source revisions; record unavailable sources.
- [ ] [class: IMPLEMENTATION_REQUIRED] At each matching historical source revision, reconstruct the output path and establish whether it resolves to the tracked prompt log or an isolated temporary repository. A literal match, commit timestamp, or possible live-path write alone does not establish attribution; require direct execution or history evidence to tie the fixture to the observed bytes.
- [ ] [class: IMPLEMENTATION_REQUIRED] Record one evidence-backed disposition beside the origin row. Attribute the incident to a fixture only when direct execution or history evidence ties it to the observed bytes; otherwise separate a possible path defect from unresolved historical attribution.
- [ ] [class: IMPLEMENTATION_REQUIRED] In the origin row, rewrite the fingerprint statement: a literal match is only a candidate requiring path validation, a non-match leaves attribution unresolved, and neither alone proves a live-path write or identifies the writer; require direct execution or history evidence to tie a writer to the observed bytes.
- [ ] [class: IMPLEMENTATION_REQUIRED] If a fixture can write to the live path, include its narrow correction and pin in the same change even when the historical writer remains unresolved; record attribution separately and claim it only with direct execution or history evidence. If a session or tool writer is identified, record the channel and supported attribution. If the search is inconclusive, record the searched and unavailable sources.
- [ ] [class: IMPLEMENTATION_REQUIRED] Close the origin in the same disposition change without adding a gate or a follow-up item solely to preserve uncertainty.
- [ ] [class: IMPLEMENTATION_REQUIRED] Set the origin's `Status` to `covered (<this plan path>)`; the completion pass folds the disposition into the archived plan and deletes the origin row under the existing lifecycle.
- [ ] [class: REPOSITORY_TEST] Run the existing prompt-log origin check. If code or a test changes, run the existing test file that owns the confirmed writer path and record its result; do not run unrelated suites.

**Acceptance:** the disposition ties any fixture to the observed write with direct evidence, or explicitly states that attribution remains unresolved after the bounded sweep; any code change is limited to a confirmed live-path leak; no new blocking behavior is added; the prompt-log and origin-closure checks pass at the corresponding landing boundaries.
