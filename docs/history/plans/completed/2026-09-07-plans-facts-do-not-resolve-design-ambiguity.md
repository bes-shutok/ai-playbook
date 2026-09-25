# Plan: plans fact-versus-decision confidence gate

> Errata (2026-09-08, from docs/history/backlog/2026-09-07-plans-confidence-gate-plan-execution-checks.md): three r6 review residuals are folded below as in-place corrections. Execution completed 2026-09-07 without these corrections, so the backlog's certify-the-amended-digest clause is void; the corrections fix the document as a record, they do not re-open or re-certify the completed execution.

Backlog: docs/history/backlog/2026-09-07-plans-facts-do-not-resolve-design-ambiguity.md

## Terms

- **Requirements buffer**: the `{tmp_dir}/plan-requirements-<slug>.md` scratch the plans skill writes during Phase 1; input to `## Gist & Examples`; deleted at plan completion.
- **Confidence gate**: the plans Phase 1 tiering at "Unclear points, confidence gate (grill or record assumptions)" in `agents/skills/plans/SKILL.md`; low confidence routes to `grill-with-docs`, high confidence records an assumption.
- **Decision-points trailer**: the required plan-file line under `## Assumptions` carrying the grill result: `Decision points requiring a grill: none remain.` or per-point receipts; enforced by `scripts/plan_readiness.py` for plans whose latest review round is dated on or after 2026-09-08.
- **Always-renders block**: a confirmation or plan block that must render even when empty, with a literal none/none-proposed line; absence is itself a detectable violation (existing pattern: the Scope extensions block).
- **Legacy plan**: a plan whose latest review round sidecar `date` is before `DECISION_MARKER_MIN_DATE` (2026-09-08); exempt from the trailer requirement.
- **Skill-gate marker**: consent marker at `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`; the owning skill refreshes it before EVERY gated plan-file write per `agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (`python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker`, fail-loud).
- **Session key**: session id from `python3 ~/.ai-playbook/scripts/session_channel.py` (env precedence per that helper); empty after strip becomes the literal `no-session`.

## Assumptions

- assume no new skill; the fix lands in the four existing skills plus the readiness script; basis: backlog Scope line plus user scoping confirmation this session (2026-09-07).
- assume the decision-points marker lives as a trailer line in an always-rendered `## Assumptions` section; basis: the Scope-extensions always-renders precedent (plans SKILL.md Step 1.2/Step 1.4) plus backlog fix item 5 ("must not be silently omitted").
- assume the mechanical readiness check tests trailer presence and shape only, keyed to the latest review round sidecar `date` >= 2026-09-08, with legacy plans exempt; basis: the backlog's own no-retrofit exclusion ("prevention belongs in forward-looking workflow rules"), the legacy-verdict-grammar time-gate precedent, and 9 open plans (several certified and awaiting execution) that must keep passing; user confirmed via the Step 1.4 named decision point.
- assume semantic detection of "a material ambiguity is identified" stays with review-plan workers; the script never guesses ambiguity from prose; basis: `evaluate_readiness` is content-blind today and the backlog acceptance criteria split detection (review-plan) from structural refusal (readiness gate).
- assume prompt-level regression cases (all seven cases of backlog fix item 7) live as a fail-closed routing list inside plans SKILL.md beside the confidence gate, and mechanical fixtures (backlog fix item 13) join the existing `plan_readiness.py --selftest` harness; basis: no canary or regression harness exists in review-plan or review-agents (rg empty, 2026-09-07); the selftest harness with named `selftest#...` checks exists.
- assume the lifecycle-verb and generic-acknowledgement triggers extend the grilling skill's mandatory ambiguity trigger block; basis: backlog fix items 10 and 12 (their regression fixtures: item 13); the cleanup trigger at grilling SKILL.md is the established anchor shape.
- assume commits stage only the files listed in each task; a peer session works on this branch concurrently and its working-tree state evolves mid-execution (observed 2026-09-07 across authoring and review rounds: execute-plan, review-loop, and receiving-review skill edits and the returned-for-ask plan doc moved from dirty to committed, and a development_lessons.md edit appeared, while this plan was being authored); this plan never stages, commits, or reverts any file outside its task lists, and the peer committing its own files mid-execution is expected and harmless; basis: git status observations 2026-09-07.
- assume the already-landed cleanup scaffolding from f93664a (2026-09-06) is not re-implemented: the grilling cleanup scope question and the plans cleanup scope ledger plus `scripts/check_cleanup_scope_baseline.py` wiring exist; this plan only extends the ledger with per-change dispositions; basis: on-disk evidence at grilling SKILL.md "Mandatory ambiguity triggers" and plans SKILL.md "Cleanup scope ledger".

