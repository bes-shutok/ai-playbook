# Done Step 3 pre-commit adjudication flags a missing review record as a witnessed reconstruction duty

[github: https://github.com/admitriev/ai-playbook] Origin: docs/history/backlog/2026-09-28-review-record-destroyed-with-exec-worktree.md (residual third expectation; its first two are already implemented)

## Gist TLDR

The origin item's transfer-out contract (migrate gitignored review records before worktree removal, verify by digest, gate removal on it) is already implemented by the Worktree-first standard and `worktree_closeout_migrate.py` (default dirs `docs/reviews docs/tmp`, per-file checksum verification, removal gated on migration). The unimplemented residual: when a record was destroyed anyway, no later run ever notices. This plan adds a done Step 3 pre-commit adjudication arm (0-series item 0d, after the stale-checkout adjudication 0c - the position the origin item loosely calls "Step 0" flags) that mechanically detects a missing review record for an archived plan by scanning the archived plan's own recorded review links against the live review corpus, and reports it as a reconstruction duty with a witness note. Detection only: never fabricate content, never block the run, never delete.

## Outcome + Gate delta

Witnessed 2026-09-28 (release-skill-follow-ups execution): the r2 code-review record was destroyed with the exec worktree and had to be recreated in the main checkout by hand with no source artifact to verify against.

The detection anchor is the archived plan file, not the run's session directory: session directories under `{tmp_dir}/execute-plan/` are evicted by the first docs-tmp-sweep after the plan archives, so they are a one-run witness at best, while archived plan files under `{plans_completed_dir}` are committed and durable, and plans written after the certification-line convention cite their review records there (for example `Plan review: docs/reviews/<record>.md`; older cite-less plans are the undetectable class stated in the arm bounds). Scanning those citations against the live `{reviews_dir}` survives sweeps, teardowns, and host restarts.

After this plan, done Step 3 gains adjudication arm 0d (immediately after 0c, before item 1's gates):

- Resolve both sides at the main checkout: the archived plan files under `{plans_completed_dir}` (tracked, identical in every checkout) and the live review corpus at the main checkout's `{reviews_dir}`, the canonical post-migration location - never a worktree's bootstrap-time copy, which lacks records created after bootstrap.
- In each archived plan file, find review-record references: filename literals containing `plan-review` or `code-review` with a trailing `-r<N>` before the extension (the repository's actual naming convention `<date>-plan-review-<slug>-r<N>.md` / `<date>-code-review-<slug>-r<N>.md`; a literal adjacency like `plan-review-r1` almost never occurs in real record names).
- A referenced record absent from the main checkout's `{reviews_dir}` is a reconstruction duty: reported in the run report (Step 7) with a witness note naming the citing plan and the missing path. The docs branch is not consulted at this position because it need not be: done Step 2's docs-branch add-only sync restores branch-present shadow files (reviews included) into the live checkout before Step 3, so live absence at this position means the record is gone from both surfaces; the witness note may still mention the branch as a historical last resort for records that predate that restore.
- The arm never fabricates record content, never blocks the run (the loss already happened; blocking cannot recover it), and never deletes anything.

Out of scope: changes to `worktree_closeout_migrate.py`, the execute-plan Worktree-first standard (both own the preventive contract), and retroactive reconstruction of the 2026-09-28 record beyond what a future run's report surfaces.

## Terms

- **Archived plan**: a plan whose file sits under `{plans_completed_dir}`; committed, therefore a durable witness.
- **Review-record reference**: a filename literal inside an archived plan file containing `plan-review` or `code-review` with a trailing `-r<N>` before the extension, resolving to a path under `{reviews_dir}`.
- **Reconstruction duty**: a reported obligation to rebuild a lost record from its witnesses, with the citing plan named; discharge belongs to a later review-reconciliation pass, not to the adjudication arm.

## Assumptions

- The plan-file citation is the detection anchor because it is durable where session directories are not (the docs-tmp-sweep legitimately evicts archived-plan session dirs, so a session-dir anchor would scan an empty corpus on every run after the first post-archive sweep). Plans written before the certification-line convention carry no citation and are honestly undetectable - stated in the arm.
- The arm lives in the done skill prose only (no new gate in `done_sweep_gates_lib.py`): the done workflow is a markdown skill, the detection is a one-pass read-only scan per run, and a hard gate would fail closed on legacy repos whose archived plans carry no citations.
- Placement at the Step 3 0-series (after 0c) rather than literal Step 0 is deliberate: Step 2's add-only restore has run by then, making the live corpus authoritative without a branch walk; the origin item's "done Step 0" phrasing maps to the 0-series adjudication family that 0c already occupies and 0d joins.

Decision points requiring a grill: none - the origin item's Expected section prescribes the flag-with-witness-note shape; the anchor, pattern, and placement decisions above were forced by r1 review evidence (sweep eviction of session dirs, measured record-naming corpus, 0c's actual step) without changing the prescribed outcome.

### Task 1 - Done Step 3: the missing-review-record adjudication arm (0d)

- [ ] In `agents/skills/done/SKILL.md`, add item **0d. Missing-review-record adjudication (before any disposition).** immediately after the stale-checkout adjudication (0c): resolve `{plans_completed_dir}` and the main checkout's `{reviews_dir}` (never a worktree-local corpus); scan archived plan files for review-record references (filenames containing `plan-review` or `code-review` with a trailing `-r<N>` before the extension); a referenced record absent from the live reviews corpus is a reconstruction duty, reported in the run report carried to Step 7 with a witness note naming the citing plan and the missing path, which may mention the docs branch as a historical last resort. State the bounds: never fabricate record content, never block the run, never delete; cite-less legacy plans are undetectable. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the same file, the workflow-continuity parenthetical (the line beginning "**Workflow continuity:**") gains the 0-series naming: insert the exact phrase "the 0c and 0d adjudications" into the step sequence (Validation command 2 greps that literal) - the line today names no 0-series items at all, so this is an insertion, not a modification. [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Validation

- [ ] All checks in Validation Commands pass from the worktree root. [class: REPOSITORY_TEST]

## Evaluation Criteria

- Done Step 3 carries the 0d arm with the durable plan-file anchor, the corrected filename pattern (token containment plus trailing `-r<N>`), the main-checkout resolution pin on both sides, the reconstruction-duty reporting with witness note, and the never-fabricate/never-block/never-delete bounds.
- The workflow-continuity line names the 0-series adjudications (0c and 0d).
- No other arm's text is disturbed; the docs-tmp-sweep bullet and transfer-out contracts are untouched.

## Review Scope

Files: `agents/skills/done/SKILL.md` (the new 0d item in Step 3, the workflow-continuity parenthetical, and no other lines). Contract files referenced read-only: `scripts/worktree_closeout_migrate.py`, `agents/skills/execute-plan/SKILL.md` (Worktree-first standard, transfer-out), origin backlog item.

## Validation Commands

Run from the worktree root:

1. `grep -n "Missing-review-record adjudication" agents/skills/done/SKILL.md` - the 0d item exists.
2. `sed -n '/Workflow continuity/p' agents/skills/done/SKILL.md | grep -c "0c and 0d"` - prints 1 (the phrase exists only if the continuity line was actually updated; the arm body cannot satisfy it).
3. `grep -n "reconstruction duty" agents/skills/done/SKILL.md` - the reporting duty and witness note are present.
4. `test "$(grep -c docs-tmp-sweep agents/skills/done/SKILL.md)" = "$(git show main:agents/skills/done/SKILL.md | grep -c docs-tmp-sweep)" && echo untouched` - the sweep contract is untouched relative to main.
