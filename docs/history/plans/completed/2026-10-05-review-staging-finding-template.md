# Plan: review staging finding template

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-execute-plan-review-staging-schema-first-pass.md`

Driving force: reliability (a witnessed 2026-10-05 staging first pass copied panel findings into placeholder ids, confidence values, and prose headings that failed the hard validator on nine independent format classes at once - non-integer ids, invalid confidence, missing reachability and blast radius, noncanonical headings, per-worker overflow, conservation, and witness-ledger requirements - churn that blocked a triage-ready blocking finding behind avoidable format work)

Plan review record: the staging series docs/reviews/2026-10-05-plan-review-review-staging-finding-template-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Hard validator: `scripts/validate_review_staging.py --hard`, the grading run whose refusal blocks a round; its non-hard run is the same schema check without the grading posture, usable as a drafting preflight.
- Finding-construction recipe: the fill-order template this plan adds to the staging skill's front matter: one fenced minimal-valid example (Metadata block, one `#### F<N>.` finding with every field's accepted spelling, the sidecar skeleton) a writer copies before drafting.
- Canonical example: the example pair embedded in the skill's fences that the validator's selftest extracts, materializes to a temporary directory, and validates green, so the documented shape can never drift from the enforced shape.
- Preflight check: running the validator (non-hard) on a drafted staging document before the round's hard gate, surfacing format errors while drafting instead of at grading.

## Why

The staging skill already owns the authoritative schema, but it exposes it as prose obligations distributed across sections, and the witnessed first pass reconstructed the shape from memory and failed nine format classes at once. The fix is presentation, not new law: a copyable minimal-valid example at the point of drafting, a fill-order recipe that names each field's accepted spelling once, and a selftest arm that validates the embedded example so the documented shape and the enforced shape cannot diverge. Every field the recipe names already has its canonical home in the schema sections; nothing new is enforced.

## Outcome

- A writer opening the staging skill meets the finding-construction recipe before the schema prose: one fenced minimal-valid example pair, the closed enums inlined, the fill order explicit, and the preflight check named, so the first hard-validator run grades substance instead of format.
- The example is load-bearing: the validator's selftest extracts and validates it green on every selftest run, so a schema change that would invalidate the documented shape fails the suite in the same edit.

Gate delta: no new refusal classes; one new selftest arm (the embedded-example validation) whose failure means the documentation example drifted from the enforced schema. The hard validator's semantics are untouched.

## Assumptions

