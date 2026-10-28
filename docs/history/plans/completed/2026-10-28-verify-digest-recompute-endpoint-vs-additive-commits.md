# Plan: verify-digest corrections re-bind arm for additive post-landing commits

Backlog origins (scope of record):
- docs/history/backlog/2026-10-27-verify-digest-recompute-head-vs-expect-head.md

```toml
date = "2026-10-28"
backlog_origins = [
  "docs/history/backlog/2026-10-27-verify-digest-recompute-head-vs-expect-head.md",
]
driving_force = "reliability"
execution_budget = "2 hours"
review_full_panel_rounds = "2"
```

Driving force: reliability
Authoring claim: docs/tmp/authoring-claims/verify-digest-recompute-endpoint-vs-additive-commits.md (session zcode-auth-188b5264-002140Z)

## Terms

- **verify-digest**: the `verify_digest` subcommand of `scripts/review_record_selection.py` - read-only; recomputes the reviewed-scope digest over `base...HEAD` through `corrections_record.diff_bytes` and refuses a record whose sidecar `source_digest` disagrees, routing the refusal to the staging validator's corrections arm.
- **Corrections chain**: the sidecar `extensions.corrections` rows whose verified chain the staging validator's corrections arm verifies; a chain whose terminal binds the current bytes and HEAD yields the accepted-stale pass.
- **Additive delta**: commits landing on the base branch between the recorded verified head and current HEAD whose changed paths are disjoint from the record-scope paths (the witnessed class: record-capture-only backlog rows landed after the reviewed delta); an empty delta (a pure HEAD move) is not additive - it refuses as vacuous.
- **Record-scope paths**: operationally, the changed-path set of `git diff --name-only <base>...<expect_head>` - the reviewed window the recorded digest was computed over - derived at re-bind time from git; a delta path outside that set is additive for this record.
- **Re-bind**: writing a verified corrections row (with its delta-path witness) that binds the record's digest and the moved HEAD through the existing corrections-chain machinery, so verify-digest's accepted-stale pass admits the record without a fresh round.

## Why

The freshness gate is the operative staleness instrument for review records, but every additive record-capture commit on the base branch between a landing and its verification re-prices the record: the witnessed session recovered only through a manual corrections re-bind (verify the post-landing delta by hand, edit the record's digest line and sidecar). The refusal is workable and deliberately live-HEAD (the introduction intent refuses rather than verify against an unknown HEAD), so the endpoint-honoring alternative stays rejected; the gap is the missing explicit writer for the additive case. One bounded subcommand converts the witnessed manual procedure into an auditable command with its delta-path witness recorded, keeping the fail-closed refusal for genuine scope drift.

## Gist & Examples

TLDR: add an explicit corrections re-bind subcommand beside verify-digest so an additive no-record-scope-delta commit re-binds a record through the existing corrections chain with its delta-path witness recorded, and update the verify-digest refusal and help text to route there (reliability: the witnessed freshness gate keeps refusing genuinely stale records while record-capture commits stop forcing manual re-binds).
- Title: verify-digest corrections re-bind arm for additive post-landing commits
- Before: verify-digest recomputes over live HEAD only; any additive base-branch commit after the recorded verified head forces a manual digest re-bind (three-file witness) or a spurious fresh round; `--expect-head` is comparison-only.
- After: verify-digest stays read-only with unchanged outcome vocabulary and exit contract; a new explicit subcommand recomputes, proves the `expect_head..HEAD` delta touches zero record-scope paths, writes the corrections row with the delta-path witness, and the next verify-digest passes through the corrections chain's accepted-stale precedence; the help text names the route.
- Edge cases: a delta that touches any record-scope path refuses fail-closed exactly as today; a chain that cannot carry the record still refuses; the re-bind is caller-invoked, never automatic inside verify-digest.

## Outcome

The witnessed manual re-bind procedure becomes one explicit command with its delta-path witness recorded in the corrections chain; verify-digest keeps its live-HEAD freshness intent, its refusal vocabulary, and its exit contract byte-stable; the help text routes the additive case to the new subcommand; the selftest covers both refusal classes and the re-bind pass.

Gate delta: none net - the re-bind arm is an explicit corrections-chain write path on the existing corrections machinery (no row-schema extension), never a new gate, refusal class, lock, ledger, or ceremony; the moved-HEAD refusal message stays byte-identical.

## Standing constraints

- verify-digest stays read-only: no write path is added inside it; the re-bind is a separate caller-invoked subcommand.
- The fail-closed classes stay fail-closed: a delta touching any record-scope path refuses; an absent, backup-shaped, orphaned, or unreadable-digest record refuses exactly as today.
- No new gate, validator, lock, ledger, or ceremony; the corrections chain, its verification arm, and the outcome vocabulary (`OUTCOME:` lines, exit codes) stay byte-stable.
- The `--expect-head` operand stays comparison-only: it never becomes the recompute endpoint (the freshness intent refuses rather than verify against an unknown HEAD).
- Machinery admission (per the repository guidelines): the addition extends an existing validator surface with one bounded behavior; incident: docs/history/backlog/2026-10-27-verify-digest-recompute-head-vs-expect-head.md (witnessed once, 2026-10-27); expected catch frequency: every additive base-branch commit between a landing and its record verification; false-positive cost: an incorrect re-bind could bless a stale record, bounded by the zero-record-scope-path check over the recompute delta and the recorded delta-path witness; sunset/review: review at the next digest-family touch beside docs/history/backlog/2026-10-22-producer-review-findings-followups.md.

## Evaluation Criteria

- Quality: the subcommand refuses (exit contract unchanged) when the delta touches any record-scope path, when the record or chain is malformed, or when the operands do not resolve; on success it writes exactly one corrections row carrying the delta-path witness and the new digest/HEAD binding, and a following verify-digest returns the accepted-stale pass naming both heads.
- Done when: the selftest covers both refusal classes (genuine scope drift stays fail-closed; the additive case re-binds and passes), the verify-digest help text and refusal text name the route, and the outcome vocabulary and exit contract are byte-stable.
- Ship when: the record-selection suite, the plan-readiness regression, the public hygiene scan, and the em-dash gate all pass.

## Review Scope

**Explicit must-fix:**
- `scripts/review_record_selection.py` (Task 1, Task 2): the re-bind subcommand and the verify-digest help/refusal routing text.
- `scripts/test_review_record_selection.py` (Task 2): the selftest coverage.

**Plan-related extension:** none.

### Task 1: Re-bind subcommand with delta-path witness

- [x] Add an explicit `re-bind` subcommand to `scripts/review_record_selection.py` that recomputes the reviewed-scope digest over the recorded base through the canonical derivation, derives the record-scope path set as `git diff --name-only <base>...<expect_head>`, and computes the `expect_head..HEAD` delta paths. [class: IMPLEMENTATION_REQUIRED]
- [x] Bind the delta anchor to the record's own recorded verified head (the manifest/chain-after-head derivation verify_digest documents): refuse on disagreement with the caller operand and refuse when the anchor is not an ancestor of HEAD; refuse when `--base`/`--expect-head` cannot be tied to the record's recorded state, and refuse the empty-delta subclass (a pure HEAD move) as vacuous. [class: IMPLEMENTATION_REQUIRED]
- [x] Refuse fail-closed when any delta path intersects the record-scope path set or when any existing record-state refusal fires; on success write the verified corrections row into the sidecar's `extensions.corrections` in the chain's serialized form (the subcommand is the writer beside verify_digest). [class: IMPLEMENTATION_REQUIRED]
- [x] Mint the row born-conformant through `corrections_record.py`'s schema builder (row_keys + validate_row), carrying the delta-path witness in the schema-tolerated hunk `header` free text (one hunk per additive commit/path), and reuse the locked writer's flock-plus-expect_sha256 discipline for the nested location. [class: IMPLEMENTATION_REQUIRED]
- [x] Grade the resulting chain through the staging validator's grading owner (`code_delta_classifier.verify_code_corrections`, the corrections arm's actual delegate; r1 review fold) and refuse on any leg failure; records without a resolvable round seal entry cannot re-bind. [class: IMPLEMENTATION_REQUIRED]

