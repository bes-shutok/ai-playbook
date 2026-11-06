# Plan: learn capture-freshness re-probe arm

Backlog origins (scope of record):
- docs/history/backlog/2026-11-05-learn-capture-freshness-reprobe.md
Driving force: efficiency
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-learn-capture-freshness-reprobe-p26df9d27-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 0.75h
Authoring claim: 2026-11-05-learn-capture-freshness-reprobe.md (session sess_2ef2f7d4-cfc2-4dac-8d4b-fde95273bf35)
Executed: yes (6694daa6f)

Design input (prose only, never a Backlog origin): the PLAN-PROMPTS entry `learn-capture-freshness-reprobe` in docs/history/backlog/PLAN-PROMPTS.md, which routes this item and contributed the scope bound and the rejected-alternative set.

## Terms

- Run's own capture artifacts: the skills-corpus backlog rows and rolling-log entries this learn run authored, identified from the run's own `committed:` receipts and the enclosing boundary's `task_boundary:` manifest rows; never artifacts some other run or session authored.
- Re-probe: the completion-checklist arm that re-reads those artifacts against the run's current evidence set before capture is reported complete.
- Dated extension: an appended line carrying its own date on an existing row or entry, recording what the earlier capture missed; never a silent rewrite of the original text.
- None-found note: the one-line clean-run record stating the re-probe ran over the run's artifacts and found nothing to extend or add.

## Why

During the 2026-11-04 parallel fleet, capture passes ran once per boundary and were repeatedly amended the same evening by the same or a peer session: a PLAN-PROMPTS entry amended at 18:50Z to cite landing lessons its emission missed (65c0ef5f3), two backlog rows extended at 21:21Z with evidence the earlier capture missed (e4fcf1a87), and a new row filed at 21:38Z for a gap the earlier captures missed entirely (a35cf8fc7). Two of the three corrections came from the session whose own earlier captures they extend. The capture contract has no freshness re-probe: artifacts written early in a multi-boundary run go stale as the run's own evidence grows, every stale capture risks a parallel session acting on incomplete evidence, and each correction is priced as a separate pass. learn's Step 1.8 self-omission rule already names the defect class (an omission by the capture pass is its own candidate); the missing piece is the mechanical moment that re-opens the run's own early captures before the run claims capture complete.

## Gist & Examples

TLDR: learn's completion checklist gains a capture-freshness re-probe arm that re-reads the run's own earlier capture artifacts against the run's current evidence set before capture is reported complete, landing dated extensions or the missed row itself, so stale early captures are corrected inside the owning run instead of arriving as separate same-day amendment passes, naming efficiency as the driving force.

Before (today): each capture boundary writes its rows and entries once; nothing re-reads them later in the run; the 2026-11-04 evening's three corrections arrive as three separate commits from whichever session notices, one of them a whole missed row.

After (this plan): the learn run that spans two or more capture boundaries ends with the re-probe: it enumerates its own artifacts from its receipts, re-reads each against the run's final evidence set, lands dated extensions or the missed row through the existing Step 1.8 and 1.9 discipline, and records the none-found note when clean.

Example: a run captures an EXEC entry at its second boundary; its fourth boundary lands a fix whose lessons apply to that entry; at completion the re-probe re-reads the entry against the now-known landing lessons and appends the dated citation itself, instead of a later session filing the amendment as a separate pass.

Edge cases: a single-boundary run has no earlier artifact to re-probe and records nothing; a run whose artifacts were extended by a peer mid-run re-reads the peer-extended bytes and judges the current text, never reverting a peer's line; the re-probe never modifies artifacts this run did not author (read-only bound); an artifact whose committed receipt cannot be resolved is reported as unverifiable rather than silently skipped.

## Outcome

A multi-boundary run's capture artifacts are current with the run's own final evidence when the run reports capture complete, witnessed by dated extensions or a none-found note in the run output.

