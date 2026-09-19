# Plan: learn and done workflow updates

Backlog origins (scope of record; the items stay in place under the backlog home while this plan is open):

- `docs/history/backlog/2026-09-16-learn-skill-usage-issue-backlog-capture.md`
- `docs/history/backlog/2026-09-16-done-lock-one-shot-shell-handoff.md`
- `docs/history/backlog/2026-09-15-drift-witness-docs-branch-sync-fallback.md`

## Terms

- Skills repo: the single repository that hosts the skills corpus and the skills backlog (facts key `skills_repo_path`; this playbook repo when work runs here).
- Backlog home: the skills repo's resolved backlog directory (`backlog_dir` from the skills repo's `.ai-playbook/facts.md` TOML; fallback `docs/history/backlog/`). Tracked in the skills repo, unlike the gitignored `docs/tmp` scratch.
- Blanket add: staging a whole tree with one command (for example `git add agents/skills/`) instead of explicit paths.
- One-shot shell: an agent shell tool mode where every command runs in a fresh shell process that exits when the command ends; environment variables do not survive between calls.
- Done lock: the per-repo exclusive lock from `scripts/done-lock.sh` acquired in done Step 0 and released in Step 6 with a token-fenced release.
- Drift witness: the `lesson-scope-audit:` line emitted by the done Step 3 item 4a audit when the company-master duplicate check could not run.

## Assumptions

