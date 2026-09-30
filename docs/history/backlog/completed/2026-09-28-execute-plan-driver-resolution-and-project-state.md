# Execute-plan driver resolution obscures project-local state ownership

Captured: 2026-09-28 (source: company consumer execute-plan session, user feedback)
Status: done (2026-09-30; implemented by the executed plan completed/2026-09-28-execute-plan-preflight-mandate-and-driver-resolution.md and its successor hardening: execute-plan SKILL.md carries the preflight mandate verifying every emitted continuation command pins --repo-root and --runtime, and the Shared driver resolution paragraph states the shared-deployment policy (one shared driver copy, run artifacts under the target project's facts-resolved tmp dir, project-local entry points only as deliberate explicit overrides, explicit --repo-root when invoked from a foreign checkout); the driver builds the canonical self-sufficient continuation command (_preflight_continuation_command) and the foreign-cwd reinvocation is pinned by test_emitted_command_reinvoked_from_foreign_cwd_reaches_adapter. Verified against every Expected bullet on disk this date; closed as a landed-work straggler)
Priority: high
Workflow: backlog
Class: correctness
Driving force: reliability
Origin class: consumer-feedback (company)
Consumer urgency: Company consumer projects running execute-plan need deterministic driver and project-root resolution to keep continuation state bound to the correct repository; the skills-repo personal priority profile must not park or defer this shared-skill fix as formal-hardening for the skills repo alone.

## Problem

The execute-plan contract names the executable as `scripts/execute_plan_runtime.py` and shows commands with that relative path, while the shared implementation lives in the ai-playbook repository. A consumer repository may have no such `scripts/` file, so the operator or agent has to discover and invoke the deployed shared copy. That makes it appear that the continuation driver and the run's temporary artifacts belong to the shared repository.

The two ownership questions are not stated together: shared code may come from ai-playbook, while each run's manifest, logs, and other temporary artifacts must be resolved from the target repository's `.ai-playbook/facts.md` (`tmp_dir`). If the shared script is invoked with the ai-playbook checkout as its working directory, the driver's default `repo_root` is also that checkout unless `--repo-root` is supplied. This risks resolving project paths against the wrong repository even when the manifest path points into the consumer project.

In the consumer session, the manifest, worker log, and telemetry were under the service repository's resolved `docs/tmp/execute-plan/<plan-slug>/`. The confusing part was the shared script location and the implicit working-directory contract, not evidence that those temporary files had been written into ai-playbook.

## Exact location

- `agents/skills/execute-plan/SKILL.md`: Phase 0.5 runtime invocation and Budget gate > Standing resume watcher command examples.
- `agents/skills/execute-plan/runtime-contract.md`: Durable driver boundary and path ownership.
- `scripts/execute_plan_runtime.py`: `--repo-root` behavior and generated continuation command.
- `scripts/execute_plan_resume_watcher.py`: shared watcher implementation and invocation path.
- Consumer repo `.ai-playbook/facts.md`: authoritative per-project temporary-artifact location.

## Environment

Local multi-repository session, 2026-09-28. The driver source is the ai-playbook repo copy; the consumer run resolved paths from its own facts file. The reported executable path was in the shared ai-playbook scripts deployment, while the consumer run artifacts remained in its own `docs/tmp/` tree.

## Severity and source reference

Severity: medium-high.

Source: user feedback during an execute-plan continuation session, 2026-09-28. Capture hygiene: `scan-public-hygiene.sh --files` pass.

## Expected

- The skill states plainly that the driver implementation is shared, while run artifacts belong to the target project and are placed under that project's facts-resolved `{tmp_dir}`.
- Every command that invokes a shared driver resolves its executable deterministically and passes or preserves the target project root. Running it from the shared checkout must not silently make ai-playbook the consumer project root.
- The project-local override/deployment contract is explicit. If a project needs a local entry point, it can live under that project's `.ai-playbook/` directory as the user suggested; the shared implementation remains the source of truth unless a deliberate local override is configured.
- A path-resolution check covers invocation from both the target repository and the shared tooling repository, and confirms that manifests and temporary artifacts stay under the target repository's resolved `{tmp_dir}`.

## Witness

Company consumer session, 2026-09-28: the target repo's `.ai-playbook/facts.md` resolves `tmp_dir` to `docs/tmp/`; its execute-plan manifest and worker artifacts were present under `docs/tmp/execute-plan/<plan-slug>/`. The runtime driver source is in ai-playbook's `scripts/`, and its generated continuation command uses the relative `scripts/execute_plan_runtime.py` form without carrying an explicit `--repo-root`.

## Why not fixed now

This session was asked to capture the workflow defect in the ai-playbook backlog. Changing the shared execution contract or deploying a project-local wrapper would alter runtime invocation behavior and needs a focused implementation plan.

## Dedup probe

Search terms: `execute-plan driver resolution`, `runtime script project root`, `consumer tmp_dir shared script`, `repo-local driver wrapper`. Nearest item: `2026-09-27-execute-plan-task-scoped-verification-contract.md`, which covers pre-launch validation of task criteria, not executable lookup or repository-root propagation. No open item defines shared-driver resolution together with consumer repo and temporary-artifact ownership.

## Suggested fix

First choose and document one supported resolution policy: (1) keep the implementation deployed under the shared ai-playbook home and have the skill resolve that executable from facts/config while always passing the target `--repo-root`; or (2) provide a small project-local `.ai-playbook/` entry point that delegates to the shared implementation and pins the current repository root. In either case, retain all run-specific artifacts under the target project's resolved `{tmp_dir}`. Update every skill command and the driver's emitted continuation command together, then add an integration-style path test for calls originating from both repository roots. Do not copy the large driver into each consumer repository unless independent versioning is an explicit requirement.