- assume authoring runs unattended under the standing operator directive, so Step 1.4 confirmation is satisfied by the row's validated record rather than a live interview; basis: the maintenance loop's authoring blueprint (loop_mode dual, continuous pacing amendment 2026-09-30).
- assume the recipe lives immediately ahead of the staging skill's Inputs section (before the schema sections) and cross-references them as the schema of record rather than restating their shapes; basis: the skill owns the authoritative documentation the validator enforces, and a second full statement would create the drift surface the selftest arm exists to close.
- assume the example pair is embedded in the skill's fences at that same placement (not a checked-in example file) and the selftest extracts it; basis: the skill directory is a vendored corpus where added files carry sync obligations, fences keep the example beside the prose that explains it, and the validator's own suite already demonstrates extraction-style fixtures.
- assume the preflight is the validator's existing non-hard invocation, not a new mode; basis: the row asks for a small validation before the first hard run, the non-hard run performs the same schema check today, and the recipe only needs to name it.
- assume the example uses a fictional-but-realistic artifact slug and record family that the validator accepts (the validator does not resolve the artifact's existence, only shapes); basis: the selftest materializes the example in a temporary directory, so no live corpus path is referenced.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the staging skill opens with a copyable minimal-valid example pair and a fill-order recipe, and the validator's selftest validates that example green forever, so the first hard-validator run grades substance instead of format.

Before (today): a writer drafts findings from memory, the hard validator rejects nine format classes at once, and a blocking finding waits behind format churn.

After (this plan): the writer copies the fenced example, fills the fill-order fields, runs the non-hard preflight while drafting, and the hard gate grades the round's substance. A schema change that invalidates the documented example fails the validator's selftest in the same edit.

Edge cases pinned: the extracted example validates green through the selftest; a deliberately malformed variant of the example (one field per critical enum) fails the validator with the expected named error, proving the example's fields are load-bearing rather than vacuously accepted; the recipe's enum spellings match the validator's closed vocabularies exactly.

## Tasks

### Task 1: The finding-construction recipe, the canonical example, and the selftest arm

Files:
- `agents/skills/review-staging/SKILL.md`
- `scripts/validate_review_staging.py`
- `scripts/test_review_record_selection.py`

Evidence:
- `python3 scripts/test_review_record_selection.py`; covers the selftest-arm criterion below at the task boundary (main-shim suite)
- `python3 scripts/validate_review_staging.py --selftest`; covers the embedded-example validation directly
- `bash scripts/check_maintenance_pins.sh`; regression: no pinned span breaks

- [x] `test_embedded_example_validates_green` (given the skill's fenced example pair extracted to a temporary directory, expects the validator to accept it with exit 0) [class: REPOSITORY_TEST]
- [x] `test_example_fields_are_load_bearing` (given per-field malformed variants of the extracted example - a non-integer finding id, an out-of-enum confidence, a missing reachability, a noncanonical `F<N>` heading - expects each variant to fail with the named error, proving no example field is vacuously accepted; and the recipe's inlined enum line, parsed from the skill text, asserts set equality with the validator's confidence, reachability, and blast-radius vocabularies, so a drifted spelling fails the suite) [class: REPOSITORY_TEST]
- [x] Implement the selftest arm in scripts/validate_review_staging.py: the `--selftest` run extracts the fenced example pair from agents/skills/review-staging/SKILL.md (stable fence markers this task introduces), materializes both files in a temporary directory, validates them green, and runs the malformed-variant assertions; a schema change that invalidates the example fails the selftest [class: IMPLEMENTATION_REQUIRED]
- [x] Skill text, recipe and example: the staging skill gains the finding-construction recipe in its front matter: the fenced minimal-valid example pair carrying the full current-contract skeleton - a canonical `source_kind: plan` record dated at writing time with the freshness quartet, record_kind, and the coverage object, so the selftest-validated shape is the shape a real round must produce, not a minimized subset (Metadata block, one complete `#### F1.` finding with numeric id, the three validator-enumerated fields inlined with their closed spellings - confidence, reachability, blast radius - worker attribution as example values, the triage field, and the sidecar skeleton with counts, panel row, and witness-ledger line), the fill order stated once including the per-worker non-blocking Low budget and the overflow escape (cross-referencing the skill's own recording rules rather than restating them), the preflight invocation (the validator's non-hard run) named as the drafting-time check, and a pointer to the schema sections as the schema of record; the recipe restates no shape the schema sections own beyond the inlined example [class: IMPLEMENTATION_REQUIRED]
- [x] Run the full suite, the validator selftest, the pins suite, the em-dash added-lines scan, the hygiene scan, and plan_readiness [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: review staging opens with a validated finding-construction example` [class: IMPLEMENTATION_REQUIRED]

## Review Scope

Files in scope (the union of the task Files lists): `agents/skills/review-staging/SKILL.md`, `scripts/validate_review_staging.py`, `scripts/test_review_record_selection.py`.

Reviewers judge: single-source-of-truth discipline (the recipe inlines an example and names enums but the schema sections stay the shape of record), the selftest arm's extraction robustness (stable fence markers, temporary materialization, no live-corpus references), the malformed-variant assertions' load-bearing proof, scope discipline (no task reaches beyond its Files list), and test reality (every criterion has a named test runnable in this repository).

## Validation Commands

The per-task checklist references the suite, the validator selftest, pins, the em-dash scan, the hygiene scan, and the readiness probe by name; the exact invocations are the six literals below.

```bash
python3 scripts/test_review_record_selection.py
python3 scripts/validate_review_staging.py --selftest
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-review-staging-finding-template.md
```

## Disposition

- Outcome: executed and landed on main (squash commit recorded at landing).
- Task 1 complete; all six checkboxes ticked; implementation commit 9f2cee9e (finding-construction recipe section opening the staging skill with the marker-grammar example pair, closed-enum line, fill order, and preflight naming; embedded_recipe_example selftest family extracting/materializing/validating the example green with malformed-variant and enum-vocabulary assertions; named tests in the selection suite).
- Exec review: r4 fresh adversarial ready=yes zero findings (mutation probes confirmed the selftest is load-bearing: sidecar drift, marker removal, schema edit, and heading change each fail it); the r3 digest-binding certification (staged by the implement agent) binds the ticked bytes; the r5 certification probe bound the final disposition-appended bytes (digest 2e34f607) and its four wording findings were folded; records + sidecars at docs/reviews/2026-10-05-plan-review-review-staging-finding-template-r{3,4,5}.md. Pre-landing voice: the landing squash commit is the landing witness.
- Gates on the exec bytes: selftest ok; selection suite 45 passed; pins OUTCOME: pass; em-dash added-lines exit 0; hygiene OUTCOME: pass; plan_readiness OK on the final bytes via the r5 binding.
- Deferred residuals: the two Low wording residuals recorded on r2 carry unchanged (extraction-precedence misattribution, front-matter placement wording), adjudicated landed at r3.
