# Backlog: enforce the local-only boundary for personal and pet projects

- **Filed:** 2026-10-10, after a remote-operation scope violation
- **Status:** covered (docs/history/plans/2026-10-17-personal-project-remote-boundary-enforcement.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** authorization-boundary failure
- **Class:** harness enforcement
- **Driving force:** safety + reliability
- **Skill/step:** `agents/skills/github-pr-workflow/SKILL.md`, project-scope and remote-operation gate; shared Git operation guards

## Problem

The previous instruction allowed an agent to push or open a PR for a personal project when the user explicitly asked. A later clarification set a stricter boundary: agents must keep personal and pet project work local, while the operator alone handles remote operations. During the same work, an instruction to clean up branch state was interpreted as permission to create and merge a pull request. The local branch and local `main` state had not first been treated as the complete agent-owned scope.

The user-level instruction and shared PR workflow now state the local-only boundary. They still depend on the agent recognizing the project scope and following prose before any remote-capable command. This item asks whether a reliable mechanical guard can enforce the boundary without blocking company-project workflows or ordinary local Git work.

## Expected

Investigate whether a portable, reliable enforcement point can resolve project scope from configured facts and block agent-initiated remote access in personal or pet projects before remote Git or GitHub CLI operations. Evaluate existing agent hooks, command wrappers, and tool policy boundaries rather than assuming shell commands can be intercepted consistently. Keep local branch inspection, edits, commits, and tests available; fail closed when scope is unknown. Branch retention and deletion policy are out of scope. If no reliable cross-agent enforcement point exists, document the evidence and retain the shared instruction gate as the smallest safe mechanism.

## Evidence

- The personal-project rule previously allowed push and PR creation after an explicit request, which conflicted with the later operator-only remote boundary for personal and pet projects.
- A shared GitHub PR skill provided remote commands but had no project-scope gate before those commands.
- Local branch inspection showed the active checkout on its local `main`; the isolated branch named in the earlier closeout record was not a local branch. The workflow proceeded to remote PR operations instead of stopping at local state and handing the remote step to the operator.

## Acceptance

- The investigation inventories supported agent hooks and Git/GitHub command boundaries, with evidence for each proposed enforcement point and a clear finding on whether a portable guard is feasible.
- The recommended guard blocks remote reads and writes for personal/pet scope, permits local Git operations, and does not block company workflows covered by their own rules.
- Unknown scope fails closed before remote access.
- If a reliable guard is feasible, regression checks cover `fetch`, GitHub CLI reads, PR creation/merge, push, and remote branch deletion, alongside permitted local status, diff, commit, and test operations. If not, provide a concrete evidence-backed explanation and preserve the operator handoff rule.
- The investigation does not propose branch-name-based cleanup or change branch retention/deletion policy.
