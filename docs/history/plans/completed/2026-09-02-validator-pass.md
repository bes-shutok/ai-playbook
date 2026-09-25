# Plan: validator pass (source-kind crash, coverage follow-ups, id-fixture hardening, v1 fixture simplifications, fence-scanner round 2)

Backlog origin: `docs/history/backlog/2026-08-30-source-kind-unhashable-crash.md`,
`docs/history/backlog/2026-08-28-validator-test-coverage-followups.md`,
`docs/history/backlog/2026-08-31-id-fixture-family-hardening.md`,
`docs/history/backlog/2026-08-31-v1-redundant-null-keep-valid-fixtures.md`,
`docs/history/backlog/2026-08-31-v1-required-field-tuple-null-semantics-split.md`,
`docs/history/backlog/2026-08-31-fence-scanner-round-2.md`

## Terms

- **r5 F1 carve-out**: on version-1 sidecars, `selection_reason` and
  `escalation_reason` are the only required fields where an explicit JSON null is the
  legal not-applicable form; every other required field must not be null.
- **r6 F1 conservation arm**: the blocking-conservation check in
  `validate_current_payload` that fails hard when a sidecar declares
  `blocking: true` but the Markdown record has no parseable `Blocking` value.
- **r6 F3 partial fallback**: `classify_with_fallback`'s two-pass contract: when a
  fence never closes, first-pass events are trustworthy only up to the opener and the
  suffix is re-classified with heading resets.
- **`_selftest_current_contract`**: the embedded selftest family in
  `scripts/validate_review_staging.py` whose `check(label, ok)` helper accumulates
  assertions; run via `python3 scripts/validate_review_staging.py --selftest`.
- **Skill-gate marker**: the per-(project, session) consent marker under
  `~/.ai-playbook/runtime/skill-invoked/` refreshed by the plans skill before every
  plan-file write, per `agents/hooks/skill-gate/README.md`.
- **Session key**: `session_channel.py` output; empty-after-strip becomes the literal
  `no-session`, otherwise `sha1(value)[:16]`.

## Assumptions

- assume the work stays on branch `2026-09-02-phase3-residue-pass`; basis: explicit
  user constraint in the scheduling prompt (standing pre-authorization 2026-09-02).
- assume the crash fix reuses the existing membership-gate message for non-string
  values; basis: probe 2026-09-02  -  a hashable mistype (`7`) today produces
  `current sidecar source_kind must be one of ['code', 'document', 'plan', 'rfc']; got 7`.
- assume fence-scanner item 1 lands as a warn-level stderr diagnostic naming the
  unclosed-opener line number, not a hard error; basis: the backlog offers "warn or
  hard error", `parse_markdown_findings`/`is_review_ready` have no result channel, and
  a hard error would reject inputs the r6 F3 fallback deliberately recovers.
- assume fence-scanner item 3 (helper returns the pre-opener prefix) is applied in
  this pass; basis: the backlog defers it to "a future plan", which this plan is.
- assume the minimal two-loop split for the version-1 widened tuple, not the
  spec-driven table; basis: the backlog rule "Either do the minimal split or go
  straight to the table; do not do both".
- assume the coverage backlog's line numbers are stale (the file evolved through the
  v1-gate-trio pass); the gaps were re-verified against current code on 2026-09-02:
  the null-rejection loop now hardcodes six fields (not two), the empty-flag selftest
  covers only `--source-plan`, and both r7 twins are absent.

## Gist & Examples

All work lives in `scripts/validate_review_staging.py`: one production gate fix, one
production behavior fix, three refactors, and the rest new selftest fixtures in the
existing families (`_selftest_versioned_schema_and_patterns` for the v1-flavored
fixtures, `_selftest_current_contract` and `_selftest_source_{plan,rfc,doc}_cli` for
the rest  -  each task names its family).

1. **Unhashable `source_kind` crash (RED→GREEN).** A JSON list in `source_kind`
   (e.g. `["code"]`) crashes the membership gate at
   `scripts/validate_review_staging.py:1199` (`declared_kind not in VALID_SOURCE_KINDS`
    -  frozenset hashing) with `TypeError: cannot use 'list' as a set element`, aborting
   the whole validation run instead of emitting a diagnostic (probed 2026-09-02). Fix:
   gate on `isinstance(declared_kind, str)` before the membership test; non-strings get
   the existing `current sidecar source_kind must be one of ...` error. Hashable
   mistypes keep their current single report; `None` stays skipped (presence-only).

