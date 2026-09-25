# Backlog: loop_mode non-enum value divergence between recipe gate and Step 3 enforcement

Status: open
Priority: medium
Urgency remark: witnessed: real divergence between the live recipe gate and Step 3 enforcement on a mistyped loop_mode
Promoted: 2026-09-26 from docs/history/backlog/deferred/ under the direction triage (source class: self-serving witnessed defect)
Driving force: primary correctness (a mistyped mode value makes the parent prompt carry a lane restriction that Step 3 enforcement does not implement, so prompt and lane decisions disagree on the same state); secondary consistency (a reviewer cannot trace the behavior to one owning paragraph, violating the plan's correctness criterion).
Origin: code review r1 of docs/plans/2026-09-21-scheduler-maintenance-state-durability.md, staging doc docs/reviews/2026-09-21-scheduler-maintenance-state-durability-code-review-r1.md, finding F9 (Medium, non-blocking; moved to overflow per the per-worker non-blocking budget; merged from contract-docs consistency#loop-mode-nonenum-divergence + correctness-completeness quality#non-enum-loop-mode-admitted-by-predicates).

zcode.md's recipe gate reads "non-dual and non-null" (negation-active: any string fires the appendix), while SKILL.md Step 3 defines excluded lanes only for the two named modes (whitelist semantics: an out-of-enum value resolves nothing) and the field paragraph defines no out-of-enum behavior. A typo like `authoring_only` satisfies the recipe gate, so the parent is repaired with an appendix built from a garbage mode while the turn's lane resolution for the same value is undefined.

Candidate fix: add one fallback sentence to the loop_mode field paragraph or the Step 3 enforcement ("a mode outside the enum is treated as null until corrected, and a turn observing one records a turn_error naming the invalid value"), and reword the recipe gate to name the two active modes (or add an enum check at the write site) so both surfaces reject the same values.
