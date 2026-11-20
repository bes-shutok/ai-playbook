# Plan: corrections-writer distinct-session dispatch gap

Backlog origin: docs/history/backlog/2026-11-12-corrections-writer-distinct-session-dispatch-gap.md
Authoring claim: 2026-11-12-corrections-writer-distinct-session-dispatch-gap.md (session sess_02508ebf-e149-462b-b45e-07c5cbaed6aa)
Driving force: automation
Plan review record: the staging series .ai-playbook/reviews/2026-11-13-plan-review-corrections-writer-distinct-session-dispatch-gap-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.5h total, largest task 0.5h
Executed: yes (interactive stale-claim takeover resume 2026-11-19; branch tip e93c93a42 pre-squash)

## Terms

- spawn recipe: the fixed writer payload a blocked authoring session hands to a distinct interactive session: identity registration through the shared session-channel helper's explicit input, the exact `record_correction_authorization` invocation (row path, verbatim operator direction, artifact path), and the verbatim RESULT/DETAIL report.
- direction of record: the operator direction text already recorded in the correction row's receipt; the relayed direction must equal it, the receipt-directive equality guard being the binding witness.
- same-identity refusal: the `record_correction_authorization` refusal raised when the writer session identity equals the row's `author_session_id`.
- spawn arm: the Recovery steps 3-4 workaround route this plan adds for that refusal class.
- writer guards: the row-digest binding, the receipt-directive equality, the distinct-writer refusal, and the atomic-replace read-back in `scripts/corrections_record.py`.

## Why

The corrections chain's separation of duties is enforced at the writer, but no skill text encodes how a blocked authoring session dispatches the distinct writer session its own sanction requires. Every operator-acked plan-family cap-closure therefore re-pays one operator hand-spawn with a hand-composed recipe, and the operator becomes the integration glue the loop should own.

## Gist & Examples

TLDR: the distinct-writer spawn recipe enters self-heal Recovery steps 3-4 and two contract surfaces point at it as the operator-acked route's completion path, so the loop spawns its own corrections writer instead of paying an operator hand-spawn (driving force: automation).

Before: an authoring session whose plan-review loop reaches a terminal fold the delta classifier refuses stands at the cap-closure boundary holding the recorded operator direction, and every route to the required `correction_authorizations` append is closed: appending itself is refused by the same-identity guard, a scheduled child is forbidden by the writer sentence, and no rule binds the runtime's session-creation primitive to this route. The 2026-11-12 witness: the operator hand-composed a one-shot writer prompt and spawned the session by hand.

After: self-heal's Recovery steps 3-4 classify the same-identity refusal and carry the authorized spawn arm; the blocked session spawns the distinct interactive session with the fixed payload, the spawned writer appends the authorization under its existing guards, and the blocked session re-runs its refused verification and continues. The state-file writer sentence and the plans graded-fold route name the same completion path, so every surface that describes the route describes one route.

## Outcome

A blocked authoring session completes the operator-acked corrections route itself, without an operator hand-spawn, under the writer's existing guards.

- The same-identity refusal class has an encoded, authorized workaround route in self-heal Recovery steps 3-4.
- The state-file writer sentence and the graded-fold operator-acked route both name the spawn recipe as the route's completion path; the state-file pointer composes with the open residues row's trust-qualifier work on that sentence.
- No writer guard, schema field, gate, validator, or automation primitive changes; the scheduled-workflow exclusion stands unchanged.

Gate delta: none; no gate, validator, lock, ledger, fence, schema field, refusal surface, or dispatch-pausing condition is added or removed (the same-identity refusal, the scheduled-workflow exclusion, and every writer guard stand unchanged); the additions are prose-only recipe text and two pointers, so no gate-liveness citation is owed.

## Assumptions

