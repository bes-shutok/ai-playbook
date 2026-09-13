# Plan: check_lesson_scope closeout (residual hardening + runtime deployment)

Backlog: `docs/history/backlog/2026-09-12-check-lesson-scope-residual-hardening.md` (8 findings from the r5 exit round, scope of record) plus `docs/history/backlog/2026-09-12-check-lesson-scope-runtime-deployment.md` (runtime symlink deployment, same validator surface; folded scope of record). No RFC/ticket.
Origin review: `docs/reviews/2026-09-12-2026-09-09-learn-company-scope-placement-code-review-r5.md` (pattern ids referenced in the backlog item).
Follow `projects/.ai-playbook/python_guidelines.md` for the validator script and its tests.

## Terms

- Project lessons corpus: the incident repo's `docs/maintenance/development_lessons.md` (or `PROJECT_CORPUS_REL` from `lessons_recall.py`); first CLI argument of the validator.
- Company guidelines master: cross-repo company guideline source of truth resolved from the `company_guidelines_master` facts key; second CLI argument of the validator.
- Cold start: the designed WARNING-on-stderr with exit 0 when either CLI file is missing (direct personal-repo runs); pre-resolving gate consumers (done 4a) must stop on any WARNING line.
- Zero-block WARNING: the WARNING emitted when an existing file parses to zero blocks; same consumer semantics as cold start.
- Witness-pointer floor: blocks under `MIN_RULE_WORDS` (25) normalized words are skipped as presumed witness pointers and never match.
- Block model: `parse_blocks` splits a file into heading-delimited blocks; content before the first heading (preamble) is excluded from comparison; heading detection is fence-aware; a fence still open at EOF is exit 2.
- h3-split amendment: this plan's change of heading boundaries from `#{1,3}` to `#{1,2}`, making h3 and deeper headings body text; supersedes the h3-split pin (`test_h3_heading_splits_blocks`) from the predecessor plan.
- Skill-gate marker: consent marker the plans skill refreshes before every plan-file write, at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker` per `agents/hooks/skill-gate/README.md` (Marker WRITE RECIPE, plans class).
- Session key: the marker's session element, derived by running `python3 ~/.ai-playbook/scripts/session_channel.py` as a subprocess; empty after strip means the literal `no-session`, otherwise `sha1(value)[:16]` hex; `project` derives via the shared `facts_paths.resolve_project_key`.

## Assumptions

- assume the h3-split fix mechanism is the `#{1,2}` heading-boundary amendment, not merged-text comparison of consecutive blocks; basis: r5 finding F2 lists both as acceptable options, the amendment is a one-line regex change plus a superseded pin while windowed comparison adds a new matching algorithm to a 185-line validator, and the 2026-09-12 authoring probes confirm the amendment flips the reproduced evasion to exit 1 with no other suite regression (31 of 32 existing tests GREEN against a fixed copy; the only failure is the h3-split pin this plan deliberately supersedes).
- assume r5 finding F5 is resolved by deleting the unmeasurable runtime-expectation sentence from done 4a.1, not by wrapping the invocation in `timeout 120`; basis: the finding offers both and says "do not keep unmeasurable prose", and the `timeout` binary is absent on the primary macOS host (probed 2026-09-12: `command -v timeout` and `command -v gtimeout` both empty), so the wrap option adds a non-portable dependency to a cross-platform skill.
- assume r5 finding F6 is resolved by the minimal test pin (WARNING lines emitted in exactly the documented conditions and no others), not by a dedicated cold-start exit code; basis: the finding names the test pin as the minimal option, and a new exit code would ripple the USAGE string, README row, and done 4a.1 outcome semantics in the same change.
- assume tests run via `python3 -m unittest discover -s scripts -p 'test_check_lesson_scope.py'`; basis: predecessor plan convention (`2026-09-09-learn-company-scope-placement` Validation Commands) and the suite's own `unittest.main()` entry point.
- assume the deployment task targets the machine that runs plan execution; basis: the backlog item text "On each machine that runs `done` against a repo with a project lessons corpus, create the symlink" and the runtime registry model verified on disk 2026-09-12 (`~/.ai-playbook/scripts/` holds 23 per-file symlinks into this repo and the validator symlink is absent).

