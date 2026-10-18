# Plan: done scan profile-scoped content exemption

Backlog origins (scope of record):
- docs/history/backlog/2026-10-12-done-private-repository-visibility-scan.md
- docs/history/backlog/2026-10-08-visibility-scanner-contract-test-gaps.md
Driving force: external (operator direction 2026-10-12, recorded in the first origin row: exclude PII and sensitive-data content scanning for company projects and private pet projects)
Plan review record: the staging series docs/history/reviews/2026-10-12-plan-review-done-sensitive-scan-profile-boundary-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 1.0h total, largest task 0.75h

## Terms

- sensitive-data-scan gate: the done landing sweep gate `gate_sensitive_data_scan` in `scripts/done_sweep_gates_lib.py`; registry key `sensitive-data-scan`.
- content arms: the gate's arms 1 and 2, the staged-diff grep and the untracked-file grep; the only arms whose pattern set this plan changes.
- credential family: `CREDENTIAL_CONTENT_PATTERNS` (api key, token, password or secret assignment shapes).
- public-artifact family: `PUBLIC_ARTIFACT_CONTENT_PATTERNS` (home-directory path prefixes, tracker host suffix, contact email).
- profile exemption: the new rule that skips both content arms entirely when the repo facts record `project_type = "company"`, or `project_type = "pet"` with `artifact_visibility = "private"`.
- strict fallback: the current full scan (both families) kept for public pets and for missing, malformed, or unrecognized profile facts.
- push-range commit-message audit: the gate's arm 3; checks `Co-authored-by` trailers and employer-brand patterns over the unpushed range; unchanged by this plan.
- employer-brand patterns: user-facts-resolved patterns (`employer_brand_patterns`, `atlassian_domain`) matched by arm 3 via `_employer_brand_patterns`.
- skills-repo hygiene arm: the gate's arm 4, the public-hygiene scan child run when the repo is the skills repo; unchanged by this plan.
- families message: the gate result string naming the active content families.
- redaction plan: docs/history/plans/completed/2026-09-30-done-scan-visibility-scoped-redaction.md, which split the constants into the two families.
- profile plan: docs/history/plans/completed/2026-10-08-pet-company-project-profile.md, which kept company and unclassified profiles strict; this plan records the operator direction reversing that choice.

## Why

A company closeout was blocked by a valid internal link, and the operator directed that PII and sensitive-data content scanning be excluded for company projects and private pet projects. Today only private pets drop the public-artifact family, they still run the credential family, and every other profile runs both families.

## Gist & Examples

TLDR: the sensitive-data-scan gate skips both content arms for company and private-pet profiles, per the operator's 2026-10-12 direction; driving force external.

Before: a company repository stages a plan line with an internal tracker link; the gate fails the commit on the public-artifact family. A private pet stages a credential-shaped line; the credential family fails it.

After: the same company and private-pet profiles pass with no content-arm scan (the result message names the profile exemption). A public pet and a repo whose `project_type` does not resolve to an exempt profile still fail on both families exactly as today. The push-range audit (attribution and employer-brand) and the skills-repo hygiene arm run for every profile as before.

Edge cases: facts values are read case-insensitively with exact-match semantics (`"COMPANY"` is company; `"pet"` with `"PRIVATE"` is a private pet), so the exemption rides the existing `GateContext.project_type` and `GateContext.artifact_visibility` resolution unchanged; a pet whose visibility does not resolve to private (missing, malformed, or public) reads public and stays strict; a company declaration exempts regardless of visibility, including a malformed visibility value; the strict rows' gate messages keep naming both families. The exemption is declaration-trusted: it reads the untracked working-tree facts fresh per gate run, so a well-formed but false declaration is honored and the profile is flippable within the same landing; the strict fallback covers an unresolvable `project_type` or a pet visibility that does not resolve to private, and well-formed declarations are honored as declared (a public declaration keeps strict).

## Outcome

Company and private-pet closeouts are no longer blocked by the sensitive-data content patterns, while every other profile and every non-content protection keeps today's behavior.

- Company and private-pet profiles pass the gate with the content arms skipped; the result message names the profile-scoped exemption.
- Public pets and profiles whose facts do not resolve to the exemption (missing, malformed, or unrecognized `project_type`; pet whose visibility is not private) keep the full strict scan (both families).
- The `Co-authored-by` prohibition, the employer-brand push-range matching, and the skills-repo hygiene arm stay active for every profile.
- The policy change and the operator direction are recorded in the shared instructions and the lib comment block, reversing the profile plan's strict-company choice on the record.

