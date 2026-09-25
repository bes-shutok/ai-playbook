# Plan: review staging leftovers disposition and filename-date calendar validity

Backlog origins (scope of record; full text read from `docs/history/backlog/`):

- `docs/history/backlog/2026-09-16-review-staging-coverage-attempt-shadowing.md` (origin 1, HIGH)
- `docs/history/backlog/2026-09-16-review-retention-and-safe-pruning.md` (origin 2)
- `docs/history/backlog/2026-09-19-review-staging-canonical-pattern-retrofit.md` (origin 3)
- `docs/history/backlog/2026-09-19-review-staging-integration-points-row-accuracy.md` (origin 4)
- `docs/history/backlog/2026-09-23-panel-profile-filename-date-calendar-validity.md` (origin 5)
- `docs/history/backlog/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md` (origin 6; folded in from plan-review r1 finding F1: the same executed plan absorbed it, so the disposition pass that claims the family closes it too)

Predecessor (the executed plan whose recorded dispositions this plan checks against):
`docs/plans/completed/2026-09-22-review-staging-infra-quality.md`, executed clean and
landed on main as 56102482 ("execute: review staging and infra quality plan").

## Terms

- origin: one of the six backlog items listed in the header; the unit of disposition.
- executed plan: `docs/plans/completed/2026-09-22-review-staging-infra-quality.md`
  (main 56102482); its Tasks 1-7 and origin receipts are the comparison basis.
- absorbed-but-unarchived stray: an origin whose fixing work already landed while the
  origin file itself stayed open in `docs/history/backlog/` with no completed twin.
- panel profile: the date-fenced reduced validator path gated by `PANEL_PROFILE_MAX_DATE`
  (executed plan Task 5).
- filename leg / sidecar leg: the two date sources `_panel_profile_record_date` consults;
  the staging filename's leading `YYYY-MM-DD`, and the sidecar `date` field fallback.
- disposition pointer: a `Status: done <date> (fixed by <plan path>; <evidence>)` line
  plus the archive move and a document-registry row.

## Assumptions

- assume origins 1-4 and 6 are fully satisfied by the executed plan and this plan closes
  them with disposition pointers only, changing no skill or script bytes; basis:
  authoring-time byte verification 2026-09-23: the `attempt_outcome` rename and the
  positive attempts-telemetry selftest check are present in
  `scripts/validate_review_staging.py` (lines ~2612 and ~12040, executed plan Task 1,
  rename itself landed pre-plan in 7baa8ce1); `scripts/review_retention.py`,
  `scripts/test_review_retention.py`, the `review_retention_months` key, the docs-branch
  transaction, and the skill/README wiring are present (executed plan Tasks 2-3); the
  `PANEL_PROFILE_MAX_DATE = "2026-09-19"` fence, the reduced path, and the shape-aware
  parser are present (executed plan Task 5); the Integration Points rows are verified
  narrowed in `agents/skills/review-staging/SKILL.md` (confluence and reconciliation rows
  attribute the Metadata twin to the universal review-staging template, the
  doing-code-review row carries the `review_record_selection.py` preflight note, the
  execute-plan Phase 3 row no longer claims the helper; executed plan Task 6); the
  `## Synthesis-time hard gates` section exists at
  `agents/skills/review-staging/SKILL.md:372` together with the validator's
  `map to the closed confidence enum` remediation hint, matching origin 6's Prevention
  items 1-2 (executed plan Task 4).
- assume origin 5's remainder is real on the current tree; basis: the filename leg of
  `_panel_profile_record_date` returns the shape-only regex match with no calendar check
  while the sidecar leg validates `date.fromisoformat` fail-closed
  (`scripts/validate_review_staging.py` ~4831-4844).
- assume origin 5's fix direction is to align the filename leg to the sidecar leg's
  calendar-strict semantics, with a calendar-invalid filename date meaning "no date"
  (return None, never a sidecar fallback); basis: the origin's own prescribed semantics
  ("meaning 'no date' on failure"), the fail-closed posture of the r1 F3 sidecar fix, and
  the dispatch's standing pre-authorization accepting the recommended option.
