# Plan: Review-doc digest scope fix (F6: Confluence scratch-file child-page scope)

Backlog origin: `docs/history/backlog/2026-08-28-review-doc-wording-fixes.md` (F6; F11 already fixed 2026-08-29 by `docs/plans/2026-08-28-fence-scanner-consolidation.md`).
Source review: `docs/reviews/2026-08-28-review-artifact-contracts-code-review-r6.md`, finding F6 (`consistency#producer-contract-scope-gap`, Medium).

## Terms

- **Reviewed content**: the parent Confluence page plus every fetched child page, in the order Step 2 fetched them; see the worker-input list item "Full fetched document content (parent page plus child pages from Step 2)".
- **Scratch file**: the throwaway file under `{tmp_dir}` that the Step 5 mechanical gate writes so the staging validator can re-hash the reviewed bytes.
- **Mechanical gate**: the `validate_review_staging.py --hard --source-doc` invocation that fails the review report until staging and digest both pass.
- **Sidecar**: the `.stats.json` version-1 record whose `source_digest` the gate compares against the scratch file's SHA-256.

## Assumptions

- assume the concatenation fix (scratch file = full reviewed content) over softening the guarantee to parent-page bytes only; basis: the backlog item lists it first and it preserves the strong no-misattribution guarantee with no validator-code change.
- assume F11 (review-staging stale fence claim) is fully closed and out of scope; basis: backlog header status line and the fence-scanner consolidation plan Task 4.
- assume doc-only change → concise `- [ ]` action items, no RED/GREEN cycles; basis: plans skill non-behavior-change rule (the edit targets a skill instruction file, not executable code).

## Gist & Examples

`agents/skills/review-confluence-doc/SKILL.md` Step 5 defines reviewed content as parent page plus child pages, but its mechanical-gate recipe writes "the fetched page bytes" to a single per-page-titled scratch file (`...-page.md`) and hashes only that file. On a multi-page document, a producer that hashes parent-only bytes and one that hashes parent+children bytes both pass the digest gate, so the documented guarantee ("findings cannot be misattributed to page bytes that were never reviewed") over-claims: a child page's findings can be attached to a digest that never covered the child page.