- assume the docs-branch side implements the witness fallback (the alternative was annotating the already-closed origin item); basis: the origin item's suggested fix lists implementation first and the user's standing pre-authorization accepts the recommended option.
- assume the witness body line matches the Step 3 corpus-commit body line byte-for-byte; basis: the origin item's open-decisions rationale (one audit-note grep pattern for both carriers).
- assume the legacy commit helper (`commit-skills.sh`, deployed outside this repository and not tracked here) dies from the commit path by removing done's invocation; basis: the origin item offers "dies or is scoped", and the repo-tracked fix is the done Step 4 rewrite.
- assume the witness line travels as an explicit caller argument to the docs-branch append, not via a file or environment protocol; basis: done executes docs-branch as a skill in the same session, environment does not survive separate shell calls (origin 2's own lesson), and the docs-branch skill already passes arguments to helper scripts the same way.
- assume `Priority: high` is the backlog corpus's top priority value routed to the maintenance loop's authoring lane; basis: 16+ open items carry it and maintenance D2 authors for the highest-priority plan-uncovered open item; `high` is the highest ranked value in active use (one open item carries an unranked legacy numeric value that D2's ordering does not treat as higher).
- assume learn's skills-repo commits use the placement of the existing skill-placement commit workflow (learn already prescribes committing skill changes in the skills repository in its placement steps); this plan introduces no new branching policy.

Decision points requiring a grill: docs-branch fallback side (implement the body line vs annotate the closed item): resolved by the origin item's fix preference order plus the user's standing pre-authorization, 2026-09-16, affecting Gist and Task 6; witness line format: byte-for-byte match with the Step 3 body line, resolved by the origin item's open-decisions rationale plus standing pre-authorization, 2026-09-16, affecting Task 6.

## Gist & Examples

### Origin 1: learn captures skill-usage issues and owns its skills-repo commits

**Before (today):** a session hits a gate failure rooted in a skill bug, an ambiguous skill instruction, or a missing runtime deployment. The only durable record is whatever the agent improvises: a lesson (wrong artifact: lessons record principles, not fix-tracked work) or a chat line that dies with the session. The maintenance loop never sees the defect, so the fix waits for a human to re-notice and re-file. Witnesses that each needed manual capture: the dead quota-window probe, done-lock recovery incidents, the plan-readiness deployment-gap signature. Meanwhile the only commit path for learn-authored skills-repo changes is done Step 4's helper script, which stages the entire `agents/skills/` tree with a blanket add (sweeping unrelated peer edits) and never sees files outside that tree (a backlog file is invisible to it).

**After (this plan):** learn gains Step 1.8. While classifying session findings it also identifies skill-usage issues and classifies each as a skills-corpus defect only when the fault traces to a skill's instructions, a bundled script, a gate validator, or a missing or wrong runtime deployment. For each issue family it writes one scrubbed backlog file into the skills repo's resolved backlog home (`YYYY-MM-DD-<slug>.md`, `Status: open`, `Priority: high`), folding duplicates into an existing open item as added witnesses, and then commits its own learn-authored skills-repo artifacts (the backlog file plus any skill-file edits from lessons) by explicit path with a descriptive message. Done Step 4 narrows to an ask-first fallback that stages only session-attributed non-learn paths by explicit path.

**Example:** a done run's Step 0 lock is released early by a prescribed trap in a one-shot shell. With this plan, learn (invoked by that same done run's Step 1) captures the lock defect as `docs/history/backlog/2026-09-16-done-lock-one-shot-shell-handoff.md` in the skills repo, scrubs reproduction output, commits it by explicit path, and the maintenance loop's next survey authors a fix plan for it. A session with no skill issues creates nothing and reports nothing.

**Failure semantics:** creation, scrubbing, or the commit failing must not block learn or the enclosing done run; learn reports the failure plus a one-line issue summary (done carries it into its Step 7 outcome report). There is no lock on the skills repo today, so the blast radius stays small: only learn's own paths are staged, with one retry on git index contention before reporting.

**Integration notes:** receiving-review's Backlog capture keeps owning the review-findings path (a disjoint source); the maintenance loop's D2 consumes the `Priority: high` marking; the done Step 2.645 inbox gate is unaffected because the file lands inside the resolved backlog home. A skill issue may also yield a lesson when it generalizes; the backlog item is the fix-tracking artifact, not a lesson replacement. Standalone learn runs become self-contained (no dangling uncommitted artifacts awaiting a later done).

### Origin 2: done-lock acquisition across one-shot shell calls

**Before (today):** done Step 0 prescribes an `EXIT` trap installed in the shell that acquires the lock. In a one-shot shell, that shell exits immediately after the acquire call, the trap fires, and the lock is released before learn, hygiene, or commit steps run. The workflow continues believing it holds a lock that is already gone; a peer can acquire the same repository lock with nothing visibly blocked. The witnessed run had to reacquire without the trap and keep the token in session context.

**After (this plan):** done Step 0 documents two explicit variants. Variant A (persistent controlling shell): install the trap after acquisition, as today. Variant B (one-shot shell calls): never install the exit trap in the acquiring call; retain `DONE_LOCK_DIR` and `DONE_LOCK_TOKEN` in session context from the acquire output, reach the Step 6 release on every exit path, and pin `DONE_LOCK_HOLDER_PID` to a long-lived process when one is identifiable so dead-holder recovery cannot reclaim the lock mid-run after the grace period. Interruption cleanup is documented for both variants. A new selftest fixture pins the protocol: an acquire in a subshell that exits (no trap, holder pinned) keeps the lock held, a second acquire is blocked, and a token-fenced release from a later process succeeds.

**Out of scope:** a session-mode flag in the lock helper (origin 2 candidate 3). The documented variants plus the harness fixture satisfy the origin's acceptance criteria; the helper itself needs no change.

### Origin 3: drift witness survives the gitignored-corpus path

**Before (today):** the done Step 3 item 4a audit carries its drift witness durably only in the Step 3 corpus-commit body, and Step 3 item 6 repeats that carrier. When the audited corpus is gitignored, Step 3 routes it to the docs branch only and no Step 3 commit exists, so the witness lands nowhere durable; a closed backlog item accordingly overstated its closure.

**After (this plan):** docs-branch gains a witness append step: an append-only empty commit on the docs branch whose message body carries the exact witness line, byte-for-byte identical to the Step 3 body line so one audit-note grep pattern covers both carriers. Done Step 3 items 4a and 6 invoke it on the gitignored path. Example: the audit reports `lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run` for a gitignored corpus; done then runs the docs-branch witness append with that line, and `git log refs/heads/docs --grep "lesson-scope-audit:"` finds it.

## Evaluation Criteria

**Quality dimensions:**

- correctness: every acceptance criterion from the three origin items maps to a named gate in Validation Commands (G1 through G10), and the whole block exits 0 on the implemented tree.
- consistency: no surface in the touched set still states the unqualified "learn never commits" contract or references the retired commit helper; the witness line format is byte-identical across both carriers.
- test coverage: `bash scripts/done-lock.sh selftest` exits 0 including the new one-shot handoff fixture.
- maintainability: the validation block is fail-closed (explicit abort on miss, forbidden match, and grep tool error) and every pinned span is quoted verbatim from a task's prescribed text.

**Done when:**

- The Validation Commands block, run from the repository root against the implemented tree, exits 0.
- learn Step 1.8 exists with the capture contract, dedupe rule, commit rule, and failure semantics; a session with no skill issues creates no files.
- done's frontmatter, Step 1, Step 4, and Rules state the split boundary; done Step 4 stages only session-attributed non-learn paths by explicit path after asking.
- done Step 0 documents both shell variants with interruption cleanup; the selftest one-shot handoff fixture passes.
- docs-branch owns the witness append; done Step 3 items 4a and 6 wire it on the gitignored path.

**Ship when:**

- Deployed runtime copies outside this repository re-sync (vendored-asset sync for other checkouts; same-machine runtime copies are symlinks and go live immediately).
- A live session that hits a real skill defect ends with a committed backlog item through the new Step 1.8 path (observed in the wild; human-owned evidence).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `agents/skills/learn/SKILL.md`
- `agents/skills/done/SKILL.md`
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/receiving-review/SKILL.md`
- `README.md`

**Tests:**

- `scripts/done-lock.sh` (selftest function only; the one-shot handoff fixture)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Partially-in-scope files:** in `scripts/done-lock.sh` only the `cmd_selftest` function (fixture addition) and the `DONE_LOCK_HOLDER_PID` line inside `usage()` may change; all acquisition, release, steal, and status logic is frozen. In `agents/skills/receiving-review/SKILL.md` only the Backlog capture section may gain the provider note; everything else is frozen.

**Out of scope; reject unless plan-related:**

- The deployed `commit-skills.sh` helper outside this repository; reason: untracked runtime file, retired from the commit path by the done Step 4 rewrite, not edited by this plan.
- The three origin backlog files under `docs/history/backlog/`; reason: scope of record, read-only inputs.
- `docs/plans/2026-09-16-review-records-contract.md` and `docs/plans/2026-09-17-backlog-long-tail-prose-predicates-small-mechanics.md`; reason: peer-session deliverables present on the shared checkout, foreign work.
- `scripts/done-lock.sh` release, steal, stale, and status logic; reason: frozen per the partially-in-scope note above.

## Documentation Impact Assessment

The workflow changes live in the owning skills (learn, done, docs-branch), which is their canonical home per the placement rules; the README catalog row update is covered by Task 3. No additional `docs/` document needs new content: the backlog items themselves document the defects, and the document registry gains rows only at the completion boundary, not as plan tasks.

## Validation Commands

Run from the repository root. The block is fail-closed: every gate aborts non-zero on a missed requirement, a forbidden match, or a grep tool error (rc 2 or higher). Forbidden-pattern gates quote the legacy sentences this plan removes; this plan file intentionally quotes those sentences in its task text and is NOT in any sweep path (the quoted strings here are the checker literals, not stale references).

```bash
#!/bin/bash
# Fail-closed validation for the learn/done workflow updates plan.
set -u
git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "VALIDATION FAIL: run from the repository root" >&2; exit 1; }
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }

