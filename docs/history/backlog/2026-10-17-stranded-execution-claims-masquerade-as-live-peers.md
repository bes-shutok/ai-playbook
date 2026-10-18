# stranded execution claims masquerade as live peer sessions

Driving force: reliability
Date filed: 2026-10-17
Status: covered (landing 5865a50a5: the gateway sweep arm plus the landing-tail own-claim release; EXEC-PROMPTS entry pruned with receipt dddf2d6e5)
Origin: 2026-10-17 exec-lane run witness (a survey stood down twice on claims whose owning sessions had finished)

Cluster: docs/history/backlog/2026-10-07-execution-claims-dir-resolution-drift.md; docs/history/backlog/2026-10-06-claim-fence-test-coverage-gaps.md; docs/history/backlog/2026-10-07-claim-fence-stem-case-drift.md

## Finding

The claim-release contract exists (`agents/skills/execute-plan/SKILL.md` Execution claim registration paragraph: "the run deletes the claim at closeout and on an owned stand-down"), but only execute-plan-skill runs honor it. Manual ad-hoc exec runs (session ids of the `manual-exec-*` shape) take claims through the same gateway and then finish without any closeout step that releases the claim: on 2026-10-17 the rearm-dispatch-ladder plan landed (`8d72b319a`) and its worktree was torn down, yet its claim file remained, and three further orphaned claims for plans landed on 2026-10-10/11/12 (plan-origins-coverage-parse, plan-scope-gist-surface, execute-plan-sequential-only-adapter-removal) survived until a manual sweep. A stranded claim is indistinguishable from a live peer by the selectors' own rule (a claim whose `updated:` is fresher than one cadence period naming a foreign session is a skip class), so landed plans read as peer-blocked and exec surveys stand down against nobody.

## Expected

A claim whose plan is landed (the plan file lives under the plans root's `completed/` archive or the plan is absent from the plans root while a landing commit names its slug) and whose recorded worktree no longer resolves cannot be a live peer; that state is sweepable without touching any live claim. The release arm needs an enforcement path that does not depend on the run's own discipline: either a sweep arm on the claim gateway (bounded to the landed-plan-plus-gone-worktree shape) or a closeout duty in the landing tail that releases the run's own claim as part of teardown.

## Evidence

- 2026-10-17 exec-lane run: rearm-dispatch-ladder claim orphaned after landing `8d72b319a`; four orphaned claims deleted from docs/tmp/execution-claims/ after verifying each plan landed and no worktree resolved
- `agents/skills/execute-plan/SKILL.md` Execution claim registration paragraph (the closeout-release contract manual runs never load)
- `agents/skills/maintenance/decisions.md` D1 fresh-execution-claim skip (the selector rule a stranded claim weaponizes)
