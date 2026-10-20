# Backlog: done dirt-regression gate blocks a valid correction

- **Filed:** 2026-10-20 (local closeout recovery)
- **Status:** open
- **Priority:** high
- **Workflow:** backlog
- **Origin class:** observed done pre-commit gate conflict
- **Class:** fix-class
- **Driving force:** reliability
- **Skill/step:** `agents/skills/done/SKILL.md` Step 3; `scripts/done_run.sh` commit stage; `scripts/dirt_regression_gate.py`
- **Environment:** local developer checkout, repository copy of the done runner, 2026-10-20
- **Suspected root area:** dirt-regression classifier cannot distinguish a legitimate correction from an accidental restoration of prior text

## Observed vs expected

Observed: the done commit gate refused a user-directed contract correction because edited files contained base-era text over lines the branch had gained since its comparison base. The correction spans several contract-bearing files, so reducing it to one isolated fixture would not complete the requested work. The refusal left the authorized changes staged and blocked the ordinary closeout.

Expected: the gate distinguishes an accidental reversal from a necessary correction while preserving the existing protection against unintended restoration.

The existing one-path authorization for an ancestor-matching staged blob belongs to the cached-diff guard. It does not address the separate dirt-regression refusal. Do not treat it as permission to bypass that later guard.

## Evidence

- The closeout reported `dirt REGRESSION` for a set of files covering an API schema, a migration, tests, and an RFC; each finding said the change restored base-era text over lines gained since the comparison base.
- The same closeout's work was a user-directed correction to make identifier prefixes consistent across the persisted, API, and documented contracts; the issue was not an unreviewed speculative cleanup.
- `scripts/dirt_regression_gate.py` owns the classifier and `scripts/test_dirt_regression_gate.py` its behavior witnesses.
- `scripts/done_run.sh` runs the dirt-regression gate after the cached-diff guard; the documented cached-diff path/blob authorization is scoped to that earlier guard.
- `docs/history/backlog/2026-10-05-done-dirt-regression-blocks-reviewed-fix.md` records a prior report reclassified as a false positive because the proposed code removal was not behaviorally necessary. That closed case does not establish that this separate contract correction is invalid, and it is a reason to examine the actual classifier before changing or removing it.

## Scope to resolve

Determine whether the dirt-regression gate still prevents a distinct, evidenced harm after the other closeout guards, or whether its origin should be removed or simplified. Trace its introduction, current protections, and exact refusal shape. Compare removal, narrowing or simplifying the classifier, and retaining it with an in-scope recovery path that does not bypass validation. Preserve protections that have independent incident evidence. Do not edit or bypass the gate during the closeout it refused.

## Expected

Recommend the smallest evidence-backed disposition for the gate, including whether its origin should be removed or simplified. If retaining it, define how a genuinely necessary, user-directed correction can pass the same integrity checks without an arbitrary behavior-preserving edit. Add only the regression witnesses needed to distinguish an accidental reversal from a valid contract correction. Do not add a new gate, standing approval ceremony, or persistent authorization.

## Alternatives to assess

- Remove the gate: consider only if the archaeology shows its protection is redundant with existing guards and no independent harm remains; otherwise this would discard the existing accidental-regression protection (`agents/skills/done/SKILL.md`, Step 3; `scripts/done_run.sh`, commit stages).
- Keep the gate unchanged and require every valid correction to be reshaped: rejected as the default pending investigation because this closeout demonstrates the refusal can cover a cross-file contract correction, while a representation-only workaround adds unrelated churn and leaves the same blocker (`scripts/dirt_regression_gate.py`, classifier output).
- Add a new persistent exception, bypass switch, or approval ceremony: rejected because no such mechanism is needed to test whether the existing classifier can be simplified, and it would grow blocking machinery before the gate's distinct value is established (`AGENTS.md`, Machinery admission protocol).
- Narrow or simplify the classifier: candidate only if its introduction evidence and current tests identify a smaller protection that catches the original harm while permitting valid changes; do not assume this is safe without reproducing both classes (`scripts/test_dirt_regression_gate.py`).

## Source

- Observed 2026-10-20 during a done closeout of a user-directed identifier-contract correction.
- Reassess alongside the closed prior incident at `docs/history/backlog/2026-10-05-done-dirt-regression-blocks-reviewed-fix.md`.
