# Plan: code-family certification digest scope and tip moves

Authoring claim: docs/tmp/authoring-claims/2026-10-21-code-family-certification-stale-after-tip-moves.md (session sess-automation-bc3ff071-0200)
Plan review record: the staging series {reviews_dir}/2026-10-24-plan-review-code-family-cert-digest-scope-pf748a935-r*.md (the highest rN for this source-plan path is authoritative)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-21-code-family-certification-stale-after-tip-moves.md

Driving force: efficiency
Execution budget: 3.0h total, largest task 1.5h

## Terms

- code-family certification: the graded binding for a reviewed code range, anchored by a seal entry whose `reviewed_base`/`reviewed_head` name the certified range and whose digests are pinned in the seal block, the review sidecar `source_digest`, the record's Round/Source-digest lines, and the plans-egress backfill record.
- reviewed-scope byte function: the single function computing the bytes a code-family digest hashes: the branch delta computed at the git layer with pathspec exclusion (`git diff base...head -- . ':(exclude)<bookkeeping prefixes>'`), never by parsing diff text.
- bookkeeping prefixes: the exact exclusion set, pinned in this plan as `docs/history/backlog/` only, component-wise matched with trailing slash; manifest updates are excluded from the set (the session manifest is gitignored and never enters a diff) and disposition notes have no canonical path outside the backlog rows.
- bookkeeping append: a tracked write under the bookkeeping prefixes made after certification; a non-mutation of the reviewed digest by construction.
- re-pin: rewriting the four pinned identities (seal block, sidecar, record lines, backfill record) after a tip move, re-validated through `validate_review_staging.py --hard --source-code-repo <repo-root> --source-code-plan <stats-sidecar>`.
- verify-digest duty: the Phase 3 freshness check in `scripts/review_record_selection.py` (`verify_digest`) that refuses on any HEAD move past the recorded verified head.
- migration set: the ~10 live code-family certifications, by role: their seal files under `.ai-playbook/review-certs/`, their paired review records and `.stats.json` sidecars under the resolved reviews home, and their plans-egress backfill completion records (the fourth pinned identity), whose pinned digests were minted whole-diff.

## Why

A clean code-family round certifies a range digest, then its own lifecycle moves the tip twice (the round-close residual append and the pre-landing rebase), plus the Phase 4 archive move, a standing in-scope tracked write whose staleness was absorbed into the same re-pins: the anchor leg refuses a non-ancestor seal commit, the whole-diff hash changes, and the session re-pins four identities by hand three times. The execute-plan Step 3.4 sentence already declares bookkeeping a non-mutation, but every digest site on the path hashes the whole diff, so the declaration is not true by construction. One git-layer byte function consumed by every site, one verify-digest amendment, one migration pass over the live seals, and one named re-pin step make a clean round's certification survive its own lifecycle.

## Gist & Examples

TLDR: scope the code-family certification digest to reviewed source paths everywhere it is computed and name the post-rebase re-pin, for efficiency: one certification per clean round, not three hand re-pins.

Before: r2 certifies at fa3591d3b; the residual row append moves the tip (re-pin 1); the pre-landing rebase moves every OID (re-pin 2); the base pin moves to the new merge-base (re-pin 3).

After: the residual append and the verify-digest duty both accept it (its bytes are outside the reviewed scope), and the Phase 4 text names one re-pin step after the archive commit (the last in-scope tracked write before landing), covering both the archive move and the pre-landing rebase.

## Outcome

A clean code-family round's certification survives the residual append by construction (anchor leg, staging validator, corrections chains, row minting, and the verify-digest duty all read the same reviewed-scope bytes); the remaining in-scope lifecycle writes (the Phase 4 archive move and the pre-landing rebase) cost one named re-pin step.

- Every digest site on the code-family path consumes the one byte function; no site parses diff text.
- The live seals and sidecars are re-pinned through the new function in the same change, so no pre-change certification silently refuses.
- The execute-plan Phase 4 text names the post-archive-and-rebase re-pin and its re-validation command.

Gate delta: checked-set narrowing, declared in two components. First, the digest's checked set shrinks by the bookkeeping prefixes; second, the validated-OID threading stops the unreviewed post-validation tail from binding silently (a soundness fix: those bytes move from silently certified to downstream verify-digest refusals). Component one means bookkeeping bytes that previously staled a certification pass without re-validation; component two means post-validation tail bytes stop passing silently. Priced by the origin row's witnessed friction (three re-pins per run, two runs) and the Step 3.4 sentence's standing classification; the fixtures pin the new boundary, and the migration task keeps every existing certification verifiable across the change.

## Assumptions