- assume closure mechanics follow the observed repository convention: rewrite (or add)
  the item's `Status:` line to `Status: done <date> (fixed by <plan path>; <evidence>)`,
  git mv the file into `docs/history/backlog/completed/` keeping the filename, and append
  one `docs/maintenance/document-registry.md` row per closed item mirroring the
  `authoring-lane-claim-check-gap` row shape; basis:
  `docs/history/backlog/completed/2026-09-18-authoring-lane-claim-check-gap.md` and its
  registry row.
- assume the EXECUTING session closes the six origins inside Tasks 3-4; the authoring
  session leaves them open; basis: the executed plan's out-of-scope receipt ("origins stay
  in place while the plan is open and are moved only by the completion step of the plan
  lifecycle") and the plans-skill lifecycle rule.
- assume one plan covers all six origins; basis: the dispatch prompt mandates a single
  plan for the P49 group, and review r1 F1 folded the sixth same-family stray into that
  single disposition pass.

Decision points requiring a grill: origin-5 direction (align the legs vs document the asymmetry as intended): align, filename leg becomes calendar-strict with no sidecar fallback (source: standing pre-authorization accepting the recommended option, 2026-09-23, Task 2); calendar-invalid filename-date semantics (fall through to the sidecar date vs no-date): no-date, return None (source: the origin text's prescribed semantics, 2026-09-23, Task 2); closure timing (authoring session closes vs executing session closes): the executing session closes all six origins inside plan Tasks 3-4 (source: executed plan out-of-scope receipt and plans-skill lifecycle rule, 2026-09-23, Tasks 3-4); sixth-origin scope (leave the r1-folded stray to a later pass vs close it here): close it here as a pointer closure (source: plan-review r1 F1 fold accepted under the dispatch's standing pre-authorization, 2026-09-23, Task 3)

## Gist & Examples

The executed review-staging plan landed its fixes but none of its origin family items
were archived: five dispatched origins (plus a sixth same-family stray found by review
r1) still sit open in `docs/history/backlog/` with no completed twins and no registry
rows, the absorbed-but-unarchived stray class that silently hides landed work. This plan
does the disposition pass. Phase 0 (Task 1) re-verifies each origin's disposition against
the executed plan's recorded receipts and the actual bytes on the execution tree,
recording one receipt per origin. Origins 1-4 and 6 are pointer closures: their fixes are
already landed and verified, so Task 3 rewrites each Status line to a done pointer naming
the executed plan, moves each file to the completed archive, and adds the registry rows.
Origin 5 has a real remainder: Task 2 implements it, Task 4 then closes it the same way
pointing at THIS plan's completed path.

The origin-5 defect, concretely: `_panel_profile_record_date` prefers the staging
filename's leading date and falls back to the sidecar `date` field. The 2026-09-23
execution made the sidecar leg calendar-strict (r1 F3: `2026-01-99` must mean "no date"
because a lexicographic fence compare is only calendar-honest for real dates), but left
the filename leg format-only. A record named `2026-01-99-foo-r1.md` is format-valid,
calendar-invalid, sorts inside the fence window, and enters the reduced path today.
Task 2 turns the authoring-time probe's discriminations into a permanent selftest check
and lands the fix. The check's fixture and expectations are fully specified in the task
item (filename, sidecar date, header-shape content, exact expected outputs), so it is
reproducible from this plan alone; the probe script (`docs/tmp/p49-authoring-probe.py`)
is an untracked authoring artifact kept as provenance, and the durable evidence is the
committed check plus Task 2's RED step, whose discrimination plan-review r1 re-executed
against the real validator (exit 0 today on the calendar-invalid name; exit 1 under the
simulated fix with `finding conservation: Markdown lists 0 finding(s) but sidecar lists 1`
among the full-contract errors and no profile selection line; the calendar-valid control
exit 0 in both states; unit return None with NO sidecar fallback even though the sidecar
date was in-window).