expect_match() {
  # Fixed-string presence: rc 1 = absent (fail), rc >= 2 = tool error (fail).
  local pattern="$1"; shift
  local rc=0
  grep -qF -- "$pattern" "$@" || rc=$?
  if [ "$rc" -ge 2 ]; then fail "grep tool error (rc $rc) matching: $pattern"; fi
  if [ "$rc" -eq 1 ]; then fail "required text absent: $pattern"; fi
}

expect_no_match() {
  # Fixed-string absence: rc 0 = forbidden match (fail), rc >= 2 = tool error (fail).
  local pattern="$1"; shift
  local rc=0
  grep -qF -- "$pattern" "$@" || rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden text present: $pattern"; fi
  if [ "$rc" -ge 2 ]; then fail "grep tool error (rc $rc) sweeping: $pattern"; fi
}

# G1: learn capture step exists (dedicated pins, one obligation each).
expect_match "## Step 1.8: Skill-usage issue capture" agents/skills/learn/SKILL.md
expect_match "resolved backlog home" agents/skills/learn/SKILL.md
expect_match "append the new witness details there and re-affirm its priority" agents/skills/learn/SKILL.md
expect_match "never a directory-wide add" agents/skills/learn/SKILL.md
expect_match "must not block learn or an enclosing done run" agents/skills/learn/SKILL.md
expect_match "public hygiene scan and the em-dash scan over the drafted item" agents/skills/learn/SKILL.md

