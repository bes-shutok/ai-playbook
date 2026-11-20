---
name: execute-plan
description: >
  Orchestrates execution of a plans-skill implementation plan with sub-agents. Trigger phrases:
  "execute the plan", "execute plan", "execute <plan-path>", "implement plan", "implement <plan-path>",
  "run plan", "run <plan-path>", "execute-plan", "/execute-plan", or attaching/invoking this skill.
  A bare plan path (no verb, no slash command, no attachment) is NOT execute-plan; see the Invocation
  detection section (run first). Flow: one host-native implementation worker per task in plan order,
  tests pass, plan checkboxes marked, the parent-owned light boundary after each task; then review/fix
  loops to the graded Phase 3 exit (one fresh blocking-clean digest, or its verified comment-only
  corrections re-bind) with reflection at configured intervals; the done skill runs once at the final
  closeout; on success remove tmp_dir/execute-plan/<plan-slug>/.
---

# Execute Plan

**First step every turn:** Run [Invocation detection](#invocation-detection-run-first) before the plan-path gate or any Phase 0 work. If detection returns `invoked`, proceed immediately; never show the three-way gate.

**Documentation paths:** At Phase 0, read `{plans_dir}`, `{plans_completed_dir}`, `{backlog_dir}`, `{backlog_completed_dir}`, `{reviews_dir}`, `{tmp_dir}`, and `{metrics_dir}` from the opening TOML block in `.ai-playbook/facts.md` (see `using-skills` Step 0). Use `{tmp_dir}/execute-plan/<PLAN_SLUG>/` for session logs. Substitute resolved paths everywhere below that shows `{...}` or legacy `docs/plans/` examples. After doc-hierarchy migration, `{plans_dir}` is often `docs/history/plans/`; treat that path the same as `docs/plans/`.

**Announce at start:** "I'm using the execute-plan skill to implement `<plan-path>`."

Orchestrate from the main agent. Run Phase 0 first and delegate heavy work. Use inline fallback only when native delegation is unavailable before launch or a launched worker is verified terminal; never edit task paths while worker liveness is unknown.

**Intermediate reviews (default on):** every executed task passes the Step 1.2b intermediate task review before its boundary commit. A plan header line `Intermediate reviews: off` skips Step 1.2b for that run, and the Recovery path does not run it; any other value or absence keeps it on.

## Module dispatch (the router contract)

The execute-plan skill's operative text lives in per-concern modules beside this router; each dispatch entry below is the one-paragraph contract plus the module pointer, and a session loads the named module's whole text when the consuming step fires (load-on-dispatch: the read set is this router plus the in-flight module named by the consuming step, never the full pre-split body). No rule is restated here; each module's headings and bodies are the moved originals, byte-verbatim.

- **Invocation, orchestration contract, and anti-patterns** - load `agents/skills/execute-plan/invocation-and-orchestration.md` (the `## Sequential native execution contract`, `## Live-session discovery ladder`, `## Invocation detection (run first)`, `## Execute-plan invocation vs plan-path gate`, `## Anti-patterns (never substitute for orchestration)`, `## Sub-agent execution logs`, and `## Worktree-first standard` headings: the run-first detection ladder with its three-way gate, the sequential worker contract and its orchestration state table, the anti-pattern table, and the sub-agent execution log and worktree-first duties) before any plan-path gate or Phase 0 work and at every launch decision.
- **Run setup (Phase 0) and configuration** - load `agents/skills/execute-plan/run-setup.md` (the `## Phase 0: Run Setup (Run Once at Start)` and `## Configuration (from facts document)` headings: the worktree-first run setup, session bootstrap and manifest creation, the plan readiness and predecessor hard gates, the quota-window Budget gate, the context budget checkpoint ladder with its task-boundary checkpoint duty, and the facts-document configuration) once at run start before any task implementation, and at every task-boundary checkpoint.
- **Read-only verification lane** - load `agents/skills/execute-plan/read-only-verification-lane.md` (the `## Read-only verification lane` heading: the lane condition evaluated once at Phase 0 entry, the primary-placement posture with its serialization consult and base-branch check, the vacuous duty list, the retained duty list ending in the plans-egress pointer record, and the tracked-edit stop rule) at Phase 0 entry when the active plan matches the lane condition (every task's `Files:` list declares none); the lane module owns which duties stay retained or vacuous for that run.
- **Implementation loop (Phases 1-2)** - load `agents/skills/execute-plan/implementation-loop.md` (the `## Orchestrator Responsibilities`, `## Stack-task entry point`, `## Phase 1: Per-Task Implementation Loop`, and `## Phase 2: Plan Completion` headings: task selection with its inclusion hard gate, the implement sub-agent launch and the intermediate task review, the done-pending reconciliation arm, progress marking and the light boundary, and plan completion validation) for every task in plan order.
- **Review / Fix loop (Phase 3)** - load `agents/skills/execute-plan/phase-3-review.md` (the `## Phase 3: Review / Fix Loop` heading: the parent-orchestrated code review, doing-code-review triage, sequential finding address, digest evaluation with the graded exit, and the tracking-list contracts for the launch ledger and dispatch-failure receipt) from the first implementation-free state through the graded Phase 3 exit.
- **Archive and cleanup (Phases 4-5)** - load `agents/skills/execute-plan/archive-and-cleanup.md` (the `## Phase 4: Archive Plan` and `## Phase 5: Remove session tmp files (success only)` headings: the archive commit and receipt, the bad-archive recovery arm, the queue-drain taxonomy-parity closeout spans, and the success-only tmp cleanup with its exit-path throwaway-script cleanup) at plan completion and final closeout.
- **Sub-agent launch rules and hard gates** - load `agents/skills/execute-plan/launch-rules-and-gates.md` (the `## Sub-Agent Launch Rules`, `## Hard Gates`, and `## User Interruption` headings: the quota-wall dispatch doctrine with its two-class classification and bounded-retry budget, the never-substitute gates list, and the interruption state table with the Active-plan referral) at every worker launch and interruption.
- **Recovery and integration points** - load `agents/skills/execute-plan/recovery-and-integration.md` (the `## Recovery: retroactive execute-plan compliance` and `## Integration Points` headings: the retroactive compliance procedure for an in-flight plan run outside the skill, and the per-skill provider and consumer contracts) when a run must be brought back under the skill and at cross-skill boundaries.