Decision points requiring a grill: none remain.

## Gist & Examples

The plans Phase 1 confidence gate can be satisfied too optimistically. In the triggering case (generic shape), the user asked to remove branch changes above a base revision that were not directly related to a named feature. The agent inspected history, the base revision, and the feature specification, identified an apparently unrelated change, and treated the classification as settled: it jumped to plan confirmation without asking the focused cleanup-scope question. The sources established facts (which commits exist, what the spec says) but did not select the decisions: which hunks are feature-owned, whether cleanup means inverse commit or history rewrite or description only, whether ignored and untracked files are preserved, and whether "directly related" covers tests, docs, and process metadata.

**Before (today):** the High-confidence tier reads "exactly one interpretation is strongly supported by repo evidence". An agent reads "the sources describe the feature in detail" as "strongly supported", records one option as a high-confidence assumption, and the decision is hidden from the user. A broad acknowledgement such as "sure" then confirms the whole batch, and an ambiguous lifecycle verb ("skip that extra code") is silently given one of three meanings (remove now, defer, leave untouched).

**After (this plan):** the gate splits fact lookup from decision resolution. A material decision point is any choice between plausible plan shapes differing in scope, ownership, boundaries, compatibility, error policy, rollout, history strategy, preservation, deletion, or validation. The per-task test asks: would another reasonable design remove, add, move, or materially change this task? If yes, the point is low-confidence regardless of source authority. Every decision point lands in a `Decision points requiring a grill` subsection that always renders in Step 1.4 (`none remain.` when clean, otherwise one-line receipts), is carried into the plan as an `## Assumptions` trailer, and is enforced mechanically: `plan_readiness.py` refuses plans whose latest review round is dated on or after 2026-09-08 when the trailer is missing or unresolved. Example: a plan reviewed 2026-09-08 without the trailer fails the gate with "missing decision-points trailer"; a legacy plan reviewed 2026-09-07 keeps passing. review-plan gains an audit duty so a plan whose tasks implement one of multiple plausible designs without a receipt is flagged even before the gate runs.

Edge cases motivating the design: factual lookups with directly observable results never grill; a design the user already explicitly selected never re-grills; the existing scope-extension hard gate stays independent and cross-referenced, not duplicated; the cleanup scope question and ledger from 2026-09-06 are reused, extended only with keep/remove/defer dispositions per candidate surface.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every backlog acceptance criterion maps to a concrete edit or fixture; the two carve-outs (no grill for factual lookups; no grill for an already-explicitly-selected design) are present in the gate text; the scope-extension hard gate text is unchanged and cross-referenced.
- mechanical verification: `plan_readiness.py --selftest` green including the new decision-marker fixture family (8 arms); every new structural obligation has its own dedicated fail-closed grep with a distinctive multi-word span; the stale-tier sweep is proven RED-today (verified: the old phrase occurs exactly once today, in the tier being replaced).
- minimality: no sidecar schema contract change (`scripts/validate_review_staging.py` untouched); no README or catalog changes (skill names and paths unchanged); no new skill; no duplication of the scope-extension gate.

**Done when:**
- Tasks 1 through 7 committed; Task 8 run end to end with no fixes needed (any fix it does need is committed to its owning file before completion); the Validation Commands block below exits 0 on the final tree; this plan's commits touched only its declared files and never staged, committed, or reverted any concurrent peer state (Task 8 invariant).

