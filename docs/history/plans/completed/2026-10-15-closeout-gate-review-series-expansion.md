# Plan: closeout-gate review-series citation expansion

Backlog origins (scope of record):

Driving force: code-quality
(the plans-skill closed taxonomy has no reliability entry; both origin rows name reliability of the teardown path, which is code-quality here - the closeout gate stops false-refusing verified-present records.)

Plan review record: the staging series .ai-playbook/reviews/2026-10-15-plan-review-closeout-gate-review-series-expansion-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.5h total, largest task 1.0h

## Terms

- series token: a `Plan review record:`/`Plan review:` label citation whose basename carries `-r*.md`; `_extract_citations` routes it to the series arm (scripts/worktree_closeout_migrate.py).
- series expansion: `_series_members(home, token, resolved_only)` matching home entries against the token's basename; the round group `-r(\d+)\.md` and the `$` anchor are fixed; the segments around the split are today escaped verbatim, which is the false-refusal surface.
- placeholder form: the plans template's literal `YYYY-MM-DD` inside the prefix (agents/skills/plans/SKILL.md plan template line).
- wildcard form: a literal `*` segment in the prefix, the date-agnostic citation adopted so rounds crossing midnight stay discoverable (adoption witnessed by the machinery-script-refactor-program series; refusal witnesses in the wildcard origin row).
- resolved-only containment: unchanged gate-removal filter - a member counts only when its filesystem-resolved path is a regular file still under the home.
- zero-member refusal: a series whose expansion matches no home entry stays a missing record naming the token; the empty-owned-set refusal is untouched.

## Why

The gate false-refuses teardown for plans whose header cites the template's placeholder form or the adopted wildcard form while every member record is present and digest-verified in the primary reviews home. Five teardowns proceeded through bounded-repair skip-with-report workarounds (the origin rows hold the witness narrative and dates). The expander owns the failed behavior.

## Gist & Examples

TLDR: the closeout gate's series matcher learns the two witnessed citation forms, so teardowns verify present records instead of false-refusing them - code-quality, the teardown path stops refusing its own evidence.

Before: a landed plan citing `YYYY-MM-DD-plan-review-<slug>-r*.md` (the template form) or `*-plan-review-<slug>-r*.md` (the midnight-crossing form) is refused by `gate-removal` even with every member digest-verified under the primary reviews home; the teardown falls back to skip-with-report.

After: both forms expand; `gate-removal` and `verify-records` pass on truly-present series and refuse absent ones; a concrete-date citation still matches only that date.

## Outcome

Series citations in the placeholder and wildcard forms verify against the reviews home like concrete dates do, without weakening any refusal.

- `gate-removal` and `verify-records` pass when the cited series is truly present and refuse when it is not, in both forms.
- Concrete-date citations stay exact; resolved-only containment and the zero-member and empty-owned-set refusals are byte-identical.
- The plans template documents the accepted forms in one sentence at the Plan review record line.

Gate delta: none - the change removes false refusals from an existing gate (fix-class origin-cited; the rows record the alternatives and why each fails), adds no refusal class, hard gate, fence, protocol layer, or schema field, and no task pauses dispatch or later work.

## Assumptions

- The expansion change is confined to `_series_members`' pattern construction; both consumers (gate-removal series arm, verify-records) inherit it through the existing call sites; basis: the two call sites at scripts/worktree_closeout_migrate.py lines 590 and 1012.
- plan_readiness's own round discovery is a different surface and is not rewired to the translator; no witnessed miss routes through it; basis: the wildcard row's Fix shape naming `_series_members` only.
- The suite runs under `$HOME/.agents/venvs/ai-playbook-test/bin/python3 -m pytest` when present; basis: suite precedent in prior plan validations.
- Task 3's one-sentence template addition is the smallest growth that documents a real behavior change at its existing home (the Plan review record line, whose predicate absorbs the case); no deletion pairs with it because no existing sentence is superseded; no second documentation surface is added.
- The concrete-date prefix stays the preferred authoring form; the gate's wildcard acceptance serves already-landed and midnight-crossing series; the template sentence documents acceptance, not authoring endorsement; basis: the wildcard row's fifth-witness remedy.
- Review-layer execution duty: the executor runs the Validation Commands battery before landing; this restates Task 4's acceptance items and existing execute-plan law, so no separate blocking-duty declaration is made.

