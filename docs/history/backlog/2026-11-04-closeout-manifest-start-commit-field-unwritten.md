# Backlog: closeout manifest branch record's declared start-commit field has no writer

- **Filed:** 2026-11-04, plan-review r2 certification residual (agent-resource-cleanup-disposition, overflow row 1)
- **Status:** open
- **Workflow:** backlog
- **Priority:** medium
- **Origin class:** plan-review residual
- **Class:** fix-class
- **Dedup probe:** searched open backlog filenames and bodies for branch record, start commit, and migration manifest. `docs/history/backlog/2026-10-31-no-charter-start-commit-missing-reason.md` covers a missing-start-commit refusal reason in the no-charter arm's done-run manifest binding, not the closeout migration manifest's branch record. `docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md` owns the base-drift false positive this field would serve. None covers a manifest field that plan surfaces declare but no task writes.
- **Cluster:** `docs/history/backlog/2026-11-02-closeout-branch-retention-base-drift.md` (owns the base-drift proof this evidence field serves); `docs/history/backlog/2026-11-02-agent-resource-cleanup-disposition.md` (shared cleanup surface)

## Problem

Plan 2026-11-04-agent-resource-cleanup-disposition declares on three surfaces that the closeout migration manifest's branch record gains a start-commit field: the Gate delta line ("gains landing-identity and start-commit fields as evidence persistence on an existing append-only surface"), the Recorded start commit Terms entry ("the closeout migration manifest's branch record as Task 1 extends it"), and the Migration manifest Terms entry ("recording a run's branch record, start commit, and owned paths"). The only Task 1 record-writing checkbox adds "the landing commit's object id and touched path set"; no checkbox records the start commit. The script writes only `{"branch", "source"}` into the record at transfer time (scripts/worktree_closeout_migrate.py branch_record construction), so as specified the third start-commit home never populates and the Gate delta over-declares the change set.

## Expected

Either one Task 1 checkbox records the start commit into the branch record at transfer time (the claims are still readable at that moment, and the Gate delta already declares the field), or the Gate delta and both Terms entries are corrected to drop the start-commit field and name only the homes that exist. The authored-delta proof then has an honest lookup chain: claims homes while fresh, the manifest record for retries.

## Evidence

- `scripts/worktree_closeout_migrate.py`: the transfer-time branch record is `{"branch": branch_name, "source": str(source)}` (or the unresolved-branch variant); no start-commit field exists anywhere in the manifest write path.
- Plan Task 1 checkbox: "Implement the landing-identity record: ... the branch record gains the landing commit's object id and touched path set" - no start commit.
- Consequence shape: retention fallback stays safe; the loss is retry-time effectiveness for strands whose claim homes drained, exactly the strands the base-drift incident describes.