**Ship when:**
- None. The runtime scripts under `~/.ai-playbook/scripts/` are repo symlinks; consumer projects pick up the gate on their next session. No deploy step exists for this repo.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md` (edits scoped to: the confidence gate block, the new scan and regression-case blocks, Step 1.4 confirmation template and meta-rule, the plan template Assumptions line, the plan-format bullet that requires Assumptions, the Cleanup scope ledger block, the Integration Points subsections with grill-with-docs and grilling; all other regions are frozen; reject any review finding that edits them)
- `agents/skills/grilling/SKILL.md` (edits scoped to: two new trigger blocks appended after the Mandatory ambiguity triggers paragraph)
- `agents/skills/grill-with-docs/SKILL.md` (edits scoped to: one appended sentence in the plans Integration Point)
- `agents/skills/review-plan/SKILL.md` (edits scoped to: Step 1 list item 7 and the Integration Point subsection "With the plan readiness gate"; all other regions frozen)
- `scripts/plan_readiness.py` (edits scoped to: module constants and `decision_marker_problem`, one new condition in `evaluate_readiness`, one new selftest family, selftest dispatcher registration, one line in `write_clean_state` emitting the round date into the fixture sidecar)

**Tests:**
- `scripts/plan_readiness.py` `--selftest` fixture family `selftest#decision_marker/*` (new; same file as production code)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`; reason: owned by the peer returned-for-ask plan work (its committed or dirty state may move during this plan's execution); execute-plan stays unchanged by design (it never re-opens settled plan decisions)
- `agents/skills/review-loop/SKILL.md`; reason: same peer ownership; untouched by this plan regardless of its committed or dirty state
- `docs/plans/2026-09-04-returned-for-ask-semantics.md`; reason: peer-owned plan doc; its state may move during this plan's execution
- `scripts/validate_review_staging.py`; reason: the sidecar schema contract is intentionally untouched
- `README.md` and `projects/.ai-playbook/agent-runtime-layout.md`; reason: skill names, paths, and catalog entries are unchanged by this plan

## Validation Commands

```bash
set -e
cd "$(git rev-parse --show-toplevel)"
P=agents/skills/plans/SKILL.md
G=agents/skills/grilling/SKILL.md
D=agents/skills/grill-with-docs/SKILL.md
R=agents/skills/review-plan/SKILL.md
V=scripts/plan_readiness.py

# Mechanical gates (behavioral truth)
python3 scripts/plan_readiness.py --selftest
python3 scripts/validate_review_staging.py --selftest
bash scripts/check-no-em-dash.sh file "$P" "$G" "$D" "$R" docs/plans/2026-09-07-plans-facts-do-not-resolve-design-ambiguity.md
bash scripts/scan-public-hygiene.sh

# Dedicated obligation pins (one grep per obligation; distinctive spans; fail-closed)
grep -qF "Facts versus decisions (gate dividing line):" "$P" || { echo "MISS: fact-vs-decision divider"; exit 1; }
grep -qF "would remove, add, move, or materially change that task" "$P" || { echo "MISS: per-task materiality test"; exit 1; }
grep -qF "do not grill a design the user has already explicitly selected" "$P" || { echo "MISS: already-selected carve-out"; exit 1; }
grep -qF "Decision-ambiguity scan (mandatory before Step 1.4):" "$P" || { echo "MISS: ambiguity scan"; exit 1; }
grep -qF "Confidence-gate regression cases (fail-closed routing):" "$P" || { echo "MISS: regression cases"; exit 1; }
grep -qF "**Decision points requiring a grill:** <point>:" "$P" || { echo "MISS: Step 1.4 decision-points block"; exit 1; }
grep -qF "broad acknowledgement (sure, ok, confirmed)" "$P" || { echo "MISS: generic-ack meta-rule"; exit 1; }
grep -qF "Required: ## Assumptions; always renders even when empty" "$P" || { echo "MISS: template trailer line"; exit 1; }
grep -qF "a keep/remove/defer disposition for every non-obvious branch-only change" "$P" || { echo "MISS: ledger change inventory"; exit 1; }
grep -qF "Lifecycle-verb clarification trigger:" "$G" || { echo "MISS: lifecycle-verb trigger"; exit 1; }
grep -qF "No generic acknowledgement confirms a material choice:" "$G" || { echo "MISS: grilling generic-ack rule"; exit 1; }
grep -qF "one-line receipt (decision, source, date)" "$D" || { echo "MISS: grill-with-docs receipt rule"; exit 1; }
grep -qF "Unresolved decision-point audit" "$R" || { echo "MISS: review-plan audit item"; exit 1; }
grep -qF "dated on or after 2026-09-08" "$R" || { echo "MISS: review-plan gate cross-ref"; exit 1; }
grep -qF 'DECISION_MARKER_MIN_DATE = "2026-09-08"' "$V" || { echo "MISS: readiness constant"; exit 1; }
grep -qF "missing decision-points trailer" "$V" || { echo "MISS: readiness named reason"; exit 1; }

# Contract-removal sweep: the replaced High-confidence tier wording must not
# survive anywhere in the gate file. RED-today proven at authoring (count was
# exactly 1, inside the replaced sentence). The plan document itself quotes
# this phrase in its Gist; the sweep deliberately targets only "$P".
if grep -qF "strongly supported by repo evidence" "$P"; then echo "STALE: old High-confidence wording remains"; exit 1; fi
```