Decision points requiring a grill: M2 fix mechanism resolved to the `#{1,2}` amendment over merged-text comparison; source: r5 finding F2 options list plus 2026-09-12 authoring probes on a fixed copy; affects Task 2 and Terms. Finding 6 resolution resolved to sentence deletion over the `timeout 120` wrapper; source: r5 finding F5 options plus the absent `timeout` binary probed 2026-09-12; affects Task 4. Finding 7 resolution resolved to the WARNING test pin over a dedicated exit code; source: r5 finding F6 minimal option; affects Task 3. Deployment exception receipt resolved via the standing pre-authorization in the 2026-09-12 scheduled authoring prompt; source: task prompt text quoted in Task 5; affects Task 5.

## Gist & Examples

`scripts/check_lesson_scope.py` is the mechanical duplicate guard behind done's pre-commit lesson scope audit (Step 3 item 4a). The r5 exit review of the predecessor plan left eight valid non-blocking findings: two Medium behavior gaps in the validator, three unpinned fence and zero-block behaviors, two contract prose gaps (done 4a.1 runtime expectation, stderr WARNING semantics), and one incomplete README exit-code row. Separately, the validator was never deployed to the runtime scripts dir, so on this machine every done 4a audit takes the cold-start warning instead of running the guard.

**Before (today), zero-block evasion:** a corpus wiped to blank lines (`"\n   \n"`) parses to one empty block, because the headingless branch returns a single block whenever the file has any lines. The documented zero-block WARNING never fires; probed 2026-09-12: exit 0 with empty stderr. done's gate, which stops on any WARNING, treats the file as a clean pass.

**After (this plan):** a headingless file with no non-whitespace content parses to zero blocks, so `_load_blocks` emits the documented WARNING (`WARNING: existing file parses to zero blocks (empty or whitespace-only): <path>`) and done stops. Probed against a fixed copy: exit 0 with that WARNING line.

**Before (today), h3-split evasion:** a duplicated rule whose corpus copy carries an internal h3 subheading splits into fragments that individually miss the 25-word floor or the ratio gate. The r5 reviewer reproduced this live and this plan re-probed it: corpus `## A` + 29-word rule + `### Sub` + 27-word tail versus master `## B` + identical rule + tail exits 0; the identical content without the `###` line exits 1 with a DUPLICATE line.

**After (this plan):** heading boundaries are h1 and h2 only; h3 and deeper headings stay body text inside their block. The same repro exits 1 with `DUPLICATE:` (probed against a fixed copy). The supersession is documented in the validator docstring, and the old pin test flips to assert the new boundary. Real corpora are unaffected in practice: the project lessons corpus carries zero h3 headings today, and both sides of any real duplicate normalize the same way.

**Before (today), unpinned fence conjuncts:** the fence-closer conjuncts (same character; nothing but whitespace after the run) are mutation-removable: no test fails if a `~~~` line wrongly closes an open backtick fence, or if a fence-run line with trailing info text wrongly closes its fence.

**After (this plan):** two characterization tests pin both conjuncts. Each fixture still exits 1 on the correct parser and was probed to exit 2 (unclosed fence) under the corresponding single-conjunct mutant, so each test discriminates its mutation. A fourth pin asserts WARNING lines appear only in the documented conditions (missing file, zero blocks) and never on clean or duplicate runs; a fifth mirrors the zero-block WARNING to the master side.

**Before (today), deployment:** `~/.ai-playbook/scripts/check_lesson_scope.py` does not exist (probed 2026-09-12), so done 4a prints `lesson scope validator absent; mechanical duplicate check skipped (cold-start)` on every audit and the mechanical duplicate guard is inert.

**After (this plan):** a per-file symlink into the repo copy (the established registry model; all 23 sibling scripts are symlinks) makes the audit run the hardened validator. A fixture trio through the runtime path exits 0 (clean), 1 (duplicate), and 2 (usage), proving the deployed artifact resolves and behaves.

Docs edits close the prose gaps: the README Scripts row gains "or unclosed code fence" in the exit-2 parenthetical (matching the docstring and USAGE), and done 4a.1 loses the sentence promising an "unusually long run" tool-failure treatment that has no mechanism.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the two Medium probes flip exactly as recorded in Gist & Examples; the full validator suite is GREEN; the three unpinned tests kill their named mutations (mutant exits recorded at authoring: both fence-conjunct mutants exit 2).
- consistency: USAGE, docstring, README, and done 4a.1 state the same exit-code and WARNING contract after the edits; the docstring documents the h3-split amendment.
- deployment verifiability: the runtime path is a symlink (not a copy) resolving into the repo checkout, and the fixture trio through it exits 0/1/2.
- minimality: no new exit codes, no new CLI flags, no `timeout` dependency, no changes outside the four listed files plus the runtime symlink.