Gate delta: one existing gate's refusal surface shrinks for two declared profiles (the staged-content and untracked-content arms' pattern matching drops for company and private-pet; both families). Pricing: explicit user decision, the operator direction recorded in docs/history/backlog/2026-10-12-done-private-repository-visibility-scan.md with the witnessed company-closeout block. No new gate, fence, refusal class, validator, ledger, schema field, or protocol layer; no other refusal, check, or field removed. No blocking review-layer duty added.

## Assumptions

- assume Phase 1 confirmation is satisfied by the operator's standing pre-authorization for authoring runs, with the PLAN-PROMPTS entry prompt as the scope of record; basis: the operator directive "resume authoring plans one by one - at least 3 in a row" scheduled as the 20:29 run, and the authoring dispatch template's standing pre-authorization.
- assume the exemption covers both content families (credential and public-artifact) for company AND private-pet profiles, so credential-shaped content stops blocking private pets; basis: the origin row's Expected section excludes "the PII and sensitive-data scan arms" for both profiles and its Severity line names private-pet credential checks "contrary to the requested policy"; the direction's preserved classes (commit attribution, skills-repo hygiene) are exactly the non-content protections.
- assume the employer-brand leg of the push-range audit stays outside the exemption (arm 3 unchanged in both legs); basis: the redaction plan scoped visibility to the content arms only at introduction, and the entry prompt directs resolving this arm "from its introduction and current policy". Recorded residuals: a company repository's push-range audit can still block on employer-brand patterns, and extending the exemption there is a separate operator direction; credentials can land silently in exempt profiles because the content arms are the only content backstop and they never re-audit landed history after a later visibility flip to public.
- assume the skills-repo hygiene arm (arm 4) is unchanged; basis: the direction names the skills-repository public-hygiene protection as preserved.
- assume the two pattern constants stay separate constants even though strict profiles now activate both; basis: reversibility-only taxonomy with no surviving behavioral fork after this change (no profile runs exactly one family any more), priced deliberately here because the redaction plan is historical record and its tests sit inside the region this plan rewrites, so nothing external constrains the split.
- assume the existing `project_type` / `artifact_visibility` facts keys express the whole policy and no second setting is added; basis: the entry's rejected alternative and the profile plan's keys.
- assume the deployed runtime-home twin of the lib is a symlink into the main repo checkout (re-derived from disk 2026-10-12: `ls -la` shows the symlink), so behavior propagates to consumers via the main-repo merge and no byte copy occurs at execution closeout; basis: the redaction plan's "real copy" deployment model is superseded on this host.
- assume the pinned tests that encode the superseded policy are rewritten as policy witnesses citing the direction: `test_visibility_scoped_private_pet_still_fails_credentials` and `test_visibility_scoped_private_repo_still_fails_credentials` (both pin credential expectations for exempt profiles) and `test_visibility_scoped_company_ignores_private_visibility` (pins the public-artifact expectation for company), each inside the `visibility_scoped` region this plan already owns; basis: the tests pin the reversed decision, not an independent contract.
- assume the runtime-home lib twin and the employer-brand silent-landing surface are recorded here once (the Ship-when line and the residual bullet above carry them); basis: the r1 panel's residual findings; the declaration-trust property is additionally cited by Task 1's comment rewrite.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the profile matrix behaves exactly as the Outcome bullets state; every changed row has a test witness and every preserved row keeps one.
- policy fidelity: the implementation matches the direction's scope (content arms only for the two profiles) with the non-content arms untouched.
- maintainability: the exemption is one condition at one site in `gate_sensitive_data_scan`; the lib comment block and the shared-instructions sentence state the same policy.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest -q scripts/test_done_sweep_gates_lib.py -k "visibility_scoped or push_range_audit or hygiene_child"` passes from the repository root with the new and rewritten witnesses plus the preserved push-range and hygiene-child pins.
- The company-exemption (including the malformed-visibility row), private-pet-exemption, public-pet-strict, pet-with-non-private-visibility-strict, and missing-or-invalid-project-type-strict rows each have a named test.
- The lib comment block and the gate's families message state the profile exemption and its declaration-trust property; the shared instructions carry the direction record.
- The no-em-dash scan and the public-hygiene scan pass over the changed bytes.

**Ship when:** consumer repositories pick the behavior up when the main-repo merge lands (the runtime-home lib is a symlink into the main checkout on this host, so no closeout copy step exists); a company repository declares `project_type = "company"` in its existing facts document (no new key).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (the profile comment block above the pattern constants and `gate_sensitive_data_scan` only; all other functions in this file are frozen; reject any review finding that touches them)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (the `visibility_scoped` test region only; all other tests are frozen)

**Documentation:**
- `docs/AGENTS.md` (the pet/company artifacts policy bullet)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/facts_paths.py`; reason: read-only reuse for the facts keys, unchanged.
- `scripts/scan-public-hygiene.sh`; reason: the hygiene arm's child scan, untouched by the profile exemption.
- `agents/skills/bootstrap-ai-playbook/SKILL.md`, `agents/skills/using-skills/SKILL.md`; reason: the profile facts keys and the bootstrap interview are unchanged; company needs no visibility key.
- `scripts/done_run.sh`; reason: consumes the gate through the registry; no consumer change.
- `docs/history/plans/completed/`; reason: the introducing plans are historical record, cited not edited.