- assume the byte function's home is the module that already owns the diff computation (`scripts/corrections_record.py`, whose `diff_bytes` the consumers import); basis: the import graph verified at review.
- assume the landing helper computes no range digest (verified 2026-10-24: `scripts/land_squash.sh` and `reconcile_post_landing.py` compare path sets and trees, never hashes), so no threading is needed there.
- assume the verification-head gap at the staging validator's current-diff call (the literal "HEAD" the origin row's Source bullet names) is fixed in the same change: the byte function's call sites thread the validated OID where one exists.
- assume the bookkeeping prefixes encode this repository's bookkeeping layout convention and apply to every `--source-code-repo` target; the machinery is this repo's own review stack and its certified repos share the layout; basis: the cross-repo reach of `--source-code-repo` verified at review, accepted as a documented convention limit.
- assume deployed runtime copies of the two files pair via the sibling import and must land together; basis: `projects/.ai-playbook/agent-runtime-layout.md` and the `_sibling_module` import.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a residual-row append after certification re-validates green with no re-pin on every instrument (staging validator, corrections chains, verify-digest duty); a reviewed-source edit still fails validation on every instrument; a diff-spoof attempt does not escape the digest.
- maintainability: the byte function is defined once; no consumer copies the exclusion list or parses diff text.

**Done when:**
- A grep over the code-family digest path (`corrections_record.py`, `code_delta_classifier.py`, `validate_review_staging.py`, `review_record_selection.py`) finds no whole-diff `diff_bytes` hash over a certified range outside the byte function.
- The corrections-record suite passes with the bookkeeping-append, source-edit, diff-spoof, empty-filter, plumbing, and rebased-tip fixtures; the staging `--selftest` passes with the bookkeeping-append and source-edit arms over `--source-code-repo`.
- The migration-set certifications re-validate green through the new function across their four pinned identities (a refusing member parks with its named reason).
- The execute-plan Phase 4 preamble sentence and the review-plan seal-paragraph pointer exist.

**Ship when:** none; local repository work only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/corrections_record.py` (the byte function; the anchor leg; the per-hop re-derivation)
- `scripts/validate_review_staging.py` (the current-diff call site; selftest fixtures)
- `scripts/code_delta_classifier.py` (row minting digests; the build-time check)
- `scripts/review_record_selection.py` (verify-digest duty)

**Tests:**
- `scripts/test_corrections_record.py` *(fixtures extended)*
- `scripts/test_review_record_selection.py` *(verify-digest fixtures)*
- `scripts/test_code_delta_classifier.py` *(minted-digest fixtures)*
- the migration set: `.ai-playbook/review-certs/` seals, their `.ai-playbook/reviews/` record/sidecar pairs, and their plans-egress backfill records *(re-pins only)*

**Plan-related extension:** the seal-paragraph sentences in `agents/skills/execute-plan/SKILL.md` and `agents/skills/review-plan/SKILL.md`, and the migration set as defined in Terms (re-pins only), are in scope when causally tied to the byte function threading.

**Out of scope; reject unless plan-related:**
- the plan-family anchor path (`resolve_landed_anchor`, FAMILY_PLAN legs); reason: frozen per the origin row.
- any new gate, exit code, or validator surface; reason: the origin row prices this as an existing-surface narrowing.
- edits to sealed plan-family records; reason: their digests are plan-family and unaffected.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_corrections_record.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_review_record_selection.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_code_delta_classifier.py -q
python3 scripts/validate_review_staging.py --selftest
bash scripts/check-no-em-dash.sh touched
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/check_review_agent_portability.py
grep -n "diff_bytes" scripts/corrections_record.py scripts/code_delta_classifier.py scripts/validate_review_staging.py scripts/review_record_selection.py
```

