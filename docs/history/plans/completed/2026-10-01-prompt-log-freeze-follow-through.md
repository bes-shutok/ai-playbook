# Plan: Prompt-log freeze rule follow-through

Backlog origin: `docs/history/backlog/2026-09-29-prompt-log-freeze-rule-follow-through.md`
Driving force: correctness
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-prompt-log-freeze-follow-through-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The prompt-log freeze rule's four consumer-side residues close: the investigate consumer line names freeze, in-session log-entry authoring freezes its own entry at start, the freeze predicate carries the corpus's freshness bound, and the rule text carries a regression pin.

- investigate's Integration Points consumer line reads "read, prune, freeze, and dispatch duties", matching the maintenance side's actual duty list.
- When the monitor's dispatch duty authors a log entry in-session, the run writes that entry's `Frozen:` line as its first log write (witness: its own slug-keyed claim file), so a concurrent session never reads the entry as dispatchable mid-authoring.
- "Live" in the freeze predicate means the claim's `updated:` fresher than one cadence period per the `G1a` discovery arm's bound; a stale claim routes through the existing claim takeover rule instead of freezing.
- A pins-suite presence pin fails when the duty (b) freeze clause disappears from the maintenance skill.

Gate delta: two checked conditions added to existing surfaces (the in-session self-freeze write at authoring start; the freshness bound gating the freeze predicate) plus one Integration Points wording fold and one presence pin; no refusal surface is removed, and the freshness bound narrows nothing (a stale claim already could not be frozen forever - it now takes the documented takeover path instead of an undefined one).

## Terms

- Freeze rule: the rolling prompt log's standing rule (`docs/history/backlog/PLAN-PROMPTS.md` header) plus its maintenance-side restatement in duty (b).
- Self-freeze: the in-session authoring run writing its own entry's `Frozen:` line at start, witnessed by its own claim file.
- Freshness bound: the one-cadence-period claim freshness the `G1a` discovery arm already uses; a stale claim takes the takeover path, not the freeze.

## Assumptions

- plans/execute-plan surfaces need no edit: the freeze rule's consumers are exactly investigate and maintenance (the origin's corpus sweep; re-verified this cycle). (Basis: the origin's source-reference sweep.)
- The pins suite holds no existing needle over the duty (b) freeze clause, so the new presence pin lands without re-keying. (Basis: the pins sweep, zero hits, this cycle.)
- The freeze-literal convention (corrected claims, not absence) governs the new pin's comment. (Basis: the pins suite's freeze-literal discipline comments.)
- The rule exercise arm (fresh claim freezes and never dispatches, abort unfreezes, landed plan prunes) is a recorded procedure exercise in the task log, not a script: the surfaces are prose rules in a tracked log and skill text, and the execute-plan anti-pattern table forbids scratch harnesses for Markdown-only plans. (Basis: the anti-pattern table row.)

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: The freeze rule's consumer surfaces catch up to the landed rule - investigate names freeze, in-session authoring self-freezes its entry, "live" gains the one-cadence bound, and a pin guards the clause; force: correctness.