**Done when:**
- `python3 -m unittest discover -s scripts -p 'test_check_lesson_scope.py'` exits 0 with 38 tests (32 existing plus 6 new; the flipped pin is a rename, not a removal).
- The Validation Commands block exits 0 end to end on the machine running execution.
- `README.md` Scripts row for the validator contains "2 usage/IO error or unclosed code fence".
- `agents/skills/done/SKILL.md` no longer contains the "unusually long run" sentence.
- `~/.ai-playbook/scripts/check_lesson_scope.py` is a symlink resolving into this repo and the runtime fixture trio exits 0/1/2.

**Ship when:**
- Every other machine that runs `done` against corpora-bearing repos gets the same per-file symlink (per-machine, human-paced work outside any single plan execution).
- The symlink is re-checked after any registry re-sync that rebuilds `~/.ai-playbook/scripts/` (recurring machine-local condition).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/check_lesson_scope.py` (heading regex, blank-headingless branch, docstring)
- `~/.ai-playbook/scripts/check_lesson_scope.py` *(machine-local runtime symlink created by Task 5; repo-untracked, so findings are limited to symlink semantics: it must stay a symlink into the repo copy, never a second file)*
- `README.md` (Scripts row for check_lesson_scope only; all other rows frozen)
- `agents/skills/done/SKILL.md` (Step 3 item 4a.1 sentence deletion only; all other steps frozen)

**Tests:**
- `scripts/test_check_lesson_scope.py` (new tests plus the flipped h3 pin)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; its `#{1,3}` is an unrelated Markdown section-split regex with different semantics, not a block-boundary pin.
- `docs/plans/completed/2026-09-09-learn-company-scope-placement.md`; archived plan, body immutable; the amendment note lives in the validator docstring instead.
- `docs/reviews/2026-09-12-2026-09-09-learn-company-scope-placement-code-review-r5.md`; review history, read-only origin of the findings.
- `~/.ai-playbook/scripts/` runtime directory contents other than the one symlink Task 5 creates; machine-local deployment target, not repo content.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)" || { echo "not inside a git repo" >&2; exit 1; }
cd "$REPO" || exit 1
fail() { echo "FAIL: $1" >&2; exit 1; }
expect_line() { grep -qF "$1" "$2" || fail "missing obligation in $2: $1"; }
expect_absent() {
  local pat="$1"; shift
  local rc=0
  grep -qF "$pat" "$@" || rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden pattern present: $pat"; fi
  if [ "$rc" -ge 2 ]; then fail "grep tool error rc=$rc for: $pat"; fi
  return 0
}

# 1. Validator suite (the canonical executable artifact behind the done scope audit)
python3 -m unittest discover -s scripts -p 'test_check_lesson_scope.py' || fail "validator unit tests"

# 2. README exit-2 contract (r5 finding 8)
expect_line "2 usage/IO error or unclosed code fence" README.md

# 3. done 4a.1 unmeasurable-runtime sentence deleted (r5 finding 6; fires until Task 4 lands)
expect_absent "an unusually long run signals a degenerate" agents/skills/done/SKILL.md

# 4. h3-split amendment documented in the validator docstring (r5 finding 2 mechanism)
expect_line "h3 and deeper headings are body text" scripts/check_lesson_scope.py

