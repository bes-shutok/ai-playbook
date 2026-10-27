# Backlog: release Step 3 sibling-branch report flags an unrelated-history branch and prints a git fatal

- **Filed:** 2026-10-26, learn Step 1.8 over the 2026-10-26 release run (Step 3 report)
- **Status:** open
Quarantine: 2026-10-27
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class (a report loop lacks the no-common-ancestor case; default shape: one guard clause in the loop)
- **Driving force:** operator time
- **Skill/step:** `agents/skills/release/SKILL.md` Step 3, the report-only `while read -r ref sha` loop over `refs/heads/` that names sibling branches sharing pre-release-only history
- **Source reference:** the 2026-10-26 release run's Step 3 output: four authoring branches named correctly, then `fatal: Not a valid object name ` followed by `sibling branch pointing into the rewritten range (or forked from it): refs/heads/docs`; the `docs` branch is the orphan documentation branch with no common ancestor to `main`
- **Why not fixed now:** the release run was in its publish step; skill-text edits ride a reviewed landing, not the release's own commit
- **Dedup probe:** searched open backlog filenames and Problem text for `release`, `sibling branch`, `merge-base`, `docs branch`; no open row owns the Step 3 report loop

## Problem

The loop computes `git merge-base "$sha" "$BACKUP_REF"` for every local branch and feeds the result to `git merge-base --is-ancestor <result> <remote>/main`. For a branch with no common ancestor (the orphan `docs` branch the docs-branch skill maintains), the inner `merge-base` prints nothing and exits 1; the outer call then receives an empty first operand, prints `fatal: Not a valid object name`, exits non-zero, and the loop reports the branch as pointing into the rewritten range. The report's meaning ("publishing this branch would send unscanned commits") does not hold for a branch that shares no history at all, and the stray fatal line reads like a failure of the release itself.

## Evidence

- `agents/skills/release/SKILL.md` Step 3 block: the loop body is a single `if ! git merge-base --is-ancestor "$(git merge-base "$sha" "$BACKUP_REF")" "refs/remotes/$REMOTE/main"` with no check that the inner substitution produced an object.
- The 2026-10-26 release run's Step 3 output shows the fatal line immediately before the `docs` branch's report line; the four other named branches produced no fatal.
- `agents/skills/docs-branch/SKILL.md` maintains `docs` as an orphan branch, so this case recurs on every release in a repository using that skill.

## Expected

A branch with no common ancestor to the backup ref is either skipped silently or reported under its own wording ("unrelated history, not scanned by this release"), and the report prints no git fatal.

## Suggested direction

Guard the loop: compute the inner `merge-base` into a variable, `continue` (or print the unrelated-history wording) when it is empty, and run the ancestor check only on a non-empty value. One-clause skill-text change; pay the growth by tightening the loop's surrounding comment.

## Alternatives

- **Leave the loop as is and let the operator read past the fatal:** rejected; the fatal line plus a false report is the only noise in an otherwise clean release summary, and the release skill asks the agent to relay the sibling list verbatim (`agents/skills/release/SKILL.md` Step 3 summary item 5).
- **Move the loop into `scripts/release-rewrite.sh` or the push script:** rejected; the report is intentionally outside the gated scripts (report-only, after publish), and moving it would grow a guard-bearing path for a cosmetic fix (`scripts/release-rewrite.sh` header comment on what the script owns).
- **Exclude the `docs` branch by name:** rejected; the defect is the missing no-ancestor case, which any orphan branch triggers, not this branch's name (`agents/skills/docs-branch/SKILL.md`).

## Machinery assessment

No machinery. A guard clause in a report-only loop; nothing blocks on it.
