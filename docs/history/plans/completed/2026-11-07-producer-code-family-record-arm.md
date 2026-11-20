# Plan: Producer chain-grammar validator seam

Backlog origins (scope of record):
- docs/history/backlog/2026-10-22-producer-self-heal-chain-grammar-dedup.md

Cluster: docs/history/plans/completed/2026-11-04-producer-code-family-record-arm.md (same-file-family sibling; its Disposition keeps this origin open and deferred this exact seam scope)
Cluster: docs/history/backlog/2026-11-04-producer-plan-review-residuals.md (sibling plan-review document residuals; not consumed here)

Driving force: code-quality

Plan review record: the staging series .ai-playbook/reviews/2026-11-07-plan-review-producer-code-family-record-arm-p919d9f5f-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 2.5h total, largest task 1.5h

Executed: yes (e3b469906, the executed branch tip at archive time; the branch rebased onto main before landing, so the pre-rebase executed content fb5e2141a+e99c381bc+fc8b7b291 reads e6f91033a+a32e0762e+82f20a927 post-rebase)

Authoring claim: 2026-10-22-producer-self-heal-chain-grammar-dedup.md (session sess_9bf1d02c-275a-4bcb-84da-7aa2d6380be2)

## Terms

- producer: `scripts/produce_exec_review_record.py`, the single-truth staging-record builder.
- validator: `scripts/validate_review_staging.py`, the staging grammar's enforcement point.
- seam: the new public derivation helpers in the validator (`well_formed_self_heal_state`, `valid_prior_chain_state`, `self_heal_chain_state`, `calendar_valid_record_date`), promoted from the producer's current chain block.
- self-heal chain state: the `extensions.convergence.self_heal_attempt` member: `status` of `unused`, `consumed`, or `unknown`, a 32-hex `run_id`, and the consumed bindings (`round`, 64-hex `source_digest`).
- chain stem: the record filename's date-and-round-stripped stem shared across a review chain; a chain's members share it and differ by round suffix.
- prior round: the dated record for chain round N-1 in the output directory, keyed by chain stem and round suffix.
- ambiguous predecessor: two dated records resolving to the same chain stem and round N-1; the producer refuses.
- post-fence canonical record: a record whose name and sidecar dates classify post-fence under `SELF_HEAL_STATE_MIN_DATE` (2026-10-09) with `record_kind: "canonical"`.
- ProducerRefusal: the producer's modeled pre-write refusal exception (exit 1, `OUTCOME: fail`); its sibling `ProducerToolError` covers malformed inputs (exit 3, `OUTCOME: tool_error`); the non-calendar date refusal is a `ProducerToolError`.
- AmbiguousChainPredecessor: the validator-owned `ValueError` subclass the seam raises on an ambiguous predecessor, carrying the producer's exact refusal message text.
- ProducerToolError: the producer's malformed-input exception (exit 3, `OUTCOME: tool_error`).
- mint gate: the validator's usage-mint obligation (`validate_usage_mint_gate`), the presence-and-format check over the record's mint pair.
- enforcement arms: the validator's gate functions (`validate_self_heal_attempt_state`, `_validate_self_heal_record`, the carry-forward check); unchanged accepted and failing sets.
- hard mode: `scripts/validate_review_staging.py --hard`; the acceptance oracle.
- regenerate tool: `scripts/regenerate_review_sidecar.py`; carries its own copy of the same derivation, out of scope (omit-extension).
- omit-extension: the maintenance-selected arm's recorded scope-omission disposition: excluded from the plan, reported, no new backlog row.
- dispatching entry: the `producer-code-family-record-arm` entry in `docs/history/backlog/PLAN-PROMPTS.md` this plan was authored from.

## Why

The producer re-encodes the shared self-heal gate's chain grammar (about 60 lines across three functions) and reaches into validator privates (`vrs._date_fence`, `vrs._calendar_valid_record_date`, `vrs.ValidationResult`, `vrs.validate_usage_mint_gate`), so every grammar change must be mirrored there or higher-round production fails late at the validator instead of at the producer. The same re-encoding exists a second time in `scripts/regenerate_review_sidecar.py` and the two copies have already diverged on the ambiguous-predecessor arm, making the drift cost the origin prices concrete.