## Validation Commands

Run from the repository root. The three positive pins fail against today's bytes and flip GREEN when their tasks land (rule 19 RED-today evidence recorded in the preamble). The forbidden sweeps target only the swept production or test files, never this plan; the forbidden test-file sweep enforces the two credential pins, and the widened selector enforces the company pin (its rc flips under the implementation, failing the rewritten test until it lands).

Authoring-time rule 29 record: the no-em-dash scan, the public-hygiene scan, the readiness pre-round invocation, the rule 19 RED-today probes, and the rule 22 mechanical audit (each pinned span exactly once in its owning snippet, plus `bash -n` over this block) run over these bytes before round 1, and their outcomes append below as Recorded lines.

Recorded 2026-10-12 (authoring session sess_9f5841ba, over the committed v1 bytes on branch authoring/done-sensitive-scan-profile-boundary): fix_plan_em_dashes.py 0 substitutions; `bash scripts/check-no-em-dash.sh touched` exit 0; public-hygiene scan final line `OUTCOME: pass`; `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-12-done-sensitive-scan-profile-boundary.md` exit 0 `OUTCOME: pass` (after the gate caught two untagged Commit items in the v1 draft, tagged in the same authoring pass); rule 19 RED-today evidence: both positive pins exit 1 against the current bytes (the lib comment span and the shared-instructions span are absent today), and both forbidden pins fire today (the stale credential-universal comment is present in the lib; the superseded `private_pet_still_fails_credentials` pin is present in the test file), so each removal pin is live; the `visibility_scoped` selector passes today over the unchanged strict rows; rule 22 mechanical audit PASS (pin 1 owning snippet is the Task 1 comment item, pin 2 owning snippet is the Task 2 shared-instructions item; each span exactly once in its owning snippet, `bash -n` PASS over the Validation block). Round-start state for r1: the bytes at the commit carrying this preamble.

Recorded 2026-10-12, r1 fold re-run (sess_9f5841ba, over the post-fold bytes): the r1 panel's nine staged findings folded (the superseded-pin rewrite set enumerated with the corrected public-artifact parenthetical and the forbidden sweep broadened to `still_fails_credentials`; the strict-fallback wording rescoped with the pet malformed-visibility row named; the split retention and symlink twin assumptions repriced; the silent-landing and declaration-trust residuals recorded and prescribed into the comment rewrite; the widened selector admitting the preserved push-range and hygiene-child pins; the selector-substring and synthetic-data-preservation clauses added; overflow OF1 folded into the Task 2 clause). Battery over the amended bytes: fix_plan_em_dashes.py 0 substitutions; em-dash touched exit 0; hygiene `OUTCOME: pass`; `--pre-round` exit 0 `OUTCOME: pass`; rule 19 RED-today re-check: the added declaration-trust pin exits 1 against the current bytes and the broadened forbidden pin fires today; the widened selector runs green today over the unchanged tree (re-verified before the selector text entered the plan); rule 22 audit PASS over the new pin geometry with `bash -n` PASS. Round-start state for r2: the bytes at the fold commit carrying this preamble.

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest -q scripts/test_done_sweep_gates_lib.py -k "visibility_scoped or push_range_audit or hygiene_child"