2. **Four coverage follow-ups (test-only, characterization GREEN).**
   - The null-rejection selftest iterates a hardcoded six-field tuple
     (`findings`, `counts`, `date`, `review_type`, `artifact_slug`, `round`); ten
     required fields have no explicit-null assertion and the loop cannot auto-extend.
     Iterate `V1_REQUIRED_TOP_LEVEL_FIELDS` minus `schema_version` (absence = legacy)
     and the two r5 F1 nullable enums, and pin the carve-out with one keep-pass check.
   - The empty-flag loud-exit selftest covers only `--source-plan`; mirror it for
     `--source-rfc` and `--source-doc` (the guard at `main`'s flag loop is shared, but
     each flag's arm is unpinned).
   - r7 F1 twin: sidecar `blocking: true` with a parseable Markdown
     `- **Blocking**: false` must produce the `blocking disagrees` conservation error  - 
     a directional rewrite of the comparison would otherwise silently reopen the
     fail-open readiness hole the r6 fix closed (only the current-shape family covers
     the reverse direction today).
   - r7 F2 twin: sidecar `blocking: false` with the Markdown Blocking bullet fenced
     (unparseable) must stay silent  -  no `no parseable Blocking value` error, no
     disagreement error  -  pinning that the r6 arm fires only for sidecar-true.

3. **Id-fixture family hardening (refactor + new fixture).** Add a `mutate_early`
   hook parameter to `_run_id_fixture` (called after the payload is built, before the
   markdown is constructed), migrate the hand-rolled `id-duplicate-agreeing` fixture
   onto the runner, and add a three-row agreeing fixture (`[1, 1, 1]` on both sides)
   asserting exactly two `duplicate id` errors alongside conservation/order silence  - 
   pinning per-occurrence reporting that a two-row fixture cannot discriminate.

4. **v1 fixture simplifications.**
   - Delete the two redundant null keep-valid entries
     (`("selection_reason", None, "null")`, `("escalation_reason", None, "null")`);
     the base payload already carries both nulls through every `_v1_copy()` check, so
     coverage is unchanged (and Task 2's carve-out keep-pass makes that explicit).
   - Split the widened field tuple in `validate_version1_payload` (~914–924) into two
     loops sharing one reporter: `review_type`/`artifact_slug`/`date` (None → r5 F1
     sole reporter) vs `selection_reason`/`escalation_reason` (None legal, r5 F1
     carve-out), each with its one-line comment.
   - Pin the focused-panel double-report (r5 additional item): a v1 payload with
     `panel_mode: "focused"` and a present-but-empty non-string `selection_reason`
     (e.g. `[]`) produces BOTH the type-gate error and the presence-gate error; pin
     with a keep-fail fixture asserting both messages (no behavior change).
   - Fix the cross-severity duplicate-id false disagreement (r6 additional item,
     RED→GREEN): two findings sharing an id at different severities, agreeing between
     sidecar and Markdown, correctly get the duplicate-id error but also a false
     `severity disagrees` error because the conservation reconciliation keys by id and
     last-match-wins collapses the rows. Suppress the per-id conservation comparison
     for ids the duplicate gate already flagged; the fixture also pins that no new
     conservation error appears for either row.

5. **Fence-scanner round 2.**
   - `parse_markdown_findings` emits one stderr warning when `unclosed_opener is not
     None`, naming the unclosed-opener line number, so post-opener metadata bullets
     being silently swallowed become a signal (warn-level per Assumptions; recovery
     behavior identical to r6 F3).
   - Extract the duplicated `^## Findings\s*$` section-extraction prelude from
     `split_finding_blocks` and `parse_markdown_findings` into one small helper placed
     beside `classify_with_fallback`; both consumers call it.
   - `classify_with_fallback` returns the pre-opener prefix of the first-pass events
     directly in the fallback case (instead of the full list), and both consumers drop
     their defensive `unclosed_opener` truncation/filter. The all-closed case keeps
     returning the full event list with `unclosed_opener = None`.

Example before/after for the crash: a sidecar with `"source_kind": ["code"]` today
aborts `validate_staging_file(hard=True)` with TypeError; after Task 1 it returns
`ok=False` with the targeted one-of error and the run continues to report any other
defects in the same payload.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the crash fixture turns RED→GREEN; the cross-severity conservation
  fixture turns RED→GREEN; every other new check is characterization GREEN on
  arrival and stays GREEN through its refactor task.
- test coverage: all four coverage gaps have self-contained given/expects checks in
  the selftest family; `--selftest` exits 0 with the new checks present.
- maintainability: one shared Findings-prelude helper (no duplicated
  section-extraction regex), one id-fixture runner (no hand-rolled inline copy), one
  two-loop v1 tuple split (None contract visible in code, not only comments).

**Done when:**
- `python3 scripts/validate_review_staging.py --selftest` exits 0.
- `python3 -m py_compile scripts/validate_review_staging.py` exits 0.
- A sidecar with `source_kind: ["code"]` produces the targeted one-of error
  (demonstrated in the Task 1 GREEN run output).
- Every task's commit leaves the selftest suite green (each commit is self-consistent).

**Ship when:**
- The change is squash-merged per the repository's merge policy; no deployed surface
  exists beyond the repository itself (validator script consumed in-repo and by
  sibling skills via the runtime sync).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if
valid):

**Production code:**
- `scripts/validate_review_staging.py`  -  scope limited to: `validate_current_payload`
  (the `source_kind` gate and the blocking-conservation reconciliation),
  `validate_version1_payload` (the widened-tuple region only),
  `classify_with_fallback`, `split_finding_blocks`, `parse_markdown_findings`, a new
  Findings-prelude helper beside `classify_with_fallback`, `_run_id_fixture`, and the
  `_selftest_current_contract` fixture regions named in the tasks. **All other
  functions in this file are frozen; reject any review finding that touches them**
  (out-of-scope bug findings are backlogged, not fixed in-place).

**Tests:**
- Selftests live inside `scripts/validate_review_staging.py` itself, in the
  `_selftest_versioned_schema_and_patterns`, `_selftest_current_contract`, and
  `_selftest_source_{plan,rfc,doc}_cli` families (the fixture regions named in the
  tasks); there are no separate test files.

**Out of scope; reject unless plan-related:**
- `README.md` and skill catalogs; reason: no CLI flag, output contract, or skill
  integration changes in this pass.
- `agents/skills/review-staging/SKILL.md`; reason: the staging-doc contract is
  unchanged (the warning is diagnostic-only).
- All other `scripts/*.py`; reason: single-file pass by design.

## Validation Commands

```bash
python3 -m py_compile scripts/validate_review_staging.py || { echo "compile failed"; exit 1; }
python3 scripts/validate_review_staging.py --selftest || { echo "selftest failed"; exit 1; }
# The selftest family must contain the new check labels (each dedicated, rule 7):
for label in \
  "unhashable source_kind" \
  "three duplicate ids" \
  "blocking disagrees with a parseable Markdown Blocking bullet" \
  "sidecar blocking false with an unparseable Markdown Blocking bullet stays silent" \
  "r5 F1 nullable enum" \
  "focused panel empty selection_reason double-report" \
  "cross-severity duplicate ids" \
  "unclosed fence warning"; do
  grep -qF "$label" scripts/validate_review_staging.py \
    || { echo "missing selftest label: $label"; exit 1; }
done
# The crash gate must be isinstance-guarded before the membership test:
grep -q "isinstance(declared_kind, str)" scripts/validate_review_staging.py \
  || { echo "source_kind str gate missing"; exit 1; }
# The Findings prelude literal must exist at exactly TWO sites after Task 5:
# the new shared helper, plus the frozen independent prelude inside
# validate_staging_file (~1706), which is out of this plan's scope by design.
test "$(grep -cF '^## Findings\s*$' scripts/validate_review_staging.py)" -eq 2 \
  || { echo "Findings prelude count unexpected (want helper + frozen site)"; exit 1; }
# The consumer-side prefix slice must be gone from BOTH consumers; the slice
# survives in exactly ONE place  -  the helper's own prefix return:
test "$(grep -cF 'events[:unclosed_opener]' scripts/validate_review_staging.py)" -eq 1 \
  || { echo "prefix slice must exist only in the helper's return"; exit 1; }
if grep -n "i < unclosed_opener" scripts/validate_review_staging.py; then
  echo "consumer-side boundary filter still present"; exit 1
fi
```

### Task 1: Fix the unhashable `source_kind` TypeError crash

Files:
- `scripts/validate_review_staging.py`

- [x] Add a selftest fixture in `_selftest_versioned_schema_and_patterns` (the
      family where the `_v1_copy()` closure and the v1 type-gate fixtures live  -
      NOT `_selftest_current_contract`, where `_v1_copy` is not in scope):
      `check` label contains `unhashable source_kind`; given a
      `_v1_copy()` payload with `source_kind` set to `["code"]`, expects
      `validate_staging_file(hard=True)` to return a non-ok result (NOT raise) whose
      errors include the `must be one of` substring. Wrap the call in
      `try/except TypeError` so the pre-fix crash records a FAIL via `check`
      instead of aborting the run (exception-contained RED fixture).
- [x] Run → expect RED: the new check fails with `TypeError: cannot use 'list' as a
      set element` recorded (all pre-existing checks stay green).
- [x] Add `isinstance(declared_kind, str)` to the gate at the
      `declared_kind not in VALID_SOURCE_KINDS` membership test
      (~line 1199), keeping the existing f-string message so non-string values
      produce the same `must be one of ...; got ['code']` diagnostic.
- [x] Run → expect GREEN: `python3 scripts/validate_review_staging.py --selftest`
      exits 0.
- [x] Commit: `fix: gate source_kind membership on str so unhashable values get the targeted error`

### Task 2: Coverage follow-ups (four test-only checks)

Files:
- `scripts/validate_review_staging.py`

- [x] Rewrite the null-rejection loop (~4177) to iterate
      `V1_REQUIRED_TOP_LEVEL_FIELDS` minus `schema_version`,
      `selection_reason`, `escalation_reason` (computed in the loop header, not
      hardcoded); each field gets the explicit-null failing assertion. Add one
      keep-pass check: label contains `r5 F1 nullable enum`; given a
      `_v1_copy()` payload with `selection_reason` and `escalation_reason` both
      None, expects the result ok (the carve-out, pinned explicitly).
- [x] Mirror the empty `--source-plan` loud-exit selftest (~3520) for
      `--source-rfc` and `--source-doc`: given an empty-string value for each
      flag via `main([...])`, expects exit code 2 (argparse error) and the
      `must not be empty` message on stderr; capture stderr with the existing
      io.StringIO swap pattern.
- [x] r7 F1 twin: `check` label contains `blocking disagrees with a parseable
      Markdown Blocking bullet`; given the r6 F1 `blocking_payload` (sidecar
      blocking true) paired with Markdown whose Blocking bullet is present and
      `false`, expects a non-ok result containing `blocking disagrees` (the
      parseable-disagreement direction; a comparison rewrite that drops this
      direction turns this check RED).
- [x] r7 F2 twin: `check` label contains `sidecar blocking false with an
      unparseable Markdown Blocking bullet stays silent`; given a sidecar
      finding with `blocking: false` and Markdown with the Blocking bullet
      fenced inside a code fence, expects the result ok with no
      `no parseable Blocking value` and no `blocking disagrees` error.
- [x] Run → expect GREEN (characterization: all four pin current behavior;
      nothing in this task changes production code).
- [x] Commit: `test: close validator coverage gaps (null loop, empty flags, blocking twins)`

### Task 3: Id-fixture family hardening

Files:
- `scripts/validate_review_staging.py`

- [x] Extend `_run_id_fixture` (~2446) with two optional parameters: a
      `mutate_early=None` hook and a `row_count=2` default. `mutate_early`
      runs on the findings LIST before the markdown is built (the runner
      currently builds `md = _current_findings_markdown(two, ...)` first, so
      a payload-only post-mutation hook cannot affect the markdown side);
      `row_count` controls how many agreeing findings the runner builds.
      Existing callers are unchanged (defaults preserve today's behavior).
- [x] Migrate the `id-duplicate-agreeing` fixture (~2586–2610) onto
      `_run_id_fixture` with a `mutate_early` that sets every row's id to 1;
      its existing assertion (exactly one `duplicate id` error, plus
      conservation/order silence) must be preserved verbatim in the migrated
      `errors_ok` lambda.
- [x] New three-row fixture: `check` label contains `three duplicate ids`;
      given three agreeing rows with id 1 on BOTH sidecar and markdown (via
      `row_count=3` plus a `mutate_early` setting all ids to 1), expects exactly
      two `duplicate id` errors (`sum(...) == 2`) and no conservation or order
      errors  -  pinning per-occurrence reporting.
- [x] Run → expect GREEN (characterization plus the new discriminating fixture).
- [x] Commit: `refactor: add mutate_early hook to _run_id_fixture and pin triple-duplicate reporting`

### Task 4: v1 fixture simplifications and the tuple split

Files:
- `scripts/validate_review_staging.py`

- [x] Delete the two redundant null keep-valid entries
      (`("selection_reason", None, "null")` and `("escalation_reason", None,
      "null")`) from the keep-valid guard loop (~4323–4342; the loop guarding
      explicit-null forms, not the type-mistype tuple below it); keep the two
      string entries. Run the selftest and confirm the count of checks drops
      by exactly two with no failures (coverage is carried by the base
      payload's nulls and Task 2's carve-out keep-pass).
- [x] Split the widened field tuple in `validate_version1_payload` (~914–924)
      into two loops over explicit tuples  -
      `("review_type", "artifact_slug", "date")` commented `None -> r5 F1 sole
      reporter` and `("selection_reason", "escalation_reason")` commented
      `None legal (r5 F1 carve-out)`  -  sharing the existing error-emitting
      body (the loop's current `continue`-on-None collapses into the two
      loops' distinct skip/comment behavior). Behavior identical;
      characterization GREEN.
- [x] Focused-panel double-report pin: `check` label contains `focused panel
      empty selection_reason double-report`; given a v1 payload with
      `panel_mode: "focused"` and `selection_reason: []`, expects BOTH the
      `must be a string` type error AND the `focused panel missing
      selection_reason` presence error (pins the cosmetic double-report so a
      future fix is a conscious contract change, not a silent one).
- [x] Cross-severity duplicate-id conservation fix (RED→GREEN): add a fixture
      with `check` label containing `cross-severity duplicate ids`; given
      sidecar and markdown that agree on two rows sharing id 1 at different
      severities (Medium and High), expects the `duplicate id` error, NO
      `severity disagrees` error, and NO new conservation error for either row
      (no `no matching Markdown block` error  -  this pins that the chosen
      mechanism does not double-report already-errored rows). Run → expect
      RED (the false
      `severity disagrees` fires today; probed shape per backlog r6 item).
      Then suppress the per-id conservation comparison for ids the duplicate
      gate already flagged  -  this suppression mechanism is prescribed; do NOT
      key the reconciliation by `(id, severity)` (that alternative produces
      the no-matching-block double-report the fixture pins against). Record
      the mechanism in the commit message. Run → expect GREEN.
- [x] Run → expect GREEN: full `--selftest` exits 0.
- [x] Commit: `fix: stop cross-severity duplicate ids from falsely disagreeing on severity; simplify v1 fixtures`

### Task 5: Fence-scanner round 2

Files:
- `scripts/validate_review_staging.py`

- [x] Extract the shared `## Findings` section-extraction prelude (the
      `re.search(r"^## Findings\s*$", ...)` + `## `-split) from
      `split_finding_blocks` and `parse_markdown_findings` into one helper
      placed beside `classify_with_fallback` (returns the findings section
      string, or `None` when the heading is absent); both consumers call it.
- [x] Add the unclosed-opener warning to `parse_markdown_findings`: when the
      fallback branch runs (`unclosed_opener is not None`), emit a stderr
      warning naming the 1-based opener line number counted within the
      Findings section (the classifier's own `splitlines` indexing basis, so
      the number is stable regardless of where `## Findings` sits in the
      file) and that post-opener
      metadata bullets are not recovered (once per `parse_markdown_findings`
      call; a full hard run may legitimately print it once per consumer
      call). Characterization check with label
      containing `unclosed fence warning`: given a findings section whose last
      fence never closes, expects the warning on stderr for a single
      `parse_markdown_findings` invocation AND the r6 F3 recovery
      behavior unchanged (same parsed findings as before this task  -  assert a
      blocking finding after the opener is still recovered via the existing
      r4 F3 fixture shape).
- [x] Change `classify_with_fallback` to return
      `events[:unclosed_opener]` as the first element in the fallback case
      (the pre-opener prefix; the all-closed case still returns the full list
      with `unclosed_opener = None`), and drop both consumers' defensive
      truncation/filter (`boundaries = [i for i in boundaries if i <
      unclosed_opener]` and `apply_events(events[:unclosed_opener], ...)`
      become plain `apply_events(events, ...)`; likewise in
      `split_finding_blocks`). Update the helper docstring to state the new
      contract WITHOUT quoting the gated literals verbatim (do not write the
      bare slice `events[:unclosed_opener]` or the Findings regex into the
      docstring/comments  -  the Validation Commands count gates match those
      exact strings and a verbatim quote would break them; paraphrase
      instead). Run → expect GREEN (the fence-classifier selftest family
      characterizes both consumers).
- [x] Run → expect GREEN: full `--selftest` exits 0, and the Validation
      Commands block passes in full (single prelude definition, no remaining
      consumer-side truncation).
- [x] Commit: `refactor: shared Findings prelude helper, unclosed-fence warning, prefix-returning fallback`