The fix makes the scratch file the **concatenation of every fetched page in the order Step 2 fetched them**, so the digest deterministically covers the full reviewed content, and rewords the guarantee sentence to match (scratch file's SHA-256, full reviewed content, not a single page). The validator is unchanged: it already hashes whatever file `--source-doc` points at.

Example: reviewing page `Api Guide` with child `Api Guide Appendix`: before, a producer could write only the parent's bytes to `confluence-review-api-guide-page.md`, and the gate would still pass even though the report reviews the appendix. After, the scratch file `confluence-review-<page-title-kebab>-reviewed.md` holds parent + appendix concatenated in review order, and the gate fails if the sidecar digest covers anything less.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the recipe unambiguously defines ONE scratch file whose bytes are the full reviewed content in a deterministic order; the guarantee sentence describes exactly what the gate verifies.
- maintainability: no residual singular-page digest claim anywhere in the skill; scratch-file naming example consistent between prose and the embedded bash block.

**Done when:**
- The Step 5 mechanical-gate paragraph and embedded bash block prescribe the concatenated reviewed-content scratch file.
- The guarantee sentence pins the digest to the scratch file's SHA-256 over the full reviewed content.
- All Validation Commands pass.

**Ship when:**
- None; doc-only change, fully repo-verifiable.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/review-confluence-doc/SKILL.md`: the digest-scope clauses only: the Step 5 mechanical-gate recipe (item 4 paragraph, embedded bash block, guarantee sentence), the Step 4.7 item 1 sidecar clause, and the `review-staging` Integration-Points sentence. All other sections of this file are frozen; reject any review finding that touches them.

**Tests:**
- None; doc-only change.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/review-staging/SKILL.md`; reason: F11 closed 2026-08-29 by the fence-scanner consolidation plan.
- `~/.ai-playbook/scripts/validate_review_staging.py` and any validator source; reason: the gate already hashes the pointed-at file; no code change is in this plan.
- `scripts/plan_readiness.py`; reason: carries a foreign in-progress modification from a parallel session, unrelated to this plan.

## Validation Commands

```bash
set -u
REPO="$(git rev-parse --show-toplevel)"
F="$REPO/agents/skills/review-confluence-doc/SKILL.md"

test -f "$F" || { echo "FAIL: $F missing"; exit 1; }

# Positive obligations (one dedicated grep each)
grep -q "parent page plus every fetched child page, concatenated in the order Step 2 fetched them" "$F" \
  || { echo "FAIL: concatenation contract absent"; exit 1; }
grep -q "ONE scratch file" "$F" \
  || { echo "FAIL: single-scratch-file contract absent"; exit 1; }
grep -q "recomputes the scratch file" "$F" \
  || { echo "FAIL: scratch-file digest sentence absent"; exit 1; }
grep -q "full reviewed content, not a single page" "$F" \
  || { echo "FAIL: full-reviewed-content guarantee absent"; exit 1; }
grep -q "REVIEWED_CONTENT_PATH" "$F" \
  || { echo "FAIL: bash block not rewired to reviewed-content path"; exit 1; }

# Prose/bash naming consistency for the scratch file example
test "$(grep -c -- "-reviewed.md" "$F")" -ge 2 \
  || { echo "FAIL: scratch filename example not consistent in prose and bash block"; exit 1; }

# Embedded bash block stays syntactically valid; the fence is indented inside
# Step 5 item 4, so extraction must tolerate leading whitespace and must be
# non-empty (an empty extraction would make bash -n pass vacuously)
BLOCK="$(awk '/^[[:space:]]*```bash/{f=1;next} /^[[:space:]]*```$/{f=0} f' "$F")"
test -n "$BLOCK" || { echo "FAIL: no bash block extracted from $F"; exit 1; }
printf '%s\n' "$BLOCK" | bash -n || { echo "FAIL: embedded bash block has a syntax error"; exit 1; }

# Forbidden stale claims (zero-match, negated); "fetched page bytes" subsumes the
# "exact fetched page bytes" variant at Step 4.7 item 1
if grep -n "fetched page bytes" "$F"; then echo "FAIL: stale singular-page byte claim remains"; exit 1; fi
if grep -n "the page's SHA-256" "$F"; then echo "FAIL: stale page-digest claim remains"; exit 1; fi
if grep -n -- "-page\.md" "$F"; then echo "FAIL: stale singular scratch filename remains"; exit 1; fi

echo "OK: digest-scope fixes verified"
```

### Task 1: Rewire the Step 5 mechanical gate to the full reviewed content

Files:
- `agents/skills/review-confluence-doc/SKILL.md`

- [ ] Replace the Step 5 item 4 opening with: `assemble ONE scratch file under {tmp_dir} holding the exact reviewed content this round: the parent page plus every fetched child page, concatenated in the order Step 2 fetched them`; change the example filename to `{tmp_dir}/confluence-review-<page-title-kebab>-reviewed.md`
- [ ] Update the Step 5 item 4 sidecar clause to say `source_digest` is computed over those exact concatenated reviewed-content bytes
- [ ] In the embedded bash block, rename `PAGE_BYTES_PATH` to `REVIEWED_CONTENT_PATH` pointing at `confluence-review-<page-title-kebab>-reviewed.md` (both the comment-bearing paragraph and the block stay consistent)
- [ ] Reword the guarantee sentence after the block to: `--source-doc recomputes the scratch file's SHA-256 (the digest of the full reviewed content, not a single page) and fails hard if it differs from the sidecar's source_digest ... (findings cannot be misattributed to content that was never reviewed)`
- [ ] In the Step 4.7 item 1 sidecar clause, change `source_digest computed over the exact fetched page bytes this round reviewed` to `source_digest computed over the exact concatenated reviewed-content bytes this round reviewed` (keep the never-copied/placeholder parenthetical)
- [ ] In the `review-staging` Integration-Points sentence, change `and the fetched page bytes via --source-doc` to `and the full reviewed-content scratch file via --source-doc`
- [ ] Run the Validation Commands block → expect all checks pass (`OK: digest-scope fixes verified`)
- [ ] Commit: `docs: scope confluence review digest to full reviewed content (F6)`

## Execution Handoff

Not part of this scheduled authoring run: do not invoke `execute-plan`. The plan is ready when the review gate reports `ready=yes`. When the plan completes, the backlog origin item moves to `{backlog_completed_dir}` with `Status: done` per the plans lifecycle (no separate backlog task).
