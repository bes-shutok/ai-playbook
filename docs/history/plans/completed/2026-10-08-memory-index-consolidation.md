# Plan: Permanent memory-index hygiene (recurring audit and append-first convention)

Backlog origin: docs/history/backlog/2026-10-08-memory-index-consolidation.md
Driving force: automation
Plan review record: the staging series docs/history/reviews/2026-10-08-plan-review-memory-index-consolidation-r*.md (the highest rN is authoritative)
Execution budget: 1.5h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/memory-index-consolidation.md (session sess_72b1f155-dee1-439a-916f-fcc26d801c74)

## Terms

- **Memory index:** the runtime's per-project `MEMORY.md` index file beside its topic files, in the user-level memory store outside this repository; it loads into every session.
- **Topic file:** one memory record file the index points to; durable memories live here, not in the index.
- **Index pointer:** any line in `MEMORY.md` carrying a Markdown link whose target ends in `.md` counts as a pointer line (the link may sit anywhere in the line, which covers the blob-era entries); a pointer resolves when the target topic file exists relative to `MEMORY.md`'s own directory, subdirectory targets resolving along their relative path.
- **Load budget:** the roughly 200-line bound the index must load within; beyond it the runtime truncates the index and recorded state can be absent from context.
- **Do-not-redo marker:** an index or topic-file record telling later sessions not to repeat completed work; truncation hiding it is a redo risk, not noise.
- **One-line shape:** one physical line per index entry, pointer plus hook, roughly 200 characters; the write convention's target shape.
- **Append-first:** the write discipline that adds new entries at the end of the index and never rewrites or reorders existing entries wholesale; the sanctioned targeted edits (clearing a cleared record's note, refreshing a note's carried value) stay targeted and are not wholesale rewrites.
- **Durable memory:** a topic file whose content outlives the conversation that wrote it: a do-not-redo marker, a standing preference, or project state. Contrast: **conversation-scoped** state, which records session or lane state and stays in the session.
- **Index rather than prune:** the tie-break for uncertain classifications: a topic file in doubt gets an index pointer, never a deletion.
- **Filing rule:** the lane's dedupe-and-fold filing discipline, the friction-audit task file's precedent: a dated evidence line on an existing row, or a new backlog row only after checking open, completed, and deferred; composed per receiving-review's Backlog capture required content with its `Origin class:` line set per that rule (an audit-lane filing is self-serving unless the witnessed defect was seen in a consumer project).
- **Compress-and-index remediation:** the operator-rescoped one-time ad hoc pass that rewrites bloated entries into the one-line shape; outside this plan; the audit only records the need and files the request for it.
- **Lane-quiet window:** a period with no live authoring or execution claims under docs/tmp/, because peer closeouts write the index concurrently (three same-day write conflicts witnessed 2026-10-08).
- **Store locator:** the pinned resolution of the measured store: the per-project memory directory the executing session's own runtime context names beside its loaded `MEMORY.md` index (the runtime derives it per project; the audit measures that directory's store for this repository), recorded in tilde form in evidence, never an absolute path in committed files.
- **Recurring-task registry:** docs/maintenance/recurring-tasks/ task files with TOML headers (id, cadence_days, kind, optional state_file).
- **Registry consult:** the maintenance skill's Recurring-task registry consult; it owns due-read, audit-kind dispatch, state advance, and failure advance for registered tasks.
- **Pins row:** one presence-check row of the maintenance pins suite, in the suite's `pin "<label>" grep -qF "<literal>" "<path>"` wrapper form with a dated origin comment.
- **Pins suite:** scripts/check_maintenance_pins.sh, the repository's literal-presence check suite over the skills and task files.
- **Sibling pins:** the four existing recognition-line pins (one per registered task file) the new row joins; their block's own rationale calls them deliberate insurance whose duplication is harmless.
- **Maintenance loop:** the repository's scheduler loop, the maintenance skill's recurring turns and lanes; "the loop" in this plan means it.
- **Recognition line:** the literal `recurring task memory-index-audit lane`, embedded in the task body's opening sentence the way the four sibling task files embed theirs, matched by the registry consult's dispatch and pinned by the maintenance pins suite.
- **State record:** the task's JSON state (next_due, last_run_at, consecutive_failures, token budget) the consult reads and advances; default path `.ai-playbook/maintenance/memory-index-audit.json`.
- **Overlay:** agents/skills/maintenance/zcode.md, the maintenance skill's ZCode runtime overlay.
- **Instructions home:** the operator's user-level agent-instructions file the runtime loads into every session in every project; machine-local, resolved from the operator environment at execution time, never committed to this repository.

## Why