The plan changes no user-facing skill prose: the closures point at skill text the
executed plan already landed.

## Evaluation Criteria

**Quality dimensions:**

- correctness: a calendar-invalid filename date can never select the panel profile; the
  discriminating selftest check is green, and the mutation probe (fix reverted) fails
  exactly that check and nothing else (baseline: whole selftest green on today's tree,
  observed 2026-09-23).
- traceability: every closed origin's Status line names the fixing plan and the
  per-origin evidence; the document registry carries exactly one completed-state row per
  closed origin pointing at the completed path; `doc_registry_validator.py validate`
  reports zero hard findings.
- no-regression: the validator selftest and the retention unittest stay green at every
  task boundary; the sidecar leg's r1 F3 semantics and all executed-plan fences are
  byte-unchanged.

**Done when:**

- the whole Validation Commands block exits 0 end to end;
- all six origins live in `docs/history/backlog/completed/` with done Status pointers,
  and no open twin remains under `docs/history/backlog/`;
- the document registry has exactly one completed row per closed origin.

**Ship when:**

- none; every condition is repository-verifiable. No deploy, external team, or human
  release gate applies to this plan.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if
valid):

**Production code:**

- `scripts/validate_review_staging.py` (partial: `_panel_profile_record_date` including
  its docstring, plus the new selftest check and its fixtures in the selftest region
  Task 2 adds. ALL other functions, constants, and regions of this file are frozen;
  reject any review finding that touches them.)

**Tests:**

- selftest additions live inside `scripts/validate_review_staging.py` (region-frozen as
  above; the standalone test files are untouched)

**Documentation/backlog:**

- `docs/history/backlog/2026-09-16-review-staging-coverage-attempt-shadowing.md` (Status
  line + archive move)
- `docs/history/backlog/2026-09-16-review-retention-and-safe-pruning.md` (same)
- `docs/history/backlog/2026-09-19-review-staging-canonical-pattern-retrofit.md` (same)
- `docs/history/backlog/2026-09-19-review-staging-integration-points-row-accuracy.md`
  (same)
- `docs/history/backlog/2026-09-23-panel-profile-filename-date-calendar-validity.md`
  (same)
- `docs/history/backlog/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md`
  (same)
- `docs/maintenance/document-registry.md` (six appended rows; the rest of the table is
  frozen)

**Plan-related extension**; implementation and review may change files not listed above.
Treat a finding as in scope when it is **causally related to this plan**: it implements
or completes a plan task, fixes a regression introduced by plan work, closes wiring or
docs implied by an explicit must-fix change, or contradicts a contract the plan changed.
If the link to the plan is weak or speculative, drop as out of scope with a one-line
reason.

**Out of scope; reject unless plan-related:**

- `agents/skills/**`; reason: every disposition pointer targets skill prose already
  landed by the executed plan; no skill byte changes under this plan.
- `scripts/review_retention.py`, `scripts/test_review_retention.py`; reason:
  predecessor-plan deliverables, frozen.
- `docs/plans/completed/2026-09-22-review-staging-infra-quality.md`; reason: immutable
  completed history; read-only comparison basis.
- every other `docs/history/backlog/` item; reason: this plan dispositions exactly the
  six named origins.

## Design Invariants (CR Guard)

- The panel profile stays strictly date-fenced and fail-closed: a record whose date
  cannot be established NEVER enters the reduced path (undated and post-window records
  keep the full contract). The Task 2 fix narrows the profile's reach; it must not widen
  it.
- The sidecar leg's r1 F3 fail-closed semantics are unchanged; the fix aligns the
  filename leg TO the sidecar leg's strictness, never the reverse, and there is NO
  sidecar-date fallback when the filename date is calendar-invalid (a fallback would
  re-admit a record the origin explicitly excludes).
- The version-1 sidecar contract, its closed enums, key allowlists, and the
  `EXTENDED_SIDECAR_MIN_DATE` fence semantics are untouched.