- Gate delta: none (no gate, validator, lock, ledger, or fence added or removed; the re-probe is checklist duty text whose only record is the none-found note in the run output, per the origin row's admission posture and the Machinery admission protocol).

- Stale-capture corrections land inside the owning run at its own completion boundary.
- Parallel sessions read complete evidence instead of filing the missed pieces themselves.

## Assumptions

- assume the arm's home is learn's completion checklist (agents/skills/learn/step-completion.md) rather than the execute-plan light-boundary text; basis: the checklist is the one completion surface every learn invocation passes (per-task light boundaries, closeout learn, maintenance harvest learn), the boundary contracts delegate learn behavior to learn instead of restating it, and a checklist arm reaches every consumer without per-consumer edits; the simpler-design comparison favored one learn-side surface over N consumer-side edits.
- assume the arm is duty text with no validator, gate, or ledger; basis: the three witnessed corrections were caught same-day by diligence passes at zero added-gate cost, so no machinery-shaped catch exists and the repository's Machinery admission protocol prices the validator arm as rejected (missing incident); the origin row and the routing entry record the same rejection.
- assume the run's artifact identity is derivable from records learn already emits (the `committed:` receipts and `task_boundary:` rows); basis: Step 1.8's commit rule already mandates the receipts, so the arm adds no new bookkeeping surface.

Decision points requiring a grill: none remain (the placement and machinery questions are resolved by the recorded simpler-design comparison and admission rejection above, under the maintenance-selected standing authorization).

## Standing constraints

- No new gate, validator, ledger, or required ceremony; the arm is checklist duty text and the none-found note is its read-only fallback record.
- Scope bound: the re-probe reads and extends only artifacts this run authored; it never sweeps the corpus, never touches another run's or session's artifacts, and never reverts a peer's line.
- Skill-text anti-growth: the arm's text is the change's entire growth; it cites Step 1.8's self-omission rule by reference and never restates it, and no existing checklist bullet is superseded or duplicated.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the re-probe enumerates exactly the artifacts the run's own receipts name and judges them against evidence the run itself holds
- portability: the arm reads as skill text without knowing which project, runtime, or boundary kind invoked learn
- simplicity: one checklist bullet plus one mechanics block; no new state, no new file, no consumer-side edits

**Done when:**
- agents/skills/learn/step-completion.md carries the re-probe bullet and its mechanics block with the scope, evidence-set, action, and read-only bounds stated
- the public hygiene scan and the pins suite exit 0

**Ship when:**
- a follow-up multi-boundary run shows the arm executed at least once with a dated extension or a none-found note (the origin row's own ship-when; post-landing observation, not a plan task)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Docs:**
- `agents/skills/learn/step-completion.md` (Task 1)

**Tests:**
- none planned; validation is the Validation Commands block's pinned set (the hygiene scan, the pins suite, the machinery inventory check); the arm is prose workflow text with no executable unit to test in this repository

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/learn/step-1-extract.md`; reason: Step 1.8's self-omission rule is the arm's named sibling, not its target, and stays unchanged
- `agents/skills/execute-plan/` including the light-boundary text; reason: the boundary contract delegates learn behavior to learn, and a consumer-side edit duplicates the checklist arm
- any validator, gate, or registry entry enforcing the re-probe; reason: the machinery-shaped arm is rejected on the admission protocol (no witnessed escaped miss; the three witnesses were same-day diligence catches)

## Validation Commands

Authoring preflight on 2026-11-06: the pre-round gate ran over the drafted bytes before the first review round (python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-06-learn-capture-freshness-reprobe.md), failed once on a single over-cap task item (r1 F1), and passed after the split fold; the re-run before the second round exited 0 with OUTCOME: pass. The pre-review sweep ran the hygiene scan (exit 0), the pins suite (exit 0), and the machinery inventory check (exit 1 on scripts/maintenance_fire_outcomes.py, a pre-existing unregistered script from commit 833e4c7d3 predating this plan; report-only per the Note below). Rule 22 audit: this is a docs-only single-surface plan; no literal-insertion or negative-grep simulation applies, and the em-dash changed-line scan covered the draft and fold commits. This validation preamble owns command purpose; measured execution results live in the run's execution evidence, not in plan review-state prose.

```bash
# Run every command from the target repository root.
bash scripts/scan-public-hygiene.sh
bash scripts/check_maintenance_pins.sh
python3 scripts/machinery_inventory.py --check
```

Note: the machinery inventory check reads registry state that is independent of this plan's own files; a failure naming an unrelated unregistered script is a pre-existing corpus finding to report, not this plan's regression to fix.

## Tasks

### Task 1: capture-freshness re-probe arm in learn's completion checklist

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/learn/step-completion.md`

- [x] Add one checklist bullet: before a multi-boundary run reports capture complete, the re-probe arm re-reads the run's own earlier capture artifacts against the run's current evidence set and lands dated extensions, the missed row, or the none-found note [class: IMPLEMENTATION_REQUIRED]
- [x] Add the mechanics block beside the checklist defining the arm's scope and inputs: a multi-boundary run spans two or more capture boundaries; the re-probe's artifacts are exactly those the run's own `committed:` receipts and `task_boundary:` manifest rows name; the evidence set is the run's current final state [class: IMPLEMENTATION_REQUIRED]
- [x] Add the mechanics block's action and bound sentences: the actions are a dated extension on an existing artifact, the missed row filed through the existing Step 1.8 and 1.9 discipline, or the none-found note recorded in the run output when clean; the re-probe is read-only over artifacts the run did not author and never reverts a peer's line; an artifact whose receipt cannot be resolved is reported unverifiable, never silently skipped [class: IMPLEMENTATION_REQUIRED]
- [x] Pay for growth: the arm's text cites Step 1.8's self-omission rule by reference instead of restating it, supersedes no existing bullet, and is the change's entire byte growth; verify the edited file carries no duplicated rule text against agents/skills/learn/step-1-extract.md [class: IMPLEMENTATION_REQUIRED]
- [x] Run the Validation Commands block's pinned set from the repository root, expecting the hygiene scan and the pins suite to exit 0 and recording the machinery inventory check's outcome as report-only [class: REPOSITORY_TEST]
- [x] Commit: `docs: add capture-freshness re-probe arm to learn completion checklist` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-05-learn-capture-freshness-reprobe.md: covered by this plan's execution landing (origin row flipped covered at 159c21ef4 and deleted through the completion fold in the same landing change; the durable witness is this completed plan).
