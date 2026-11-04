# Plan: Make execution state machine-readable across the landing and queue surfaces

Backlog origin: docs/history/backlog/2026-11-04-execution-lane-authored-plans-misread-as-landed.md
Driving force: efficiency + code-quality (compound, ranked primary + secondary)
Plan review record: the staging series .ai-playbook/reviews/2026-11-04-plan-review-execution-lane-authored-plans-misread-as-landed-p1ed48568-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 4h total, largest task 1.5h
Authoring claim: 2026-11-04-execution-lane-authored-plans-misread-as-landed.md (session sess_09bed986-130b-422a-a613-a44f79918f92)
Executed: yes (fd8ed93aeba4658b1f733cb28c1cc9e8113eab36)

## Terms

- authoring landing: the commit that lands a newly authored plan document at the plans root, certified by its sealed review cert (an untracked seal under `.ai-playbook/review-certs/`); carries no operative changes, a landing whose diff carries the plan's own executed scope is an execution landing, disclosed by the warning-only mismatch notice and completed by the execution-status writers (the verb debt discharges through the writers, no re-verb). Verb after this plan: `plans: file <slug>`.
- execution landing: the commit that lands a plan's executed changes; verbs `execute-plan: land <slug>` and `done: execute <slug>`, unchanged by this plan.
- authoring verb family: the commit-subject prefixes that mark an authoring landing after this plan: `plans: file ` and the retained `author: land `.
- retired verb: `plans: land `, the pre-plan authoring verb; retired for authoring going forward and never adopted as an execution verb; commits predating this plan's rename landing classify authoring by verb (pre-rename the verb classified authoring by convention; witnessed same-day execution landings under the retired verb, `b8036d031` and `1a1673921`, classify authoring by verb, accepted, scan behavior unchanged from today), post-rename commits classify by diff composition.
- plans root: `docs/history/plans/`; the D-1 execution queue (operator-directives; realized by D1 in `agents/skills/maintenance/decisions.md`).
- origin row: the open backlog item file under `docs/history/backlog/` a plan promotes; its `Status:` line carries the coverage lifecycle.
- execution claim: the run claim file under `docs/tmp/execution-claims/` (or the claims gateway) recording which session owns a plan's execution.
- stand-down: the exec lane's decision to run nothing for a turn, which this plan requires to carry per-candidate evidence.
- the guard: `scripts/reverse_squash_guard.py`, whose `LANDING_CLAIM_PREFIXES` classifies landing-claim commit subjects by lane kind.
- origins gates: `scripts/check_plan_origins_closed.py` and `scripts/check_prompt_log_origins.py`, the two validators over origin-row coverage.
- verified-absent distinctive span: a plan's distinctive change token probed twice (working-tree grep plus `git log -S`) returning zero, the evidence form this plan's origin row records.
- stale-claim takeover: the existing plans/authoring-claim machinery that reassigns a claim whose `updated:` went stale.
- `Executed:` field: the plan-header metadata field on plans-root plans carrying `no` until the execution landing flips it to `yes (<recorded tip>)`, where `<recorded tip>` is the executed branch's pre-squash tip sha named explicitly (never the landing commit digest, which does not exist at rider time).
- covered-pending-execution: the origin-row status the authoring landing writes; flipped by the execution landing to the existing `covered (<plan path>)` witness (or folded and deleted by the completion pass, its current terminal state).
- pins suite: `scripts/check_maintenance_pins.sh`, the pinned operative-text span gate.

## Why

Two same-day exec sessions stood down 0/1 reporting "all open plans landed" while twelve authored, certified plans waited unexecuted at the plans root: authoring-landing commits narrate the plan's intended changes as if landed, origin rows flip `covered` at authoring time, and no surface records execution state, so every survey that derives candidates from landing-commit surface misreads the queue. Ten of the twelve plans carry verified-absent distinctive spans.

## Gist & Examples

TLDR: renames the authoring landing verb, carries execution state in origin rows and a plan-header field, and pins the exec-lane candidate derivation to the plans root, execution claims, and that field, so the queued plans dispatch.

Before: `plans: land done-lock-hold-overbroad-commit-stop (scope the done blocked-acquire stop to its lock-bound write set: ...)` reads as landed work; an exec survey greps landing commits, concludes the candidate set is empty, and stands down while the plan's change exists nowhere on disk.