The memory index is over budget and decaying: measured 2026-10-08 at roughly 2.7k lines against the ~200-line load budget, with only 4 well-formed one-line pointers, most of the roughly 806 topic files unindexed, and the truncation hiding the loop's do-not-redo markers, which is a redo risk rather than noise. The dominant write shape amplifies the decay: a read-edit-rewrite cycle over a multi-line blob collides with peer closeouts writing concurrently, three same-day conflicts witnessed 2026-10-08. The operator rescoped the row on 2026-10-08 so the one-time cleanup runs ad hoc outside any plan; this plan lands only the permanence mechanism.

## Outcome

A registered weekly audit task gives the decay a periodic reader and the collision-prone write shape a recorded replacement, so the operator's one-time cleanup stays fixed instead of re-decaying.

- A registered weekly audit task (`memory-index-audit`) measures the index against the load budget, checks pointer integrity, classifies unindexed topic files under index-rather-than-prune, and writes one atomic state-record update per run.
- An over-budget finding is filed through the filing rule as a new backlog row carrying the operator-decision framing: the row records the recurrence witness and asks the operator to choose between running the ad-hoc compress-and-index pass at a lane-quiet window and authorizing a plan; it never self-authorizes plan work, and the operator's standing rescope keeps the pass ad hoc absent a new operator decision. The filing is the schedule's carrier; no audit or remediation run ever rewrites the index mid-lane.
- The append-first one-line write convention (the targeted-edit carve-out and the roughly 200-character per-entry bound included) is recorded as the final line of the overlay's Audit recipe section and as one bullet in the operator's instructions home.
- No script, gate, ledger, or skill duty is added: the registry consult owns dispatch and state advance.

