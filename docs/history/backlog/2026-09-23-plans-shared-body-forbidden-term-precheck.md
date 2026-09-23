# Backlog: plans authoring pre-check for shared-body forbidden-term gates

Status: open
Priority: high
Workflow: backlog
Date: 2026-09-23
Origin: P37 execution (learn Step 1.8 skill-usage issue)

## Skill and step

agents/skills/plans/SKILL.md, Documentation Impact Assessment / Validation Commands authoring rules; interacting gate: runtime-neutrality shared-body test (scripts/test_execute_plan_runtime.py test_shared_skill_bodies_remain_runtime_neutral in consumer repos) that forbids terms like JSONL in shared skill bodies.

## Observed vs expected

A plan prescribed exact prose insertions containing `context.jsonl` path literals into a shared skill body (execute-plan SKILL.md). The consumer repo's runtime-neutrality test forbids the term JSONL (case-insensitive) in that body, so the mid-run full suite went RED on a plan-prescribed, digest-frozen insertion, and the executor had to widen a frozen test file (plan-related regression repair). Expected: plan authoring catches this before certification.

## Reproduction

1. Repo has a shared-body forbidden-term scan over skill markdown.
2. Author a plan whose prescribed insertion text includes a filename containing a forbidden term (e.g. `<x>.jsonl` vs forbidden `JSONL`).
3. Execute: mid-suite RED at the first full-suite run; frozen test file must be amended out of declared scope.

## Suspected root area

plans authoring rules lack a pre-certification step: sweep each prescribed literal insertion into shared bodies against the consumer repo's shared-body forbidden-term gates (grep the scan's term list) and either reword the prescribed text or declare the gate amendment in the plan's Review Scope.

## Environment

ZCode runtime, 2026-09-23, repo copy of skills.