- Origins 1-4 and 6 closures are pointer-only: no skill or script bytes change; the
  executed plan's landed state is the comparison basis and is not re-litigated or
  re-implemented.
- The completed archive transition is move-and-annotate only: origin bodies keep their
  historical text except the Status line.

## Validation Commands

Authoring-time state (2026-09-23, recorded per the RED-today rule): the selftest,
retention unittest, registry validator, and em-dash sweep pass on today's tree; the
closure greps fail until Tasks 3-4 land (first actually-failing gate on today's tree:
the calendar-invalid check-name grep, the check does not exist yet; the RED direction of
the closure greps re-verified by plan-review r1). The block is the FINAL gate and is
expected green only after Task 4.

```bash
python3 scripts/validate_review_staging.py --selftest || { echo "validator selftest failed"; exit 1; }
python3 scripts/test_review_retention.py || { echo "retention unittest failed"; exit 1; }
python3 scripts/doc_registry_validator.py validate >/dev/null || { echo "registry validation failed"; exit 1; }
grep -qF "panel profile: calendar-invalid filename date does not select the reduced path" scripts/validate_review_staging.py || { echo "calendar-invalid fixture check missing"; exit 1; }
grep -qF "fromisoformat(name_match.group(1))" scripts/validate_review_staging.py || { echo "filename leg calendar-strict validation missing"; exit 1; }
if grep -qF "keeps its format-only parse" scripts/validate_review_staging.py; then echo "format-only asymmetry docstring still present"; exit 1; fi
for f in \
  docs/history/backlog/completed/2026-09-16-review-staging-coverage-attempt-shadowing.md \
  docs/history/backlog/completed/2026-09-16-review-retention-and-safe-pruning.md \
  docs/history/backlog/completed/2026-09-19-review-staging-canonical-pattern-retrofit.md \
  docs/history/backlog/completed/2026-09-19-review-staging-integration-points-row-accuracy.md \
  docs/history/backlog/completed/2026-09-23-panel-profile-filename-date-calendar-validity.md \
  docs/history/backlog/completed/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md ; do
  test -f "$f" || { echo "missing completed origin: $f"; exit 1; }
  grep -q "^Status: done 2026-09-23 (fixed by docs/plans/completed/" "$f" || { echo "done Status pointer missing: $f"; exit 1; }
done
for f in \
  docs/history/backlog/2026-09-16-review-staging-coverage-attempt-shadowing.md \
  docs/history/backlog/2026-09-16-review-retention-and-safe-pruning.md \
  docs/history/backlog/2026-09-19-review-staging-canonical-pattern-retrofit.md \
  docs/history/backlog/2026-09-19-review-staging-integration-points-row-accuracy.md \
  docs/history/backlog/2026-09-23-panel-profile-filename-date-calendar-validity.md \
  docs/history/backlog/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md ; do
  if test -e "$f"; then echo "open twin still present: $f"; exit 1; fi
done
for id in review-staging-coverage-attempt-shadowing review-retention-and-safe-pruning review-staging-canonical-pattern-retrofit review-staging-integration-points-row-accuracy panel-profile-filename-date-calendar-validity review-staging-synthesis-friction-undocumented-gates ; do
  n=$(grep -cF "| $id |" docs/maintenance/document-registry.md)
  test "$n" -eq 1 || { echo "registry row count for $id is $n, expected 1"; exit 1; }
  grep -qF "| $id | no | completed |" docs/maintenance/document-registry.md || { echo "registry row not completed state: $id"; exit 1; }
  grep -qF "docs/history/backlog/completed/" docs/maintenance/document-registry.md || { echo "registry completed path missing: $id"; exit 1; }
done
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file docs/plans/2026-09-23-review-staging-leftovers-disposition.md docs/history/backlog/completed/2026-09-16-review-staging-coverage-attempt-shadowing.md docs/history/backlog/completed/2026-09-16-review-retention-and-safe-pruning.md docs/history/backlog/completed/2026-09-19-review-staging-canonical-pattern-retrofit.md docs/history/backlog/completed/2026-09-19-review-staging-integration-points-row-accuracy.md docs/history/backlog/completed/2026-09-23-panel-profile-filename-date-calendar-validity.md docs/history/backlog/completed/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md || { echo "em-dash scan failed"; exit 1; }
```

