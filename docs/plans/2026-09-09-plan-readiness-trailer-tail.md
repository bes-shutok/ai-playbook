# Plan: plan_readiness trailer-tail and Review Scope hardening (7 backlog items)

Backlog origin (scope of record; items stay in place until completion):
- `docs/history/backlog/2026-09-09-plan-readiness-deduplicate-date-guards.md`
- `docs/history/backlog/2026-09-09-plan-readiness-scope-category-label-grammar.md`
- `docs/history/backlog/2026-09-09-plan-readiness-scope-token-heuristic-tail.md`
- `docs/history/backlog/2026-09-09-plans-trailer-date-pointer-rewrite.md`
- `docs/history/backlog/2026-09-09-trailer-gate-plan-r5-base-sha-scratch.md`
- `docs/history/backlog/2026-09-09-trailer-gate-meta-guard-witness.md`
- `docs/history/backlog/2026-09-09-trailer-gate-tilde-side-arm-coverage.md`

Reviews: `docs/reviews/2026-09-09-plan-review-plan-readiness-trailer-tail-r*.md`

## Terms

- **Arm**: one row of a selftest fixture table (`selftest#decision_marker/*`
  or `selftest#review_scope/*`); a fail-arm asserts the gate rejects the
  fixture, a pass-arm asserts it passes.
- **Gated probe**: the forward-looking steps 6 and 7 of
  `evaluate_readiness` (trailer gate, Review Scope gate), which run only
  when the latest review round's sidecar date is well-formed and at or
  above the probe's minimum date.
- **Sidecar**: the `.stats.json` companion of a review artifact; its
  `date` field drives both gated probes.
- **Scratch**: a file under `docs/tmp/` used for baselines and probes;
  never committed.
- **Latch**: a per-task-section flag that lets only the first `Files:`
  block open collection (r3 F3).

## Assumptions

- assume the trailer-gate r5-deferrals plan of record lives at
  `docs/plans/completed/2026-09-09-plan-readiness-trailer-gate-r5-deferrals.md`
  (post-archive path); the base-sha backlog item's scope line names the
  pre-archive `docs/plans/` path, but the file moved at execution; basis:
  on-disk listing and the meta-guard item's plan-of-record line.
