# Plan: RFC SOT writeability preflight

Backlog origin: docs/history/backlog/2026-09-30-rfc-sot-writeability-preflight.md
Driving force: automation
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-rfc-sot-writeability-preflight-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Investigation receipt (the origin's Trigger)

The origin directs promoting through investigate and plans before any shared-skill change. The investigation (run in this authoring session against the four surfaces the origin names) concluded:

1. `rfc-design` Edit mode (SKILL.md "Edit mode (mandatory)" and the mode table) requires reading the skill and the editing checklist before an edit, but never resolves the document's registry state or the validator's writeability for the path - the first edit attempt is the discovery mechanism.
2. `scripts/doc_registry_validator.py` freezes accepted RFC bodies exactly like completed history (the registry freeze applied by `rfc-design`'s closure transition; the ADR-0001 corruption-override audit note is the only licensed edit path). That freeze is correct policy, not a validator defect.
3. `done`'s doc-registry gate guidance routes hard findings to "fix the registry row or move the change into the living SOT" without requiring evidence that the destination SOT owns the moved topics - the duplicate-contract risk the origin witnessed.
4. The witnessed incident (guidance names an RFC active while the validator blocks its body writes) is therefore an ownership-signal conflict between project guidance and the registry, and the skills route it nowhere: the fix is a preflight and a proven destination, both guidance-level; the validator and lifecycle contract need no change.

This plan implements that conclusion: a writeability preflight in `rfc-design` Edit mode and an ownership-proof clause in `done`'s remediation guidance, with the origin's three regression cases named as the routing arms.

## Outcome

An RFC edit session checks document ownership and writeability before the first edit, and a closeout that redirects content to a living SOT verifies the destination owns the topics - so a validator-blocked RFC that guidance calls active produces a recorded conflict and an explicit policy decision instead of ad-hoc edits or duplicated contracts.

- An editable living RFC passes the preflight and proceeds to the editing checklist unchanged.
- A frozen RFC with a registered successor routes to the successor document (or the closure-transition rules) instead of a doomed body edit.
- A guidance-versus-registry conflict (named active, validator blocks) stops before any edit or content move: the session records the conflict and routes it through an explicit policy decision.

Gate delta: no refusal class is added to any mechanical gate; the change adds one preflight duty and one proof clause to two skills' guidance prose (a checked-condition addition on guidance routing, priced by the origin's witnessed incident: a consumer closeout that made ad-hoc edits and had to reverse course after the ownership conflict surfaced - the completed-integrity-failure witness; the class-default alternatives are addressed by the investigation: there is no false positive to remove (the validator rejection was correct), and no simpler exit exists because today's prose has no preflight to fix, only its absence).

## Terms

- **Writeability preflight**: the Edit-mode step that resolves the RFC's registry row (state, audit note) and the validator's writeability for the path before the first edit.
- **Ownership conflict**: project guidance naming a document the active SOT while the registry freezes or blocks its body writes.
- **Proven destination**: a living SOT the registry records as owning the topics of the content being moved there.

## Assumptions

- assume the fix is guidance-level only (two skills' prose); basis: the investigation receipt above - the validator's freeze is correct policy, and the origin's Suggested fix says to implement only the minimal changes the investigation supports and to consider shared skills versus the validator contract, which the investigation resolves to shared-skills prose.
- assume `doc-hierarchy` needs no change in this plan: its active-SOT lifecycle and ADR-0001 override already describe the freeze correctly; the origin itself conditions a doc-hierarchy change on plan review confirming the mismatch at that boundary, and the investigation located the gap in the two consumers' routing, not the hierarchy contract; basis: the investigation receipt.
- assume the origin's classification is fix-class; basis: the header declares `Class: fix-class`, and the body records a witnessed ad-hoc-edit-and-reverse incident with a routing remedy.
- assume the repository's pytest-runner contract applies where tests are referenced (venv interpreter first, ambient fallback with a version guard); basis: plan `docs/history/plans/completed/2026-09-30-done-sweep-closeout-baseline-exemption.md` Task 3 (Validation).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: rfc-design Edit mode gains a writeability preflight and done's SOT-redirect remedy gains an ownership-proof clause, so ownership conflicts surface as recorded decisions instead of ad-hoc edits; the driving force is automation (the check runs before the work, not as its aftermath).

Before (today): a closeout session is told an RFC is the implementer SOT, starts the edit checklist, and discovers on the first body write that the validator freezes the document (accepted-RFC closure). It then moves behavior details into an operational guide without checking that guide owns the topics, and reverses course later. Both skills' guidance permitted every step of that path.

After (this plan): the same session's preflight resolves the registry row first: the living RFC proceeds; the frozen-with-successor RFC routes to its successor; the conflict case (guidance says active, validator blocks) records the conflict and stops for an explicit policy decision. A closeout redirect verifies the destination's ownership before moving content.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the preflight names all three routing arms (editable living, frozen with successor, conflict) and the conflict arm prohibits both edits and content moves before the policy decision; the done guidance conditions the SOT redirect on recorded ownership of the moved topics.
- regression safety: neither skill's existing checklist steps are removed or reordered; the preflight precedes the editing checklist as an additional mandatory step.
- maintainability: both amendments name the registry row fields they read (state, audit note) so a reader can re-derive the check.

**Done when:**
- `agents/skills/rfc-design/SKILL.md` Edit mode carries the writeability preflight with the three arms; `agents/skills/done/SKILL.md`'s doc-registry remediation carries the ownership-proof clause; all Validation Commands exit 0.

**Ship when:**
- Consumer runtimes pick both skills up through their normal vendored-asset sync; no further release action belongs to this plan.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/done/SKILL.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/doc_registry_validator.py` and the registry lifecycle contract; reason: the investigation receipt concludes the validator's freeze is correct policy and needs no change.
- `agents/skills/doc-hierarchy/SKILL.md`; reason: the origin conditions a change there on review confirming the mismatch at that boundary, and the investigation located the gap in the two consumers' routing.

## Validation Commands

```bash
# 1. The rfc-design preflight is wired with its three arms (dedicated pins).
grep -qF 'writeability preflight' agents/skills/rfc-design/SKILL.md || { echo "FAIL: preflight missing" >&2; exit 1; }
grep -qF 'frozen with a registered successor' agents/skills/rfc-design/SKILL.md || { echo "FAIL: successor arm missing" >&2; exit 1; }
grep -qF 'records the conflict and routes it through an explicit policy decision' agents/skills/rfc-design/SKILL.md || { echo "FAIL: conflict arm missing" >&2; exit 1; }

# 2. The done remediation carries the ownership-proof clause (dedicated pin).
grep -qF 'verify the destination registry row owns those topics' agents/skills/done/SKILL.md || { echo "FAIL: ownership-proof clause missing" >&2; exit 1; }

# 3. Em-dash gate over the branch's added lines.
bash scripts/check-no-em-dash.sh added-lines --base main || { echo "FAIL: em-dash gate" >&2; exit 1; }
```

Authoring-time gate record (rule 29/19/22): the four investigation surfaces were read on this tree at authoring time and the receipt is recorded in the Investigation receipt section. RED-today evidence, rule 19: Commands 1 and 2's three pins are absent from both files today (verified), so they fail until Tasks 1-2 land; Command 3 is the branch-wide added-lines gate. Rule 22 mechanical audit: each Validation Command pin occurs once in its owning Task's prescription beside its Command occurrence (plan-wide mentions in the Investigation receipt, Gist, and Evaluation Criteria are not pin sites); `bash -n` over this block passed.

### Task 1: rfc-design Edit-mode writeability preflight (GREEN)

Files:
- `agents/skills/rfc-design/SKILL.md`

Evidence:
- `grep -qF 'writeability preflight' agents/skills/rfc-design/SKILL.md && grep -qF 'frozen with a registered successor' agents/skills/rfc-design/SKILL.md && grep -qF 'records the conflict and routes it through an explicit policy decision' agents/skills/rfc-design/SKILL.md`; covers: the preflight and its three arms.

- [ ] In the Edit mode section, insert the writeability preflight as a mandatory step before the editing checklist: before changing an existing RFC, resolve the document's writeability by running the validator's read-only check-writes mode with a body-edit change letter for the path (or, when the validator is absent, by reading the registry row's state and audit note directly - the gate's own fail-open semantics); an editable living RFC proceeds to the editing checklist; a body frozen with a registered successor routes to that successor document (or the closure-transition rules) instead of a body edit; when project guidance names the document active while the validator blocks body writes, the session records the conflict and routes it through an explicit policy decision before any edit or content move, recording the conflict in the session log. [class: IMPLEMENTATION_REQUIRED]
- [ ] Amend the mode table's Edit row to point at the preflight: after "apply editing checklist", insert "(after the Edit mode writeability preflight below)". [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: Validation Command 1's three pins pass. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: rfc-design edit mode gains a writeability preflight` [class: IMPLEMENTATION_REQUIRED]

### Task 2: done SOT-redirect ownership proof (GREEN)

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -qF 'verify the destination registry row owns those topics' agents/skills/done/SKILL.md`; covers: the ownership-proof clause.

- [ ] Amend the doc-registry gate's hard-finding remediation: before moving a change into the living SOT, verify the destination registry row owns those topics (the registered SOT for the moved content); when no registered owner exists or the destination is itself frozen, record the conflict and route it through an explicit policy decision instead of moving content by inference, recording the conflict in the session log. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: Validation Command 2's pin passes; `bash scripts/check-no-em-dash.sh added-lines --base main` exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: done SOT redirect requires a proven destination` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Whole-plan validation gate

Files:
- `agents/skills/rfc-design/SKILL.md`
- `agents/skills/done/SKILL.md`

Evidence:
- `awk '/^```bash$/{f=1;next}/^```$/{f=0}f' docs/history/plans/2026-09-30-rfc-sot-writeability-preflight.md > "$TMPDIR/whole-plan-validation.sh" && bash "$TMPDIR/whole-plan-validation.sh"` (the block's own commands extracted and executed; the awk expression is described because the literal sequence cannot appear inside this fenced block); covers: every criterion in Done when.

- [ ] Run the extracted Validation Commands block from the worktree root; every command exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `test: whole-plan validation for the RFC SOT writeability preflight` [class: REPOSITORY_TEST]