### Task 1: plans confidence gate: facts versus decisions

Files:
- `agents/skills/plans/SKILL.md`

- [x] Record the current HEAD sha as `<base>` in the session notes before this task's commit (Task 8 uses it for the scope-integrity check).
- [x] Run the stale-tier sweep against the PRE-EDIT tree once first to record it fires (RED-today proof); expect it to fire. (inserted by the 2026-09-08 errata; the original execution ran this sweep post-edit, per r6 F2)
- [x] In the confidence gate block, replace the first sentence of the High-confidence bullet (today: `exactly one interpretation is strongly supported by repo evidence, established convention, or an already-confirmed decision, and a wrong call is cheap to correct during implementation.`) with: `exactly one reasonable interpretation exists, choosing any other would be unreasonable or is cheap to correct, and that interpretation is supported by repo evidence, established convention, or an already-confirmed user decision.` Keep the rest of the bullet unchanged.
- [x] Immediately after the High-confidence bullet (the last tier bullet, before the Scope-extension hard gate paragraph), insert:

```markdown
**Facts versus decisions (gate dividing line):** source verification resolves facts (what exists, what the sources already decide), not unselected design trade-offs. A material decision point is any choice between two or more plausible plan shapes that differ in scope, source-of-truth ownership, module boundary, compatibility mode, error policy, rollout shape, history strategy, preservation rules, deletion permissions, or validation evidence. Source detail never converts a decision point into a fact: authoritative sources that describe multiple alternatives leave the point low-confidence. Test every proposed task: if another reasonable design would remove, add, move, or materially change that task, the underlying choice is a low-confidence decision point regardless of source authority or detail. Do not grill factual lookups whose result is directly observable and involves no choice, and do not grill a design the user has already explicitly selected when no separate material ambiguity remains; the scope-extension hard gate below stays independent and is cross-referenced, not duplicated.
```

- [x] Directly after that inserted paragraph, insert:

```markdown
**Confidence-gate regression cases (fail-closed routing):** (1) a single-boundary feature whose single implementation is clearly required stays eligible for a high-confidence assumption; (2) a feature with an adjacent boundary, compatibility path, or ownership choice routes to `grill-with-docs`; (3) authoritative sources describing multiple alternatives still route to the grill; (4) a cleanup request with one apparently unrelated commit beside feature work still asks the grilling scope question; (5) a cleanup request with dirty, untracked, or ignored files records preservation before any restore; (6) a source-owned prerequisite is placed under `Ship when`, not converted into an assumption or executable task; (7) an explicit user decision suppresses only the already-resolved question, never unrelated ambiguity.
```

- [x] Run the dedicated pins for this task (dividers, materiality test, carve-out, regression cases) in the fail-closed form of Validation Commands, then re-run the stale-tier sweep post-edit; expect both GREEN and the sweep silent.
- [x] Commit (only the file listed above): `skills: plans fact-vs-decision confidence gate, ambiguity scan base`

