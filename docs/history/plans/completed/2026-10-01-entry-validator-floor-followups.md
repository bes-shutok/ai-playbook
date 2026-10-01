# Plan: Entry-validator floor follow-ups

Backlog origin (scope of record): `docs/history/backlog/2026-10-01-entry-validator-floor-followups.md`
Driving force: documentation precision; fail-safe consistency
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-entry-validator-floor-followups-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The four marker-floor follow-ups land as one pass: the subdirectory invocation gets a named hard refusal instead of a silently weaker existence arm, the single-line disposition constraint and the citation tail-strip edge are stated where future editors read, and the investigate skill's floor description points at the validator docstring as the owning list.

- `scripts/check_investigate_entries.py` refuses (exit 2, named message) when invoked outside the repository root (the git toplevel differs from the cwd), because the documented cwd-relative path convention silently drops the `isfile` existence arm from a subdirectory; the repo-root invocation behavior is unchanged.
- The validator docstring states the single-line disposition constraint (the per-line END anchor rejects a citation landing mid-block in a multi-line disposition style - latent today, pinned as documented) and carries a note beside `CITATION_TAIL_CHARS` that the strip can remove a legitimate trailing character from an exotic filename (accepted trade).
- `agents/skills/investigate/SKILL.md` Stage 4's structural-minimum sentence names the validator docstring as the owning list for the marker semantics (the skill's older path/hex/witness-token phrasing stays as the summary it is) so a future editor is pointed at the drift-sensitive source.

Gate delta: one new refusal surface (subdirectory invocation, exit 2) on the entry validator; two documentation notes; one skill pointer sentence. No existing behavior changes for repo-root invocations.

## Terms

- cwd convention: the validator resolves citation paths relative to the process cwd (its documented path convention).
- Floor: the structural minimum `check_investigate_entries.py` owns (non-empty rejected alternatives, evidence-cited dispositions, file-precision marker semantics).

## Assumptions

- The refusal is the right arm over auto-resolving paths to the repo root: the script's docstring pins cwd-relative resolution as the convention, and silently re-rooting would change citation semantics for every existing caller; a hard named refusal keeps the convention and fails closed on the environment mismatch (the corpus's missing-validator treatment).
- The git toplevel check uses `git rev-parse --show-toplevel` from the cwd; a non-git cwd or a detached toplevel mismatch both refuse with the same named message.
- The skill's Stage 4 sentence is the only touch point; the older marker phrasing elsewhere in the skill is the summary the origin already accepted as drift-tolerant.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: subdirectory invocations of the entry validator refuse with a named error, the docstring owns its two known sharp edges in writing, and the skill points at the docstring; force: documentation precision, fail-safe consistency.

Today an investigate session that runs the validator from a subdirectory silently loses the existence arm of the file-evidence check (every repo-relative span reads as non-file), and neither the single-line disposition constraint nor the tail-strip trade is written anywhere an editor would look. After this plan the mismatch refuses loudly and the two constraints live in the docstring the skill points at.

## Evaluation Criteria

**Quality dimensions:**
- Fail-closed: the new refusal fires on every non-repo-root cwd and never on the repo root; the message names the mismatch and the fix (run from the repository root).
- Documentation lands where editors read: both constraints sit in the docstring beside the code they constrain; the skill points rather than restates.

**Done when:**
- Every Validation Commands line exits 0 and the guard pin holds.

**Ship when:**
- The next investigate Stage 4 run exercises the validator (operator-observed; external condition, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_investigate_entries.py`
- `agents/skills/investigate/SKILL.md` (one pointer sentence)

**Tests:**
- `scripts/test_check_investigate_entries.py` (new guard pins; created only if the file does not exist, else extended)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- changing the cwd-relative path convention to repo-root resolution; reason: rejected in Assumptions, the convention is documented and callers depend on it.
- the marker-floor predicate itself; reason: the marker-floor-tightening plan owns it; this pass only documents and guards around it.

## Validation Commands

```bash
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_check_investigate_entries.py -k entry_validator_floor -q || { echo FAIL: guard pins; exit 1; }
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_check_investigate_entries.py -q || { echo FAIL: validator suite; exit 1; }
grep -q "single-line disposition" scripts/check_investigate_entries.py || { echo FAIL: disposition constraint note; exit 1; }
grep -q "CITATION_TAIL_CHARS" scripts/check_investigate_entries.py && grep -q "legitimate trailing" scripts/check_investigate_entries.py || { echo FAIL: tail-strip note; exit 1; }
grep -q "docstring owns" agents/skills/investigate/SKILL.md || { echo FAIL: skill pointer; exit 1; }
bash scripts/check-no-em-dash.sh file scripts/check_investigate_entries.py agents/skills/investigate/SKILL.md docs/history/plans/2026-10-01-entry-validator-floor-followups.md || { echo FAIL: em-dash; exit 1; }
```

### Task 1: subdirectory refusal

Files:
- `scripts/check_investigate_entries.py`
- *(new)* `scripts/test_check_investigate_entries.py`

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_check_investigate_entries.py -k entry_validator_floor -q`; covers the guard pins

- [x] Run → expect RED: `grep -c "outside the repository root" scripts/check_investigate_entries.py` prints 0 (grep exits 1) [class: REPOSITORY_TEST]
- [x] Implement the cwd guard in `main`: resolve `git rev-parse --show-toplevel` from the cwd and compare BOTH sides resolved (`Path.cwd()`/`os.getcwd()` physical path vs the toplevel, never a logical `$PWD` comparison - macOS `/tmp` to `/private/tmp` would false-refuse); when the toplevel fails to resolve or differs from the resolved cwd, print the named refusal (`entry validator: invoked outside the repository root; run from the repository root`) and exit 2 before any validation; add the guard pins, each named with the `entry_validator_floor` substring so the Evidence selector collects the family: `test_entry_validator_floor_refuses_subdirectory_invocation` (subprocess from a subdirectory: exit 2, named message) and `test_entry_validator_floor_repo_root_invocation_unchanged` (repo-root invocation with an explicit `--log` fixture behaves as today: a subdirectory run with the default log already exits 2 on the unreadable-log path, so the witness needs the explicit fixture to isolate the guard) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Evidence command [class: REPOSITORY_TEST]
- [x] Commit: `validator: refuse subdirectory invocation of the entry floor` [class: IMPLEMENTATION_REQUIRED]

### Task 2: docstring constraints and skill pointer

Files:
- `scripts/check_investigate_entries.py`
- `agents/skills/investigate/SKILL.md`

Evidence:
- the Validation Commands grep lines; covers both notes and the pointer

- [x] Add to the module docstring: the exit-code line names the new refusal surface (exit 2 also covers the outside-the-repository-root invocation); the single-line disposition framing for the already-stated per-line END-anchor requirement (each `- ` disposition line is checked separately; a multi-line disposition style with a mid-block citation is rejected) and, beside `CITATION_TAIL_CHARS`, the tail-strip trade note (the strip can remove a legitimate trailing character from an exotic filename; accepted) [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the Stage 4 structural-minimum sentence in `agents/skills/investigate/SKILL.md` with a pointer naming the validator docstring as the owning list for the marker semantics (file-precision floor included) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Validation Commands grep lines; full validator suite green [class: REPOSITORY_TEST]
- [x] Commit: `validator: document disposition and tail-strip constraints, point the skill at the docstring` [class: IMPLEMENTATION_REQUIRED]

### Task 3: full validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [x] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]
