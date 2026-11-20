# Backlog: disambiguate the two policy referents in execute-plan-stack step 7

Driving force: consistency

## Summary

agents/skills/execute-plan-stack/SKILL.md step 7 records "policy source and resolved target/maximum/exclusions" (the PR-size policy) and "the boundary's policy-qualified validation sets" (the suite policy) in one record-field sentence. The field groupings disambiguate, but an executor recording fields could conflate the two policies.

## Evidence

Witness: the execute-plan-project-test-policy-scope Phase 3 consistency+correctness panel (2026-11-09, branch 2026-11-09-execute-plan-test-policy-scope).

## Expected behavior

The first field group names its policy explicitly ("PR-size policy source").