### Task 2: plans ambiguity scan and requirements buffer subsection

Files:
- `agents/skills/plans/SKILL.md`

- [x] After the Cleanup scope ledger block (the paragraph ending with the checker limitation note), insert:

```markdown
**Decision-ambiguity scan (mandatory before Step 1.4):** after source discovery, separate discovered facts from decisions still requiring a choice, and record every material decision point in the requirements buffer under a `Decision points requiring a grill` heading. Each entry resolves in exactly one way: grilled via `grill-with-docs` with the user's answer recorded as a one-line receipt (decision, source, date); resolved by an already-confirmed user decision (cite its source); or the scan found no material ambiguity, which renders the literal line `Decision points requiring a grill: none remain.` in the Step 1.4 confirmation block. The subsection always renders; silently omitting it is a detectable violation of this gate.
```

- [x] Run the scan pin in fail-closed form; expect GREEN.
- [x] Commit (only the file listed above): `skills: plans mandatory decision-ambiguity scan`

### Task 3: plans Step 1.4 decision-points block, template trailer, ledger inventory

Files:
- `agents/skills/plans/SKILL.md`

- [x] In the Step 1.4 confirmation template, insert between the Assumptions block and the Scope extensions block:

```markdown
**Decision points requiring a grill:** <point>: <one-line receipt: user decision, source, date>, or the literal line `Decision points requiring a grill: none remain.` when the ambiguity scan found no material decision point.
```

- [x] Extend the HTML meta-rule comment that follows the Scope extensions line in the same template so it also reads: an absent Decision points block is itself a detectable violation of this gate; a broad acknowledgement (sure, ok, confirmed) confirms only the material decisions explicitly named in this block; a decision about one adjacent concern is never generalized to another unlisted concern; an ambiguous lifecycle verb (skip, leave, drop, defer, preserve) must already have been restated as a concrete tree action and answered before its candidate appears here as settled.
- [x] In the plan template comment for Assumptions (today: `[Optional: ## Assumptions; required when Phase 1 recorded any high-confidence assumption (confidence gate); one bullet per assumption with its basis]`), replace the line with: `[Required: ## Assumptions; always renders even when empty; one bullet per high-confidence assumption with its basis, then the trailer line "Decision points requiring a grill: none remain." or per-point receipts carried from the Step 1.4 confirmation]`
- [x] In the plan-format bullet that requires the Assumptions section, replace `a plan that silently builds on an unlisted assumption is a defect.` with `a plan that silently builds on an unlisted assumption is a defect; the section always renders and closes with the decision-points trailer carried from the Step 1.4 confirmation, and plan_readiness.py enforces the trailer for plans whose latest review round is dated on or after 2026-09-08.`
- [x] In the Cleanup scope ledger block, replace `untracked paths, and explicit deletion permissions.` with `untracked paths, explicit deletion permissions, and a keep/remove/defer disposition for every non-obvious branch-only change and affected cross-cutting surface (files, interfaces, headers, configuration, documentation), each backed by direct source evidence or an explicit user decision; a broad statement such as "preserve adjacent behavior" is not a substitute for classifying each candidate surface.`
- [x] Run the task pins (Step 1.4 block, generic-ack meta-rule, template trailer line, ledger inventory) in fail-closed form; expect GREEN.
- [x] Commit (only the file listed above): `skills: plans decision-points confirmation block, template trailer, ledger inventory`

### Task 4: grilling lifecycle-verb and generic-ack triggers

Files:
- `agents/skills/grilling/SKILL.md`

- [x] Append after the Mandatory ambiguity triggers paragraph:

```markdown
**Lifecycle-verb clarification trigger:** when a user says skip, leave, drop, defer, preserve, or otherwise uses a lifecycle verb whose effect on the current tree is unclear, restate the candidate interpretations as concrete tree actions (for example: remove it from the current change now, defer it to a later change, or leave it in place untouched) and ask which applies; record the answer before treating the candidate as settled.

**No generic acknowledgement confirms a material choice:** a reply such as sure, ok, or confirmed confirms only the material decisions explicitly named in the question or confirmation block; a decision about one adjacent concern is never generalized to another unlisted concern.
```