### Task 1: Phase 0 disposition receipts (verification only)

Files:
- none (verification only; no commit)

- [x] Record the Phase 0 receipt per origin in the task log: origin path, the executed plan task that satisfied it, and the byte-level evidence observed on the execution tree; the pointer closures cite origin 1 executed plan Task 1 (attempts-telemetry fixture and same-family sweep; rename landed pre-plan in 7baa8ce1), origin 2 executed plan Tasks 2-3 (retention helper, docs-branch transaction, lifecycle wiring; the origin's own Current disposition paragraph names the reusable policy as the remaining work), origin 3 executed plan Task 5 (date-fenced panel profile, direction b; retrofit script rejected), origin 4 executed plan Task 6 (row accuracy pass), origin 6 executed plan Task 4 (Synthesis-time hard gates checklist at agents/skills/review-staging/SKILL.md:372 plus the map-to-the-closed-confidence-enum remediation hint, matching the origin's Prevention items 1-2), all under main 56102482 [class: REPOSITORY_TEST]
- [x] Confirm origin 5's remainder is still real on the execution tree: the filename leg of `_panel_profile_record_date` returns the shape-only regex match while the sidecar leg validates `date.fromisoformat` fail-closed [class: REPOSITORY_TEST]
- [x] Whole-suite state: `python3 scripts/validate_review_staging.py --selftest` exits 0 and `python3 scripts/test_review_retention.py` exits 0 (predecessor baseline; no plan work landed yet) [class: REPOSITORY_TEST]

### Task 2: Calendar-strict filename leg (RED then GREEN)

Files:
- `scripts/validate_review_staging.py`