# 5. Runtime deployment through the symlink (backlog item 2, machine running this validation)
SC="$HOME/.ai-playbook/scripts/check_lesson_scope.py"
test -L "$SC" || fail "runtime validator is not a symlink: $SC"
test -e "$SC" || fail "runtime validator symlink does not resolve: $SC"
case "$(readlink "$SC")" in */scripts/check_lesson_scope.py) ;; *) fail "symlink target is not the repo copy: $(readlink "$SC")";; esac
TMPD="$(mktemp -d)" || fail "mktemp"
trap 'rm -rf "$TMPD"' EXIT
RULE="When a configuration rollout expands the pull request scope beyond its original title, update the title before merging so reviewers can rely on the title as the scope of record for later audits and incident tracing."
RULE_B="Before renaming a shared database column, grep every repository that consumes the schema and file the migration plan with each consuming team, because silent consumers break at runtime long after the rename lands."
printf '# P\n\n## 12. Rollout titles\n\n%s\n' "$RULE" > "$TMPD/corpus.md"
printf '# M\n\n## 51. Column renames\n\n%s\n' "$RULE_B" > "$TMPD/master.md"
printf '# M\n\n## 51. Keep titles\n\n%s\n' "$RULE" > "$TMPD/other.md"
python3 "$SC" "$TMPD/corpus.md" "$TMPD/master.md" >/dev/null 2>"$TMPD/err0"
[ "$?" -eq 0 ] || fail "runtime clean run did not exit 0"
if [ -s "$TMPD/err0" ]; then fail "runtime clean run emitted stderr"; fi
python3 "$SC" "$TMPD/corpus.md" "$TMPD/other.md" >/dev/null 2>&1
[ "$?" -eq 1 ] || fail "runtime duplicate run did not exit 1"
python3 "$SC" >/dev/null 2>&1
[ "$?" -eq 2 ] || fail "runtime usage run did not exit 2"
echo "validation: all checks passed"
```

### Task 1: RED tests for the two Medium evasion gaps

Files:
- `scripts/test_check_lesson_scope.py`

- [x] Add module constant `TAIL` with the exact probed text: `"This witness tail documents where the rule was first applied and why the audit trail keeps the rollout title as the scope of record for every later incident trace."`
- [x] Add `CheckLessonScopeTest#test_whitespace_only_corpus_warns`; given a corpus file whose full content is `"\n   \n"` and a normal master, expects exit 0, `WARNING:` on stderr, and the corpus path named in stderr (same contract as `test_zero_block_corpus_warns`).
- [x] Add `CheckLessonScopeTest#test_h3_split_duplicate_evasion_closed` with the exact probed construction (probed 2026-09-12: exit 0 today, exit 1 after Task 2):
- [x] corpus body built as `self._write(self.corpus, self._corpus_with("12. Rollout title rule", f"{RULE_A}\n\n### Subsection\n\n{TAIL}"))`
- [x] master body built as `self._write(self.master, self._master_with("51. Rollout title rule", f"{RULE_A}\n\n{TAIL}"))`
- [x] expects exit 1 with `DUPLICATE:` on stdout (the h3 must not split the corpus rule into fragments that miss the gate).
- [x] Run `python3 -m unittest discover -s scripts -p 'test_check_lesson_scope.py'`; expect exactly the two new tests RED (probed 2026-09-12: the whitespace corpus run exits 0 with empty stderr, and the h3 repro exits 0 with no DUPLICATE line) and all 32 existing tests GREEN. Commit deviation note (execution 2026-09-13): the runtime driver's done handoff requires a per-task commit_identity, so the RED tests were committed alone as e15a324 instead of riding Task 2's commit; the suite at e15a324 is intentionally RED (2 failing) and GREEN from 86e2101 onward.

### Task 2: GREEN: `#{1,2}` boundaries and the blank-headingless zero-block branch

Files:
- `scripts/check_lesson_scope.py`
- `scripts/test_check_lesson_scope.py`

- [x] Change `_HEADING_RE` to `re.compile(r"^#{1,2} ")`.
- [x] Change the headingless branch of `parse_blocks` to `return [_make_block(lines, 1)] if "".join(lines).strip() else []` so an all-blank headingless file parses to zero blocks.
- [x] Extend the module docstring's block model note with the exact sentences: `Heading boundaries are h1 and h2; h3 and deeper headings are body text inside their block (amendment superseding the earlier h3-split behavior, which let internal h3 subheadings split a duplicated rule into fragments that individually miss the ratio gate).` and `A headingless file with no non-whitespace content parses to zero blocks.`
- [x] Flip the pin: rename `test_h3_heading_splits_blocks` to `test_h3_heading_does_not_split_blocks`; given `parse_blocks("# Top\nintro\n\n### Sub\nbody\n")`, expects a single block whose line is `1` (the h3 stays body text).
- [x] Run the suite; expect all 34 tests GREEN.
- [x] Commit: `validator: close zero-block and h3-split evasion gaps (r5 findings 1-2)`

### Task 3: characterization pins for the fence conjuncts and the WARNING contract

Files:
- `scripts/test_check_lesson_scope.py`

