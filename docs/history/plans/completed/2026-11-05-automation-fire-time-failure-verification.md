# Plan: Maintenance one-shot fire outcome verification

Backlog origin: docs/history/backlog/2026-11-05-automation-fire-time-failure-verification.md
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-05-plan-review-automation-fire-time-failure-verification-p4167ddfc-r*.md
Execution budget: 1.5h total, largest task 1.0h
Executed: yes (0446f7cb19bdb483a4cf9d95c32b4977bb915aaa)
Authoring claim: 2026-11-05-automation-fire-time-failure-verification.md (session 01a1aaae-8c68-7b13-86ad-37de874170b7)

## Terms

- **Fire outcome:** a terminal success or failure reported for a scheduled one-shot's session after its fire time.
- **Armed memory item:** the existing memory entry that says a scheduled one-shot is pending or will fire.
- **Warning-only:** the verification reports and records evidence but cannot stop dispatch, retry a fire, or change carrier creation.

## Why

A one-shot can fail before its prompt runs, leaving its scheduled memory entry to imply that work is still pending. The maintenance survey needs a durable, post-fire result so later sessions can correct that record from runtime evidence.

## Gist & Examples

TLDR: record one-shot fire outcomes after they happen, automating stale-record correction without adding a dispatch gate.

Before: the memory entry says a one-shot is scheduled even after the runtime reports its session failed at launch.

After: the next maintenance survey reads the ZCode automation run ledger by automation id and repository workspace key, records the terminal outcome and linked session id, then appends a keyed correction note that supersedes the matching armed memory entry for either success or failure. It records an error class only when the linked task row exposes structured attribution; otherwise it records `error=unknown`. If the lifecycle result is absent or ambiguous, it reports unknown and changes neither record.

Edge cases: a still-running session stays unclassified; a missing lifecycle record stays unknown; two overlapping carriers are reported after firing without preventing either one.

## Outcome

A maintenance survey leaves a durable, evidence-linked terminal result for each verifiable scheduled one-shot fire and appends a keyed correction for the matching armed memory line after either success or failure.

- Failed fires are visible without hand-reading raw runtime logs when the run ledger contains a terminal result.
- Successful fires no longer leave an armed memory statement implying the work has not happened.
- Missing or ambiguous events remain warning-only and do not create false failures.
- Scheduler-state outcome notes are capped at the newest 30 regardless of correction status; a missing correction is re-derived from the runtime ledger on later surveys, and unrelated notes are preserved.

Gate delta: add one warning-only post-fire verification arm using existing scheduler state and memory-index write contracts; add no dispatch gate, schema field, or pre-fire lookup. The incident and verified runtime read path are described in the design and Task 1 below.

Machinery admission: incident: `docs/history/backlog/2026-11-05-automation-fire-time-failure-verification.md`; expected catch frequency: nightly carrier fires against a quota-limited account, with two dead fires observed in the 24-hour window; false-positive cost: a slow live run could be misread as failed, bounded by accepting only terminal lifecycle outcomes; unrelated concurrent runs may be reported as overlap candidates, clearly labeled without asserting duplicate mandates; review date: 2026-12-05; promotion requires a true catch and a pre-registered registry-removal row.

## Design Invariants

- Resolve the run with a read-only query of ZCode's `automation_runs` table, keyed by the armed automation id and repository workspace key; require exactly one terminal row whose `scheduled_at` matches the fire being checked. Resolve the database from `ZCODE_DATA_BASE_DIR`, falling back to `~/.zcode/v2/tasks-index.sqlite`; missing database, table, or required columns yields unknown.
- Write a result only for an explicit terminal success or failure, after the fire time.
- Persist one outcome note before attempting memory correction. Use the existing `{at,note}` shape with a fixed `one-shot-fire-outcome|` prefix, exact `(automation_id, scheduled_at)` key, and `correction=pending|done|ambiguous` status; never add a `type` field.
- Make outcome writes idempotent: reuse an identical exact-key note; conflicting outcome data is unknown. Before a targeted append, re-read after state drift and retry per the existing writer rule; suppress a duplicate when that re-read finds a peer's identical note.
- Retain at most the newest 30 outcome notes by `scheduled_at`, regardless of correction status; prune only older notes with the `one-shot-fire-outcome|` prefix and preserve unrelated notes. The next survey re-derives missing corrections from terminal rows still present in the runtime ledger.
- Record an error class only from non-empty `lastError.attribution.exceptionKind` and `.reason` fields in the task row linked by workspace key and session id; an absent field is stored as `unknown`. Store only that class and the boolean retryability, never raw error detail, message, request id, or provider payload.
- After the fire, compare all recent run rows in the same workspace, including recurring carriers. Define each observed interval as `scheduled_at` through terminal `updated_at`; report a potential overlap when intervals overlap. When both prompts are present, report whether their normalized payloads match; when prompt data is absent, report `mandate_match=unknown` with both run ids. Never claim a duplicate mandate from timing alone, and do not prevent, cancel, or reschedule either carrier.
- Preserve the original armed memory line. Append a short `fire-outcome-correction|` entry keyed by `(automation_id, scheduled_at)` and carrying `supersedes=<automation_id>@<scheduled_at>`. Before appending, read the index for that exact key: an identical entry is complete, conflicting entries are ambiguous, and an absent entry may be appended only when the armed target is uniquely identified.
- On each survey, re-read terminal run rows still retained for this workspace and compare their exact keys with the memory index. If a correction is absent, retry the append; identical concurrent corrections coalesce by key and body, while conflicting bodies are reported as ambiguous. If the run row has aged out or the source is unavailable, report unknown and do not infer an outcome.
- Never add a pre-fire duplicate lookup, retry, or dispatch-blocking condition.
- Keep this arm warning-only through its review date; promotion requires the admission protocol's true-catch and registry-removal evidence.