- assume the direction relay is verbatim relay from the direction of record, the receipt-directive equality guard being the binding witness; basis: the origin row's Expected section.
- assume the spawned session is a live interactive session, not a scheduled workflow, so the writer sentence's "scheduled workflows never invoke it" clause composes unchanged; basis: the origin row's Expected section and the writer sentence's own semantics.
- assume the runtime's session-creation primitive exists and the recipe binds it to this route only, never as a new automation primitive; basis: the origin row's Problem item 3.
- assume the spawn arm routes the writer identity through the session-channel helper's explicit input, so the recorded writer_session_id is workflow-compliance evidence, never an enforced boundary against a process controlling its own environment; basis: the open residues row's residue 4 owns the strength qualifier (this plan adds no trust wording) and the writer guards are the binding controls.
- assume the relay question (who carries the direction) is settled by the verbatim-relay rule above; basis: the origin row's Expected section settles it in text.

Decision points requiring a grill: none remain.

## Standing constraints

- Byte-budget posture: `agents/skills/maintenance/state-file.md` sits advisory-over its pilot target; every touched skill file prices through the repo-wide byte-budget gate (`python3 scripts/skill_text_budget.py --check`, blocking posture, exit 0 required), and growth past a cap deletes equivalent bytes in the same change.
- Anti-growth rule: operative text cites the 2026-11-12 incident in at most one line; the dossier lives in the origin row.

## Evaluation Criteria

**Quality dimensions:**
- guard preservation: `scripts/corrections_record.py` byte-unchanged; the focused corrections suite green.
- surface alignment: the state-file pointer and the graded-fold reference name the completion path without restating the recipe; the recipe text lives only in the self-heal spawn arm the plan writes (Task 1) and nowhere else.
- exclusion intact: the "scheduled workflows never invoke it" clause survives byte-identical in the writer sentence.

**Done when:**
- self-heal Recovery steps 3-4 carry the same-identity refusal class arm with the spawn recipe and the step-4 verification.
- the state-file `correction_authorizations` writer sentence carries exactly one completion-path pointer.
- the graded-fold operator-acked route names the same completion path by reference.
- the pins suite, the public hygiene scan, the em-dash gate, and the byte-budget gate all exit 0.

**Ship when:**
- nothing external; every check is repository-verifiable.

## Disposition of executed work

Tasks 1-3 executed on branch 2026-11-18-corrections-writer-distinct-session-dispatch-gap (Task 1 by the original codex run, Tasks 2-3 by the 2026-11-19 takeover resume). Phase 3 execution review round 1: 1 High (plan-artifact duplication from a progress-mark scripting bug; repaired in e93c93a42) + 1 Medium (rebase-carriage duty against the landed self-heal step-4 rewrite; carried by the rebase onto main with the corrections sentences inserted into the rewritten steps 3-4, the user-override sub-bullet preserved) + 2 Low (RESULT/DETAIL format is a recipe-defined convention; the plan-quality-gate clause is broader than the arm's classification condition, both recorded here, no backlog rows owed: the first is plan-faithful inherited vocabulary, the second matches the plan's own Task 3 spec wording). Gates post-rebase: byte-budget exit 0, hygiene exit 0, em-dash exit 0, writer suite 92 passed, spawn-recipe loop 3/3.


## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Skill text (this plan's only edit surface):**
- `agents/skills/self-heal/SKILL.md` (Task 1)
- `agents/skills/maintenance/state-file.md` (Task 2)
- `agents/skills/plans/plan-quality-gate.md` (Task 3)

