# Plan: Plan-review gate hook selects the review round by round number

Backlog origin: docs/history/backlog/2026-11-05-plan-review-gate-hook-round-tie-picks-stale-verdict.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-20-plan-review-plan-review-gate-hook-round-tie-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically).
Execution budget: 2h total, largest task 1h
Executed: yes (5f9941592ac609f162a7982868e6e3098d817bdf)
Authoring claim: 2026-11-05-plan-review-gate-hook-round-tie-picks-stale-verdict.md (session 883322f3-c823-4664-87ca-27d5422722a3)

## Terms

- review gate hook: the Claude `PreToolUse` Bash hook `check-plan-review-gate.sh` that refuses a `git commit` staging a plan file when the newest matching review round records a No-Go verdict.
- round: one canonical plan-review artifact `<YYYY-MM-DD>-plan-review-<slug>[-p<8 hex>]-r<N>.md` under a `reviews/` directory, where `<slug>` is the plan's feature slug, optionally preceded by one date or story key that the review name kept; `<N>` (digits directly before `.md`) is its round number.
- canonical: a name that matches the round shape above exactly (case-insensitive slug equality, so a longer slug that extends the plan's slug is another plan). Names carrying `-exec-`, `-code-review`, or a suffix after `-r<N>` (such as `.wt-1`, `.backup-<ts>`, `-reconciliation`) are not canonical.
- no-artifact warning: the stderr notice the hook already prints when no matching review artifact exists, after which it exits 0 and the commit proceeds.
- tie: two candidates whose modification times are equal, so the shell `-nt` test is false in both directions.
- runtime hooks directory: `~/.claude/hooks/`, where the live hook file sits today as an ordinary file.

## Why

The review gate hook picks the "newest" round by modification time only, so when an old No-Go round and the latest ready round share one mtime, listing order decides and a ready plan commit is refused. The same rule also lets a newer code-review or exec round decide a plan commit; the fix limits the choice to the plan's own canonical plan-review rounds. The hook also has no versioned copy or test in this repository, so the defect cannot be fixed reviewably today.

## Gist & Examples

TLDR: the review gate hook moves into `agents/hooks/plan-review-gate/` and judges the highest canonical round number for the plan instead of the newest mtime, fixing a false block (code-quality).

Before: `x-r13.md` (No-Go) and `x-r14.md` (`ready=yes`) written in the same second; the commit is blocked or allowed depending on `find` listing order.
After: round 14 is always judged, whatever the mtimes; `x-r10.md` outranks `x-r9.md`; a higher code-review or exec round never decides; a plan with no canonical round gets the existing no-artifact warning and is allowed.

## Outcome

Aim: a ready plan commit is never blocked by a superseded No-Go round, and the hook is versioned and tested like its sibling hooks.

- A same-second tie no longer changes which round is judged.
- Round 10 outranks round 9 (numeric, not lexical).
- A code-review or exec No-Go round no longer blocks a plan commit.
- The hook has a repository copy and a regression test; once the operator installs it, a tied commit no longer needs the touch-the-file workaround.

Gate delta: none added (no refusal, gate, fence, schema field, or pause condition is added; the mtime-only selection rule is replaced by a canonical-round-number rule and the exact verdict grep stays unchanged; one refusal case is removed: a commit is no longer blocked by a code-review or exec No-Go round that is not a plan-review round; one is exposed: a plan-review No-Go round that a newer non-plan-review file used to hide now blocks, which is the intended authority).

Follow-up disposition: the backlog item's adjacent concern (a ready round whose prose merely mentions `No-Go` is blocked by the whole-file grep) has no witness and stays recorded in the origin item. A second accepted limit: a plan re-authored under the same slug with a new `-p<8 hex>` token restarts at round 1, so an older token's higher round can outrank it; a corpus probe found 39 of 1141 plan-review slugs mixing tokens. It is promoted to a backlog origin only if a masked No-Go is witnessed, and is not widened here.

## Assumptions

- The live hook at `~/.claude/hooks/check-plan-review-gate.sh` is the only copy and its body matches the origin item's description (basis: read directly on 2026-11-20; the selection loop uses `-nt` and keeps the first candidate on a tie).
- Canonical match: the basename matches `^[0-9]{4}-[0-9]{2}-[0-9]{2}-plan-review-([0-9]{4}-[0-9]{2}-[0-9]{2}-|[a-z]+-[0-9]+-)?<regex-escaped slug>(-p[0-9a-f]{8})?-r[0-9]+\.md$` case-insensitively, where the slug is the one the hook already derives from the plan stem; the optional prefix group covers the date or story key the hook strips but the review name keeps (basis: every canonical plan-review name in the corpus starts with a date; a corpus probe found 56 files in 24 series that keep a date and 26 files that keep a story key in the slug; one execute-plan-review code-review name contains `plan-review-` mid-name).
- Selection key: among canonical candidates judge the highest `<N>`; equal `<N>` (possible only across different tokens) goes to the newest mtime, then the lexicographically greatest basename. Non-canonical names are ignored. When no canonical candidate exists the hook emits its existing no-artifact warning and allows, so a stale code-review, exec, or authoring No-Go no longer blocks a plan commit (basis: a corpus probe of `.ai-playbook/reviews/` on 2026-11-20 found 5 plan slugs with only non-plan-review rounds and 45 slugs whose highest round is in a non-plan-review series).
- Sibling hooks are versioned under `agents/hooks/<name>/` and symlinked into `~/.claude/hooks/` (basis: `lessons-recall.sh` and `skill-gate.sh` are symlinks into this repository).
- Replacing the live file with a symlink edits user-level configuration, so it is an operator step under Ship when, not a task.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the judged round is the highest canonical round number for the plan regardless of mtime; mtime only breaks equal round numbers.
- Behavior preservation: commits with no staged plan, no matching review, or a ready latest round behave exactly as before.

**Done when:**
- The versioned script judges the highest canonical round number and every Task 1 witness passes.
- A README beside the script records install steps and the three skill-gate README prose mentions that name the hook carry the versioned path.

**Ship when:**
- The operator replaces `~/.claude/hooks/check-plan-review-gate.sh` with a symlink to the versioned script and keeps its settings entry unchanged [class: OPERATIONS_FOLLOW_UP]; evidence owner: the operator; closed when `ls -l` shows the symlink to the versioned script and a commit staging a plan with tied rounds is allowed without touching a review file.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/hooks/plan-review-gate/check-plan-review-gate.sh` (Task 1) *(new)*
- `agents/hooks/plan-review-gate/README.md` (Task 2) *(new)*
- `agents/hooks/skill-gate/README.md` (Task 2)

**Tests:**
- `scripts/test_plan_review_gate_hook.py` (Task 1) *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `~/.claude/settings.json` and the live hook file; user-level configuration owned by the operator.
- The verdict grep (`No-Go|ready=no|Ready for execution: No`); unwitnessed, kept as is.

## Validation Commands

```bash
python3 -m pytest scripts/test_plan_review_gate_hook.py -q
```

### Task 1: Versioned hook with round-number selection

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/hooks/plan-review-gate/check-plan-review-gate.sh` *(new)*
- `scripts/test_plan_review_gate_hook.py` *(new)*

Primary class anchors:
- `newest_review` in `agents/hooks/plan-review-gate/check-plan-review-gate.sh`

- [x] Copy the live hook body into the new file unchanged, then make the selection a function `newest_review` [class: IMPLEMENTATION_REQUIRED]
- [x] Test harness: each case runs the versioned script in a throwaway git repo with `HOME` and `GIT_CONFIG_GLOBAL` pointed at a temp dir, sets every fixture mtime explicitly with `os.utime(ns=...)` (equal means the same ns value, unequal means at least 2 seconds apart so second-granularity `-nt` still orders them), runs each case with the candidate listing in both orders (a stub `find` first on `PATH`), and asserts the exit code plus the stderr verdict text [class: REPOSITORY_TEST]
- [x] `newest_review` delivers highest-round selection: given round 13 (No-Go) and round 14 (`ready=yes`) of one plan with identical mtimes, expects the commit is allowed in both listing orders [class: REPOSITORY_TEST]
- [x] Reverse witness: given round 13 (ready) and round 14 (No-Go) with identical mtimes, expects the commit is blocked in both listing orders; given round 14 (No-Go) with an older mtime than round 13 (ready), expects blocked [class: REPOSITORY_TEST]
- [x] Numeric witness: given round 9 (No-Go, newest mtime) and round 10 (ready, older mtime), expects allowed; given round 10 (No-Go, older mtime) and round 9 (ready, newer mtime), expects blocked [class: REPOSITORY_TEST]
- [x] Same-number witness: given two canonical rounds numbered 5 with different tokens, one ready and one No-Go, identical mtimes, and the No-Go basename sorting last, expects blocked with stderr naming that basename in both listing orders; with the ready basename sorting last, expects allowed [class: REPOSITORY_TEST]
- [x] Non-plan-review witness: given plan-review round 3 (ready) beside code-review round 6 and exec round 7 (both No-Go, both strictly newer mtimes than round 3), expects allowed; given plan-review round 2 (No-Go) beside a newer ready exec round, expects blocked [class: REPOSITORY_TEST]
- [x] Slug witness: given plan `foo` with its own round 1 (ready) beside a `foo-bar` plan-review round 9 (No-Go, newer mtime), expects allowed; given a code-review name that merely contains `plan-review-foo` mid-name (No-Go, newer mtime), expects allowed [class: REPOSITORY_TEST]
- [x] Prefix witness: given plan `<date>-p65-x` with review `plan-review-<date>-p65-x-r2` (No-Go) and plan `RCD-9-x` with review `plan-review-rcd-9-x-r1` (No-Go), expects blocked for each [class: REPOSITORY_TEST]
- [x] Variant witness: given round 3 (ready) and `-r2.backup-<ts>` (No-Go, newer mtime) and `-r3.wt-1` (No-Go), expects allowed [class: REPOSITORY_TEST]
- [x] No-artifact witness: given only a code-review No-Go and no plan-review file for the plan, expects exit 0 with the existing no-artifact warning; given only non-canonical plan-review variants, expects the same [class: REPOSITORY_TEST]
- [x] Preservation witness: given a commit with no staged plan, no matching review, or a `git -C` target in another repo whose No-Go review must not apply, expects exit 0 as today [class: REPOSITORY_TEST]
- [x] Run → expect RED against the copied body (at least one listing order fails each tie, numeric, and non-plan-review witness), then write the round-number selection, then run → expect GREEN [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `fix: judge the highest review round in the plan-review gate hook` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Install notes and cross-reference

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- `agents/hooks/plan-review-gate/README.md` *(new)*
- `agents/hooks/skill-gate/README.md`

Primary class anchors:
- `plan-review-gate` in `agents/hooks/plan-review-gate/README.md`

- [x] README states purpose, the highest-canonical-round rule with the equal-number tie-break, the no-artifact allow, the accepted re-authored-token limit, and the symlink install command [class: IMPLEMENTATION_REQUIRED]
- [x] In the skill-gate README, append "(versioned at `agents/hooks/plan-review-gate/check-plan-review-gate.sh`)" after the hook filename in the "only wired precedent" parenthetical, the "MUST be preserved" Bash entry sentence, and the Doctor no-regression check (roughly lines 55, 266, 410); the settings `command` path line stays unchanged; comment mentions in the skill-gate adapter and core scripts are left as is [class: IMPLEMENTATION_REQUIRED]
- [x] Run the hygiene scan and the em-dash check over the changed files, expect exit 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs: version the plan-review gate hook beside its siblings` [class: IMPLEMENTATION_REQUIRED]

## Origin dispositions

- `2026-11-05-plan-review-gate-hook-round-tie-picks-stale-verdict`: closed by Tasks 1 and 2 (versioned hook judging the highest canonical round, regression test, README and cross-references).
- Operator step still open (Ship when): replace `~/.claude/hooks/check-plan-review-gate.sh` with a symlink to the versioned script; install command in `agents/hooks/plan-review-gate/README.md`.
