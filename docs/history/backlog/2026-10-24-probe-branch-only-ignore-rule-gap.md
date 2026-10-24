# Backlog: probe tracked-ignored warning reads only the base worktree's ignore rules

- **Filed:** 2026-10-24, Phase 3 review round r1 of plan ignored-audit-home-tracked-index-fence
- **Status:** open
- **Workflow:** backlog
- **Priority:** normal
- **Origin class:** self-serving
- **Class:** fix-class
- **Driving force:** correctness
- **Skill/step:** scripts/land_squash.sh, probe tracked-ignored pass (check-ignore --no-index --stdin over the branch delta)
- **Cluster:** docs/history/plans/2026-10-23-ignored-audit-home-tracked-index-fence.md (the probe arm this row bounds)

## Problem

The probe's tracked-ignored pass pipes the branch delta into `git check-ignore --no-index --stdin`, and check-ignore resolves exclude sources (`.gitignore`, `.git/info/exclude`, core.excludesFile) from the checked-out worktree, which during the probe is the base worktree. A branch that introduces its ignore rule in the same delta that force-tracks a path under it is therefore never warned: at probe time the rule is not in the base worktree, so check-ignore does not match the path. The plan's target class is still covered, because the `.ai-playbook/` audit-home rule pre-exists on main; the miss is the broader class where a branch carries its rule and its forced path together.

Witness: Phase 3 review round r1 (correctness-completeness lens, finding F13), reasoned from git's exclude-source resolution semantics; no landing incident.

## Outcome sought

Either union the source tip's ignore rules into the match, for example by additionally feeding check-ignore `--exclude-from` with the source tip's `.gitignore` (`git show "$SOURCE_TIP":.gitignore`) so a branch-carried rule is honored, or record a decision that base-rules scope is the documented limit of the warning (one sentence in the plan's Edge cases and the probe arm's comment).

## Rejected alternatives

- Building the `--exclude-from` arm without machinery admission: rejected, the machinery admission protocol requires an incident, catch frequency, false-positive cost, and a sunset for any addition that can block a lane; this row is the pre-registration home if the arm is ever built.
- Leaving the limit undocumented: rejected, a silent scope limit on a correctness report is the drift class the corpus records lessons for.
