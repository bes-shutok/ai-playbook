# Plan: review-plan inline sidecar schema drift

Backlog origin: docs/history/backlog/2026-09-28-review-plan-inline-sidecar-schema-drift.md
Driving force: code-quality + token-usage
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-review-plan-inline-sidecar-schema-drift-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Make the review-plan skill's inline sidecar schema trustworthy again, so a producer shaping a review record from the skill text alone whose record still fails the schema check hits that failure at its own pre-staging gate run with the validator named in place as the single recovery authority, instead of hunting the shape across sources.

- The inline schema copy becomes a declared stable-core summary with an explicit validator-first rule, so the enforced contract has exactly one doc authority (review-staging) and one enforcement owner (the validator) instead of a second stale copy.
- A producer whose record fails the schema check now hits that failure at its own gate run before the round is reported complete, with the validator named in place as the single recovery authority, ending the multi-source hunt that cost the witnessed session six failed gate runs; first-submission success is explicitly not the bar, because the summary deliberately omits enforced shapes.
- The drift surface narrows: the Step 3 summary is reduced to a field-name skeleton with attribution, and while frozen Step 4 and readiness-gate restatements elsewhere in the file remain, the validator-first rule is the compensation that catches their staleness at staging time instead of silently.

## Terms

- sidecar: the `.stats.json` companion record of a review staging document, validated by `scripts/validate_review_staging.py`.
- staging document: the per-round review Markdown under `docs/reviews/` that the readiness gate discovers by glob.
- cap closure: the operator-authorized terminal review-loop shape recorded in a sidecar's `extensions.cap_closure` and the reviewed plan's `## Residual findings (cap closure)` section.
- readiness gate: `scripts/plan_readiness.py`, the mechanical done-boundary check over plan bytes plus the latest review round pair.

## Assumptions

- assume the shrink arm over the refresh arm (shrink the inline copy to a summary plus a validator-first rule, rather than re-syncing the full enforced shape into the skill text); basis: the drift mechanism is live, not hypothetical: the copy was already refreshed once for the coverage sentence (2026-09-19) and the cap-closure re-bind (2026-09-28) and has re-drifted anyway, its optional-field list omitting the `usage` key that the validator accepts and review-staging documents (measured 2026-09-28), so a refresh arm re-stales by the same mechanism; the origin item offers both arms; the standing pre-authorization on this authoring run accepts the recommended option.
- assume `agents/skills/review-staging/SKILL.md` stays the documentation authority and is not edited by this plan; basis: on current main it documents the coverage contract, the cap-closure extension, the attempt-ledger obligations, and the top-level field inventory (verified 2026-09-28); it is outside this plan's must-fix set.
- assume the validator script is not edited; basis: the witnessed defect is the skill-side stale copy, not the enforcement; the validator is the shape's single owner.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: shrink review-plan's inline sidecar schema to a stable-core summary with a validator-first rule, so the enforced contract stops drifting a second stale copy into the skill text, for code-quality and token-usage.

Today, `agents/skills/review-plan/SKILL.md` Step 3 inlines a sidecar schema copy introduced "so it is in context without loading `review-staging`". The copy is not a stable summary: it restates enforced shapes in its own words, and those restatements have already needed two refreshes (the coverage sentence, 2026-09-19; the cap-closure re-bind lines, 2026-09-28) and have re-drifted anyway. Measured against the current validator, the copy today: omits the optional top-level field `usage` (accepted by the validator, documented by review-staging); names the coverage object without its enforced shape rules (the completed list is validated as a lens list, not a worker list; attempts rows carry required keys with free-form keys rejected; retry_budget requires positive values when attempts are non-empty); omits the closed `risk_signals` tag vocabulary; omits the finding ordering rule and the per-worker non-blocking Low overflow budget; names the record-kind Metadata mirror line and the last-fix-commit witness shape only as unpinned pointers; and omits the coverage-line outcome parity, the attempt-ledger row parity, and the enforced no-fix spelling family entirely. A producer following the inline copy alone still fails `validate_review_staging.py --hard` on first submission and can only recover by reading the validator source; the witnessed session burned six failed gate runs across two rounds that way, most of them on shapes the copy names but does not pin.

The fix keeps the inline copy's context value but kills its authority: the copy becomes a summary of the stable core (top-level field names including the optional set, finding-row shape, pattern id form) with two load-bearing sentences added: run the Step 4 mechanical gate before staging, and on any schema error read the validator source, never this summary. The Integration Points paragraph that advertises the inline copy as the in-context schema is reworded to the same framing.