# G2: learn commit-boundary rewrite (new boundary present, legacy sentences gone).
expect_match "commits only its own learn-authored artifacts in the skills repository" agents/skills/learn/SKILL.md
expect_match "commits only its own learn-authored skills-repo artifacts" agents/skills/learn/SKILL.md
expect_no_match "committing is the" agents/skills/learn/SKILL.md
expect_no_match "it does not commit" agents/skills/learn/SKILL.md

# G3: done commit-boundary rewrite.
expect_match "owns all git commits except learn's own learn-authored skills-repo artifacts" agents/skills/done/SKILL.md
expect_match "non-learn fallback" agents/skills/done/SKILL.md
expect_match "Stage by explicit path only" agents/skills/done/SKILL.md
expect_no_match "commit-skills.sh" agents/skills/done/SKILL.md
expect_no_match "only skill that performs git commits" agents/skills/done/SKILL.md

# G4: catalog row and provider note.
expect_match "commits its own learn-authored skills-repo artifacts" README.md
expect_match "learn's skill-usage-issue capture" agents/skills/receiving-review/SKILL.md
expect_match "the two sources are disjoint and neither owns the other's path" agents/skills/receiving-review/SKILL.md

# G5: one-shot handoff harness (executable, not grep-only).
out="$(bash scripts/done-lock.sh selftest 2>&1)" || fail "done-lock selftest exited non-zero"
printf '%s\n' "$out" | grep -qF "selftest OK: one-shot handoff" || fail "one-shot handoff fixture missing or failing"
expect_match "one-shot shell callers" scripts/done-lock.sh

# G6: done Step 0 two-variant lock procedure (per-obligation pins).
expect_match "Variant A, persistent controlling shell" agents/skills/done/SKILL.md
expect_match "Variant B, one-shot shell calls" agents/skills/done/SKILL.md
expect_match "never install the exit trap in the acquiring call" agents/skills/done/SKILL.md
expect_match "the run must reach the Step 6 release on every exit path" agents/skills/done/SKILL.md
expect_match "pin DONE_LOCK_HOLDER_PID to a long-lived process" agents/skills/done/SKILL.md

# G7: docs-branch witness append mode.
expect_match "Lesson-Scope Drift Witness Append" agents/skills/docs-branch/SKILL.md
expect_match "--allow-empty" agents/skills/docs-branch/SKILL.md
expect_match "must start with lesson-scope-audit:" agents/skills/docs-branch/SKILL.md
expect_match "invoke this step's witness append" agents/skills/docs-branch/SKILL.md

# G8: done wiring of the witness append (both carrier surfaces).
expect_match "invoke the docs-branch skill's witness append" agents/skills/done/SKILL.md
expect_match "the witness append on the docs branch carries the line instead" agents/skills/done/SKILL.md
expect_match "the append failure is a manual follow-up reported in the Step 7 outcome report" agents/skills/done/SKILL.md

# G9: byte-for-byte witness format shared with the Step 3 body line.
expect_match "lesson-scope-audit: config drift:" agents/skills/docs-branch/SKILL.md

# G9c: byte-parity of the witness line across both carriers (full line, one gate per file).
expect_match "lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run" agents/skills/done/SKILL.md
expect_match "lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run" agents/skills/docs-branch/SKILL.md