After: the same landing reads `plans: file done-lock-hold-overbroad-commit-stop (authored plan; execution pending; no operative changes in this commit; r3 certified ready=yes)` (message template landed in the landing-grammar text, Task 2); the origin row reads `Status: covered-pending-execution (docs/history/plans/2026-11-04-....md)`; the plan header reads `Executed: no`; the exec survey dispatches from the plans root plus execution claims plus the field; at execution landing the row returns to the existing `covered (<plan path>)` witness or folds away with its completion pass, and the header flips to `Executed: yes (<recorded tip>)`.

## Outcome

The execution queue is machine-readable and dispatches instead of starving.

- Exec-mode surveys derive candidates from the plans root, execution claims, and the `Executed:` field; a stand-down names per-candidate evidence, never a landing-commit grep.
- An authoring landing is unmistakable from its commit verb alone (`plans: file` / `author: land` are the authoring family; `plans: land` is retired, pre-rename commits classify authoring by verb, post-rename by diff composition).
- A backlog row shows pending execution from its authoring flip until its plan executes, the executing tip afterwards carried by the plan's `Executed:` header field; legacy `covered (<plan>)` rows and field-less plans read as pending execution under the same semantics, so the queued plans dispatch unchanged.
- The two same-day 0/1 stand-down class is closed: the misread surface (verb ambiguity plus stateless rows plus stateless plan files) no longer exists going forward.

Gate delta: +1 dispatch-input read (D1 consumes the `Executed:` field as a candidate filter; it is a selection input, not a gate or validator), admitted under the repository guidelines' Machinery admission protocol with the witnessed incident `docs/history/backlog/2026-11-04-execution-lane-authored-plans-misread-as-landed.md` (two same-day 0/1 stand-downs over a twelve-plan queue, 2026-11-04), expected catch: every exec survey that would otherwise misread the queue (two witnessed in one day), false-positive cost: a queued plan wrongly excluded when the field is stale, bounded by the survey's candidate-with-report arm and the metadata-retrofit-at-revival rule, review date 2026-12-04. The field itself is justified against the row token that carries overlapping state: 6 of the 13 plans-root plans carry no resolvable `Backlog origin:` link (including the `none` form) and out-of-repo executions leave no row-resolvable trace, so the header field is the only per-plan executed-state surface for the whole queue. +1 accepted status token in the two origins gates (`covered-pending-execution` in `scripts/check_plan_origins_closed.py` and, as a served-class member, `scripts/check_prompt_log_origins.py`), priced by paying siblings: the verb rename retires the ambiguous authoring verb (removing the landing-ambiguity misread class) and the marker-wording alignment prescribes one receipt vocabulary going forward; completed-integrity witness: the twelve-plan phantom queue in the origin row. No refusal paths, checks, or fields are removed; no new blocking validator lands.

## Assumptions

- assume every selection or classification rule that reads verbs classifies a pre-rename `plans: land` commit as authoring by verb (the pre-rename verb was unambiguously authoring) and a post-rename `plans: land` commit by diff composition (plan-document/cert/log/row-status bytes only reads authoring; an operative diff reads execution; inconclusive defaults to authoring); basis: operator option B plus the panel's verified 7-commit mixed-diff history walk (2026-11-04; same-day execution landings under the retired verb, `b8036d031` and `1a1673921`, classify authoring by verb, accepted)
- assume the post-rename authoring verb family is `plans: file` plus the retained `author: land `; basis: the guard constant's existing second authoring prefix
- assume an authoring landing carries no operative changes and a landing whose diff carries the plan's own executed scope is an execution landing; the grammar-notice arm discloses the mismatch warning-only and the execution-status writers complete the execution-direction flips (the verb debt discharges through the writers, no re-verb); basis: the r2 panel's combined-landing finding (2026-11-04)
- assume a stranded half-state (row flipped pending-execution, plan never executed; or an execution landing flipping one surface and not the other) resolves through the combined-landing disposition (an authoring closeout whose landing diff carries the plan's own executed scope writes the `Executed:` flip and the row's execution witness) and the survey's candidate-with-report arm at the next survey; the stale-claim takeover applies to claims only; basis: the r2 panel's unreachable-remedy finding (2026-11-04)
- assume execution-landing verbs `execute-plan: land` and `done: execute` stay unchanged; basis: operator option B renames only the authoring verb
- assume the pins suite and any validator citing renamed text or the new token are updated in the same tasks that change that text; basis: repository guidelines' pins mandate
- assume the `Executed: no` line in this plan's own header is the field's first instance, carried by the plan that defines it; basis: the metadata block this plan's Task 3 adds to the Plan Format template
- assume history records (`docs/history/plans/`, the completed/rejected archives, `docs/maintenance/development_lessons.md`) are immutable context and are not swept for the verb rename; the two rolling logs' rules sections are living text Task 5 owns; ledger witness-note bytes and fixture subjects pinning the historical grammar keep the verb they witnessed; basis: the completed-history immutability convention

