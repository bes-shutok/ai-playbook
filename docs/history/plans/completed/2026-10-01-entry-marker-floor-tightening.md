# Plan: Investigate entry marker floor: file-path precision and paren anchoring

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-09-30-investigate-entry-marker-floor-tightening.md`
Driving force: correctness; secondary simplicity

## Gist TLDR

TLDR: tighten the entry validator's path marker so a bare directory path (`docs/history/backlog/`) no longer counts as evidence while a real `.md` file path does, and require a citing disposition line to END with the citation parenthetical (or the path itself) so unverified free-text tails stop riding after a real path - the floor stays structural, the precision rises.

## Outcome + Gate delta

The two witnessed leak shapes close: a disposition citing only the corpus directory (`docs/history/backlog/`) no longer passes the path marker (the marker requires the matched span to end in `.md` or point at an existing file), and a real path followed by trailing free text (`docs/...md scope decision`) passes only when the text after the path is empty or inside the citation parenthetical. The p93 entry's basis line is citation-fixed in the same execution.

Gate delta: the `PATH_MARKER_RE` regex tightens (requires `.md` suffix on the matched span), one new post-match file-existence check in the marker predicate (an existing file also counts, for non-.md repo paths), and the disposition-line acceptance requires the line to end at the path/citation (trailing prose after the parenthetical fails); the live p93 line gains its file-path citation; no new gate, schema, or refusal class.

## Terms

- **Directory-only citation**: a matched path span ending in `/` or a bare directory name - the corpus home, not a witness.
- **Trailing tail**: free text after the matched path span on the same line (outside a citation parenthetical).
- **Citing disposition line**: a `Rejected alternatives:` list item carrying at least one marker.

## Assumptions

- Requiring `.md` suffix or on-disk existence covers the corpus's real citations (they cite plan/origin `.md` files and scripts); a hypothetical citation of a non-md existing file keeps passing via the existence check.
- The p93 line's own prose names the plan it means; the citation-fix appends the plan's actual repo-relative `.md` path, so the tightened marker passes on the corrected line.

Decision points requiring a grill: none remain - the origin's two leak shapes prescribe both tightenings verbatim.

### Task 1 - The tightened marker and the paren anchor

- [x] In `scripts/check_investigate_entries.py`: tighten `PATH_MARKER_RE` so the matched path span must end in `.md` (the corpus's citations are file paths; a bare `docs/history/backlog/` directory no longer matches); add a fallback in the marker predicate - a non-`.md` span still passes when the file exists on disk relative to the repo root; and require a citing disposition line to END with the citation parenthetical or the matched path (trailing free text after it fails the marker with the line named). Update the docstring's marker description. [class: IMPLEMENTATION_REQUIRED]

### Task 2 - Live-corpus citation fix and suite arms

- [x] Citation-fix the live p93 entry's basis line: append the actual plan/origin `.md` path it names so the tightened marker passes; sweep the live log for any other line the tightened marker now fails and citation-fix those identically. [class: IMPLEMENTATION_REQUIRED]
- [x] The entry validator's corpus run is the test surface per the plan's assumptions (no separate test file); verify all live entries pass against the tightened marker. [class: REPOSITORY_TEST]

### Task 3 - Validation

- [x] Run every Validation Command below from the worktree root; each must pass against the amended tree. [class: REPOSITORY_TEST]

## Evaluation Criteria

- A directory-only citation (`docs/history/backlog/`) no longer passes; a real `.md` path passes; an existing non-md file passes via existence.
- A real path followed by trailing free text fails; a line ending at the path or parenthetical passes.
- The live log passes the tightened validator (the p93 line citation-fixed).

## Review Scope

Editable regions: `scripts/check_investigate_entries.py` (the path marker, the marker predicate, the docstring), `docs/history/backlog/PLAN-PROMPTS.md` (disposition-line citation fixes only). Read-only: the origin backlog item; every other file.

## Validation Commands

Run from the worktree root; every check fails closed (a miss or an error aborts non-zero).

1. `python3 scripts/check_investigate_entries.py || { echo FAIL: live log; exit 1; }` - the tightened validator passes the live corpus.
2. `grep -qF '.md' scripts/check_investigate_entries.py && grep -qF 'endswith' scripts/check_investigate_entries.py || { echo FAIL: tightening missing; exit 1; }` - the suffix requirement and the endswith anchor are pinned.
3. `python3 scripts/check_investigate_entries.py --help >/dev/null || { echo FAIL: validator broken; exit 1; }` - the validator itself is runnable (the directory-only-citation and trailing-tail behaviors are pinned by the corpus run in command 1: the live p93 line is citation-fixed to a file path, so a regression to directory-acceptance would re-fail the corpus if any line still cites the bare directory; the fixture-based behavioral pins live in the execution log, not this block, per the validator's corpus-run test-surface assumption).
4. `bash scripts/check-no-em-dash.sh added-lines --base main || { echo FAIL: em dash; exit 1; }` and `bash scripts/scan-public-hygiene.sh || { echo FAIL: hygiene; exit 1; }` - both exit 0.