- [x] Run the two grilling pins in fail-closed form; expect GREEN.
- [x] Commit (only the file listed above): `skills: grilling lifecycle-verb and generic-ack triggers`

### Task 5: grill-with-docs receipt cross-reference

Files:
- `agents/skills/grill-with-docs/SKILL.md`

- [x] Append one sentence to the plans Integration Point paragraph (the one beginning `` `plans` Phase 1 invokes this skill through its confidence gate ``): `When the interview resolves a plans confidence-gate decision point, record the answer as a one-line receipt (decision, source, date) in the requirements buffer's Decision points requiring a grill subsection during the interview, not after it.`
- [x] Run the grill-with-docs pin in fail-closed form; expect GREEN.
- [x] Commit (only the file listed above): `skills: grill-with-docs decision-point receipts cross-ref`

### Task 6: review-plan unresolved decision-point audit

Files:
- `agents/skills/review-plan/SKILL.md`

- [x] In Step 1 (Load Plan and Context), append item 7:

```markdown
7. **Unresolved decision-point audit**: flag for the correctness-completeness worker: (a) plan tasks that implement one of multiple plausible designs where the plan records neither a decision-point receipt nor a `none remain` grill result; (b) a cleanup plan lacking a scope ledger or a grill result while material ownership, preservation, or history-strategy choices remain open; (c) a material candidate appearing in the branch diff or task scope with no keep/remove/defer disposition and no evidence or explicit-confirmation basis; a generic `user confirmed` or `behavior unchanged` phrase is not a basis. Each hit is a correctness-completeness finding.
```

- [x] In the Integration Point subsection "With the plan readiness gate (scripts/plan_readiness.py)", append: `The gate additionally requires the plan's decision-points trailer for plans whose latest review round is dated on or after 2026-09-08; treat a missing or unresolved trailer in such a plan as a blocking documentation finding.`
- [x] Run the two review-plan pins in fail-closed form; expect GREEN.
- [x] Commit (only the file listed above): `skills: review-plan unresolved decision-point audit`

### Task 7: plan_readiness decision-points trailer gate (RED first)

Files:
- `scripts/plan_readiness.py`

- [x] RED: add module constants after `VERDICT_TOKEN_RE`:

```python
# Plans reviewed on or after this date must carry the decision-points trailer
# (plans skill Step 1.4 confirmation, carried into ## Assumptions). Plans with
# an earlier latest-round date are legacy and stay exempt: the rule is
# forward-looking and does not retrofit already-certified plans (origin
# backlog exclusion).
DECISION_MARKER_MIN_DATE = "2026-09-08"

# The trailer line in plan bytes: "Decision points requiring a grill: <value>".
# The bolded "**Decision points requiring a grill:**" form is the Step 1.4
# chat template and never matches; the plan-file trailer is plain.
DECISION_MARKER_RE = re.compile(
    r"^Decision points requiring a grill:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE
)
```

- [x] RED-adjacent fixture support (same commit): in `write_clean_state`, emit the round date into the sidecar by adding `sidecar["date"] = date` next to the existing sidecar assembly. Today `_clear_sidecar` emits no `date` key and the `date=` kwarg feeds only the plan and review filenames, so the fixtures could never exercise the date keying (r1 F1). No pre-existing check asserts the sidecar lacks a date.
- [x] RED: add the predicate next to `summary_section` (r3 F1: the trailer search is scoped to the `## Assumptions` section so a later quoted template line elsewhere in the plan can never satisfy or mask the gate; a plan with no `## Assumptions` heading falls back to the whole document and fails as missing for gated plans, which is correct because the template always renders the section):