What does not change: the validator, review-staging's authoritative documentation sections, the readiness gate, the Step 4 mechanical gate invocation, and every consumer of the sidecar contract. One review-staging surface is consciously left to a tracked landing path rather than edited here: the `review-plan` row of review-staging's Integration Points table still says the schema is "inlined" in Step 3, which this plan makes stale; the companion backlog item docs/history/backlog/2026-09-28-review-staging-integration-points-review-plan-row-stale.md carries the one-line reword, filed by this plan's run and landed beside it, so the mirrored claim is never orphaned.

## Evaluation Criteria

**Quality dimensions:**

- correctness: the summary carries no shape claim the validator would reject, and every obligation the inline copy drops is named as validator-owned rather than deleted silently.
- maintainability: the summary contains no date-literal fences, closed vocabularies, or per-key shape rules that a validator extension can stale.
- operability: a producer reading only Step 3 knows, before staging, that the mechanical gate is the contract check and the validator source is the shape authority.

**Done when:**

- the Step 3 schema intro declares the summary framing and carries the validator-first rule as prescribed text.
- the top-level bullet lists required and optional field names only (the optional set including `usage`), with date-fenced obligations, closed vocabularies, per-key shapes, ordering and budget rules, staging Markdown obligations, and the cap-closure shape attributed to review-staging and the validator.
- the Integration Points paragraph no longer advertises the inline copy as the in-context schema.
- all Validation Commands pass with the counts and negations they pin.

**Ship when:**

