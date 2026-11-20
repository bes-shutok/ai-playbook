# Plan: Memory index retirement pass and fire-time record refresh

Backlog origin: docs/history/backlog/2026-11-08-memory-index-retirement-pass-unguarded.md
Cluster: docs/history/backlog/2026-11-05-memory-index-lane-charter-review-residue.md (same surface family; that row owns the charter file's paperkeeping residue list; deliberately not consumed here, see Review Scope)
Required agent type: none (runtime-neutral)
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-09-plan-review-memory-index-retirement-pass-p3e4d5a62-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 1.5h total, largest task 0.5h
Executed: yes (d7b39fe425ee7ee2958c675af56a3d4dd9f5b5c1)
Authoring claim: 2026-11-08-memory-index-retirement-pass-unguarded.md (session sess_60bd8a14-9e70-4a45-8020-5d40b6ab664a)

## Terms

- memory index (MEMORY.md): the per-project index file the runtime loads beside its topic files; for this repository it resolves under the user-level memory store, written in tilde form in committed text, never an absolute path.
- topic file: a file in the memory directory that an index line points at through a Markdown link; the index line is the pointer plus hook, the topic file carries the record's detail.
- append-first convention: the memory-write convention paragraph in `agents/skills/maintenance/zcode.md`: memory writes are append-first one-line entries, pointer plus hook, added at the index end; a wholesale rewrite or reorder is never the write shape.
- sanctioned targeted edit: a mutation shape the convention names as allowed (clearing a cleared record's note, refreshing a carried value, folding a superseded entry); bulk means unreviewed mass retirement and is never sanctioned.
- Standing retirement rule: the convention paragraph's complement bullet set (supersession fold, deletion pairing, reviewed shape, live-marker refusal, write-time supersession), added 2026-11-05 by the load-budget consolidation plan.
- Retirement pass member: the threshold-gated mutation member this plan adds to the memory-index-audit lane file; it applies the Standing retirement rule's existing fold shapes to terminal records and is the lane's one sanctioned index mutation arm.
- terminal record: an index record whose run state is final and recorded: a completed-run record (landed, executed, or fired with its outcome recorded on disk or in the fire ledger) or a superseded record whose successor already carries the durable signal; the complement class is live markers.
- live marker: a record a lane still depends on: a pending re-arm or pending dispatch record, a paused run, an in-flight claim, or any pending-carrier line; the pass never retires one.
- proxy target: 20,000 bytes, the consolidation charter's fold target below the witnessed 25,166-byte load cut; the byte count triggers the pass and is never the binding check.
- whole-load witness: the lane's binding budget check: a fresh session's runtime context carries the index's final line with no truncation notice; byte and line counts are proxies only.
- Survival audit: the charter member that names each touched do-not-redo marker's reachable home (compressed index or git-tracked durable surface); a marker with no reachable home fails the audit, and the pass refuses that row.
- fire ledger: the runtime's persisted automation-run outcome record: the tasks-index store `automation_runs` table read through `scripts/maintenance_fire_outcomes.py` (the existing outcome recording the refresh binds to).
- pre-fire record line: an index line a scheduling session wrote for a not-yet-fired carrier, carrying its "scheduled not executed" status phrase and naming the carrier automation id.
- fire-outcome fold: the convention rule this plan adds to the Standing retirement rule: a fired run's outcome write folds its own pre-fire record line in the same targeted edit that records the outcome, so a pre-fire status phrase never survives a completed dispatch.

## Why

The memory index only ever grows. The append-first convention adds roughly 25 to 30 records a day, and the consolidation plan (landed 2026-11-05) set a load budget and an audit lane, but the lane only measures and reports: nothing removes. Three days after the budget landed the index was back over it, and at this plan's authoring time it measures 820 lines and 209,751 bytes against the 20,000-byte proxy target, so the runtime truncates the index at load and older records, including live paused-run and pending-rearm markers near the tail, fall out of loaded context. Separately, a scheduled carrier's pre-fire record line survives its own dispatch because the fired session appends a fresh outcome line instead of folding the stale one: the twin carriers of 2026-11-07 22:30 still read "scheduled not executed" in the index after both runs had failed and been recorded.

## Gist & Examples

TLDR: A threshold-gated retirement pass on the existing memory-index-audit lane plus a fire-outcome fold rule in the memory-write convention, so the index stops growing without bound and stale pre-fire carrier lines retire at their own dispatch; the driving force is automation.

Before (today): the audit lane's run measures the index at 209,751 bytes, files an over-budget finding, and stops: no run may rewrite the index, so the measurement repeats every week while the index grows another 25 to 30 lines. In the same index, the line "One-shot $maintenance exec automation-X fires 22:30 ... scheduled not executed" keeps its stale status phrase forever after the 22:30 fire failed, because the fired session wrote a new outcome line instead of folding the pre-fire line.

After (this plan): the same audit run, measuring above the 20,000-byte proxy target, runs its Retirement pass member after classification: it retires terminal records row by row under the Standing retirement rule's fold shapes, drops each index line only when the touched marker's durable signal keeps a reachable home (the successor or per-mandate summary line, the compressed index, or a git-tracked durable surface, as the chartered Survival audit defines), records every per-row disposition in the run's state record, and leaves live markers and in-doubt entries untouched, bringing the index back toward the proxy target on the lane's existing cadence. The next fired carrier's outcome write folds its own pre-fire line in the same edit that records the outcome, so the stale status phrase is gone the moment the run completes.

Edge cases: a live marker (pending re-arm, paused run, in-flight claim) is never a retirement row; an entry in doubt stays (index-rather-than-prune); a marker whose durable signal would survive only in its untracked topic file has no reachable home and its row refuses; the pass runs at most once per audit run; the whole-load witness stays the binding budget check (a fresh session's untruncated load), and byte count remains only the trigger.

## Outcome

A standing retirement pass and a fire-time refresh duty run inside the existing audit lane and the existing write convention, so index growth stops being monotonic and stale pre-fire carrier lines retire themselves.

- The audit lane's run above the proxy target retires terminal records through the chartered member, with per-row dispositions recorded and every touched marker keeping a reachable home.
- A fired carrier's pre-fire record line is folded at the outcome write, never surviving its own dispatch.
- The append-first convention, the load budget, and the index-rather-than-prune posture are unchanged; no new gate, validator, lock, ledger, or schema field exists.

Gate delta: one fence scoping in the audit lane file (the never-rewrites-the-index fence narrows to the measure, check, classify, and report legs, admitting the threshold-gated Retirement pass member as the lane's one sanctioned mutation arm); no gate, validator, lock, ledger, or schema field is added or removed, and no task condition pauses dispatch or later work; the fence widening prices itself against the completed-integrity-failure witness the origin row's Source reference records (the index back over its budget within three days of the consolidation landing, the load truncation returning, and the twin carriers' status phrases surviving their own dispatch), with the three alternatives and why each fails stated here inline: capping appends pushes records out of durability, raising the load budget reintroduces the witnessed truncation, and moving every record to topic files immediately loses the loaded do-NOT-redo recall value of recent records, so the threshold-gated member inside the existing reviewed-shape vocabulary is the remaining shape.

## Assumptions

- Assume the index state at authoring time (820 lines, 209,751 bytes, 1610 topic files, measured 2026-11-09 15:11 UTC) re-derives at execution time; basis: disk measurement at authoring and the origin row's explicit re-derivation mandate.
- Assume the fire ledger (tasks-index store `automation_runs`, read through `scripts/maintenance_fire_outcomes.py`) is the runtime's existing outcome recording the fire-outcome fold binds to; basis: the fire-ledger paragraph in `agents/skills/maintenance/zcode.md` (added 2026-11-06).
- Assume the audit lane file has no byte-cap entry and the convention file's cap is 116,647 bytes with the file already in advisory breach at 120,102 bytes before this plan; basis: `scripts/skill_text_budget_caps.json` and `python3 scripts/skill_text_budget.py --check` at authoring time.
- Growth-payment receipt: Task 1's recomposition lands at or below the pre-edit bytes of the capped file (the plan's byte witnesses enforce this); if composition attempts cannot reach it, the executor widens the deletion pairing or reports the refusal, never shipping a positive delta; the paying sibling of record is the charter-residue row's byte-negative item-2 fix (filed and dispatchable, deliberately not consumed by this plan).
Decision points requiring a grill: executor home = the existing memory-index-audit lane rather than a new registry task or a scheduler-turn duty (source: simpler-design comparison, the lane already owns index measurement, cadence, the state record, and filing, while a new task adds a second cadenced lane and registry row and a per-turn duty pays every turn, 2026-11-09, affected sections: Task 2 / Outcome); threshold = measured index bytes above the 20,000-byte proxy target with the whole-load witness unchanged as the binding check (source: the consolidation charter's fold target and the lane file's Load budget bullet, 2026-11-09, affected sections: Task 2 / Terms); record scope = terminal records only, never live markers and never conversation-scoped lane state, per the lane's existing Classify rule (source: origin row Expected section and the lane file Classify section, 2026-11-09, affected sections: Task 2 / Key invariants); fire-time refresh home = the convention paragraph as a write-shape rule rather than per-template duty edits (source: single-homing over the payload templates, fired sessions being maintenance sessions that already load the overlay, 2026-11-09, affected sections: Task 1).

## Standing constraints

- Operative text cites incidents in at most one line; the dossier lives in the origin row and the consolidation plan's archived Terms, never in the edited rule text.
- No em dashes land in changed bytes; the repository's em-dash gates run over added lines.
- The convention file (agents/skills/maintenance/zcode.md) is byte-cap tracked: its recomposition targets net bytes at or below zero, with the pre-edit count re-derived from the execution base commit, never quoted from this plan.
- Root discipline: verifications run from the executing worktree root; no task edits the memory store itself or the user-level instructions file; both stay outside this repository.
- The pins suite carries one pre-existing baseline-red cell on the unedited base (`prompt log has no all-served (stale) entry`); every plan witness and the battery require the pins failure set unchanged from that base set, never a bare exit 0, and no task prunes the log entries that cell names.

## Evaluation Criteria

**Quality dimensions:**
- correctness: given the lane's measured byte count above the proxy target, the Retirement pass member retires only records whose run state is terminal and recorded, and the Survival audit passes every touched marker with a reachable home; given a live marker or an in-doubt entry, expects no retirement row for it; given a fired run's outcome write, expects its pre-fire record line folded in the same edit.
- maintainability: each rule has one home (write-shape rules in the convention paragraph, run procedure in the lane file), cross-referenced by name, never restated; the pass reuses the charter's existing members instead of redefining them.
- minimality: the diff touches exactly the two files; no scripts, no registry rows, no schema fields, no new machinery.

**Done when:**
- Both tasks' RED and GREEN presence witnesses hold as written in their checklists, run from the executing worktree root.
- The convention file's byte count is at or below its pre-edit count re-derived from the execution base commit.
- The Validation Commands battery passes with the pins line's failure set identical to the unedited base's recorded baseline-red set, and `python3 scripts/plan_readiness.py docs/history/plans/2026-11-09-memory-index-retirement-pass.md` exits 0 with `OUTCOME: pass` at execution start, before the first checkbox flip.

**Ship when:**
- The next audit-lane run measuring above the proxy target completes a retirement pass whose state record shows per-row dispositions and a passing Survival audit, and the next fired carrier's outcome write leaves no pre-fire line behind, both without operator involvement.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- (none; this plan changes no production code)

**Docs and skill text:**
- `agents/skills/maintenance/zcode.md` (Task 1)
- `docs/maintenance/recurring-tasks/memory-index-audit.md` (Task 2)

**Tests:**
- (none added; verification is the tasks' presence witnesses plus the standing suites under Validation Commands)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- The charter-residue sibling row's seven paperkeeping fixes (`docs/history/backlog/2026-11-05-memory-index-lane-charter-review-residue.md`); reason: that row owns them; coordinated, not absorbed.
- `scripts/maintenance_fire_outcomes.py`; reason: the fire-ledger read path is existing machinery; this plan changes write-contract and procedure text only.
- The one-time consolidation charter section's post-run disposition; reason: the sibling row's item 6 owns it.
- The user-level instructions file and any memory-store content; reason: outside this repository; the convention paragraph is the repo-side source of truth this plan edits.

## Validation Commands

```bash
# Presence witnesses (Tasks 1-2), from the executing worktree root:
grep -c "Fire-outcome fold" agents/skills/maintenance/zcode.md
grep -c "Retirement pass" agents/skills/maintenance/zcode.md
grep -c "Retirement pass member" docs/maintenance/recurring-tasks/memory-index-audit.md
# Byte discipline (Task 1): the capped file does not grow past its pre-edit size
PRE=$(git show <base-ref>:agents/skills/maintenance/zcode.md | wc -c)  # base-ref = the execution run's base commit
test "$(wc -c < agents/skills/maintenance/zcode.md)" -le "$PRE"
# Standing gates, from the executing worktree root:
bash scripts/check_maintenance_pins.sh  # baseline-red cell "prompt log has no all-served (stale) entry" exists on the unedited base; require the failure set unchanged from that base set, never a bare exit 0
python3 scripts/skill_text_budget.py --check
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_skill_text_budget.py -q
bash scripts/check-no-em-dash.sh added-lines --base <base-ref>
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-11-09-memory-index-retirement-pass.md
```

### Task 1: Convention paragraph gains the retirement-pass sanction and the fire-outcome fold

Context surface: the plan's Terms and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode.md`

- [x] Presence witness (RED): `grep -c "Fire-outcome fold" agents/skills/maintenance/zcode.md` reports 0 and `grep -c "Retirement pass" agents/skills/maintenance/zcode.md` reports 0 before any edit [class: REPOSITORY_TEST]
- [x] Recompose the Standing retirement rule block adding the retirement-pass sanction without restating lane-file mechanics: the memory-index-audit lane's threshold-gated retirement member applies the rule's existing fold shapes as sanctioned targeted edits, its threshold, record scope, and run guards owned by that lane file; the composed text names the rule `Retirement pass` [class: IMPLEMENTATION_REQUIRED]
- [x] Add the fire-outcome fold rule to the same block: a fired run's outcome write folds its own pre-fire record line in the same targeted edit that records the outcome, so a pre-fire status phrase never survives a completed dispatch; the composed text names the rule `Fire-outcome fold` [class: IMPLEMENTATION_REQUIRED]
- [x] The recomposition keeps every existing bullet's semantics, and given the pre-edit byte count of the rule block plus its Terms paragraph re-derived from the base commit, expects the composed bytes at or below it [class: IMPLEMENTATION_REQUIRED]
- [x] Presence witness (GREEN): both Task 1 greps report nonzero counts, and `python3 scripts/skill_text_budget.py --check` reports the pre-existing advisory breach line for the file and no new caps-gap line for it [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` from the worktree root reports no pin failure beyond the base's recorded baseline-red set (the pre-existing cell `prompt log has no all-served (stale) entry`, identical on the unedited base); any new pin failure refuses the task [class: REPOSITORY_TEST]
- [x] Commit: `docs: convention retirement-pass sanction and fire-outcome fold` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Audit lane file gains the threshold-gated Retirement pass member

Context surface: the plan's Terms and `## Standing constraints`.

Files:
- `docs/maintenance/recurring-tasks/memory-index-audit.md`

- [x] Presence witness (RED): `grep -c "Retirement pass member" docs/maintenance/recurring-tasks/memory-index-audit.md` reports 0 before any edit [class: REPOSITORY_TEST]
- [x] Scope the lane intro's never-rewrites fence to the measure, check, classify, and report legs, admitting the Retirement pass member as the lane's one sanctioned index mutation arm, and align the Filing rule's mid-lane sentence with the same scope; given the unedited file, expects both sentences present before, scoped after, and no other Filing rule sentence changed [class: IMPLEMENTATION_REQUIRED]
- [x] Add the Retirement pass member definition: fires only when the measured index byte count exceeds the 20,000-byte proxy target; retires only terminal records; never retires live markers or conversation-scoped lane state; in-doubt entries stay (index-rather-than-prune); at most one pass per run [class: IMPLEMENTATION_REQUIRED]
- [x] Pin the drop precondition: an index line carrying a live do-not-redo marker drops only when the marker's durable signal keeps a reachable home (the successor or per-mandate summary line, the compressed index, or a git-tracked durable surface, per the Live-marker refusal capture rule and the chartered Survival audit); a signal surviving only in the untracked topic file fails the audit and the row refuses [class: IMPLEMENTATION_REQUIRED]
- [x] Pin the pass mechanics: the fold retires the oldest eligible rows first and stops once the post-pass measurement reads at or under the proxy target; when every eligible row retires and the target is still unmet, the run records the residual in the state record and the existing Filing rule carries the follow-up, the run not classified failed by the unmet target alone [class: IMPLEMENTATION_REQUIRED]
- [x] Pin the guard reuse: the existing Rollback posture, Index-write drift check, Post-write verification, and Atomic store writes members apply to the pass unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Presence witness (GREEN): the Task 2 grep reports a count of 2 or more, and each reused member is named exactly as the file defines it [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the Validation Commands battery from the worktree root passes with the pins line's failure set identical to the unedited base's recorded set (the one pre-existing baseline-red cell), and plan_readiness reports `OUTCOME: pass` at execution start, before the first checkbox flip [class: REPOSITORY_TEST]
- [x] Commit: `docs: audit lane retirement pass member` [class: IMPLEMENTATION_REQUIRED]