- assume this plan satisfies both NEW items' owner-window disposition
  ("land in the next plan touching the `_selftest_decision_marker`
  arms-table family"); basis: both items' disposition constraints and this
  plan's task set.
- assume the built-in selftest families are the only test layer for
  `scripts/plan_readiness.py` (no dedicated pytest file exists); basis:
  `scripts/` inventory.
- assume no arm-count literals are maintained anywhere ("the pins are the
  count of record"); the archived tooling-polish plan is NOT edited (its
  r4 record note is conditional on a revision that is not planned); basis:
  the token-tail item's r4 additions section.
- assume each fixture shape prescribed below behaves as stated today;
  every RED/GREEN expectation was probed against the working tree on
  2026-09-09 in the authoring session (probes ran the real
  `_review_scope_category_re`/token/collection functions,
  `review_scope_problem`, `decision_marker_problem` after
  `_strip_fences`, and both selftest modes).

Decision points requiring a grill: category-label grammar fix widens `_REVIEW_SCOPE_CATEGORY_RE` to accept a bold label followed by same-line prose, the item's first-listed candidate (standing pre-authorization, task prompt 2026-09-09, grammar task); F10 prose-item fix requires the backticked span to be the item's leading content before it wins, the item's first-listed candidate (standing pre-authorization, task prompt 2026-09-09, token task); F11 space-path fix keeps unbackticked items on the first-token rule with backticks as the convention for space-bearing paths, the item's recommended candidate (standing pre-authorization, task prompt 2026-09-09, collection task); r4 F2 phantom-token fix uses a path-shape predicate (contains `/` or a known suffix) at the collection site with no stop-set, a superset of the item's options (standing pre-authorization, task prompt 2026-09-09, collection task).

## Gist & Examples

Four code families in `scripts/plan_readiness.py` harden, two docs
sentences align with their owners.

**Gated-probe dedup (item 1).** Steps 6 and 7 of `evaluate_readiness`
repeat the same date guard (`re.fullmatch` + lexicographic minimum) and
the same reason wrapper once per probe. **Before (today):** the predicate
and the `(required for plans reviewed on or after ...)` suffix are
copy-pasted in two blocks; a third gated probe would copy them a third
time. **After (this plan):** one `_gate_fires(round_date, min_date)`
predicate and one `_gated_probe_reason(problem, min_date, round_no,
round_date)` wrapper; the shared decode stays conditional on at least one
gate firing, and new characterization arms pin both decode-sharing cases
(undecodable plan + exempt date passes; undecodable plan + gated date
fails with the decode reason).

**Review Scope grammar (item 2).** `_REVIEW_SCOPE_CATEGORY_RE` requires a
category label to end at `:**`, but the plans skill's own Review Scope
template writes `**Documentation:**` followed by guidance prose on the
same line. **Before:** a plan copying that template line opens no category
block, so a `src/service.py` listed under it escapes the category check
(probed: the template-prose label matches nothing today). **After:** the
grammar accepts a bold label followed by same-line prose, the items
belong to that block, and the misattributed implementation path is named
in the check (a) reason.

**Review Scope token tail (item 3).** Off-convention authoring shapes
currently fabricate phantom paths or escape collection: a prose item with
two backticked spans yields the first span as a false path (F10); an
uppercase `FILES:` opener is never collected while a second bare `Files:`
echo re-opens collection and harvests one-word note tokens (F11, r3 F3;
probed: a `#### Task` section's files leak into the preceding section's
tail or vanish entirely, and `- none` yields the phantom token `none`);
an annotation inside the backtick span attaches to the extracted path
(r3 F2); a backslash-separated path false-rejects inventory coverage
(probed reason: `task Files path scripts\service.py is omitted from the
Review Scope inventory`). **After:** only path-shaped tokens are
collected, only the first `Files:` block per task section opens,
`###`/`####` Task and Step headings are all scanned, the backticked span
wins only as leading content, a trailing parenthesized annotation inside
the span is stripped, and separators normalize to `/` at extraction.
Space-bearing paths stay a backtick convention (F11 candidate accepted).

**Meta-guards and tilde arms (items 6, 7).** The arms table's two
meta-guards raise `AssertionError(suffix)` with no clue which guard fired,
and no selftest row ever violates them, so weakening either guard flips
zero lines. **Before:** a firing traceback says only the arm suffix.
**After:** a `_validate_arm` helper raises distinct messages and two
malformed meta-rows assert each message fires; the guards' `-O` survival
is witnessed by a `python3 -O` selftest run in the validation block. The
three tilde-side parser invariants (shorter-run closer, indent-4 closer,
backtick-info opener) get the fail-arms their backtick-side twins already
have, each proven to flip red under its named regression.

**Docs pointers (items 4, 5).** The plans skill restates the concrete
trailer date `2026-09-08` that `DECISION_MARKER_MIN_DATE` owns (exactly
one occurrence today); the sentence tail becomes a pointer to the
constant. The archived trailer-gate plan's Task 4 scope check reconstructs
its base commit from prose; Task 1 gains the scratch recording of the
base sha and Task 4 consumes and deletes that file, the same pattern this
plan's own Task 1 and final task use.

## Evaluation Criteria

**Quality dimensions:**
- correctness: `python3 scripts/plan_readiness.py --selftest` exits 0 with
  `ALL PASS` in plain and `-O` modes; every new arm flips red under its
  named mutation probe during its task (each probe's failing set recorded
  in the task log, then restored).
- regression safety: arm-name preservation for both families shows zero
  removed names and exactly the declared additions.
- maintainability: steps 6/7 call the two shared helpers; exactly one
  fullmatch date predicate and one reason template remain in the file.
- docs consistency: the SKILL.md pointer span is present, the stale inline
  date is gone, and the archived plan's record/consume/delete scratch
  chain greps clean.

**Done when:**
- All tasks checked and the full Validation Commands block exits 0 from
  the repo root.

**Ship when:**
- Nothing beyond the repository: this plan ships entirely in-repo (no
  deploy, cross-team, or human-owned condition).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review
and fix if valid):

**Production code:**
- `scripts/plan_readiness.py`

**Tests:**
- none separate; the selftest families (`selftest#decision_marker/`,
  `selftest#review_scope/`) live inside `scripts/plan_readiness.py` and
  are covered by its listing above.

**Documentation:**
- `agents/skills/plans/SKILL.md`
- `docs/plans/completed/2026-09-09-plan-readiness-trailer-gate-r5-deferrals.md`