### Task 1: Define the byte function and thread every digest site

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/corrections_record.py`
- `scripts/validate_review_staging.py`
- `scripts/code_delta_classifier.py`
- `scripts/review_record_selection.py`
- `scripts/test_corrections_record.py`
- `scripts/test_review_record_selection.py`
- `scripts/test_code_delta_classifier.py`
- the migration set: `.ai-playbook/review-certs/` seals, their `.ai-playbook/reviews/` record/sidecar pairs, and their plans-egress backfill records *(re-pins only)*

- [ ] Add one reviewed-scope byte function next to `diff_bytes` in `scripts/corrections_record.py`: compute the delta at the git layer with pathspec exclusion (`git diff base...head -- . ':(exclude)docs/history/backlog/'`), never by parsing diff text. [class: IMPLEMENTATION_REQUIRED]
- [ ] Pin the byte function's outcome routing table: bytes (reviewed content present, including a raw-empty delta hashed over empty bytes, preserving today's empty-range behavior), a distinct named BOOKKEEPING-ONLY outcome (raw diff non-empty, filtered bytes empty), and the existing indeterminate/refusal shape (plumbing failure); the last two are never conflated. [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-derive from disk the full digest-site list before editing (anchor leg, per-hop re-derivation, current-diff, minting, build-time check, verify-digest); record it in the task log. [class: IMPLEMENTATION_REQUIRED]
- [ ] Switch every site in that re-derived list to the byte function; where a caller passes a verified OID, thread it through (the origin row's Source bullet names the literal-HEAD gap at the current-diff call site); no consumer copies the exclusion list. [class: IMPLEMENTATION_REQUIRED]
- [ ] Behavior witness: given a post-certification commit touching only `docs/history/backlog/`, expects every instrument's digest unchanged; given a reviewed source path commit, expects each digest to change. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness (spoof): given a bookkeeping-path commit embedding crafted `diff --git` header lines, expects the digest to still bind the source hunks; fixture it. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness (empty filter): a non-empty raw diff filtering to zero bytes yields the distinct BOOKKEEPING-ONLY outcome, never a digest over empty bytes; fixture the all-bookkeeping range. [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness (plumbing): a plumbing failure over the range base propagates the existing indeterminate/refusal shape. [class: IMPLEMENTATION_REQUIRED]
- [ ] Amend the verify-digest duty (`review_record_selection.py verify_digest`): a HEAD advance whose delta the byte function classifies BOOKKEEPING-ONLY (positive evidence: raw diff non-empty and filtered bytes empty as the distinct outcome, never inferred from a plumbing refusal) is accepted with the verified head advanced. [class: IMPLEMENTATION_REQUIRED]
- [ ] The same amendment keeps refusing a reviewed-path delta and a plumbing failure; fixture the raw-empty advance, bookkeeping-advance accept, reviewed-delta refuse, and plumbing-refuse routings in `scripts/test_review_record_selection.py`. [class: REPOSITORY_TEST]
- [ ] Migration: re-pin every member of the migration set through the new function (recompute each pinned digest across the four identities), re-validating each landed range with `validate_review_staging.py --hard --source-code-repo <repo-root> --source-code-plan <stats-sidecar>` plus `--verification-head <landing OID>` (the origin row's detached-checkout trap), recording the re-pin list in the task log; a refusing member parks with the named reason. [class: IMPLEMENTATION_REQUIRED]
- [ ] Rollout guard: feature-detect the byte function at every consumer entry point (the staging validator, the classifier, the record selector) and degrade to the named-gap tool-error shape, never a crash, on a mixed-vintage pair; fixture it. [class: IMPLEMENTATION_REQUIRED]
- [ ] Fixtures: corrections-record suite gains the bookkeeping-append, source-edit, spoof, empty-filter, and plumbing cases; the staging `--selftest` gains the bookkeeping-append and source-edit arms over `--source-code-repo` with a minted hop chain ending at the append commit. [class: REPOSITORY_TEST]
- [ ] Run: RED for the bookkeeping-append, spoof, and empty-filter fixtures; first-run GREEN for the source-edit fixtures (regression guards, recorded as expected); implement; all GREEN. [class: REPOSITORY_TEST]
- [ ] Run the Validation Commands; expect all suites green and the grep showing no whole-diff hash outside the byte function. [class: REPOSITORY_TEST]
- [ ] Commit: `feat: scope the code-family certification digest to reviewed source paths` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Name the post-rebase re-pin in the skill texts

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [ ] Add one sentence to the execute-plan Phase 4 text keyed after the archive commit step: after the archive move or a pre-landing rebase (whichever moved the tip last), re-pin the four identities and re-validate through `validate_review_staging.py --hard --source-code-repo <repo-root> --source-code-plan <stats-sidecar>` with `--verification-head <landing OID>` before the landing critical section. [class: IMPLEMENTATION_REQUIRED]
- [ ] The re-pinned four identities are named in that sentence: seal block anchors and reviewed range, sidecar source_digest and certified_range, the record's Round and Source digest lines, the plans-egress backfill record; pay the text growth with a deletion in the same paragraph. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add one sentence to review-plan's plan-family round-close seal paragraph referencing that Phase 4 re-pin step for code-family certifications, by reference, no restatement; pay the growth with a deletion in the same paragraph. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the Validation Commands; expect hygiene and portability checks passing. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: name the post-rebase certification re-pin in the Phase 4 preamble` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Rebased-tip re-pin fixture

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/test_corrections_record.py`

- [ ] Fixture: a range rebased onto a new merge-base whose reviewed-scope delta bytes are unchanged re-pins green through the byte function; the rebased commits carry committer dates pinned at or before the re-pinned round-close commit (through the fixture repo's date mechanism or `--committer-date-is-author-date`), so the dating leg never masquerades as a digest refusal. [class: REPOSITORY_TEST]
- [ ] Fixture negative arm: a rebase whose new merge-base touched a reviewed source path still refuses, and the fixture asserts the refusal reason is the digest re-hash, not a dating message. [class: REPOSITORY_TEST]
- [ ] Run: expect first-run GREEN on both arms (regression guards; the three-manual-re-pins friction they retire is the origin row's witness, noted in the task log). [class: REPOSITORY_TEST]
- [ ] Run the Validation Commands; expect all suites green. [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin the rebased-tip re-pin and its dating discipline` [class: IMPLEMENTATION_REQUIRED]
