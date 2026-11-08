# Backlog: harvest-export plan certification residuals

Status: open
Workflow: backlog
Priority: low
Origin class: plan-review residual
Class: fix-class
Driving force: code-quality

## Problem and evidence

The r5 certification round of `docs/history/plans/2026-11-07-session-rollout-retention-postmortem-evidence.md` (plan bytes sha256 782088cdb6aa111ab6e97d3209abceed27d0c798f83ea21a6c4f4b9e36a12ccc) staged no blocking finding and routed six non-blocking findings to overflow. Each premise was re-verified from disk before routing:

1. Evidence-dir lifetime (Medium): Task 1 says the docs/tmp retention machinery governs the evidence dir's lifetime, but `scripts/done_sweep_gates_lib.py` defaults `DOCS_TMP_DRAIN_ARMS_DEFAULT = "report-only"`, `.ai-playbook/facts.md` sets no `docs_tmp_drain_arms` knob, and no drain surface names a harvest evidence dir, so exported rollouts accumulate per cycle with no deletion duty.
2. Unexportable-locator arm (Medium): Task 1's locator item records telemetry-only outright when no rollout locator resolves, skipping the durable-store consult that the Terms, the degraded-posture item, and the Outcome make the gate for telemetry-only.
3. Runtime-neutral indirection (Low): `agents/skills/maintenance/decisions.md` names no runtime overlay by file (zero `zcode` hits) and routes runtime specifics through "the runtime overlay"; the plan has the duty text name `zcode.md` and carry a runtime-specific tilde literal.
4. Harvest outputs undefined (Low): Outcome, Task 1, and Ship-when record per-session outcomes in "the harvest's outputs" without naming the surface (for example the cycle-closing turn's `decision_reason`).
5. Header series glob (Low): the plan header's review-record glob omits the `-pc38c23e6-` identity infix and fixes a 2026-11-07 date prefix, so the literal pattern matches no file.
6. Review-round jargon (Low): the Done-when bullet says "at the r4 fold" and "at the r4 rebase", review-round vocabulary used in the readability range without a Terms entry.

## Correction

At plan execution, the executor folds items 1-4 into the decisions.md edit: a bounded lifecycle sentence for the evidence dir (removed once the read legs finish, or drained at the next harvest start) or an honest report-only posture; the unexportable arm routed through the same store-then-residual duty; the overlay referenced as "the runtime overlay's proxy-locator bullet"; and the record surface named. Items 5-6 are plan-text wording, fixed through the normal plan edit and review lifecycle; never silently mutate certified bytes.

Dedup probe: searched open backlog for harvest, rollout, evidence dir, docs_tmp_drain_arms, and proxy-locator; the only related open rows are the origin row (`docs/history/backlog/2026-11-05-session-rollout-retention-postmortem-evidence.md`, which this plan covers) and the docs/tmp retention strand row (`docs/history/backlog/2026-11-02-docs-tmp-retention-redesign-strand-resumption.md`, which owns drain-arm posture, not the harvest's own lifecycle sentence).