**Tests:**
- `scripts/test_corrections_record.py` (review-only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/corrections_record.py`; reason: the writer guards are unchanged by design (arm 4), and any edit there is a contract breach this plan's own Review Scope rejects.
- `scripts/session_channel.py`; reason: the identity helper is consumed as-is; the recipe registers its explicit input, never edits it.
- `docs/history/backlog/2026-10-21-corrections-contract-doc-residues.md`; reason: the residues row's residue 4 lands on the same writer sentence as that row's own work; this plan cites the composition and absorbs none of it.

## Validation Commands

```bash
# writer untouched: expect empty diff for the corrections writer
git diff main --stat -- scripts/corrections_record.py
# the scheduled-workflow exclusion survives byte-identical
grep -c "scheduled workflows never invoke it" agents/skills/maintenance/state-file.md
# each edited surface names the spawn recipe as the completion path (per-file assertion, not a single-hit count)
for f in agents/skills/self-heal/SKILL.md agents/skills/maintenance/state-file.md agents/skills/plans/plan-quality-gate.md; do grep -q "spawn recipe" "$f" || { echo "missing spawn recipe: $f" >&2; exit 1; }; done
# added-lines em-dash gate
bash scripts/check-no-em-dash.sh added-lines --base main
# writer guards suite green (guards untouched, suite still passes)
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_corrections_record.py -q
# mechanical gates
python3 scripts/skill_text_budget.py --check
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
```

### Task 1: self-heal Recovery steps 3-4 gain the same-identity spawn arm

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/self-heal/SKILL.md`

Primary class anchors:
- `record_correction_authorization` in `scripts/corrections_record.py`

- [x] Recovery step 3's refusal classification names the corrections-route same-identity refusal class and its authorized workaround: the blocked session, holding the recorded operator direction, spawns the distinct interactive session whose payload is the fixed spawn recipe [class: IMPLEMENTATION_REQUIRED]
- [x] The spawn recipe payload the task writes into self-heal is pinned verbatim in this plan (authoring-time spec, never the recipe's durable home): identity registration through the session-channel helper's explicit input; the exact `record_correction_authorization` invocation with row path, verbatim direction, artifact path; the verbatim RESULT/DETAIL report [class: IMPLEMENTATION_REQUIRED]
- [x] Recovery step 4 carries the verification: after the spawned writer reports RESULT OK, the blocked session re-runs its refused verification before continuing dependent work, and the relay rule is stated once: the direction is relayed verbatim from the direction of record, the receipt-directive equality guard being the binding witness [class: IMPLEMENTATION_REQUIRED]
- [x] Every writer guard, the scheduled-workflow exclusion, and the state schema are cited by reference and restated nowhere; the incident is cited in at most one line [class: REPOSITORY_TEST]
- [x] Run the writer-guard suite green (the writer is untouched; the suite proves the guards intact): `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_corrections_record.py -q` [class: REPOSITORY_TEST]
- [x] Price the Task 1 growth against the byte-budget gate (self-heal carries no caps entry today; the gate's advisory ratchet row is a growth-watch signal, never a blocking input) [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `feat: self-heal gains the corrections-route distinct-writer spawn arm` [class: IMPLEMENTATION_REQUIRED]
### Task 2: the state-file writer sentence gains the completion-path pointer

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/state-file.md`

Primary class anchors:
- `correction_authorizations` in `agents/skills/maintenance/state-file.md`

- [x] The `correction_authorizations` field paragraph's writer sentence gains exactly one pointer naming the self-heal spawn recipe as the route's completion path, composing with the open residues row's trust-qualifier clause that lands on the same sentence; no trust wording is edited (residue 4 stays that row's own work) [class: IMPLEMENTATION_REQUIRED]
- [x] Price the Task 2 growth against the byte-budget gate: any growth past a cap deletes equivalent bytes in the same change, the gate's breach report being the record [class: IMPLEMENTATION_REQUIRED]
- [x] Run the mechanical gates green (pins suite, byte-budget check) over the touched file [class: REPOSITORY_TEST]
- [x] Commit: `feat: state-file correction_authorizations writer sentence points at the spawn recipe` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the graded-fold operator-acked route names the completion path by reference

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/plan-quality-gate.md`

Primary class anchors:
- `record_correction_authorization` in `scripts/corrections_record.py`

- [x] Rule 2's operator-acked route sentence gains one clause naming the self-heal spawn recipe as the route's completion path by reference, with no recipe restatement and no change to the route's verification chain; the clause adds no trust wording and claims no co-landing of residue 4's qualifier (the residues row's Expected scopes that qualifier to the state-file paragraph alone; residue 4 stays that row's own work) [class: IMPLEMENTATION_REQUIRED]
- [x] Run the byte-budget check green over the touched file [class: REPOSITORY_TEST]
- [x] Commit: `feat: graded-fold operator-acked route cites the spawn recipe completion path` [class: IMPLEMENTATION_REQUIRED]