## Gist & Examples

TLDR: the self-heal chain-grammar derivation moves behind a public validator seam and the producer reads it from there, deleting the producer's copy of the grammar; this removes the producer's principal drift surface (driving force: code-quality).

Before: a change to the gate's chain grammar in the validator must be hand-mirrored into `produce_exec_review_record.py`'s block; until then, producing a round N>1 record fails only at the final hard-mode validation, after the pair is written. The producer bypasses the validator's public surface with four private reaches.
After: the derivation lives in the validator's public seam (beside the enforcement arm's own intentional twin derivation), and the producer's block, its private reaches, and its round-tail regex constant are deleted; emitted pairs, refusal texts, and the validator's enforcement sets are byte-compatible with today.

## Outcome

The producer's chain-grammar re-encoding is deleted, with the derivation living in the validator's public seam.

- The validator exposes the four derivation helpers publicly; the producer's three private copies, its `_ROUND_TAIL_RE` constant, and its private reaches are gone.
- A produced higher-round pair emits the same chain state and the same refusal texts as before the change.
- The validator's enforcement arms keep their accepted and failing sets unchanged; the seam and the enforcement derivation are cross-referenced intentional twins, and a parity witness holds them in agreement on the documented cases.
- A source-level canary pins that the producer neither re-encodes the grammar nor reaches validator privates, and that its call sites read the seam.

Gate delta: none - no gate, refusal class, hard gate, fence, protocol layer, schema field, or dispatch-pausing condition is added or removed; the seam is a public derivation surface over the grammar's existing home and the producer's private duplication is removed (surface reduction).

## Assumptions

- The three derivation functions move verbatim (logic-preserving promotion, same selection and refusal behavior); basis: the origin's fix shape is the seam, not a rewrite, and behavior preservation is the acceptance witness.
- The ambiguous-predecessor refusal crosses the seam as the validator-owned `AmbiguousChainPredecessor` (a `ValueError` subclass) carrying the producer's exact message text; the producer maps exactly that class, at the single seam call expression, to `ProducerRefusal(str(exc))`; basis: the validator cannot import the producer's exception type (dependency direction), the named-refusal posture (tool-owned named exception classes over bare raises) stays with each tool, and a named type keeps incidental `ValueError`s from being rebranded as modeled refusals.
- The seam is additive derivation surface, never a gate; basis: the dispatching entry's machinery admission ("adds no gate, validator, lock, ledger, or required ceremony").
- The mode-narrowing and lens-table single-homing bullets carry no scope here; basis: landed by the sibling 2026-11-04 plan (ad3361d25, e9d81cf5d) whose Disposition explicitly keeps this origin open ("its chain-grammar seam scope was never opened here").
- The validator's enforcement-side grammar is not replaced by the seam: the seam and the enforcement carry-forward block are intentional twin derivations, and Task 1 adds a parity witness plus cross-referencing comments holding them in agreement on the documented cases; basis: gate-bearing paths stay enforcement-owned; the origin's drift surface is the producer-side re-encoding.
- The date pre-flight reach (`vrs._calendar_valid_record_date(date_value)` in `build_context`) folds onto the public calendar surface in the same touch; basis: the origin names `_calendar_valid_record_date` in its reach set and the seam makes the public form available.
- All digests, paths, and line numbers are re-derived from disk at execution; basis: the repository's precision-critical re-derivation rule.
- Scope decision (maintenance-selected arm, simpler-design comparison recorded): the seam home is the validator itself rather than a new shared module, because the validator already owns every dependency the derivation needs and a new module adds a boundary with no third consumer; deleting the producer's pre-flights in favor of post-write arbitration was rejected per the origin's own pricing (higher-round production would then refuse only after writing a pair, breaking the no-strand posture, the refusal-before-anything-is-written discipline).
- Scope decision: `regenerate_review_sidecar.py` rewiring is omitted, confined to its diverged third function (`_self_heal_chain_state`'s silent ambiguous-prior fallback where the producer refuses): the origin names the producer only, and folding the diverged arm needs a behavior-reconciliation decision the origin never priced; its two logic-identical helpers are foldable onto the seam in a future touch with the repair-only posture unchanged and are not priced here (omit-extension, maintenance-selected arm).
- Scope decision: the origin's 2026-10-22 scope-note pre-flight duplications (the identity-tail regex `_IDENTITY_QUALIFIED_TAIL_RE`, the kebab-shape refusal, and `_NULL_LAST_FIX_TOKENS` versus the validator's `ABSENT_LAST_FIX_TOKENS`) are explicitly deferred by this plan; their durable home is this plan's landing disposition fold, mirroring the sibling plan's tracked-landing-path precedent, with no new backlog row.