Gate delta: adds one registry task file and one pins row; adds no runtime gate, script, or skill-duty prose beyond the overlay convention line. Each addition prices itself: the task file pays for the decay evidence (the origin row's measured baseline with no periodic reader); the pins row pays as the recognition literal's drift insurance beside its sibling pins (their block's own deliberate-insurance rationale); the overlay line and the instructions-home bullet pay for the witnessed three-conflict collision class the append-first shape closes.

## Assumptions

- Weekly cadence (7 days) bounds the decay: the index went from healthy to ~2.7k lines within days of multi-closeout lanes, and the friction-audit precedent uses the same cadence; basis: the origin row's measurement and docs/maintenance/recurring-tasks/friction-audit.md.
- The default state-record path (`.ai-playbook/maintenance/memory-index-audit.json`) needs no `state_file` override; basis: the registry consult's default resolution, `<maintenance_state_dir>/<id>.json`.
- The ~200-line load budget is the audit's over-budget threshold and the ~200-character bound is guidance for the one-line shape, not a hard gate; basis: the origin row's measured numbers.
- The instructions home and the per-project store locator are resolvable at execution time from the operator environment; the plan never commits their absolute paths; basis: the runtime's own loading behavior.

Decision points requiring a grill: none remain. The dispatch entry's investigate pass (2026-10-08, renewed at the current HEAD) resolved the cadence home, the overlay anchor, and the ad-hoc boundary with the operator's recorded rescope.

## Standing constraints

- The audit is read-only over the memory store and reports through its state record and the filing rule; the compress-and-index remediation it requests runs only at a lane-quiet window and is the only sanctioned index rewrite: no audit run ever rewrites the index, and no run bulk-rewrites or reorders it during live lanes.
- Index rather than prune; never bulk-delete topic files; never delete a topic file whose live do-not-redo marker a lane still depends on.
- The one-time consolidation (compress-and-index, then the reviewed prune) stays ad hoc outside any plan, per the operator's recorded rescope; this plan adds only the permanence mechanism.
- No new script, ledger, gate, or maintenance-skill duty: the registry consult owns due-read, dispatch, and state advance; the task file is the procedure of record.
- The instructions-home edit is one appended bullet in a machine-local file outside this repository; documented in repo records by file shape, never by absolute path; never a rewrite of the home file.
- Committed files carry repo-relative paths only.

## Gist & Examples

TLDR: register a weekly memory-index audit task and record the append-first one-line write convention, so the loop's index hygiene runs itself (the automation force) instead of re-decaying after the operator's one-time cleanup.

Before (today): the index loads truncated every session (about 2.7k lines against a 200-line budget), most topic files have no pointer, do-not-redo markers can be absent from context, and the blob-rewrite write shape collides with peer closeouts (three same-day conflicts witnessed).

After (this plan): every 7 days the registry consult dispatches the memory-index-audit audit child; it measures the index (line count against the load budget, pointer integrity, unindexed-topic-file classification), writes one atomic state-record update, and on an over-budget finding files the compress-and-index request through the filing rule for a lane-quiet window. New index writes are append-first one-line entries in both the overlay's maintenance-side guidance and the operator's instructions home. For example, an audit finding "index at 340 lines, 12 dangling pointers, 40 durable topic files unindexed" records exactly that in the state record and files the remediation request; it does not touch the index itself.

## Evaluation Criteria

**Quality dimensions:**
- Simplicity: two small arms, no new script, gate, ledger, or skill duty; the registry consult's existing machinery carries the recurrence.
- Reliability: the over-budget response has a real consumer (the filed request on a tracked row) and respects the witnessed collision class; the state write is atomic per run.
- Durability: the convention lives in both binding surfaces (overlay for maintenance-side writes, instructions home for every session), so hygiene survives the cleanup.
- Consistency: the task file, pins row, recognition line, and state-record shape mirror the four existing registry tasks.

**Done when:**
- `docs/maintenance/recurring-tasks/memory-index-audit.md` exists with the TOML header (id `memory-index-audit`, cadence_days 7, kind `audit`), the recognition line embedded in its opening sentence, and the audit body: the pinned store locator, load-budget measurement, pointer-integrity check, the durable-versus-conversation-scoped classification under index-rather-than-prune, the single atomic state-record write, the filing-rule over-budget response, the failure arm, and the caps sentence.
- `scripts/check_maintenance_pins.sh` carries the recognition-line pin for the new task file in the sibling wrapper form and the pins suite passes.
- The overlay's Audit recipe section carries the append-first one-line convention as its final line (one line, no new heading).
- The operator's instructions home carries the same convention as one appended bullet, and the execution evidence records the edit by file shape, never by absolute path.
- A dry run of the audit body's measurement arms (load budget, pointer integrity, and classification) against the current index shape records measured values in the execution evidence.

**Ship when:**
- [class: EXTERNAL_RELEASE_GATE] Before declaring the lane done, the operator (or the operator-designated reviewer) reads the new task file and confirms the audit never deletes or rewrites index or topic content and its TOML kind is `audit` within the consult's closed audit|rider set; reads the recorded instructions-home edit confirming it is one appended convention bullet in the machine-local home; checks the dry-run record in the execution evidence (the audit body's measurement arms executed once against the current index shape, measured values recorded, nothing in the memory store mutated and no state record written); and checks the cold-start due-read verification (the TOML header parses, the missing state record reads due, and the verification created no state file). The reviewer records a pass/fail per check in the execution evidence log; closure requires all checks pass.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope:

**Production code:**
- `scripts/check_maintenance_pins.sh`

**Documentation and skills:**
- `docs/maintenance/recurring-tasks/memory-index-audit.md` (new file)
- `agents/skills/maintenance/zcode.md`

**Out of scope; reject unless plan-related:**
- The one-time compress-and-index or prune passes; operator-rescoped ad hoc.
- Any script, gate, ledger, or runtime implementation of the audit checks; the body is procedural by design.
- The memory index or topic files' content itself; the audit measures and reports, it never edits the store.
- Other registry tasks' bodies and cadences.

## Validation Commands

Run from the repository root (the authoring or execution worktree root):

```bash
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh touched
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-08-memory-index-consolidation.md
```

### Task 1: Register the memory-index-audit recurring task

Context surface: Terms, this task, and Standing constraints.

Files:
- `docs/maintenance/recurring-tasks/memory-index-audit.md` *(new)*
- `scripts/check_maintenance_pins.sh`

Evidence:
- `rg -n 'recurring task memory-index-audit lane' docs/maintenance/recurring-tasks/memory-index-audit.md`; covers the recognition line the registry consult matches and the pins row guards.
- `rg -n 'memory-index-audit' scripts/check_maintenance_pins.sh`; covers the wrapped pin row beside the four existing task-file pins.
- Dry-run record: the audit body's measurement arms (load budget, pointer integrity, and classification) executed once against the current index shape with the measured values (index line count, pointer count, dangling pointers, unindexed durable topic files) written into the execution evidence log; the dry run mutates nothing in the memory store and writes no state record.

- [x] Author `docs/maintenance/recurring-tasks/memory-index-audit.md`: TOML header (id = "memory-index-audit", cadence_days = 7, kind = "audit"), the opening sentence embedding the recognition literal the way the four sibling files do ("You are running the `recurring task memory-index-audit lane` in the repository at <REPO_ROOT> ..."), and the pinned store locator with its resolution method: the executing session's own runtime context names its per-project memory directory beside the loaded `MEMORY.md` index; the audit measures that directory's store for this repository, tilde form in evidence, never an absolute path in committed files. [class: IMPLEMENTATION_REQUIRED]
- [x] Author the audit procedure in the same file: measure the index line count against the roughly 200-line load budget; check every index pointer resolves relative to `MEMORY.md`'s own directory (a pointer is any line carrying a Markdown link whose target ends in `.md`, wherever the link sits in the line; subdirectory targets resolve along their relative path) and report dangling pointers; classify unindexed topic files durable (do-not-redo marker, standing preference, or project state) versus conversation-scoped (session or lane state) under index-rather-than-prune, mixed notes classifying by their dominant signal, with the classification pass bounded to the run's recorded token budget: when the unindexed set exceeds what the budget covers, classify a prefix of the directory listing and record the covered fraction, draining the set across runs; write ONE atomic state-record update per run (measured values, findings, last_run_at, and the advanced next_due together, through a temp file plus atomic replace, so a death mid-run leaves either the prior record or a complete one); on an over-budget finding, file the compress-and-index remediation request through the filing rule as a NEW backlog row (the row records the recurrence witness, carries the operator-decision framing, and never self-authorizes plan work) composed per receiving-review's Backlog capture required content with its `Origin class:` line set per that rule, naming a lane-quiet window; never rewrite the index. [class: IMPLEMENTATION_REQUIRED]
- [x] Carry the failure arm and caps sentence in the same body: a one-line last_result on failure, consecutive_failures incremented on failure and reset on success with the consult owning the one-day failure advance; at most 2 sub-agents, a recorded token budget (recorded by its first completed run), idle/off-peak preferred. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the fifth recognition-line pin to `scripts/check_maintenance_pins.sh` in the sibling block's form: a dated ADDED comment line and the wrapped row `pin "recognition line in memory-index-audit task file" grep -qF "recurring task memory-index-audit lane" "docs/maintenance/recurring-tasks/memory-index-audit.md"`, and update the sibling block's descriptive count comment ("each of the four task files stores its own recognition-line tail") for the fifth file. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: register the memory-index-audit recurring task` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Record the append-first one-line write convention in both binding surfaces

Context surface: Terms, this task, and Standing constraints. This task also edits one machine-local file outside the repository: the operator's instructions home, whose repo-side record is the overlay line below and whose edit is appended, never rewritten.

Files:
- `agents/skills/maintenance/zcode.md`

Evidence:
- `rg -n 'append-first' agents/skills/maintenance/zcode.md`; covers the overlay convention line inside the Audit recipe section.
- The instructions-home leg is evidenced by the recorded file shape (the user-level agent-instructions file every session loads) plus the appended bullet text in the execution evidence log; the absolute path is never committed.

- [x] Add exactly one line as the final line inside the existing `## Audit recipe` section of `agents/skills/maintenance/zcode.md` (the section's heading count stays exactly 1; add no new heading): maintenance-side memory writes are append-first one-line entries, pointer plus hook, roughly 200 characters per entry, added at the end of the index; a wholesale rewrite or reorder is never the write shape, while the sanctioned targeted edits (clearing a cleared record's note, refreshing a note's carried value) stay targeted; conversation-scoped lane state is not durable memory; when in doubt, index rather than prune. [class: IMPLEMENTATION_REQUIRED]
- [x] Append the same convention as one bullet to the operator's instructions home (the user-level agent-instructions file the runtime loads into every session; resolve it from the operator environment at execution time and record only its file shape in the evidence, never an absolute path). Exception receipt: exception confirmed by user: the operator's recorded rescope decision, quoted verbatim: "The one-time consolidation (compress and index, then the reviewed prune) is data cleanup in the user-level store, not repository behavior, so it runs ad hoc - no plan - with a full-store snapshot taken first, the survival postcondition checked, and the pass timed for a lane-quiet window ... This row's remaining scope, and the dispatched entry's prompt, is the permanence mechanism only: the maintenance lane's periodic memory-index audit duty and the append-first one-line write convention recorded in the operator's standing instructions home."; item: Task 2's instructions-home append leg; target/environment: the operator's user-level agent-instructions home (machine-local, outside this repository, resolved from the operator environment at execution time); confirmation time/session: the operator's rescope decision recorded 2026-10-08 in docs/history/backlog/2026-10-08-memory-index-consolidation.md (the durable record of the operator's chat confirmation; after this plan's landing the row's content survives in the completed plan twin at docs/history/plans/completed/ and in git history); why executable now: the executing session's runtime exposes both the per-project memory store and the instructions home in its own environment, so the append target exists and is writable without new access; completion evidence: the home file contains the appended bullet, recorded by file shape in the execution evidence log. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: record the append-first memory-index write convention` [class: IMPLEMENTATION_REQUIRED]
