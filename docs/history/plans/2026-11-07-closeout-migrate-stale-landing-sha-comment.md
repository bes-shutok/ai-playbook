# Plan: Correct the stale pre-rewrite landing sha citations in the closeout-migrate surfaces

Backlog origin: docs/history/backlog/2026-11-01-closeout-migrate-stale-landing-sha-comment.md
Driving force: correctness
Plan review record: the staging series .ai-playbook/reviews/2026-11-07-plan-review-closeout-migrate-stale-landing-sha-comment-pbdcb317b-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Executed: no

## Terms

- pre-rewrite twin: a commit sha left behind by a squash landing rewrite; it resolves as an object but is not an ancestor of the default branch, so it cites a landing that never landed (lesson 359: ancestry, not existence).
- squash-twin signature: two dangling commits carrying the identical subject line, the mark of one landing rewritten more than once.
- receipt line: a `PLAN-PROMPTS-PRUNE:` line in `docs/history/backlog/PLAN-PROMPTS.md` recording a pruned entry; the prune audit resolves its witness token by object existence.
- ancestry witness: a sha that passes both `git cat-file -e` and `git merge-base --is-ancestor <sha> main`; the only sha form a landing citation may carry.
- the closeout-gates trio: the closeout-gates change (expired gate-report destinations report-only in gate-removal; FM_OUT local; identity-arm residual wording plus pins), landed on main by the batch landing `843cc9709e12aa1255a24d483cd4a092e5d8dd26` (subject "execute-plan: land closeout gate trio, vendored sync, and doctrine corrections (2026-10-31)"; the subject "closeout: land done-closeout-gates-trio" exists only on the dangling twins, so the witness check passes on ancestry plus this recorded subject, never on subject equality with the old slug).
- origin row: the backlog row at `docs/history/backlog/2026-11-01-closeout-migrate-stale-landing-sha-comment.md` that spawned this plan; its evidence text keeps the historical shas and stays out of scope.
- swept-artifact classification comment: the inline block inside `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py` that labels swept closeout artifacts by landing sha.
- durable citation span: a sha citation in a tracked, durable surface (script comment, receipt line, or test comment), as opposed to session notes.

## Why

Five durable citation spans across four files cite the closeout-gates trio by a dangling pre-rewrite sha (`52750a1fe...`), so a reader who git-logs the citation reaches a landing that never landed. The origin row's named replacement is also dangling, so the citations must be corrected to a sha verified ancestral on main, derived from disk at authoring time.

## Gist & Examples

TLDR: five stale sha citations across four files move to the verified ancestral trio landing digest, so every citation resolves as a landed commit, priced by the correctness force.

Before: the swept-artifact classification comment in `scripts/worktree_closeout_migrate.py`, the `gate-removal-drained-destination-disposition` receipt line in `docs/history/backlog/PLAN-PROMPTS.md`, and three test-comment spans cite `52750a1fe...`; `git log` on it dead-ends.
After: the same spans cite `843cc9709e12aa1255a24d483cd4a092e5d8dd26`, which passes the object-existence and ancestry probes; `git log` reaches the real landing.

## Outcome

The five citing spans in this plan's scope name a landing commit that is reachable from main.

- The five citing spans resolve through `git log` to the real trio landing.
- The receipt line's witness token resolves not just as an object but as an ancestor of main; the audit's resolution mechanism is unchanged (Gate delta: none).
- No behavior change: comment and citation bytes only, guard code untouched.

Gate delta: none; no gate, validator, lock, ledger, refusal class, or required ceremony is added, removed, or changed.

## Assumptions

