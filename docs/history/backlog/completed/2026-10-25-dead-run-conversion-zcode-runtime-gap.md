# Dead-run conversion is unreachable on this runtime: session channel empty, status provider unconfigured

- Cluster: dead-run-resume-claim-conversion
- Cluster: docs/history/backlog/2026-10-23-dead-run-conversion-coverage-residuals.md (refusal-path test coverage; this row owns the runtime reachability gap)
- Status: covered (docs/history/plans/2026-10-25-dead-run-conversion-zcode-runtime-reachability.md)
- Priority: normal
- Age: new (2026-10-25)

## What is owed

The dead-run conversion arm (`scripts/execution_claim.sh take`, plan `docs/history/plans/completed/2026-10-21-dead-run-resume-claim-conversion.md`) refuses conclusively on this host's primary runtime, so a stale foreign claim whose registered manifest still exists can never be taken over - the historical stale-takeover flow is unreachable whenever a manifest survives. Witnessed 2026-10-25 resuming the task-complete `2026-10-23-java-guideline-builder-placement-multi-constructor` run (commit 87a8e8b6 stranded pre-landing under stale claim `zcode-exec-f7fc2182-2200`; parked in scheduler-state children[], outcome blocked):

1. **Session channel gap** - the trusted session channel (`scripts/session_channel.py`) derives the active ID from Claude/Cursor/Codex env vars only; the host's actual runtime injects none, so the channel returns empty for every session and the channel-equality check (`active == --session`, empty refuses) refuses all conversions regardless of intent. The plan's own trust model states the match "is not authentication against a same-account caller who can forge those variables" - an anti-mismatch guard that currently mismatches everything.
2. **Status provider unconfigured** - `session_status_command` is absent from the primary facts document and no `docs/history/release-evidence/session-status-provider/` smoke record exists (the plan's external release gate, unmet). Even with the channel fixed, conversion refuses at the provider gate.
3. **Scan refusal reporting** - the registered-manifest scan's inconclusive verdict does not name the worktree whose facts refuse discovery (lesson 218), and an identical primary-side record mirror makes the scan ambiguous for every manifest-registered run. Both refusal classes forced diagnosis rounds during the same takeover attempt.

Bounded workarounds already applied during the witness: additive `facts.md` copies into the two config-less worktrees; mirror paused-and-restored around one gate call. No gate or validator was edited.

## Why it matters

Exec carriers that pick a plan stranded by a quota-dead peer (the recurring night-run shape) will keep parking instead of resuming near-finished runs, re-paying the full execution cost on the next dispatch. The conversion machinery exists precisely for this case and is dead code on this runtime until items 1-2 land.

## Shape of the fix

Runtime-configuration-first: add the absolute `session_status_command` to the primary facts, write the provider smoke-evidence record, and extend the channel derivation with this runtime's session-environment source (or document an explicit runtime-unsupported note so takeovers route around conversion honestly). Item 3 rides lesson 218's reporting rule in the same execution. Cluster sibling `docs/history/backlog/2026-10-23-dead-run-conversion-coverage-residuals.md` owns the refusal-path test coverage; this row owns the runtime reachability gap.
