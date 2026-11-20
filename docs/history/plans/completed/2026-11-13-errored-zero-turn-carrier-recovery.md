# Plan: fired-but-zero-turn carrier census warning

Backlog origin: docs/history/backlog/2026-11-13-errored-zero-turn-carrier-recovery.md
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-errored-zero-turn-carrier-recovery-pf8878962-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 2.5h total, largest task 1.0h
Executed: yes (883fb4727, the review-certified execution tip; the branch's pre-squash tip at the landing call is the archive-ceremony commit above it)
Authoring claim: 2026-11-13-errored-zero-turn-carrier-recovery.md (session sess_657e2ab1-02cb-464a-b8aa-43c886a4b514)

## Terms

- Carrier: an automation record (one-shot or recurring) whose firing launches a maintenance session; the fired carrier is the loop's scheduling unit.
- Twin: a second carrier armed for the same clock slot as another, each firing its own session.
- Arming (a carrier): scheduling an automation so it fires later; the loop's carrier re-arm sense of the word.
- Arm (census): a detection branch of a census operation, as in the fired-but-zero-turn arm; distinct from carrier arming.
- Carrier-liveness census: the survey turn's read-only fire-state consult, the `carrier-liveness` operation in `scripts/execute_plan_runtime.py`, recorded report-only in the scheduler state file's notes.
- Zero-turn session: a carrier-spawned session whose transcript holds no content-bearing assistant record created after the failed run's `created_at`; content-bearing means at least one assistant record (role `assistant` in the record JSON) with text parts (the session store's `part` table joined on `message_id`) or output tokens above zero.
- Tasks-index store: the ZCode task index SQLite database (default under `~/.zcode/v2/tasks-index.sqlite`), holding the `automation_runs`, `tasks`, and `automations` tables this census reads; the run-to-task join is `tasks.task_id = automation_runs.session_id` and the task status column is `tasks.task_status`.
- Session store: the ZCode session SQLite database (the facts document's `session_store_path` key, read-only, never written), whose `message` table holds transcript records with the role discriminator inside the record JSON and whose `part` table holds text parts.
- Survey turn: one scheduler-turn pass of the maintenance skill's Step 1 survey, which runs the consults and records their results.
- Liveness note: the scheduler state file's `notes[]` entry the survey consult writes with the `carrier-liveness|` prefix.
- Maintenance loop: the recurring scheduler-turn cycle that surveys, guards, decides, and dispatches (`agents/skills/maintenance/SKILL.md`).
- Lane: one work channel of the loop (execution or authoring), guarded independently.
- Execution slot: one scheduled carrier firing whose payload runs execution-mode work.
- Origin row: the backlog file under `docs/history/backlog/` whose path the plan's `Backlog origin:` line names.
- Standing authorization: the maintenance authoring payload's pre-authorization to decide in-scope choices without confirmation questions (the plans skill Phase 1 maintenance-selected arm).
- SOT-corrected: rewritten to the current source-of-truth placement when the origin's recorded home contradicts it (the plans origin-acceptance rule).
- Fixture cell: one named classification scenario in the focused suite (a test pinning one given/expects shape); all new cells live under `CarrierLiveness*Test` classes with `zero_turn` in the method name.
- Transcript-absent marker: the census warning marker emitted when the session store holds no message rows for the linked session.
- Missing-task marker: the census verdict marker recorded when a failed run inside the lookback has no task row.
- Missing-session marker: the census verdict marker recorded when a failed run's `session_id` is null or empty.
- Byte cap: the per-file cap in `scripts/skill_text_budget_caps.json` (85706 bytes for survey-arms.md).
- Blocking posture: the skill-text budget gate's blocking exit class (ceiling breaches fail the gate; advisory rows do not).
- True catch: a witnessed production detection of the class an arm exists to catch (the machinery admission protocol's promotion unit).
- Warning-only: a finding class that reports and never blocks, refuses, arms, retries, or mutates; every classified verdict exits 0.
- Satisfaction (session-owned): the schedule-ask convention in the repository AGENTS.md Scheduling asks section: an ask is satisfied only by an automation record the asking session itself created or patched.
- Machinery registry: `scripts/machinery_registry.json`, the keep-or-delete inventory whose entries carry admission records and pre-registered removals rows.

## Why

Two carrier-fired sessions in one 24h window errored before their first post-run content-bearing turn and nothing downstream consumed the failure, so a recurring operator ask lay dropped for 13 hours and an execution slot was covered only by a twin's independent arming. The census that already reads fire outcomes never reads spawned-session health, and the errored-carrier satisfaction rule (development_lessons.md #444) has no detection input and no clause in the scheduling-asks convention home, so the drop stays invisible to every consumer of the ask.

## Gist & Examples

TLDR: the carrier-liveness census gains a fired-but-zero-turn warning arm and the schedule-ask satisfaction convention cites its errored-carrier branch with a live detection input, so a dropped carrier ask is reported instead of silently lost, which is why the automation force applies: the loop detects and reports the drop itself.

Before: an automation run row reads outcome `failed`, its linked task reads status `error`, the transcript holds zero post-run content-bearing assistant records; no report, no state disposition, no memory record; the ask drops until the operator re-issues it 13 hours later.

After: the same shape produces one warning row naming the automation id, the automation title, the scheduled time, and the session id; the survey records it report-only beside the liveness note; the scheduling-asks convention classifies the ask as dropped, never satisfied.

## Outcome

A fired carrier whose session errors before its first post-run content-bearing turn is detected and reported by the maintenance loop itself, without blocking any lane.

- The census warning names the dropped ask so the next capable session re-derives or re-arms it without operator re-derivation (lesson #444's own prescription, now with a producer).
- The scheduling-asks convention's errored-carrier clause keeps session-owned satisfaction semantics honest: an errored zero-turn carrier is never satisfaction.
- The warning arm's posture is pre-registered in the machinery registry with its promotion criteria and sunset.

Gate delta: net addition of one warning-only, read-only census arm (a report-only survey recording duty, no refusal class) plus one machinery-registry duty row (registry kind protocol, like the sibling `duty:carrier-liveness-missed-fire` row) carrying its warning-only wiring and its pre-registered removals row (sunset 2026-12-13, promotion on a third true catch); no refusal-class, hard-gate, fence, protocol-layer, or scheduler-state schema-field change; removals: none. Priced by the origin row's machinery admission record (two witnessed incidents, one-line false-positive cost) and the registry row's own sunset and promotion criteria, the same shape the sibling archive-ceremony warning arm landed with.

Follow-up disposition: the anticipated follow-ups are the registry row's sunset and promotion review at 2026-12-13 (recorded in the removals row, never a backlog row) and the fold-time witness re-point the new row's note pre-registers (the completion pass that archives this plan owns it).

## Assumptions

- assume the durable transcript home is the session store `message` table with the role discriminator inside the record JSON, joined to the `part` table for text parts (`part.message_id = message.id`); basis: probed 2026-11-13 (witness session sess_41b6f8c8-9ce5-4553-a579-4e4d5ac786a2 holds assistant records with zero output tokens and no text parts across its whole retained transcript; witness session sess_02751696-dd14-4ef6-92a5-0a50b4c16209 carries pre-run content-bearing history from a reused session, so the content-bearing predicate is bounded by run time; the rollout model-io jsonl files are transient and absent for both witnesses).
- assume zero-turn means zero content-bearing assistant records within the run's lifetime (records whose `time_created` is after the run's `created_at`), not zero message rows; basis: the same probe (witness 2's pre-run turns are content-bearing and must not mask the drop; witness 1 holds 11 records, none content-bearing).
- assume the run and task record surface is the tasks-index `automation_runs` and `tasks` tables joined by `tasks.task_id = automation_runs.session_id`, the status column `tasks.task_status`, and the lookback anchored on `automation_runs.created_at`; basis: probed (both witnesses read run outcome `failed` with linked `task_status` `error`).
- assume the session store resolves through an explicit `session_db_path` payload key for fixture injection, and absent the key through the facts document's `session_store_path` key then the home default (mirroring `scripts/tool_runtime_stats.py`'s `load_facts`/`resolve_store_path` shape), fail-open to a census unknown marker; basis: the facts row and that script's existing convention.
- assume the errored-carrier satisfaction rule's durable home is development_lessons.md #444 (landed 2026-11-13, same witnessed incidents): the AGENTS.md clause cites it rather than restating it, and Task 3 aligns #444's transcript criterion to the content-bearing definition; basis: probed (no satisfaction text exists in zcode.md while AGENTS.md owns the Satisfaction-is-session-owned bullet; the origin row's zcode.md pointer is stale and is SOT-corrected here per the plans origin-acceptance rule).
- assume a 48h default lookback bounded on `automation_runs.created_at`, with a payload key for fixture pinning; basis: the consult runs once per survey turn and a bounded window keeps the read cheap.
- assume a failed run inside the lookback with no task row, and a failed run with a null or empty `session_id`, classify as unclassified markers (no warning, the marker names the missing evidence); basis: the warning contract requires the task-status conjunction and a session id to name, so absent evidence cannot produce a witnessed warning (decided 2026-11-13 under the standing authorization, simpler than inventing warning text for unverifiable shapes).

Decision points requiring a grill: none remain; single-operation extension versus a separate operation: extend `_carrier_liveness_operation` with an additive census member, the survey consult already invoking the operation once per turn so one invocation keeps the wiring minimal while the registry row carries its own admission record (decided 2026-11-13 under the standing authorization); satisfaction-branch homing in the repository AGENTS.md citing lesson #444, the convention's existing home outside the skill byte-budget gate (decided 2026-11-13 under the standing authorization); unclassified-marker disposition for missing-task and missing-session shapes (decided 2026-11-13 under the standing authorization).

## Standing constraints

- Warning-only posture: nothing in this plan may block, refuse, arm, retry, or mutate based on a census finding; every classified verdict exits 0.
- Read-only stores: both SQLite reads use mode=ro URIs, asserted by a recording double around the connect call; fixtures inject explicit store paths (state file, tasks-index store, session store) and never touch live stores, with a negative control pinning that no fallback resolution is consulted.
- No runtime outside this repository is modified; the session store and tasks-index store are read surfaces only.
- Fail-closed validation block: every Validation Commands line that can fail carries an explicit `|| exit 1` or explicit conditional exit, so no line's failure is masked and the hygiene scan always runs last.

## Evaluation Criteria

**Quality dimensions:**
- correctness: fixture cells prove the classification matrix (warning on the run-time-bounded witnessed conjunction, contrast negative when post-run content-bearing turns exist, reused-session warning, transcript-absent marker, missing-task and missing-session markers, store-error census unknown, healthy-run negative, arm presence on early-return verdicts).
- safety: no production or test path writes either store; the recording double proves every read opens read-only.
- maintainability: the survey-arms.md addition stays within its byte cap (85706 bytes; 83135 at authoring), witnessed by the pinned wc -c gate, or pays equivalent bytes in the same change per the anti-growth rules.
- posture: the pinned machinery inventory command reports no failure beyond the recorded `duty:carrier-liveness-missed-fire` known-red (the raw check exits 1 until that row's sanctioned re-point lands; this plan never touches that row).

**Done when:**
- the pinned `-k "liveness or zero_turn"` selector passes, and the pinned `-k zero_turn` invocation (which collects zero tests today, failing presence) collects and passes the new cells.
- the new row battery cells pass (`pytest scripts/test_machinery_inventory.py -q -k zero_turn`, which collects zero tests today); the file's whole-suite run carries exactly the one recorded pre-existing RealTreeCheck known-red (derived 2026-11-13, the same stale-witness family; this plan never touches that row).
- the pinned doc needles (survey-arms.md row-id needle, AGENTS.md lesson-#444 needle) pass; both are RED on the authoring tree.
- the survey-arms byte-cap witness (`wc -c <= 85706`) passes.
- the skill-text budget check passes (blocking posture).
- the public hygiene scan passes.
- the pinned machinery inventory command exits 0 with no non-baseline failure.

**Ship when:**
- a live survey turn records a real zero-turn warning naming a dropped ask; the promotion review rides the registry removals row's 2026-12-13 sunset.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py` (Task 1)
- `scripts/machinery_registry.json` (Task 3)
- `AGENTS.md` (Task 3)
- `agents/skills/maintenance/survey-arms.md` (Task 3)
- `docs/maintenance/development_lessons.md` (Task 3)
- `agents/skills/maintenance/CHANGELOG.md` (Task 3)

**Tests:**
- `scripts/test_execute_plan_resume_watcher.py` (Task 1)
- `scripts/test_execute_plan_resume_watcher.py` (Task 2)
- `scripts/test_machinery_inventory.py` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/maintenance_fire_outcomes.py`; reason: read-only reuse of its existing store conventions, no edit planned.
- `agents/skills/maintenance/SKILL.md`; reason: the Step 1 dispatch already routes to the module holding the census arm; no router edit.
- `docs/history/backlog/EXEC-PROMPTS.md`; reason: the execution lane's rolling log is untouched by this plan.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execute_plan_resume_watcher.py -q -k "liveness or zero_turn" || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_execute_plan_resume_watcher.py -q -k zero_turn || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_machinery_inventory.py -q -k zero_turn || exit 1
python3 scripts/skill_text_budget.py --check || exit 1
TMPM="$(mktemp -d)"; python3 scripts/machinery_inventory.py --check --repo-root . >"$TMPM/out.txt" 2>&1; if grep '^FAIL' "$TMPM/out.txt" | grep -vF 'duty:carrier-liveness-missed-fire: witness ref does not resolve to a tracked path'; then rm -rf "$TMPM"; exit 1; fi; rm -rf "$TMPM"
test "$(wc -c < agents/skills/maintenance/survey-arms.md)" -le 85706 || exit 1
grep -qF 'duty:carrier-liveness-zero-turn' agents/skills/maintenance/survey-arms.md || exit 1
grep -qF 'development_lessons.md #444' AGENTS.md || exit 1
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh"
```

Validation preamble (authoring-time preflight record, 2026-11-13, rule 29; updated at the r1 fold):

- Pinned selector `-k "liveness or zero_turn"`: measured at authoring 13 selected / 248 deselected (261 total), all pre-existing carrier-liveness cells; an earlier draft selector `-k "carrier_liveness or zero_turn"` selected zero tests (the classes are named `CarrierLiveness*Test`, no underscore) and was corrected before round 1.
- Pinned selector `-k zero_turn`: collects zero tests today (pytest exit 5, no tests ran), so the pinned `|| exit 1` makes it RED on the authoring tree and GREEN once Task 1 lands the first zero_turn cells (Task 1 owns the first cells; Task 2 completes the matrix).
- Pinned row battery: `pytest scripts/test_machinery_inventory.py -q -k zero_turn` collects zero tests today (RED presence pin, GREEN after Task 3); the file's whole-suite run measured `1 failed, 26 passed` on the authoring tree before any plan work, the one failure being `RealTreeCheck::test_real_tree_checks_green` (known-red baseline, same stale-witness family as the machinery check red, derived 2026-11-13; no plan task touches that row).
- Pinned budget check: `OUTCOME: pass` (0 blocking ceiling breaches; the 3 advisory ratchet rows are the recorded pre-existing ones).
- Pinned machinery inventory command: the raw check prints exactly one failure on a clean tree, `duty:carrier-liveness-missed-fire: witness ref does not resolve to a tracked path: docs/history/backlog/2026-11-12-missed-carrier-fire-liveness-watchdog.md` (the origin row folded at its covering landing while the registry row still cites the living path; known-red baseline, derived 2026-11-13 from the clean authoring tree, no plan task touches that row; the sibling row's own note carries the overdue re-point duty that would clear it). The pinned command is baseline-relative: it fails on any FAIL line other than that exact known line, so Task 3's row addition must introduce zero new failures and a repaired baseline does not false-fail the gate; the baseline-relative form was executed against today's tree (positive control: the known line present, no other FAIL).
- Pinned byte-cap witness: `wc -c < agents/skills/maintenance/survey-arms.md` measured 83135 at authoring (cap 85706), passing today, enforced after Task 3's addition.
- Pinned doc needles: `grep -qF 'duty:carrier-liveness-zero-turn' agents/skills/maintenance/survey-arms.md` and `grep -qF 'development_lessons.md #444' AGENTS.md` are RED on the authoring tree (row id and citation appear nowhere today), GREEN after Task 3.
- Pinned hygiene scan: `OUTCOME: pass`.
- Em-dash authoring-time self-check: `bash scripts/check-no-em-dash.sh touched` over the new plan bytes, clean; the write-time fixer ran with 0 substitutions before round 1 and re-runs after every fold batch.
- Rule 22 authoring-time mechanical audit: the Validation Commands block passes `bash -n` after the r1 fold (fail-closed shape: every fallible line carries `|| exit 1` or an explicit conditional exit, so the hygiene scan always runs); the plan pins fixed-string needles against target files (rule 28: scoped to files this plan edits, not whole-corpus sweeps); the machinery baseline-relative gate was executed in the shell (positive control present).
- Rule 19 RED-today evidence: the witness-shaped cell's assertion references the not-yet-implemented `zero_turn_census` member (probed: `_carrier_liveness_operation`'s verdict keys carry no such member), so the RED leg is execution-time; the `-k zero_turn` and needle pins give command-level RED evidence today.
- Pre-round gate (`python3 scripts/plan_readiness.py --pre-round`): first run failed with three violations (missing classification tag on the Task 1 commit item, malformed Task 2 anchor entry form, Task 1 evidence criterion 527 bytes over the 512 cap); all three folded in the same authoring pass that added this preamble, then the gate re-ran clean; re-run again clean after the r1 fold batch.
- Round-start state for r1: round_start_commit d73808fba5f8029d8df10d32944dbe6b99be857b, round_start_digest 33c1776f8854149657061a29fc3481075a05b8a003be0280cabe75688137d5f9 (superseded by the post-fold checkpoint recorded beside the round-close seal).

### Task 1: Zero-turn census arm in the carrier-liveness operation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_resume_watcher.py`

Primary class anchors:
- `_carrier_liveness_operation` in `scripts/execute_plan_runtime.py`

- [x] Census-arm presence on every verdict: given the not-yet-due fixture shape (a recorded fire time in the future) with fixture stores attached, expects the verdict to still carry `zero_turn_census` computed from the stores; the census read runs before and independent of the missed-fire early returns, and a state-file or store failure yields the census unknown marker with the member still present [class: IMPLEMENTATION_REQUIRED]
- [x] Warning row on the witnessed conjunction, bounded by run time: given fixture stores with an `automation_runs` row inside the lookback at outcome `failed`, its linked `tasks` row (joined by `tasks.task_id = automation_runs.session_id`) at `task_status` `error`, and no content-bearing assistant record created after the run's `created_at`, expects `zero_turn_census` to carry one warning row naming the automation id and the session id [class: IMPLEMENTATION_REQUIRED]
- [x] Content-bearing read surface: given the same conjunction, expects content-bearing to mean an assistant record with text parts (the `part` table joined on `message_id`) or output tokens above zero, evaluated only over records created after the run's `created_at` [class: IMPLEMENTATION_REQUIRED]
- [x] Warning row completeness: given the same conjunction, expects the row to also carry the automation title joined from the `automations` table and the scheduled time from `automation_runs.scheduled_at` [class: IMPLEMENTATION_REQUIRED]
- [x] Session-store wiring: given a fixture session store passed through the explicit `session_db_path` payload key, expects the census to read that path; absent the key, expects resolution from the facts document's `session_store_path` key then the home default (mirroring `scripts/tool_runtime_stats.py`'s `load_facts`/`resolve_store_path` shape), with an unresolvable store yielding the census unknown marker and the live store never read when the key is present [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given fixture store paths, a recording double around the SQLite connect call asserts every connection opens `file:...?mode=ro` with `uri=True`, and the byte snapshot extended to the session store plus a no-sidecar directory assertion shows nothing written [class: IMPLEMENTATION_REQUIRED]
- [x] Error containment: given a fixture store missing the `automation_runs` or `tasks` tables, expects the verdict to carry a census unknown marker and exit 0; every census query wraps `sqlite3.Error` into the verdict, never raising [class: IMPLEMENTATION_REQUIRED]
- [x] Run the focused suite expecting RED (the new assertions reference the missing member) [class: REPOSITORY_TEST]
- [x] Write minimal implementation; Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: census arm reports fired-but-zero-turn carriers warning-only` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Classification matrix suite cells

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_execute_plan_resume_watcher.py`

Primary class anchors:
- `_carrier_liveness_operation` in `scripts/execute_plan_runtime.py`

- [x] Contrast cell: given a failed run whose session holds a content-bearing assistant record created after the run's `created_at`, expects no zero-turn warning row for that run [class: REPOSITORY_TEST]
- [x] Reused-session cell: given a failed run whose session carries pre-run content-bearing history but zero post-run content-bearing records, expects one warning row (the witness 2 shape) [class: REPOSITORY_TEST]
- [x] Transcript-absent cell: given a failed run whose session has no message rows at all, expects one warning row carrying the transcript-absent marker rather than a silent pass [class: REPOSITORY_TEST]
- [x] Missing-task cell: given a failed run inside the lookback with no task row, expects no warning plus the missing-task marker in the verdict [class: REPOSITORY_TEST]
- [x] Missing-session cell: given a failed run with a null or empty `session_id`, expects no warning plus the missing-session marker [class: REPOSITORY_TEST]
- [x] Healthy-run cell: given dispatched or succeeded run rows and sessions with post-run content-bearing records, expects no zero-turn warning [class: REPOSITORY_TEST]
- [x] Lookback-bounding cell: given a failed run older than the census window, expects census silence for that row [class: REPOSITORY_TEST]
- [x] Read-only negative-control cell: given `HOME` and `ZCODE_DATA_BASE_DIR` redirected to the temp root and every store path injected, expects no fallback resolution consulted and the injected session store read [class: REPOSITORY_TEST]
- [x] CLI dispatch cell: given the operation dispatched through the runtime CLI over fixture stores, expects exit 0 and the additive member present [class: REPOSITORY_TEST]
- [x] Naming contract: every new cell lives under a `CarrierLiveness*Test` class with `zero_turn` in the method name, so the pinned `-k zero_turn` selector collects them [class: REPOSITORY_TEST]
- [x] Run → expect GREEN; Commit: `test: pin the zero-turn census classification matrix` [class: REPOSITORY_TEST]

### Task 3: Consumer, convention, and registry wiring

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/survey-arms.md`
- `AGENTS.md`
- `docs/maintenance/development_lessons.md`
- `agents/skills/maintenance/CHANGELOG.md`
- `scripts/machinery_registry.json`
- `scripts/test_machinery_inventory.py`

- [x] The survey-arms.md Carrier-liveness consult bullet records the returned zero-turn warnings report-only beside the liveness notes entry, each note formatted `carrier-liveness|zero-turn|automation=<id>|session=<id>`, never arming or mutating [class: IMPLEMENTATION_REQUIRED]
- [x] The same bullet states the zero-turn notes deliberately share the newest-30 retention cap with the liveness notes (eviction newest-by-`at` stamp across the shared prefix); the pinned byte-cap witness and the same-change payment duty keep the file within its 85706-byte cap [class: IMPLEMENTATION_REQUIRED]
- [x] The AGENTS.md Scheduling asks Satisfaction bullet gains the errored-carrier branch as one clause citing development_lessons.md #444 (a fired carrier whose session errored with zero post-run content-bearing assistant records is never satisfaction of its ask; the ask is reported dropped, never silently unsatisfied), not a restatement with a diverging criterion [class: IMPLEMENTATION_REQUIRED]
- [x] development_lessons.md #444's transcript criterion is aligned to the content-bearing definition (assistant records with text parts or output tokens above zero, within the run's lifetime), so the lesson's operational test matches the census predicate [class: IMPLEMENTATION_REQUIRED]
- [x] agents/skills/maintenance/CHANGELOG.md gains the dated Revisions row for the census arm (the extracted ledger the sibling landing used) [class: IMPLEMENTATION_REQUIRED]
- [x] The machinery registry gains the entries row `duty:carrier-liveness-zero-turn` (disposition keep; warning-only wiring note; the origin row's admission record with sunset 2026-12-13 and third-true-catch promotion; witness ref citing this plan's own living path, never the origin row's living path) [class: IMPLEMENTATION_REQUIRED]
- [x] The entries row's note pre-registers the witness re-point duty to `docs/history/plans/completed/2026-11-13-errored-zero-turn-carrier-recovery.md` at this plan's completion fold (the duty:archive-ceremony-post-landing-report shape) [class: IMPLEMENTATION_REQUIRED]
- [x] The machinery registry gains the removals row with the same id carrying the pre-registered sunset, the third-true-catch promotion criterion, and the co-removal set (the census member, its suite cells, and both registry rows) [class: IMPLEMENTATION_REQUIRED]
- [x] The row battery in scripts/test_machinery_inventory.py pins the new row pair: allowed witness refs (this plan's living path and its post-fold completed twin), reds when either row is dropped or thinned, following the sibling row battery's shape [class: IMPLEMENTATION_REQUIRED]
- [x] Run the pinned machinery inventory command expecting exit 0 with no failure beyond the recorded `duty:carrier-liveness-missed-fire` known-red [class: REPOSITORY_TEST]
- [x] Run the new row battery (`pytest scripts/test_machinery_inventory.py -q -k zero_turn`), both doc needles, the byte-cap witness, and the budget check, each expecting GREEN; the file's RealTreeCheck pre-existing known-red stays out of this plan's scope [class: REPOSITORY_TEST]
- [x] Commit: `feat: wire the zero-turn census into the survey consult, the satisfaction convention, and the machinery registry` [class: IMPLEMENTATION_REQUIRED]

## Documentation Impact Assessment

- `agents/skills/maintenance/survey-arms.md` is the operative skill surface this plan edits; its census-arm bullet is the only documentation home for the recording duty (single-homed, no README or topic-page duplication), and `agents/skills/maintenance/CHANGELOG.md` takes the dated Revisions row.
- The repository AGENTS.md Scheduling asks section is the convention surface this plan edits; the errored-carrier rule's durable home is development_lessons.md #444, which Task 3 aligns and the AGENTS.md clause cites; no other doc page mirrors the satisfaction bullets.
- No catalog or registry README lists carrier-liveness surfaces by name, so no index updates are required.

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-13-errored-zero-turn-carrier-recovery.md`: covered by this plan and deleted in this landing (the covering execution landed the census arm, the classification matrix, and the Task 3 wiring; the plan's `Backlog origin:` line names the row; the row's durable citation home is this completed twin, never the deleted living path).