Decision points requiring a grill: vocabulary rename to `plans: file` (operator, in-session structured questions, 2026-11-04, Gist and Task 1); origin-row covered-pending-execution lifecycle (operator, in-session structured questions, 2026-11-04, Task 2); Executed header field included now with the D1 dispatch-input read (operator, in-session structured questions, 2026-11-04, Task 3); selection home D1 plus template mirror (operator, in-session structured questions, 2026-11-04, Task 3).

## Standing constraints

- The queued plans stay dispatchable: no task re-certifies, re-authors, or re-executes them; this plan changes classification surfaces only, and their rows keep the legacy covered/open shapes (or none) reading as pending execution under the new semantics.
- This repository never runs its whole test suite during ordinary execution; validation runs the focused suites named in Validation Commands.

## Evaluation Criteria

**Quality dimensions:**
- correctness: after the rename, an authoring landing is unmistakable from its verb; the origins gates accept `covered-pending-execution` and still fail closed on genuinely uncovered rows; the guard's classification maps the authoring family and diff-composes `plans: land` correctly (focused suites green)
- maintainability: every operative text citation of the retired authoring verb is updated in the same change; the pins suite is green after each task's sweep; the investigate-entry checker and the plan-readiness validator exit 0
- consistency: PLAN-PROMPTS and EXEC-PROMPTS marker wording states one lifecycle going forward

**Done when:**
- a simulated exec-mode survey built on the new D1 derivation selects every queued plan at the plans root and excludes none of them for landed-state reasons, with the walk recorded as Task 3's evidence
- the origins checker accepts a `covered-pending-execution` fixture row and still refuses an uncovered row (focused test evidence)
- the pins suite, the entry checker, and the readiness validator exit 0 at closeout

