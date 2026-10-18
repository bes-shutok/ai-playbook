# Plan: verify-records resolves explicit review citations only, with Path-consistent candidates

Backlog origins (scope of record):
- docs/history/backlog/2026-10-06-closeout-verify-records-false-positives.md
- docs/history/backlog/2026-10-10-worktree-closeout-record-checker-overmatches-paths.md
- docs/history/backlog/2026-10-11-closeout-verify-records-str-crash.md
Driving force: reliability (outside the five driving principles; justification: three witnessed closeouts were blocked or degraded by the same preflight, once by nineteen false missing-review rows, once by repeated false misses across two runs, and once by an AttributeError crash; the remedy narrows an existing check's resolution rule on the landing-closeout critical path, and park-triage would not take it because every occurrence blocks a legitimate worktree teardown)
Plan review record: the staging series {reviews_dir}/2026-10-14-plan-review-closeout-verify-records-citation-resolution-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-14-closeout-verify-records-citation-resolution.md (session sess_4d6217a8-4acc-4047-85c0-1db95d18adb7)

## Terms

- verify-records: the `scripts/worktree_closeout_migrate.py` subcommand that verifies a plan's cited and caller-claimed review records against the target's primary reviews home; plain-exit convention (0 verified, 1 missing records named on stderr, 2 named failure) with one JSON line on stdout.
- Reviews home: the target checkout's facts-resolved `reviews_dir`, never the source worktree's gitignored twin.
- Exact citation token: a path-like plan token (`.md` or `.json`) whose basename carries a concrete round number or no round marker; checked as one path.
- Series citation token: a token whose basename carries the `-r*` round marker immediately before the `.md` extension (the round glob form); expanded to its present members with the numerically highest as witness.
- Basename fallback: the exact-token arm that re-anchors a token not resolving under the reviews home as `home / basename`.
- Explicit reviews-home citation: a token whose absolute or target-relative form resolves under the reviews home, with containment judged on filesystem-resolved paths on both sides (the citation candidate and the home), link-following kept exactly as the series arm's documented legacy behavior.
- Owned record: the executing plan's own review record cited in its header's staging-series line or body.
- Folded origin row: a backlog row merged into another row's cluster at landing, so its old path no longer exists at the top level.
- Claimed record: a `--claims` file entry; outside-home entries are skipped with a named warning, inside-home entries must exist.

## Why

The verify-records preflight treats every path-like token in a plan's bytes as a possible review citation: its ignore arm is dead code because the basename fallback it tests against is contained in the reviews home by construction, so every nonexistent prose citation becomes a missing-review row and the exit 1 blocks the closeout. A separate construction slip leaves absolute path tokens as plain strings, so the candidate existence test raises AttributeError. Three closeouts across five days hit these shapes; each time the run degraded to targeted manual checks or a blocked preflight.

## Gist & Examples

TLDR: the closeout record preflight stops manufacturing missing-review rows out of ordinary plan prose and stops crashing on absolute path tokens, so a closeout passes exactly when its declared review records are present, per the reliability driving force.

Before (today): a plan body citing its folded origin row, archived dependency plans, tmp baselines, and skill docs fails the preflight with every one of those tokens reported missing under the reviews home, because the tautological containment test makes the ignore branch unreachable and the basename fallback manufactures a reviews-home candidate for each. A plan citing an absolute path token crashes the preflight with `AttributeError: 'str' object has no attribute 'exists'` before any verdict is printed.

After (this plan): an exact token is a review citation only when its absolute or target-relative form resolves under the reviews home (missing there means a genuinely missing declared record, named exactly), or when its basename matches an existing review file at the home (identified, checked, passes); every other token is ignored without manufacturing a candidate. Absolute tokens are built as `Path` from the start, so the crash shape is gone. Series expansion, claimed-record checks, exit codes, and the JSON shape are untouched.

Edge cases pinned: the witnessed folded-origin shape (nineteen nonexistent prose citations, owned record present) exits 0; a target-relative citation under the reviews home whose file is absent still exits 1 naming the exact home path; a bare-basename token matching an existing review file is checked and passes; an absolute token that exists under the home is contained and checked, never basename-verified, and an absolute token under the home whose file is absent exits 1 naming the exact absolute path; containment is judged on resolved paths, so a `..`-bearing citation that lands under the home after resolution is a checked citation (absent file: exit 1) and a `..`-threaded escape past the home with an absent basename is ignored; an absolute token outside the home is ignored like any other non-review path.

## Outcome

A closeout's record preflight reports exactly the records that are genuinely missing: declared citations under the reviews home, absent series, and claimed records inside the home, and ordinary plan prose never blocks a teardown again.

- A plan citing its present owned record plus ordinary backlog, source, tmp, and docs paths passes with exit 0 (the first origin's named acceptance).
- A genuinely absent declared record still fails and names the exact expected home path (the second origin's acceptance).
- Absolute path tokens classify instead of crashing (the third origin's ask).
- The module docstring's subcommand list names every reachable subcommand.

Gate delta: no new refusal class, hard gate, fence, protocol layer, or schema field; one false-refusal arm removed (the exact-token basename fallback that reported nonexistent non-review paths as missing under the reviews home); the exact-token missing arm survives only for citations resolving under the reviews home, and the basename fallback survives only as existing-file identification that can never manufacture a missing row; series, claims, exit-code, and JSON contracts unchanged. Accepted residual, named: citations in bare-basename form whose record is absent at the home, and absolute citations outside the home, are ignored rather than failed; the declared citation channels that still fail closed are the header staging series, explicit home-resolving paths, and claims-file entries inside the home. No gate or fence is added, so no guard liveness ledger citation is due. The removal is priced by the three origin rows' witnessed closeout blocks, and this plan's Rejected alternatives section records why each alternative is impossible or worse, which is the origin-cited no-exit justification form.

## Assumptions

- The subcommand keeps its plain-exit convention (0/1/2, JSON, no `OUTCOME:` lines); basis: `docs/history/plans/completed/2026-10-06-exec-review-record-primary-home-fence.md` records this assumption for the subcommand it introduced, and the file's existing verify-records exits match it.
- The narrowed fallback follows the first origin's Expected text: the basename fallback applies only to tokens already identifiable as review records, with an existing review file at the home as the identification test; basis: docs/history/backlog/2026-10-06-closeout-verify-records-false-positives.md, Expected section.
- The existing-basename identification arm is kept rather than deleted to the two-arm form: it can never change an exit code or stderr line (its only effect is a complete JSON `checked` list for present bare-basename citations, preserving today's harmless JSON behavior), and the first origin's Expected names it as the sanctioned fallback scope; basis: docs/history/backlog/2026-10-06-closeout-verify-records-false-positives.md, Expected section.
- Absolute citations stay exact-path checks and are never basename-verified; basis: the gate-removal contract's absolute-citation stance, documented in the module docstring, applied symmetrically to verify-records.
- The third origin's CLI-shape question resolves as sanctioned present, not drift: `main()` routes both `gate-removal` and `owned-files-clean` before the legacy parser, each through its own standalone OUTCOME-contract parser, and `owned-files-clean` landed 2026-10-10 (1477a946c) with the wip-auto-checkpoint execution; the row's absence note was derived from a parser-registration grep that the pre-parser routing is invisible to. No parser change is needed; the residue is the module docstring's subcommand list, which names neither verify-records nor owned-files-clean; basis: `main()` routing in scripts/worktree_closeout_migrate.py and `git log -S owned-files-clean`.
- The JSON output keeps its existing four keys; ignored tokens appear in no list, and no new field is added; basis: `docs/history/plans/completed/2026-10-06-exec-review-record-primary-home-fence.md`'s no-new-schema-field gate delta.
- Tests extend the existing verify-records fixture class in its established temp-dir style; basis: that class's existing helpers in `scripts/test_worktree_closeout_migrate.py` and the fixture-placement assumption in `docs/history/plans/completed/2026-10-06-exec-review-record-primary-home-fence.md`.

Decision points requiring a grill: none remain.

## Rejected alternatives

- Remove `verify-records` and trust later migration: rejected because the primary-home fence was introduced to stop worktree-only review records from surviving teardown as unverified artifacts; removing the check reopens the witnessed stranding class (docs/history/plans/completed/2026-10-06-exec-review-record-primary-home-fence.md).
- Keep the current resolver unchanged: rejected because its basename fallback makes nonexistent ordinary plan paths look like missing review records, and the candidate string can crash before the check completes (scripts/worktree_closeout_migrate.py).
- Widen matching to every path-like basename regardless of record type: rejected because prose paths outside the reviews home are not review records and the completed fence plan limits body citations to reviews-home paths (docs/history/plans/completed/2026-10-06-exec-review-record-primary-home-fence.md).
- Rewrite execute-plan prose to omit ordinary plan paths: rejected because the helper's original contract explicitly limits body citations to paths resolving under the reviews home, and the plan body naturally names archived or folded inputs (docs/history/plans/completed/2026-10-06-exec-review-record-primary-home-fence.md).
- Add a separate validator, ledger, or ceremony around the helper: rejected because the witnessed defects are in the existing resolver, no separate incident justifies more machinery, and the repository's machinery admission protocol defaults to fewer blockers (scripts/worktree_closeout_migrate.py).

## Evaluation Criteria

**Quality dimensions:**
- correctness: an exact token yields exactly one of three dispositions (checked under-home citation, identified existing-basename citation, ignored non-review token); candidate construction never holds a plain string; the disposition holds for absolute, target-relative, and bare-basename tokens alike.
- no weakening: the series arm (highest-member witness, zero-member failure), the claims arm (outside skipped with warning, inside must exist), the exit-code contract, and the JSON keys are byte-for-byte behaviorally unchanged; the subcommand's existing fixtures pass without modification.
- testability: each new disposition pins through a fixture with both the pass and the fail shape where a fail shape exists.

**Done when:**
- The false-miss fixture, the crash fixture, the missing-declared-record fixture, and the existing-basename fixture pass, and the full test file's suite passes.
- The module docstring lists all six reachable subcommands (capture, migrate, gate-removal, sweep, verify-records, owned-files-clean).

**Ship when:**
- Nothing external; every acceptance condition is repository-verifiable through the validation commands below.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/worktree_closeout_migrate.py` (the `cmd_verify_records` exact-token region and the module docstring)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py` (the verify-records fixture class)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `gate-removal`, `sweep`, `migrate`, `capture`, and `owned-files-clean` behavior in the same helper; reason: the origins tie no defect to them, and the CLI-shape question resolves without parser changes.
- `agents/skills/execute-plan/SKILL.md` prose; reason: rewriting executor prose to avoid the checker is a rejected alternative.

## Validation Commands

```bash
python3 scripts/test_worktree_closeout_migrate.py
python3 scripts/worktree_closeout_migrate.py verify-records --plan docs/history/plans/2026-10-14-closeout-verify-records-citation-resolution.md --target "$(dirname "$(git rev-parse --git-common-dir)")"
```

The second command is the live self-check, run from the authoring worktree: `git rev-parse --git-common-dir` resolves the primary checkout's git dir, so the `dirname` operand is the primary checkout whose facts-resolved reviews home holds the staged records, never the worktree's gitignored twin. Its exit-0 verdict presupposes this plan's own review record (the staging series' highest member) is already staged under that primary home; a mid-review run against a home without the record exits 1 by design and is not a fix failure. The plan's backlog-origin citations must be ignored either way.

### Task 1: Narrow exact-token resolution and make candidate construction Path-consistent

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `cmd_verify_records` in `scripts/worktree_closeout_migrate.py`

- [x] Pin the false-miss disposition: given a plan citing its present owned round record plus nonexistent backlog, archived-plan, and tmp paths, expects exit 0 with the owned record checked and an empty missing list [class: REPOSITORY_TEST]
- [x] Pin the crash disposition: given a plan body citing an absolute path token outside the reviews home, expects exit 0 with a JSON line whose checked, missing, skipped, and series_witness are all empty, and no traceback on stderr [class: REPOSITORY_TEST]
- [x] Pin the absolute-contained checked shape: given an absolute path token whose file exists under the reviews home, expects exit 0 with the token checked, never basename-verified [class: REPOSITORY_TEST]
- [x] Pin the absolute-contained missing shape: given an absolute path token under the reviews home whose file is absent at the target, the token living in a home subdirectory while a different existing file of the same basename sits directly at the home root, expects exit 1 naming the exact absolute path with no basename substitution; a basename-verifying implementation would flip this verdict to exit 0 [class: REPOSITORY_TEST]
- [x] Pin the missing-declared-record survival: given a target-relative citation under the reviews home whose file is absent at the target, expects exit 1 naming the exact home path [class: REPOSITORY_TEST]
- [x] Pin the existing-file identification: given a bare-basename token matching an existing review file at the home, expects exit 0 with the token checked [class: REPOSITORY_TEST]
- [x] Pin resolved-path containment: given a facts reviews_dir that is an absolute path through a symlink and a target-relative citation whose file is absent, expects exit 1 naming the home path; and given a `..`-bearing citation that lands under the home after resolution with the file absent, expects exit 1 [class: REPOSITORY_TEST]
- [x] Pin the escape-token ignore: given a `..`-threaded citation escaping past the reviews home whose basename matches no home file, expects the ignored disposition with exit 0 [class: REPOSITORY_TEST]
- [x] Pin the claims-arm inside-must-exist witness: given a claims file with one inside-home absent entry and one present inside-home entry, expects exit 1 with the absent entry in missing naming the target-anchored path, the present entry in checked, and an empty skipped list [class: REPOSITORY_TEST]
- [x] Run → expect RED: the false-miss, crash, absolute-token, escape-token-ignore, and folded-origin safety-witness fixtures fail against today's resolver (manufactured missing rows, the AttributeError); the survival pins (missing-declared-record, existing-file identification, claims) and the resolved-containment pins pass today by design and guard against regression [class: REPOSITORY_TEST]
- [x] Implement the three-arm exact-token classification (resolve-under-home check, existing-basename identification, ignore) and wrap absolute tokens as `Path` so candidate construction never holds a plain string; judge containment on filesystem-resolved paths on both sides (candidate and home resolved once), keeping the missing-path display via the `home / token` form and link-following matching the series arm's legacy behavior [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the new fixtures and the subcommand's existing fixtures all pass, the latter unmodified [class: REPOSITORY_TEST]
- [x] Safety witness: given the witnessed folded-origin closeout shape (a plan whose body cites many nonexistent prose paths while its owned record is present at the home), expects exit 0 so the closeout proceeds to teardown [class: REPOSITORY_TEST]
- [x] Commit: `fix: verify-records ignores non-review citations and builds candidates as Path` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Complete the docstring subcommand list behind the CLI-shape adjudication

Context surface: the plan's Terms, this task, and `## Assumptions` (the CLI-shape adjudication bullet); referenced, never restated.

Files:
- `scripts/worktree_closeout_migrate.py`

Primary class anchors:
- `main` in `scripts/worktree_closeout_migrate.py`

- [x] Add verify-records and owned-files-clean summaries to the module docstring's subcommand list, each stating its exit contract in the list's established style [class: IMPLEMENTATION_REQUIRED]
- [x] Verify both subcommand help surfaces parse and exit 0 [class: REPOSITORY_TEST]
- [x] Run the full suite → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `docs: list verify-records and owned-files-clean in the closeout helper docstring` [class: IMPLEMENTATION_REQUIRED]
