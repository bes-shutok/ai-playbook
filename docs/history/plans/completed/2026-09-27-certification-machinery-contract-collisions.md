# Plan: certification-machinery contract collisions

Backlog origins (scope of record):
- docs/history/backlog/2026-09-26-at-cap-finalization-done-gate-collision.md (anchor)
- docs/history/backlog/2026-09-20-selection-empty-digest-exit-code-corpus-dependence.md
- docs/history/backlog/2026-09-26-shadow-plan-reconcile-rows-migration-audit-marker.md

Driving force: new-capability
Force justification: not one of the four driving principles; implemented anyway because the missing at-cap terminal shape strands operator-authorized, finalized plans unlandable and pressures orchestrators to exceed their round cap (witnessed 2026-09-26, per the anchor origin's environment record); park-triage would take it: the collision blocks the done landing path on every authoring run whose cap round is not clean, a recurring lifecycle failure rather than speculative polish.
Plan review record: the staging series docs/reviews/2026-09-27-plan-review-certification-machinery-contract-collisions-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Give the plan certification machinery one mechanically expressible at-cap terminal shape, a corpus-independent usage-error exit order in the review-record selector, and a registry marker the origins-checker consult can resolve, so three standing contract collisions stop blocking landings and scans.

- A plan closed at its configured review-round cap under the authorizing directive's finalize-with-residuals rule passes the done plan-readiness gate: the gate accepts the declared cap-closure record, bound to a residual-findings section in the plan bytes, when no blocking finding stays unresolved.
- A caller that supplies an invalid --source-digest to the review-record selector always gets the usage-error exit (2), regardless of unrelated record-corpus state such as an orphaned record half.
- The origins-checker registry consult resolves the six origins reconciled by the docs-branch shadow plan's completed-corpus deletion, so the corpus scan stops warning on them, while the two genuine straggler warns keep firing.

## Terms

- **cap closure**: the operator-authorized terminal state of a plan review loop that reached its configured round cap without a clean round; declared by an `extensions.cap_closure` object in the cap round's stats sidecar and by a `## Residual findings (cap closure)` section in the plan bytes.
- **residual finding**: a review finding present at the cap round recorded in the cap-closure section with its disposition; each is listed with its post-finalize disposition, `folded` (fixed in the cap-closure fold) or `accepted` (left unfixed), and the declaration's `residuals` field counts the `accepted` entries.
- **origins-checker registry consult**: the arm of `scripts/check_plan_origins_closed.py` that resolves a plan's deleted origins when the matching document-registry row carries both the `user-approved` token and the `migration audit` marker.
- **selection usage error**: a `select_record` refusal caused purely by invalid invocation input (slug grammar, slug length, backup infix, digest presence, digest grammar); always exit 2, knowable without reading the record corpus.

## Assumptions

- assume candidate (a) of the anchor origin: the gate learns a recorded residual-finalization state (a plan section referenced by the sidecar), not candidate (b) (require clean-at-cap plus the recorded-stop path) or candidate (c) (a new review-plan staging verdict shape); basis: the standing pre-authorization to accept the recommended option in the 2026-09-27 authoring directive, plus mechanism fit: the directive already orders residual findings recorded in the plan, so the section keeps the durable artifact authoritative while the sidecar extension carries the machine-readable reference; candidate (b) discards an operator-authorized escape path and stretches recorded-stop to a situation it does not match, and candidate (c) adds a third verdict value to a two-value contract consumed by several gates.
- assume the cap round's sidecar verdict field keeps the round's honest value (`no` when the round staged findings); the gate accepts the composite (verdict `no` + conforming `extensions.cap_closure` + section present in the plan bytes + zero unresolved blocking findings) and never rewrites or relaxes the verdict field itself; basis: the verdict field is the panel's honest record and the extension exists precisely to explain why a `no` is terminal.
- assume the digest re-bind is sanctioned only under a cap-closure declaration: finalizing at cap edits the plan after the last round, so the cap-closure finalize step recomputes and rewrites the final sidecar's `source_digest` to the post-fold plan bytes; every other post-round plan edit keeps failing as a stale digest; basis: the shared schema gate stays the single digest authority and the binding must hold at done time.
- assume no current test pins orphan-refusal-over-usage-error precedence in `select_record`; basis: authoring-time read of `scripts/test_review_record_selection.py`: `test_select_refuses_orphan_half` passes a valid digest and `test_select_rejects_empty_source_digest` runs on an empty corpus, so the reorder breaks no existing expectation.
- assume the registry edit is a cell-content edit on the existing reconcile row (the `done-sweep-residuals-and-stale-origin-dispositions` row, `user-approved 2026-09-25: fold-then-delete reconcile` notes cell) and no other row, column, or format element moves; basis: authoring-time read of `docs/maintenance/document-registry.md` and the established `migration audit` idiom on adjacent rows.

- assume the re-bind scope and verdict-field integrity at finalize are producer-side discipline with no mechanical enforcement; the residual accepted is that no mechanical witness exists for cap-reached, fold scope, and residual accounting, not "ceremony only": unlike the ordinary ready=yes arm, whose digest binding enforces that landed bytes equal the bytes a round reviewed, the cap-closure arm lands bytes no round reviewed, so the sanctioned re-bind waives exactly the guarantee the ordinary arm enforces; basis: the validator checks declaration shape, not edit diffs, and no cross-round verdict-consistency check exists; mitigation: the Task 2 texts state the producer-side sidecar edit scope (the folded findings' triage marks plus the `source_digest` re-bind; the verdict field is never edited), the gate cross-checks every staged finding pattern against the residual section body with dispositions, and the declaration's `pre_fold_digest` field keeps the pre-fold bytes recoverable for post-hoc audit.
- assume cap-reached is assertion-only and not mechanically verifiable by the gate: the configured cap lives in directive and skill prose, not machine-readable config, so the composite relies on producer-side discipline; basis: authoring-time analysis of the composite (the extension `round` conjunct equals the sidecar's own round and evidences nothing about the configured cap); mitigation: the Task 2 discipline wording makes an earlier-round declaration a falsified certification.
- assume the substance of each recorded disposition stays producer-asserted: the gate cross-checks the mechanically checkable part (every finding pattern in the final sidecar's findings array appears in the section body with a disposition, and a declaration claiming `residuals: 0` with an empty body passes only when the round genuinely staged zero findings), but whether a disposition truthfully describes the fold is not verifiable; accepted because blocking findings stay gated by is_review_ready and the round's staged findings remain durably recorded in the review Markdown and the sidecar findings array, so the delta is a wrong ceremony record, not lost gating; basis: no mechanical witness exists for disposition truthfulness; mitigation: the disposition-accounting, empty-body, and zero-residual witness tests pin the conjunct's shape.

Decision points requiring a grill: at-cap terminal shape = candidate (a), a plan section referenced by a conforming sidecar extension plus gate acceptance of that composite; source: anchor origin candidate list resolved by the standing pre-authorization in the 2026-09-27 authoring directive; date: 2026-09-27; affects: Assumptions, Gist & Examples, Tasks 1 and 2.

## Gist & Examples

TLDR: the done plan-readiness gate learns an operator-authorized cap-closure terminal shape, the review-record selector's exit taxonomy stops depending on corpus state, and the origins-checker consult gains one registry marker, because three certification-machinery contracts currently collide with recorded state.

### Collision 1: cap finalization versus the readiness gate

The standing authoring directive caps plan-review rounds and orders, at the cap, finalizing with the best available draft and recording residual findings in the plan. The done plan-readiness gate independently requires the latest review round to report `ready=yes` with zero unresolved blocking findings, and its only bypass is recorded-stop, which means the user chose to stop without finalization. When the cap round is not clean, the two orders collide: the directive commands a finalization the gate mechanically refuses, no further round is permitted, and the run strands.

After this plan: at the cap without a clean round, the loop closes through the cap-closure terminal shape. The orchestrator folds accepted blocking findings and marks every folded staged finding resolved on BOTH record surfaces (the review Markdown `- **Triage**:` bullet and the matching sidecar `findings[].triage`, carrying the same resolved-triage value on both per the finding-conservation triage-agreement arm, using the resolved vocabulary `fixed`, `dropped`, or `done`, never the residual-section words `folded`/`accepted`), records every staged finding of the cap round with its disposition (`folded` or `accepted`) in the plan section `## Residual findings (cap closure)`, re-binds the final sidecar's `source_digest` to the post-fold plan bytes, and declares `extensions.cap_closure` in that sidecar. `evaluate_readiness` accepts exactly that composite as the explicit operator-authorized terminal state; a `ready=no` without the declaration, a malformed declaration, a stale digest, or an unresolved blocking finding all still fail with today's named reasons, and a declaration without a real residual section (missing heading, quoted or misleveled mention, or empty body under a nonzero count) fails with its own missing-terminal-state reason.

Example: six rounds run, the sixth stages findings that are all folded, their dispositions recorded; today the done gate refuses and the worktree strands. After: the sixth sidecar carries `extensions.cap_closure`, the plan carries the section, the digest is re-bound, the gate passes, the plan lands.

### Collision 2: exit code depends on corpus state

In `scripts/review_record_selection.py`, `select_record` runs the record enumeration and the orphan-half refusal before the empty-digest and digest-grammar usage checks. When the corpus holds an orphan half matching the slug, an invocation that also supplies an empty or malformed `--source-digest` exits 1 with the orphan message instead of exiting 2 with the digest message: the same caller mistake surfaces with a different exit code and diagnosis depending on unrelated corpus state. Both orders fail closed; only the taxonomy is nondeterministic.

After this plan: every exit-2 usage error is decided before any record-corpus state is consulted, so the same invalid input produces the same exit code and message everywhere.

Example: `select --slug demo --source-digest ""` over a corpus with an orphan `demo` sidecar today exits 1 naming the orphan; after, it exits 2 naming `--source-digest`, exactly as on a clean corpus.

### Collision 3: the consult cannot resolve six resolved origins

The `done-sweep-residuals-and-stale-origin-dispositions` registry row records the fold-then-delete reconcile that executed the docs-branch shadow plan's completed-corpus deletion and carries `user-approved`, but not the `migration audit` marker, so the origins-checker registry consult cannot resolve those six origins and every corpus scan still warns on all six.

After this plan: the marker is appended to that row's notes cell (cell-content edit, matching the sibling-row idiom), the six warns resolve, and the two genuine straggler warns (`2026-09-25-rearm-form-field-writer-attribution.md`, `2026-09-25-stale-branch-diff-restaging-reverse-squash-guard.md`) still fire.

## Evaluation Criteria

**Quality dimensions:**

- correctness: every direction of the new cap-closure rule has a failing-test witness: the accept arm plus five bypass arms (section missing, declaration missing, malformed declaration, unresolved blocking, stale digest) plus a quoted-or-misleveled-mention witness, an empty-section-body witness (no non-blank line before the next level-2 heading or end of file), a first-occurrence-governs witness (a second conforming heading with a non-blank body never rescues an empty first section), a zero-residual exempt-arm witness, a versionless-carrier witness, a disposition-accounting witness (staged sidecar finding patterns absent from the section body fail with the dedicated reason), `pre_fold_digest` rejection arms (missing, non-hex64, equal-to-`source_digest`) with the accept arm carrying the field, an int-declaration acceptance arm, and an unaffected arm (ordinary `ready=yes` sidecar); the exit-order gate asserts the full ordering, not mere presence.
- determinism: the same invalid `--source-digest` produces exit 2 with the same message over an orphan corpus and over a clean corpus (precedence canary).
- documentation coherence: the four contract surfaces (plans, done, review-plan, execute-plan) describe the same shape in the same change, and the review-plan integration point stops over-claiming that every `ready=no` fails the gates.
- minimal diff: the registry edit changes one notes cell's content on one row; no other row, column, or format element moves.

**Done when:**

- every suite and gate in Validation Commands exits 0;
- the origins-checker consult gate shows the six `done-sweep-residuals` origin warns resolved and the two genuine straggler warns firing;
- the pre-round structural gate passes over the plan bytes (`scripts/plan_readiness.py --pre-round`).

**Ship when:**

- Nothing; every closure condition in this plan is repository-verifiable. No deploy, cross-team, or human-owned step exists.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `scripts/plan_readiness.py`
- `scripts/validate_review_staging.py`
- `scripts/review_record_selection.py`
- `docs/maintenance/document-registry.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-staging/SKILL.md`

**Tests:**

- `scripts/test_plan_readiness.py`
- `scripts/test_review_record_selection.py`

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `docs/history/backlog/2026-09-26-at-cap-finalization-done-gate-collision.md` and the two sibling origin files; reason: scope of record consumed by this plan; the plans lifecycle folds and deletes them at completion, no execution task edits them.
- `scripts/check_plan_origins_closed.py`; reason: read-only consult consumer; this plan changes registry data the consult reads, not the checker; a checker defect is a separate ticket.
- `scripts/test_execute_plan_runtime.py`; reason: executed by validation only, never edited.
- `scripts/test_check_plan_origins_closed.py`; reason: executed by validation only, never edited.
- `scripts/test_execute_plan_address_fanout.py`; reason: executed by validation only, never edited.

## Validation Commands

Authoring-time record (worktree at main 6ba02da6, 2026-09-27): baseline suites green (`test_plan_readiness`, `test_review_record_selection`, `test_check_plan_origins_closed`, `test_execute_plan_address_fanout`, `ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral`); the Task 2 presence gates are RED today (literals absent from the five skill files); the Task 3 ordering gate is RED today (the empty-digest check sits below the enumeration call); the Task 4 consult gate is RED today (the six warns fire); the registry simulation (marker edit applied, checker run, edit reverted) resolved the seven warn lines covering the six named origins (including the archived-plan warn citing `2026-09-22-plans-watcher-schedule-fresh-state-cas-stale.md`); the two named stragglers still fire; corpus-wide totals drift with unrelated landings and are re-measured at task points; `bash -n` over this block is clean; the em-dash scan, hygiene scan, and the pre-round structural gate pass over these plan bytes. Before execution these authoring-time records are context; the gates below are re-run at their task points and at the end.

```bash
# Anchor every check to the repository root: scripts that resolve scan
# roots from the invocation cwd must run from the top level.
cd "$(git rev-parse --show-toplevel)" || exit 1

expect_present() {
    pattern="$1"; file="$2"
    rc=0; grep -qF "$pattern" "$file" 2>/dev/null || rc=$?
    if [ "$rc" -ne 0 ]; then echo "FAIL: missing in $file: $pattern (rc=$rc)"; exit 1; fi
}
expect_absent() {
    pattern="$1"; file="$2"
    rc=0; grep -qF "$pattern" "$file" 2>/dev/null || rc=$?
    if [ "$rc" -eq 0 ]; then echo "FAIL: forbidden match in $file: $pattern"; exit 1; fi
    if [ "$rc" -ge 2 ]; then echo "FAIL: grep error rc=$rc for $pattern"; exit 1; fi
}

# Task 1: cap-closure contract validator and gate acceptance, both directions.
PYTHONPATH=scripts python3 -m unittest scripts.test_plan_readiness -v || exit 1
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_address_fanout || exit 1

# Task 2: the contract surfaces carry the terminal-shape literals
# (dedicated gate per file: the obligation is per-file, so a multi-file
# grep union would not do).
expect_present 'extensions.cap_closure' agents/skills/plans/SKILL.md
expect_present 'Residual findings (cap closure)' agents/skills/plans/SKILL.md
expect_present 'extensions.cap_closure' agents/skills/done/SKILL.md
expect_present 'Residual findings (cap closure)' agents/skills/done/SKILL.md
expect_present 'extensions.cap_closure' agents/skills/review-plan/SKILL.md
expect_present 'Residual findings (cap closure)' agents/skills/review-plan/SKILL.md
expect_present 'extensions.cap_closure' agents/skills/execute-plan/SKILL.md
expect_present 'Residual findings (cap closure)' agents/skills/execute-plan/SKILL.md
expect_present 'Cap-closure sidecar extension' agents/skills/review-staging/SKILL.md
expect_present 'sanctioned in-plan home for cap-round residual dispositions' agents/skills/plans/SKILL.md
expect_present 'stale-disposition findings about it stay valid' agents/skills/review-plan/SKILL.md
PYTHONPATH=scripts python3 -m unittest scripts.test_execute_plan_runtime.ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral || exit 1

# Task 3: every usage error is decided before any record-corpus state is
# consulted (full ordering, not presence).
PYTHONPATH=scripts python3 -m unittest scripts.test_review_record_selection -v || exit 1
python3 - <<'PY' || exit 1
from pathlib import Path
text = Path("scripts/review_record_selection.py").read_text(encoding="utf-8")
empty = text.index("if not source_digest.strip():")
grammar = text.index("if SOURCE_DIGEST_PATTERN.fullmatch(source_digest) is None:")
slug = text.index("if not SLUG_PATTERN.fullmatch(slug):")
enum = text.index("pairs, orphans, backups_ignored = _enumerate(")
assert empty < enum, "empty-digest usage check must precede enumeration"
assert grammar < enum, "digest-grammar usage check must precede enumeration"
assert slug < enum, "slug usage check must precede enumeration"
print("select_record exit-order gate: ok")
PY

# Task 4: the consult resolves the six reconciled origins; the two
# genuine stragglers still fire.
out="$(mktemp)"
python3 scripts/check_plan_origins_closed.py > "$out" 2>&1
check_rc=$?
if [ "$check_rc" -ne 0 ]; then cat "$out"; rm -f "$out"; echo "FAIL: origins checker exited $check_rc"; exit 1; fi
expect_absent 'origin 2026-09-24-done-session-isolation-r1-nonblocking-findings.md unresolved' "$out"
expect_absent 'origin 2026-09-24-plans-watcher-schedule-fresh-install-cas-block.md unresolved' "$out"
expect_absent 'origin 2026-09-22-plans-watcher-schedule-fresh-state-cas-stale.md unresolved' "$out"
expect_absent 'origin 2026-09-22-done-parallel-session-isolation.md unresolved' "$out"
expect_absent 'origin 2026-09-22-active-review-post-verification.md unresolved' "$out"
expect_absent 'origin 2026-09-23-execute-plan-immutable-scope-plan-drift.md unresolved' "$out"
expect_present 'origin 2026-09-25-rearm-form-field-writer-attribution.md unresolved' "$out"
expect_present 'origin 2026-09-25-stale-branch-diff-restaging-reverse-squash-guard.md unresolved' "$out"
rm -f "$out"
PYTHONPATH=scripts python3 -m unittest scripts.test_check_plan_origins_closed || exit 1

# Whole-plan mechanical gates. The end-state em-dash scan runs in paths
# mode over the task-touched files: on the clean post-commit tree the
# `touched` form scans zero files and cannot fail for landed text, while
# the `touched` form stays for mid-task passes while the edits are still
# uncommitted dirt.
bash scripts/check-no-em-dash.sh paths scripts/validate_review_staging.py scripts/plan_readiness.py scripts/test_plan_readiness.py scripts/review_record_selection.py scripts/test_review_record_selection.py agents/skills/plans/SKILL.md agents/skills/done/SKILL.md agents/skills/review-plan/SKILL.md agents/skills/execute-plan/SKILL.md agents/skills/review-staging/SKILL.md docs/maintenance/document-registry.md || exit 1
bash scripts/scan-public-hygiene.sh || exit 1
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-09-27-certification-machinery-contract-collisions.md || exit 1
```

### Task 1: cap-closure terminal shape in the staging validator and the readiness gate

Frozen except: in the readiness validator, the verdict arm inside `evaluate_readiness` (step 4, consuming the staging validator's section-literal constant via the existing `vrs` import), the single defensive decode hoisted beside the fence-balance consumption and its reuse by step 6, the module docstring's opening question, and a new module-level probe function beside `fence_balance_problem` in `scripts/plan_readiness.py`; in the staging validator, the new cap-closure contract validator, its single-owner section-literal constant, and its single wiring call beside the address-fanout wiring inside `_validate_stats_sidecar_gates` (the inner gate function the `validate_stats_sidecar` wrapper delegates to); in the readiness test module, new test classes appended while existing classes stay frozen; plus the sibling-compat constant line in each validator file (`EXPECTED_SIBLING_COMPAT_VERSION` / `COMPAT_VERSION`, bumped 2 to 3 in the same commit).

Files:
- `scripts/validate_review_staging.py`
- `scripts/plan_readiness.py`
- `scripts/test_plan_readiness.py`

Fixture recipe for every `CapClosureReadinessTest` arm: the sidecar is a full version-1 record carrying all `V1_REQUIRED_TOP_LEVEL_FIELDS` (nearest builder `vrs._version1_payload`, adapted: `review_type` and `source_kind` set to plan, `verdict: "no"`, `artifact_slug` and `round` matching the fixture plan slug and round grammar, `source_digest` bound to the fixture plan bytes, findings mirroring the review Markdown), and BOTH the sidecar `date` and the round record filename's leading date stay below the fences (`EXTENDED_SIDECAR_MIN_DATE` 2026-09-09 and `DECISION_MARKER_MIN_DATE` 2026-09-08) so the gated structural probes remain exempt: the staging validator's dual-key fence rejects a pre-fence sidecar date under a post-fence filename (the r2 F3 backdated-sidecar-date error), so a mixed-dating fixture fails step 3 permanently; the test file's existing versionless builders cannot construct these fixtures. Fixtures whose declaration is present carry the residual section in the plan bytes with a body listing every mirrored finding's pattern and a disposition (`folded` or `accepted`), so the disposition-accounting conjunct is satisfiable in every accept-derived arm. Accept-arm fixtures whose sidecar `findings` carry blocking rows also give each mirrored Markdown finding a resolved `- **Triage**: fixed` bullet and the same `triage` value on the sidecar row (step-5 `is_review_ready` and the finding-conservation triage-agreement arm both require it), so blocking findings in accept-derived arms are triage-resolved on both record surfaces.

- [x] `CapClosureContractTest#test_cap_closure_contract_rejects_malformed_declarations`; given a version-1 sidecar whose `extensions.cap_closure` misses a required key, carries an unknown key, uses a section string other than `## Residual findings (cap closure)`, carries a `round` that is neither an int nor a string, is a boolean, does not equal the sidecar `round` after string normalization (the v1 sidecar contract types `round` as string, for example `"r1"`, or integer), normalizes to a string that does not parse as an integer after stripping one optional leading `r` (the dedicated unparsable-round rejection below), or normalizes below `CAP_CLOSURE_MIN_ROUND` (the dedicated floor rejection below), carries a `residuals` that is not a non-negative int (booleans excluded), misses `pre_fold_digest`, carries a non-lowercase-hex64 `pre_fold_digest`, or carries a `pre_fold_digest` equal to the re-bound `source_digest`, expects the new `validate_cap_closure_contract` (called with the same `payload, validation, schema_class` idiom as `validate_address_fanout_contract`) to report the specific problem each time [class: REPOSITORY_TEST]
- [x] `CapClosureContractTest#test_cap_closure_contract_enforces_minimum_round_floor`; given a version-1 sidecar whose declaration `round` and sidecar `round` agree after string normalization but normalize below `CAP_CLOSURE_MIN_ROUND = 3` (for example `"2"`/`2`), expects `validate_cap_closure_contract` to report the dedicated floor rejection naming `extensions.cap_closure` (the integer parsed after stripping a leading `r`, since the sidecar `round` is dual-typed), and given the paired `"3"`/`3` fixture, expects no problem, pinning the floor boundary in both directions (the floor matches the loop's own reconciliation arithmetic, so no honest cap closure can precede round 3; it never claims the configured cap itself was verified) [class: REPOSITORY_TEST]
- [x] `CapClosureContractTest#test_cap_closure_contract_rejections_avoid_routed_substrings`; collect every problem `validate_cap_closure_contract` reports across all its rejection arms and assert none contains `source_digest`, `source_kind`, or `missing the required 'coverage' object`, pinning the negative-literal routing contract as a suite invariant instead of prose discipline [class: REPOSITORY_TEST]
- [x] `CapClosureContractTest#test_cap_closure_contract_accepts_int_typed_declaration_round`; given a version-1 sidecar whose `round` is the string `"5"` and whose declaration carries `"round": 5` (the integer), expects `validate_cap_closure_contract` to report no problem, the mirrored pairing of the string-declaration accept arm, pinning both-sides string normalization as load-bearing in both directions [class: REPOSITORY_TEST]
- [x] `CapClosureContractTest#test_cap_closure_contract_rejects_versionless_carrier`; given a versionless legacy payload carrying `extensions.cap_closure` (mirror the sibling's schema-version-removed case), called with a non-current `schema_class`, expects the named version-boundary error [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_accepts_cap_closure_terminal_shape`; given a latest round whose sidecar carries `verdict: "no"`, a conforming `extensions.cap_closure` whose `round` deliberately uses the paired-but-different type (sidecar `round` the integer `5`, declaration `"round": "5"`, proving string normalization is load-bearing), a `source_digest` re-bound to the current plan bytes, a `pre_fold_digest` carrying the pre-fold bytes' digest (lowercase hex64, different from the re-bound `source_digest`), zero unresolved blocking findings, and plan bytes carrying `## Residual findings (cap closure)`, expects `evaluate_readiness` to pass [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_cap_closure_without_plan_section`; given the accept-arm fixture with the section literal removed from the plan bytes, expects `evaluate_readiness` to fail naming the missing terminal state [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_verdict_no_without_cap_closure`; given a latest round with `verdict: "no"` and an extensions object carrying only `extensions.convergence` (no `cap_closure` key), expects `evaluate_readiness` to fail with today's verdict reason, unchanged, and to discriminate the key name (an any-extensions-key gate would wrongly pass) [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_cap_closure_heading_with_empty_body`; given the accept-arm fixture with the heading present, an empty section body, and `residuals: 2`, expects `evaluate_readiness` to fail with the dedicated reason naming the missing-or-empty terminal state and the declared residual count; the body scan follows `md_section` semantics: it stops at the next level-2 heading (md_section semantics) or end of file, so trailing text under a `###` sub-heading within the section counts as body text and satisfies the conjunct, and the empty-body failure means no non-blank line before the next level-2 heading or end of file [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_first_conforming_heading_governs`; given plan bytes that carry the prescribed heading with an empty body and then a second identical `## Residual findings (cap closure)` heading followed by a non-blank body, expects `evaluate_readiness` to fail naming the missing-or-empty terminal state (the first occurrence governs; a non-empty body under any later conforming heading never rescues an empty first section) [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_cap_closure_under_reporting_staged_findings`; given the accept-arm fixture whose sidecar `findings` array mirrors the round's staged findings but whose residual section body does not list their patterns with dispositions, expects `evaluate_readiness` to fail with the dedicated terminal-state reason (under-reporting; `residuals: 0` with an empty body passes only when the round genuinely staged zero findings) [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_pattern_listed_without_disposition`; given the accept-arm fixture whose residual section body contains every staged sidecar finding pattern but at least one pattern's list item carries neither `folded` nor `accepted`, expects `evaluate_readiness` to fail with the dedicated under-reporting reason, pinning the disposition check as per pattern (same list entry as the pattern), never section-wide [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_cap_closure_disposition_outside_accepted_vocabulary`; given the accept-arm fixture whose residual section body lists every staged pattern but marks one with `- disposition: deferred` and another with no disposition token at all, expects `evaluate_readiness` to fail with the same dedicated under-reporting reason; the test docstring cites the `folded`/`accepted` vocabulary as the pinned enum so the vocabulary and its witness cannot drift apart [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_residuals_count_mismatch`; given the accept-arm fixture adapted to `residuals: 0` with a body listing `accepted` entries (fails; the count must equal the accepted-entry tally) and, as the paired direction, `residuals: 2` with three `accepted` entries (fails), expects `evaluate_readiness` to fail with the dedicated terminal-state reason naming the count mismatch, pinning that the declared `residuals` count is tied to the dispositions the gate already parses [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_accepts_cap_closure_with_zero_residuals_and_empty_body`; given the accept-arm fixture adapted to a genuinely finding-free round (the sidecar `findings` array empty and the review Markdown carrying no findings), with `residuals: 0` and an empty section body, expects `evaluate_readiness` to pass (RED today via the verdict reason) [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_cap_closure_only_as_quoted_or_misleveled_mention`; given the accept-arm fixture whose plan bytes mention `## Residual findings (cap closure)` only inside a fenced code block and as a `###` heading, expects `evaluate_readiness` to still fail naming the missing terminal state [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_cap_closure_with_unresolved_blocking`; given the accept-arm fixture with one blocking finding left unresolved, mirrored into BOTH the review Markdown and the sidecar `findings` array using the version-1 finding shape (`vrs._current_finding(blocking=True, severity="High")`, canonical `pattern`, snake_case `blast_radius`; the `_write_clean_state(blocking=True)` shape lacks `pattern` and is rejected by the v1 gate), with the finding's `- **Pattern**:` bullet mirrored into the Markdown finding so the finding-conservation gate stays quiet, expects `evaluate_readiness` to fail on the blocking-consistency arm (is_review_ready), unchanged [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_cap_closure_with_pending_triage`; given the accept-arm fixture with one blocking finding's triage back on `pending` in both record surfaces (the Markdown `- **Triage**:` bullet and the sidecar `findings[].triage`), expects `evaluate_readiness` to fail at the `is_review_ready` reason, pinning that the composite requires the folded findings' triage resolved on both surfaces per the triage-agreement arm, not just the residual section [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_stale_digest_under_cap_closure`; given the accept-arm fixture whose sidecar `source_digest` still records the pre-fold bytes, expects `evaluate_readiness` to fail on the digest arm, proving the re-bind is load-bearing and the shared gate stays the single digest authority [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_malformed_cap_closure_declaration`; given the accept-arm fixture whose declaration is non-conforming (a wrong `plan_section` literal, a `round` mismatching the sidecar, an unknown extension key, or a `pre_fold_digest` equal to the re-bound `source_digest`), expects `evaluate_readiness` to fail with the step-3 mapped reason (malformed stats sidecar), asserting the full mapped reason string for each case and witnessing the wiring call inside `_validate_stats_sidecar_gates` (the inner gate function the `validate_stats_sidecar` wrapper delegates to); each asserted mapped reason, including the differ case, names `extensions.cap_closure` and lands in the malformed-sidecar family, never the stale-digest family (the differ rejection must route to fixing `pre_fold_digest`, not to the re-bind remedy) [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_ordinary_rounds_unaffected_by_cap_closure_rule`; given a normal `ready=yes` sidecar without any extensions object, expects today's outcome (over-blocking witness for the new rule) [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_rejects_yes_verdict_sidecar_with_violating_cap_closure`; given the accept-arm fixture adapted to `verdict: "yes"` with all findings resolved but the residual section body emptied under a nonzero `residuals`, expects `evaluate_readiness` to fail with the dedicated terminal-state reason, not a pass via the yes verdict [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_accepts_yes_verdict_sidecar_with_conforming_cap_closure`; given the same fixture fully conforming, expects `evaluate_readiness` to pass, proving the probe keys on declaration presence, not the verdict value, in both directions [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_accepts_cap_closure_on_modern_plan_with_structural_gates`; given the accept-arm fixture with the sidecar `date` and the round record filename's leading date on/after `DECISION_MARKER_MIN_DATE` (for example `2026-09-26`), plan bytes carrying both the cap-closure section with a conforming body and the `Decision points requiring a grill: none remain.` trailer, expects `evaluate_readiness` to pass; the negative twin removes the trailer line and expects the trailer reason, proving steps 5-6 still run after a satisfied cap-closure conjunct (fall-through, not early return) [class: REPOSITORY_TEST]
- [x] `CapClosureReadinessTest#test_gate_names_undecodable_plan_bytes_under_cap_closure`; given the accept-arm fixture whose plan bytes are invalid UTF-8 while its sidecar matches, expects `evaluate_readiness` to return the named cannot-read-plan-bytes reason, not raise (the declaration-gated decode keeps today's failure shape for declaration-free rounds; the undecodable-bytes reason fires only when the declaration routes the probe at the bytes) [class: REPOSITORY_TEST]
- [x] Run → expect RED: every new cap-closure arm fails today except exactly four guards (`test_ordinary_rounds_unaffected_by_cap_closure_rule`, `test_gate_rejects_verdict_no_without_cap_closure`, `test_gate_rejects_stale_digest_under_cap_closure`, and `test_gate_accepts_yes_verdict_sidecar_with_conforming_cap_closure`), which pass today and must keep passing before and after the change; the fourth guard is green today because today's verdict arm only rejects `no` and today's staging validator accepts unknown extension keys, so a fully conforming yes-verdict fixture passes end to end; any arm not named as a guard is RED today (its asserted reason or behavior does not exist yet, or today's verdict arm fires before the reason it asserts can be reached); the contract test fails because the callable does not exist; all pre-existing suites stay green at this point [class: REPOSITORY_TEST]
- [x] Implement `validate_cap_closure_contract` in `scripts/validate_review_staging.py` mirroring the `validate_address_fanout_contract` idiom (version-1-only, unknown-key rejection): required keys `plan_section` (exactly `## Residual findings (cap closure)`), `round` (int or string, excluding booleans, equal to the sidecar `round` after string normalization; normalize BOTH sides through `str()` after the type gate, then compare the two strings, so a declaration `round` of either JSON type is accepted when the string forms match; reject a normalized declaration round below `CAP_CLOSURE_MIN_ROUND = 3` with a dedicated message naming `extensions.cap_closure`, parsing the integer after stripping a leading `r` since the sidecar `round` is dual-typed, and reject a normalized declaration-round string that does not parse as an integer after stripping that optional leading `r` with its own dedicated message naming `extensions.cap_closure` (collected by the routed-substring arm); the floor is a lower bound on honest cap closures (plans loop rule 8 reconciles at three non-monotonic rounds), never claims the configured cap itself was verified, and presumes a configured cap of at least 3, the only cap the loop's current directives configure, so a directive with a lower configured cap needs its own terminal shape first), `residuals` (non-negative int, booleans excluded; counts the `accepted` section-body entries, and the readiness probe enforces the tie), and `pre_fold_digest` (lowercase hex64, written before folding, must differ from the re-bound `source_digest`; reject a missing key, a non-hex64 value, or a value equal to the re-bound digest); every `validate_cap_closure_contract` error message names `extensions.cap_closure` and avoids the step-3 routed substrings (`source_digest`, `source_kind`, `missing the required 'coverage' object`), including the `pre_fold_digest` differ-from-record rejection, which must phrase itself without embedding those literals; a legacy/versionless record carrying `extensions.cap_closure` fails closed at the version boundary with a named error (never a silent skip); declare the section literal as a module constant here (the single owner of the literal; the constant holds the BARE heading `Residual findings (cap closure)` and the `plan_section` equality check compares against `'## ' + <constant>` so the single owner serves both forms) and wire one call beside the address-fanout wiring inside `_validate_stats_sidecar_gates` (the inner gate function the `validate_stats_sidecar` wrapper delegates to) [class: IMPLEMENTATION_REQUIRED]
- [x] Implement the gate acceptance in `evaluate_readiness` (step 4, the verdict arm) as one probe call plus the ordering decision: add a module-level probe function beside `fence_balance_problem`, `cap_closure_terminal_state_problem(plan_text, cap_closure_declaration, staged_patterns)` (the patterns from the final sidecar's `findings` array; keeping the accounting inside the probe is what lets the verdict arm stay ordering-only), returning `None` on a satisfied conjunct or the dedicated named reason. The probe's conjunct: the fence-stripped plan text carries `## Residual findings (cap closure)` as a line-anchored level-2 heading, implemented as `md_section(_strip_fences(plan_text), <the staging validator's section-literal constant via the existing vrs import>)` being non-empty, where the constant holds the BARE heading `Residual findings (cap closure)` because `md_section` composes its matcher from the bare heading (consuming the `## `-prefixed form never matches) and the declaration check compares `plan_section == '## ' + <constant>` so the single owner serves both forms, citing the Assumptions-trailer precedent at scripts/plan_readiness.py:395 (a quoted mention, a fenced copy, or a `###` heading never satisfies the conjunct); and, when the declaration's `residuals` count is greater than zero, the section body (which stops at the next level-2 heading (md_section semantics) or end of file; when multiple conforming headings exist, the first occurrence governs) contains at least one non-blank line; the declared `residuals` count equals the number of distinct section-body entries carrying the `accepted` disposition, with disposition words outside the `folded`/`accepted` vocabulary rejected while parsing so the matcher is total; and, whenever the declaration is present, every finding pattern in the final sidecar's `findings` array appears in the section body with a disposition (`folded` or `accepted`), the disposition check applied per pattern (the disposition token sits on the same list entry as its pattern, never scanned section-wide), with any under-reporting of the round's staged findings returning the dedicated named reason. Before the probe call, add one shared defensive decode that only the gated consumers of the plan text run (`try: plan_text = plan_bytes.decode("utf-8")` with `except UnicodeDecodeError` returning the existing cannot-read-plan-bytes reason family): the probe call decodes and passes `plan_text` only when the declaration is present, and step 6 reuses the same decode along its existing date-gated arms instead of re-decoding, so the decode runs at most once per call with one named failure reason and no new traceback path while the r2 F2 exemption holds (an undecodable plan whose round is date-exempt and which carries no declaration keeps today's pass and its own later reason family; the pinned `--selftest` decode arms keep their current expectations). The verdict arm keeps only the ordering decision, mirroring the `fence_balance_problem` consumption at scripts/plan_readiness.py:1200-1205: when the sidecar verdict field is `no` and the declaration is absent, return today's named verdict failure; when the declaration is present and the probe returns `None`, pass; when the probe returns a reason (missing heading, quoted-or-misleveled mention only, empty body under a nonzero count, disposition under-reporting, or a residuals-count mismatch), return that dedicated reason, one string naming the terminal state and, when the body is empty under a nonzero count, the declared residual count; extend the module docstring's opening question to name the exception; consume the staging validator's section-literal constant via the existing `vrs` import instead of declaring a second constant [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the full `scripts/test_plan_readiness.py` suite including the new classes [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `scripts/test_execute_plan_address_fanout.py` (adjacent extension validator untouched) [class: REPOSITORY_TEST]
- [x] Bump `COMPAT_VERSION` 2 to 3 in `scripts/validate_review_staging.py` and `EXPECTED_SIBLING_COMPAT_VERSION` 2 to 3 in `scripts/plan_readiness.py` in the same commit: the verdict arm now consumes a vrs constant and the malformed-declaration rejection lives in the new vrs wiring, so the shared-rule semantics are pair-coupled and a partial deployment must fail with the handshake's named message (precedent: the address-fanout change bumped the pair 1 to 2 in 7baa8ce1) [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `plans: cap-closure terminal shape in readiness and staging gates` [class: IMPLEMENTATION_REQUIRED]

### Task 2: document the cap-closure shape on the four contract surfaces and the sidecar schema home

Frozen except: the round-cap paragraph area plus loop rules 2, 6, and 9, the Ready for execution definition, the Pre-finalization self-check block, the Final Step's done precondition, and the Plan Format template meta-rule's residual-narrative ban (its cap-closure carve-out) in the plans skill's Plan Quality Gate loop rules area; the plan-readiness gate bullet in the done skill; the Iteration Discipline list (one added cap-closure item plus amended item 1), the sidecar-contract digest sentence, the `With the plan readiness gate` integration paragraph, the Reconciliation gate paragraph (its cap-closure discharge), and the reviewer-side review-state ban (its cap-closure exemption) in the review-plan skill; the Step 0.5 plan-readiness gate paragraph in the execute-plan skill; a new `### Cap-closure sidecar extension` subsection beside the address-fanout one in the review-staging skill. Every other region of the five files is frozen.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/review-plan/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-staging/SKILL.md`

- [x] In `agents/skills/plans/SKILL.md`, add the round-cap paragraph to the Plan Quality Gate loop rules area: "At the configured round cap without a clean round, close the loop through the cap-closure terminal shape instead of exceeding the cap or stranding the plan: fold accepted blocking findings and mark every folded staged finding resolved in the round's own record surfaces (the review Markdown `- **Triage**:` bullet and the matching sidecar `findings[].triage`, the same resolved-triage value on both per the finding-conservation triage-agreement arm, using the resolved vocabulary `fixed`, `dropped`, or `done`, never the residual-section words `folded`/`accepted`), record every staged finding of the cap round with its disposition (`folded` or `accepted`) in the plan section `## Residual findings (cap closure)`, re-bind the final round sidecar `source_digest` to the post-fold plan bytes, and declare `extensions.cap_closure` carrying `pre_fold_digest` (lowercase hex64 recorded before folding, different from the re-bound `source_digest`; the re-bind rewrites only `source_digest`, which remains the only other sidecar edit after the triage marks; the sidecar `verdict` field keeps the round's honest value and is never edited); declare cap closure only at the configured round cap, a declaration at an earlier round is a falsified certification; the readiness gate accepts this operator-authorized terminal state when no blocking finding stays unresolved." The prescribed text stays runtime-neutral (no tool or harness tokens). Also amend the Plan Format template meta-rule in the same task: after "no round-attributed residual narratives" insert "except the `## Residual findings (cap closure)` section required by the cap-closure terminal shape, which is the sanctioned in-plan home for cap-round residual dispositions". Also qualify the contradicting standing sentences with the exception: loop rule 2 ("launch a fresh round before exit is allowed"), rule 6 ("Exit only when one fresh review on the post-fold digest reports zero unresolved blocking findings"), rule 9 ("revert to the exact reviewed bytes and re-verify the hash"), and the Ready for execution definition each gain "except through the cap-closure terminal shape"; also qualify the Pre-finalization self-check's question 4 ("Does the latest review report `ready=yes`?" and its "The agent must not describe the plan as ready for execution when any answer is negative" prohibition) and the Final Step precondition ("After the plan file is saved, the review gate reports `ready=yes`, and the execution-handoff choice has been offered, invoke the `done` skill") with the same exception [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/done/SKILL.md`, amend the plan-readiness gate bullet: after the verdict requirement in the plan-readiness gate bullet, name the exception (a sidecar declaring the operator-authorized cap-closure terminal shape, `extensions.cap_closure` bound to the plan section `## Residual findings (cap closure)` and carrying `pre_fold_digest`, with zero unresolved blocking findings, passes; folded staged findings carry resolved triage from the vocabulary `fixed`, `dropped`, or `done` on both record surfaces, the review Markdown `- **Triage**:` bullet and the matching sidecar `findings[].triage`, the same value on both per the triage-agreement arm; the re-bind rewrites only `source_digest` and never the sidecar `verdict` field); recorded-stop remains the only way past every other failure. Also qualify the bullet's "require a fresh `review-plan` round (after any plan edit that changes the digest) before re-running the gate" sentence with the same exception [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/review-plan/SKILL.md`, add the cap-closure procedure as an Iteration Discipline item with the producer-side wording of the same shape (including the resolved-triage marks on both record surfaces per the conservation triage-agreement arm using the resolved vocabulary `fixed`, `dropped`, or `done`, the staged-finding disposition recording with its `folded`/`accepted` vocabulary, the only-other-sidecar-edit `source_digest` re-bind scope, the `pre_fold_digest` field recorded before folding, and the configured-round-cap-only constraint: a declaration at an earlier round is a falsified certification), and amend the `With the plan readiness gate` integration paragraph so its failure list no longer over-claims: a `ready=no` verdict fails the downstream gates except under a conforming cap-closure declaration. Also extend the reviewer-side review-state ban's exemption list with the cap-closure section (stale-disposition findings about it stay valid; the staging record remains authoritative for verdicts and round chains). Also qualify the integration paragraph's "a post-round plan edit fails the gates as a stale digest" sentence and the sidecar contract's "The digest must reflect the **post-fold** plan bytes the final round reviewed" sentence with the sanctioned cap-closure re-bind, and qualify Iteration Discipline item 1 ("Exit condition: one fresh review of the current source digest with zero unresolved blocking findings and no unresolved reconciliation trigger") with the cap-closure exception, and amend the Reconciliation gate paragraph so a fired cap-reached trigger is discharged by the recorded cap-closure closure in the final staging artifact or a linked note, requiring no fresh review beyond the closure [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/execute-plan/SKILL.md`, qualify the Step 0.5 plan-readiness gate paragraph with the same exception: the exit-0 parenthetical becomes "(sidecar digest match, `ready=yes` or the operator-authorized cap-closure terminal shape, zero unresolved blocking findings)", with the terminal shape named as a sidecar declaring `extensions.cap_closure` bound to the plan section `## Residual findings (cap closure)` with zero unresolved blocking findings, and the "require a fresh `review-plan` round" remedy sentences gain "except when the failure is remediable through the cap-closure terminal shape"; the prescribed text stays runtime-neutral (the file is in the runtime-neutrality gated set) [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/review-staging/SKILL.md`, add a `### Cap-closure sidecar extension` subsection beside the address-fanout one, documenting the `extensions.cap_closure` shape: required keys `plan_section` (exactly `## Residual findings (cap closure)`), `round` (int or string, equal to the sidecar `round` after string normalization and normalizing to at least `CAP_CLOSURE_MIN_ROUND` = 3), `residuals` (non-negative int, booleans excluded; counts the section-body entries carrying the `accepted` disposition, and the readiness probe enforces the tie), and `pre_fold_digest` (lowercase hex64, written before folding, differing from the re-bound `source_digest`); the section's contract is the cap-round disposition ledger: every staged finding of the cap round is listed with its disposition (`folded` or `accepted`); version-1-only, fail-closed at the version boundary; the validator's section-literal constant is the shape's single owner and holds the bare heading (the declaration value carries the `## ` prefix) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `ExecutePlanRuntimeTest.test_shared_skill_bodies_remain_runtime_neutral` (plans SKILL.md is in the gated file set) and the Task 2 presence gates from Validation Commands [class: REPOSITORY_TEST]
- [x] Commit: `skills: document the cap-closure terminal shape on plans, done, review-plan, execute-plan, review-staging` [class: IMPLEMENTATION_REQUIRED]

### Task 3: deterministic usage-error precedence in select_record

Frozen except: the interior statement order of `select_record` before the `emit` definition (the two usage-check blocks move above the enumeration call) and the moved blocks' comments; in the test module, the new precedence test appended while existing tests stay frozen.

Files:
- `scripts/review_record_selection.py`
- `scripts/test_review_record_selection.py`

- [x] `SelectionHelperTest#test_select_usage_error_precedes_orphan_refusal`; given a reviews directory holding an orphan sidecar half and an invocation whose `--source-digest` is empty, expects exit 2 with the `--source-digest` usage message (not exit 1 with the orphan message); given the same corpus with a malformed digest (`xyz`), expects exit 2 with the digest-grammar message; given the same corpus with a traversal slug (`../../x`) and a valid digest, expects exit 2 naming the slug, and given a backup-infix slug (`demo.backup-x`) with a valid digest, expects exit 2 naming the slug (both slug usage errors precede the orphan refusal, never exit 1 naming the orphan) [class: REPOSITORY_TEST]
- [x] Run → expect RED: the new precedence test fails today (empty digest over an orphan corpus exits 1 with the orphan message); every existing test in the file stays green at this point, including the orphan refusal test over a valid digest [class: REPOSITORY_TEST]
- [x] Move the empty-digest check (the `if not source_digest.strip():` block) and the digest-grammar check (the `if SOURCE_DIGEST_PATTERN.fullmatch(source_digest) is None:` block) above the `pairs, orphans, backups_ignored = _enumerate(` call in `select_record`; keep both refusal messages byte-identical; update the moved blocks' comments to say the usage error is decided before any record-corpus state is consulted [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the full `scripts/test_review_record_selection.py` suite including the new precedence test and the unchanged orphan refusal test [class: REPOSITORY_TEST]
- [x] Commit: `scripts: decide select_record usage errors before corpus state` [class: IMPLEMENTATION_REQUIRED]

### Task 4: append the migration-audit marker to the reconcile row and verify the consult

Frozen except: the notes cell of the reconcile row named in the first checklist item; every other row, column, and registry element is frozen.

Files:
- `docs/maintenance/document-registry.md`

- [x] Precondition check: given the row's notes cell as read from disk, expect it to start with `user-approved 2026-09-25: fold-then-delete reconcile` and to not already contain `migration audit`; on either precondition failing, stop and report the drift instead of editing [class: REPOSITORY_TEST]
- [x] Corpus precondition: before the edit, run `python3 scripts/check_plan_origins_closed.py` and assert (a) each of the six `done-sweep-residuals` origin strings and the two genuine-straggler strings is present in the warn output exactly as the Task 4 consult gate asserts, with none already absent, and (b) the `2026-09-25-done-sweep-residuals-and-stale-origin-dispositions.md` plan contributes exactly its six warn lines; corpus-wide totals beyond these eight lines are informational and drift with unrelated landings; on any of (a) or (b) failing, stop and report instead of editing [class: REPOSITORY_TEST]
- [x] In the `done-sweep-residuals-and-stale-origin-dispositions` row's notes cell, insert the marker so the cell opens `user-approved 2026-09-25: migration audit - fold-then-delete reconcile of the completed/ inbox executed by` with the rest of the cell continuing byte-identical; single-line cell-content edit, no column, pipe, or format change [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 4 consult gate from Validation Commands: the six `done-sweep-residuals` origin warns are absent, the two genuine-straggler warns still fire, and the checker's warn arm exits 0 [class: REPOSITORY_TEST]
- [x] Delta witness: revert the row edit, re-run the checker, and require the six `done-sweep-residuals` origin warns to reappear; re-apply the edit and require them absent again, attributing the resolved-warn delta to this row's marker (the same simulate-and-revert protocol as the authoring-time record) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `scripts/test_check_plan_origins_closed.py` (checker suite untouched by the data edit) [class: REPOSITORY_TEST]
- [x] Commit: `registry: mark the shadow-plan reconcile row for the origins consult` [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

- implementation#requirement-coverage: folded (fixed in the cap-closure finalize)
- consistency#residual-definition-vs-disposition-ledger: folded (fixed in the cap-closure finalize)
- consistency#frozen-review-state-ban-vs-mandated-section: folded (fixed in the cap-closure finalize)
- consistency#precondition-pins-drifting-corpus-total: folded (fixed in the cap-closure finalize)
- architecture#missing-invariant-enforcement: folded (fixed in the cap-closure finalize)
- security#disposition-association-unwitnessed: folded (fixed in the cap-closure finalize)
- testing#missing-gate-needle: folded (fixed in the cap-closure finalize)
- consistency#em-dash-scan-omits-task-files: folded (fixed in the cap-closure finalize)
- consistency#task2-surface-count-drift: folded (fixed in the cap-closure finalize)
- security#future-maintainer-section-constant-md-section-contract: folded (fixed in the cap-closure finalize)
- security#cap-closure-rejection-routing-unwitnessed: folded (fixed in the cap-closure finalize)
- testing#layer-confused-coverage: folded (fixed in the cap-closure finalize)
- testing#coverage-claim-unchecked: folded (fixed in the cap-closure finalize)
- quality#edge-case: folded (fixed in the cap-closure finalize)
- implementation#api-contract: folded (fixed in the cap-closure finalize)
- simplification#yagni: folded (fixed in the cap-closure finalize)
- architecture#substring-routing-contract: folded (fixed in the cap-closure finalize)

## Origins disposition (archived 2026-09-27)

All three backlog origins are discharged by this plan's executed tasks and are deleted per the fold-then-delete rule:

- docs/history/backlog/2026-09-26-at-cap-finalization-done-gate-collision.md (anchor): Collision 1 closed by Task 1 (cap-closure terminal shape in the staging validator and the readiness gate, commit 7a731ca8) and Task 2 (contract-surface documentation, commit 9c8b3e60); candidate (a) implemented per the recorded decision point.
- docs/history/backlog/2026-09-20-selection-empty-digest-exit-code-corpus-dependence.md: Collision 2 closed by Task 3 (usage errors decided before record-corpus state, commit e1193dd3).
- docs/history/backlog/2026-09-26-shadow-plan-reconcile-rows-migration-audit-marker.md: Collision 3 closed by Task 4 (migration audit marker on the reconcile row; consult resolves the six origins with the delta witness, commit d68360f7).

Execution record: Phase 3 code review r1 clean (zero blocking; nine non-blocking findings deferred to durable backlog items 2026-09-27-cap-closure-*), full Validation Commands exit 0, plan archived at docs/history/plans/completed/2026-09-27-certification-machinery-contract-collisions.md.
