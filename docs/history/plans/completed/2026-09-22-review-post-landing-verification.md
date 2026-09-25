# Plan: review-post landing verification

Origin: `docs/history/backlog/2026-09-22-active-review-post-verification.md` (P46, high): a GitHub batch review submission returned an approved review while silently dropping every inline finding; the workflow marked the review complete from the submission response alone. (The origin file sits on the origin-capture branch at authoring time, not yet on the base branch; the observed behavior here is quoted from it.)

## Terms

- **Staging record**: the review deliverable under `docs/reviews/` (Markdown plus `.stats.json` sidecar); its Metadata carries a `- Status:` header.
- **STAGED / POSTED / INCOMPLETE**: values of the staging record's `- Status:` header. `STAGED (not yet posted)`: findings written, nothing posted. `POSTED`: every intended finding is verified live on the pull request. `INCOMPLETE`: posting was attempted and findings remain unlanded after the recovery pass.
- **Inline comment**: a GitHub pull-request review comment anchored to a file path and line (REST collection `repos/{owner}/{repo}/pulls/{pr}/comments`).
- **Batch review submission**: one `POST repos/{owner}/{repo}/pulls/{pr}/reviews` call carrying a top-level body plus a `comments` array; the `github-pr-workflow` "Post active review comments" primitive.
- **Landing verification**: the post-submission check that matches every intended finding against the live pull-request comment collection.
- **Distinctive body fragment**: a short span unique to one finding's `#### Comment` text (for example its first sentence), used as the body match key.

## Assumptions

- assume single-file scope: only `agents/skills/doing-code-review/SKILL.md` changes; basis: the origin item names that surface (posting step + staging record contract), confirmed by standing pre-authorization.
- assume the individual re-post call is documented inline in the posting step and `agents/skills/github-pr-workflow/SKILL.md` is not edited; basis: origin surface line, plus the existing precedent of `doing-code-review` embedding concrete `gh` payload shapes in its Direct Mode section.
- assume prose-only change (no runtime scripts); validation is grep plus hygiene scans; basis: docs-plan origin and the repo's docs-plan claim boundary.
- assume the document template line `- Status: STAGED (not yet posted)` stays byte-identical; basis: `scripts/validate_review_staging.py` template literals anchor on its `- Status: STAGED` prefix (validator lines 5098 and 12256; Worker-status label collision note near line 176), so the prefix and therefore the full line must not change.

Decision points requiring a grill: INCOMPLETE header value for partially-failed posting rather than overloading STAGED: accepted via standing pre-authorization (authoring dispatch, 2026-09-22), Terms and Task 2; single individual re-post pass then report incomplete, no retry loops: accepted via standing pre-authorization (authoring dispatch, 2026-09-22), Task 1; landing verification scoped to GitHub PR postings, branch reviews exempt: accepted via standing pre-authorization (authoring dispatch, 2026-09-22), Task 1 and Task 3.

## Gist & Examples

`doing-code-review` treats a successful review-submission response as proof that inline comments were attached. The batch submission endpoint can accept the review and still drop the `comments` array (observed: `APPROVED` review, zero comments under the returned review id, findings visible only after individual posting). The posting step then marks the staging record `POSTED` and reports completion, so a silently emptied review reads as delivered.

This plan inserts a mandatory post-submission landing verification between posting and the `POSTED` transition, and defines recovery plus an honest incomplete outcome:

- After posting, the workflow builds the intended set (one entry per posted finding: file, line, distinctive body fragment) and fetches the live pull-request review comments with the existing `github-pr-workflow` "Fetch existing review comments before active review" primitive. When the submission returned a review id, comments are first narrowed to `pull_request_review_id` matches; otherwise all review comments are searched.
- A finding has landed only when a live comment carries the same path, the same line, and the distinctive body fragment; the intended-vs-landed count must match.
- Only then does the staging record header move to `POSTED`.
- On a silent batch drop, each missing finding is re-posted individually through the pull-request review-comments endpoint (one call per finding), then the full verification runs again. If findings are still missing after that single recovery pass, the header moves to `INCOMPLETE`, unlanded findings stay `pending`, and the review is reported as incomplete with the unlanded findings named. The submission response alone is never completion evidence.
- Direct Mode PR postings get the same gate: findings are marked `posted` only after the same verification.
- Branch reviews are unchanged: they have no remote landing to verify.

No README, document-registry, or metrics changes: the skill is catalog-listed by name only and its name, path, and invocation are unchanged. No new staging sidecar fields: verification evidence is reported in the posting step's output, keeping `scripts/validate_review_staging.py` out of scope.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every Validation Command obligation fails when its amended text is stripped from the skill file (each pin is a dedicated, count-exact grep; the forbidden sweep of the old unconditional step flips exactly when Task 1 lands)
- completeness: all three contract surfaces amended (posting step, staging record Status contract, Direct Mode); no stale unconditional `POSTED` transition remains
- maintainability: amendments reuse the existing `github-pr-workflow` primitive name and the existing staging Status vocabulary; no new tool-specific APIs and no new sidecar fields

