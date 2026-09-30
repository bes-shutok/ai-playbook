# Plan: Review posting landing receipt

Backlog origin: docs/history/backlog/2026-09-28-review-posting-completion-evidence.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-review-posting-landing-receipt-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A PR review's completion claim and its staging transition to `POSTED` become machine-gated on recorded landing evidence: every posted finding must carry a recorded receipt binding its identity (file, line, distinctive body fragment, live comment id) before the record may read `POSTED` and the session may report completion.

- The witnessed 2026-09-28 skip (a session reported four inline findings landed while the live PR showed only the approval) can no longer produce a `POSTED` record and a clean completion report, because the transition requires the receipt section and a focused checker pass.
- The intended-versus-landed sets are recorded in the staging document, so an incomplete posting carries its unlanded findings in the record, not only in chat.
- The existing individual-repost recovery and `INCOMPLETE` outcome are unchanged; the receipt records their results.

Gate delta: one new focused checker script plus a recording duty on the posting steps. This is a refusal-path addition on a fix-class origin whose body carries both pricings: the completed-integrity-failure witness (the consumer session that reported completion without landed comments while both the report and staging implied success) and an origin-prescribed sanctioned exit (the origin's Suggested fix names exactly this shape: the smallest machine-checkable receipt binding intended findings to post-submission comments, with `POSTED` allowed only when the set matches). The three class-default alternatives are addressed by the origin body: there is no false positive to remove (the existing prose requirement is correct but unenforced), removing the block would delete the existing live-verification requirement the origin says not to weaken, and no simpler exit exists because a prose restatement is precisely the enforcement shape that was skipped.

## Terms

- **Intended set**: one entry per posted finding with its `File`, `Line`, and a distinctive body fragment of its `#### Comment` text (built by posting step 4 today, never recorded before this plan).
- **Landing receipt**: the `## Landing receipt` section a posting writes into the staging document: one line per intended finding, `landing: file=<File> line=<Line> fragment="<distinctive substring>" comment=<live comment id or url> landed=yes|no`, plus an `intended=<n> landed=<m>` summary line.
- **Focused checker**: `scripts/check_review_landing_receipt.py`, an offline validator over a staging document; it enforces the receipt contract on records whose header value is exactly `POSTED` or starts with `INCOMPLETE (posting incomplete` and is a no-op on every other staging document (plan reviews, branch reviews, unposted records, and the suffixed `POSTED (...)` record families).
- **Landed evidence**: a receipt line with `landed=yes` whose file and line match the finding block's own `File`/`Line` bullets and whose fragment is a non-empty substring of that finding's `#### Comment` block text.

## Assumptions

- assume the checker is offline: it validates recorded receipts for presence, completeness, and identity match against the finding blocks, and never fetches the live PR; the post-submission fetch-and-compare stays procedural in step 4, and the receipt is the recorded output of that procedure. Basis: the origin's Expected bullet 4 asks for "a focused check or validator [that] rejects a completion receipt whose landed evidence is absent, incomplete, or mismatched by path, line, and distinctive body fragment" (all recorded-surface properties), and its Suggested fix binds "the intended finding identities to comments fetched from the PR after submission" (the receipt records what the fetch observed).
- assume the receipt lives in the staging document body as an additive section, not in the sidecar schema; basis: the origin's Exact location names the posting workflow and "the posting helper or review staging validator, if a machine-readable landing receipt can be added without duplicating the source of truth" - the staging doc is the source of record for posting state (the `POSTED` header lives there), so the receipt records beside it, and the load-bearing `validate_review_staging.py` plan-review gate is not extended.
- assume the checker keys on the exact posting header values, so plan-review records, branch-review records, suffixed `POSTED (...)` record families (the execute-plan Phase 3 code-review records carry `Status: POSTED (...)` with record-level "review record posted" semantics, verified by corpus sweep), and unposted records are unaffected no-op inputs; basis: the PR posting workflow writes the bare `POSTED` value and the pinned `INCOMPLETE (posting incomplete; unlanded findings remain pending)` form, and the checker classifies by those exact shapes (Task 2), keeping the witnessed PR-posting class enforced and every other record family a no-op.
- assume the origin item's declared `Class: correctness` agrees with a fix-class re-derivation (a witnessed enforcement gap closed by an enforcement artifact); basis: the body records the witnessed incident and prescribes the receipt-and-validator remedy.
- assume the repository's pytest-runner contract applies to the new tests (venv interpreter first, ambient fallback with a version guard); basis: plan `docs/history/plans/completed/2026-09-30-done-sweep-closeout-baseline-exemption.md` Task 3 (Validation).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the posting workflow records what the post-submission verification observed, and a focused checker refuses `POSTED` records whose receipts are absent, incomplete, or mismatched; the driving force is code-quality (a completion claim must carry its evidence in the record).

Before (today): a session posts four findings plus an approval in one submission. Step 4's fetch-and-compare is procedural prose; the session skips it, reports "all four findings posted", and the staging header moves to `POSTED`. Nothing in the record can contradict the claim; the user discovers the missing comments by looking at the PR. This is the witnessed 2026-09-28 consumer incident in the origin item.

After (this plan): step 4 ends by writing the observed result into the staging document as a `## Landing receipt` section (one line per intended finding with file, line, fragment, live comment id, landed yes/no, plus an `intended=<n> landed=<m>` summary). Step 5 flips the header to `POSTED` and immediately runs `python3 scripts/check_review_landing_receipt.py <staging-doc>`: exit 0 confirms the completion report (citing the checker pass), and exit 1 reverts the header to `INCOMPLETE (posting incomplete; unlanded findings remain pending)` naming the receipt defects, so a `POSTED` record can never stand without a complete receipt. A silently dropped finding leaves a `landed=no` line, which forces the `INCOMPLETE` header and the existing recovery path; after a successful repost the re-run receipt flips those lines to `landed=yes` with the new comment ids.

Receipt shape pinned by the checker:

    ## Landing receipt
    intended=4 landed=4
    landing: file=src/service.py line=42 fragment="retry once after a short pause" comment=2210456123 landed=yes
    landing: file=src/queue.py line=108 fragment="dead-letter after three failures" comment=2210456124 landed=yes

## Evaluation Criteria

**Quality dimensions:**
- correctness: a `POSTED` record without a receipt section, with a missing per-finding line, or with a file/line mismatch against the finding blocks exits 1 with named findings; a complete record exits 0; `STAGED`, plan-review, and branch-review records are no-ops.
- regression safety: the existing verification prose, recovery path, and `INCOMPLETE` outcome are amended only additively (recording the receipt, running the checker); no requirement is weakened.
- maintainability: the receipt contract is pinned by the checker's own test file naming all four origin fixture classes.

**Done when:**
- `scripts/check_review_landing_receipt.py` exists and `scripts/test_review_landing_receipt.py` passes (successful batch, dropped finding, mismatched comment, recovery shapes, and the no-op negative controls).
- `agents/skills/doing-code-review/SKILL.md` posting steps and Direct Mode carry the receipt-recording duty, the checker gate on the `POSTED` transition, and the completion-report citation.
- All Validation Commands exit 0 from the worktree root.

**Ship when:**
- Consumer runtimes pick the skill and script up through their normal vendored-asset sync; the checker is repo-local tooling with no deployment twin beyond the vendored copy.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_review_landing_receipt.py` *(new)*
- `agents/skills/doing-code-review/SKILL.md`

**Tests:**
- `scripts/test_review_landing_receipt.py` *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py` and the review-staging sidecar schema; reason: the load-bearing plan-review gate is deliberately not extended (see Assumptions); the receipt is a body-level additive section.
- The live-PR fetch primitives in `github-pr-workflow`; reason: runtime-specific fetch mechanics are unchanged; the receipt records their observed output.

## Validation Commands

```bash
# Runner contract: venv pytest interpreter first, ambient fallback with a loud guard.
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest --version || { echo "no pytest-capable interpreter" >&2; exit 1; }

# 1. The checker's test file passes.
"$TEST_PY" -m pytest scripts/test_review_landing_receipt.py -q || { echo "FAIL: receipt checker tests" >&2; exit 1; }

# 2. Skill pins: the receipt duty, the checker gate, and the direct-mode duty are wired (dedicated pins).
grep -qF 'write the `## Landing receipt` section into the staging document' agents/skills/doing-code-review/SKILL.md || { echo "FAIL: receipt-recording duty missing" >&2; exit 1; }
grep -qF 'python3 scripts/check_review_landing_receipt.py' agents/skills/doing-code-review/SKILL.md || { echo "FAIL: checker invocation missing" >&2; exit 1; }
grep -qF 'only after the checker exits 0' agents/skills/doing-code-review/SKILL.md || { echo "FAIL: POSTED gate wording missing" >&2; exit 1; }
grep -qF 'the same landing receipt duty' agents/skills/doing-code-review/SKILL.md || { echo "FAIL: direct-mode duty missing" >&2; exit 1; }

# 3. Em-dash gate over the branch's added lines.
bash scripts/check-no-em-dash.sh added-lines --base main || { echo "FAIL: em-dash gate" >&2; exit 1; }
```

Authoring-time gate record (rule 29/19/22): the pre-round structural gate, the em-dash `touched` scan, and the public-hygiene scan ran over these plan bytes before round 1. RED-today evidence, rule 19: Validation Command 1 cannot pass (neither script exists yet), and Command 2's four skill pins were executed against the unamended SKILL.md with all four spans verified absent. Rule 22 mechanical audit: each Validation Command pin occurs exactly once in its owning Task's prescribed snippet beside its Command occurrence (plan-wide mentions in Terms and Gist are not pin sites), and `bash -n` over this block passed.

### Task 1: Pin the receipt contract (RED)

Files:
- `scripts/test_review_landing_receipt.py` *(new)*

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_review_landing_receipt.py -q`; covers: the checker's contract fixtures exist and fail while the checker is absent.

- [ ] Create `scripts/test_review_landing_receipt.py` (pytest style, `subprocess` invocation of the checker script path resolved relative to the repo root, tmp_path fixture docs built as minimal staging documents with a `## Landing receipt` header candidate, finding blocks carrying `- **File**:`/`- **Line**:` bullets, and the pinned receipt line shape) covering the origin's four classes: `test_posted_record_with_complete_receipt_passes` (successful batch), `test_posted_record_missing_receipt_section_fails` and `test_posted_record_missing_one_finding_line_fails` (silently dropped finding, both), `test_receipt_identity_mismatch_fails` (receipt file or line differing from the finding block), `test_receipt_fragment_not_in_comment_fails` (a fragment string absent from the finding's Comment block), `test_receipt_census_mismatch_fails` (summary counts disagreeing with the posted-finding census), `test_incomplete_record_with_unlanded_lines_passes` and `test_incomplete_record_missing_unlanded_lines_fails` (recovery outcome shapes), `test_unposted_and_plan_records_are_noops` (STAGED header and a plan-review-style record both exit 0 with no receipt section), `test_phase3_style_suffixed_posted_record_is_noop` (a `Status: POSTED (review record posted)` value exits 0 with no receipt section). [class: REPOSITORY_TEST]
- [ ] Run → expect RED: `"$TEST_PY" -m pytest scripts/test_review_landing_receipt.py -q` exits non-zero (the checker script does not exist; every subprocess invocation fails). [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin review posting landing receipt contract (RED)` [class: REPOSITORY_TEST]

### Task 2: Implement the focused checker (GREEN)

Files:
- `scripts/check_review_landing_receipt.py` *(new)*

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_review_landing_receipt.py -q`; covers: every contract class passes.

- [ ] Implement `scripts/check_review_landing_receipt.py` (stdlib only, argparse single positional staging-doc path, exit 0 clean / exit 1 with one named error per finding): parse the header `Status:` region of the staging document; classify the record by exact value `POSTED` (the bare posting value; a suffixed value like `POSTED (review record posted)` is a different record family and reads as a no-op) and by the value starting with `INCOMPLETE (posting incomplete` (the posting workflow's own pinned full form); on a `POSTED` record require the `## Landing receipt` section, an `intended=<n> landed=<m>` summary line whose `<n>` equals the count of finding blocks whose per-finding Status is `posted` and whose `<m>` equals the count of `landed=yes` lines (both also equal to each other on a POSTED record), exactly one `landed=yes` line per posted finding block, each line's `file=`/`line=` matching that finding block's `File`/`Line` bullets, each line's `fragment=` being a non-empty substring of that finding block's `#### Comment` block text (the fragment is recorded from the live comment, which was posted verbatim from that block), and a non-empty `comment=`; on an `INCOMPLETE` record require the section with at least one `landed=no` line; on any other header value (including absent, `STAGED`, and suffixed `POSTED (...)` families) exit 0 without further checks. Report each violation as `<error class>: <finding or line>` on stderr. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `"$TEST_PY" -m pytest scripts/test_review_landing_receipt.py -q` exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `feat: focused landing receipt checker for PR review posting records` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Wire the receipt into the posting workflow (GREEN)

Files:
- `agents/skills/doing-code-review/SKILL.md`

Evidence:
- Validation Command 2's four pins pass against the amended SKILL.md.

- [ ] Amend posting step 4 to end with the recording duty: after the live fetch-and-compare, write the `## Landing receipt` section into the staging document (one `landing:` line per intended finding with `file=`, `line=`, `fragment=`, `comment=`, `landed=yes|no`, plus the `intended=<n> landed=<m>` summary line); the receipt is the recorded output of this verification, never a substitute for it. [class: IMPLEMENTATION_REQUIRED]
- [ ] Amend posting step 5 to the flip-then-check gate: move the header to `POSTED` first, then run `python3 scripts/check_review_landing_receipt.py <staging-doc>`; on exit 1 revert the header to `INCOMPLETE (posting incomplete; unlanded findings remain pending)`, leave the affected findings' Status unflipped, and name the receipt defects instead of reporting completion (the checker is a no-op on any non-`POSTED` value, so the check only gates after the flip); proceed only after the checker exits 0, then cite the checker pass in the completion report alongside the posted/dropped findings. [class: IMPLEMENTATION_REQUIRED]
- [ ] Amend posting step 6's recovery outcome so the receipt stays truthful with a single author: the recovery pass does not hand-edit the receipt; the step 4 re-run over the full intended set rewrites the `## Landing receipt` section in place (its write is the only author), so the reposted findings' lines carry `landed=yes` with the new comment ids before step 5 re-runs, and an `INCOMPLETE` record keeps its `landed=no` lines (the record of the unlanded set). [class: IMPLEMENTATION_REQUIRED]
- [ ] Amend Direct Mode so PR postings carry the same landing receipt duty (record the receipt during the same post-submission verification; run the checker before marking findings `posted`), while branch reviews keep their current no-remote behavior. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: Validation Command 2's four pins pass; `bash scripts/check-no-em-dash.sh added-lines --base main` exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: gate review posting completion on recorded landing receipts` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Whole-plan validation gate

Files:
- `agents/skills/doing-code-review/SKILL.md`

Evidence:
- The full `## Validation Commands` block run from the worktree root; covers: every criterion in Done when (the two new scripts are creation-owned by Tasks 1 and 2 and validated here by execution).

- [ ] Run the complete `## Validation Commands` block from the worktree root; every command exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `test: whole-plan validation for review posting landing receipt` [class: REPOSITORY_TEST]