Decision points requiring a grill: none remain.

## Standing constraints

- The validator's enforcement arms keep their accepted and failing sets unchanged; the seam adds public derivation surface only.
- The producer stays creation-only; every refusal behavior is byte-preserved (round selection, unknown fallback, ambiguity refusal text, and the `ProducerToolError` date arm).
- No witness pair is ever written into the real reviews series: the hard-pass witness recipe produces its r1-then-higher-round pair only under a fresh temporary directory outside `.ai-playbook/reviews/`, with a fixed synthetic run id and explicit cleanup.
- `scripts/regenerate_review_sidecar.py` is untouched (omit-extension confined to its diverged ambiguity arm; see Assumptions).
- `agents/skills/**` stays out of scope.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a produced pair passes hard mode; chain states and refusal texts byte-identical pre/post rewiring; the validator selftest stays green.
- maintainability: the producer's former copy lives only in the seam; the producer carries no chain-grammar re-encoding and no validator-private reach (source-level canary); the seam and enforcement derivations agree on the parity corpus.
- scope containment: enforcement accepted sets unchanged; the regenerate tool untouched; skills untouched.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_step31_record_validation_gate.py -q` passes.
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_produce_exec_review_record.py -q` passes.
- `python3 scripts/validate_review_staging.py --selftest` passes.
- A produced pair (r1 then the higher-round r2, produced under a fresh temporary directory outside `.ai-playbook/reviews/` with a fixed synthetic run id and explicit cleanup) passes `python3 scripts/validate_review_staging.py <record> --hard` with `OUTCOME: pass`.
- The drift canary (producer source free of the grammar re-encoding and private reaches, call sites reading the seam) passes.

**Ship when:**
- none; repository-internal tooling improvement.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/validate_review_staging.py` (Task 1) *(edit; additive public derivation seam only)*
- `scripts/produce_exec_review_record.py` (Task 2) *(edit; chain block rewired, date reach closed, docstring note)*

**Tests:**
- `scripts/test_step31_record_validation_gate.py` (Task 1) *(edit; seam canaries)*
- `scripts/test_produce_exec_review_record.py` (Task 2) *(edit; rewiring pins and drift canary)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/regenerate_review_sidecar.py`; reason: omit-extension recorded in Assumptions (diverged ambiguity arm needs its own priced reconciliation).
- `scripts/review_record_selection.py`; reason: the verifier's digest domain is contractually unchanged.
- `agents/skills/**`; reason: standing constraint.
- The validator's enforcement arms' accepted or failing sets; reason: no enforcement change is priced here.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_step31_record_validation_gate.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_produce_exec_review_record.py -q
python3 scripts/validate_review_staging.py --selftest
python3 scripts/validate_review_staging.py <emitted-record-path> --hard
```

### Task 1: Validator seam, the derivation goes public

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/validate_review_staging.py` *(edit)*
- `scripts/test_step31_record_validation_gate.py` *(edit)*

Primary class anchors:
- `validate_self_heal_attempt_state` in `scripts/validate_review_staging.py`
- `well_formed_self_heal_state` in `scripts/validate_review_staging.py`
- `valid_prior_chain_state` in `scripts/validate_review_staging.py`
- `self_heal_chain_state` in `scripts/validate_review_staging.py`