**Done when:**
- the `## Validation Commands` block exits 0 against the amended `agents/skills/doing-code-review/SKILL.md`
- `bash scripts/check-no-em-dash.sh file agents/skills/doing-code-review/SKILL.md` exits 0
- the public hygiene scan exits 0 from the repository root

**Ship when:**
- the next real PR review that posts staged findings executes the verification step and records a `POSTED` or `INCOMPLETE` outcome (human-run reviews; observed behavior, prose only)

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/doing-code-review/SKILL.md` (partially in scope: the `### Posting Staged Findings` subsection, the `**Status values**` list area that Task 2 extends, and the `### Direct Mode (skip staging)` PR-review bullet that Task 3 amends. All other sections in this file are frozen; reject any review finding that touches them.)

**Tests:**
- none (docs plan; verification is the `## Validation Commands` block)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/github-pr-workflow/SKILL.md`; reason: its primitives are consumed as-is; the origin scopes the change to `doing-code-review`
- `scripts/validate_review_staging.py`; reason: validator behavior unchanged; the template anchor line stays byte-identical

## Validation Commands

```bash
set -u
REPO="$(git rev-parse --show-toplevel)" || exit 1
SKILL="$REPO/agents/skills/doing-code-review/SKILL.md"
test -f "$SKILL" || { echo "missing $SKILL"; exit 1; }

# Dedicated grep per structural obligation; exactly-once criteria use count gates.
# grep -c exit status: 0 = count>0, 1 = count 0 (normal), >=2 = tool error.
expect_once() {
  n="$(grep -cF -- "$1" "$SKILL")"; rc=$?
  if [ "$rc" -gt 1 ]; then echo "GREP ERROR rc=$rc: $1"; exit 1; fi
  [ "$n" -eq 1 ] || { echo "EXPECT-ONCE(got $n) FAIL: $1"; exit 1; }
}
# Forbidden sweeps: rc 0 = match = fail, rc 1 = clean pass, rc >= 2 = tool error = fail.
forbid() {
  rc=0; grep -qF -- "$1" "$SKILL" || rc=$?
  if [ "$rc" -eq 0 ]; then echo "FORBIDDEN MATCH: $1"; exit 1
  elif [ "$rc" -gt 1 ]; then echo "GREP ERROR rc=$rc: $1"; exit 1; fi
}

