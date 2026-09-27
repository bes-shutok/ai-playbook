# Plan: investigate skill + tracked rolling prompt log

Backlog origin: docs/history/backlog/2026-09-27-investigate-skill-urgent-prompt-rolling-log.md
Driving force: new-capability
Justification: the capability is load-bearing, not speculative: on 2026-09-27 an untracked group-roster scratch file caused a parallel validity triage to mass-reject 11 grouped origins, and the P77 guard decision inverted its own fix framing until ad hoc archaeology (git log -S, motivating plans, both-sides analysis) was run by hand. Park-triage would take this plan: operator directive, priority high, real class, consumer-facing authoring-lane defect.
Plan review record: the staging series docs/reviews/2026-09-27-plan-review-investigate-rolling-prompt-log-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Give the authoring lane a owned investigation step and a tracked, ordered home for ready-to-dispatch plan prompts.

- A new `investigate` skill runs issue archaeology and possibility-space analysis for a backlog item or group, and writes its recommended plan-creation prompt plus rejected-alternative dispositions into a tracked rolling log entry.
- Ready-to-dispatch authoring prompts live in one tracked file (`docs/history/backlog/PLAN-PROMPTS.md`, most urgent on top) that every ownership survey and parallel session can see, replacing the gitignored scratch file `docs/tmp/future-plan-prompts-2026-09-16.md`.
- The maintenance scheduler turn reads the log, prunes entries whose plan already exists in the plans root, and authors the top ready entry in-session through the existing authoring machinery's gates instead of losing queue order to chat.

## Terms

- **investigate skill**: the new `agents/skills/investigate/` skill; runs pre-authoring investigation and emits a log entry.
- **rolling prompt log** (or "the log"): `docs/history/backlog/PLAN-PROMPTS.md`; the single tracked queue of ready-to-dispatch authoring prompts, most urgent first.
- **plans root**: the resolved `plans_dir` (default `docs/history/plans/`); a plan file existing here is the authored state.
- **monitor step**: the new survey/decision duty added to the maintenance scheduler turn that reads, prunes, and dispatches from the log.
- **the scratch**: the gitignored `docs/tmp/future-plan-prompts-2026-09-16.md`, retired by this plan. The retirement covers only that one 2026-09-16 prompt-queue scratch file; the `docs/tmp/future-plan-prompts-<date>...` naming family stays owned by the maintenance park path (pending_rearm/pending_dispatch payload copies, pinned by `scripts/check_maintenance_pins.sh`) and is out of scope here; new park copies under that family are not remnants of the retired queue.

## Assumptions

- assume the log filename `PLAN-PROMPTS.md` in the backlog home is clean under the backlog-inbox shape gate; basis: `scripts/check_backlog_inbox_location.py` is filename-only and fires on basenames containing `backlog` or `deferred`, which `PLAN-PROMPTS.md` does not contain (read 2026-09-27).
- assume the docs-branch sync covers the log with no new wiring; basis: the sync is add-only over tracked `docs/history/` files per `agents/skills/docs-branch/SKILL.md` (read 2026-09-27), and the log is tracked repo content under the backlog home.
- assume plans must never cite the log as `Backlog origin` (the log is not a backlog item); plans produced from log entries cite the log as design input in prose instead; basis: the origin file's own gate-interaction note plus the plans skill's backlog-origin contract.
- assume no document-registry row is required for the log; basis: `scripts/doc_registry_validator.py` write-gates only the completed-history, rejected, context, and feature-notes directories (read 2026-09-27); the open backlog home is not gated.
- assume the maintenance SKILL.md additions stay runtime-agnostic and the existing authoring machinery (claims, guards, stand-down gates) is reused in-session with the log-entry substitutions prescribed in Task 3; the scheduled-child payload template (`agents/skills/maintenance/prompt-templates.md`) is not modified and log entries are never dispatched through it; basis: the runtime-agnosticism pin in `scripts/check_maintenance_pins.sh`, the item-keyed payload gates in `agents/skills/maintenance/prompt-templates.md`, and the authoring-child contract in `agents/skills/maintenance/SKILL.md`.
- assume deleting the scratch loses nothing already tracked: its fulfilled P0-P71 entries are recorded in `docs/history/plans/completed/` plans and session memory; basis: STATUS-line survey of the scratch, 2026-09-27.
- assume the `investigate` skill carries an MIT `LICENSE.txt` copied from `agents/skills/plans/LICENSE.txt`; basis: repository guideline "Every new skill directory must include LICENSE.txt".
- assume no plan-readiness gate interaction with the log; basis: `scripts/plan_readiness.py` gates plan files structurally and does not require a `Backlog origin` line (read 2026-09-27).

