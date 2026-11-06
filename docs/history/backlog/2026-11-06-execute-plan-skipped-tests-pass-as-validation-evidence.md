Status: open
Priority: high
Consumer urgency: This affects consumer projects whose standard suite needs a container runtime; do not park or defer it as formal-hardening for the skills repository alone.
Class: fix-class
Origin class: consumer-feedback (company)

# Repository-standard validation evidence accepts a green run whose Docker-backed tests were skipped

Cluster: docs/history/backlog/2026-11-05-debugging-validation-misses-required-ci-checks.md (same family: a required check is skipped yet verification is reported green; that item covers the debugging skill, this one covers execute-plan, execute-plan-stack, and unit-test-runner)

## Problem

A task's repository-standard suite run ended with build success and exit code 0 while a couple hundred container-backed tests (Testcontainers) were reported as skipped, because the container daemon was down ("Could not find a valid Docker environment"). Earlier tasks in the same run had executed the identical suite with zero skipped. A skipped test produces no failure, so the exit code, the build status line, and the zero-failure counts all looked like the passing evidence the skills ask for. The parent caught it only by reading per-module `Tests run` and `Skipped` counts and comparing them with the previous boundary by hand; nothing in the skills tells it to.

Current text, all silent on skipped counts:

- `agents/skills/execute-plan/SKILL.md`, Phase 2 step 2: "Missing guidance, incomplete inventory, unavailable commands, or failures leave Phase 2 incomplete". Unavailable commands are covered; a command that runs but silently skips part of the inventory is not.
- `agents/skills/execute-plan/SKILL.md`, the worker-success paragraph near the top: asks for fresh validation evidence and selected test identities, with no totals.
- `agents/skills/execute-plan-stack/SKILL.md`, step 5: "Missing, failing, unavailable, incomplete, or stale evidence blocks advancement" names incomplete evidence but gives no way to detect a skipped-test shortfall.
- `agents/skills/unit-test-runner/SKILL.md`, step 4 (Report): asks for the test count from the runner's reports and says never to describe a subset as the full suite, but does not ask for skipped or errored-out-of-run counts.
- `agents/skills/unit-test-runner/maven.md`: no mention of the Surefire or Failsafe `Skipped` column.

Existing guideline text is adjacent but different: `agent_workflow_guidelines.md` section 12 covers a newly written test method silently not running, and section 17.2 reads the `Tests run ... Skipped` line only to tell test failures from application log noise. Neither makes skipped totals part of the evidence gate.

## Observed vs expected

Observed: a green exit with a large skipped count was recorded as a verification attempt and caught by chance (an operator-style read of per-module counts), not by the workflow.

Expected: the evidence envelope for a repository-standard run records the aggregate `Tests run` and `Skipped` totals; a skipped total above the previous boundary's (or above an explicit expected baseline) is treated as incomplete evidence, the same disposition as an unavailable command, so the boundary does not commit and the stack does not advance until a rerun shows the skipped count back at or below the baseline (or the extra skips are explained and accepted by a recorded decision).

## Exact location

- `agents/skills/execute-plan/SKILL.md`: Phase 2 step 2 and the stack-task validation return (the worker-success paragraph and the light-boundary evidence binding).
- `agents/skills/execute-plan-stack/SKILL.md`: step 5 evidence check.
- `agents/skills/unit-test-runner/SKILL.md` step 4 and `agents/skills/unit-test-runner/maven.md`: report skipped totals alongside the count.

## Suggested fix (minimal)

1. `unit-test-runner` step 4 and the Maven adapter: report `Tests run`, `Failures`, `Errors`, and `Skipped` totals for the run, per module when the build is multi-module.
2. `execute-plan` Phase 2 step 2 and the worker-success evidence list: record the run's `Tests run` and `Skipped` totals in the evidence envelope; treat a skipped total above the previous boundary's (first boundary: the recorded baseline, or zero when the project documents none) as incomplete evidence, leaving the boundary or Phase 2 incomplete like an unavailable command. One sentence plus the envelope fields; do not add a validator script.
3. `execute-plan-stack` step 5: one clause pointing at the same comparison, so the stack boundary does not re-derive it.

## Severity and source

Severity: High; a false-green repository-standard run can let a commit and a draft PR proceed without the tests that exercise the real database or broker paths.
Source: a company consumer project stack run, 2026-11-06; parent read per-module counts and held the commit. Capture hygiene: scan and em-dash check run before filing.

## Why not fixed now

Learn capture only; the fix touches three skills and should be reconciled with the open project-test-policy item (`docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md`), which also edits Phase 2 step 2, before editing.

## Driving force

reliability

## Dedup probe

Searched open backlog names and bodies for `skipped`, `Testcontainers`, `Docker`, `Tests run`, `evidence`, and `validation`, and the three skills' current text for `skipped`. Only the debugging-skill item (different skill, same family, now linked as Cluster) and the project-test-policy-scope item (suite selection, not skipped totals) are adjacent; neither covers skipped-count evidence.