# G1 mandatory verification step present, exactly once
expect_once '**Post-submission landing verification (mandatory; never skipped'
# G2 POSTED is verification-gated
expect_once 'When every intended finding has landed, update the staging doc: change the Status header to'
# G3 absolute prohibition survives
expect_once 'Never mark the staging record `POSTED` while any intended finding is missing'
# G4 individual re-post recovery path
expect_once 're-post each missing finding individually through the pull-request review-comments endpoint'
# G5 individual post endpoint shape
expect_once 'POST repos/{owner}/{repo}/pulls/{pull_number}/comments'
# G6 review-id narrowing for batch submissions
expect_once 'whose `pull_request_review_id` matches that id'
# G6b post-recovery verification widening (r1 F1 fold)
expect_once 'later verification run after individual re-posts, match against all review comments'
# G7 verification consumes the live comment collection via the shared primitive
expect_once 'Fetch existing review comments before active review'
# G8 PR-only scope stated
expect_once 'branch reviews have no remote landing to verify'
# G9 incomplete report obligation
expect_once 'report the review as incomplete'
# G10 Direct Mode PR posting gated on the same verification
expect_once 'only after the same post-submission landing verification passes'
# G11 header transitions contract recorded
expect_once 'Staging record header Status transitions (posting)'
# G12 submission success is not completion evidence
expect_once 'own success response is never evidence of'
# G13 unlanded findings keep pending
expect_once 'unlanded findings keep Status'
# G14 unconditional old step removed (RED today; GREEN exactly when Task 1 lands)
forbid '4. Update the staging doc: change Status header to `POSTED`, mark posted findings as `posted`, keep dropped findings as `drop`'
# G15 validator anchor line untouched
expect_once '- Status: STAGED (not yet posted)'
# G16 no em dash in the amended file (octal so this plan never embeds the character)
forbid "$(printf '\342\200\224')"
# G17 public hygiene scan, anchored to the repo root
( cd "$REPO" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" ) || { echo "HYGIENE FAIL"; exit 1; }

echo "ALL VALIDATION GATES GREEN"
```

Authoring-time record (2026-09-22, current tree): the block executes RED today at G1 (`EXPECT-ONCE(got 0)`) and every presence gate G1-G13 and G6b fails, G14's forbidden sweep fires on the present old step-4 line, and G15-G17 pass today; see `docs/tmp/plan-requirements-review-post-landing-verification.md` for the recorded run. (r1 fold: G6b added with the recovery-widening pin; audited absent today and exactly-once in the Task 1 artifact.) (r2 fold: the Task 1 block's recovery payload gains the GitHub-required `commit_id` field, matching the executed skill text after review r1 F1; gates unchanged, G5 pins only the endpoint string.)

### Task 1: verification-gated posting step

Files:
- `agents/skills/doing-code-review/SKILL.md`

- [x] Replace the body of the `### Posting Staged Findings` subsection (the intro line through old step 5, heading itself unchanged) with the block below, verbatim [class: IMPLEMENTATION_REQUIRED]

```markdown
When the user says "post comments", "post the review", or "post approved":
1. Read the staging doc from the review session path, or resolve exactly one `{reviews_dir}/*-PR-<number>-*.md`
2. Collect all findings with `status: post` or `status: edit` (or `pending` when the user explicitly approves posting all pending)
3. For each finding, read the `#### Comment` block verbatim; verify `File`/`Line` are in diff hunks (§4.9); post via `github-pr-workflow` as inline comments
4. **Post-submission landing verification (mandatory; never skipped, even when the submission call reports success):** build the intended set: one entry per posted finding with its `File`, `Line`, and a distinctive body fragment of its `#### Comment` text (for example the first sentence). Fetch the live pull-request review comments with the `github-pr-workflow` "Fetch existing review comments before active review" primitive. When the posting used one review submission that returned a review id and this is the first verification run, first narrow to the comments whose `pull_request_review_id` matches that id; in any later verification run after individual re-posts, match against all review comments, because individually posted comments do not carry the batch submission's review id; when the posting returned no review id, match against all review comments. The same all-comments match applies when findings were posted across multiple review submissions. A finding has landed only when the live collection contains a comment with the same path, the same line, and the distinctive body fragment (treat the comment's recorded commit as informational; head may have moved). Every intended finding must land; an intended-vs-landed count comparison is the minimum evidence. This verification applies to GitHub PR postings only; branch reviews have no remote landing to verify.
5. When every intended finding has landed, update the staging doc: change the Status header to `POSTED`, mark posted findings as `posted`, keep dropped findings as `drop`, then report which findings were posted and which were dropped.
6. When any finding did not land (silent batch drop), recover: re-post each missing finding individually through the pull-request review-comments endpoint (`POST repos/{owner}/{repo}/pulls/{pull_number}/comments` with `commit_id` (the head commit sha the PR is pinned to), `path`, `line`, `side: "RIGHT"`, `body`; one call per finding), then re-run step 4 over the full intended set. When the re-run verifies every finding, continue with step 5. When findings are still missing after this one recovery pass, set the staging doc's Status header to `INCOMPLETE`, leave the unlanded findings' Status as `pending`, and report the review as incomplete: name each finding that did not land. Never mark the staging record `POSTED` while any intended finding is missing, and never treat the submission response alone as completion.
```

- [x] Run gates G1 through G6b and G7-G9, G14, G15 of `## Validation Commands`; expect G14's forbidden sweep GREEN (old unconditional step replaced) and gates G1-G6b, G7-G9 GREEN; G10-G13 still fail until Tasks 2-3 land [class: REPOSITORY_TEST]
- [x] Commit: `docs: add post-submission landing verification to review posting` [class: IMPLEMENTATION_REQUIRED]

### Task 2: staging record Status contract

Files:
- `agents/skills/doing-code-review/SKILL.md`

- [x] Insert the paragraph below between the `**Status values**` list and the `After triage` paragraph, verbatim [class: IMPLEMENTATION_REQUIRED]

```markdown
**Staging record header Status transitions (posting):** the header value `STAGED (not yet posted)` moves to `POSTED` only through the posting step's landing verification, when every intended finding is live on the pull request. When findings remain unlanded after the recovery pass, the header moves to `INCOMPLETE (posting incomplete; unlanded findings remain pending)` and the unlanded findings keep Status `pending`; a later posting pass re-runs the verification and may move `INCOMPLETE` to `POSTED`. The submission call's own success response is never evidence of `POSTED`. After posting, landed findings carry the per-finding Status `posted`; the list's `post` value records pre-posting approval.
```

- [x] Run gates G11-G13 and G15 of `## Validation Commands`; expect GREEN; G10 still fails until Task 3 lands [class: REPOSITORY_TEST]
- [x] Commit: `docs: document INCOMPLETE staging record transition` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Direct Mode gating

Files:
- `agents/skills/doing-code-review/SKILL.md`

- [x] In `### Direct Mode (skip staging)`, replace the bullet `Still write the staging doc as a record with all findings marked as \`posted\`` with the bullet below, verbatim [class: IMPLEMENTATION_REQUIRED]

```markdown
- Still write the staging doc as a record; for PR postings, mark findings as `posted` only after the same post-submission landing verification passes, and record an unlanded finding per the posting step's incomplete outcome (header `INCOMPLETE`, finding left `pending`)
```

- [x] Run gate G10 of `## Validation Commands`; expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `docs: gate direct-mode posting on landing verification` [class: IMPLEMENTATION_REQUIRED]

### Task 4: full validation sweep

Files:
- `agents/skills/doing-code-review/SKILL.md`

- [x] Run the complete `## Validation Commands` block; expect exit 0 with `ALL VALIDATION GATES GREEN` [class: REPOSITORY_TEST]
- [x] Run `git status --porcelain` from the repository root; expect empty (all tasks committed) [class: REPOSITORY_TEST]
