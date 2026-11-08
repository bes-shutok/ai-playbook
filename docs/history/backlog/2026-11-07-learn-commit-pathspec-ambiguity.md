# Learn Step 1.8's "stage and commit by explicit path" reads as stage-by-path plus a bare index commit, which sweeps a foreign staged hunk

- **Filed:** 2026-11-07, learn Step 1.8 self-capture from the budget-resume-carrier-gc authoring session
- **Status:** open
- **Workflow:** backlog
- **Priority:** high (the swept hunk was a peer session's staged rolling-log entry; the same read can land any peer's staged bytes under a learn commit)
- **Cluster:** docs/history/plans/completed/2026-11-02-rolling-log-write-foreign-staged-remedy.md (the foreign-staged-hunk family on shared-index commits; that plan owns the log-write runner's staged refusal and operator-gated remedy, this row owns learn's own commit wording)
- **Cluster:** docs/history/backlog/2026-11-07-rolling-log-freeze-foreign-bytes-setaside-recipe.md (same foreign-staged-hunk family; that row owns the freeze-side recovery recipe for blocked log writes, this row owns learn's own commit wording)
- **Cluster:** docs/history/backlog/2026-11-07-plan-prompts-orphaned-landed-entry-body.md (same foreign-staged-sweep family; that row owns the committed log residue this row's witnessed sweep resurrected, this row owns learn's own commit wording)
- **Origin class:** session-witnessed flow gap (learn Step 1.8 commit rule wording)
- **Class:** fix-class
- **Skill/step:** `~/.agents/skills/learn/SKILL.md` step-1-extract.md, Step 1.8 commit rule ("stage and commit learn-authored skills-repo artifacts by explicit path ... never a directory-wide add")
- **Source reference:** commit 96b615c65 of this session, whose stat carries a foreign staged `docs/history/backlog/PLAN-PROMPTS.md` hunk (a peer session's staged investigate entry) swept because the session staged its four owned paths by path but ran a bare `git commit` over the whole index; the session's own pre-stage word-diff check errored on a grep pattern and its non-zero exit was not treated as a stop; capture hygiene: `scan-public-hygiene.sh` pass
- **Why not fixed now:** learn has already closed this run; the wording amendment belongs to the skills corpus's own authoring lane
- **Dedup probe:** searched open backlog rows for `explicit path`, `foreign staged`, `index commit`; nearest is the covered rolling-log-write row (runner-side refusal; this row is the learn-side commit wording), no open row; no merge

## Problem

The commit rule says "stage and commit ... by explicit path", which admits the reading "stage by pathspec, then run a bare `git commit`". In a shared primary checkout whose index can hold a peer's staged hunk (witnessed: a peer session's staged rolling-log entry), a bare index commit lands the peer's staged bytes under learn's commit, and the receipt line then reports more than the session landed. The rule's own pre-stage word-diff own-edit check does not cover this shape: it inspects the session's staged paths, not the rest of the index, and an errored check invocation that is not treated as a stop passes the sweep silently.

## Expected

The commit rule states the commit form mechanically: the learn-authored artifact commit carries the explicit pathspec on the commit command itself (`git commit -- <owned paths>` after staging), never a bare index commit; and the own-edit pre-check's failure (non-zero exit, tool error) is a stop-and-report, never a pass-through. Optionally one line points at the memory-side recipe for committing own hunks out of a foreign-dirty file.

## Suggested fix

Amend the Step 1.8 commit rule's first sentence to pin the pathspec-on-commit form and add the errored-check-is-a-stop clause, citing this commit as the incident witness.

## Second witness (2026-11-08, 24h session-pattern harvest REM run)

The same bare-index-commit sweep also resurrected two already-landed PLAN-PROMPTS entries: the learn session's own stale staged snapshot of the log (held since before landings 487a15fc9 and 347f835a2 pruned their entries) was committed wholesale, re-adding the `operative-file-read-budget-gate` and `doing-code-review-staging-doc-scaffold-pointer` entries after their `PLAN-PROMPTS-PRUNE:` receipts existed. Consequences witnessed the same afternoon: a ~15:40 WET authoring walk skipped the resurrected entry as a stale pick and a ~16:05 WET authoring run stood down 0/1 on the log's foreign staged delta (index blob 66d8ece7c resurrecting a landed entry over a stale Frozen line). The pathspec-on-commit commit form closes this vector too: a log path outside the declared owned pathspec cannot ride the commit. Priority stands high.