**Plan-related extension**; implementation and review may change files not
listed above. Treat a finding as in scope when it is **causally related to
this plan**: it implements or completes a plan task, fixes a regression
introduced by plan work, closes wiring or docs implied by an explicit
must-fix change, or contradicts a contract the plan changed. If the link
to the plan is weak or speculative, drop as out of scope with a one-line
reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/*.md`; reason: items move to
  `backlog_completed_dir` at plan completion and are never edited for
  content by tasks.
- `docs/plans/completed/2026-09-09-plan-authoring-tooling-polish.md`;
  reason: its Evaluation Criteria count note is conditional on a revision
  no task performs.
- `~/.ai-playbook/` runtime copies; reason: redeploy is a separate
  standing decision, not a plan task.
- every other skill, hook, and doc file; reason: no task names them.

## Design Invariants (CR Guard)

- r2-F2 decode sharing: plan bytes are decoded ONCE and ONLY when at
  least one gated probe fires; an undecodable plan whose round is
  date-exempt must not newly fail. The refactor task keeps this
  structurally and pins it with the two decode characterization arms.
- Meta-guards are explicit `raise AssertionError`, never bare `assert`,
  so they survive `python3 -O`; the negative witnesses assert the distinct
  message prefixes, which also detects a conversion back to bare `assert`
  (message lost) and the `-O` run detects stripping.
- Existing arm names are never removed or renamed (preservation checks);
  no arm-count literal is added anywhere ("the pins are the count of
  record").
- The Review Scope gate stays fail-closed for every conventioned shape;
  the items fixed here are the off-convention tail only. Known accepted
  tail after this plan: non-path-shaped tokens in Review Scope CATEGORY
  blocks are still tracked unfiltered (the item scopes the path-shape
  filter to task-Files collection); the widened category grammar admits
  any bold label with same-line prose as a block opener, so items under
  off-template prose labels join the duplicate check (a false duplicate
  there is visible and correctable, the accepted direction); and the
  r3-F1 polarity direction where a SLASHED scope entry covers a BARE
  task-Files token (scope `docs/` covering task `docs`) loses its
  task-side witness because bare non-path-shaped tokens are no longer
  collected from Files lists, while the surviving direction (a bare scope
  entry covering a slashed task token) gains a dedicated characterization
  arm in Task 6.
- Reasons emitted by the gated probes stay byte-identical; the wrapper
  reproduces the exact `(required for plans reviewed on or after MIN;
  latest round rN is dated DATE)` shape.

## Validation Commands

Run from the repository root. The block is segmented for staging:
`[A]` selftests, `[B]` arm-name preservation, `[C]` SKILL.md pins,
`[D]` archived-plan pins, `[E]` scope integrity. Interim gates run only
the segments whose inputs exist at that task point: every Run item in
every task runs segment `[A]` (BOTH selftest lines, plain and `-O`, even
where the item spells only one invocation and expects the same outcome
from both); Task 8 adds `[C]` (its edit makes `[C]` fire); Task 9 adds
`[D]` (its edit makes `[D]` fire); only Task 10 runs the full block
`[A]`-`[E]`,
after every task commit exists for `[E]` and both baseline files from
Task 1 exist for `[B]`. Running `[C]` before Task 8's edit, `[D]` before
Task 9's edit, `[B]` before Task 1, or `[E]` before all eight commits is
a staging error, not a plan defect.

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1

# [A] Full selftest, plain and -O (the -O run witnesses the explicit-raise guards)
python3 scripts/plan_readiness.py --selftest || { echo "selftest FAILED"; exit 1; }
python3 -O scripts/plan_readiness.py --selftest || { echo "-O selftest FAILED"; exit 1; }

# [B] Arm-name preservation: nothing removed, additions exactly as declared
python3 scripts/plan_readiness.py --selftest | grep -oE 'selftest#decision_marker/[A-Za-z0-9_/]+' | sort -u > docs/tmp/decision-marker-names.after
python3 scripts/plan_readiness.py --selftest | grep -oE 'selftest#review_scope/[A-Za-z0-9_/]+' | sort -u > docs/tmp/review-scope-names.after
if comm -23 docs/tmp/decision-marker-names.before docs/tmp/decision-marker-names.after | grep -q .; then echo "decision_marker arm name removed"; exit 1; fi
if comm -23 docs/tmp/review-scope-names.before docs/tmp/review-scope-names.after | grep -q .; then echo "review_scope arm name removed"; exit 1; fi
diff <(comm -13 docs/tmp/decision-marker-names.before docs/tmp/decision-marker-names.after | sed 's|^selftest#decision_marker/||' | sort) <(printf '%s\n' undecodable_plan_date_exempt_passes undecodable_plan_gated_fails meta_polarity_mismatch_raises meta_empty_needle_part_raises trailer_inside_tilde_short_close_fails trailer_after_indent_4_tilde_closer_stays_fenced trailer_inside_tilde_fence_with_backtick_info_fails | sort) || { echo "unexpected decision_marker additions"; exit 1; }
diff <(comm -13 docs/tmp/review-scope-names.before docs/tmp/review-scope-names.after | sed 's|^selftest#review_scope/||' | sort) <(printf '%s\n' template_prose_label_doc_under_documentation_ok template_prose_label_implementation_under_documentation uppercase_files_opener_collected second_files_block_latched step_heading_files_collected task4_heading_files_collected bare_none_files_item_not_phantom backticked_space_path_coverage_ok bare_scope_entry_covers_slashed_task_ok prose_two_spans_not_a_path in_tick_annotation_stripped windows_separator_coverage_ok | sort) || { echo "unexpected review_scope additions"; exit 1; }

# [C] SKILL.md trailer-date pointer (owned by DECISION_MARKER_MIN_DATE, not prose)
grep -q "see the DECISION_MARKER_MIN_DATE constant in scripts/plan_readiness.py" agents/skills/plans/SKILL.md || { echo "SKILL.md pointer sentence missing"; exit 1; }
if grep -q "dated on or after 2026-09-08" agents/skills/plans/SKILL.md; then echo "SKILL.md still restates the inline trailer date"; exit 1; fi

# [D] Archived trailer-gate plan: record, consume, delete scratch chain
grep -q "git rev-parse HEAD > docs/tmp/trailer-gate-base-sha.txt" docs/plans/completed/2026-09-09-plan-readiness-trailer-gate-r5-deferrals.md || { echo "archived plan Task 1 does not record the base sha"; exit 1; }
grep -q '"$(cat docs/tmp/trailer-gate-base-sha.txt)"..HEAD' docs/plans/completed/2026-09-09-plan-readiness-trailer-gate-r5-deferrals.md || { echo "archived plan Task 4 does not consume the base sha"; exit 1; }
grep -q '`docs/tmp/decision-marker-names.after`, `docs/tmp/trailer-gate-base-sha.txt`' docs/plans/completed/2026-09-09-plan-readiness-trailer-gate-r5-deferrals.md || { echo "archived plan cleanup item does not delete the base-sha scratch"; exit 1; }

# [E] Scope integrity: every commit this plan created touches only declared files
BASE="$(cat docs/tmp/plan-readiness-tail-base-sha.txt)"
if [ -z "$BASE" ]; then echo "base sha scratch missing"; exit 1; fi
for subj in \
  "test: distinct meta-guard messages with negative witnesses" \
  "test: add tilde-side fence selftest arms" \
  "refactor: deduplicate gated-probe date guards in evaluate_readiness" \
  "fix: accept bold-label-with-prose Review Scope category lines" \
  "fix: harden Review Scope Files collection against off-convention shapes" \
  "fix: path-shape gate and token normalization in Review Scope extraction" \
  "docs: point the trailer-date sentence at DECISION_MARKER_MIN_DATE" \
  "docs: record trailer-gate base-sha scratch in the archived plan"; do
  shas="$(git log --format=%H --fixed-strings --grep="$subj" "${BASE}..HEAD")"
  if [ -z "$shas" ]; then echo "commit missing: $subj"; exit 1; fi
  for sha in $shas; do
    git show --format= --name-only "$sha" | sort -u | while IFS= read -r f; do
      [ -z "$f" ] && continue
      case "$f" in
        scripts/plan_readiness.py|agents/skills/plans/SKILL.md|docs/plans/completed/2026-09-09-plan-readiness-trailer-gate-r5-deferrals.md) ;;
        *) echo "unexpected file $f in commit $sha"; exit 1 ;;
      esac
    done || { echo "scope leak in commit $sha"; exit 1; }
  done
done
```

### Task 1: Baselines and scratch (no behavior change)

Files:
- none new (scratch only; every file this task creates lives under
  `docs/tmp/` and is never committed)

- [ ] Record the base sha for the Task 10 scope-integrity check BEFORE any
  commit-affecting task: `git rev-parse HEAD > docs/tmp/plan-readiness-tail-base-sha.txt` (create the file; scratch only, never committed)
- [ ] Record the decision_marker arm-name baseline: `python3 scripts/plan_readiness.py --selftest | grep -oE 'selftest#decision_marker/[A-Za-z0-9_/]+' | sort -u > docs/tmp/decision-marker-names.before`
- [ ] Record the review_scope arm-name baseline: `python3 scripts/plan_readiness.py --selftest | grep -oE 'selftest#review_scope/[A-Za-z0-9_/]+' | sort -u > docs/tmp/review-scope-names.before`
- [ ] Run → expect GREEN baseline: `python3 scripts/plan_readiness.py --selftest` and `python3 -O scripts/plan_readiness.py --selftest` both `ALL PASS`, exit 0 (verified at authoring time, 2026-09-09)

### Task 2: Meta-guard helper, distinct messages, negative witnesses

Test-plus-refactor change in one commit; every step is green under the
current parser, so discrimination is proven by the mutation probes below,
not by a red run. This is the owner window both NEW items prescribe.

Files:
- `scripts/plan_readiness.py`

- [ ] Factor the two per-row guard statements out of the `_selftest_decision_marker` arms loop (today at the top of the loop body: the polarity `raise AssertionError(suffix)` and the needle-parts `raise AssertionError(suffix)`) into a module-level `def _validate_arm(suffix: str, needle: str | None, expect_ok: bool) -> None` placed directly above `_selftest_decision_marker`; the polarity guard raises `AssertionError(f"needle/expect_ok polarity mismatch: {suffix}")` and the needle-parts guard raises `AssertionError(f"empty needle part: {suffix}")`; both stay explicit raises (survive `python3 -O`); the loop calls `_validate_arm(suffix, needle, expect_ok)` as its first statement; keep the existing r5-F4/r1-F2/r2-F1 rationale comment with the helper
- [ ] Immediately after the standard arms loop in `_selftest_decision_marker`, add a negative-witness table `meta_arms: list[tuple[str, object, str]]` with two rows: `("meta_polarity_mismatch_raises", lambda: _validate_arm("meta_probe", None, False), "needle/expect_ok polarity mismatch")` and `("meta_empty_needle_part_raises", lambda: _validate_arm("meta_probe", "a| |b", False), "empty needle part")`; each row runs in `try`/`except AssertionError` capturing `str(exc)` (no exception captured means empty message), then `check(f"selftest#decision_marker/{name}", expected in message, f"message={message!r}")`
- [ ] Run → expect GREEN: `ALL PASS`, exit 0 (both new meta-rows green: they witness the current guards)
- [ ] Mutation probe 1: weaken the polarity guard (make its condition constant `False`), run the plain selftest, record that `selftest#decision_marker/meta_polarity_mismatch_raises` FAILS, restore
- [ ] Mutation probe 2: delete the needle-parts raise, run the plain selftest, record that `selftest#decision_marker/meta_empty_needle_part_raises` FAILS, restore
- [ ] Mutation probe 3: convert both guard raises back to bare `assert <cond>, suffix`, run `python3 -O scripts/plan_readiness.py --selftest`, record that BOTH meta-rows FAIL (stripped asserts raise nothing), and run the plain selftest, record that BOTH meta-rows also FAIL (the bare-assert message is the bare suffix, missing the distinct prefixes); restore
- [ ] Commit: `test: distinct meta-guard messages with negative witnesses`

### Task 3: Tilde-side fence selftest arms (r1 overflow F3/F4)

Test-only change; all three arms are fail-arms that are GREEN under the
current parser (probe verified 2026-09-09: each fixture returns
`missing decision-points trailer` after `_strip_fences`), so discrimination
is proven by the mutation probes below. Date is `2026-09-08` and needle is
`"missing decision-points trailer"` for all three; `trailer` is the
existing local `f-string` prefix variable.

Files:
- `scripts/plan_readiness.py`

- [ ] Add fail-arm `trailer_inside_tilde_short_close_fails` beside the backtick twin `trailer_inside_short_close_fails`: plan_text `"# P\n\n## Assumptions\n\nNone needed.\n\n~~~~\nquoted template\n~~~\n" + trailer + "none remain.\n~~~~\n"`; a 3-tilde line inside a 4-tilde fence is legal content, not a closer, so the real trailer after it stays swallowed
- [ ] Add fail-arm `trailer_after_indent_4_tilde_closer_stays_fenced` beside the backtick twin `trailer_after_indent_4_closer_stays_fenced`: plan_text `"# P\n\n## Assumptions\n\nNone needed.\n\n~~~~\nquoted template\n    ~~~\n" + trailer + "none remain.\n~~~~\n"`; a 4-space-indented tilde line is content (indent > 3 can never close), so the trailer stays swallowed
- [ ] Add fail-arm `trailer_inside_tilde_fence_with_backtick_info_fails` beside the r5-F8 backtick arm: plan_text `"# P\n\n## Assumptions\n\nNone needed.\n\n~~~x ``` styled\nquoted template\n" + trailer + "none remain.\n~~~\n"`; a tilde opener keeps accepting any info string (the r5-F8 backtick-info rejection must NOT apply to tilde openers), so the fence opens and swallows the trailer
- [ ] Run → expect GREEN: `ALL PASS`, exit 0 (three new arms green, all pre-existing arms green)
- [ ] Mutation probe 1: relax the closer run-length rule (`len(m.group(1)) >= fence[1]` to `len(m.group(1)) >= 3`), run the plain selftest, record the failing set and that it includes `trailer_inside_tilde_short_close_fails`, restore
- [ ] Mutation probe 2: drop the `lead <= 3` indent gate for closers, run the plain selftest, record the failing set and that it includes `trailer_after_indent_4_tilde_closer_stays_fenced`, restore
- [ ] Mutation probe 3: extend the r5-F8 backtick-info opener rejection to tilde openers, run the plain selftest, record the failing set and that it includes `trailer_inside_tilde_fence_with_backtick_info_fails`, restore
- [ ] Commit: `test: add tilde-side fence selftest arms`

### Task 4: Deduplicate the gated-probe date guards (decode-sharing pinned first)

Characterization arms land FIRST (both GREEN today: the decode-sharing
behavior exists and is pinned by comments only), then the refactor keeps
them green.

Files:
- `scripts/plan_readiness.py`

- [ ] In `_selftest_decision_marker` after the sidecar-arms loop, add a decode-arms table `decode_arms: list[tuple[str, object]] = [("undecodable_plan_date_exempt_passes", lambda s: s.pop("date")), ("undecodable_plan_gated_fails", lambda s: None)]`; per row: `_write_clean_state(..., plan_text="# P\n\nBody.\n", date="2026-09-08")`, load the sidecar JSON, apply the mutation, overwrite the plan bytes with `plan.write_bytes(b"\xff\xfe\x00 undecodable")`, refresh `sidecar["source_digest"] = vrs.compute_source_digest("plan", plan.read_bytes())` (both arms need a matching digest or the stale-digest reason masks the decode reason), write the sidecar back, evaluate; surface each row through the same `check` call shape the rest of the family uses, `check(f"selftest#decision_marker/{name}", <row assertion>, f"ok={ok} reason={reason}")`, so the arm names segment [B] greps are actually printed: the pass-row assertion is `ok and reason is None`, the fail-row assertion is `not ok and "cannot read plan bytes" in (reason or "")`; comment cites r2-F2 (decode only when at least one gate fires)
- [ ] Run → expect GREEN: `ALL PASS`, exit 0 (the two decode arms pin today's behavior)
- [ ] Refactor: add module-level `def _gate_fires(round_date: str, min_date: str) -> bool` returning `bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", round_date)) and round_date >= min_date`, and `def _gated_probe_reason(problem: str, min_date: str, round_no: int, round_date: str) -> str` returning `f"{problem} (required for plans reviewed on or after {min_date}; latest round r{round_no} is dated {round_date})"`, both placed directly above `evaluate_readiness`
- [ ] Rewrite steps 6/7 of `evaluate_readiness` to use them: `trailer_gated = _gate_fires(round_date, DECISION_MARKER_MIN_DATE)` and `scope_gated = _gate_fires(round_date, REVIEW_SCOPE_MIN_DATE)` replace the two duplicated fullmatch+comparison pairs, and both probe reason returns become `_gated_probe_reason(problem, <MIN_DATE constant>, round_no, round_date)`; the shared conditional decode block stays exactly as is (single decode, gated on `trailer_gated or scope_gated`); emitted reasons stay byte-identical
- [ ] Run → expect GREEN: `ALL PASS`, exit 0 (all arms including the decode pair; emitted reasons unchanged)
- [ ] Commit: `refactor: deduplicate gated-probe date guards in evaluate_readiness`

### Task 5: Review Scope category-label grammar accepts label-with-prose lines

RED then GREEN. Probe verified 2026-09-09: today the template-prose label
`**Documentation:** production code and tests use the explicit list`
matches `_REVIEW_SCOPE_CATEGORY_RE` as None (no block opens), so an
implementation path under it escapes check (a).

Files:
- `scripts/plan_readiness.py`

- [ ] Add RED fail-arm `template_prose_label_implementation_under_documentation` in `_selftest_review_scope` (fixture via the existing `rs_plan` helper, date `2026-09-09`): scope_body `"**Documentation:** production code and tests use the explicit list\n\n- src/service.py\n"`; expects `not ok` with a reason naming `src/service.py`, `Documentation`, and `Production code`
- [ ] Add characterization pass-arm `template_prose_label_doc_under_documentation_ok` (green before and after): scope_body `"**Documentation:** production code and tests use the explicit list\n\n- docs/guide.md\n"`; expects `ok and reason is None`
- [ ] Run → expect RED: exactly `template_prose_label_implementation_under_documentation` FAILS (today no block opens, the gate passes vacuously); the characterization arm and all pre-existing arms PASS
- [ ] Widen `_REVIEW_SCOPE_CATEGORY_RE` to `re.compile(r"^\*\*(.+?):\*\*[ \t]*(.*)$")` and update its comment: a bolded label line opens a category block with or without same-line guidance prose (the plans skill Review Scope template's own Documentation label carries prose); label handling (strip, out-of-scope exclusion) is unchanged and uses `group(1)` only
- [ ] Run → expect GREEN: `ALL PASS`, exit 0 (the prose label now opens a Documentation block: the implementation path is named by check (a), the doc path is authoritative)
- [ ] Commit: `fix: accept bold-label-with-prose Review Scope category lines`

### Task 6: Harden Review Scope Files collection (opener, latch, headings, phantom tokens)

RED then GREEN; every arm's fixture is spelled in full below and each
named shape was probed against the working tree on 2026-09-09 in the
authoring session (per shape: the uppercase opener is never collected, an
echo re-opens collection and harvests `word`, `### Step` and `#### Task`
sections are skipped or leak into the preceding tail, `- none` tokenizes
to the phantom `none`, and a backticked space path extracts whole).

Files:
- `scripts/plan_readiness.py`

- [ ] Add RED fail-arm `uppercase_files_opener_collected` (date `2026-09-09`): scope_body `"**Documentation:**\n\n- docs/guide.md\n"`, task section `### Task 1: X` with a `FILES:` (uppercase) block listing `- src/unlisted.py`; expects `not ok` with the omitted-from-inventory reason naming `src/unlisted.py` (today the block is never collected, so the gate passes vacuously)
- [ ] Add RED pass-arm `second_files_block_latched`: scope_body `"**Documentation:**\n\n- docs/guide.md\n"`, task with a real `Files:` block `- docs/guide.md`, then a `Notes: echo` line, then a bare `Files:` echo, then `- word`; expects `ok and reason is None` (today the echo re-opens collection and the phantom `word` fails the inventory check)
- [ ] Add RED fail-arm `step_heading_files_collected`: scope_body `"**Documentation:**\n\n- docs/guide.md\n"`, task section `### Step 1: X` with `Files:` listing `- src/unlisted.py`; expects the omitted-from-inventory reason (today `^### Task` skips Step headings entirely)
- [ ] Add RED fail-arm `task4_heading_files_collected`: scope_body `"**Documentation:**\n\n- docs/guide.md\n"`, task section `#### Task 1: X` with `Files:` listing `- src/unlisted.py` and NO `### Task` section anywhere in the fixture; expects the omitted-from-inventory reason (today nothing is scanned)
- [ ] Add RED pass-arm `bare_none_files_item_not_phantom`: scope_body `"**Documentation:**\n\n- docs/guide.md\n"`, task `Files:` listing `- docs/guide.md` and `- none`; expects `ok and reason is None` (today `none` tokenizes to a phantom path and false-rejects check (c))
- [ ] Add characterization pass-arm `backticked_space_path_coverage_ok` (green before and after): scope_body `"**Production code:**\n\n- \`my docs/white paper.md\`\n"`, task `Files:` listing `- \`my docs/white paper.md\``; expects `ok` (a backticked span carries spaces intact; backticks are the convention for space-bearing paths, so unbackticked multi-token payloads keep the first-token rule unchanged)
- [ ] Add characterization pass-arm `bare_scope_entry_covers_slashed_task_ok` (green before and after, r3-F1 surviving polarity witness): scope_body `"**Production code:**\n\n- scripts\n"`, task `Files:` listing `- scripts/`; expects `ok and reason is None` (a bare scope entry covers a slashed task token; GREEN today, probed; pins the coverage direction that survives Task 6's path-shape filter, whose lost mirror direction is recorded in Design Invariants)
- [ ] Run → expect RED: exactly the five new RED arms FAIL; `backticked_space_path_coverage_ok`, `bare_scope_entry_covers_slashed_task_ok`, and all pre-existing arms PASS
- [ ] GREEN, collection side of `_review_scope_task_files`: replace the `line.startswith("Files:")` branch with a case-insensitive opener (`re.match(r"files:", line, re.IGNORECASE)`) guarded by a per-section `seen_files_block` latch initialized `False` beside `collecting`: an empty-payload opener fires only when not yet latched (then `seen_files_block = True; collecting = True`), any other `files:` line (already latched, or carrying an inline payload such as `Files: none new (...)`) leaves collection closed via `collecting = False` and `continue` (a payload-bearing first line is prose and must NOT latch, so a later real opener still works); update the docstring (case-insensitive opener, first-block latch r3 F3)
- [ ] GREEN, heading variants: change the section scan to `re.finditer(r"^#{3,4} (?:Task|Step).*$", stripped, re.MULTILINE)` and the section-boundary split to `re.split(r"\n#{2,4} ", ..., maxsplit=1)` in the SAME commit (the split must break at `#### ` once such headings are scanned, or a `####` task's files leak into the preceding section's tail); update the docstring (Task and Step, `###` and `####`)
- [ ] GREEN, phantom tokens: in the collection branch, append the token only when it is path-shaped: `"/" in token or token.lower().endswith(REVIEW_SCOPE_DOC_SUFFIXES + REVIEW_SCOPE_IMPLEMENTATION_SUFFIXES)`; add a one-line comment citing r4 F2 (bare `- none` items must not fabricate paths); the filter lives at the collection site per the backlog item, NOT inside `_review_scope_path_token`, so Review Scope category-block parsing keeps today's token behavior
- [ ] Run → expect GREEN: `ALL PASS`, exit 0 (the five arms flip green; the uppercase, echo, heading-variant, and phantom shapes are now fail-closed)
- [ ] Commit: `fix: harden Review Scope Files collection against off-convention shapes`

### Task 7: Token extraction: leading-span rule, annotation strip, separator normalization

RED then GREEN; all expectations probed 2026-09-09.

Files:
- `scripts/plan_readiness.py`

- [ ] Add RED pass-arm `prose_two_spans_not_a_path` (date `2026-09-09`): scope_body `"**Documentation:**\n\n- docs/guide.md\n"` (the scope text must NOT mention `docs/a.md` or `docs/b.md` anywhere, or the raw-text boundary fallback masks the RED), task `Files:` listing only the prose item `- see \`docs/a.md\` and also \`docs/b.md\``; expects `ok and reason is None` (today the first backticked span `docs/a.md` wins as a false path and fails the inventory check, probed reason text)
- [ ] Add RED pass-arm `in_tick_annotation_stripped`: scope_body `"**Production code:**\n\n- src/service.py\n"` (the label is pinned so check (a) stays silent and the arm exercises check (c), probed both ways), task `Files:` listing `- \`src/service.py (new; this plan)\``; expects `ok and reason is None` (today the annotation stays attached and the omitted-from-inventory reason fires, probed)
- [ ] Add RED pass-arm `windows_separator_coverage_ok`: scope_body `"**Production code:**\n\n- scripts/\n"`, task `Files:` listing `- scripts\service.py`; expects `ok and reason is None` (today the backslash path is omitted from the inventory, probe-verified reason text)
- [ ] Run → expect RED: exactly the three new arms FAIL; all pre-existing arms PASS (including the annotated leading-span arms)
- [ ] GREEN in `_review_scope_path_token`: the backticked span wins only when it is the item's leading content (`item.lstrip().startswith("`")`), else fall through to the existing backtick-stripped delimited-token rule; strip a trailing parenthesized annotation inside the winning span (`re.sub(r"\s*\([^()]*\)\s*$", "", span).strip()`, r3 F2); normalize separators at extraction for BOTH branches (`token.replace("\\", "/")`) so every downstream comparison sees one form (r3 overflow Windows-separator drift); keep the `./` strip; rewrite the docstring to state the leading-span rule, the annotation strip, and the normalization (today it documents first-span-wins unconditionally)
- [ ] Run → expect GREEN: `ALL PASS`, exit 0 (prose items contribute no path, annotated spans extract bare, backslash paths cover under slash scope entries)
- [ ] Commit: `fix: path-shape gate and token normalization in Review Scope extraction`

### Task 8: plans SKILL.md trailer-date pointer rewrite

Docs-only change. The sentence at `agents/skills/plans/SKILL.md` line 364
is the file's ONLY restatement of the concrete trailer date (grep count 1
verified 2026-09-09); the constant name does not appear in the file yet.

Files:
- `agents/skills/plans/SKILL.md`

- [ ] Rewrite the sentence tail `and plan_readiness.py enforces the trailer for plans whose latest review round's sidecar date field is dated on or after 2026-09-08.` to `and plan_readiness.py enforces the trailer under the sidecar-date rule (see the DECISION_MARKER_MIN_DATE constant in scripts/plan_readiness.py for the exact date and exemption semantics).`; no other line in the file changes
- [ ] Run Validation Commands segments [A] and [C] → expect exit 0 (segment [C] fires for the first time: the pointer pin passes and the stale-date sweep is clean; both selftest modes green)
- [ ] Commit: `docs: point the trailer-date sentence at DECISION_MARKER_MIN_DATE`

### Task 9: Archived trailer-gate plan records and consumes its base sha

Docs-only change to the executed plan of record at its post-archive path
(checkboxes stay `[x]`; only item text is amended). The scratch file
`docs/tmp/trailer-gate-base-sha.txt` itself is history-neutral: the
executed run is over, the edit makes the recorded procedure
self-consistent for any future reader.

Files:
- `docs/plans/completed/2026-09-09-plan-readiness-trailer-gate-r5-deferrals.md`

- [ ] Amend Task 1's first checklist item (the baseline-recording item, which already writes `docs/tmp/decision-marker-names.before`) to ALSO record the base commit before the first commit-affecting item, appending to that item's text: `and record the base commit for the Task 4 scope check: git rev-parse HEAD > docs/tmp/trailer-gate-base-sha.txt`
- [ ] Amend Task 4's scope-check item: replace the trailing prose `(base is the commit current when Task 1 started)` with `over the base recorded by Task 1: git log --name-only "$(cat docs/tmp/trailer-gate-base-sha.txt)"..HEAD`
- [ ] Amend Task 4's cleanup item to include the scratch file, so its deletion list reads `docs/tmp/decision-marker-names.before`, `docs/tmp/decision-marker-names.after`, `docs/tmp/trailer-gate-base-sha.txt`, and any replay-probe scratch
- [ ] Run Validation Commands segments [A] and [D] → expect exit 0 (segment [D] fires for the first time: all three archived-plan pins pass, including the backtick-adjacency cleanup pin; both selftest modes green)
- [ ] Commit: `docs: record trailer-gate base-sha scratch in the archived plan`

### Task 10: Final validation and scratch cleanup

Files:
- none (validation and scratch cleanup only)

- [ ] Run the full Validation Commands block, segments [A] through [E], from the repository root → expect exit 0: both selftest modes `ALL PASS`, both preservation checks clean with exactly the declared additions (7 decision_marker, 12 review_scope), SKILL.md pointer pinned and stale date gone, archived-plan chain pinned, and every commit this plan created touching only the three declared files
- [ ] Confirm the mutation-probe records exist in the task log for every probe of Tasks 2 and 3 (each probe's failing set includes the named arm)
- [ ] Delete the scratch files `docs/tmp/plan-readiness-tail-base-sha.txt`, `docs/tmp/decision-marker-names.before`, `docs/tmp/decision-marker-names.after`, `docs/tmp/review-scope-names.before`, `docs/tmp/review-scope-names.after`, and the requirements buffer `docs/tmp/plan-requirements-plan-readiness-trailer-tail.md`
