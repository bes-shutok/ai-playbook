# Changed window-dispatch duty clauses have no pins-suite witnesses

- **Filed:** 2026-10-29 (execute-plan Phase 3 code review r1 address pass, window-dispatch-hardening)
- **Status:** open
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** review finding (Phase 3 r1, testing + design-simplicity + risk)
- **Class:** fence-class (unwitnessed operative duty clauses lose their regression evidence silently)
- **Driving force:** reliability
- **Dedup probe:** searched open backlog filenames and bodies for pins witness, presence pin, placeholder-set pin, and mutation-verified; nearest item `docs/history/backlog/2026-10-29-payload-placeholder-set-pin-parity.md`, which owns placeholder-set pin parity and payload-directive placement across the three dispatch payload modules; this row owns duty-clause presence pins over the quota, scheduling, guards, and constant-restatement surfaces, a disjoint span set from that row's set-membership scope, so the two rows stay separate with no merge.
- **Capture hygiene:** scan-public-hygiene --files pass over this draft before landing (2026-10-29).
- **Why not fixed now:** the Machinery admission protocol refuses a mid-lane blocking pin without a witnessed catch; warning-only presence pins are the admitted remedy and belong to a scheduled maintenance pass, not this address pass.

## Problem

The changed duties' load-bearing clauses have no pins-suite witnesses. Mutation-verified by the Phase 3 testing lens (scratch-clone deletion runs, HEAD-validator-versus-tree differential; no tree writes): each clause listed below can be deleted from the working tree with every plan Validation grep and `scripts/check_maintenance_pins.sh` staying green:

- the park-arm routing sentence (quota-policy.md Step 4, the parkable-kind `pending_dispatch` routing);
- the resume clause (the window-start carrier lead of the same arm);
- the 2-hour staleness clause (the boundary probe economy in the Quota leg's opening paragraph);
- the child-side park arm (the execution payload's Boundary probe and park arm paragraph in template-execution.md);
- the spacing D3-resolution clause (scheduling.md's window distribution rule);
- the two-surface discovery sentence (scheduling.md, the automation-listing and pending-children read set);
- three of the four scheduling effort fills (the Dispatch, Unblock-dispatch, and Authoring slice effort-fill clauses; only the `{EFFORT_DIRECTIVE}` placeholder greps are witnessed);
- the cap-value spans guards `reaches 3`, zcode `capped at three`, and README `fleet cap of three` (no pin reads the value itself);
- the 95 stop threshold and the freshness constants at their restated surfaces (quota-policy.md, template-execution.md, zcode.md, survey-arms.md).

Consequence: a later retune or single-homing pass (moving the 95 threshold, retuning the freshness constant, rewording the routing) can silently land stale contradicting restatements, and no gate fails while park windows and probe cadence change behavior under the readers.

## Suggested remedy (when admitted)

Region-scoped warning-only presence pins, one pin per clause family over the owning file's region, per the Machinery admission protocol: the admission lands a registry-removal row naming the sunset and the promotion criteria, the pins stay warning-only until a true catch is recorded, and promotion to blocking happens only against that catch; no blocking pin is added by this remedy without one.
