Status: done (2026-09-30; executed+landed squash main e9f35bba via docs/history/plans/completed/2026-09-30-plans-sut-naming-authoring-rule.md)
Priority: high
Origin class: learned-skill-defect (plans skill Validation Commands authoring rules; witnessed 2026-09-28, execute-plan-codex-worker-terminal-recovery plan review rounds r2-r4)

# plans Validation rules lack a system-under-test naming rule for wrapper-converted results

## Which skill and step

`agents/skills/plans/SKILL.md`, `## Validation Commands (authoring rules)` (rules 1-40) and the test-item format rules; review-plan's panel catalogs have no matching lens pattern either.

## Observed versus expected

Observed: a plan pinned a test expectation ("reconcile returns `available` with the worker active") without naming the layer under test. The codebase has two layers at that seam: the pure reducer returns `available`, while the driver wrapper structurally cannot (it downgrades any available result to a `capacity-live` refusal whenever an active worker holds a live capacity entry). Three full review rounds (r2-r4 of the witness plan) re-derived the same defect in different words - unreachable fixture, dead guard code, unfalsifiable canary - before the plan pinned the system under test explicitly and added a companion driver-layer assertion for the wrapper's actual outcome.

Expected: a plans authoring rule that, whenever a behavior is observable at two layers (pure reducer versus wrapper that post-processes or downgrades the reducer's result), each test item names the system under test, and each wrapper-level expectation states the wrapper's actual post-conversion outcome (with the reducer-level pin as a green-at-RED regression pin where today's code already produces it).

## Environment

Runtime: ZCode, macOS; repo copy is the runtime source. Date: 2026-09-28. The witness plan's r2 F4, r3 F1/F4, and r4 F1 (five staged findings across four workers in three rounds) all trace to this one missing authoring rule.

## Suspected root area

The existing rules cover task-coupling (rule 25) and whole-tree gate states (rule 21) but not layer-pinned expectations; nothing in the test-item format ("given X, expects Y") requires naming WHERE the behavior is observed when a wrapper sits between the tested unit and the outcome.

## Suggested fix

Add one authoring rule to the Validation Commands section (next free number): when a wrapper transforms or can veto a lower layer's result, every test item names its system under test; the wrapper's post-conversion outcome gets its own named assertion, and any reducer-level expectation that today's wrapper already satisfies is labeled a green-at-RED regression pin rather than a RED target.