- assume the verified live landing digest for the closeout-gates trio is `843cc9709e12aa1255a24d483cd4a092e5d8dd26`; basis: disk re-derivation 2026-11-07 (`git log -S` over `main` shows it introduces both the script comment block and the test spans; `git merge-base --is-ancestor` passes).
- assume the origin row's named replacement `eebc930c0` is not usable; basis: disk re-derivation 2026-11-07 shows it resolves as an object but `git merge-base --is-ancestor eebc930c0 main` fails (rc 1); the row's premise that `eebc930c0` is the live ancestor replacement is rewritten to the verified digest per the plans skill's origin-rewrite rule, and this assumption is that recorded rewrite.
- assume the sibling dangling-literal citations under `eebc930c0` (the same dangling landing, other abbreviation) are known-remaining outside this plan's scope: the origin row's verdict entry at `docs/history/backlog/PLAN-PROMPTS.md` (removed by this plan's own landing prune), two completed-plan archives under `docs/history/plans/completed/`, and one lessons-corpus witness; basis: repo-wide grep 2026-11-07; disposition: omit-extension (the completed archives are immutable history and the lessons corpus owns its own correction lane).
- assume the five spans listed in Review Scope are the complete citation set at authoring time; basis: repo-wide grep over tracked files at authoring time found no further `52750a1fe` literal outside the origin row's and this plan's own quoted evidence text; execution re-sweeps before committing.
Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every corrected span's new sha passes `git cat-file -e` and `git merge-base --is-ancestor <sha> main`; the old sha fails the ancestry probe.
- completeness: a repo-wide tracked-file grep for `52750a1fe` returns zero hits outside the origin row's and this plan's own quoted evidence text.
- behavior preservation: the two touched test suites pass unchanged; no guard code or decision semantics move.

**Done when:**
- the five citing spans name the verified digest; the sweep is clean; both suites are green; the working tree is clean.

**Ship when:**
- none; this is a repository-internal correction with no external release condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/worktree_closeout_migrate.py` (Task 1)

**Tests:**
- `scripts/test_done_run_wrapper.py` (Task 1)
- `scripts/test_worktree_closeout_migrate.py` (Task 1)

**Documentation:**
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it corrects another citing span the sweep surfaces, or fixes a regression introduced by plan work. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-11-01-closeout-migrate-stale-landing-sha-comment.md`; reason: the origin row's own evidence text is the incident record and keeps its historical shas.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py -q
git grep -n "52750a1fe" -- ':!docs/history/backlog/2026-11-01-closeout-migrate-stale-landing-sha-comment.md' ':!docs/history/plans/2026-11-07-closeout-migrate-stale-landing-sha-comment.md' && exit 1 || exit 0
git merge-base --is-ancestor 843cc9709e12aa1255a24d483cd4a092e5d8dd26 main
```

### Task 1: Correct the five stale sha citations to the verified ancestral trio landing

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/worktree_closeout_migrate.py`
- `docs/history/backlog/PLAN-PROMPTS.md`
- `scripts/test_done_run_wrapper.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `_gate_branch_closeout` in `scripts/worktree_closeout_migrate.py`

- [ ] The swept-artifact classification comment in `scripts/worktree_closeout_migrate.py` (inside `_gate_branch_closeout`) cites the verified digest: given `git merge-base --is-ancestor <new sha> main`, expects success; given `git log -S "landed 52750a1fe" main -- scripts/worktree_closeout_migrate.py`, expects the new sha as the oldest introducing hit [class: IMPLEMENTATION_REQUIRED]
- [ ] Subject witness: given `git log -1 --format=%s <new sha>`, expects the batch trio landing subject recorded in Terms; the subject differs from the dangling twins' slug, so the check never compares against the old slug [class: REPOSITORY_TEST]
- [ ] The `PLAN-PROMPTS-PRUNE: gate-removal-drained-destination-disposition` receipt line carries the verified digest in full 40-hex form as its witness: given the prune audit's token resolution, expects the token to resolve as an object and an ancestor; the landing closeout's prune audit then surfaces one warning-only RECEIPT-WITHOUT-REMOVAL line for this token refresh beside the surviving entry, an expected outcome the change's report names rather than investigates [class: IMPLEMENTATION_REQUIRED]
- [ ] The two comment spans in `scripts/test_done_run_wrapper.py` and the one in `scripts/test_worktree_closeout_migrate.py` citing `52750a1fe` cite the verified digest: given a grep over the touched files, expects zero old-sha hits and the new sha present [class: IMPLEMENTATION_REQUIRED]
- [ ] Sweep: a repo-wide tracked-file grep for `52750a1fe` returns zero hits outside the origin row's and this plan's own quoted evidence text; any newly surfaced citing span is corrected in the same change [class: REPOSITORY_TEST]
- [ ] Safety witness: given `git merge-base --is-ancestor 52750a1fe7ae0de83cc622f87a8d91bad9543216 main`, expects failure, recorded in the change's report text so the replacement reason stays reproducible [class: REPOSITORY_TEST]
- [ ] Run the two suites per Validation Commands -> expect GREEN unchanged [class: REPOSITORY_TEST]
- [ ] Commit: `closeout: cite the verified ancestral trio landing in the closeout-migrate sha citations` [class: IMPLEMENTATION_REQUIRED]