When the freeze rule landed, the maintenance side was amended and the investigate side was not: its consumer line still enumerates "read, prune, and dispatch". And when the monitor authors a log entry in-session, nothing freezes that entry during its own authoring - a concurrent session reads it as dispatchable until it runs its own claim check. This plan closes both, adds the freshness bound the predicate left to inference (live = the claim's `updated:` inside one cadence period; stale takes the takeover path), and pins the duty (b) freeze clause so a wholesale duties rewrite cannot silently drop freeze.

## Evaluation Criteria

**Quality dimensions:**
- Consistency: each side's claim matches the other's actual duties (the bidirectional-integration rule); the freshness bound matches the `G1a` discovery arm's existing convention.
- Minimality: wording-level edits plus one pin; no new state fields, no schema change, no new refusal surface.
- Guard coverage: the new pin fails when the duty (b) freeze clause disappears.

**Done when:**
- Every Validation Commands line exits 0, and the rule exercise is recorded in the task log.

**Ship when:**
- The next in-session log-entry authoring freezes its entry at start (operator-observed; external condition, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/investigate/SKILL.md`
- `agents/skills/maintenance/SKILL.md`
- `docs/history/backlog/PLAN-PROMPTS.md` (the log's standing-rules header only)
- `scripts/check_maintenance_pins.sh`

**Tests:**
- none; verification is the grep canaries, the pins suite, and the recorded rule exercise.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the queue-depth token's counting semantics; reason: it already reads the freeze rule and inherits these edits unchanged.
- the payload templates; reason: log-blind by design (duty (c)'s own sentence).

## Validation Commands

```bash
grep -q "read, prune, freeze, and dispatch duties" agents/skills/investigate/SKILL.md || { echo FAIL: consumer line; exit 1; }
[ "$(grep -c 'read, prune, and dispatch duties' agents/skills/investigate/SKILL.md)" -eq 0 ] || { echo FAIL: stale enumeration; exit 1; }
grep -q "writes the entry's \`Frozen:\` line as its first log write" agents/skills/maintenance/SKILL.md || { echo FAIL: self-freeze duty; exit 1; }
grep -q "witnessed by its own slug-keyed claim file" agents/skills/maintenance/SKILL.md || { echo FAIL: self-freeze witness; exit 1; }
grep -q "stale claim taking the takeover path instead of freezing" docs/history/backlog/PLAN-PROMPTS.md || { echo FAIL: log freshness bound; exit 1; }
grep -q "a stale claim taking the takeover path instead of freezing" agents/skills/maintenance/SKILL.md || { echo FAIL: duty freshness bound; exit 1; }
grep -c "marks any entry whose authoring has started" scripts/check_maintenance_pins.sh | grep -q -v "^0$" || { echo FAIL: freeze clause pin; exit 1; }
bash scripts/check_maintenance_pins.sh || { echo FAIL: pins suite; exit 1; }
bash scripts/check-no-em-dash.sh file agents/skills/investigate/SKILL.md agents/skills/maintenance/SKILL.md docs/history/backlog/PLAN-PROMPTS.md scripts/check_maintenance_pins.sh docs/history/plans/2026-10-01-prompt-log-freeze-follow-through.md || { echo FAIL: em-dash; exit 1; }
bash scripts/scan-public-hygiene.sh --files docs/history/backlog/PLAN-PROMPTS.md || { echo FAIL: hygiene log; exit 1; }
python3 scripts/check_investigate_entries.py || { echo FAIL: investigate checker; exit 1; }
```

### Task 1: investigate's consumer line names freeze

Files:
- `agents/skills/investigate/SKILL.md`

Evidence:
- `grep -q "read, prune, freeze, and dispatch duties" agents/skills/investigate/SKILL.md`; covers the fold
- `[ "$(grep -c 'read, prune, and dispatch duties' agents/skills/investigate/SKILL.md)" -eq 0 ]`; covers the stale enumeration gone

- [x] Run → expect RED: `grep -c "freeze, and dispatch" agents/skills/investigate/SKILL.md` returns 0 [class: REPOSITORY_TEST]
- [x] In the Integration Points row's first sentence, replace `reads the emitted entries for its read, prune, and dispatch duties` with `reads the emitted entries for its read, prune, freeze, and dispatch duties` keeping everything else unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence commands [class: REPOSITORY_TEST]
- [x] Commit: `skills: investigate consumer line names the freeze duty` [class: IMPLEMENTATION_REQUIRED]

### Task 2: the freshness bound in the freeze rule, both surfaces

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -q "stale claim taking the takeover path instead of freezing" docs/history/backlog/PLAN-PROMPTS.md`; covers the log restatement
- `grep -q "a stale claim taking the takeover path instead of freezing" agents/skills/maintenance/SKILL.md`; covers the duty restatement (two single-path lines: a dual-path grep -q is OR-semantics and would pass on either file alone)

- [x] Run → expect RED: `grep -c "takeover path instead of freezing" docs/history/backlog/PLAN-PROMPTS.md` returns 0 [class: REPOSITORY_TEST]
- [x] In the log's freeze rule (the standing-rules header), extend the live-claim parenthetical: after `a live authoring claim file keyed to the entry slug or one of its origins under the tmp authoring-claims directory` insert `, live meaning its `updated:` fresher than one cadence period per the `G1a` discovery arm's bound (a stale claim taking the takeover path instead of freezing)` keeping the worktree/branch alternative and the rest of the rule unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] In maintenance duty (b), extend the freeze clause's live-claim parenthetical with the same gloss in its shorter form: `live per the log's freshness bound (a stale claim taking the takeover path instead of freezing)` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence command; both files em-dash clean [class: REPOSITORY_TEST]
- [x] Commit: `backlog: freeze rule names the one-cadence freshness bound` [class: IMPLEMENTATION_REQUIRED]

### Task 3: in-session authoring self-freezes its entry

Files:
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -q "writes the entry's \`Frozen:\` line as its first log write" agents/skills/maintenance/SKILL.md`; covers the self-freeze arm
- `grep -q "witnessed by its own slug-keyed claim file" agents/skills/maintenance/SKILL.md`; covers the witness naming

- [x] Run → expect RED: `grep -c "self-freeze" agents/skills/maintenance/SKILL.md` returns 0 [class: REPOSITORY_TEST]
- [x] In duty (d) machinery mapping, after the claim-file keying sentence, insert: `Self-freeze: the in-session authoring writes the entry's \`Frozen:\` line as its first log write, witnessed by its own slug-keyed claim file, before any plan work (mirroring duty (b)'s mark duty; the mark clears per the log's rule when the authoring aborts without a plan file in the plans root), so a concurrent session never reads the entry as dispatchable mid-authoring` [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence commands [class: REPOSITORY_TEST]
- [x] Commit: `skills: in-session log-entry authoring self-freezes its entry` [class: IMPLEMENTATION_REQUIRED]

### Task 4: the regression pin and the recorded rule exercise

Files:
- `scripts/check_maintenance_pins.sh`

Evidence:
- `grep -c "marks any entry whose authoring has started" scripts/check_maintenance_pins.sh`; covers the presence pin landed
- the recorded exercise in the task log; covers the rule exercise arm

- [x] Run → expect RED: the Evidence grep returns 0 [class: REPOSITORY_TEST]
- [x] Add one presence pin inside the pins suite's mechanical-gates wiring block, after its `$MS` definition line (inserting before the variable definitions would crash the suite under `set -u` rather than failing as a pin): `pin "duty (b) freeze clause wired" grep -qF 'marks any entry whose authoring has started' "$MS"` with a comment naming this plan as the provenance (the freeze-literal convention: the needle is the operative sentence, corrected claims not absence) [class: IMPLEMENTATION_REQUIRED]
- [x] Record the rule exercise in the task log: walked against a simulated fresh claim (the entry freezes at duty (b) or self-freezes at duty (d), is never a dispatch candidate, and unfreezes on abort without a plan file) and against a landed plan (the prune still fires and the entry leaves the queue-depth token), with the p89 live freeze as the witnessed instance [class: REPOSITORY_TEST]
- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `pins: duty (b) freeze clause presence pin` [class: IMPLEMENTATION_REQUIRED]
