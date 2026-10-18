# Plan: Two-mode maintenance loop policy

Backlog origin: none
Driving force: simplicity + automation
Plan review record: the staging series docs/history/reviews/2026-10-06-plan-review-two-mode-loop-policy-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 4h total, largest task 1.5h (over the 3h cap by the shared-file seam rule: Tasks 1-3 each edit agents/skills/maintenance/SKILL.md, so no split exists; the pre-round warning is accepted and recorded in the review staging doc)
Authoring claim: docs/tmp/authoring-claims/2026-10-06-two-mode-loop-policy.md (session sess_3cb0dc6e-62bc-441b-8bfa-686ffdb400d6)

## Terms

- Session mode: the work mode a maintenance session binds at launch from its own directive; never persisted, never shared across sessions.
- Author mode: the session authors plans nonstop (plan-uncovered backlog work, rolling-log entries); the execution lane resolves to no-op for that session.
- Exec mode: the session executes work nonstop from one urgency-ordered candidate set: dispatchable plans, ready EXEC-PROMPTS.md entries, and directly ad-hoc-eligible backlog items; the authoring lane resolves to no-op for that session.
- Mode binding: the launch-time classification of the session directive into author, exec, or dual; interactive sessions ask one clarifying question when the wording is unclear; unattended sessions with no mode wording run dual.
- Starvation: the bound mode's lane has no work input left (its candidate set is empty under the mode's own selection rules).
- Starvation switch: the session lifts its own mode exclusion for the turned work and works the other mode's lane, effort following the work; the bound mode's non-persistence invariant is the Mode binding paragraph's, stated once there.
- Ad-hoc-eligible: an open backlog item passing the eligibility test: plan-uncovered, not profile-deferred, formal-class per the receiving-review triage class, or body-named single-surface fix with no open design choice; tracked skill, docs, or script surfaces only, never a guard-bearing path (the pins suite, the machinery registry, any skill's guard or mode paragraphs, state-schema field paragraphs); no new dependency, no state-schema or guard change, no machinery removal.
- EXEC-PROMPTS.md: the tracked rolling log of ready-to-dispatch ad-hoc work entries beside PLAN-PROMPTS.md, fed by investigate's work-type verdict, consumed by exec-mode sessions.
- Work-type verdict: investigate's classification of an investigated item as plan-worthy (entry lands in PLAN-PROMPTS.md) or ad-hoc-able (entry lands in EXEC-PROMPTS.md); ad-hoc-able is the verdict label for an item that passes the eligibility test, i.e. ad-hoc-eligible. Composition rule (stated once here, governing the verdict step over investigate's group semantics): the verdict runs per origin item against the eligibility test; a group whose members classify uniformly routes as one entry by that verdict, and a mixed group splits so each entry routes by its members' shared verdict.
- Project-class guard: the pet-project gate above the modes; the facts document's declared priority profile class decides. Company-profile or undeclared projects resolve both work lanes to survey-only in every mode.
- Survey-only: the loop's report-only shape: survey, guards, read-backs, and state writes run; no authoring, execution, or ad-hoc dispatch of any kind.
- Priority profile: the facts document's `## Priority profile` block (guidelines rule 68) whose text names the profile class (personal or company).
- Review panel: the doing-code-review skill's sub-agent panel over a change set; the ad-hoc arm's reviewer of record.
- loop_mode (retired): the persisted scheduler-state mode field and its machinery, deleted by this plan.
- Mode appendix (retired): the per-mode paragraph the parent automation prompt carried; deleted with the field.
- Mode-held retention (retired): the pending_dispatch retention for mode-excluded targets; deleted with the field.
- cycles_completed: the pacing cycle count; re-homes from loop_mode onto the authoring_cycle_gate object as an additive key.
- Pins suite: scripts/check_maintenance_pins.sh, the literal-span gate over the maintenance skill files.
- D-2, D-3, D-4: the operator's standing directive records in docs/maintenance/operator-directives.md; D-2 requires review validation for ad-hoc fixes and refuses archiving plans without real changes; D-3 and D-4 pin the carrier cadences (daily 11:00 scheduler, daily 05:49 authoring). D-2 resolution (2026-10-06, operator interview answer): the panel-before-landing route is the operator's resolution of D-2's validation requirement for eligibility-passing ad-hoc items, so a plan-free reviewed landing is not D-2-violating.
- Effort pairing: the operator policy coupling work kind to reasoning effort (authoring work high, execution work reduced); the runtime overlay's Child model and effort policy is its policy of record.
- P54, P57: landed plan identifiers for the fleet-cap doctrine (P54) and the per-execution worktree-isolation doctrine (P57).
- queued_execution: the fence's landed-unclaimed census array (read by the starvation fence; this retirement does not touch it); execution_queue: D1's dispatchable-plan head queue popped on dispatch, whose head Task 3's ordering contract reads by reference; the two are distinct additive state fields, never aliases.
- Starvation fence: the queued-execution aging bound whose turn_error fires when a landed-unclaimed plan survives three consecutive surveys without a dispatch.
- Postfix: the mode directive postfix vocabulary of the launch wording (exec, author, dual, their aliases, and the survey wording family) the Mode binding classifies.
- Runtime overlay: the runtime-specific companion file agents/skills/maintenance/zcode.md, loaded only on the ZCode runtime.
- Merge landing lock: the repo-keyed lock serializing every landing critical section on the default branch.
- Zero-survivor gate: the Validation item counting loop[_-]mode references on the governed surfaces.
- Revisions ledger: the `## Revisions` section at the end of SKILL.md, the file's change history of record.
- Monitor: the rolling prompt log duties step (read, prune, freeze, dispatch, investigate) the scheduler turn runs over the rolling logs.
- Public-hygiene scan: the repository's hygiene gate script (scan-public-hygiene.sh), exit 0 required before any commit.
- Readiness pre-round: the plan_readiness.py --pre-round invocation over the plan bytes, passing on `OUTCOME: pass`.
- Machinery registry: scripts/machinery_registry.json, the registered-machinery inventory whose removals record lists retired machinery with witnesses.
- Fold time: the moment this plan's landing commit lands; measurements tagged at fold time are taken then, not at authoring.
- Turn-cap paragraph: the per-turn bound paragraph on main landed by the same-day scheduler-second-execution-leg plan (one clocked dispatch plus the directive-bound second execution leg).
- Urgency-first selection: the exec-mode rule that builds one urgency-ordered candidate set (Task 3) and dispatches its most urgent member.
- Failure caps: the failure-cap machinery in SKILL.md's Failure detection and the failure cap section (three strikes stop scheduling); per-lane caps: the per-turn and per-lane dispatch bounds of Step 2.

