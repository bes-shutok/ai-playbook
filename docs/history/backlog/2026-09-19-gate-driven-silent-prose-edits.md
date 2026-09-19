# Backlog: no silent gate-satisfying rewrites of human-authored prose

Captured: 2026-09-19 (source: cross-session friction audit - user-correction mining over 1,776 typed prompts, 2026-07-17 → 09-19)
Status: open
Priority: medium

Workflow: backlog

## What was witnessed

Witnessed 2026-07-21 (tax-reporting): the done sub-agent silently rewrote 58 lines of the user's plan prose (em dashes → semicolons) to satisfy `check-no-em-dash.sh`; the user caught it, restored the pristine plan, and corrected: "YOu shouldn't have done it. The done agent was doing it's job." Plus ~8 correction-class prompts in the same family: unrequested edits needing revert ("stop execution and rollback changes", "I asked to review 'uncommitted changes' why did you started review ahgainst main"), i.e. defaults overriding narrower user intent.

The mechanical half (the em-dash checker lacks an insertion-scoped mode) is already tracked in 2026-09-16-em-dash-insertion-scope-check; this item is the complementary behavioral contract, which applies to every current and future prose gate.

## Suggested fix

A minimal-diff/no-silent-reformat pin in the done and implement worker contracts: when a gate can only be satisfied by rewording or reformatting human-authored prose, the worker must not rewrite it wholesale - it makes the narrowly-scoped insertion the gate actually requires, or stops and surfaces the conflict (returned-for-ask shape) for the user to adjudicate. Whole-file rewording of user-authored text is out of scope for any worker, always.

## Acceptance

- The done and implement contracts carry the pin.
- A deliberate probe (a gate that only passes by rewording human prose) halts for ask instead of editing.
- Zero new "why did you rewrite my text" corrections in the next corrections-mining pass.