- nothing; the change is repository-local skill documentation with no external dependency or release condition.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/review-plan/SKILL.md` *(Step 3 sidecar schema block and the Integration Points paragraph "With `review-staging` skill" only; all other sections in this file are frozen: reject any review finding that touches them, documenting real defects elsewhere as separate findings for triage instead of in-place fixes)*

**Tests:**

- none as separate files; the Validation Commands block is this plan's mechanical gate surface.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `agents/skills/review-staging/SKILL.md`; reason: it stays the documentation authority this plan points at, and editing the authority inside the same plan that re-points at it would blur which side moved; the one stale consumer surface (the `review-plan` row of its Integration Points table) is disposed as the filed companion backlog item named in the Gist, a tracked landing path, not an in-plan edit.
- `scripts/validate_review_staging.py`; reason: the enforcement is correct per the origin witnesses; only the skill-side copy drifted.
- `scripts/plan_readiness.py` and any consumer of the sidecar contract; reason: this plan changes producer-facing prose only, no schema byte.

## Validation Commands

```bash
#!/usr/bin/env bash
# G1 count pin helper: occurrence counting (grep -oF, per plans rule 33) with the
# three-way exit split (rc 0 matches counted, rc 1 clean zero, rc >= 2 tool error).
cnt() { rc=0; got="$(grep -oF -- "$1" "$2")" || rc=$?; if [ "$rc" -ge 2 ]; then echo "FAIL: grep error rc=$rc on $2"; exit 1; fi; n=0; if [ "$rc" -eq 0 ]; then n="$(printf '%s\n' "$got" | wc -l | tr -d ' ')"; fi; if [ "$n" != "$3" ]; then echo "FAIL: occurrences of pinned span in $2 is $n, want $3: $1"; exit 1; fi; }
REPO="$(git rev-parse --show-toplevel)" || { echo "FAIL: not a git checkout"; exit 1; }
RP="$REPO/agents/skills/review-plan/SKILL.md"
RS="$REPO/agents/skills/review-staging/SKILL.md"
test -f "$RP" || { echo "FAIL: missing $RP"; exit 1; }
test -f "$RS" || { echo "FAIL: missing $RS"; exit 1; }
# G2: the new summary framing intro is present exactly once in review-plan.
cnt "the enforced contract is the validator, not this copy" "$RP" 1
# G3: the validator-first rule is present exactly once in review-plan.
cnt "on any schema error, read the validator source" "$RP" 1
# G4: the summary-may-lag sentence is present exactly once in review-plan.
cnt "this summary is not the contract" "$RP" 1
# G5: the old inline-authority framing sentence is gone from review-plan Step 3.
cnt "inlined here so it is in context without loading" "$RP" 0
# G6: the old Integration Points inline-schema claim is gone.
cnt "schema is inlined in Step 3" "$RP" 0
# G7: the reworded Integration Points framing is present exactly once.
cnt "stable-core summary of the sidecar schema" "$RP" 1
# G11: the Task 1 trim removed every enforced-shape restatement from the Step 3
# region (fail-closed region extraction with sentinel and unconditional trap
# teardown; the pins are region-scoped because `pre_fold_digest` legitimately
# remains in the frozen Step 5 cap-closure procedure outside this region, so a
# whole-file want-0 would be unsatisfiable for that pin).
# Region counts today: dated-on-or-after 3, COVERAGE literal 2, then 1 each for
# the remaining eighteen pins; want 0 for all twenty after the trim.
STEP3="$(mktemp)" || { echo "FAIL: mktemp for Step 3 region"; exit 1; }
trap 'rm -f "$STEP3"' EXIT
awk '/^## Step 3:/{f=1} /^## Step 4:/{f=0} f' "$RP" > "$STEP3"
grep -qF 'Sidecar schema' "$STEP3" || { echo "FAIL: Step 3 region extraction lost its sentinel"; exit 1; }
cnt "dated on or after" "$STEP3" 0
cnt "COVERAGE_SIDECAR_MIN_DATE" "$STEP3" 0
cnt "EXTENDED_SIDECAR_MIN_DATE" "$STEP3" 0
cnt "RECORD_KIND_SIDECAR_MIN_DATE" "$STEP3" 0
cnt "four-value enum" "$STEP3" 0
cnt 'owners: `quality`' "$STEP3" 0
cnt 'not `"F1"`' "$STEP3" 0
cnt 'must carry `lead_worker`' "$STEP3" 0
cnt 'for the five base workers' "$STEP3" 0
cnt 'any other top-level field is rejected' "$STEP3" 0
cnt '64-hex' "$STEP3" 0
cnt 'compute_source_digest' "$STEP3" 0
cnt 'populated-or-N/A' "$STEP3" 0
cnt 'pre_fold_digest' "$STEP3" 0
cnt 'string `yes` or `no`' "$STEP3" 0
cnt 'panel_mode == "full"' "$STEP3" 0
cnt '`"full"` | `"focused"`' "$STEP3" 0
cnt '`"plan"` for plan reviews' "$STEP3" 0
cnt 'unless a sixth worker was launched' "$STEP3" 0
cnt '(`[]` when none)' "$STEP3" 0
# G12: the entire old intro line is gone, pinned as one contiguous fixed string
# (the replace-target of Task 1 item 1; the pin forces the whole-line reading,
# plans Validation rule 40; count 1 today, 0 after the edit).
cnt '**Sidecar schema (inlined here so it is in context without loading `review-staging`; authoritative copy lives there).** Every `.stats.json` is a version-1 record (`"schema_version": 1`) and must carry, at minimum:' "$RP" 0
# G13: the stable core survives the trim (retention pins; over-deletion guards;
# the usage pin is RED-today, the rest GREEN-today; the owner names must remain
# so the attribution sentence keeps its named authorities).
for opt in depth domains verdict extensions usage; do grep -qF "\`$opt\`" "$STEP3" || { echo "FAIL: Step 3 summary lost the optional field name: $opt"; exit 1; }; done
grep -qF 'review-staging' "$STEP3" || { echo "FAIL: Step 3 summary lost the review-staging owner attribution"; exit 1; }
grep -qF 'validate_review_staging.py' "$STEP3" || { echo "FAIL: Step 3 summary lost the validator owner attribution"; exit 1; }
# G8 (dedicated per anchor, heading-anchored regex so deleting the heading breaks the gate): the review-staging authority anchors this plan points at exist.
grep -q '^### Coverage sidecar contract' "$RS" || { echo "FAIL: review-staging lost the coverage contract anchor"; exit 1; }
grep -q '^### Cap-closure sidecar extension' "$RS" || { echo "FAIL: review-staging lost the cap-closure anchor"; exit 1; }
grep -q '^### Attempt ledger' "$RS" || { echo "FAIL: review-staging lost the attempt-ledger anchor"; exit 1; }
# G9: the validator the rule names is invocable (the canonical executable artifact).
python3 "$REPO/scripts/validate_review_staging.py" --help >/dev/null 2>&1 || { echo "FAIL: validate_review_staging.py --help not runnable"; exit 1; }
# G10: no em-dash anywhere in the touched skill file.
( cd "$REPO" && bash scripts/check-no-em-dash.sh file agents/skills/review-plan/SKILL.md ) || { echo "FAIL: em-dash in review-plan SKILL.md"; exit 1; }
( cd "$REPO" && bash scripts/check-no-em-dash.sh file docs/history/plans/2026-09-28-review-plan-inline-sidecar-schema-drift.md ) || { echo "FAIL: em-dash in plan file"; exit 1; }
echo "ALL VALIDATION GATES GREEN"
```

Authoring-time gate record (plans Validation rules 19, 22, 29): the block above was executed against the pre-edit tree; G2, G3, G4, and G7 were RED (occurrences 0 against want 1), G5, G6, and G12 were RED (occurrences 1 against want 0), the twenty G11 removal pins were RED over the extracted Step 3 region (region occurrences: 3, 2, then 1 for each of the remaining eighteen; want 0), and two G13 retention pins were RED-today (the usage name and the validator owner attribution are absent from the region until Task 1 lands), each flipping GREEN exactly when Task 1 lands; G8, G9, G10, and the remaining G13 retention pins were GREEN pre-edit and stay GREEN; the block passes `bash -n`; the pre-round readiness invocation and the hygiene scan were run over the final plan bytes with no structural failure (authoring record 2026-09-28, r3 low fold).

### Task 1: Shrink the Step 3 inline sidecar schema to the stable-core summary with the validator-first rule

Files:

- `agents/skills/review-plan/SKILL.md`

- [ ] Replace the entire Step 3 schema intro line, quoted byte-exact in the replace-target block below, with the prescribed summary framing block below it (the prescription covers the whole line including its tail clause; no tail text survives the replacement) [class: IMPLEMENTATION_REQUIRED]
- [ ] Trim the top-level required-set bullet to field names with ownership attribution: keep the required-field name list and the freshness field names, reduce every field entry to its bare name (the digest hash rule, the verdict and panel_mode enums, the selection_reason conditional, and the digest-helper name are validator-owned), and add the optional top-level field names as a names-only list (depth, domains, verdict, extensions, usage); then replace, in the same bullet and the sibling bullets, every enforced-shape restatement with one attribution sentence naming review-staging and the validator as the owners of: the date-fenced obligations including the coverage object and the record-kind fence, the closed vocabularies including the risk_signals tags and the pattern-owner set, the per-key shapes including the attempts rows, retry_budget values, and the discarded wrong-owner rows, the finding ordering rule and the per-worker non-blocking Low overflow budget, the staging Markdown obligations including the record-kind line, the coverage line, the exact last-fix-commit shape, and the attempt-ledger row parity, and the extensions cap-closure shape; the pattern-id, panel-row, findings-row, and discarded-row bullets survive as key-name pointers only, with no closed vocabulary or conditional shape rule left in any of them [class: IMPLEMENTATION_REQUIRED]
- [ ] Reword the Integration Points paragraph "With review-staging skill": replace the sentence claiming the sidecar JSON schema is inlined in Step 3 for context without a load step with the prescribed framing below, keeping the mechanical-gate half of the paragraph unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Sweep the edited file for em-dashes introduced by the edit and run the Validation Commands block; expect every RED-today pin (G2, G3, G4, G5, G6, G7, the twenty G11 pins, G12, and the two RED-today G13 pins) to flip to its wanted state and the GREEN-today pins (G8, G9, G10, the other G13 retention pins) to stay GREEN [class: REPOSITORY_TEST]
- [ ] Commit: `skills: shrink review-plan inline sidecar schema to summary with validator-first rule` [class: IMPLEMENTATION_REQUIRED]

Replace-target for Task 1 item 1 (the entire intro line, byte-exact, verified present exactly once today):

```
**Sidecar schema (inlined here so it is in context without loading `review-staging`; authoritative copy lives there).** Every `.stats.json` is a version-1 record (`"schema_version": 1`) and must carry, at minimum:
```

Prescribed replacement intro for Step 3 (verbatim; replaces the entire line above):

```
**Sidecar schema (stable-core summary; the enforced contract is the validator, not this copy).** Every `.stats.json` is a version-1 record (`"schema_version": 1`). This summary exists so a producer can shape a record without loading `review-staging`; it deliberately carries only the stable core and may lag the enforced shape. As part of staging, before the round is reported complete, run the Step 4 mechanical gate (`validate_review_staging.py --hard` with `--source-plan`); on any schema error, read the validator source for the enforced shape; this summary is not the contract. At minimum a record carries:
```

Prescribed replacement sentence for the Integration Points paragraph (verbatim):

```
Step 3 carries a stable-core summary of the sidecar schema (the enforced contract is the validator and review-staging's authoritative copy), and the Step 4 mechanical gate runs `validate_review_staging.py --hard` before the round is reported complete.
```

### Task 2: Post-edit mechanical audit

Files:

- none new; this task runs the plan's gates over the edited tree.

- [ ] Run the full Validation Commands block from the repository root; expect the final line `ALL VALIDATION GATES GREEN` [class: REPOSITORY_TEST]
- [ ] Run `( cd "$(git rev-parse --show-toplevel)" && python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-09-28-review-plan-inline-sidecar-schema-drift.md )`; expect exit 0 with no structural failure [class: REPOSITORY_TEST]
- [ ] Run the public hygiene scan from the repository root; expect exit 0 [class: REPOSITORY_TEST]