```python
def assumptions_section(plan_text: str) -> str:
    """Text of the ``## Assumptions`` section (whole document when absent)."""
    match = re.search(r"^## Assumptions\s*$", plan_text, re.MULTILINE)
    if not match:
        return plan_text
    tail = plan_text[match.end():]
    return re.split(r"\n## ", tail, maxsplit=1)[0]


def decision_marker_problem(plan_text: str) -> str | None:
    """Reason when the decision-points trailer is missing or unresolved.

    ``None`` when the single trailer line inside the ``## Assumptions``
    section reads ``none remain.`` or carries a non-placeholder receipt; a
    named reason otherwise. More than one trailer line is ambiguous and is
    rejected on its own reason (r4 F1: last-wins would let an unresolved
    line hide under a terminal none-remain line).
    """
    values = DECISION_MARKER_RE.findall(assumptions_section(plan_text))
    if not values:
        return "missing decision-points trailer"
    if len(values) > 1:
        return f"ambiguous decision-points trailer: {len(values)} lines"
    value = values[0]
    if value.strip().lower() == "none remain.":
        return None
    if value.lstrip().startswith("<") or value.strip().lower() in {
        "pending",
        "tbd",
        "todo",
    }:
        return f"unresolved decision-points trailer: {value!r}"
    return None
```

- [x] RED: add the selftest family and register it in the `run_selftest` dispatcher alongside the existing families:

```python
def _selftest_decision_marker(plans_dir: Path, reviews_dir: Path, check) -> None:
    """Decision-points trailer family: gated vs legacy rounds, shapes."""
    trailer = "Decision points requiring a grill: "
    # gated_none_remain_passes.
    plan, _ = write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=f"# P\n\n## Assumptions\n\n{trailer}none remain.\n",
        date="2026-09-08",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#decision_marker/gated_none_remain_passes",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # gated_missing_trailer_fails.
    plan, _ = write_clean_state(
        plans_dir, reviews_dir, plan_text="# P\n\nBody.\n", date="2026-09-08"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#decision_marker/gated_missing_trailer_fails",
        not ok and reason is not None
        and "missing decision-points trailer" in reason
        and "2026-09-08" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # gated_placeholder_trailer_fails.
    plan, _ = write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=f"# P\n\n## Assumptions\n\n{trailer}<point>: <receipt>\n",
        date="2026-09-08",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#decision_marker/gated_placeholder_trailer_fails",
        not ok and reason is not None
        and "unresolved decision-points trailer" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # gated_receipt_passes.
    plan, _ = write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=(
            "# P\n\n## Assumptions\n\n"
            f"{trailer}cleanup scope: ledger-only plan "
            "(user confirmed 2026-09-07)\n"
        ),
        date="2026-09-08",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#decision_marker/gated_receipt_passes",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # legacy_missing_trailer_passes: a round dated before the constant is
    # exempt (no retrofit of already-certified plans).
    plan, _ = write_clean_state(
        plans_dir, reviews_dir, plan_text="# P\n\nBody.\n", date="2026-09-07"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#decision_marker/legacy_missing_trailer_passes",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # sidecar_date_missing_exempt (characterization, r2 F1): a current-shape
    # sidecar without a date key is exempt from the trailer gate; the schema
    # does not hard-require the field and failing it would retrofit legacy
    # artifacts.
    plan, review = write_clean_state(
        plans_dir, reviews_dir, plan_text="# P\n\nBody.\n", date="2026-09-08"
    )
    sidecar = json.loads(
        review.with_suffix(".stats.json").read_text(encoding="utf-8")
    )
    del sidecar["date"]
    review.with_suffix(".stats.json").write_text(
        json.dumps(sidecar), encoding="utf-8"
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#decision_marker/sidecar_date_missing_exempt",
        ok and reason is None,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # trailer_outside_assumptions_fails (r3 F1): a later quoted template
    # mention outside ## Assumptions can never satisfy the gate.
    plan, _ = write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=(
            "# P\n\n## Assumptions\n\nNone needed.\n\n"
            "## Notes\n\nDecision points requiring a grill: none remain.\n"
        ),
        date="2026-09-08",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#decision_marker/trailer_outside_assumptions_fails",
        not ok and reason is not None
        and "missing decision-points trailer" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)

    # ambiguous_two_trailer_lines_fails (r4 F1): an unresolved line above a
    # terminal "none remain." line must not pass on last-wins semantics.
    plan, _ = write_clean_state(
        plans_dir,
        reviews_dir,
        plan_text=(
            "# P\n\n## Assumptions\n\n"
            f"{trailer}<point>: <receipt>\n\n{trailer}none remain.\n"
        ),
        date="2026-09-08",
    )
    ok, reason = evaluate_readiness(plan, plans_dir, reviews_dir)
    check(
        "selftest#decision_marker/ambiguous_two_trailer_lines_fails",
        not ok and reason is not None
        and "ambiguous decision-points trailer" in reason,
        f"ok={ok} reason={reason}",
    )
    _clean_reviews_dir(reviews_dir)
```