# G9b: executable witness-append fixture (extract the prescribed function,
# run it in a throwaway repo, verify refusal of a wrong prefix and the
# greppability of a canonical line).
_wf="$(mktemp)"; _td="$(mktemp -d)" || fail "fixture setup failed"
awk '/^docs_branch_witness_append\(\) \{/{f=1} f{print} f&&/^\}$/{exit}' agents/skills/docs-branch/SKILL.md > "$_wf"
test -s "$_wf" || fail "witness append function not extractable from docs-branch SKILL"
(
  cd "$_td" || exit 1
  git init -q repo || exit 1
  cd repo || exit 1
  export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
  git commit -q --allow-empty -m init || exit 1
  _tree="$(git mktree </dev/null)" || exit 1
  _c="$(git commit-tree "$_tree" -m "docs: init")" || exit 1
  git update-ref refs/heads/docs "$_c" || exit 1
  source "$_wf" || exit 1
  if docs_branch_witness_append "bogus line"; then
    echo "VALIDATION FAIL: witness append accepted a wrong-prefix line" >&2
    exit 1
  fi
  docs_branch_witness_append "lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run" || exit 1
  test -n "$(git log refs/heads/docs --grep=lesson-scope-audit: --format=%H)" || exit 1
) || fail "executable witness-append fixture failed"
rm -f "$_wf"; rm -rf "$_td"

# G10: stale-reference sweep over the touched set (case-insensitive, regex;
# three-way rc split so a grep tool error aborts instead of passing).
_rc=0
grep -rniE "learn (never|does not) commit" agents/skills/learn/SKILL.md agents/skills/done/SKILL.md agents/skills/docs-branch/SKILL.md README.md || _rc=$?
if [ "$_rc" -eq 0 ]; then
  fail "stale learn-never-commits wording survives"
fi
if [ "$_rc" -ge 2 ]; then
  fail "grep tool error (rc $_rc) sweeping stale wording"
fi