Decision points requiring a grill: log shape: one tracked file `docs/history/backlog/PLAN-PROMPTS.md`, one section per entry, most urgent on top, with an explicit maintenance survey exclusion for the log basename, source user grill answer 2026-09-27, affects Terms, Task 1, Task 2, Task 3, recorded 2026-09-27; scratch retirement: migrate only still-live entries into the log, then delete the gitignored scratch after per-origin verification, source user grill answer 2026-09-27, affects Task 1, recorded 2026-09-27; prune trigger: an entry leaves the log when its plan file exists in the plans root (prune at authored), and the monitor step additionally refuses to dispatch any entry whose plan file exists, source user grill answer 2026-09-27, affects Task 1 and Task 3, recorded 2026-09-27; investigate output destination: the log entry itself carries the recommended prompt and the rejected-alternative dispositions, no gitignored side record, source user grill answer 2026-09-27, affects Task 1 and Task 2, recorded 2026-09-27.

## Gist & Examples

TLDR: adds an investigate skill and a tracked rolling prompt log, so ready-to-dispatch authoring prompts and the investigation behind them survive session boundaries; new-capability, closing the witnessed untracked-scratch and ad-hoc-archaeology gaps.

Today, the prompt queue for plan authoring lives in gitignored scratch (`docs/tmp/` is in `.gitignore` line 16), so an ownership survey in a parallel session cannot see it. That caused the 2026-09-27 mass rejection: a validity triage session rejected 11 of 22 grouped origins because the group roster was invisible to it. And when an operator asks a "should this guard exist" question, the archaeology that answers it (when was it introduced, what incident motivated it, what depends on it, what are the complement gaps) is re-derived ad hoc each time with turn-dependent quality.

After this plan:

1. An operator or maintenance turn facing a backlog item runs the investigate skill. It checks the open backlog for grouped siblings, runs archaeology on each guard or contract the item touches, enumerates the possibility space including the remove-or-keep axis and the missing-complement axis, and writes one log entry: the recommended plan-creation prompt (origins, scope arms, orientation, surfaces) plus one-line dispositions for each rejected alternative.
2. The maintenance scheduler turn's survey excludes the log from open-backlog triage, prunes entries whose plan file already exists in the plans root, and authors the top ready entry in-session as an additional authoring target beside the existing backlog-item path.
3. The gitignored scratch is deleted after its still-live entries are migrated and verified.

