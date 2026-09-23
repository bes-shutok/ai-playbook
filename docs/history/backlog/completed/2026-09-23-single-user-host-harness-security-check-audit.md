# Backlog: harness security-motivated checks audit for a single-user host

Status: superseded (2026-09-23; consolidated into docs/plans/2026-09-23-ai-harness-friction-audit.md)
Priority: high
Workflow: backlog
Source: user directive 2026-09-23 (Andrey, this repo): "I am using this laptop alone and I don't expect and should not really check if anyone else can cause some harm. That should be out of scope for the ai-playbook." Limitations, checks, and extra security introduced into the AI harness and skills "for the sake of security" are slowing the work (especially parallel changes to the same project) and sometimes make progress impossible.
Severity: High (agent work becomes unreliable, laggy, and flaky after the security and formal checks were introduced; parallel execution on one project is the worst case and is occasionally fully blocked)

## Problem

The harness and skills accumulated confirmation gates, verification layers, witness requirements, lane guards, claim files, hygiene scans, and defensive checks justified by "security reasons" that assume a hostile actor on the host. This host has a single user; that threat model does not apply. The checks tax every run: more tool-call round trips, more gates that can misfire, more cross-session state that parallel work must respect, more places where a flaky check blocks legitimate progress. The user is NOT asking to weaken security of produced code (product code review keeps its own bar; myrepos projects carry minimal security concerns anyway, per the user). The target is the harness's own process machinery.

## What it should become

1. Inventory: sweep the harness (skills, hooks, scripts, validators, plan and execution review gates) for checks whose stated or effective justification is host security or distrust of the agent's own actions, as opposed to correctness of produced artifacts. Candidates to verify, not a confirmed list: authoring claim files and lane-occupancy guards, budget-guard hook enforcement, dispatch collision-avoidance state, hygiene scans as hard gates, witness and verification receipt requirements, confirmation gates that re-ask what a single user already decided.
2. Classification: each inventoried gate is classed (a) still warranted on a single-user host because it catches real agent mistakes (correctness class, stays), (b) hostile-actor assumption, removable, or (c) real risk but over-enforced, demoted from hard gate to advisory note.
3. Removal plan: class (b) removed and class (c) demoted, each with a one-line reason; guidelines gain a rule that harness checks must justify themselves against the actual threat model (single user, trusted host) and agent-workflow reliability outranks process safety machinery.
4. Regression guard: harness-authoring work must state its threat model; security-flavored additions on this host need the same justification or they are rejected at review.

## Grill points

Where the security-versus-correctness line sits per gate (a misfiring correctness gate that blocks parallel work may still be class (c), not (b)); whether hygiene scans stay hard gates given their motivation is publication safety of the public repo, not host security; whether this directive also relaxes product-code security deferral on myrepos (user hint: "much less security concerns if any at all") or only harness machinery; whether the fix is one plan family or a batch of per-gate removals; how this reorders the in-flight verification-hardening work on the runtime reconciliation branch, which adds further execution-time checks.

## Overlap note (2026-09-23)

A peer session owns an overlapping plan on branch `2026-09-23-agent-harness-friction-audit` (worktree `~/.codex/worktrees/ai-harness-audit-plan/ai-playbook`): `docs/plans/2026-09-23-ai-harness-friction-audit.md` ("Reduce AI Harness Stops and Friction"), which records the same user decision ("remove controls whose sole purpose is malicious co-user defense") and adds a completed 30-day evidence inventory. This origin stays open as the durable carrier of the 2026-09-23 directive in case the peer branch strands; the first surface to land owns the audit, and the loser folds into it as a duplicate. Do not author a third plan for this scope.