echo "VALIDATION OK: all gates green"
```

### Task 1: learn Step 1.8, skill-usage issue capture, and the learn-side commit boundary

Files:
- `agents/skills/learn/SKILL.md`

- [x] Add a new section `## Step 1.8: Skill-usage issue capture` after Step 1.7 and before Step 2, with this contract:
  - While classifying session findings (Step 1), also identify skill-usage issues: gate failures rooted in skill or script bugs, wrong or ambiguous skill instructions, missing runtime deployments, trigger failures. Classify an issue as a skills-corpus defect only when the fault traces to a skill's instructions, a bundled script, a gate validator, or a missing or wrong runtime deployment; consumer-project code bugs are out of scope (they belong to the project's own workflow).
  - For each issue family (same root area, same skill and step), resolve the skills repo from `skills_repo_path` (user facts; runtime symlink equivalent) and its resolved backlog home (`backlog_dir` from the skills repo's `.ai-playbook/facts.md` TOML; fallback `docs/history/backlog/`).
  - Dedupe before create: survey open items (`Status: open`, top level of the backlog home, excluding the completed and deferred subdirectories) for an existing item on the same skill and step; when found, append the new witness details there and re-affirm its priority instead of creating a duplicate.
  - New files follow `YYYY-MM-DD-<slug>.md` with `Status: open` and `Priority: high` (the corpus's top priority value, which routes the maintenance loop's authoring lane). Required contents: which skill and step (file path plus step number), observed versus expected behavior, trimmed reproduction evidence with secrets, usernames, org domains, project names, and ticket prefixes scrubbed, environment context (runtime, date, vendored copy versus repo copy), and suspected root area. Follow receiving-review's "Backlog capture for valid findings not fixed in scope" for item shape and apply done Step 2.7's sensitive-data discipline and learn Step 1.7's proper-noun review to the drafted item text before writing it. Phrase everything in skill terms so the item reads correctly without knowing which project the session ran in.
  - Commit rule: stage and commit learn-authored skills-repo artifacts by explicit path (the backlog item files and skill-file edits from lessons) with a descriptive message; never a directory-wide add. Before committing, run the public hygiene scan and the em-dash scan over the drafted item text and the changed skill files; fix hits before staging, or report per the failure semantics below. Retry once when the commit fails because another process holds the git index lock file (retry after the lock clears; delete nothing) before reporting.
  - Failure semantics: capture and the commit must not block learn or an enclosing done run; on failure, report the failure plus a one-line issue summary in the learn output (an enclosing done carries it into its Step 7 outcome report) as a manual follow-up.
  - A skill issue may also yield a lesson when it generalizes; the backlog item is the fix-tracking artifact, not a lesson replacement. A session with no skill issues creates no backlog items and reports nothing new.
- [x] Replace the learn "When to Use" closing sentence ("Do not commit changes; committing is the `done` skill's responsibility.") with: "Commit boundary: `learn` commits only its own learn-authored artifacts in the skills repository (Step 1.8 and the skill-placement commit workflow); the `done` skill owns every other commit, including the whole project repository."
- [x] Replace the learn Step 6.6 "Commit ownership" sentence ("`learn` writes the corpus; it does not commit.") with: "`learn` writes the corpora and commits only its own learn-authored skills-repo artifacts (Step 1.8; the skill-placement commit workflow); the project lessons corpus itself is committed by `done` Step 3 item 4b when it is not gitignored; do not treat orphan `docs` sync as a substitute for that commit."
- [x] Align the two existing skills-repo commit mentions (Step 4's "when changing the learn workflow itself" bullet and Step 5's "Commit workflow" paragraph) with the standing boundary: commit by explicit path, never a directory-wide add.
- [x] Add Completion Checklist entries: Step 1.8 ran (items created, folded, or none needed); every backlog item text passed the scrub review before writing; learn-authored skills-repo artifacts were committed by explicit path, or the failure was reported with a one-line issue summary.
- [x] Add Integration Points entries: with `done` (done Step 1 invokes learn; learn's skills-repo commit lands during that step; done Step 4 keeps only the non-learn fallback) and with `receiving-review` (shape provider for backlog items; disjoint sources). The maintenance loop consumes backlog items generically through D2 and needs no learn-specific entry on its side.
- [x] Run the Validation Commands block; expect G1 and G2 green; G3 through G9c still red (pending tasks); G10 green from the start; block exits non-zero on the first pending gate.
- [x] Commit: `skills: learn captures skill-usage issues and owns its skills-repo commits`

### Task 2: done-side commit-boundary migration

Files:
- `agents/skills/done/SKILL.md`

- [x] Rewrite the frontmatter description sentence "This is the only skill that performs git commits, other skills (learn, review, etc.) make file changes but never commit." to: "This skill owns all git commits except learn's own learn-authored skills-repo artifacts (learn Step 1.8 and the learn skill-placement commit workflow); other skills (review, etc.) make file changes but never commit."
- [x] In Step 1, after the learn invocation, add a note: learn may commit its own skills-repo artifacts during this step; that is expected and does not double-commit, because Step 4 sees only non-learn leftovers and no-ops when clean.
- [x] Rewrite Step 4 as a narrowed fallback titled `## Step 4: Commit Pending Skill Changes (non-learn fallback)`:
  1. Resolve the skills repo from the user's facts document (key `skills_repo_path`); when unresolvable, ask the user. Remove the sentence that derives the path from the legacy helper script.
  2. Check `git status --porcelain -- agents/skills/` in the skills repo (plus any skills-repo backlog home paths learn reported as failed captures). When clean, report "no non-learn skills-repo changes" and no-op.
  3. Classify each dirty path as session-attributed (this session's non-learn skill edits) or foreign. Ask the user before staging each session-attributed path (same discipline as Step 3 item 0); never stage foreign or peer-session paths.
  4. Stage by explicit path only; never stage a whole tree with one command. Re-run the Step 2.7 sensitive-data scan over the staged content, then commit with a descriptive message.
- [x] Update the Configuration table row for `skills_repo_path`: drop the legacy helper script from the fallback column; the fallback is asking the user.
- [x] Add a Rules line: never stage skills-repo changes with a directory-wide add; learn-owned artifacts are committed by learn in Step 1, and Step 4 stages only session-attributed non-learn paths after asking.
- [x] Run the Validation Commands block; expect G1 through G3 green; G4 through G9c still red; G10 green from the start.
- [x] Commit: `skills: done narrows the skills-repo sweep to a non-learn ask-first fallback`

### Task 3: catalog row and provider note

Files:
- `README.md`
- `agents/skills/receiving-review/SKILL.md`

- [x] Extend the `learn` catalog row's description column with: "Captures skill-usage issues as high-priority backlog items in the skills repo and commits its own learn-authored skills-repo artifacts." (The `done` skill has no dedicated catalog row; it is named in the vendored-skills paragraph, which needs no change.)
- [x] In receiving-review's "Backlog capture for valid findings not fixed in scope" section, add one provider line: "Scope: review findings in the current project. learn's skill-usage-issue capture (learn Step 1.8) reuses this item shape for skills-corpus defects in the skills repo's backlog home; the two sources are disjoint and neither owns the other's path."
- [x] Run the Validation Commands block; expect G1 through G4 green; G5 through G9c still red; G10 green from the start.
- [x] Commit: `docs: catalog learn skill-usage capture and note the disjoint backlog sources`

### Task 4: done-lock one-shot handoff harness

Files:
- `scripts/done-lock.sh`

- [x] Add selftest fixture 17 (inside `cmd_selftest`, after fixture 16, mirroring the existing fixture style): "One-shot handoff: an acquire in an exiting subshell (no trap installed, holder PID pinned to a live process) keeps the lock held across that exit; a second acquire from a fresh process is blocked; a token-fenced release re-exported from the first acquire's stdout succeeds in a later process." Implementation shape: start a `sleep 120` holder process; inside a subshell, run the acquire with `DONE_LOCK_HOLDER_PID` set to that process, write `DONE_LOCK_DIR` and `DONE_LOCK_TOKEN` to temp files, and let the subshell exit without a trap; from the fixture shell, expect a second `acquire` to exit 2; then release with both values read from the temp files via `release-repo` and expect success; print `selftest OK: one-shot handoff` on pass.
- [x] Update the `DONE_LOCK_HOLDER_PID` line inside `usage()` to: "For one-shot shell callers: pin this to a long-lived process so the lock survives the acquiring call's exit; leave unset when eval'ing from a persistent shell (the default stays the PPID of the eval'ing shell; do not use the acquire script's own PID)."
- [x] `bash scripts/done-lock.sh selftest` fixture 17 (characterization: captures the protocol the done Step 0 Variant B text documents); given an acquire whose subshell exits immediately with `DONE_LOCK_HOLDER_PID` pinned to a live process and no trap installed, expects the lock still held (a second acquire from a fresh process exits 2) and a token-fenced release from the re-exported first acquire's values to succeed.
- [x] Run → expect GREEN (characterization: the lock helper already implements cross-process hold and token-fenced release; the defect this plan fixes was the skill's trap prescription, not the helper).
- [x] Run the Validation Commands block; expect G1 through G5 green; G6 through G9c still red; G10 green from the start.
- [x] Commit: `scripts: pin the done-lock one-shot handoff protocol in selftest`

### Task 5: done Step 0 two-variant lock procedure

Files:
- `agents/skills/done/SKILL.md`

- [x] Replace the single trap prescription after the Step 0 acquire script with two labeled variants:
  - "Variant A, persistent controlling shell: install the trap in the controlling shell immediately after the successful acquire (the existing trap snippet stays here) so an interrupted same-shell run attempts token-fenced release. The trap is a safety net, not a substitute for the explicit Step 6 release."
  - "Variant B, one-shot shell calls: never install the exit trap in the acquiring call; the acquiring shell exits when the call ends and the trap would release the lock while the workflow continues. Retain `DONE_LOCK_DIR` and `DONE_LOCK_TOKEN` in session context from the acquire output (Step 0 item 3), and the run must reach the Step 6 release on every exit path (completion, failure, or blocked). When a long-lived process is identifiable (for example the agent runtime), pin DONE_LOCK_HOLDER_PID to a long-lived process so dead-holder recovery cannot reclaim the lock mid-run after the grace period."
  - Interruption cleanup for both variants: Variant A's trap attempts release on interrupt; in Variant B the lock intentionally survives the call, cleanup is the explicit Step 6 release from session context, and when the session itself died the operator escapes are `status` plus `stale-clean` per Step 0 item 5.
- [x] In Step 6, extend the re-export sentence to name the variant: "In Variant B environments re-export both values from your Step 0 acquire output (chat context) before releasing."
- [x] Run the Validation Commands block; expect G1 through G6 green; G7 through G9c still red; G10 green from the start.
- [x] Commit: `skills: document done lock acquisition for persistent and one-shot shells`

### Task 6: docs-branch witness append and done wiring

Files:
- `agents/skills/docs-branch/SKILL.md`
- `agents/skills/done/SKILL.md`

- [x] Add a new section `## Step 3: Lesson-Scope Drift Witness Append` after Step 2 in docs-branch: when the caller holds a lesson-scope-audit drift witness line (from done Step 3 item 4a) for a corpus whose path is gitignored, the docs-branch-only path has no Step 3 commit to carry the line, so this step lands it as the body of an append-only empty commit on the docs branch. Contract: the caller passes the exact witness line as the single argument; the line must start with lesson-scope-audit: (fail loud otherwise). The canonical drift witness line this skill expects is: lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run. Failure semantics: a missing docs branch, a failed worktree add, or a failed commit each returns non-zero with a loud message; a missing docs branch means no sync ever carried the corpus, so the append must refuse rather than overstate coverage. Run this exact block from the new section (single shell invocation, bash not zsh, worktree removed on every exit path; never push, the docs branch stays a local safety net per this skill's rules):

```bash
docs_branch_witness_append() {
  # $1: the exact witness line; must start with lesson-scope-audit:
  _w="$1"
  case "$_w" in
    lesson-scope-audit:*) ;;
    *) echo "docs-branch: witness must start with lesson-scope-audit:" >&2; return 1 ;;
  esac
  git show-ref --verify --quiet refs/heads/docs || { echo "docs-branch: no docs branch; run a sync first" >&2; return 1; }
  _wt="$(mktemp -d "${TMPDIR:-/tmp}/docs-branch-witness.XXXXXX")"
  if ! git worktree add "$_wt" docs; then
    rm -rf "$_wt"
    echo "docs-branch: witness worktree add failed" >&2
    return 1
  fi
  if ! git -C "$_wt" symbolic-ref -q HEAD >/dev/null; then
    git worktree remove --force "$_wt" >/dev/null 2>&1 || rm -rf "$_wt"
    echo "docs-branch: witness worktree is detached; aborting (a detached worktree would drop the witness commit)" >&2
    return 1
  fi
  ( cd "$_wt" && git commit --allow-empty -m "docs: lesson-scope-audit drift witness" -m "$_w" )
  _rc=$?
  git worktree remove --force "$_wt" >/dev/null 2>&1 || rm -rf "$_wt"
  if [ "$_rc" -ne 0 ]; then
    echo "docs-branch: witness commit failed" >&2
    return 1
  fi
  return 0
}
```

The witness line is byte-for-byte identical to the Step 3 corpus-commit body line so one audit-note grep pattern covers both carriers.
- [x] Add a docs-branch Integration Points entry: "With done (drift witness): done Step 3 items 4a and 6 invoke this step's witness append when the audited corpus is gitignored; docs-branch owns the append mechanics, done owns the witness line text."
- [x] In done Step 3 item 4a, extend the drift-path sentence: "When the project corpus path is gitignored there is no Step 3 corpus commit to carry the line: invoke the docs-branch skill's witness append (its Step 3) with the exact witness line so the docs-branch history carries the same byte-for-byte line."
- [x] In done Step 3 item 6, after the existing body-line sentence, add: "When the audited corpus path is gitignored (no Step 3 corpus commit exists), the witness append on the docs branch carries the line instead; the append failure is a manual follow-up reported in the Step 7 outcome report and never blocks the Step 3 commit path."
- [x] Run the Validation Commands block; expect all gates G1 through G10 green and the block to exit 0.
- [x] Commit: `skills: carry the lesson-scope drift witness onto the docs branch`

### Task 7: final validation and hygiene gates

Files:
- none new (verification only; commit only if a prior task left an unchecked fix)

- [x] Run the full Validation Commands block from the repository root; expect exit 0 with `VALIDATION OK: all gates green`.
- [x] Run the em-dash scan over touched prose files and the repository's public hygiene scan; both must exit 0 before any commit.
- [x] Verify the touched-file set matches the Review Scope explicit list plus nothing else (`git status --porcelain` from a clean start of this plan's work); report any extra path instead of committing it.
- [x] Commit only if Tasks 1 through 6 left fixes pending: `skills: finish learn and done workflow updates validation sweep`
