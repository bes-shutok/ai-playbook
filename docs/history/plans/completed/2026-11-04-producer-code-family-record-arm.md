# Plan: Producer code-family record arm

Backlog origins (scope of record):
- docs/history/backlog/2026-10-22-producer-review-findings-followups.md (the 2026-10-25 and 2026-10-30 exec-run witnesses own the range-arm and grammar-home scope; the r1/r2 finding bullets own the folded flag-surface and lens-table bullets)

Cluster: docs/history/backlog/2026-10-22-producer-self-heal-chain-grammar-dedup.md (same script family; its chain-grammar seam scope stays with that row and is not opened here)

Driving force: new-capability (primary), simplicity (secondary)

Plan review record: the staging series .ai-playbook/reviews/2026-11-04-plan-review-producer-code-family-record-arm-pd69a64a2-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)

Execution budget: 3h total, largest task 1.5h

## Terms

- producer: `scripts/produce_exec_review_record.py`, the single-truth staging-record builder this plan extends.
- code-family record: a staging review record pair whose artifact slug carries the `-code-review` token and whose `Source digest` hashes the reviewed diff range, as opposed to the plan-review record whose digest hashes plan bytes.
- range arm: the new producer CLI mode `--range <base>...<head>` that emits a code-family record pair mechanically.
- selection verifier: the `verify-digest` subcommand of `scripts/review_record_selection.py`, the freshness oracle that recomputes a code-family record's digest over the reviewed range.
- reviewed-scope digest: the SHA-256 over `reviewed_scope_bytes()` output (`scripts/corrections_record.py`), the git-layer branch diff with the `docs/history/backlog/` bookkeeping prefix excluded; the digest domain the selection verifier recomputes.
- staging pair: the Markdown record plus its `.stats.json` sidecar written under `.ai-playbook/reviews/`.
- clear-record grammar: the minimal validating record shape (the `### Panel` / `### Counts` / `### Triage outcomes` sub-sections under `## Review Statistics` and their parity fields), currently rendered only by the validator's fixture builders (`_current_clear_markdown()`, `_current_findings_markdown()` in `scripts/validate_review_staging.py`).
- grammar home: the non-test documentation surface (the validator's usage-text region) where the clear-record example will live and that staging refusals cite by repo-relative path.
- hard mode: `scripts/validate_review_staging.py --hard`, the gating invocation whose exit 0 with `OUTCOME: pass` is the acceptance oracle.
- dispatching entry: the code-family record production prompt in `docs/history/backlog/PLAN-PROMPTS.md` (the frozen authoring entry this plan was authored from).
- fold: an accepted review finding amended into the plan before the next review round.

## Why

An execute-plan round that must hand-build a code-family staging pair re-derives the record grammar from validator source across multiple produce-validate cycles, and a hand-hashed digest conflicts with the selection verifier's reviewed-scope recomputation. Both costs are witnessed (2026-10-25 and 2026-10-30) and recur per run.

## Gist & Examples

TLDR: the producer gains a `--range` arm that emits a validating code-family record pair mechanically, and the clear-record grammar gets a citable non-test home; this removes the witnessed hand-derivation cost (driving forces: new-capability, simplicity).

Before: a run needing a code-family pair copies the shape from the validator's fixture builders, hand-builds the Markdown, hand-hashes a digest, and fails staging validation on undocumented sub-sections until the shape converges; the selection verifier then refuses any digest not derived through `reviewed_scope_bytes()`.
After: `python3 scripts/produce_exec_review_record.py --range <base>...<head> ...` emits a pair whose digest the selection verifier accepts unchanged; a residual hand-builder reads the grammar home that staging refusals cite by path.

## Outcome

A run produces a validating code-family record pair in one produce-validate cycle without reading validator source.

- The producer renders the code-family truth (the fixed `-code-review` record shape) from the same findings-row CLI schema it already owns.
- The emitted `Source digest` equals the selection verifier's recomputation over the same range.
- The clear-record grammar example lives beside the validator's usage text, and the three record-grammar diagnostics cite that home by repo-relative path on their existing channels.
- The duplicated lens tables collapse into one producer constant, and the flag surface renders only truths the builder emits (`--review-type` is gone).

Gate delta: no gate, validator, lock, ledger, schema field, or dispatch-pausing condition is added. Added producer-input refusal classes: unresolvable or option-shaped range halves, bookkeeping-only range, empty reviewed scope, and the mutually-exclusive-flag usage errors - each refusal-surface growth priced by the paying sibling removals in this plan (`--review-type` deleted, `--review-mode` narrowed to the rendered set, one duplicated lens table eliminated) and by the two witnessed incidents on the origin row; the validator refusal-message citation pointer is priced the same way. One producer flag (`--review-type`) is removed.

## Assumptions

- The range arm's digest derives through `reviewed_scope_bytes()` (`scripts/corrections_record.py`), never a raw `git diff` hash; basis: the 2026-10-31 witness on the origin row where a raw-hash record passed staging but the selection verifier refused it, and the verifier imports the same helper for its recomputation.
- The selection verifier's code-family digest domain stays unchanged; basis: the dispatching entry (`docs/history/backlog/PLAN-PROMPTS.md`, the code-family record production prompt) instructs "Keep the selection verifier's code-family digest domain unchanged unless the plan shows the range arm cannot carry it", and the range arm emits exactly the recomputed domain, so no conflict arises.
- Both arms ride one plan because they edit one file family (`scripts/produce_exec_review_record.py`, `scripts/validate_review_staging.py`); basis: the seam rule against splitting a shared-file set, and the dispatching entry pricing "or both" against the witnessed per-run cost.
- The folded bullets (mode narrowing, lens-table single-homing) ride the same touch; basis: the dispatching entry's fold instruction and the r1 `simplification#flag-surface-wider-than-truth` and `simplification#lens-table-literal-duplication` findings naming the same file.
- The chain-grammar pre-flight seam stays with `docs/history/backlog/2026-10-22-producer-self-heal-chain-grammar-dedup.md`; basis: that row's own seam scope note and the dispatching entry listing it as the seam row, not this plan's scope.
- `vrs.REQUIRED_PANEL_LENSES` is already imported by the producer (used at the panel-lens collection site); basis: read of `scripts/produce_exec_review_record.py` line 508 at authoring time.
- Smaller-design comparison recorded (source-resolved in-scope choice): producer arm alone removes the per-run cause but leaves residual hand-builders re-deriving the grammar; grammar home alone shortens convergence but every run still hand-builds and hand-hashes; both together remove the witnessed cost at its cause and give refusal citations a target, at the price of one extra task on an already-touched file family. Both selected.
- Unresolvable range halves classify as `tool_error` exit 3, the established class for the missing-plan-file input-resolution family; basis: the producer's outcome contract docstring pins that family at exit 3, and the range analog carries the same ownership.
- Digests at execution are re-derived from disk before any digest-sensitive step; basis: repository guidelines' precision-critical re-derivation rule.

Decision points requiring a grill: none remain.

## Standing constraints

- `agents/skills/` text stays out of scope for this plan's tasks: the digest-family routing paragraphs in execute-plan Step 3.1 (the lines stating the producer emits plan-family records only and that verify-digest never accepts a producer record) are made stale by this plan's range arm; the 2026-10-31 witness on the origin row already defers that amendment to a separate skill change, and this plan's execution leaves the tracked landing path for it on the origin row (Task 3), so no counterpart is stranded silently.
- The producer stays creation-only: existing records are never touched and nothing is ever repaired.
- `scripts/validate_review_staging.py` edits touch refusal message text, the usage-text region, the fixture-side pointer beside the example-bearing fixture builders, the selftest pin-cell re-pins the edited messages necessarily move, and the new standing grammar-home selftest cell; no validation arm's accepted set widens or narrows, and the two non-gating warning sites are never promoted to errors.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the emitted pair passes `--hard` validation on the first attempt, and the selection verifier accepts its `Source digest` over the recorded range.
- maintainability: one lens-to-workers association constant in the producer; the Markdown and sidecar builders both read it.
- discoverability: a hand-builder converges using only the citation a refusal prints.
- scope containment: no `agents/skills/` file changes, the verifier digest domain is unchanged, and no chain-grammar bytes move.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_produce_exec_review_record.py -q` passes.
The telemetry suite passes: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_invocation_telemetry.py -q` (its refusal-line baseline re-pinned in the same commit as the citation edits).
- `python3 scripts/validate_review_staging.py --selftest` passes.
- A produced range-mode pair passes `python3 scripts/validate_review_staging.py <record> --hard` with `OUTCOME: pass`.
- Produced at the final branch HEAD, `python3 scripts/review_record_selection.py verify-digest --record <emitted record> --dir <reviews dir> --base <base> --expect-head <head>` accepts the emitted digest (the check is HEAD-freshness-coupled: produce at the final HEAD, then verify).
- The grammar diagnostics print the citation path and the cited file contains the example.
- `--review-type` is absent from the CLI and `--review-mode` accepts only the modes the builder renders, on both the flag and the findings-JSON surfaces.

**Ship when:**
- none; repository-internal tooling improvement.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/produce_exec_review_record.py` (Task 1) *(edit; Tasks 1-3 edit this file)*
- `scripts/validate_review_staging.py` (Task 3) *(edit; refusal text, usage-text region, fixture-side pointer, moved-message selftest pin-cell re-pins, new standing grammar-home cell)*
- `docs/history/backlog/2026-10-22-producer-review-findings-followups.md` (Task 3) *(edit; tracked landing path note only)*

**Tests:**
- `scripts/test_produce_exec_review_record.py` (Task 1) *(edit; Tasks 1-2 edit this file)*
- `scripts/test_invocation_telemetry.py` (Task 3) *(edit; refusal-line baseline re-pin)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/review_record_selection.py`; reason: the verifier's digest domain is contractually unchanged.
- `scripts/corrections_record.py`; reason: import-only consumer of the existing helper.
- `agents/skills/**`; reason: standing constraint, skill text stays out of scope (the tracked landing path lives on the origin row, Task 3).
- `scripts/validate_review_staging.py` validation arms beyond refusal text and the usage region; reason: no accepted-set change is priced here.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_produce_exec_review_record.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_invocation_telemetry.py -q
python3 scripts/validate_review_staging.py --selftest
python3 scripts/validate_review_staging.py <emitted-record-path> --hard
```

### Task 1: Range arm emitting the code-family truth

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/produce_exec_review_record.py` *(edit)*
- `scripts/test_produce_exec_review_record.py` *(edit)*

Primary class anchors:
- `produce` in `scripts/produce_exec_review_record.py`
- `build_markdown` in `scripts/produce_exec_review_record.py`

- [x] `produce` accepts `--range <base>...<head>` as the source-flag alternative to `--plan` (mutually exclusive, one required): given a range invocation, expects a written pair whose record title is the code-family truth, whose filename follows the family's suffix form `{date}-{artifact-slug}-code-review-r{N}.md`, and whose sidecar declares `source_kind: "code"` [class: IMPLEMENTATION_REQUIRED]
- [x] Range-derived record surfaces: given a range invocation, expects the title, URL or Artifact, and digest annotation lines to derive from the recorded base and head with no plan reference, and the `Source digest` to equal the SHA-256 of `reviewed_scope_bytes()` output for that range [class: IMPLEMENTATION_REQUIRED]
- [x] Range inputs resolve before any git call: given a base or head half beginning with `-` or unresolvable through `corrections_record.resolve_commit`, expects the named `tool_error` refusal (exit 3, final `OUTCOME: tool_error` line, the established missing-input class) before any `reviewed_scope_bytes` call and no pair written [class: IMPLEMENTATION_REQUIRED]
- [x] Helper outcome routing: given a `SCOPE_BOOKKEEPING_ONLY` outcome, expects a named pre-write refusal with no pair written; given an empty reviewed scope (equal base and head or otherwise zero filtered bytes), expects the same refusal (a digest over empty bytes is never minted) [class: IMPLEMENTATION_REQUIRED]
- [x] Flag-surface refusals: given both `--plan` and `--range`, expect the usage tool error; given neither, expect the usage tool error; each asserts the final OUTCOME line [class: REPOSITORY_TEST]
- [x] Digest correctness: given a mixed range (reviewed paths plus the bookkeeping prefix the reviewed-scope helper excludes), expects the emitted digest to differ from the raw diff hash and to equal the selection verifier's recomputation (the exclusion is observable in the digest); the two non-circular automated legs are the raw-hash inequality and a subprocess `verify-digest` call with cwd set to the scratch repo [class: REPOSITORY_TEST]
- [x] Range-mode surface pins: the explicit `--artifact-slug` is required in range mode (the plan-stem default has no input); the `- Type:` line renders the code-family truth's own label; the findings-JSON `plan` cross-check is relaxed or re-pointed for range mode; the repo root resolves from an explicit range-mode source (the out-dir anchor), never the ambient cwd [class: IMPLEMENTATION_REQUIRED]
- [x] `extensions.certified_range` records the base and head of the emitted record's range (the existing optional sidecar field; no schema change) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the range-arm behavior's failing checks (hermetic scratch-git-repo fixtures under TemporaryDirectory per the `scripts/test_corrections_record.py` pattern, cwd pinned) are selected at execution from repository evidence [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: producer range arm emits code-family record pairs` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Flag surface and lens-table single-homing

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/produce_exec_review_record.py` *(edit)*
- `scripts/test_produce_exec_review_record.py` *(edit)*

Primary class anchors:
- `build_context` in `scripts/produce_exec_review_record.py`
- `build_payload` in `scripts/produce_exec_review_record.py`

- [x] `--review-type` is removed from the CLI; given any invocation naming it, expects the argparse usage tool error (exit 3, final `OUTCOME: tool_error` line) [class: IMPLEMENTATION_REQUIRED]
- [x] The narrowed mode set is named in the task's implementation and enforced once in `build_context` (the funnel both surfaces share), with the argparse `choices` derived from that same constant so both refusals name one set; the set covers the modes the builder truthfully renders for findings-bearing rounds [class: IMPLEMENTATION_REQUIRED]
- [x] Clean-round contradiction ownership: the clean-round contradiction (a clean verdict under a non-full-panel mode) stays owned by the two existing guards - the producer's last-fix freshness gate pre-write for last-fix-carrying clean rounds, and the validator's clean-verdict contradiction post-write for the no-last-fix subset [class: IMPLEMENTATION_REQUIRED]
- [x] Mode-set refusal on both surfaces: given an out-of-set mode via the findings JSON with the flag omitted, expects a named refusal naming the supported set [class: REPOSITORY_TEST]
- [x] The five worker/lens associations single-home in one ordered producer constant (rendered strings never iterate a frozenset directly; order normalized, worker order riding the canonical insertion order); the discriminating witness asserts both surfaces' rendered associations equal the projection of `vrs.REQUIRED_PANEL_LENSES` [class: IMPLEMENTATION_REQUIRED]
- [x] `ctx["verdict_field"]` computes in `build_context` so `build_markdown` and `build_payload` are pure readers; given either builder called twice, expects identical output with no context mutation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED then GREEN for the changed surface; the pre-existing suite stays green [class: REPOSITORY_TEST]
- [x] Commit: `refactor: narrow producer flag surface and single-home lens tables` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Grammar home, refusal citations, and contract-note corrections

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/validate_review_staging.py` *(edit)*
- `scripts/produce_exec_review_record.py` *(edit)*
- `scripts/test_invocation_telemetry.py` *(edit)*
- docs/history/backlog/2026-10-22-producer-review-findings-followups.md *(edit; tracked landing path note)*

Primary class anchors:
- `validate_staging_file` in `scripts/validate_review_staging.py`

- [x] The clear-record example is copied into the validator's usage-text region as the grammar home, built from (or byte-pinned to) the fixture builders' rendering, carrying the current-dated contract shape with its date fences annotated; a standing selftest cell validates the housed example passes `validate_staging_file` (the cell is the permanent accepted-set witness for the home); the fixture builders keep a pointer comment naming the home [class: IMPLEMENTATION_REQUIRED]
- [x] The three record-grammar diagnostics each name the citation path of the grammar home on their existing channels: the `### Panel` error line (its citation joins the message beside the skill-pointer parenthetical, so the pointer table and its exact-suffix mapping pin hold unchanged) and the two or-gated warning lines whose disjunctions stay byte-intact and are never promoted to errors [class: IMPLEMENTATION_REQUIRED]
- [x] Citation witness: given the both-missing shape per site (sub-section and its alternative absent), expects the diagnostic line on the same channel that carried each message before (ERROR for Panel, WARN for the other two) carrying the citation path [class: REPOSITORY_TEST]
- [x] The telemetry suite's byte-exact refusal baseline re-pins in the same commit (the citation edit necessarily moves `VRS_REFUSAL_LINES`, and the usage block edit may move `VRS_USAGE`) [class: IMPLEMENTATION_REQUIRED]
- [x] The validator selftest's byte-exact printed-line pin cells that the citation placement moves re-pin in the same commit (the malformed-fixture first-diagnostics cell and its companion), and the standing grammar-home selftest cell lands within the same declared edit surface [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given the citation edit applied, expects every validation arm's accepted set unchanged (a previously passing record still passes, a previously failing record fails with the same class, only the message text gains the pointer), witnessed by `python3 scripts/validate_review_staging.py --selftest` [class: REPOSITORY_TEST]
- [x] The producer's module docstring is corrected in the same touch that adds the grammar-home note: the family-boundary sentence (the producer now emits both plan-family and code-family records), the raw-diff digest description (the code-family digest derives through `reviewed_scope_bytes()`), and the Usage block (the `--range` form) [class: IMPLEMENTATION_REQUIRED]
- [x] The tracked landing path for the stranded execute-plan Step 3.1 amendment is recorded on the origin row: a dated note naming the plan-family-only routing sentence and the repeatable-minter sentence in the execute-plan skill (both made stale by this plan's range arm), whose amendment stays with the separate skill change the 2026-10-31 witness already defers [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the producer suite (pytest collector form), the telemetry suite (pytest collector form), and the validator selftest [class: REPOSITORY_TEST]
- [x] Commit: `docs: single-home clear-record grammar and cite it from staging refusals` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-10-22-producer-review-findings-followups.md (consumed origin, deleted with this completion pass): its range-arm and grammar-home scope, the r1/r2 folded flag-surface and lens-table bullets, and the tracked landing path for the deferred execute-plan Step 3.1 amendment are all carried by this plan (Tasks 1-3, landed on the run branch); the row's residual findings live on in docs/history/backlog/2026-11-04-producer-plan-review-residuals.md (filed at the r3 certification, still open, NOT covered here).
- docs/history/backlog/2026-10-22-producer-self-heal-chain-grammar-dedup.md: cluster row only; not consumed by this plan, stays open at the backlog top level (its chain-grammar seam scope was never opened here).
