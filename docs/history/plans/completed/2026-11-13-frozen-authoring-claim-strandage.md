# Plan: Authoring parked-state records for frozen-entry strandage

Backlog origin: docs/history/backlog/2026-11-11-frozen-authoring-claim-strandage.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-frozen-authoring-claim-strandage-p4b59f408-r*.md
Execution budget: 1.5h total, largest task 0.5h
Authoring claim: 2026-11-11-frozen-authoring-claim-strandage.md (session sess_5e402b47-4239-4c7e-a3f5-cdf18b8195b1)
Executed: yes (9d8f02ea45d8d641cf71a9795aa78956a354f2c8)

## Terms

- Parked-state record: one `parked-state:` body line in the authoring claim file (docs/tmp/authoring-claims/<backlog-item-basename>.md) recording where a paused or exited authoring run's parked state lives; the claim file's own identity, ownership re-check, freshness, and deletion lifecycle govern it.
- Parked state: the staged review findings, resume notes, and telemetry a frozen authoring run leaves under the resolved tmp tree (for example `docs/tmp/authoring/<plan-slug>/` or `docs/tmp/execute-plan/<plan-slug>/`) or in the authoring worktree's `.ai-playbook/reviews/` staging home before its landing-time migration.
- Frozen entry: a PLAN-PROMPTS.md entry carrying the `Frozen:` mark per the log's Standing rules Freeze rule; a frozen entry is never a dispatch candidate until the mark clears or the entry is pruned.
- Claim: the authoring claim file the AUTHORING CLAIM duty (agents/skills/maintenance/template-authoring.md) creates and governs: five frontmatter lines (session, item, created, updated, runtime_id) plus free body content.
- Stale-foreign-claim takeover: the AUTHORING CLAIM procedure's path that deletes a foreign claim stale past one cadence period and re-creates the claim for the taking session.
- Quota wall: a provider usage refusal that pauses or kills a session (the 5h-window exhaustion shape the loop's quota leg governs).
- The monitor: the scheduler turn's rolling-log step (agents/skills/maintenance/decisions.md, the Rolling prompt log duties bullet) that prunes, freezes, and clears entries in both logs.
- Machinery inventory: the registry for repo gates (scripts/machinery_registry.json; recorded-red register scripts/gate_liveness_ledger.json; the pre-existing advisory rows the validation battery triages against).
- Pickup paths: the entry's names for the three paths that open a frozen entry: the fresh-dispatch availability walk (the authoring selection's availability check), the clearance-arm unfreeze (duty (b)'s mark-clears clause, agents/skills/maintenance/decisions.md), and the stale-foreign-claim takeover (the AUTHORING CLAIM procedure).
- Cadence period: 2 hours, the loop's freshness bound.
- Clearance record: the durable entry-scoped line the monitor's clearance targeted log edit writes into the frozen entry, replacing any prior one, recording the parked-state path or none; the claim-absent pickup branch consumes it.
- Run report: the reporting session's own run report or decision record; the sink for recorded discards and raced-pick continuations, never a stand-down-class record.
- Payload-side mirror: the scheduled-child payload template's embedded AUTHORING CLAIM DUTY text in agents/skills/maintenance/template-authoring.md, the compact duty set beside its takeover sentence.

## Why

An authoring session that dies at a quota wall strands three things together: the entry stays frozen, the staged review rounds it parked have no consumer duty, and nothing records where the parked state lives, so the next pickup re-authors from scratch and silently discards the staged rounds. One window witnessed three such deaths; one held ten staged lens findings.

## Gist & Examples

TLDR: a parked-state record on the authoring claim plus pickup duties so a dead authoring run's parked rounds are consumed instead of discarded, converting strandage into resumable work (efficiency).

Before (today): a session freezes the `exec-dispatch-claim-recheck` entry, stages five r1 and five r2 lens findings under `docs/tmp/authoring/exec-dispatch-claim-recheck/`, then dies at the 2026-11-11 quota wall. No record names that directory. The next pickup session sees only a frozen entry with a stale claim, takes the takeover path, and re-authors from scratch; the ten staged findings silently vanish. A second witnessed variant: an entry frozen at 00:56 while a parallel landing at 00:34 made its premise stale, and nothing flags the staleness to the pickup.

After (this plan): the dying session, at any pause or exit boundary it observes that leaves the claim standing (and when it first creates its parked-state directory), replaces exactly the `parked-state:` line in its own claim file with the parked-state path (or `none`); the write rides the claim duty's ownership re-check, and the claim's existing `updated:` freshness stays the one freshness surface. Every pickup path reads the claim's parked-state line whenever the path fires, with one ordering stated once in the convention home: premise re-derivation first, then the named parked-state path's existence check (the recorded value names its explicit-rooted location; the check resolves against that root), then resume or recorded discard; the read precedes any claim-deleting boundary, so a takeover consumes the line before its delete-first unlink. Authoring-side pickups (fresh dispatch, takeover) resume the parked rounds or record the discard in the run report or decision record; the monitor's clearance read informs the clearance decision, and the clearance's targeted log edit records the path (or none) as a durable entry-scoped clearance-record line, the sink the claim-absent pickup branch consumes. Frozen-line provenance is single-homed in the Freeze rule: a claim owner's self-freeze names its own session id; duty (b)'s mark arm stays a sanctioned writer recording the observed claim's session id (or `unowned` when none is readable); its mark-clears clause stays the sanctioned remover; a mark whose recorded writer is neither is the investigable class.

Edge cases: a pause with no parked state writes `parked-state: none`, still recording the boundary; no independent age gate exists for the parked-state line, so a stale claim's line is still readable at the pickup paths that a stale claim opens; an abrupt hard kill writes nothing at the kill boundary itself (no session turn observes it); a kill after the run first created its parked-state directory leaves the creation-time line standing, so the line-exists read path covers it, while the no-line recorded-discard branch covers only kills before any parked state existed, as does a swept parked-state directory found absent at read time; the claims directory's sweep retention is the sibling plan's surface (`authoring-claim-sweep-exemption-and-refresh-recipe`).

## Outcome

A quota-wall death no longer silently discards an authoring run's staged rounds.

- The dying session records the parked-state path on its claim at every observed pause or exit boundary that leaves the claim standing.
- Every pickup path reads the parked-state line before re-authoring, re-derives the premise first, and resumes or records the discard reason; the monitor's clearance read informs the clearance decision and records the path for the next dispatch.
- Frozen-line provenance is single-homed in the Freeze rule with the monitor's arms explicitly sanctioned.

Gate delta: none (recorded-convention text only: one body line on the existing claim file, written and read by existing paths under their existing ownership and freshness rules; no gate, validator, lock, ledger, schema field, refusal class, or dispatch-pausing condition added or removed).

Follow-up disposition: existing strands (the 2026-11-10/11 frozen entries) resolve through the existing clearance and takeover paths; this plan adds no retroactive sweep and promotes no follow-up row unless review evidences one, in which case it takes the durable backlog route; the queued sibling entry's five-line frontmatter shape assertion reconciles on that sibling's own landing path (this landing's parked-state line is body content, not frontmatter).

## Assumptions

- assume the parked-state record lives as a `parked-state:` body line in the claim file, not a sibling file, Frozen-line field, frontmatter line, or directives-home record; basis: the AUTHORING CLAIM duty pins the frontmatter keys, not the body, so one body line inherits the claim's writer, readers, freshness, and deletion lifecycle instead of re-creating all four for a sibling file (simpler-design comparison recorded 2026-11-13; receipt in the trailer).
- assume parked-state or record loss degrades to a recorded restart discard, never a stop; basis: the resume-or-record-discard branches specified in this plan tolerate absence by design, and sweep retention is the sibling plan's surface.
- assume D-18 composition rides wording only: the parked-state record is evidence recorded beside the exit token, never a new token; basis: D-18 (`docs/maintenance/operator-directives.md`) adds no primitives by its own terms and the dispatch entry orders composition, not forking.
- assume no scheduler-state schema change: the record is a claim-file body line, not a state field; basis: the PLAN-PROMPTS entry's Machinery admission field is removal-shaped.

- assume the provenance clause supersedes the dispatch entry's scope arm (3) writer-only wording; basis: duty (b)'s existing mark arm and the Phase 0 entry freeze are existing sanctioned writers, owning-session-only would be a behavior change beyond a recorded convention, and the entry is pruned at this landing per the prune rule; a Frozen mark naming the deposed predecessor a takeover consumed is legitimate succession until that prune (a freeze already present is verified, never rewritten).

Decision points requiring a grill: parked-state placement: maintenance-selected receipt 2026-11-13 (session sess_5e402b47): claim-body parked-state line selected over sibling file, Frozen-line field, claim-frontmatter line, and directives-home record after r1 F7 evidenced the body region is unpinned; basis and affected sections as in Assumption 1; Provenance scoping: maintenance-selected receipt 2026-11-13 (session sess_5e402b47): self-freeze/monitor-arm split supersedes the entry's scope arm (3) writer-only wording per Assumption 5; affects Task 2.

## Standing constraints

- Skill text stays tool-agnostic: describe behaviors by intent, never runtime tool names (repository guidelines, Skill Design Guidelines).
- Byte-budget duty: a change that grows a skill file past its cap deletes equivalent bytes in the same change (`scripts/skill_text_budget.py --check` must stay blocking-clean).
- No machinery: no gate, validator, lock, ledger, required ceremony, or scheduler-state schema field is added; wording and one claim-body line convention only (the PLAN-PROMPTS entry's Machinery admission field is removal-shaped).
- Single-home pointers: each pointer names the section it extends and never restates the pointed rule; the AUTHORING CLAIM duty paragraph is the one home of the parked-state line spec, its write arm, and the pickup read with its ordering; the Freeze rule is the one home of the provenance rule; the Phase 0 entry boundary carries the pickup pointer only.
- Pin safety: byte-payment trims avoid the pins suite's byte-exact and counted spans (scripts/check_maintenance_pins.sh); a trim-induced pin red resolves by re-trimming an unpinned span, never a pins-script edit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each pickup path's wording matches its real trigger (anchors verified in `decisions.md` duty (b), the template-authoring takeover arm, and the Phase 0 entry boundary), and the read-before-delete, premise-first, existence-check ordering is stated where each step lives
- consistency: wherever the parked-state line's facts appear, they match the convention home's current wording; pointers resolve, nothing restates
- anti-growth: the byte-budget gate stays blocking-clean; each file's net growth paid or under cap

**Done when:**
- all five files carry the convention with pointers resolving to the two homes (AUTHORING CLAIM duty; Freeze rule) and no conflicting or restating wording (collateral search shows only the landed convention's wording plus the entry's own scope text and the retained `plans-resume-marker` operation name)
- the validation commands pass at their pre-existing posture, any red triaged only when verifiably pre-existing on the base, the plan's own named baseline reds (Task 4) as their record of record, other reds named in the run record

**Ship when:**
- the next observed-exit quota-wall death in the wild leaves a readable parked-state record a pickup consumes; human-witnessed evidence, prose only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `agents/skills/maintenance/template-authoring.md` (Task 1)
- `agents/skills/plans/phase-0-placement.md` (Task 1)
- `agents/skills/maintenance/decisions.md` (Task 2)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 2)
- `agents/skills/plans/budget-gate.md` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above when causally related: a wording reconciliation in an adjacent section of the same five files, or a review-record correction.

**Out of scope; reject unless plan-related:**
- `scripts/done_sweep_gates_lib.py`; the claims-directory sweep retention is the sibling entry `authoring-claim-sweep-exemption-and-refresh-recipe`'s surface
- `docs/history/backlog/2026-11-10-paused-run-resume-first-duty.md`; the dispatch-lane resume-first sibling stays its own row
- `agents/skills/maintenance/state-file.md`; no scheduler-state schema change is in scope

## Validation Commands

```bash
python3 scripts/skill_text_budget.py --check
python3 scripts/fix_plan_em_dashes.py docs/history/plans/2026-11-13-frozen-authoring-claim-strandage.md
mise run test:required
bash scripts/check_maintenance_pins.sh
python3 scripts/check_prompt_log_origins.py --prune-audit --base "$(git merge-base main HEAD)"
bash scripts/scan-public-hygiene.sh
grep -qF "parked-state:" agents/skills/maintenance/template-authoring.md
grep -qF "premise re-derivation" agents/skills/maintenance/template-authoring.md
grep -qF '`unowned`' docs/history/backlog/PLAN-PROMPTS.md
grep -qF "parked-state" agents/skills/plans/budget-gate.md
grep -qF "clearance record carries a recorded parked-state path" agents/skills/maintenance/template-authoring.md
grep -qF "exactly one clearance record per entry" agents/skills/maintenance/decisions.md
rg -n "parked-state|parked state|resume[- ]marker" agents/skills docs/history/backlog/PLAN-PROMPTS.md
rg -n "four frontmatter lines" agents/skills
```

### Task 1: Convention home on the claim duty and the Phase 0 pickup pointer

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/plans/phase-0-placement.md`

- [x] Parked-state line spec in the AUTHORING CLAIM duty: given the duty's claim paragraph, expects the `parked-state:` body line beside the frontmatter field set (value: exactly one explicit-rooted path token or `none`, never cwd-relative or compound, resume notes staying in the parked state the line names, with both homes parked the token names the staged-review home; the five-line frontmatter spec scopes the frontmatter only; no second timestamp) [class: IMPLEMENTATION_REQUIRED]
- [x] Claim-line refresh mechanics: given the duty's claim paragraph, expects replace exactly that line in place, never rewriting the frontmatter, and the `updated:` refresh preserving body content [class: IMPLEMENTATION_REQUIRED]
- [x] Parked-state boundary arm, same duty: given a claim-owning session at an observed pause or exit boundary that leaves the claim standing, expects the `parked-state:` line written or refreshed inside the duty's ownership re-check while the session's id owns the claim, also at first parked-state directory creation; claim-deleting boundaries remove the line with the file [class: IMPLEMENTATION_REQUIRED]
- [x] Pickup read: given the claim lifecycle, every pickup path (fresh-dispatch availability walk, clearance-arm unfreeze, stale-foreign-claim takeover) reads the claim's parked-state line whenever the path fires, no age gate, an absent line reading as none; the read precedes any claim-deleting boundary, and the takeover's final pre-unlink identity read re-derives the read's value [class: IMPLEMENTATION_REQUIRED]
- [x] Pickup ordering: given the claim lifecycle, the ordering is stated once: premise re-derivation first, then the named parked-state path's existence check against its explicit-rooted location, then resume or recorded discard (authoring-side pickups; the discard-record sink is the run report or decision record) [class: IMPLEMENTATION_REQUIRED]
- [x] Pickup malformed-value branch: given the claim lifecycle, a value neither a parseable path nor `none`, or a path outside the parked-state homes (the resolved tmp tree or staging home), takes the recorded-discard branch, malformed value noted, no stop [class: IMPLEMENTATION_REQUIRED]
- [x] Pickup transaction wiring: given the claim lifecycle, a resume or recorded-discard branch runs only after the claim transaction completes, a takeover refused at the pre-unlink read voids the consumed value, a refused claim re-create after the unlink transfers the consumed value into the run report's raced-(b) record before the walk continues, and on resume completion the owning session refreshes the line to `none` or the surviving state in the same ownership re-check [class: IMPLEMENTATION_REQUIRED]
- [x] Resume extraction ordering: given the claim lifecycle, the recorded parked state is extracted out of any standing authoring worktree, its branch wip commits preserved or consumed, before any stale worktree or branch removal [class: IMPLEMENTATION_REQUIRED]
- [x] Pickup read's claim-absent branch: given the claim lifecycle, when the claim file is absent at a pickup path but the entry's clearance record carries a recorded parked-state path, that record is the read's value [class: IMPLEMENTATION_REQUIRED]
- [x] Payload-side mirror reconciled: given the payload-side mirror's compact duty set, expects by-reference deferrals of the parked-state write arm and the pickup read (beside the takeover sentence) to the convention home, and its frontmatter list reading the five-line shape (runtime_id included) [class: IMPLEMENTATION_REQUIRED]
- [x] Pickup pointer at the Phase 0 boundary: given the continuation-ownership paragraph, expects the boundary-listing pointer to the convention home's pickup clause, never restated [class: IMPLEMENTATION_REQUIRED]
- [x] Frontmatter-count drift reconciled: given phase-0-placement.md's "four frontmatter lines" wording, expects the five-line shape (runtime_id included) matching the procedure of record [class: IMPLEMENTATION_REQUIRED]
- [x] Byte payment: given the byte-budget gate over both files (baselines 51559/16737), expects blocking-clean with each insertion paired with a named same-file compression [class: REPOSITORY_TEST]
- [x] Commit: `docs: parked-state record on the claim duty and Phase 0 pickup pointer` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Provenance home and the maintenance pickup pointers

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`
- `agents/skills/maintenance/decisions.md`

- [x] Freeze rule self-freeze and mark legs: given the Standing rules Freeze rule bullet, expects one provenance clause with split legs: a claim owner's self-freeze names its own session id; duty (b)'s mark arm stays a sanctioned writer recording the observed claim's session id, or `unowned` when the claim file stands but names no parseable session line; duty (b)'s mark-clears clause stays the sanctioned remover with no recording duty, existing self-clear legs unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Freeze rule unowned witness slot: given the Standing rules Freeze rule bullet, an `unowned` mark's witness slot stays the claim path, the session-id parenthetical carrying `unowned` [class: IMPLEMENTATION_REQUIRED]
- [x] Freeze rule ad-hoc writer legs: given the Standing rules Freeze rule bullet's matching ad-hoc case, expects the provenance clause to scope its session-id legs to authoring-claim freezes, with the ad-hoc freeze writers (the ad-hoc arm's pre-landing freeze edits, duty (b)'s EXEC mark leg, duty (i)'s pre-landing PLAN-PROMPTS freeze) kept as sanctioned writers with their existing witness shapes [class: IMPLEMENTATION_REQUIRED]
- [x] Freeze rule claim-absent mark leg: given the Standing rules Freeze rule bullet's worktree/branch-witnessed trigger with no claim file standing, the mark records `unowned` with the live worktree or branch as its witness slot, sanctioned on that witness slot and `unowned` value [class: IMPLEMENTATION_REQUIRED]
- [x] Freeze rule takeover succession leg: given the Standing rules Freeze rule bullet, takeover succession (a mark naming the deposed predecessor) is legitimate until the entry's prune; no succession record is added, the investigable test reading only the live claim file per the investigable leg; plus the pointer to the parked-state convention home [class: IMPLEMENTATION_REQUIRED]
- [x] Freeze rule investigable leg: given the Standing rules Freeze rule bullet, the investigable class is a mark whose recorded session id matches neither the marked claim's own session id nor `unowned`; the test reads the live claim file only, while it stands, and is vacuous once the claim file's closeout deletes it (no post-closeout read surface) [class: IMPLEMENTATION_REQUIRED]
- [x] Monitor pickup pointer: given duty (b)'s mark-clears clause, expects one by-reference pointer to the convention home's pickup clause, never restating it, the monitor's disposition stated: the read informs the clearance decision, and the clearance's targeted log edit records the parked-state path (or none) as a durable entry-scoped clearance-record line (until replaced or the entry's prune), the sink the claim-absent pickup branch consumes [class: IMPLEMENTATION_REQUIRED]
- [x] Clearance-record replace semantics: given duty (b)'s mark-clears clause, the clearance edit leaves exactly one clearance record per entry, replacing any prior one, so the claim-absent branch's singular read is well-defined [class: IMPLEMENTATION_REQUIRED]
- [x] Frozen-entry residue handled by receipt, not edit: given the frozen entry's pre-redesign wording, expects no entry edit (the Freeze rule bars prompt rewrites); the supersession receipts in Assumptions and this landing's own entry prune with receipt resolve the residue [class: REPOSITORY_TEST]
- [x] Log write follows the Standing rules: given the PLAN-PROMPTS edit, expects a targeted section edit committed in the same turn under the log's write discipline, never a whole-file rewrite [class: REPOSITORY_TEST]
- [x] Byte payment: given the byte-budget gate over decisions.md (96 bytes of blocking headroom, advisory cap already breached), expects blocking-clean with same-file trims from restated fragments in the Rolling prompt log duties bullet, identified before the first edit, paying growth [class: REPOSITORY_TEST]
- [x] Commit: `docs: freeze-rule provenance home and monitor pickup pointer` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Budget pause writes the parked-state record

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/budget-gate.md`

- [x] Budget pause writes the record: given the pause boundary in the budget gate, expects the pause-path duty to write or refresh the claim's `parked-state:` line beside the pause record, by pointer to the convention home, with one disambiguating clause distinguishing the claim's parked-state record from the `plans-resume-marker` watcher operation named in the same file [class: IMPLEMENTATION_REQUIRED]
- [x] Budget mirror delta enumeration: given the Canonical home note's closed declared-delta list, expects the pause-path parked-state write added to that enumeration [class: IMPLEMENTATION_REQUIRED]
- [x] Byte payment: given the byte-budget gate over the file, expects blocking-clean [class: REPOSITORY_TEST]
- [x] Commit: `docs: budget pause writes the parked-state record` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Validation sweep and collateral reconciliation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/plans/phase-0-placement.md`
- `agents/skills/maintenance/decisions.md`
- `docs/history/backlog/PLAN-PROMPTS.md`
- `agents/skills/plans/budget-gate.md`

- [x] Run the validation commands: given the five touched files at final bytes, expects the byte-budget gate blocking-clean, the em-dash fixer reporting `total: 0 substitutions`, the required test suite `mise run test:required` at its recorded baseline posture (the deploy-runtime-helpers closure-gap failure is the known red at the base, timeout variance host-load), and the hygiene scan exit 0 [class: REPOSITORY_TEST]
- [x] Triage the pins suite and prune audit: given their runs at final bytes, expects their pre-existing posture with any red triaged only when verifiably pre-existing on the base against the machinery inventory's known-red record, and the frontmatter-count grep showing the reconciled phase-0 hit gone with the templates-CHANGELOG historical execution-claim record remaining untouched [class: REPOSITORY_TEST]
- [x] Collateral search expected residue: given a search for parked-state, parked state, and resume marker across the skill tree and PLAN-PROMPTS.md, expects only the landed convention's wording; the frozen entry's own text is expected residue until this landing prunes it (receipts in Assumptions), and the `plans-resume-marker` watcher operation's name in budget-gate.md is expected residue the Task 3 disambiguation clause retains [class: REPOSITORY_TEST]
- [x] Collateral reconciliation: given the collateral search at final bytes, any stale restatement outside the expected residue reconciled or removed in the same change [class: REPOSITORY_TEST]
- [x] Commit: `docs: validation sweep for the parked-state convention` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-11-frozen-authoring-claim-strandage.md: deleted in this completion pass; the covering archived plan (this file) landed its full scope (parked-state convention home on the AUTHORING CLAIM duty, Phase 0 pickup pointer, Freeze-rule provenance, monitor clearance-record semantics, budget-gate pause-path write) through the executing run's squash landing from branch 2026-11-19-frozen-authoring-claim-strandage (pre-squash tip 9d8f02ea45d8d641cf71a9795aa78956a354f2c8).