- [x] The seam canaries pin literal golden values derived from today's producer behavior; `test_step31_record_validation_gate.py` never imports `produce_exec_review_record` (no differential-oracle import whose oracle Task 2 deletes) [class: REPOSITORY_TEST]
- [x] `well_formed_self_heal_state` promoted verbatim from the producer's current bytes: given each state shape (valid unused, valid consumed with round and 64-hex source digest, unknown, wrong key set, bad run id or round form), expects the golden booleans pinned from today's behavior [class: IMPLEMENTATION_REQUIRED]
- [x] `valid_prior_chain_state` promoted verbatim: given a post-fence canonical prior whose record and sidecar both validate (fence classes, calendar dates, digest form, well-formed state, clean mint gate), expects the prior state dict; given each other prior evidence shape (missing file, malformed JSON, pre-fence, non-canonical, bad digest, state not well-formed, gate errors), expects `None` [class: IMPLEMENTATION_REQUIRED]
- [x] `self_heal_chain_state(record_path, run_id)` promoted verbatim, its promoted bytes carrying the round-tail regex constant the walk needs [class: IMPLEMENTATION_REQUIRED]
- [x] Round selection: given round 1 or unnumbered, expects `{status: unused, run_id}` [class: IMPLEMENTATION_REQUIRED]
- [x] Carry arm: given a higher round with one valid prior whose state is consumed-shaped (`{"status": "consumed", "run_id": <distinct id>, "round": "r1", "source_digest": <64-hex>}`), expects the prior state carried verbatim (a result reachable only by carrying, never by re-minting) [class: IMPLEMENTATION_REQUIRED]
- [x] Unknown and round-filter arms: given a higher round with no valid prior, expects `{status: unknown, run_id}`; given a higher round with only a wrong-round same-stem record present, expects `unknown` (the round filter honored) [class: IMPLEMENTATION_REQUIRED]
- [x] Unnumbered-candidate arm: given a higher round with an unnumbered same-stem record present, expects the unnumbered record treated as the prior candidate [class: IMPLEMENTATION_REQUIRED]
- [x] Ambiguity refusal: given two dated records for the same chain stem and prior round, expects a refusal of the seam's own `AmbiguousChainPredecessor` type carrying the producer's exact ambiguous-predecessor message text [class: IMPLEMENTATION_REQUIRED]
- [x] `calendar_valid_record_date` public surface over the private date validator (a one-line alias or a rename with the validator's internal callers following): given a calendar-valid and a non-calendar value, expects the same results `vrs._calendar_valid_record_date` returns today [class: IMPLEMENTATION_REQUIRED]
- [x] Parity witness: given a shared prior-evidence fixture corpus (valid prior, missing file, malformed JSON, pre-fence, non-canonical, bad digest, mint-gate errors, and a shape exercising the enforcement arm's `AttributeError` tolerance) run through both `valid_prior_chain_state` and the enforcement carry-forward block, expects agreement on the documented cases; the seam and the enforcement derivation carry cross-referencing comments naming them intentional twins with a change-both duty [class: REPOSITORY_TEST]
- [x] Enforcement unchanged: given the validator's existing self-heal enforcement cells (state grammar, record chain, carry-forward), expects every accepted record still accepted and every failing record failing with the same class, witnessed by the selftest [class: REPOSITORY_TEST]
- [x] Run → expect RED: the seam canaries fail on the absent public surface (import errors count as RED) [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: promote self-heal chain-grammar derivation to a public validator seam` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Producer rewired onto the seam

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/produce_exec_review_record.py` *(edit)*
- `scripts/test_produce_exec_review_record.py` *(edit)*

Primary class anchors:
- `build_context` in `scripts/produce_exec_review_record.py`
- `main` in `scripts/produce_exec_review_record.py`

- [x] The producer's three private functions (`_well_formed_self_heal_state`, `_valid_prior_chain_state`, `self_heal_chain_state`) and the `_ROUND_TAIL_RE` constant are deleted; the call sites read the seam through the existing `vrs` import with no new module boundary: given round-1 and higher-round invocations, expects emitted chain states identical to the pre-change outputs [class: IMPLEMENTATION_REQUIRED]
- [x] Ambiguity mapping: given an output directory holding two dated records for the same chain stem and prior round, expects `ProducerRefusal` carrying the exact ambiguous-predecessor message text, mapped from the seam's `AmbiguousChainPredecessor` at the single `vrs.self_heal_chain_state(...)` call expression (the try wraps exactly that expression, never the surrounding assembly) [class: IMPLEMENTATION_REQUIRED]
- [x] The date pre-flight reads `vrs.calendar_valid_record_date`: given a non-calendar `--date`, expects the same `ProducerToolError` refusal (exit 3, `OUTCOME: tool_error`) as today [class: IMPLEMENTATION_REQUIRED]
- [x] Drift canary: a source-level suite cell asserting, with pinned needle forms (`def <name>` for definitions, exact `vrs.<attr>` strings for reaches), that the producer source defines none of the three grammar functions nor `_ROUND_TAIL_RE` and reaches none of `vrs._date_fence`, `vrs._calendar_valid_record_date`, `vrs.ValidationResult`, `vrs.validate_usage_mint_gate`; positive needles requiring the `vrs.self_heal_chain_state(` and `vrs.calendar_valid_record_date(` call sites [class: REPOSITORY_TEST]
- [x] Delegation pin: monkeypatching `vrs.self_heal_chain_state` and asserting `build_context` carries its return [class: REPOSITORY_TEST]
- [x] The module docstring's self-heal chain region names the seam home (the derivation lives in `scripts/validate_review_staging.py`'s public surface) [class: IMPLEMENTATION_REQUIRED]
- [x] Emitted pair and one validator pass: given a produced higher-round pair (r1 then r2 produced under a fresh temporary directory outside `.ai-playbook/reviews/`, fixed synthetic run id, explicit cleanup), expects `python3 scripts/validate_review_staging.py <record> --hard` to end `OUTCOME: pass` [class: REPOSITORY_TEST]
- [x] Run → expect RED: the drift canary fails before the rewiring (the private definitions and private reaches are still present) [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the drift canary and delegation pin pass; the ambiguity-mapping, date-refusal, and hard-pass cells are regression pins expected green throughout; the pre-existing producer suite stays green [class: REPOSITORY_TEST]
- [x] Commit: `refactor: producer reads chain grammar from the validator seam` [class: IMPLEMENTATION_REQUIRED]

## Disposition

Executed 2026-11-07 under the operator one-shot exec mandate automation-74207943 (03:00 WET, max 1, stop after 1st), worktree-first run on branch 2026-11-07-producer-code-family-record-arm (base main@46fe276b5). Task 1 commit e6f91033a (pre-rebase fb5e2141a) (validator seam: `well_formed_self_heal_state`, `valid_prior_chain_state`, `self_heal_chain_state`, `_ROUND_TAIL_RE`, `AmbiguousChainPredecessor`, `calendar_valid_record_date` alias, canaries + parity witness); Task 2 commit a32e0762e (pre-rebase e99c381bc) (producer rewired onto the seam, drift canary + delegation pin, byte-identical outputs confirmed by differential witness); Phase 3 focused fix 82f20a927 (pre-rebase fc8b7b291) (label-aware corpus prior paths so the seam's pre-fence arm is genuinely exercised; the fix's own residual folded to docs/history/backlog/2026-11-04-producer-plan-review-residuals.md). Phase 3 full fresh-adversarial panel (2 lenses + 1 focused re-review): zero blocking findings; byte-compatibility of emitted pairs, refusal texts, and enforcement sets independently reproduced. Plan bytes drifted from the r3 certification digest by the Primary-class-anchors canonical-shape fix only (readiness pre-round re-certified green at execution start, drift reason recorded in the run manifest). Pre-existing (not plan-caused) cross-suite telemetry test order-flake recorded as docs/history/backlog/2026-11-07-producer-telemetry-test-order-flake.md. Origin row 2026-10-22-producer-self-heal-chain-grammar-dedup.md consumed by this landing (fold-deleted per the covered-row rule; its cluster pointer family retargets to this completed twin); the origin's 2026-10-22 scope-note pre-flight duplications stay deferred with their durable home in this fold per the plan's Assumptions.