Files: `scripts/review_record_selection.py`
Primary class anchors: `verify_digest` (the recompute leg the subcommand reuses), the corrections-chain writer beside it.

### Task 2: Routing text and selftest coverage

- [x] Update the verify-digest help text and exactly one refusal message - the digest-mismatch stale refusal's routing tail - to name the re-bind subcommand for the additive case; the moved-HEAD refusal stays byte-identical, and the verify-digest JSON outcome keys (fresh/accepted-stale) and exit codes stay byte-stable. [class: IMPLEMENTATION_REQUIRED]
- [x] Add selftest coverage: the genuine scope-drift refusal stays fail-closed; an additive delta the grading owner's classification leg accepts (comment-only script hunks, with seal-path captures beside them) re-binds with a recorded witness and the following verify-digest passes as accepted-stale naming both heads. [class: REPOSITORY_TEST]
- [x] Add selftest coverage: the witnessed Markdown record-capture class refuses at grading and routes to a fresh round (r2 review fold: the corrections arm's delegate classifies comment-only script hunks only); the written row grades verified through the corrections arm; the stale-refusal message and help text name the re-bind subcommand. [class: REPOSITORY_TEST]
- [x] Run the record-selection suite, the plan-readiness regression, the public hygiene scan, and `bash scripts/check-no-em-dash.sh touched`. [class: REPOSITORY_TEST]

Files: `scripts/review_record_selection.py`, `scripts/test_review_record_selection.py`
Primary class anchors: the stale-refusal message text (routing update), the selftest's two refusal-class cases.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_review_record_selection.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_plan_readiness.py -q
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh touched
```

## Assumptions

- The sidecar's `extensions.corrections` chain is written by the subcommand itself in the chain's serialized form; `corrections_record.py`'s existing `append_corrections` writes a different (top-level) document shape, so only its row validation and lock discipline are reused, never its write target; the row is minted in the conformant delta-anchored shape and graded through `code_delta_classifier.verify_code_corrections` with `extensions.certified_range` written when absent (r1 review fold: the raw verifier's grading legs under-arm the row against the corrections arm's ref rules).
- Record-scope paths derive from git over the recorded operands (`git diff --name-only <base>...<expect_head>`); the record pair carries no path list, and the operands are validated against the record's recorded state before any derivation is trusted.
- The witnessed additive class (backlog capture rows outside the plan scope) turned out to be outside the grading owner's classification leg (comment-only script hunks only; r2 review fold), so the served classes are comment-only script deltas, with seal-path captures beside them (a seal-only delta refuses at grading), while the .md capture class still routes to a fresh round (tracked beside docs/history/backlog/2026-10-28-rebind-stale-recovery-doc-route.md); a delta mixing additive and record-scope paths takes the fail-closed refusal (the check is over the whole delta, never a filtered subset).

Decision points requiring a grill: none remain.

Scope extensions (grilled): none proposed.