Example (witness, from the origin file): the P77 routing produced a one-arm prompt first; only operator pushback and by-hand guard archaeology produced the correct two-arm scope (seed gate plus recovery path). Under this plan, the archaeology step is owned, and its two-arm output would have been a tracked log entry visible to every session.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every prescribed insertion lands in the file the task names; the validation block is fail-closed and each structural obligation the block can discriminate has its own dedicated grep (content-shaped obligations, such as the Configuration section contents, the Integration Points prose, and the Revisions entry, are witnessed by Task 5's re-read/reconcile item).
- simplicity: the log is one file, the monitor step reuses the existing authoring machinery (no new dispatch path, no new state file fields), and the investigate skill adds no new gates.
- visibility: after execution, the ready-to-dispatch authoring prompt queue lives in git: a fresh session's ownership survey finds the log by listing tracked files. (The pinned maintenance park-payload copies under `docs/tmp/` remain gitignored by design and are out of scope; see Terms.)
- runtime-agnosticism: all new skill and skill-edit prose stays tool-agnostic (no runtime primitive names in `agents/skills/maintenance/SKILL.md`, per the existing pins).

**Done when:**
- all task checklists are checked and the Validation Commands block exits 0 from the repository root.
- `bash scripts/check-no-em-dash.sh touched` exits 0 and the public-hygiene scan (public_hygiene_scan_script in the user facts document) exits 0.
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-09-27-investigate-skill-rolling-prompt-log.md` exits clean (structural checks; the full gate binds at review certification).

**Ship when:**
- an operator dispatches an authoring turn from a log entry in a fresh session, and a parallel ownership survey session sees the log by default (human-adopted workflow; prose, no checklist item).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/investigate/SKILL.md` *(new)*
- `agents/skills/investigate/LICENSE.txt` *(new)*
- `docs/history/backlog/PLAN-PROMPTS.md` *(new)*
- `agents/skills/maintenance/SKILL.md`
- `README.md`
- `projects/.ai-playbook/agent-runtime-layout.md`

**Tests:**
- none; this plan prescribes documentation and skill-prose work only. Verification is the Validation Commands block plus the existing mechanical gates (`scripts/check_backlog_inbox_location.py`, `scripts/check_maintenance_pins.sh`, em-dash scan, hygiene scan).

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/zcode.md` and `agents/skills/maintenance/prompt-templates.md`; reason: the monitor step is runtime-agnostic prose in SKILL.md, log entries are authored in-session and never dispatched through the payload template (Task 3 machinery-mapping duty), and the runtime overlay changes only if execution finds a genuine wiring gap (then it is plan-related and in scope).
- any backlog item other than the origin file; reason: origin dispositions are the monitor step's runtime behavior, not edits to other items.
- `docs/tmp/future-plan-prompts-2026-09-16.md`; reason: gitignored and deleted by Task 1; nothing reviewable remains.

## Validation Commands

Authoring-time record (2026-09-27): pre-round readiness gate clean (structural checks); em-dash scan and public-hygiene scan exit 0 over the plan bytes; the validation block executed RED-today in the authoring worktree with the FIRST failing gate G1 (log missing, exit 1). Post-r1-fold re-execution (same day): fail set G1, G4, G5, G6 as expected for a creation plan (targets not yet implemented); G3 clean; G2 vacuous pass in this worktree (N/A, see G2 comment); G7's em-dash leg fails only with BASE unset and is green with the recorded base (added-lines mode verified). Note on G2: it is a deletion gate over a gitignored path, so in this worktree it passes vacuously (the scratch is absent here and lives only in the primary checkout) and in the scratch-holding checkout it is RED until Task 1's deletion lands there; a vacuous G2 never discharges Task 1's deletion item (see G2 comment and Task 1 precondition). The same executions confirmed every G4-G6 needle RED (no matches in the current files).

```bash
# Run from the repository root. Fail-closed block: any FAIL exits 1.
# BASE must be exported before the first task commit: the commit sha recorded
# at execution start, so the em-dash gate's added-lines mode re-witnesses the
# plan's committed changes on post-commit reruns.
fail=0

# Local fail-closed guard: BASE must be set (see header comment).
[ -n "${BASE:-}" ] || { echo "FAIL: BASE unset"; fail=1; }

# G1: the log exists and carries its format obligations (distinctive spans, one grep each).
if [ ! -f docs/history/backlog/PLAN-PROMPTS.md ]; then echo "FAIL: log missing"; fail=1;
else
  grep -qF "Tracked rolling log of ready-to-dispatch plan-creation prompts, most urgent first." docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: log header span missing"; fail=1; }
  grep -qF "Prune rule: an entry is removed when its plan file exists in the plans root." docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: log prune-rule span missing"; fail=1; }
  grep -qF "Not a backlog item: never cite this file as a plan's Backlog origin." docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: log not-a-backlog-item span missing"; fail=1; }
  grep -qF "Rejected alternatives:" docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: log entry template missing"; fail=1; }
  grep -qF "Urgency:" docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: log urgency field missing"; fail=1; }
  grep -qF "Prompt:" docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: log prompt field missing"; fail=1; }
  grep -qF "Before every write, re-read the file and compare it against the read the edit was prepared from; any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file (conflict-free under the targeted-edit rule); only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the next write attempt re-emits from that record instead of re-running the investigation." docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: log write-discipline rule missing"; fail=1; }
  grep -qF "Writes are targeted section edits (an entry's own section), never a whole-file rewrite from a stale read." docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: log targeted-edit rule missing"; fail=1; }
  grep -qF "Every log write is committed in the same turn that performs it." docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: log commit rule missing"; fail=1; }
  grep -qF "Entries carry repo-relative paths only and no personal or machine-specific data." docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: log hygiene rule missing"; fail=1; }
fi

# G2: the scratch is gone. Deletion gate over a gitignored path: it only
# discriminates in the checkout that held the scratch (the primary checkout,
# where Task 1's scratch steps run); in any other checkout it passes
# vacuously and is recorded N/A, never green.
if [ -e docs/tmp/future-plan-prompts-2026-09-16.md ]; then echo "FAIL: scratch still present"; fail=1; fi

# G3: no plan cites the log as Backlog origin. Bracket-escaped literal is
# intentional self-match immunity: this plan's own tracked bytes carry the
# escaped form and must not match. Three-way exit split: rc 0 = forbidden
# match (fail), rc 1 = clean, rc >= 2 = tool error (fail).
rc=0
grep -rn "Backlog origin:.*PLAN-PROMPT[s]" docs/history/plans --include='*.md'
rc=$?
if [ "$rc" -eq 0 ]; then echo "FAIL: log cited as Backlog origin"; fail=1;
elif [ "$rc" -ge 2 ]; then echo "FAIL: G3 grep tool error rc=$rc"; fail=1; fi

# G4: the investigate skill exists with its stage, gate, and integration obligations (dedicated greps per obligation).
if [ ! -f agents/skills/investigate/SKILL.md ] || [ ! -f agents/skills/investigate/LICENSE.txt ]; then echo "FAIL: investigate skill files missing"; fail=1;
else
  grep -qF "### Stage 1: group discovery" agents/skills/investigate/SKILL.md || { echo "FAIL: stage 1 missing"; fail=1; }
  grep -qF "### Stage 2: issue archaeology" agents/skills/investigate/SKILL.md || { echo "FAIL: stage 2 missing"; fail=1; }
  grep -qF "### Stage 3: possibility space" agents/skills/investigate/SKILL.md || { echo "FAIL: stage 3 missing"; fail=1; }
  grep -qF "### Stage 4: log entry emission" agents/skills/investigate/SKILL.md || { echo "FAIL: stage 4 missing"; fail=1; }
  grep -qF "## Hard gates" agents/skills/investigate/SKILL.md || { echo "FAIL: hard gates section missing"; fail=1; }
  grep -qF "## Integration Points" agents/skills/investigate/SKILL.md || { echo "FAIL: investigate integration points missing"; fail=1; }
  grep -qF "## Integration Points" agents/skills/maintenance/SKILL.md || { echo "FAIL: maintenance integration points missing"; fail=1; }
  rc=0
  grep -niE "codex|cursor|claude|zcode|opencode|copilot|gemini|antigravity" agents/skills/investigate/SKILL.md
  rc=$?
  if [ "$rc" -eq 0 ]; then echo "FAIL: runtime name in investigate SKILL.md"; fail=1;
  elif [ "$rc" -ge 2 ]; then echo "FAIL: G4 grep tool error rc=$rc"; fail=1; fi
fi

# G5: the maintenance monitor step obligations (dedicated greps per obligation).
grep -qF "Rolling prompt log duties" agents/skills/maintenance/SKILL.md || { echo "FAIL: monitor step heading missing"; fail=1; }
grep -qF "excludes the rolling prompt log file" agents/skills/maintenance/SKILL.md || { echo "FAIL: survey exclusion missing"; fail=1; }
grep -qF "refuses to dispatch an entry whose plan file already exists" agents/skills/maintenance/SKILL.md || { echo "FAIL: dispatch refusal missing"; fail=1; }
grep -qF "removes any log entry whose plan file exists in the plans root" agents/skills/maintenance/SKILL.md || { echo "FAIL: prune duty missing"; fail=1; }
grep -qF "citing the entry (not a backlog item) as the prompt source" agents/skills/maintenance/SKILL.md || { echo "FAIL: prompt-source duty missing"; fail=1; }
grep -qF "at most one investigation per turn" agents/skills/maintenance/SKILL.md || { echo "FAIL: investigate bound missing"; fail=1; }
grep -qF "keyed on the entry slug" agents/skills/maintenance/SKILL.md || { echo "FAIL: machinery mapping missing"; fail=1; }
grep -qF "the state intent wins" agents/skills/maintenance/SKILL.md || { echo "FAIL: state-intent precedence missing"; fail=1; }
grep -qF "re-read and compare before every write" agents/skills/maintenance/SKILL.md || { echo "FAIL: monitor write discipline missing"; fail=1; }
grep -qF "in-session log-entry covered-stand-down" agents/skills/maintenance/SKILL.md || { echo "FAIL: carve-out amendment missing"; fail=1; }

# G6: catalog rows.
grep -qF "agents/skills/investigate/SKILL.md" README.md || { echo "FAIL: README row missing"; fail=1; }
grep -qF "agents/skills/investigate/SKILL.md" projects/.ai-playbook/agent-runtime-layout.md || { echo "FAIL: runtime-layout row missing"; fail=1; }
grep -qF "top ready entry of docs/history/backlog/PLAN-PROMPTS.md" README.md || { echo "FAIL: README monitor-step sentence missing"; fail=1; }
grep -qF "top ready entry of docs/history/backlog/PLAN-PROMPTS.md" projects/.ai-playbook/agent-runtime-layout.md || { echo "FAIL: runtime-layout monitor-step note missing"; fail=1; }

# G7: existing mechanical gates still hold over the edited files.
python3 scripts/check_backlog_inbox_location.py || { echo "FAIL: inbox gate"; fail=1; }
bash scripts/check_maintenance_pins.sh || { echo "FAIL: maintenance pins"; fail=1; }
bash scripts/check-no-em-dash.sh added-lines --base "$BASE" || { echo "FAIL: em-dash scan"; fail=1; }

# G8: the public-hygiene scan (the script home is public_hygiene_scan_script
# in the user facts document; resolved here to its deployed default path).
bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" || { echo "FAIL: hygiene scan"; fail=1; }

if [ "$fail" -eq 1 ]; then echo "VALIDATION FAILED"; exit 1; fi
echo "VALIDATION OK"
```

### Task 1: Create the rolling prompt log and retire the scratch

Files:
- `docs/history/backlog/PLAN-PROMPTS.md` *(new)*

(The scratch deletion target `docs/tmp/future-plan-prompts-2026-09-16.md` is gitignored and untracked, so it is not a Files entry; its deletion is prescribed and gated in the checklist items below.)

- [x] Create `docs/history/backlog/PLAN-PROMPTS.md` opening with the exact line `Tracked rolling log of ready-to-dispatch plan-creation prompts, most urgent first.`, followed by the standing rules, including the exact lines `Prune rule: an entry is removed when its plan file exists in the plans root.` and `Not a backlog item: never cite this file as a plan's Backlog origin.`, the write-discipline rule with the exact span `Before every write, re-read the file and compare it against the read the edit was prepared from; any difference is drift: retry once from the fresh read, then attempt a pure append of the entry at the end of the file (conflict-free under the targeted-edit rule); only when that append also fails the drift check, abort and report the full intended entry text in the turn output as the fallback record; the next write attempt re-emits from that record instead of re-running the investigation.`, the targeted-edit rule with the exact span `Writes are targeted section edits (an entry's own section), never a whole-file rewrite from a stale read.`, the commit rule with the exact span `Every log write is committed in the same turn that performs it.`, the per-write hygiene rule with the exact span `Entries carry repo-relative paths only and no personal or machine-specific data.`, and an entry template: heading with a short slug, `Added:`, `Origins:` (backlog paths), `Urgency:`, `Prompt:` (full payload), `Rejected alternatives:` (one line each). [class: IMPLEMENTATION_REQUIRED]
- [x] Precondition: record the base commit sha in a shell variable `BASE` before the first task commit (the em-dash gate's added-lines mode consumes it). Scratch steps: the gitignored scratch lives only in the primary checkout, so the seeding and deletion steps run in the checkout where `docs/tmp/future-plan-prompts-2026-09-16.md` exists; begin with a presence check that aborts loudly when the scratch is absent there (a missing scratch in the holding checkout is an abort-and-report, never an empty migration; in any other checkout G2 is recorded N/A, never green, and does not discharge this item). [class: IMPLEMENTATION_REQUIRED]
- [x] Seed the log from the scratch: for each still-live scratch entry, verify against the current tree that no plan covering its origins exists in the plans root (git log and the plans-root listing, not the scratch's own STATUS lines), then write the entry in the log. Do not migrate fulfilled or superseded entries; their record lives in `docs/history/plans/completed/`. [class: IMPLEMENTATION_REQUIRED]
- [x] Order entries most-urgent-first per the log header; the seeding turn records the urgency judgment in each entry's `Urgency:` line. [class: IMPLEMENTATION_REQUIRED]
- [x] Durable-write ordering: commit `docs/history/backlog/PLAN-PROMPTS.md` with all migrated entries first, so the migrated queue is durable in git; only then delete `docs/tmp/future-plan-prompts-2026-09-16.md` (plain delete; the gitignored bytes are not in main history, and a stale docs-branch shadow copy, if any, is swept at the next docs sync and is not a migration source). Before deleting, confirm the log carries every origin the scratch listed as still live and state in the turn output that the log bytes are committed; a mismatch aborts the deletion with the mismatch reported. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the validation block through G3 in the scratch-holding checkout; expect G1 and G2 green after this task there (in any other checkout G1 green and G2 N/A) and G3 green (no plan has ever cited the log). [class: REPOSITORY_TEST]

### Task 2: Author the investigate skill

Files:
- `agents/skills/investigate/SKILL.md` *(new)*
- `agents/skills/investigate/LICENSE.txt` *(new)*

- [x] Create `agents/skills/investigate/SKILL.md`, tool-agnostic and repo-relative throughout, with: a purpose statement (pre-authoring investigation for a backlog item or small set, producing a plan-creation prompt) that pins the boundary against the plans skill in one line: investigate runs autonomously with no user interview and stops at the log entry, while plans Phase 1 owns user-facing requirements discovery and consumes the log entry as design input; a "Configuration (from facts document)" section listing the `plans_dir` and `backlog_dir` facts keys with their defaults; the four stages below, each its own `### Stage N:` heading with the exact heading text pinned in the validation block; a `## Hard gates` section; and an `## Integration Points` section. [class: IMPLEMENTATION_REQUIRED]
- [x] Stage 1 is exactly `### Stage 1: group discovery`: check the open backlog (resolved `backlog_dir`) for similar or grouped items; when found, investigate the group as one unit and record the roster in the log entry so parallel sessions see it (the witnessed 2026-09-27 mass-rejection cause). [class: IMPLEMENTATION_REQUIRED]
- [x] Stage 2 is exactly `### Stage 2: issue archaeology`: for each guard, contract, or mechanism the item touches, establish when and why it was introduced (history search such as `git log -S`, the motivating plan or incident, current dependents) before judging it. [class: IMPLEMENTATION_REQUIRED]
- [x] Stage 3 is exactly `### Stage 3: possibility space`: enumerate the alternatives including the remove-or-keep axis and the missing-complement axis (a correct mechanism with a missing complement is completed, not removed); a recommendation must name what was rejected and why. [class: IMPLEMENTATION_REQUIRED]
- [x] Stage 4 is exactly `### Stage 4: log entry emission`: write one entry into the rolling prompt log (`docs/history/backlog/PLAN-PROMPTS.md`) at the urgency position the entry merits: origins, scope arms, orientation, the full ready-to-dispatch prompt payload, and one-line dispositions for each rejected alternative. The entry is the artifact; no side record under the gitignored scratch directory. The write follows the log's standing rules: a targeted section edit prepared from a fresh read (re-read, compare, drift retry, and abort-with-fallback per the write-discipline rule), the entry carries repo-relative paths only and no personal or machine-specific data, and the write is committed in the same turn. [class: IMPLEMENTATION_REQUIRED]
- [x] `## Hard gates` in the skill: never execute or dispatch anything (the skill ends at the log entry); never cite the log as a plan's Backlog origin; keep every path repo-relative. [class: IMPLEMENTATION_REQUIRED]
- [x] `## Integration Points` in the investigate skill names the maintenance scheduler turn as consumer (its monitor step invokes investigate for ungrouped backlog items when the log has no ready entry, and reads the emitted entries) and plans as downstream consumer of the emitted prompt; verify the claims against the Task 3 prescription in this plan before finalizing (the landed maintenance text does not exist yet at this task's execution time). [class: IMPLEMENTATION_REQUIRED]
- [x] Copy `agents/skills/plans/LICENSE.txt` to `agents/skills/investigate/LICENSE.txt` unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check-no-em-dash.sh touched` and the public-hygiene scan; expect exit 0 for both. [class: REPOSITORY_TEST]

### Task 3: Wire the monitor step into the maintenance scheduler turn

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] In the Step 1 survey section, add the exclusion: the open-backlog listing `excludes the rolling prompt log file` (`PLAN-PROMPTS.md` under the resolved backlog home) so the log is never triaged as a backlog item. [class: IMPLEMENTATION_REQUIRED]
- [x] Add a `Rolling prompt log duties` subsection inside Step 3 (decision), evaluated after the D2 decision, with these duties, reusing the existing authoring machinery's gates with no new state-file fields. The monitor dispatch is subject to the Step 3 standing authoring-lane exclusions unchanged: when loop-mode enforcement or `authoring_cycle_gate` resolves the authoring lane to D3, or the audit/retriage same-turn contention clause takes the slot, the top entry is held with the standing reason recorded and re-decided next turn. Duties: (a) read the log top-down; (b) `removes any log entry whose plan file exists in the plans root` (prune at authored) before any dispatch decision. [class: IMPLEMENTATION_REQUIRED]
- [x] Dispatch duty: (c) when the authoring lane is free, the top entry is ready, and the entry was not appended in the same scheduler turn (a same-turn investigate output is not a dispatch candidate until a later turn), author the top entry in-session, `citing the entry (not a backlog item) as the prompt source`; the in-session log-entry authoring occupies the turn's single authoring slot (when it fires, D2 resolves to no-op under the recorded reason `log-entry-authoring`; when D2 already has a target, the entry is held, so one turn never authors both a backlog item and a log entry), and on quota-scarce or otherwise dispatch-blocked conditions the entry is held with a recorded reason (the log is the retention; the entry is re-decided next turn, never routed through the scheduled-child payload path). [class: IMPLEMENTATION_REQUIRED]
- [x] Machinery-mapping duty: (d) the in-session authoring applies the log-entry substitutions: the pre-work stand-down gates are restated as the entry is still present in the log and no plan file for its origins exists in the plans root, the authoring claim file is keyed on the entry slug, an in-session log-entry run that stands down under the restated pre-work gates records the outcome in its `(in-session)` `children[]` entry with `outcome_reason: covered-stand-down` and the justification in `decision_reason` (no marker file; the payload-side stand-down marker is a scheduled-child surface this plan does not touch), and the in-session `children[]` entry's `target` for a log-entry authoring run is the entry slug (marked in-session) so the G1a discovery arm's target-keyed explanation match works against the slug-keyed claim; on a slug collision in the claim or `children[]` target, stand down with a recorded reason rather than overwriting; the scheduled-child payload (`agents/skills/maintenance/prompt-templates.md`) is not modified and log entries are never dispatched through it, and pending-dispatch retention for log-entry targets is out of scope. [class: IMPLEMENTATION_REQUIRED]
- [x] Investigate duty: (e) when the log has no ready entry, skip any ungrouped open backlog item whose origins intersect an existing log entry's `Origins:` line or a plans-root plan file (recording the skip reason), then invoke the investigate skill on the highest-priority remaining one to append one entry, `at most one investigation per turn`. [class: IMPLEMENTATION_REQUIRED]
- [x] Precedence duty: (f) before dispatching a log entry, consult the scheduler state file for a live pending_dispatch intent (or parked payload copy) naming the same target or origins: `the state intent wins`, and the monitor holds the log entry with a recorded reason until the intent resolves, pruning only if a covering plan file already exists per the log's prune rule. [class: IMPLEMENTATION_REQUIRED]
- [x] Race re-check duty: (g) immediately before any dispatch decision, re-check the plans root for the entry's origins and `refuses to dispatch an entry whose plan file already exists`, standing down with a recorded reason; the in-session authoring re-checks both the entry's presence in the log and the plans root for the entry's origins before writing any plan file, standing down with a recorded reason when either fails. [class: IMPLEMENTATION_REQUIRED]
- [x] Write-discipline duty: (h) the monitor's log-writing duties (prune, investigate append) follow the log's standing rules: re-read and compare before every write, targeted section edits, commit the write in the same turn, and run the public-hygiene scan over the log after any write the turn performs. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep every new line runtime-agnostic: no runtime automation-primitive names; runtime-specific mechanics stay in the runtime overlay files which this task does not edit. [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the covered-stand-down carve-out paragraph and the children[] entry schema note in the same SKILL.md edit so the in-session log-entry variant is a second qualified surface named `in-session log-entry covered-stand-down`: its target is the entry slug, its qualification is the checking turn re-running the restated pre-work gates (the entry absent from the log, or a covering plan file existing in the plans root, per the `decision_reason` justification), explicitly no marker file, and the failure-cap exclusion applies to it unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Add an `## Integration Points` section to the maintenance SKILL.md naming the investigate skill bidirectionally: maintenance's monitor step consumes investigate's log entries and invokes investigate per duty (e); investigate's Integration Points entry names maintenance as its consumer. [class: IMPLEMENTATION_REQUIRED]
- [x] Append a Revisions entry dated 2026-09-27 summarizing the monitor step addition. [class: IMPLEMENTATION_REQUIRED]
- [x] Run `bash scripts/check_maintenance_pins.sh`; expect exit 0 (guard order, agnosticism, and all existing pins intact). [class: REPOSITORY_TEST]

### Task 4: Catalog rows

Files:
- `README.md`
- `projects/.ai-playbook/agent-runtime-layout.md`

- [x] Add a README skill-catalog row for `investigate` (path `agents/skills/investigate/SKILL.md`): pre-authoring investigation that turns a backlog item or group into a tracked rolling-log entry with a recommended plan-creation prompt and rejected-alternative dispositions; complements `plans` Phase 1 and the maintenance monitor step. [class: IMPLEMENTATION_REQUIRED]
- [x] Add the matching row in `projects/.ai-playbook/agent-runtime-layout.md` with the same path and a one-line scope note. [class: IMPLEMENTATION_REQUIRED]
- [x] Update the README maintenance row's decision-order sentence, and add a one-line maintenance scope note to `projects/.ai-playbook/agent-runtime-layout.md` (the file has no maintenance note today), each naming the monitor step with the exact span `top ready entry of docs/history/backlog/PLAN-PROMPTS.md`. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify no other README or layout row duplicates or contradicts the new rows (search for existing investigate mentions); update stale mentions if found. [class: REPOSITORY_TEST]

### Task 5: Full validation

Files: none (verification only)

- [x] Re-read `agents/skills/investigate/SKILL.md` `## Integration Points` against the landed Task 3 maintenance text and confirm every claim about the monitor step matches what landed; re-read its Configuration (from facts document) section against the facts keys; confirm the maintenance SKILL.md Revisions entry landed as prescribed; reconcile any mismatch in the same run. [class: REPOSITORY_TEST]
- [x] Run the complete Validation Commands block from the repository root with `BASE` set per Task 1; expect `VALIDATION OK` (exit 0). [class: REPOSITORY_TEST]

## Origins dispositions

- `docs/history/backlog/2026-09-27-investigate-skill-urgent-prompt-rolling-log.md`: folded - executed in full by this plan (investigate skill, tracked rolling prompt log, maintenance monitor step); item file fold-then-deleted at archive.

## Disposition of migrated backlog items

Fold-then-delete consult (execution completion 2026-09-28): the origin item file below was deleted from the open backlog top level after its scope landed.

- docs/history/backlog/2026-09-27-investigate-skill-urgent-prompt-rolling-log.md