## Assumptions

- assume a maintenance session can read the ZCode task-index database; basis: the installed runtime persists run rows with automation id, workspace key, fire time, outcome, and session id. Open it read-only from `ZCODE_DATA_BASE_DIR` or `~/.zcode/v2/tasks-index.sqlite`; if the database or schema is unavailable, report unknown and do not write a guessed outcome.
- assume the existing scheduler state `notes[]` is the smallest audit-cache home; basis: its `{at,note}` schema accepts incident and residue notes without adding a field. A fixed note-string prefix identifies outcome records, and all such records are capped at 30.
- assume the maintenance survey owns correction of the memory entry after verification; basis: the survey already owns child-outcome checks and persistent memory-index reads.
- assume the armed memory record can be matched by automation id and fire time; basis: it names the carrier and scheduled time, while the run row supplies `automation_id` and `scheduled_at`. An absent or non-unique match stays unchanged and is reported.

Decision points requiring a grill: liveness source: runtime session lifecycle terminal outcome, not process state; maintenance-selected receipt from origin evidence, 2026-11-05, Tasks 1-2; record home: existing scheduler state `notes[]`; maintenance-selected receipt based on existing schema, 2026-11-05, Task 1; correction owner: next maintenance survey after recording; maintenance-selected receipt from current child-outcome ownership, 2026-11-05, Task 2; memory correction: append a keyed success or failure correction with fire time and automation id; maintenance-selected receipt from incident evidence, 2026-11-05, Task 2.

Scope extensions (grilled): none proposed.

Sources inspected: the origin backlog row; maintenance scheduling, survey, state-file, ZCode, and Codex overlays; `scripts/check_maintenance_pins.sh`. The installed ZCode run and linked task records supply terminal outcome, session correlation, and structured error attribution; raw detail is excluded.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: terminal success and failure each produce one record; missing or nonterminal evidence leaves state unchanged.
- Safety: no pre-fire lookup, retry, or blocking dispatch behavior is introduced.
- Recoverability: a recorded failure remains actionable when the memory correction cannot be completed.

**Done when:**
- Focused fixtures cover success, failure, duplicate observation, nonterminal, missing event, absent error detail, recurring overlap, missing prompt, retention, append-first supersession, failed-append recovery, and concurrent observation. Inject temporary database and scheduler-state paths; pin UTC epochs, assert the live scheduler-state digest is unchanged, and verify unknown-without-write for missing DB/schema plus omission of sensitive error fields.
- Success and failure fixtures prove the original armed line stays intact and an exact-key correction supersedes it for later survey reads; identical duplicates coalesce, conflicting duplicates are ambiguous, and a non-unique target is reported without correction. A missing correction is re-derived after its state note ages out while the runtime row remains.
- Maintenance pin checks pass with the new clauses and warning-only admission fields.

**Ship when:**
- The warning arm catches one true failed fire before promotion is considered.
- A registry-removal row is pre-registered before any blocking promotion.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope.

**Production instructions:**
- `agents/skills/maintenance/scheduling.md` (Task 1)
- `agents/skills/maintenance/survey-arms.md` (Task 1)
- `agents/skills/maintenance/state-file.md` (Task 1)
- `agents/skills/maintenance/zcode.md` (Task 1)

**Production code:**
- `scripts/maintenance_fire_outcomes.py` (Task 1) *(new)*

**Tests and gates:**
- `scripts/test_maintenance_fire_outcomes.py` (Task 1) *(new)*
- `scripts/check_maintenance_pins.sh` (Task 1)

