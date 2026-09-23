# First real rejected row hard-fails under a stale runtime-home validator with no deployment-gap hint

Status: open
Workflow: backlog

## Problem statement

Until the deployed runtime-home copy of `doc_registry_validator.py` (`~/.ai-playbook/scripts/`) is refreshed from `scripts/`, the first real `state: rejected` registry row (none exist yet) hits the old enum check in the deployed copy and fails done's doc-registry gate with `invalid state value`. The failure is fail-closed and visible, but the done skill's deployment-gap signature covers only (a) a missing or unopenable validator and (b) a `ModuleNotFoundError`, so the operator is routed to the investigate path instead of the standard copy remedy (`cp scripts/doc_registry_validator.py` into the runtime home).

Evidence (hypothesis confidence): the mechanism is read from code — the stale-enum rejection text is certain against a pre-`rejected` copy of the validator — but the deployed runtime-home copy on this host was not inspected when the finding was staged.

Extension (r2 re-review, risk pass, 2026-09-23): the lag window is broader than the enum check. A deployed pre-fix copy also lacks the rejected-archive immutability and licensed-transition coverage the r1-F1 fix added to `is_immutable()` / `cmd_check_writes`, so until redeploy a body edit or deletion under either rejected archive passes the done sweep's doc-registry gate silently on the deployed copy — the same copy-remedy redeploy covers both directions (the enum false-fail and the missing freeze), so the remediation is unchanged; only the lag's blast radius grew.

## Location

- `agents/skills/done/SKILL.md` — plan-readiness gate bullet, "Deployment-gap signature (narrow)" sentence
- deployed validator copy under the runtime home `scripts/` directory (remedy target)

## Suggested fix

When the first real rejection nears (or at the next done-skill touch), extend the deployment-gap signature with the stale-enum shape: a doc-registry failure printing `invalid state value` on a row whose state the repo-copy validator accepts routes to the copy remedy rather than the investigate path.

## Severity and source reference

Low. Source: code review round r1 finding F6 (risk worker, premortem rollout pass), `docs/reviews/2026-09-23-code-review-ai-harness-friction-audit-r1.md`. Capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

Non-blocking Low finding triaged to backlog capture by the r1 address-phase instruction. No rejected row exists yet, the failure is loud and recoverable by the standard redeploy, and the finding's own analysis says no action is required until the first rejection.

Driving force: observability, secondary: reliability
