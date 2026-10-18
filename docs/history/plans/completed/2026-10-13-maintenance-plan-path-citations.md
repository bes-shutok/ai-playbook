# Plan: maintenance-plan-path-citations

| Field | Value |
| --- | --- |
| Date | 2026-10-13 |
| Dispatch entry | PLAN-PROMPTS `maintenance-plan-path-citations` (frozen cd2aa1e3f) |
| Origin | docs/history/backlog/2026-10-08-maintenance-plan-path-citations-stale-after-archive.md |
| Work type | Citation string refresh across four live surfaces; no behavior change |
| Authoring session | sess_5c51c846 (worktree 2026-10-13-mpc-authoring) |
| Review budget | At most 2 review rounds within 2 hours (D-8); delta rounds do not consume the budget |

## Terms

- Archived plan: a plan file moved under docs/history/plans/completed/ after execution. The move for this plan's target was the pure rename fa6c03350, which changed zero references.
- Live surface: any tracked file a runtime or agent loads outside docs/history/ (skill modules, scripts, registries). Historical records under docs/history/ keep citing pre-archive paths as historical context and are not live surfaces.
- Provenance comment: a pins-suite comment naming the plan and task a pin row was registered from. It carries no checked span and no expected literal.

## Why

The pure-rename archive fa6c03350 moved docs/history/plans/2026-10-06-two-mode-loop-policy.md to docs/history/plans/completed/2026-10-06-two-mode-loop-policy.md with zero reference updates. The pre-archive path fails `git cat-file -e` at tip while the completed/ twin resolves, and nine live-surface citation sites still name the dead path. The dispatch entry's site inventory (2026-10-08) named the sites at their then homes in agents/skills/maintenance/SKILL.md; the 2026-10-10 maintenance-skill-size-refactor since extracted those regions (the Ad-hoc backlog arm bullet into decisions.md, the Revisions lines into CHANGELOG.md), and one same-witness registry note was not in the 2026-10-08 inventory. This plan binds the defect (dangling citations of the fa6c03350 archive), not the 2026-10-08 file layout; the site inventory below is re-derived at main f0fa4199a.

## Site inventory (the whole change set)

