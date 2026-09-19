# Backlog: Codify the done sweep's deterministic gates into one gate-runner script

Status: open
Workflow: backlog
Source: Andrey 2026-09-18: "some highly regulated and standardized parts of the skills like done should be replaced with scripts/code". Analysis in `docs/tmp/2026-09-18-harness-principles-triage.md` ranks the done sweep as the #3 wall-clock cost.
Severity: Medium (done runs once per task; every plan pays 690 lines of prose interpretation per task-end, and each gate is an agent-read-run-interpret cycle that can drift from its script)
Scope: agents/skills/done/SKILL.md, new repo-root scripts/ gate runner, agents/skills/done/ (supporting docs)

## Problem

The done skill (22 steps, 690 lines) is mostly a regulated sequence of
deterministic checks that already have scripts: `check-no-em-dash.sh`,
`check-instruction-size.sh`, `scan-public-hygiene.sh`,
`doc_registry_validator.py`, `check_backlog_inbox_location.py`,
`validate_review_staging.py`, plus cross-reference and import scans. Today the
agent reads the prose for each step, runs the script, and interprets the
output one step at a time. Costs per invocation: heavy context load, per-step
latency, and drift risk between prose and script (the class that produced the
docs-branch reset-unstages-mv and shadow-preamble incidents).

## Proposed direction

1. A single `done_sweep_gates.sh` (repo-root scripts/, synced to
   `~/.ai-playbook/scripts/` per the canonical-copy rule) that runs every
   deterministic gate in the SKILL.md order, in parallel where independent,
   and emits ONE machine-readable report (gate, rc, short message) plus a
   human summary.
2. The skill keeps only: lock acquire/release, learn (judgment work),
   commit staging decisions, and failure handling for gates the runner flags.
   The gate steps collapse to "run the runner; fix what it flags".
3. Generalizable rule for `learn` to capture: any skill step that is a
   fixed command with an exit-code verdict must live in a script; SKILL.md
   prose may only orchestrate and interpret failures.
4. Acceptance: SKILL.md shrinks materially (target under ~350 lines); a
   full gate pass is one script call; all existing gates still gate (no
   check silently dropped; diff the runner's gate list against the current
   step list during review).