**Ship when:**
- none; all checks are repository-verifiable

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/reverse_squash_guard.py` (Task 1)
- `scripts/execution_claim.sh` (Task 2)
- `scripts/base_reflog_audit.py` (Task 2)
- `scripts/land_squash.sh` (Task 2)
- `scripts/check_plan_origins_closed.py` (Task 3)
- `scripts/check_prompt_log_origins.py` (Task 3)
- `scripts/check_maintenance_pins.sh` (Tasks 1-5)

**Skill and guideline text:**
- `agents/skills/plans/SKILL.md` (Tasks 3-4)
- `agents/skills/maintenance/decisions.md` (Task 4)
- `agents/skills/execute-plan/worktree-first.md` (Task 2)
- `AGENTS.md` (Task 3)
- `agents/skills/execute-plan/SKILL.md` (Task 4)
- `agents/skills/maintenance/template-execution.md` (Task 4)

**Tests:**
- `scripts/test_reverse_squash_guard.py` (Task 1)
- `scripts/test_execution_claim.py` (Task 2)
- `scripts/test_base_reflog_audit.py` (Task 2)
- `scripts/test_land_squash.py` (Task 2)
- `scripts/test_check_plan_origins_closed.py` (Task 3)
- `scripts/test_check_prompt_log_origins.py` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. The verb sweep's grep arm (Task 1) may surface additional operative citations of the retired verb; those files are plan-related when the citation is operative text. Fixture subjects and ledger witness notes pinning the historical grammar are exempt (history-immutability assumption). If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** the rolling logs' marker-wording edits (Task 5) touch `docs/history/backlog/PLAN-PROMPTS.md`'s Standing rules block and `docs/history/backlog/EXEC-PROMPTS.md`'s line-1 intro; the edits follow the logs' Write boundary rule (pinned in PLAN-PROMPTS's Standing rules) at execution time and are in scope for review of wording consistency.

**Out of scope; reject unless plan-related:**
- `docs/maintenance/development_lessons.md`; historical record, not operative text
- `docs/history/plans/**` and `docs/history/backlog/completed/**` content; immutable history
- the twelve queued plan files' own content; this plan changes classification surfaces only

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_reverse_squash_guard.py scripts/test_execution_claim.py scripts/test_check_plan_origins_closed.py scripts/test_check_prompt_log_origins.py scripts/test_base_reflog_audit.py scripts/test_land_squash.py -q
bash scripts/check_maintenance_pins.sh
python3 scripts/check_investigate_entries.py --log docs/history/backlog/PLAN-PROMPTS.md
python3 scripts/check_investigate_entries.py --log docs/history/backlog/EXEC-PROMPTS.md
python3 scripts/plan_readiness.py docs/history/plans/2026-11-04-execution-lane-authored-plans-misread-as-landed.md
```

### Task 1: Rename the authoring landing verb to `plans: file` (guard classification)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/reverse_squash_guard.py`
- `scripts/test_reverse_squash_guard.py`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `LANDING_CLAIM_PREFIXES` in `scripts/reverse_squash_guard.py`
- `AUTHORING_RENAME_BOUNDARY` in `scripts/reverse_squash_guard.py`

- [x] `LANDING_CLAIM_PREFIXES` maps `plans: file ` to the authoring kind and keeps `author: land ` authoring unchanged: given a fixture subject `plans: file <slug> (authored plan; execution pending)`, expects the authoring classification [class: IMPLEMENTATION_REQUIRED]
- [x] `plans: land ` is the retired verb with the rename-boundary split: a commit predating this plan's rename landing classifies authoring by verb; a post-rename commit classifies by diff composition (plans-only diff → authoring; operative diff → execution; inconclusive → authoring); the boundary is the first commit in walked history whose subject starts with `plans: file `, resolved once into the `AUTHORING_RENAME_BOUNDARY` guard module constant, controllable in fixtures [class: IMPLEMENTATION_REQUIRED]
- [x] `plans: land ` stays in `LANDING_CLAIM_PREFIXES` (recognition unchanged; only `anchor_kind`'s classification changes): given walk and batch scans over a historical plans-only `plans: land` anchor, expects the anchor to surface with its `[flip]`/`[prune]` residue findings, and an operative-diff `plans: land` anchor to classify execution [class: IMPLEMENTATION_REQUIRED]
- [x] Diff-composition fixtures: given a post-rename mixed-diff `plans: land <slug>` commit (plan bytes plus code bytes), expects the execution classification; given a plans-bytes-only commit, expects the authoring classification producing the `[flip]`/`[prune]` residue findings [class: IMPLEMENTATION_REQUIRED]
- [x] Historical and boundary-edge fixture cells: given a pre-rename mixed-diff commit (the seven-commit witness class), expects the authoring classification by verb; given a commit sharing the rename landing's date but preceding the resolved boundary, expects the authoring classification by verb [class: IMPLEMENTATION_REQUIRED]
- [x] Residue flags follow the anchor's classification: given an authoring-classified anchor, expects the `[flip]`/`[prune]` arms; given an execution-classified anchor, expects the `done: archive`/`done: fold` arms (no `classify_followups` edit; the earlier authoring-residue-phrase reading is superseded by this rule) [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a pre-rename `plans: land <slug>` commit of any diff composition, expects the authoring classification by verb (never the execution kind), so no historical authoring anchor, plans-only or mixed-diff, loses its residue sweep [class: IMPLEMENTATION_REQUIRED]
- [x] Pinned-span updates ride this task: `scripts/check_maintenance_pins.sh` spans over any pinned text this task edits are updated in the same change, and the pins suite passes [class: REPOSITORY_TEST]
- [x] Run → expect RED: the updated guard fixtures fail against the current verb mapping before the edits [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `scripts/test_reverse_squash_guard.py` passes with the renamed-verb and diff-composition fixtures, the pinned `plans: land` authoring assertions migrated per the fixture-migration boundary (Task 2) with the flip/prune expectations unchanged [class: REPOSITORY_TEST]
- [x] Commit: `feat: rename the authoring landing verb to plans: file and retire the plans: land authoring verb` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Landing-grammar, notice, audit, and claim-sweep fixtures for the renamed verb

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/execution_claim.sh`
- `scripts/base_reflog_audit.py`
- `scripts/land_squash.sh`
- `scripts/test_execution_claim.py`
- `scripts/test_base_reflog_audit.py`
- `scripts/test_land_squash.py`
- `agents/skills/execute-plan/worktree-first.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `sweep_landing_subject_names_slug` in `scripts/execution_claim.sh`
- `LANDING_PHRASED` in `scripts/base_reflog_audit.py`

- [x] Operative-text sweep: the grep-verified operative sites use the new vocabulary (the guard constant's grammar comment, re-pointed since its cited prose home is immutable; `scripts/execution_claim.sh` usage text and case pattern), plus the grep arm's discovery of further operative citations [class: IMPLEMENTATION_REQUIRED]
- [x] The landing-grammar text in `agents/skills/execute-plan/worktree-first.md` gains the authored-plan message template `plans: file <slug> (authored plan; execution pending; no operative changes in this commit; <cert summary>)` [class: IMPLEMENTATION_REQUIRED]
- [x] The grammar-notice fixtures track the remap: the `scripts/test_land_squash.py:704` fixture is updated to the post-remap expectation (`emit_grammar_notice` reads the guard constant as single source); given an authoring-verb subject, expects no unrecognized-prefix warning [class: IMPLEMENTATION_REQUIRED]
- [x] The grammar-notice arm discloses a verb/diff mismatch warning-only: given an authoring-family subject whose diff carries operative-scope bytes (outside the Assumptions' authoring-class enumeration), or a retired-verb subject whose operative diff contradicts its family's expectation, expects a warning naming the mismatch (no new blocker, no refusal) [class: IMPLEMENTATION_REQUIRED]
- [x] The mismatch arm consumes the guard's diff-composition classifier via the existing guard-module import (one classifier serving scan-time and compose-time surfaces) [class: IMPLEMENTATION_REQUIRED]
- [x] Scan-time shape of a combined landing is named and accepted: an operative-diff `plans: file` anchor classifies authoring at scan time; the residue sweep's miss of the execution-direction closeouts for that shape is accepted and named here (the compose-time mismatch warning and the execution-status writers own it) [class: IMPLEMENTATION_REQUIRED]
- [x] `plans: file ` joins `LANDING_PHRASED`'s authoring coverage in `scripts/base_reflog_audit.py`: given a content-bearing `plans: file <slug>` landing, expects the audit clean, exit 0; given an empty-tree authoring landing, expects the empty-receipt row (fixtures mirroring the existing shapes) [class: IMPLEMENTATION_REQUIRED]
- [x] Sweep exemptions hold: the retired verb is not adopted as an execution verb and the execution verb set stays unchanged; ledger witness-note bytes and fixture subjects pinning the historical grammar keep the verb they witnessed [class: IMPLEMENTATION_REQUIRED]
- [x] `sweep_landing_subject_names_slug` in `scripts/execution_claim.sh` recognizes the `plans: file ` subject shape in its case pattern, with a fixture joining the per-prefix subTest family and a negative fixture with a `plans: file <slug>` subject whose plan sits parked at the plans root outside the completed archive expecting the skip and unchanged claim bytes [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture migration boundary: recognition and rename-boundary/historical-anchor fixtures keep `plans: land` subjects; plain authoring-classification assertions migrate to `plans: file` subjects [class: IMPLEMENTATION_REQUIRED]
- [x] Pinned-span updates ride this task: `scripts/check_maintenance_pins.sh` spans over any pinned text this task edits are updated in the same change, and the pins suite passes [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `scripts/test_execution_claim.py`, `scripts/test_base_reflog_audit.py`, and `scripts/test_land_squash.py` pass with the renamed-verb, grammar-notice, and LANDING_PHRASED fixtures [class: REPOSITORY_TEST]
- [x] Commit: `feat: land the renamed-verb grammar, notice, audit, and claim-sweep fixtures` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Origin-row pending-execution lifecycle

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/check_plan_origins_closed.py`
- `scripts/check_prompt_log_origins.py`
- `scripts/test_check_plan_origins_closed.py`
- `scripts/test_check_prompt_log_origins.py`
- `agents/skills/plans/SKILL.md`
- `AGENTS.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors:
- `STATUS_COVERED_VALUE_RE` in `scripts/check_plan_origins_closed.py`

- [x] `STATUS_COVERED_VALUE_RE` accepts the `covered-pending-execution (<plan>)` status value as a non-closed, plan-witnessed state: archive mode with a resolvable different-plan witness yields no straggler row, exit 0; a pending token with an unresolvable witness fails closed exactly as today [class: IMPLEMENTATION_REQUIRED]
- [x] Corpus-mode verdict pinned: quiet while the covering plan is top-level-active, the standard no-longer-top-level warning once it completes (matching today's plain-covered behavior) [class: IMPLEMENTATION_REQUIRED]
- [x] The pending token joins the served class in `SERVED_STATUS_RE` in `scripts/check_prompt_log_origins.py`: an all-pending entry goes stale at the authoring flip and owes its prune; the execution flip is staleness-preserving (both tokens served), unstaling only via prune or the completion fold-and-delete [class: IMPLEMENTATION_REQUIRED]
- [x] The authoring-time flip writer emits the new token: `_flip_status_line`/`run_mark_covered_mode` in `scripts/check_plan_origins_closed.py` write `covered-pending-execution (<repo-relative plan path>)` at the authoring flip, with the idempotency and different-witness conflict arms classifying both the new and the legacy token and writer fixtures added [class: IMPLEMENTATION_REQUIRED]
- [x] The authoring closeout's conditional writer arm: the writer emits the pending token by default and, on the execution branch, flips the row token and the plan-header `Executed:` field to `yes (<recorded tip>)` (the tip being the pre-squash branch sha), with writer fixtures for both branches [class: IMPLEMENTATION_REQUIRED]
- [x] The execution-direction writer arm is pinned: at the execution landing the row flips to `covered (<plan path>)` or is folded and deleted per the existing completion pass, with a writer fixture for each arm [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a fixture row with no status or an unresolvable covering-plan witness, expects the gates to still fail closed exactly as today (the new token admits nothing on its own) [class: IMPLEMENTATION_REQUIRED]
- [x] `AGENTS.md`'s Commit & PR section carries the row lifecycle duties: the authoring-landing flip writes `covered-pending-execution (<plan>)`; the execution-landing flip returns the row to the existing `covered (<plan path>)` witness or folds and deletes it through the existing completion pass (the fold-and-delete duty retained unchanged; the execution-flip wording is a transient diff-level convention) [class: IMPLEMENTATION_REQUIRED]
- [x] The legacy disposition and half-state remedy land in `AGENTS.md`: legacy `covered (<plan>)` rows read as pending execution until their execution flip; the stranded half-state remedy names the combined-landing disposition and the survey's candidate-with-report arm (the stale-claim takeover applies to claims only); the plans skill's landing-closeout duty wording (the `--mark-covered` invocation) states the pending-execution witness [class: IMPLEMENTATION_REQUIRED]
- [x] Pinned-span updates ride this task: `scripts/check_maintenance_pins.sh` spans over any pinned text this task edits are updated in the same change, and the pins suite passes [class: REPOSITORY_TEST]
- [x] Run → expect RED: the origins-gate and writer fixtures for the new token fail before the regex and writer edits [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: `scripts/test_check_plan_origins_closed.py` and `scripts/test_check_prompt_log_origins.py` pass with the pending-execution, served-class, and fail-closed fixtures [class: REPOSITORY_TEST]
- [x] Commit: `feat: carry execution state in origin rows via covered-pending-execution` [class: IMPLEMENTATION_REQUIRED]

### Task 4: The `Executed:` field, the D1 dispatch-input read, and the template mirror

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/template-execution.md`
- `scripts/check_maintenance_pins.sh`

- [x] The Plan Format template's metadata block in `agents/skills/plans/SKILL.md` gains the `Executed:` field (`no` at authoring, `yes (<recorded tip>)` after the execution landing, the recorded tip being the executed branch's pre-squash tip sha), with the metadata-retrofit rule stating existing plans gain the field at their next natural edit or revival [class: IMPLEMENTATION_REQUIRED]
- [x] The execution closeout's landing duty in `agents/skills/execute-plan/SKILL.md` flips the executed plan's `Executed:` field and the origin row's covered witness in the same landing, recording the pre-squash branch tip sha in the field [class: IMPLEMENTATION_REQUIRED]
- [x] D1 in `agents/skills/maintenance/decisions.md` derives the execution candidate set from the plans root plus execution claims plus the `Executed:` field, never from landing-commit surface; the stand-down rule requires named per-candidate evidence; D1's admission citation is written at the durable completed-twin path, dangling only until the same run's completion pass creates it, and the completion pass verifies rather than re-points [class: IMPLEMENTATION_REQUIRED]
- [x] The `Executed:` field's absent-line semantics are pinned in D1: a plans-root plan with no `Executed:` line selects as pending (missing = not executed; only a literal `yes (<recorded tip>)` excludes) [class: IMPLEMENTATION_REQUIRED]
- [x] The surface precedence is pinned in D1: the header field is authoritative for executed state over the row token on disagreement (the row carries coverage, the field carries execution); header/row disagreement selects as candidate-with-report, never silent exclusion; a field `yes (<recorded tip>)` with a pending row selects as candidate-with-report until the row is repaired [class: IMPLEMENTATION_REQUIRED]
- [x] The survey arm carries a live-change probe for agreement-pending plans: a plan whose field and row both read pending but whose distinctive span is verified-present in the tree selects as candidate-with-report; a plan with no derivable distinctive span still selects as candidate-with-report with span-derivation unavailable recorded [class: IMPLEMENTATION_REQUIRED]
- [x] The template mirror line in `agents/skills/maintenance/template-execution.md` states the same candidate derivation in one line, referencing D1 as the owning rule [class: IMPLEMENTATION_REQUIRED]
- [x] The maintenance lane's `done: execute` closeout flips the executed plan's `Executed:` field in its completion-archival text in `agents/skills/maintenance/template-execution.md`, so both execution lanes own their terminal-state writer [class: IMPLEMENTATION_REQUIRED]
- [x] The Done-when simulation has an owning step and evidence home: the closeout records a walk over every plans-root plan listing its `Executed:` read and its D1 selection verdict, demonstrating every queued plan at run start selects (a field-less plan selects as pending) [class: IMPLEMENTATION_REQUIRED]
- [x] The walk's excluded cell is recorded against a stated hypothetical `yes (<recorded tip>)` row: a scratch plan outside the plans root or an explicit hypothetical in the closeout record (no corpus instance exists); the same hypothetical channel covers the disagreement cell, a field-`yes`-with-pending-row pair [class: IMPLEMENTATION_REQUIRED]
- [x] Pinned-span updates ride this task: `scripts/check_maintenance_pins.sh` spans over any pinned text this task edits are updated in the same change, and the pins suite passes [class: REPOSITORY_TEST]
- [x] Commit: `feat: add the Executed plan-header field and pin D1 candidate derivation to the plans root` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Marker-wording alignment and corpus validation

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`
- `docs/history/backlog/EXEC-PROMPTS.md`
- `scripts/check_maintenance_pins.sh`

- [x] The rolling logs prescribe the canonical receipt vocabulary going forward: PLAN-PROMPTS's Standing rules block and EXEC-PROMPTS's line-1 intro gain the wording (authoring-landed receipts state `origin row covered-pending-execution (<plan>)`, execution-completed receipts state the execution form); inspect each target's actual bytes first; historical receipt lines stay byte-for-byte untouched [class: IMPLEMENTATION_REQUIRED]
- [x] The rules edit is descriptive lifecycle wording only: receipt line formats stay as pinned (the PRUNE receipt enums and the digest-free covered witness format are unchanged) [class: IMPLEMENTATION_REQUIRED]
- [x] The sealed review certs for this plan are present in the execution worktree (the run's transfer-in step) before the readiness command runs, and the command is invoked from the execution worktree root [class: IMPLEMENTATION_REQUIRED]
- [x] The pins spans pinning the changed operative text are updated in `scripts/check_maintenance_pins.sh` in the same change, and the suite passes [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the entry checker exits 0 on both logs and the readiness validator exits 0 on this plan [class: REPOSITORY_TEST]
- [x] Commit: `feat: align rolling-log marker wording with the execution-state lifecycle` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- docs/history/backlog/2026-11-04-execution-lane-authored-plans-misread-as-landed.md: covered and executed by this plan (execution landing of the run branch 2026-11-04-execution-lane-authored-plans-misread-as-landed; Executed field carries the pre-squash tip). The origin row is deleted in the same completion pass; its durable home is this archived twin.