- [x] Run `python3 scripts/plan_readiness.py --selftest`; expect RED with exactly this empirically derived failing set (r1 F2): `selftest#decision_marker/gated_missing_trailer_fails`, `selftest#decision_marker/gated_placeholder_trailer_fails`, `selftest#decision_marker/trailer_outside_assumptions_fails`, and `selftest#decision_marker/ambiguous_two_trailer_lines_fails` fail, while the four pass-expecting arms (`gated_none_remain_passes`, `gated_receipt_passes`, `legacy_missing_trailer_passes`, `sidecar_date_missing_exempt`) pass vacuously because the gate does not consume the trailer yet; every pre-existing check still passes.
- [x] GREEN: in `evaluate_readiness`, after the `is_review_ready` condition and before `return True, None`, insert:

```python
    # 6. Decision-points trailer (forward-looking): plans whose LATEST round
    # is dated on or after DECISION_MARKER_MIN_DATE must carry the trailer
    # in their bytes; legacy rounds stay exempt (no retrofit). A sidecar
    # with a missing or empty date is also exempt: the schema does not
    # hard-require the field on versionless current-shape sidecars, and
    # failing those would retrofit legacy artifacts; the authoring-side
    # prose gate covers newly authored plans regardless (r1 F3).
    round_date = str(payload.get("date", ""))
    if round_date >= DECISION_MARKER_MIN_DATE:
        try:
            plan_text = resolved.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            return False, f"cannot read plan bytes for trailer check: {exc}"
        problem = decision_marker_problem(plan_text)
        if problem:
            return False, (
                f"{problem} (required for plans reviewed on or after "
                f"{DECISION_MARKER_MIN_DATE}; latest round r{round_no} is "
                f"dated {round_date})"
            )
```

- [x] Run `python3 scripts/plan_readiness.py --selftest`; expect GREEN: all checks pass including the eight new ones. Then run `python3 scripts/validate_review_staging.py --selftest`; expect GREEN (sibling untouched).
- [x] Run the two readiness pins (constant, named reason) in fail-closed form; expect GREEN.
- [x] Commit (only the file listed above): `scripts: plan_readiness decision-points trailer gate with selftest family`

### Task 8: final validation and scope-integrity gate

Files: none new (validation only; fixes commit to the owning file)

- [x] Run the full Validation Commands block from a clean shell at the repo root; expect exit 0 end to end.
- [x] Verify scope integrity of this plan's own commits: with `<base>` recorded before Task 1's commit, `git log --format:'' --name-only <base>..HEAD | sort -u` must equal the plan's declared artifact set: the union of the task Files lists, this plan document, and this plan's review artifacts; the done commit-all path must be fenced by enumerating any additional paths the done step commits; any extra path in this plan's commit history is a defect to fix before completion.
- [x] Verify no concurrent peer state was consumed: the commit half is proven by the scope-integrity check above; the working-tree half is proven by never staging, committing, checkout-reverting, or otherwise touching any path this plan never declares. The peer committing or reworking its own files mid-execution is expected and harmless; the invariant binds only this plan's actions.
- [x] Commit any validation-driven fixes individually to their owning files; expect none needed.

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-07-plans-facts-do-not-resolve-design-ambiguity.md: disposition folded into 2026-09-07-plans-facts-do-not-resolve-design-ambiguity.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-20-plans-watcher-schedule-payload-contract-ambiguity.md: disposition folded into 2026-09-07-plans-facts-do-not-resolve-design-ambiguity.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-05-plans-session-constraints-not-plan-constraints.md: disposition folded into 2026-09-07-plans-facts-do-not-resolve-design-ambiguity.md (2026-09-25); per-item file deleted.