1. scripts/check_maintenance_pins.sh: four provenance comments (authoring-time lines 601, 2866, 2897, 2949). Comment-only hits: no pin literal or expected span in the suite contains the old path (verified by search: the suite's only occurrences of the path are these comments).
2. agents/skills/maintenance/decisions.md: the Ad-hoc backlog arm bullet's eligibility-test source citation (authoring-time line 29, the plan path stated once there).
3. agents/skills/maintenance/CHANGELOG.md: the two Revisions-ledger entries dated 2026-10-08 citing the plan as witness.
4. scripts/machinery_registry.json: the state-field:loop_mode removals record cites the plan as witness twice, in the note prose (authoring-time line 1582) and in the structured witness ref (authoring-time line 1587, class user-decision). The note is prose inside a JSON string value; the witness ref sits in the delete-disposition row's witness object. The machinery inventory gate is deeply red at base for unrelated reasons (dangling witnesses of other archived plans, unregistered-script regrowth) and resolves witness refs only for keep-disposition rows, so neither occurrence is gate-checked today; the file must stay valid JSON.

## Non-goals

- scripts/check_maintenance_pins.sh also carries a provenance comment citing docs/history/plans/2026-10-06-plans-egress-coverage.md, a different plan also dangling at tip whose completed/ twin resolves; it was stranded by a different archive commit, not fa6c03350, so it is outside this entry's prompt. It is witnessed here for a follow-up row, not folded in.
- No archive-time reference-refresh check: rejected in the dispatch entry (a new duty on the guard-bearing archive step ahead of a second witness).
- No history-record rewrites and no operative-rule, span, or pin-literal changes of any kind.

## Task 1: refresh the nine citation sites to the completed/ twin

- [x] Refresh the four two-mode-loop-policy provenance comments in scripts/check_maintenance_pins.sh (authoring-time lines 601, 2866, 2897, 2949) to cite docs/history/plans/completed/2026-10-06-two-mode-loop-policy.md; comment bytes only: no pin literal, expected span, or checked-file list changes. [class: IMPLEMENTATION_REQUIRED]
- [x] Refresh the eligibility-test source citation in agents/skills/maintenance/decisions.md (the Ad-hoc backlog arm bullet, the plan path stated once there, authoring-time line 29) to the completed/ twin; body text only, the module's headings stay byte-verbatim. [class: IMPLEMENTATION_REQUIRED]
- [x] Refresh the two Revisions-ledger entries in agents/skills/maintenance/CHANGELOG.md (the 2026-10-08 two-mode loop policy lines) to cite docs/history/plans/completed/2026-10-06-two-mode-loop-policy.md. [class: IMPLEMENTATION_REQUIRED]
- [x] Refresh the state-field:loop_mode removals record in scripts/machinery_registry.json to the completed/ twin at both occurrences: the note prose (authoring-time line 1582) and the witness ref (authoring-time line 1587); the file must stay valid JSON (python3.14 json.load passes). [class: IMPLEMENTATION_REQUIRED]
- [x] Pins battery: run bash scripts/check_maintenance_pins.sh at the working tree and compare its PIN FAIL name set with a base run at the merge base (21 failures at authoring time, none over the touched files or spans): the two sets must be identical; any new or vanished failure is a foldable result. [class: REPOSITORY_TEST]
- [x] Scans: bash scripts/check-no-em-dash.sh file over the four touched files exits 0, and the public hygiene scan (user facts key public_hygiene_scan_script) exits 0. [class: REPOSITORY_TEST]
- [x] Zero-residue census: a repo-wide search for the byte string plans/2026-10-06-two-mode-loop-policy.md across tracked files with docs/history/ excluded returns no file. [class: REPOSITORY_TEST]
- [x] Target resolution: git cat-file -e HEAD:docs/history/plans/completed/2026-10-06-two-mode-loop-policy.md exits 0 at the working tree. [class: REPOSITORY_TEST]

## Assumptions

- assume the site inventory drift is a discovery duty: the dispatch entry named SKILL.md homes that the 2026-10-10 skill-size refactor has since extracted; this plan binds the defect (dangling fa6c03350 citations on live surfaces), not the 2026-10-08 file layout; basis: the re-derived inventory in this plan over main f0fa4199a.
- assume the machinery inventory gate stays out of the battery: its base failures are pre-existing and unrelated (dangling witnesses of other archived plans, unregistered-script regrowth), and it resolves witness refs only for keep-disposition rows, so the touched delete row's note and ref are not gate-checked; this plan neither pins it as a gate nor repairs it; basis: `python3.14 scripts/machinery_inventory.py --check` red at base with no failure naming the two-mode row (r1 re-run).
- assume the pins suite's 21 base failures stay reported, never repaired: they are the recorded pre-existing peer-owned red set at the 2026-10-13 tips; the battery's equality criterion scopes the gate to touched spans per the standing constraint; basis: the base run in this worktree at cd2aa1e3f (21 PIN FAIL lines).
- assume the dispatch entry's third validator ("the entries checker") is dropped with this recorded reason: the repo's entries checkers at tip (scripts/check_investigate_entries.py and the backlog placement checkers) validate investigate entries and backlog row placement, surfaces this plan does not touch, and no entries checker reads pins provenance comments or the four touched files; basis: the checker inventory re-derived at f0fa4199a.

Decision points requiring a grill: none remain.

## Standing constraints

- Plan scripts and validators run under `python3.14`; all commands stay repo-relative with no machine-specific absolute paths, and nothing in this plan authorizes a push to origin.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_maintenance_pins.sh` (the four provenance comment lines only)
- `scripts/machinery_registry.json` (the state-field:loop_mode removals record's note and witness ref only)

**Documentation:**
- `agents/skills/maintenance/decisions.md` (the Ad-hoc backlog arm bullet's citation only)
- `agents/skills/maintenance/CHANGELOG.md` (the two 2026-10-08 Revisions-ledger lines only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. The landing's own riders (the frozen entry's prune line, the PLAN-PROMPTS-PRUNE receipt) ride the landing branch per the log charter. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the plans-egress-coverage provenance comment and any other archived plan's citations; reason: different archive commit, outside the fa6c03350 defect this entry dispatches (Non-goals).
- docs/history/ records; reason: historical context keeps pre-archive citations (Terms).
- the machinery inventory gate and its registry rows beyond the touched note; reason: Assumption 2.
- the 21 pre-existing pins failures' spans; reason: Assumption 3, reported never repaired.