- [x] Add the selftest check `panel profile: calendar-invalid filename date does not select the reduced path`; given a staged fixture whose filename date is format-valid but calendar-invalid (`2026-01-99-panel-profile-calendar-invalid-r1.md`) while the sidecar `date` field is in-window (`2026-09-01`), whose finding blocks are authored in the panel header shape (`### 1. <title> (Severity)` blocks, never `#### F<N>.` blocks, so the full contract's extractor recognizes zero finding blocks), expects `--hard` to exit 1 with the full-contract conservation errors `finding conservation: Markdown lists 0 finding(s) but sidecar lists 1` and `sidecar finding id 1 has no matching Markdown #### F block` (both observed verbatim in the authoring-time fixed-state probe, 2026-09-23) and with no `panel profile: record dated` selection line; pair it in the same check with the positive control: the identical bytes renamed to a calendar-valid in-window filename date (`2026-09-01-panel-profile-calendar-control-r1.md`) pass `--hard` with exit 0 [class: REPOSITORY_TEST]
- [x] Run, expect RED: `python3 scripts/validate_review_staging.py --selftest` exits non-zero with exactly the new check failing (today's filename leg selects the profile for the calendar-invalid name; every pre-existing check stays green: whole-suite baseline rc 0 observed 2026-09-23) [class: REPOSITORY_TEST]
- [x] Implement the fix in `_panel_profile_record_date`: after the filename regex match, validate the captured date with `date.fromisoformat` inside try/except ValueError; on ValueError return None (undated: no reduced path, NO sidecar fallback); keep returning the matched string on success; update the docstring: delete the closing sentence anchored by the phrase `keeps its format-only parse` and describe the aligned fail-closed semantics (both legs calendar-strict; a calendar-invalid filename date means no date, never a sidecar fallback) [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect GREEN: the selftest exits 0 with the new check OK (whole-suite state: selftest green; `python3 scripts/test_review_retention.py` untouched and green) [class: REPOSITORY_TEST]
- [x] Mutation probe: revert the filename leg to the shape-only return (remove the try/except), run the selftest, record the observed failing set in the task log; expected failing set: exactly the new check (authoring-time probe evidence: the fixture exits 0 under the mutation and the rest of the suite is green); restore the fix and re-run to green [class: REPOSITORY_TEST]
- [x] Commit: `validator: calendar-strict filename leg for the panel profile fence (review staging leftovers task 2)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Close origins 1-4 and 6 with disposition pointers

Files:
- `docs/history/backlog/2026-09-16-review-staging-coverage-attempt-shadowing.md`
- `docs/history/backlog/2026-09-16-review-retention-and-safe-pruning.md`
- `docs/history/backlog/2026-09-19-review-staging-canonical-pattern-retrofit.md`
- `docs/history/backlog/2026-09-19-review-staging-integration-points-row-accuracy.md`
- `docs/history/backlog/2026-09-18-review-staging-synthesis-friction-undocumented-gates.md`
- `docs/maintenance/document-registry.md`

- [x] For each of the five origins: rewrite (or, for the canonical-pattern item, which carries no Status line, add directly under the title heading) the Status line to `Status: done 2026-09-23 (fixed by docs/plans/completed/2026-09-22-review-staging-infra-quality.md; <per-origin evidence>)`, where the per-origin evidence cites the executed plan's task per the Task 1 receipts; change nothing else in the bodies [class: IMPLEMENTATION_REQUIRED]
- [x] git mv each of the five files to `docs/history/backlog/completed/` keeping the filenames [class: IMPLEMENTATION_REQUIRED]
- [x] Append one registry row per closed origin to `docs/maintenance/document-registry.md` mirroring the authoring-lane-claim-check-gap row shape: `| <identity> | no | completed | 2026-09-23 | executed | docs/history/backlog/completed/<file>.md |  |  |  |` for identities review-staging-coverage-attempt-shadowing, review-retention-and-safe-pruning, review-staging-canonical-pattern-retrofit, review-staging-integration-points-row-accuracy, review-staging-synthesis-friction-undocumented-gates [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect GREEN: selftest, retention unittest, and the registry validator all exit 0; the five open twins are gone (whole-suite state: validator bytes unchanged since Task 2) [class: REPOSITORY_TEST]
- [x] Commit: `docs: close five absorbed review-staging origins with disposition pointers (review staging leftovers task 3)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Close origin 5 with disposition pointer

Files:
- `docs/history/backlog/2026-09-23-panel-profile-filename-date-calendar-validity.md`
- `docs/maintenance/document-registry.md`

- [x] Rewrite the Status line to `Status: done 2026-09-23 (fixed by docs/plans/completed/2026-09-23-review-staging-leftovers-disposition.md; filename leg aligned calendar-strict with no sidecar fallback, Task 2 of that plan)`; change nothing else in the body [class: IMPLEMENTATION_REQUIRED]
- [x] git mv the file to `docs/history/backlog/completed/` keeping the filename [class: IMPLEMENTATION_REQUIRED]
- [x] Append the registry row for panel-profile-filename-date-calendar-validity in the Task 3 row shape [class: IMPLEMENTATION_REQUIRED]
- [x] Run, expect GREEN: the registry validator exits 0 and the open-twin loop in Validation Commands finds nothing (whole-suite state: selftest and retention unittest green since Task 2) [class: REPOSITORY_TEST]
- [x] Commit: `docs: close the panel-profile filename-date residual origin (review staging leftovers task 4)` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Final validation sweep

Files:
- none (verification only; commit only if the sweep surfaces residue)

- [x] Run the whole Validation Commands block top to bottom and record each command's outcome in the task log (whole-suite state: every command exits 0) [class: REPOSITORY_TEST]
- [x] Residue sweep: the Validation Commands open-twin loop and registry count loop are the mechanical checkers; confirm from the task log that both ran clean (zero open twins, exactly one completed registry row per closed origin) [class: REPOSITORY_TEST]
- [x] Commit only if the sweep fixed residue: `docs: review staging leftovers final sweep (task 5)` [class: IMPLEMENTATION_REQUIRED]