**Out of scope; reject unless plan-related:** provider retry behavior, pre-fire duplicate detection, carrier creation, general runtime failure recovery, and process monitoring; none is needed for post-fire verification.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_maintenance_fire_outcomes.py -q
bash scripts/check_maintenance_pins.sh
```

### Task 1: Record and correct post-fire outcomes

Context surface: this plan's Terms, Design Invariants, and the origin row's incident and expected behavior.

Files:
- `agents/skills/maintenance/scheduling.md`
- `agents/skills/maintenance/survey-arms.md`
- `agents/skills/maintenance/state-file.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/maintenance_fire_outcomes.py` *(new; read-only SQLite adapter and bounded state-note helper; accepts explicit database and state paths)*
- `scripts/check_maintenance_pins.sh`
- `scripts/test_maintenance_fire_outcomes.py` *(new)*

Evidence:
- `agents/skills/maintenance/survey-arms.md` owns the existing post-dispatch outcome check and memory-index read.
- `agents/skills/maintenance/state-file.md` defines `notes[]` as the existing durable incident and residue record home.
- `agents/skills/maintenance/zcode.md` documents automation lifecycle fields separately from a session's terminal outcome.
- `scripts/maintenance_fire_outcomes.py` owns the read-only runtime query and bounded state-note adapter with injectable database and state paths.

Acceptance:
- [x] Record explicit terminal session success or failure once in `notes[]`, keyed by automation id and fire time. [class: IMPLEMENTATION_REQUIRED]
- [x] Leave state and memory unchanged and report unknown for missing, ambiguous, or nonterminal lifecycle evidence. [class: IMPLEMENTATION_REQUIRED]
- [x] For either outcome, append a keyed correction without rewriting the armed memory line; for failure include fire time and available error class (or `unknown`), and for success include fire time and linked session id. [class: IMPLEMENTATION_REQUIRED]
- [x] Make outcome-note writes idempotent by `(automation_id, scheduled_at)` using the existing targeted state edit and drift retry; reuse an identical note, suppress a peer's identical append, and report conflicting outcome data as unknown. [class: IMPLEMENTATION_REQUIRED]
- [x] Before memory append, read the exact correction key. On each survey re-derive missing corrections from terminal runtime rows, including after their outcome notes age out; coalesce identical concurrent entries, report conflicts as ambiguous, and mark a note resolved only after the index confirms the correction. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the armed memory line immutable; append a correction with an explicit supersedes identity. The survey treats an exact-key correction as authoritative and suppresses the old pending wording; an absent or non-unique target is reported without correction. [class: IMPLEMENTATION_REQUIRED]
- [x] Read outcomes from the task-index SQLite `automation_runs` table in read-only mode, scoped to automation id and workspace key. Require one terminal row at the expected `scheduled_at`; missing database/schema or absent, ambiguous, or nonterminal rows yield unknown. [class: IMPLEMENTATION_REQUIRED]
- [x] Join the linked task by workspace key and session id. Read structured `lastError.attribution` only; persist the `exceptionKind`, `reason`, and retryability, or `unknown` when absent. Never persist raw detail, message, request id, or provider payload. [class: IMPLEMENTATION_REQUIRED]
- [x] After firing, compare all recent runs in the same workspace, including recurring carriers, and report overlapping intervals (`scheduled_at` through terminal `updated_at`) as candidates. Include both run ids; compare normalized prompts only when both are available, otherwise say the mandate match is unknown. The report is post-fire and report-only. [class: IMPLEMENTATION_REQUIRED]
- [x] Store outcome records in the existing `{at,note}` shape with a fixed `one-shot-fire-outcome|` prefix. Retain at most the newest 30 records regardless of correction status; preserve unrelated `notes[]` entries. Re-derive a missing correction from retained runtime rows after its state note ages out. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the monitor warning-only and preserve the existing children outcome and lane-capacity semantics. [class: IMPLEMENTATION_REQUIRED]
- [x] Add fixtures for idempotent outcomes, failed-append recovery, concurrent identical observation, conflicting outcomes, success/failure supersession, unknown DB/schema, sensitive-field omission, recurring overlap with missing prompt, and retention. Inject temporary database and scheduler-state paths and fixed UTC epochs; assert the live scheduler state is unchanged. [class: REPOSITORY_TEST]
- [x] Preserve the fire path without pre-fire lookup, retries, or dispatch blocking. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep the admission incident, frequency, false-positive cost, and 2026-12-05 review date visible in operative instructions. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the listed pytest and maintenance pin commands successfully. [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

Origin row docs/history/backlog/2026-11-05-automation-fire-time-failure-verification.md: Status: covered (docs/history/plans/completed/2026-11-05-automation-fire-time-failure-verification.md), execution witness 0446f7cb19bdb483a4cf9d95c32b4977bb915aaa. No other backlog origins; the two residual rows captured during execution (2026-11-06-fire-outcomes-robustness-residuals.md, 2026-11-06-fire-outcomes-pin-and-guard-accuracy.md) are new findings, not migrated items.