grep -q "skips both content arms for company and private-pet profiles" scripts/done_sweep_gates_lib.py || { echo "lib comment does not state the profile exemption"; exit 1; }

grep -q "declaration-trusted" scripts/done_sweep_gates_lib.py || { echo "lib comment does not state the declaration-trust property"; exit 1; }

grep -q "skips the sensitive-data content arms for company and private-pet profiles" docs/AGENTS.md || { echo "shared instructions do not carry the direction record"; exit 1; }

if grep -q "active in every repository regardless" scripts/done_sweep_gates_lib.py; then echo "stale credential-universal comment survived"; exit 1; fi

if grep -q "still_fails_credentials" scripts/test_done_sweep_gates_lib.py; then echo "superseded policy pin survived"; exit 1; fi
```

### Task 1: skip both content arms for exempt profiles

Context surface: the plan's Terms, this task, and the origin row's Expected section; referenced, never restated.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `gate_sensitive_data_scan` in `scripts/done_sweep_gates_lib.py`

- [x] `gate_sensitive_data_scan` delivers the profile exemption: given repo facts recording `project_type = "company"` and a staged line matching the public-artifact family, expects gate exit 0 with a result message naming the profile-scoped exemption and no content-arm scan; a second row records a malformed `artifact_visibility` value beside the company declaration expecting the same exemption [class: REPOSITORY_TEST]
- [x] Policy witness (direction flip): given repo facts recording `project_type = "pet"` with `artifact_visibility = "private"` and a staged credential-shaped line, expects gate exit 0 under the profile exemption [class: REPOSITORY_TEST]
- [x] Rewrite-set witness: the rewrite set covers all three superseded tests (`test_visibility_scoped_private_pet_still_fails_credentials`, `test_visibility_scoped_private_repo_still_fails_credentials`, `test_visibility_scoped_company_ignores_private_visibility`), each replacement citing the direction in its docstring [class: REPOSITORY_TEST]
- [x] Strict retention witness: given repo facts recording `project_type = "pet"` with `artifact_visibility = "public"` and a staged public-artifact line, expects gate failure naming the credential+public-artifact families, unchanged from today [class: REPOSITORY_TEST]
- [x] Strict fallback witness: given repo facts with no `project_type` key, a malformed `project_type` value, and a pet row whose `artifact_visibility` is absent or malformed, a staged public-artifact line expects gate failure in all three cases [class: REPOSITORY_TEST]
- [x] Safety witness (preserved arm): given repo facts recording `project_type = "company"` and a push-range commit message carrying a `Co-authored-by` trailer, expects the attribution finding to still fail the gate [class: REPOSITORY_TEST]
- [x] Rewrite the profile comment block above the pattern constants and the exemption branch plus families message in `gate_sensitive_data_scan`; the comment block states that the profile exemption skips both content arms for company and private-pet profiles and that the exemption is declaration-trusted (untracked working-tree facts read fresh per gate run, flippable within the same landing); the non-exempt branch runs both families for every non-exempt profile [class: IMPLEMENTATION_REQUIRED]
- [x] Every new witness name carries the `visibility_scoped` substring so the freeze and the widened selector admit it [class: REPOSITORY_TEST]
- [x] Run → expect RED: the selector fails on the new exemption and flip witnesses before the implementation lands [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the whole widened selector passes with the rewritten and new witnesses and the preserved push-range and hygiene-child pins [class: REPOSITORY_TEST]
- [x] Commit: `feat: skip sensitive-data content arms for company and private-pet profiles per operator direction` [class: IMPLEMENTATION_REQUIRED]

### Task 2: record the direction in the shared instructions

Context surface: the plan's Outcome bullets and the origin row's operator direction; referenced, never restated.

Files:
- `docs/AGENTS.md`

- [x] Extend the pet/company artifacts policy bullet in `docs/AGENTS.md` with one sentence stating the done sensitive-data scan skips the sensitive-data content arms for company and private-pet profiles and stays strict for public pets and unrecognized profiles, citing the 2026-10-12 operator direction; the extension leaves the existing synthetic-data sentence unchanged and the landing commit message names the reversal of the profile plan's strict-company choice [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the shared-instructions pin in Validation Commands passes and the forbidden-comment sweeps stay clean [class: REPOSITORY_TEST]
- [x] Commit: `docs: record the sensitive-data scan profile exemption in shared instructions` [class: IMPLEMENTATION_REQUIRED]