## Why

The loop runs both lanes on every turn regardless of what the operator wants from that run, at one effort setting, and its only mode machinery is a persisted state field whose live value today is the inert dual default plus directive and note text whose persistence no surviving consumer requires once modes bind per session (the migration Task 2 prescribes carries the live text out before the deletion). A per-session binding gives the operator the same control with less machinery, and urgency-first selection lets exec sessions take the most urgent work whether it is a plan or a simple item. Autonomous authoring and execution must also never run in company or undeclared projects.

## Outcome

Maintenance sessions bind author or exec at launch, work only their mode's lane at the paired effort, switch work automatically on starvation, and execute simple backlog items ad-hoc under the review panel; the persisted loop_mode machinery is gone; company and undeclared projects run survey-only.

- An operator launches "maintenance exec" and the session takes the most urgent allowed item, plan or ad-hoc, at reduced effort, reporting its mode.
- A starved mode switches to the other lane's work in the same session instead of idling.
- Simple backlog items reach done through EXEC-PROMPTS.md entries and reviewed ad-hoc landings without a plan.
- The scheduler state file, the parent prompt, and the child payloads carry no mode field; the retirement surface measured at fold time disappears (21 pre-Revisions gate lines in SKILL.md, 2 in zcode.md, 7 in prompt-templates.md, the suite's loop_mode pins, and the registry entry).
- A company-profile or undeclared project never sees autonomous authoring or execution.

Gate delta: additions, each priced: (1) the project-class guard refusal (a new survey-only resolution class) is the operator-directed pet-project policy recorded in this plan's interview, paying sibling: the existing guard stack gains one read of the already-surveyed priority profile, no new survey pass; (2) the ad-hoc arm's panel-before-landing gate and eligibility test pay their rent through operator directive D-2's review requirement for ad-hoc fixes (its 2026-10-06 panel-route resolution recorded in Terms) and the witnessed stray-close incident that produced D-2; (3) the starvation switch is a resolution path, not a gate, witnessed by the 2026-09-28 dark-gap incident the continue-loop condition already records; (4) the monitor's EXEC-PROMPTS duties extend the existing rolling-log monitor with its own gates, no new protocol layer. Removals: the loop_mode state field and paragraph, the mode appendix paragraph and its self-heal arm, the mode-held retention, the two directive writer clauses' loop_mode members, the blueprint sourcing sentences; a claimed simplification naming concrete removals. The guard liveness ledger's catch-to-incident ratio, re-measured at fold time, is 7:12 (scripts/gate_liveness_ledger.py show, 2026-10-06T18:39Z; the ledger is live state and drifts as rows land, so the reviewer re-measures rather than trusting this figure).

## Assumptions

- assume "in parallel" means selection-time consideration of both work kinds; the per-turn bound is one clocked execution dispatch plus the directive-bound second execution leg exactly as main's turn-cap paragraph provides (the second leg stays plans-only and never carries ad-hoc or EXEC-PROMPTS targets); basis: the fleet-cap doctrine (P54/P57) as qualified by the same-day turn-cap landing.
- assume the ad-hoc arm is gated to exec-mode sessions; dual sessions keep plans-only selection; basis: the operator's original "the latter mode" framing.
- assume mode visibility means each session's opening and closing reports and every readiness report name the bound mode; basis: the operator's 2026-10-06 visibility requirement, re-aimed per-session.
- assume nonstop means within-run one-item-after-another chaining under the standing D-3/D-4 cadences, whose payloads bind their modes naturally; the carrier cadence is untouched; basis: the operator's own D-3/D-4 directive texts.
- assume one plan covers all pieces; basis: the shared-file seam rule (Tasks 1-3 each edit agents/skills/maintenance/SKILL.md; Task 4 is integration-only over the plan's companion surfaces).
- assume companion pins are reconciled in scripts/check_maintenance_pins.sh in the same landing as the bytes they pin; basis: repo convention on every landed change to these files.

Decision points requiring a grill: effort pairing is mode-coupled, dual sessions keep the 2026-09-15 per-lane defaults (user answer 2026-10-06, affects the zcode.md policy and the Loop modes section); starvation switches automatically with effort following the switched work, session-local by construction (user answer 2026-10-06, affects the Loop modes bypass and Step 3); ad-hoc eligibility is plan-uncovered items that are formal-class per the receiving-review triage class or carry a body-named single-surface fix with no open design choice (never guard-bearing paths, never profile-deferred), with the panel before the merge-locked landing (user answer 2026-10-06, affects the Step 3 arm); the mode is per-session, set by the launch wording or one interactive launch question, never persisted (user message 2026-10-06, affects the Loop modes binding); the persisted loop_mode machinery is retired in this plan with cycles_completed re-homed onto authoring_cycle_gate (user answer 2026-10-06, affects Task 2); work-type classification lives at investigate time feeding EXEC-PROMPTS.md (user answer 2026-10-06, affects Task 3); selection is urgency-first over the unified set with starvation as the empty set (user message 2026-10-06, affects Task 3); the project-class guard makes company-profile and undeclared projects survey-only in every mode with an interactive confirmation ask and unattended reporting (user message and answer 2026-10-06, affects the Loop modes guard).

## Standing constraints

- Runtime-agnostic surface: agents/skills/maintenance/SKILL.md names no runtime primitive; concrete settings live in the runtime overlay.
- One-home naming: every new rule is stated once and referenced by name; no restatements.
- No semantic child-blueprint changes: prompt-templates.md edits in this plan are limited to the mechanical retirement re-aims Task 2 enumerates.
- Pin and text reconcile in the same task: a byte change that breaks or obligates a pins-suite span reconciles that span in the same task, keeping the suite green at every task boundary.
- The archived-plan fences, failure caps, merge landing lock, per-lane caps, and the D-2 archive refusal keep their thresholds and existing predicates unchanged; Task 3's additions to the failure-cap progress predicate and the queued-execution fence's aging bound are additive carve-outs on top of them.

## Gist & Examples

TLDR: per-session author and exec modes with per-mode effort, urgency-first selection, starvation switching, and a pet-project guard, replacing the persisted loop_mode machinery, for simplicity (a mode field and its appendix machinery are deleted) and automation (the loop self-switches lanes and effort without manual re-direction).

A session launched with "maintenance exec" in this repository binds exec: it reports "mode: exec (session)" in its opening line, surveys the candidate set (dispatchable plans, ready EXEC-PROMPTS.md entries, directly eligible simple items), and works the most urgent one at reduced effort; when the set empties it switches to author work at high effort in the same session rather than idling. An ad-hoc item runs in its own worktree, passes the doing-code-review panel and the hygiene scan, and lands as one merge-locked squash commit that deletes the backlog row it completed. A session launched with "maintenance author" binds author and works uncovered items one by one; its freshly landed plans queue in queued_execution and wait, without tripping the starvation fence, because the mode makes the pile expected. The nightly scheduler payload names no mode and runs dual, today's behavior. In a company-profile repository every session reports the class guard and works survey-only, and an interactive launch is asked the one confirmation question; the answer never enables authoring or execution there.

The deletion side: the state file loses its loop_mode field, the parent prompt loses its mode appendix, the child payloads lose their appendix-sourcing sentences, the guards lose the mode-held retention, and the readiness report reads the session's own binding instead of a state field.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the pins suite, the public-hygiene scan, and the readiness pre-round all exit 0 on the landing tree; every validation grep is fail-closed per file.
- completeness: no loop[_-]mode reference survives on the governed surfaces (the three skill files outside SKILL.md's Revisions ledger, the reconciled pins suite carrying its own gate literals, the registry removals record); frozen history (docs/history/) is exempt; every retired span's live consumer is re-aimed in the same landing.
- consistency: each new rule has one named home in SKILL.md; cross-references use the name; no semantic child-blueprint change; one name owns the eligibility concept (the Terms' "eligibility test").
- reviewability: review rounds certify with zero blocking findings before landing.

**Done when:**
- `bash scripts/check_maintenance_pins.sh` exits 0 with "maintenance pins: all hold" on the landing tree.
- The zero-survivor gate over SKILL.md, zcode.md, and prompt-templates.md (Revisions excluded) counts zero loop_mode hits.
- `python3` registry-removal check (Validation item 7): entries lack `state-field:loop_mode` and the removals record carries it.
- The readiness pre-round invocation exits 0 with `OUTCOME: pass`.

**Ship when:**
- A postfix-launched session in a personal-profile project reports its mode, works the urgency-first set at the paired effort, and switches on starvation; a company or undeclared project shows the survey-only guard line. No deploy step exists; the next scheduler or authoring fire carries the behavior.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/investigate/SKILL.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `docs/history/backlog/EXEC-PROMPTS.md` *(new; a tracked corpus document created by this plan)*

**Tests:**
- `scripts/check_maintenance_pins.sh`
- `scripts/machinery_registry.json`
- `scripts/check_prompt_log_origins.py`
- `scripts/test_check_prompt_log_origins.py`
- `scripts/validate_review_staging.py`

**Plan-related extension:** implementation and review may change files not listed above when causally related: a retired span's consumer this plan missed, a pins-suite span the re-aims orphaned, or a doc reference the retirement staled. Weak or speculative links drop as out of scope with a one-line reason.

**Documentation:**
- `README.md`
- `docs/history/backlog/PLAN-PROMPTS.md` *(header rule text gains the ad-hoc witness class)*

The README catalog rows for maintenance and investigate are explicit must-fix; other docs only under plan-related extension.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/prompt-templates.md` semantic body; reason: child blueprints are frozen except Task 2's enumerated mechanical retirement re-aims.
- `docs/history/plans/2026-10-05-execute-plan-done-boundary-evidence-gates.md`; reason: its single loop_mode mention is a historical assumption citation and its subject is unrelated.
- `docs/maintenance/operator-directives.md`; reason: the operator declined directives-home rows for mode or class regulation.

## Validation Commands

Validation preamble, round-start state for r1: recorded at authoring time in the execution record; the format gates (em-dash scan over the plan bytes, public-hygiene scan, readiness pre-round) run before the first review round and their outcomes are recorded in the review staging doc; the zero-survivor sweep is RED today (21 SKILL.md pre-Revisions gate lines matching either spelling, 15 lines carry the underscore spelling, 8 the hyphen spelling, 2 carry both, 2 zcode.md, 7 prompt-templates.md) and flips GREEN at Task 2; the presence gates for the section heading, binding marker, bypass token, guard resolution span, exemption token, selection span, panel receipt, verdict span, effort marker, and the doing-code-review span are all RED today (each measured absent) and flip GREEN at their owning tasks; the sweep's targets are exactly the three skill files item 3 names (the pins suite is the gate's home, not a target), so no self-match escape is needed.

```bash
# Run from the repository root. Every gate is fail-closed; any failure exits non-zero.

# 1. Pins suite (every task boundary and the final gate)
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite"; exit 1; }
tail -1 /dev/null # suite prints its own "maintenance pins: all hold" final line

# 2. Public-hygiene scan
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh || { echo "FAIL: hygiene"; exit 1; }

# 3. Zero-survivor gate: no loop[_-]mode spelling outside the SKILL.md Revisions ledger (Task 2; zcode.md and prompt-templates.md carry no Revisions heading, so their counts are whole-file)
n=$(awk '/^## Revisions/{exit} {print}' agents/skills/maintenance/SKILL.md | grep -cE 'loop[_-]mode' || true)
if [ "$n" -ne 0 ]; then echo "FAIL: SKILL.md carries $n loop_mode references outside Revisions"; exit 1; fi
for f in agents/skills/maintenance/zcode.md agents/skills/maintenance/prompt-templates.md; do
  test -f "$f" || { echo "FAIL: $f missing"; exit 1; }
  n=$(grep -cE 'loop[_-]mode' "$f" || true)
  if [ "$n" -ne 0 ]; then echo "FAIL: $f carries $n loop_mode references"; exit 1; fi
done

# 4. Per-session machinery presence (Task 1), one dedicated grep per obligation, each a prescribed contiguous span
grep -qF '## Loop modes' agents/skills/maintenance/SKILL.md || { echo "FAIL: Loop modes section"; exit 1; }
grep -qF 'Mode binding.' agents/skills/maintenance/SKILL.md || { echo "FAIL: binding paragraph marker"; exit 1; }
grep -qF 'mode-starved-bypass' agents/skills/maintenance/SKILL.md || { echo "FAIL: starvation switch token"; exit 1; }
grep -qF 'resolves both work lanes to survey-only' agents/skills/maintenance/SKILL.md || { echo "FAIL: class guard resolution span"; exit 1; }
grep -qF 'class-guard-survey-only' agents/skills/maintenance/SKILL.md || { echo "FAIL: guard exemption token"; exit 1; }
grep -qF 'Mode enforcement.' agents/skills/maintenance/SKILL.md || { echo "FAIL: enforcement marker"; exit 1; }
grep -qF 'mode: <author|exec|dual|survey> (session)' agents/skills/maintenance/SKILL.md || { echo "FAIL: visibility format"; exit 1; }

# 5. Exec-mode machinery presence (Task 3)
grep -qF 'urgency-ordered candidate set' agents/skills/maintenance/SKILL.md || { echo "FAIL: unified selection"; exit 1; }
grep -qF 'Ad-hoc-panel-pass:' agents/skills/maintenance/SKILL.md || { echo "FAIL: panel receipt literal"; exit 1; }
grep -qF 'work-type verdict' agents/skills/investigate/SKILL.md || { echo "FAIL: investigate verdict"; exit 1; }
test -f docs/history/backlog/EXEC-PROMPTS.md || { echo "FAIL: EXEC-PROMPTS.md missing"; exit 1; }
grep -qF 'EXEC-PROMPTS.md' agents/skills/maintenance/SKILL.md || { echo "FAIL: dual-log exclusion wiring"; exit 1; }
grep -qF 'ad-hoc-superseded' docs/history/backlog/PLAN-PROMPTS.md || { echo "FAIL: PLAN-PROMPTS prune witness class"; exit 1; }
~/.agents/venvs/ai-playbook-test/bin/python -m pytest scripts/test_check_prompt_log_origins.py -q || { echo "FAIL: prune-audit probe"; exit 1; }

# 6. Task 4 spans: effort policy heading and the doing-code-review integration
grep -qF 'Mode-coupled effort pairing' agents/skills/maintenance/zcode.md || { echo "FAIL: effort policy heading"; exit 1; }
grep -qF 'Source digest' agents/skills/review-staging/SKILL.md || { echo "FAIL: staging digest field"; exit 1; }
grep -qF 'ad-hoc' agents/skills/doing-code-review/SKILL.md || { echo "FAIL: review-panel integration"; exit 1; }
grep -qF 'ad-hoc backlog arm' agents/skills/doing-code-review/SKILL.md || { echo "FAIL: review-panel integration"; exit 1; }

# 7. Machinery registry removal is recorded (Task 2); the inventory's pre-existing unrelated findings are out of scope
python3 - <<'PYEOF' || { echo "FAIL: machinery registry removal"; exit 1; }
import json
r = json.load(open('scripts/machinery_registry.json'))
blob = json.dumps(r)
assert 'state-field:loop_mode' not in [e.get('id') for e in r.get('entries', [])], 'entries still carry state-field:loop_mode'
assert 'state-field:loop_mode' in blob, 'removals record missing state-field:loop_mode'
print('registry removal recorded')
PYEOF

# 8. Readiness pre-round
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-06-two-mode-loop-policy.md || { echo "FAIL: readiness pre-round"; exit 1; }
python3 scripts/check_investigate_entries.py --log docs/history/backlog/EXEC-PROMPTS.md || { echo "FAIL: EXEC-PROMPTS entry validation"; exit 1; }
python3 scripts/check_backlog_inbox_location.py || { echo "FAIL: backlog inbox location"; exit 1; }
```

### Task 1: Per-session mode machinery in the maintenance skill

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/SKILL.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the suite stays green at this boundary
- Validation Commands block items 1, 2, and 4; covers the section, binding, bypass token, and guard spans exist

- [ ] Insert the `## Loop modes` section between the Cycle gate section and the Configuration section, owning five named paragraphs: Mode binding, Mode enforcement, Starvation switch, Mode visibility, Project-class guard [class: IMPLEMENTATION_REQUIRED]
- [ ] Mode binding paragraph (opens with the literal marker `Mode binding.` so the validation needle and the companion pin read a prescribed contiguous span): the session classifies its own directive at launch; the postfix vocabulary classifies exec, execute, execution wording as exec mode, author, authoring wording as author mode, both, dual, alternation wording as dual, and survey, survey-only, stand-down wording routes the session through the Project-class guard paragraph's survey-only resolution with precedence over any competing postfix wording (survey and stand-down wording outrank both-lanes wording, and the dual resolution applies only to payloads carrying no survey or stand-down wording), so it inherits the guard's resolution, the class-guard-survey-only token family, and the visibility format; the queue-depth token and the corpus freshness rule read both rolling logs per Task 3's re-aims; an interactive session (one whose current directive arrived in a live human-typed message; automation-originated sessions are unattended regardless of wording provenance) whose wording supports no classification asks exactly one launch question; both-lanes wording outranks single-lane tokens in one payload (an exec+author mandate resolves dual), and an unattended session whose wording is absent or supports no confident classification runs dual and records the ambiguity in its decision channels (the launch question is interactive-only by construction); the bound mode lives only in the session's context, never persisted as a scheduler-state field, its only records being the per-turn mode token and the report line, and the session records it in its decision channels, each turn's decision_reason carries the token `mode:<author|exec|dual|survey>` beside the lane decisions [class: IMPLEMENTATION_REQUIRED]
- [ ] Mode enforcement paragraph (opens with the literal marker `Mode enforcement.` mirroring the binding marker; its prescribed content includes the survey_only flag's operative read and write duty: the paragraph reads the state file's survey_only flag as an operator-set all-lane stand-down input each lane decision consults, and an operator-directed turn receiving a lane-stop or lane-open directive writes the flag via one targeted field edit in that turn, before the turn ends, beside the decision record, a lane-stop directive whose wording scopes to one lane resolving explicitly: the turn either writes the flag with the over-broad all-lane consequence recorded in decision_reason and named in the turn report, or refuses the flag write and surfaces that only an all-lane stop persists across sessions; the targeted edit rides the sanctioned-writer enumeration's existing scheduler-turn class (no ninth writer class) and the Step 6 carry-forward enumeration gains `survey_only` (written outside Step 6 by this operator-directed targeted edit, so the rewrite must carry it; Task 2's carry-forward edit lands the enumeration change)): the per-lane decision reads the session's bound mode first; author mode resolves D1 and D4 to D3 with the mode recorded in that lane's decision_reason, exec mode resolves D2 to D3; dual is inert; this paragraph is the Step 3 enforcement's source of record from Task 2 onward [class: IMPLEMENTATION_REQUIRED]
- [ ] Starvation switch paragraph: the per-mode starvation predicates (author mode starved when the authoring lane's inputs are empty per D2's selection rules, the rolling-log readiness, and the investigate leg's set; exec mode starved when the execution lane's candidate set from Task 3 is empty); the switch lifts the exclusion for the turn, records `mode-starved-bypass:<lane>` in decision_reason, and the effort pairing follows the switched work (where the runtime fixes effort at launch, the switched turn records the effort mismatch in decision_reason and the escalation rides the next payload rather than an impossible mid-run change); the switched turn runs the other lane's own machinery, for the execution lane, D1's plans-only selection (the ad-hoc arm and EXEC-PROMPTS entries stay gated to sessions bound exec), for the authoring lane, D2's selection rules; per the Mode binding paragraph, the bound mode stays session-local (never persisted, never read back) [class: IMPLEMENTATION_REQUIRED]
- [ ] Mode visibility paragraph: every maintenance session's opening report and closing report names its bound mode in one line (`mode: <author|exec|dual|survey> (session)`); the Cycle gate readiness report names the session's mode beside the live-loop fields [class: IMPLEMENTATION_REQUIRED]
- [ ] Project-class guard paragraph (opens with the literal marker `Project-class guard.`): the survey's Priority-profile resolution records the profile class; a company-profile or undeclared project resolves both work lanes to survey-only in every mode, the guard outranks the mode machinery, an interactive launch asks the confirmation question ("this project is company-class or undeclared; the loop runs survey-only here; confirm you want the loop session at all?") and records the answer in the turn record, an unattended session reports the guard line and stands the lanes down; the guard never reads or writes any directives-home row. Fail-closed class resolution, unconditional for survey-worded sessions: a session whose binding classified survey wording resolves both lanes to survey-only regardless of the recorded profile class, recording the class-guard-survey-only token beside the recorded class and inheriting the same survey-only shape (monitor holds, registry holds, read and audit arms live). A missing facts file, a missing profile block, and a block whose text names no class all record class=undeclared and resolve survey-only; the class token (`personal` or `company`) may sit anywhere in the block's text, and a block naming both, qualifying, or negating either token records class=undeclared; the default profile's ordering applies to survey grouping only and never classifies the project personal; an explicit personal declaration is the only lanes-live record for a non-survey binding. The state file's incident survey_only flag gains its standing reader in the Mode enforcement paragraph (by name); the guard never writes or clears the flag, and the flag never changes the recorded profile class, so an operator lane stop propagates across sessions through one machine-readable switch; the guard never writes or clears the flag and the flag never changes the recorded profile class; the flag remains an undocumented operator surface whose only contract is this reader text, no schema paragraph is added for it and the machinery registry stays untouched. Under survey-only the monitor's corpus-write duties (log appends, prune and freeze commits) hold with the standing reason recorded and its read and audit arms still run, and the registry consult's audit-kind and re-triage dispatches are held the same way (their due-read records the standing class-guard-survey-only reason and the task re-fires next turn) [class: IMPLEMENTATION_REQUIRED]
- [ ] Name the guard's no-dispatch resolution in the sanctioned must-dispatch exemption vocabulary: a survey-only turn records the token `class-guard-survey-only` beside the recorded profile class in decision_reason as a sanctioned must-dispatch exemption (no dispatch-defect turn_error), and the Human check on a stalled loop paragraph names the class-guard reason so a guard-idled loop is diagnosable from the state file alone [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the Step 1 Priority-profile resolution bullet to record the profile class per the Project-class guard paragraph's fail-closed resolution (which owns the absent-profile branch and the default-profile clause by name); the recorded class rides the survey output beside the per-item tokens so the guard reads survey output, not a second read [class: IMPLEMENTATION_REQUIRED]
- [ ] Register companion presence pins for the section heading, the binding vocabulary literals, the bypass token, the guard literals, the enforcement marker, the visibility format literal, and the survey_only write-duty span in scripts/check_maintenance_pins.sh; run the suite green [class: REPOSITORY_TEST]
- [ ] Run the pins suite and Validation Commands items 1, 2, and 4; expect GREEN on item 4's spans and unchanged suite outcome [class: REPOSITORY_TEST]

### Task 2: Retire the persisted loop_mode machinery

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/maintenance/zcode.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`
- `scripts/machinery_registry.json`

Evidence:
- Validation Commands block item 3 (zero-survivor gate, both spellings); covers the deletion is complete outside the SKILL.md Revisions ledger
- Validation Commands block item 7 (registry-removal check); covers the removal is recorded
- `bash scripts/check_maintenance_pins.sh`; covers pin and text reconciled in the same task

- [ ] Migration-before-deletion: before any Task 2 deletion, read the live `loop_mode` value from the primary checkout's scheduler state file, the read-export-delete running as one sequence with the export read immediately preceding the live state-file line deletion; export the field's recorded `directive` string, `note` string, `set_at`, every live member the field paragraph does not declare (today's beyond-schema `notes[]` entries), and the live `cycles_completed` value when present into the local execution record only (a gitignored surface beside the execution record; the bulk text never enters the landing tree or permanent public history); the landing commit message carries the marker `loop-mode-directive-export:` followed only by the exported text's sha256 digest; if the live value carries a non-dual mode, surface it to the operator before deleting; verify the surviving directive surfaces (the directives home, the `authoring_cycle_gate` directive field, and live operator messages) cover the lanes the retired directive text covered before the zero-survivor gate runs [class: IMPLEMENTATION_REQUIRED]
- [ ] Rewrite the Step 3 loop-mode enforcement paragraph to read the session's bound mode per the Mode enforcement paragraph (Task 1's section), deleting the state-field source, the mode-appendix freshness test references, and the `loop-mode-held` retention; the exclusion semantics are otherwise unchanged; add the starvation switch sentences referencing the Loop modes section by name [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-aim the surviving hyphenated and directive-text name references the retirement strands: the Step 0 rearm-on-touch Consultation's fresh `loop_mode` write cannot-decide trigger (delete the trigger), the Step 1 Pending re-arm reader's mode-appendix parenthetical (delete), the execution_priority paragraph's cleared_at precedent mention (re-point to the surviving `authoring_cycle_gate` cleared trace), the `authoring_cycle_gate` field paragraph's two `loop_mode` precedent mentions (reword to the cleared-trace precedent without the retired name), the Cycle-gate continuation-classification mirror's `loop_mode.directive` copy in zcode.md (re-aim to the session's mode binding), D1's two sanctioned-reason enumerations and the Parked re-arm discharge precedence and Parked-intent discharge (park-discharge duty) gate lists' `loop-mode` members (rename to the mode-exclusion vocabulary), D3's precedence sentence naming the loop-mode enforcement paragraph (re-point at the Mode enforcement paragraph by name), the fate bullet's keeps-its-precedence sentence naming the same paragraph (re-point identically), and the rolling prompt log duties' standing exclusion naming loop-mode enforcement (re-word to the Mode enforcement paragraph) [class: IMPLEMENTATION_REQUIRED]
- [ ] Delete the state file's `loop_mode` JSON block line and the whole `loop_mode` field paragraph; re-home `cycles_completed` onto the `authoring_cycle_gate` field paragraph as an additive optional key stated inside that paragraph's text (never as a new `X is` field paragraph, so the machinery inventory's state-field parser sees no new top-level field) whose drop leg fires only when the pacing directive itself is withdrawn (an explicit withdrawal record), a cycle-start clear preserving the count; re-aim the closeout targeted edit's increment leg to write `authoring_cycle_gate.cycles_completed` under the same writer condition and add that span to the re-aim enumeration; pin the chosen semantics in the re-homed paragraph text [class: IMPLEMENTATION_REQUIRED]
- [ ] Delete the scheduler-turn and rearm-on-touch writer classes' `loop_mode` write/replace members, keeping each clause's `authoring_cycle_gate` clear leg as the directive-write clause's surviving member; drop `loop_mode` from the Step 6 carry-forward enumeration, keeping `pending_rearm` and adding `survey_only` per Task 1's Mode enforcement persistence leg (written outside Step 6 by the operator-directed targeted edit, so the rewrite must carry it) [class: IMPLEMENTATION_REQUIRED]
- [ ] Delete the Step 0 self-heal arm's mode-appendix legs (detection, repair, removal, and their precheck and bound records); the surviving shape is explicit: the live-bound condition and its structured-first-line token registry and the precheck-discipline reference survive hosted by the rearm-on-touch bullet's remaining contracts, and the appendix-triggered legs are deleted whole [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-aim the G1a target-distinctness rule's standing-directive parenthetical from the state field to the session's bound mode or an explicit standing directive in the dispatching payload; re-aim the near-reset carve-out's directive surfaces from `loop_mode` to the session's mode binding and the `authoring_cycle_gate` directive field, stating the re-aimed predicate: a session whose bound mode is author, exec, or dual counts as covered for its own lane by construction (the binding is directive-derived and the mode policy makes the lane nonstop), the gate field keeps its textual continuity-phrasing test, and the witness precedence enumerates the mode-binding token in place of the retired field; re-aim the Cycle gate readiness report's recorded-wording phrase from `loop_mode.directive` to the session's mode binding [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-aim the Step 1 pending-dispatch reader: delete the `loop-mode-held` retention and its label-precedence mentions, keeping the `cycle-gate-armed` retention and the rate-pressure gates unchanged [class: IMPLEMENTATION_REQUIRED]
- [ ] Delete the zcode.md Mode appendix paragraph; the recipe template and the recognition rule keep their byte-identical opening line and title [class: IMPLEMENTATION_REQUIRED]
- [ ] Re-aim the prompt-templates.md retirement spans: delete both re-arm duty paragraphs' mode-appendix sourcing sentences, the successor re-create sourcing sentence, the successor chain-nothing loop-mode condition, and the stray-close quote-coordination bullet's `loop_mode` directive clause; the chain-nothing condition's cross-session lane restriction moves to the survey_only flag's new standing reader (Task 1's Mode enforcement paragraph: operator-set, all-lane, session-spanning; the witnessed 2026-10-02/03 stop-class incidents are its paying witnesses), so an operator lane stop told to any session still constrains successor chains; no other blueprint sentence changes, and the registry annotation bullets describing the retired edits (prompt-templates.md's re-arm duty and successor re-create mode-appendix sourcing annotations) are deleted together with the edits they describe [class: IMPLEMENTATION_REQUIRED]
- [ ] Reconcile the machinery registry: move the `state-field:loop_mode` entry to the removals list with this plan as the witness; this plan makes no other registry change and the inventory's pre-existing unrelated findings are out of scope [class: REPOSITORY_TEST]
- [ ] Reconcile the suite's loop_mode pins: delete pins over deleted spans, re-aim pins over re-aimed spans to their new literals, the compound state-schema presence check reducing to its pending_rearm half when the loop_mode schema line is deleted, add the zero-survivor count gate matching both spellings (`loop[_-]mode`), scoped whole-file for zcode.md and prompt-templates.md (neither carries a Revisions heading) and pre-Revisions for SKILL.md; reconcile the union tree's pins including the same-day turn-cap spans (the cap second-execution-leg pin and the fired-arm carve-out pin landed on main after this plan's snapshot); run the suite green on the landing tree (its built-in selftest included), and for each new or re-aimed pin record a RED flip probe run against a full second checkout (git init plus the complete pinned-file set) with the mutated pin's exact `PIN FAIL:` line as the recorded observable [class: REPOSITORY_TEST]
- [ ] Verify the migration evidence at its runnable boundary: after the landing commit exists, extract the digest from the commit message's `loop-mode-directive-export:` line, compute sha256 over the local execution record's exported-text span, and require equality (failing closed on mismatch, mirroring the receipt pattern), the verification running before any tmp-cleanup window can touch the local record; record both in the execution record [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: Validation Commands items 1, 3, and 7 [class: REPOSITORY_TEST]

### Task 3: Exec-mode work machinery and the ad-hoc arm

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/SKILL.md`
- `agents/skills/investigate/SKILL.md`
- `docs/history/backlog/EXEC-PROMPTS.md` *(new)*
- `docs/history/backlog/PLAN-PROMPTS.md`
- `scripts/check_maintenance_pins.sh`
- `scripts/check_prompt_log_origins.py`
- `scripts/test_check_prompt_log_origins.py`

Evidence:
- Validation Commands block item 5; covers the unified selection, ad-hoc arm, verdict, and log file spans, and the extended prune-audit's fail-closed probe (the doing-code-review span is item 6's, satisfied at Task 4)
- `bash scripts/check_maintenance_pins.sh`; covers the suite stays green at this boundary

- [ ] Step 3 exec-mode selection rule: an exec-mode session with a free execution lane builds one urgency-ordered candidate set from dispatchable open plans (D1's inputs and skip classes), ready unfrozen EXEC-PROMPTS.md entries, and directly ad-hoc-eligible open items, and dispatches the most urgent; D1's selection priorities carry: an actionable parked_dependencies entry selects the unblock dispatch ahead of the merged set (still through the guards, quota leg, landing gate, and rate-pressure condition), and the fresh-plan continuation preference orders within the plans segment. Ordering contract: the `execution_queue` head and `execution_priority` read first exactly as D1's Queue and priority ordering provides (by reference); the merged remainder orders cross-kind as plans (D1's ordering), then ready EXEC-PROMPTS entries (log position), then ad-hoc-eligible items (the priority profile's group with the consumer-urgency exception, then the oldest-basename tiebreak), with the consumer-urgency exception promoting its item ahead of the preceding segment; the deciding session records the taken ordering in decision_reason. Inherited gates, named: the guards, the certification oracle for plans, the Step 4 quota leg with the Quota-aware lane decisions' near-reset branch and governor policy, the rate-pressure deferral, the Execution-lane carrier-selection ordering for the in-session leg, D4, and the landing gate apply as today; the integrity defers outrank the session mode. The per-turn bound is one clocked execution dispatch plus the directive-bound second execution leg as the turn-cap paragraph provides (that second leg stays plans-only and never carries ad-hoc or EXEC-PROMPTS targets, and its fired-arm sibling applies unchanged) [class: IMPLEMENTATION_REQUIRED]
- [ ] Ad-hoc backlog arm bullet in Step 3: the ad-hoc path of the selection rule runs in-session with kind `adhoc` in its own ad-hoc worktree per the worktree-first standard; the eligibility test is the Terms definition stated once here with its mechanical denylist: the pins suite, the machinery registry, the skills' guard and mode paragraphs, and the state-schema field paragraphs are never ad-hoc-eligible surfaces, enforced mechanically at the same fail-closed containment step as a per-hunk ALLOWLIST: banned whole paths (the pins suite, the machinery registry, and doing-code-review/SKILL.md as the panel of record, plan route only) fail by path, and every remaining diff hunk must classify against the item's named surface span(s) or the sanctioned companion paths, failing closed on any hunk outside them (the allowlist covers every skill by construction; no marker enumeration to drift); the doing-code-review panel over the run's full branch delta runs before any landing with blocking findings folded first, the folding edits and the backlog-row deletion edit are made on the worktree branch BEFORE the final panel run, so the panel reviews the exact bytes to be landed and the receipt digest is taken from that final reviewed head, then the public-hygiene scan and the pins suite (both exit 0 required; a suite failure stands the landing down with a recorded reason and any broken span is reconciled in the same run, mirroring the standing constraint), then one merge-landing-lock-serialized squash landing whose commit carries the machine-checkable receipt line `Ad-hoc-panel-pass: <review record path> <Source digest>`, the digest being the staging record's own canonical `Source digest` field (review-staging's owned sha256 of the exact reviewed bytes, recomputed at the final post-fold panel run; no twin field is invented), and whose critical section re-derives the sha256 over the branch's diff against its merge base at the head being landed (the same byte function the record's `Source digest` was computed over) and requires the three-way equality receipt digest == record Source digest == re-derived head while checking the zero-blocking verdict against the record's findings rules, failing closed on an absent or unparseable pass, on a reference that does not resolve (the receipt's form is the review record path only: the path must exist in the reviews home and its verdict must record zero blocking findings; every panel run writes a staging record, so no second resolution form exists), and on a digest mismatch (bytes amended after the panel re-enter the panel); the same fail-closed check verifies scope containment: the branch diff's changed paths all sit under the item's named surface(s), for a formal-class item, the surface the triage record records, plus the arm's sanctioned companion paths (the completed item's own backlog row, the pre-landing PLAN-PROMPTS freeze edit, the pre-landing EXEC-PROMPTS freeze edit, and the folding edits bounded to panel findings), and the diff carries no state-schema, guard, or machinery bytes; the landing deletes the completed backlog row only after re-verifying the row still sits at the recorded top-level path (a peer move stands the deletion down with a recorded reason) and no open plan or live execution child covers the item's origins (a covering plan or in-flight execution stands the landing down with a recorded reason). Quota-scarce or otherwise dispatch-blocked conditions hold the item with a recorded reason as sanctioned must-dispatch exemption vocabulary, never a scheduled-child payload route; the arm never authors, edits, or archives plan files; directive D-2's 2026-10-06 panel-route resolution (the operator interview answer recorded in Terms) rides this landed text beside the directives home's record, so a session honoring the Step 0 home read resolves the plan-free reviewed landing as sanctioned [class: IMPLEMENTATION_REQUIRED]
- [ ] Ad-hoc candidate consults, mirroring the existing lanes: a candidate whose fresh foreign authoring claim or live peer entry sits on the item is skipped as occupied with the recorded sanctioned reason (D2's fresh-foreign-claim consult mirrored); a candidate whose origins intersect any live rolling-log entry's origins is skipped so the entry routes the work (D2's machinery mapping mirrored) [class: IMPLEMENTATION_REQUIRED]
- [ ] Supporting arms: the widened arm's marker classification gains an ad-hoc marker occupying only the execution lane; the state-file arm's completion evidence gains the ad-hoc kind keyed on the run's own landing receipt (the target item's absence attributable to this run's landing commit, beside the recorded panel pass), never bare absence; the failure-cap progress section gains the ad-hoc predicate (progress means the run's recorded worktree branch tip advanced or the target item left the backlog top level, the deciding turn recording the ad-hoc run's worktree path and branch tip on its own adhoc children[] entry through the in-session write pair's scheduler-turn class, progress_mark carrying the tip like the checkbox precedent, and the predicate comparing the recorded tip across turns; the landing receipt is the terminal witness per the completion-evidence clause); the completion-stranding enumeration names ad-hoc-eligible items and ready EXEC-PROMPTS entries; the queued-execution fence's aging bound gains two carve-outs: the author-mode carve-out (the pile is the mode's expected product) and the class-guard carve-out (while the guard stands the lanes down, an aged entry records the standing class-guard-survey-only reason and the bound does not fire); the rolling prompt log duties' investigate leg fires only when neither log has a ready entry and its origin-intersection skip reads entries in both logs; the in-session entries paragraph and the sanctioned-writer write-pair clause cover the ad-hoc kind, folding ad-hoc state writes into the existing scheduler-turn class (never a ninth writer class) and extending the children[] kind enum in the State file schema block append-only together with the state-file arm's per-kind completion-evidence enumeration (pending_dispatch's enum stays unchanged: blocked ad-hoc work holds with a recorded reason and never parks) [class: IMPLEMENTATION_REQUIRED]
- [ ] Rolling prompt log duties extension: the monitor reads EXEC-PROMPTS.md beside PLAN-PROMPTS.md with the same write discipline; prune an entry when its ad-hoc work completes with an `EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>` receipt; freeze an entry when an ad-hoc run claims it, the freeze edit conditional on the entry still reading unfrozen at write time (the targeted-edit drift-retry rule's re-read before atomic replace names the frozen-entry precondition, failing a second freezer closed), the freeze mark clearing when the run's landing is stood down with a recorded reason or the run aborts without a landing commit (the entry reopens for dispatch); dispatch the top ready entry as the ad-hoc run's context source; when an ad-hoc run completes an item, the monitor freezes any PLAN-PROMPTS.md entry whose origins name the completed item before the landing, and prunes it strictly after the landing commit is recorded, with the recorded landing commit digest as the witness of record (the ad-hoc-superseded removal class: no plan file exists, so the digest substitutes for the plans-root witness, and check_prompt_log_origins.py's prune-audit is extended to enumerate both rolling logs and to accept that witness class rather than flagging REMOVED-WITHOUT-WITNESS; for both logs the audit accepts a removal whose commit carries the `EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>` receipt naming the removed slug, with the landing commit resolving to an existing commit; the extension is verified in the same task by a fail-closed probe in scripts/test_check_prompt_log_origins.py mirroring Task 2's RED-flip discipline: a negative case, an EXEC-PROMPTS.md entry removed without the `EXEC-PROMPTS-PRUNE: <slug> -> <landing commit>` receipt or with a non-matching digest, asserts the audit still exits 1 with REMOVED-WITHOUT-WITNESS, and a positive case, a removal carrying the recorded digest witness, asserts exit 0); the same task amends docs/history/backlog/PLAN-PROMPTS.md's Prune rule text to enumerate the ad-hoc-superseded removal class (a removal whose witness is the recorded ad-hoc landing commit digest substituting for the plans-root witness where no plan file exists, audited by the extended prune-audit), so the log's standing rule and the landed monitor duty name the same removal class, and the Freeze rule's reopen clause gains the matching ad-hoc case; the investigate leg appends by the verdict; the queue-depth token bullet's ready-entry count is re-aimed to sum ready entries across both rolling logs, and the corpus freshness rule's tracked-corpus category is re-aimed to name both logs, and the maintenance skill's own Integration Points investigate bullet is re-aimed to the two-log shape beside these duties re-aims [class: IMPLEMENTATION_REQUIRED]
- [ ] Create docs/history/backlog/EXEC-PROMPTS.md whose header references PLAN-PROMPTS.md's standing rules by the labels that file carries (Order, Prune rule, Freeze rule, Not a backlog item) and whose entries follow that file's Entry template unchanged, the same structural-minimum gate applying per the re-aimed Stage 4 self-check and by their cross-skill established names with their homes named (the targeted-edit drift-retry rules and the same-turn commit duty per agents/skills/maintenance/SKILL.md; repo-relative-only entries), stating only its deltas: the prune witness is the ad-hoc landing commit with the `EXEC-PROMPTS-PRUNE` receipt, the freeze trigger is an ad-hoc run claim, and entries dispatch to exec-mode sessions [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the Step 1 open-backlog listing exclusion and the never-cited-as-Backlog-origin invariant to both rolling prompt logs (PLAN-PROMPTS.md and EXEC-PROMPTS.md under the resolved backlog home), and extend investigate's Stage 0 sweep skip to the EXEC log, so neither log is ever triaged as a backlog item, cited as a plan origin, or swept as an ungrouped item [class: IMPLEMENTATION_REQUIRED]
- [ ] investigate skill: add the work-type verdict step classifying the investigated item plan-worthy or ad-hoc-able per the eligibility test referenced by name from the maintenance skill's ad-hoc arm; route the appended entry to PLAN-PROMPTS.md or EXEC-PROMPTS.md by the verdict; update the frontmatter description, the Purpose/Boundary paragraph, and the Hard gates to the two-log verdict shape, and re-aim the Stage 4 self-check invocation to pass `--log` naming the log the verdict routed the entry to (or run once per destination log), with a companion pin for the re-aimed invocation literal; extend both Integration Points sections to name the routing bidirectionally [class: IMPLEMENTATION_REQUIRED]
- [ ] Register companion pins for the selection rule, the ad-hoc arm span, the fence carve-out, the EXEC-PROMPTS duties, the dual-log survey exclusion, the PLAN-PROMPTS ad-hoc-superseded prune-witness class, and the verdict span; run the suite green [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: Validation Commands item 5 [class: REPOSITORY_TEST]

### Task 4: Effort policy, doc integrations, and the final gate

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/zcode.md`
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `scripts/validate_review_staging.py`
- `README.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- Validation Commands block, the whole block green (items 1 through 8); covers the final landing tree

- [ ] Rewrite the body of the pinned `## Child model and effort policy` section in zcode.md (the section heading is unchanged, so the suite's heading pin holds; the rewritten body leads with the literal `Mode-coupled effort pairing:` as its marker): author-mode work at High effort; exec-mode work at low effort (the runtime's own level name) with escalation to High when the target demands active research or reflection; dual sessions keep the 2026-09-15 per-lane defaults; the runtime-limitation paragraph stands unchanged; the overlay's fleet-member enumeration gains the adhoc kind (fleet members via the execution lane they occupy) with the suite's enumeration pin re-aimed in the same task, and the overlay's child-marker catalog gains the ad-hoc marker definition (occupying only the execution lane; the Task 3 widened-arm classification span is its consumer, this catalog entry its home) [class: IMPLEMENTATION_REQUIRED]
- [ ] doing-code-review: extend the existing `## Integration Points` section with a `With maintenance` subsection naming the ad-hoc backlog arm as the consumer, the panel receiving the worktree branch's diff against its merge base, blocking findings folded before the landing [class: IMPLEMENTATION_REQUIRED]
- [ ] review-staging alignment for ad-hoc panels: the ad-hoc panel's staging record carries its canonical `Source digest` at the final post-fold panel run (over the exact bytes to be landed) and its findings rules express the zero-blocking verdict, both already owned by review-staging's record contract and validator, which join this task's consumed surfaces; validation greps for `Source digest` and the ad-hoc integration join Validation item 6 [class: IMPLEMENTATION_REQUIRED]
- [ ] README: extend the maintenance catalog row with the per-session modes, the urgency-first selection, the starvation switch, and the class guard; add the work-type verdict and EXEC-PROMPTS routing to the investigate row [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the whole Validation Commands block; expect GREEN on every item [class: REPOSITORY_TEST]
