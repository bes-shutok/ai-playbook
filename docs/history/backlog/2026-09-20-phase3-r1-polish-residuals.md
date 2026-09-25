# Backlog: phase 3 r1 polish residuals (tests, prose, script)

- **Status:** open
Priority: medium
Urgency remark: witnessed: fail-open on the live added-lines gate, a typo'd path reads CLEAN (verified empirically at discovery)
Promoted: 2026-09-26 from docs/history/backlog/deferred/ under the direction triage (source class: self-serving witnessed defect)
- **Origin:** execute-plan phase 3 code review r1 (testing + design + contract-docs lenses, 2026-09-20), staging doc findings 9, 11, 12, 13, 14, 15, 16, 18

## Findings

1. added-lines with a typo'd/nonexistent path argument yields an empty `git diff` with exit 0 and reads as CLEAN (verified empirically); git exit >= 2 aborts, but exit-0-with-no-matches is indistinguishable from clean. Candidate: warn or fail on a pathspec matching no tracked file.
2. No negative arm rejects an unknown claim state string through `validate_manifest`; adding `waiting-capacity` grows an unguarded closed set. Add a junk-state rejection witness.
3. `_park_waiting_capacity_locked` re-implements `_apply_blocked`'s task-persist block + worker-blocked history append verbatim (divergence trap if RESUMABLE_REASONS ever changes); parameterize the shared blocked-persist tail with a claim state.
4. The at-least-one-task-heading predicate is inlined at two mirror sites (terminal gate, readiness plan-shape guard) with separate evidence strings; share one predicate to keep the mirrors from drifting.
5. The CD5-2 edit re-emitted an envelope-level paragraph flush-left, terminating the decision bullet list mid-section in runtime-contract.md (:792 region); a two-space re-indent restores the structure.
6. `added-lines --base=REF` (long form) and the `--` pathlist separator are implemented but absent from the usage text, the plan, and any test.
7. The driver-emitted recovery action literal `resume-same-claim` appears nowhere in the contract (only a paraphrase in the Transition table's capacity row); consumers keying on recovery-action values cannot find it documented.
8. The bounded-read missing-file refusal fragment gained a `: {exc}` suffix (Task 5 said "keep the refusal fragments"; additive, tests pin the stable substring), and the helper docstring's numbering note is half-true: leading blank lines DO shift numbers because text is stripped once (trailing half is accurate). Fold into [[2026-09-20-bounded-read-pin-hardening]]: align docstring wording and decide whether the fragment change is sanctioned.

## Driving force

Each is a small divergence between what a surface claims and what it does (usage text, docstring, contract, shared code shape); cheap now, confusing later.