- [x] Add module constants with the exact probed fixture bodies (the triple-backtick runs sit mid-line inside the strings):
- [x] `FENCE_TILDE_BODY = f"{RULE_A}\n\n` + three-backtick-open + `bash` + newline + `~~~` + newline + `printf titles` + newline + three-backtick-close + `\n"` (probed verbatim 2026-09-12)
- [x] `FENCE_TRAILING_BODY = f"{RULE_A}\n\n` + three-backtick-open + `text` + newline + three-backtick-open + `bash extra` + newline + `### fake heading` + newline + three-backtick-close + `\n"` (probed verbatim 2026-09-12)
- [x] Add `CheckLessonScopeTest#test_tilde_line_does_not_close_backtick_fence`; given corpus and master blocks whose shared body is `FENCE_TILDE_BODY` under `12. Rule` / `51. Rule` headings, expects exit 1 with `DUPLICATE:` on stdout and empty stderr (pins the same-character closer conjunct; probed 2026-09-12 to exit 2 under a mutant that drops the conjunct).
- [x] Add `CheckLessonScopeTest#test_fence_line_with_trailing_text_does_not_close`; given corpus and master blocks whose shared body is `FENCE_TRAILING_BODY` under `12. Rule` / `51. Rule` headings, expects exit 1 with `DUPLICATE:` on stdout and empty stderr (pins the no-trailing-content conjunct; probed 2026-09-12 to exit 2 under a mutant that drops the conjunct).
- [x] Add `CheckLessonScopeTest#test_zero_block_master_warns`; given an empty master file and a normal corpus, expects exit 0, `WARNING:` on stderr, and the master path named in stderr (mirror of `test_zero_block_corpus_warns`).
- [x] Add `CheckLessonScopeTest#test_warning_lines_only_in_documented_conditions`; given (a) the divergent-body clean pair from `test_divergent_rule_bodies_clean` and (b) the verbatim `RULE_A` duplicate pair, expects exit 0 and exit 1 respectively with completely empty stderr in both runs (WARNING is emitted only for a missing file or a zero-block file, never on clean or duplicate outcomes).
- [x] Run the suite; expect all 38 tests GREEN immediately (these are characterization pins, verified GREEN on today's tree at authoring; their value is mutation kill, with both mutant exits recorded in the Gist).
- [x] Commit: `tests: pin fence-closer conjuncts and the WARNING emission contract (r5 findings 3-5, 7)`

### Task 4: docs: README exit-2 row and done 4a.1 sentence deletion

Files:
- `README.md`
- `agents/skills/done/SKILL.md`

- [x] In the `scripts/check_lesson_scope.py` row of the README Scripts table, change the parenthetical `(exit 0 clean/cold start, 1 duplicate, 2 usage/IO error)` to `(exit 0 clean/cold start, 1 duplicate, 2 usage/IO error or unclosed code fence)`.
- [x] In done Step 3 item 4a.1, delete exactly the sentence `The validator is sized for prose corpora; an unusually long run signals a degenerate (for example fence-damaged or headingless) corpus and is treated as a tool failure per the sentence above.` (the surrounding Outcome semantics sentences stay untouched).
- [x] Run Validation Commands checks 2 and 3; expect both to pass (check 3 is RED-today and flips with this task).
- [x] Commit: `docs: align README exit-2 row and done audit prose with validator contract (r5 findings 6, 8)`

### Task 5: runtime deployment of the validator symlink

Files:
- `~/.ai-playbook/scripts/check_lesson_scope.py` *(machine-local runtime symlink; no repo-tracked file changes, so this task ends without a commit)*

- [x] Create the idempotent per-file symlink, keeping symlink semantics (never a second copy): `ln -sfn "$(git rev-parse --show-toplevel)/scripts/check_lesson_scope.py" "$HOME/.ai-playbook/scripts/check_lesson_scope.py"`
- [x] exception confirmed by user: "Standing pre-authorization: accept all recommended options and suggestions throughout without asking me." (2026-09-12 scheduled authoring prompt, automation-c1c77b40); item: create the runtime validator symlink; target/environment: `~/.ai-playbook/scripts/` on the machine running execution; confirmation time/session: 2026-09-12, authoring session for this plan; why executable now: the repo copy exists at `scripts/check_lesson_scope.py`, the runtime dir exists on this machine with the all-symlink registry model (23 sibling symlinks verified 2026-09-12), and the consumer (done 4a) runs on this machine; completion evidence: `test -L` plus the fixture trio through the runtime path exiting 0/1/2, both in this task's checklist and in Validation Commands check 5.
- [x] Verify with `test -L` and `readlink` that the path is a symlink resolving into the repo checkout (Validation Commands check 5 does this fail-closed).
- [x] Run the full Validation Commands block; expect exit 0 end to end including the runtime fixture trio.