Decision points requiring a grill: none remain: the dispatching PLAN-PROMPTS entry is the confirmed design (operator-directed investigate pass, rejected alternatives recorded 2026-10-14); the taken arm is the expander widening, with the entry's other arms rejected - removing gate-removal (closes a witnessed artifact-loss gate), narrowing citations to concrete dates (breaks midnight-crossing rounds), author-side placeholder replacement with wildcards dropped (template churn that leaves landed plans false-refusing), and a separate citation-form validator (new machinery with no witnessed incident)

## Standing constraints

- Never push to origin; stage by explicit path only; never amend a commit reachable from main.
- The hygiene scan (exit 0) runs before every commit; no em-dashes and no absolute personal home directory paths in committed files.
- Bounded repair only: never edit a gate or validator mid-lane to unblock the lane.

## Evaluation Criteria

**Quality dimensions:**
- correctness: both citation forms verify present series and refuse absent ones in gate-removal and verify-records.
- safety: resolved-only containment refuses a member whose resolved path leaves the home, in both new forms.
- simplicity: one translator helper, one match-pattern construction, no second expansion surface.

**Done when:**
- the Validation Commands battery exits 0 and the new fixtures cover both forms plus the exactness, containment, and zero-member controls.

**Ship when:**
- the landing carries the plan, fixtures, template sentence, and the origin disposition; no deployed-environment condition remains.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/worktree_closeout_migrate.py`

**Tests:**
- `scripts/test_worktree_closeout_migrate.py`

**Documentation:**
- `agents/skills/plans/SKILL.md`

**Backlog disposition:**
- `docs/history/backlog/2026-10-08-gate-removal-placeholder-citation.md` *(deleted in the landing change)*
- `docs/history/backlog/2026-10-14-worktree-closeout-gate-wildcard-citation.md` *(deleted in the landing change)*
- `docs/history/backlog/2026-10-07-gate-removal-unremediable-refuse-deadlock.md` *(Cluster pointer tidy)*
- `docs/history/backlog/2026-10-08-gate-removal-residual-fail-open-shapes.md` *(Cluster pointer tidy)*
- `docs/history/backlog/2026-10-08-gate-removal-usage-doubled-token.md` *(Cluster pointer tidy)*
- `docs/history/backlog/PLAN-PROMPTS.md` *(landing prune rider, its own entry only)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: its round discovery is a separate surface, deliberately not rewired (Assumptions)
- `scripts/check_plan_origins_closed.py`; reason: the singular-origin-line extractor asymmetry generalizes beyond this plan (r1 overflow residual, separate concern)

## Validation Commands

Validation preamble (authoring-time mechanical audit): pre-round structural gate OUTCOME: pass; no-em-dash scan over the plan bytes (touched): clean; public-hygiene scan: clean.
Round-start state for r1: reviewed bytes committed 2f159f031 (digest 6284cc2df644935a10fb699d28b5a80dd961190c5e7f7730cc9b8b74792dfa0b).
Round-start state for r2: reviewed bytes committed 6ac436905 (digest 0a8689d670c520c95f97a0a7866bf2c5c724f2f490608f498239b8ff948c2999).
Round-start state for r3: this commit.

Run from the repository root (the executor's checkout of this plan):

- `$HOME/.agents/venvs/ai-playbook-test/bin/python3 -m pytest scripts/test_worktree_closeout_migrate.py` (fallback when the venv is absent: `python3 -m pytest scripts/test_worktree_closeout_migrate.py`)
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-15-closeout-gate-review-series-expansion.md`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`
- `bash scripts/check-no-em-dash.sh touched`
- `bash scripts/check_maintenance_pins.sh`

### Task 1: series-token grammar normalization

- [x] `_series_members` delivers placeholder-form expansion: given a home holding `2026-10-13-plan-review-x-r1.md` and a label citing `YYYY-MM-DD-plan-review-x-r*.md`, expects the series verifies with that member as highest-round witness. [class: IMPLEMENTATION_REQUIRED]
- [x] `_series_members` delivers wildcard-form expansion: given a home with mixed-date members (`2026-10-13-...-r1.md`, `2026-10-14-...-r2.md`) and a label citing `*-plan-review-x-r*.md`, expects both members match and the highest round is the witness. [class: IMPLEMENTATION_REQUIRED]
- [x] `_series_members` keeps concrete dates exact: given a concrete-date citation `2026-10-13-plan-review-x-r*.md` over a home holding only a `2026-10-14` member, expects a zero-member series (the refusal arm), never a cross-date match. [class: IMPLEMENTATION_REQUIRED]
- [x] Containment and behavior arms stay byte-identical: given a member whose resolved path leaves the home, expects it never counts in either new form; given the old call signature, expects unchanged round-ordering, link-following for verify-records, and the resolved-only filter for gate-removal. [class: IMPLEMENTATION_REQUIRED]

Files:
- scripts/worktree_closeout_migrate.py

Primary class anchors:
- `_series_members` in `scripts/worktree_closeout_migrate.py`

### Task 2: regression fixtures for both citation forms

- [x] Placeholder-form pass fixture: given the Task 1 placeholder scenario assembled in the test home, expects `gate-removal` passes and `verify-records` reports the dated r1 member as witness. [class: REPOSITORY_TEST]
- [x] Wildcard-form pass fixture: given the Task 1 mixed-date scenario, expects `gate-removal` passes naming the highest round. [class: REPOSITORY_TEST]
- [x] Exactness control fixture: given the concrete-date/cross-date scenario, expects `gate-removal` refuses naming the token (zero-member). [class: REPOSITORY_TEST]
- [x] Containment control fixtures: given a symlinked member resolving outside the home under each new form, expects the member never counts and the gate refuses; given a genuinely absent series in each form, expects the zero-member refusal. [class: REPOSITORY_TEST]

Files:
- scripts/test_worktree_closeout_migrate.py

### Task 3: template and gate grammar alignment

- [x] Template documents acceptance: given the plans template's Plan review record line, expects one added sentence stating the worktree-removal gate normalizes both the literal `YYYY-MM-DD` placeholder and wildcard date prefixes, either form verifies when the records are present, and concrete dates stay exact. [class: IMPLEMENTATION_REQUIRED]
- [x] Authoring preference recorded: given the same sentence, expects it to name the concrete-date prefix as the preferred authoring form, with no other skill text changed and the three prescribed-invocation pins untouched. [class: IMPLEMENTATION_REQUIRED]

Files:
- agents/skills/plans/SKILL.md

### Task 4: end-to-end validation and origin disposition

Pre-satisfaction note (path repair, 2026-10-15): the authoring landing 63618596c already deleted both origin rows, tidied the three cluster pointers, and pruned the frozen PLAN-PROMPTS entry with its receipt. The task's remaining execution work is verification of those landed dispositions plus the battery run and the completion-pass disposition record; the checkboxes below keep their wording, satisfied by verifying the landed bytes.

- [x] Battery green: given the Validation Commands section, expects every command exits 0 including the new fixtures (suite, readiness gate, hygiene scan, no-em-dash check, pins suite). [class: REPOSITORY_TEST]
- [x] Origin rows deleted in the landing change: given both origin rows completed by this plan, expects both rows deleted with this plan as the per-row commit-message witness. [class: IMPLEMENTATION_REQUIRED]
- [x] Cluster pointers tidied in the same change: given the three rows citing the placeholder row (`2026-10-07-gate-removal-unremediable-refuse-deadlock.md`, `2026-10-08-gate-removal-residual-fail-open-shapes.md`, `2026-10-08-gate-removal-usage-doubled-token.md`), expects each Cluster pointer re-aimed or dropped coherently. [class: IMPLEMENTATION_REQUIRED]
- [x] Landing riders hold: given the landing flow, expects `--check-coverage`/`--mark-covered` run for gate value (no-op once the rows are gone) and the PLAN-PROMPTS entry pruned by the landing rider with its receipt line. [class: IMPLEMENTATION_REQUIRED]
- [x] Completion-pass disposition recorded: given both rows deleted by the landing, expects the completion pass to append the plans-skill `## Disposition of migrated backlog items` section naming this plan as the covering disposition, so the archive census reports ok for both origins. [class: IMPLEMENTATION_REQUIRED]

Files:
- docs/history/backlog/2026-10-07-gate-removal-unremediable-refuse-deadlock.md
- docs/history/backlog/2026-10-08-gate-removal-residual-fail-open-shapes.md
- docs/history/backlog/2026-10-08-gate-removal-usage-doubled-token.md
- docs/history/backlog/PLAN-PROMPTS.md

## Disposition of migrated backlog items

Both origin rows (`2026-10-08-gate-removal-placeholder-citation.md`, `2026-10-14-worktree-closeout-gate-wildcard-citation.md`) were deleted by the authoring landing 63618596c with this plan as the per-row commit-message witness; the three cluster pointers were re-aimed in the same change and the frozen PLAN-PROMPTS entry was pruned with its receipt. This plan is the covering disposition for both rows.
