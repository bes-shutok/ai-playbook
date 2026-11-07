# Plan: Resolve the target project suite policy separately from plan validation

Backlog origin: docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md
Driving force: efficiency + code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-execute-plan-project-test-policy-scope-p1d2fb554-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list).
Execution budget: 2h total, largest task 0.5h
Executed: no
Authoring claim: 2026-11-04-execute-plan-project-test-policy-scope.md (session sess_e0d1f436-011c-430a-9f85-4db92acea660)

## Terms

- Suite policy: the target repository's explicit declaration of when its complete repository-standard suite must run, declared as the `test_suite_policy` TOML key in the target repository's `.ai-playbook/facts.md`.
- `full-before-final`: the suite policy value requiring the complete repository-standard suite once before final completion: the Phase 2 boundary in ordinary mode, the run's final stack-task boundary in stack-task mode.
- `focused-never-full`: the suite policy value prohibiting whole-repository suite runs during execution; validation uses plan-specific commands, focused regression tests, and named repository gates.
- Plan-specific validation: the commands a plan lists under `## Validation Commands`, run at the boundaries that plan prescribes.
- Project-wide final validation: the target project's complete-suite obligation at the final boundary, owned by the suite policy, not by any individual plan.
- Phase 2: the execute-plan completion phase that runs plan validation commands and project-wide final validation after all tasks pass.
- Stack-task boundary: the parent-owned light boundary of one `--stack-task` invocation.
- Final stack-task boundary: the boundary whose selected task is the stack plan's last task (no unchecked later task exists at invocation time); this is the boundary that carries the policy's final-boundary obligation.
- Liveness pin suite: `scripts/test_authoring_plans_liveness.py` and the other named focused suites that pin preserved anchors, the targeted coverage whose loss motivated the full-suite requirement.
- Named repository gates: the pinned-file and hygiene gates a `focused-never-full` repository's guidance names (for example this repository's pins suite and public-hygiene scan); they resolve from the same authoritative test-guidance documents as the policy, and a repository whose guidance names none runs no gates and records that resolution in the boundary evidence.
- Certification: the plans authoring gate that finalizes a plan after its review rounds record `ready=yes`; the boundary where the plan-versus-policy conflict duty fires.

## Why

execute-plan treats the complete repository-standard suite as a universal requirement for every plan and every stack-task boundary. For this skills repository that mandate contradicts the operator's standing prohibition on running the whole-repository suite inventory, and the 2026-11-06 Phase 2 run was stopped by the operator after 23 of 84 suites with Phase 2 recorded incomplete. Company projects still need the complete suite before final completion. The two obligations need separate resolution so each repository spends validation time where its policy requires it.

## Gist & Examples

TLDR: execute-plan resolves an explicit per-project suite policy instead of universally running the complete suite, and plan authoring states plan-specific and project-wide validation as distinct obligations, recovering efficiency and keeping the operator's policies consistent.

**Before (today):** `agents/skills/execute-plan/SKILL.md` Phase 2 step 2 and the stack-task entry, and `agents/skills/execute-plan/runtime-contract.md`, require "the complete repository-standard suite" at Phase 2 and at every stack-task boundary, resolved from "authoritative repository test guidance and inventory" with no explicit per-project policy. Executing an ordinary plan in this repository starts a whole-inventory suite run the operator must stop; the 2026-11-06 witness (recorded in the origin row's Reproduction evidence, commit `803cc1584`) records Phase 2 incomplete after 23 of the 84 then-inventoried suites.

**After (this plan):** execute-plan reads the target repository's `test_suite_policy` declaration: `full-before-final` runs the complete suite once before final completion (the Phase 2 boundary in ordinary mode, the run's final stack-task boundary in stack-task mode) and never at intermediate stack-task boundaries; `focused-never-full` never runs the whole suite and instead runs the plan's validation commands, the relevant focused regression suites, and the named repository gates. When the key is absent, the target repository's declared test-guidance documents (for this repository, its coding guidelines) resolve the policy, recognizing `full-before-final` and `focused-never-full` where declared; when guidance is missing or names conflicting policies, the executor records the policy unresolvable and surfaces the gap to the operator before Phase 2 completes instead of guessing. Plan authoring (`agents/skills/plans/SKILL.md` and its extracted module) states plan-specific validation and project-wide final validation as separate obligations and routes a plan-versus-policy conflict (for example a whole-suite instruction naming this repository) to the operator before certification.

**Edge cases:** a repository whose facts file lacks the key but whose guidance documents name the policy resolves through that guidance; a repository with neither, or with conflicting guidance, surfaces to the operator rather than defaulting. A plan whose text demands a whole-suite run in a `focused-never-full` repository is a conflict surfaced at execution time (before the command runs, at whichever boundary first reaches it) and again at certification, never silently run or silently dropped. A company project's final suite still runs even when every task's focused validation already passed: in stack-task mode the run's final stack-task boundary carries that obligation, verified from its returned evidence before the stack claim is released. Policy resolution happens once at Phase 0 run setup in both ordinary and stack-task mode; an unresolvable policy stands the run down before any task work, and a boundary that still cannot resolve the policy blocks claim release with the gap surfaced. The liveness incident's targeted coverage is preserved: the focused suites that pin preserved anchors keep running when their pinned surfaces are touched.

## Outcome

Each target repository spends plan-execution validation time where its own policy requires it, and no execution silently runs or silently skips a whole-repository suite.

- execute-plan resolves an explicit suite policy per target repository and applies `full-before-final` and `focused-never-full` differently, with an operator-surfaced gap when no policy is resolvable.
- Stack-task boundaries stop requiring the complete suite universally; the suite obligation moves to the policy's final boundary.
- Plan authoring keeps plan-specific validation commands and project-wide final validation as separately stated obligations and surfaces plan-versus-policy conflicts before certification.

Gate delta: net removal plus prose-only operator-surface stop conditions. Removed: the universal complete-suite requirement at every stack-task boundary and the unconditional Phase 2 suite mandate (both named removals). Added: a Phase 0 and stack-flow stop condition when the target policy is unresolvable (unrecognized value, missing, or conflicting guidance; existing stop semantics, claim release blocked), a final-boundary suite obligation at the run's final stack-task boundary under `full-before-final`, an execution-time conflict-surfacing duty when a plan command demands a whole-suite run under `focused-never-full`, and a certification-time conflict-surfacing duty in plan authoring; no new validator, registry, lock, script, or blocking review duty is added, and this landing discharges the inherited 2026-11-29 policy review obligation on the removed mandate, whose successor arms (the unresolvable-policy stop and the final-boundary duty) carry a deliberate successor review schedule, next review at 2026-11-29 or after the first company-keyed execution, whichever is later (a reschedule of the removed mandate's earliest-of obligation, so catches are measured after real company-policy usage while the deadline still bounds it, carried by a dated backlog row filed in the same change). Pricing witness: the completed integrity failure of the universal mandate, the operator-stopped Phase 2 run (23 of 84 suites run, Phase 2 incomplete) recorded in this plan's origin row `docs/history/backlog/2026-11-04-execute-plan-project-test-policy-scope.md` (Reproduction evidence) at commit `803cc1584`, plus the recorded unknown catch frequency and 2026-11-29 policy review date on the mandate-introducing plan `docs/history/plans/completed/2026-10-29-stacked-pr-plan-execution.md` (its Gate delta).

## Assumptions

- Assume the declaration surface is the target repository's `.ai-playbook/facts.md` TOML block; basis: it is the project configuration home execute-plan already resolves for `base_branch` and the directory keys, so no new surface is introduced. The simpler alternative, deriving the policy from the plan or from project class alone, was declined: the origin requires per-repository resolution without guessing organization or project identity, and the 2026-11-06 witness shows prose-only guidance resolving into an 84-suite run.
- Assume missing-policy behavior surfaces to the operator rather than defaulting; basis: the origin forbids silently promoting focused commands to a full suite and forbids silently skipping an explicit requirement.
- Assume the facts key is a configuration declaration read by prose, not a new validator or schema enforced by scripts; basis: machinery admission, no witnessed incident requiring a gate, and the dispatch entry's recorded rejected alternative against a mandatory suite-policy registry or blocking validator (docs/history/backlog/PLAN-PROMPTS.md, execute-plan-project-test-policy-scope entry).
- Assume the certification-time authoring duty covers plan-versus-policy conflicts only, with missing-policy surfacing owned by the execution-time Phase 0 stand-down; basis: the origin's fix-shape sentence names the conflict arm, and the origin's Expected-behavior sentence's missing-policy arm is satisfied transitively because the Phase 0 stand-down precedes certification and surfaces louder than a certification-time check.
- Assume this repository's own policy value is `focused-never-full` and company projects declare `full-before-final`; basis: the operator clarification of 2026-11-04 recorded in the origin. Company repositories gain the key through their own configuration maintenance; this plan only declares the key locally and documents its meaning.
- Assume the liveness cluster's focused coverage is preserved by keeping the named focused suites in the `focused-never-full` validation set; basis: the origin cluster row and the liveness origin `docs/history/backlog/2026-10-24-liveness-pin-plans-archive-twin-span-missing.md`.
- Assume the adjacent plan `docs/history/plans/2026-11-06-test-suite-runtime-reduction.md` owns runtime optimization and this plan owns selection policy only; basis: that plan's Review Scope explicitly defers suite-selection policy to "the adjacent policy backlog item", this origin.
- Assume `projects/.ai-playbook/coding_guidelines.md` is the shared guideline surface consuming repositories load, so the Task 4 policy statement names the ai-playbook skills repository explicitly instead of the reader-relative "this repository"; basis: the file is the deployed shared guidelines twin whose reader may be another repository.
- Scope ledger: authoring base `f89e958330337915228d26aca474ff432ba7e760`; the primary checkout is clean and no foreign dirt is expected in the authoring worktree. Frozen surfaces: `scripts/` validators and workflow scripts are untouched; no test file changes. The gitignored `.ai-playbook/facts.md` key addition is a local runtime configuration step that rides no commit.
Decision points requiring a grill: none remain. (Maintenance-selected authoring: the declaration-surface choice records its simpler-design comparison above; the missing-policy behavior and the per-boundary removal follow the origin's explicit scope arms and rejected alternatives.)
Scope extensions (grilled): none proposed.
Sources inspected: not a tracker-linked request.

## Evaluation Criteria

**Quality dimensions:**
- Consistency: the four execution surfaces (`execute-plan/SKILL.md`, `execute-plan/runtime-contract.md`, `execute-plan-stack/SKILL.md`, `plan-stack/SKILL.md`) state one policy-resolution rule with no residual universal whole-suite mandate.
- Correctness: both policy values are exercisable; `focused-never-full` names what runs instead of the suite, and `full-before-final` keeps the complete-suite requirement at the final boundary only.
- Authoring clarity: the plans authoring rules state the two validation obligations separately and name the conflict-surfacing duty with its boundary (before certification).
- Safety: no policy path silently skips an explicit requirement or silently runs a prohibited suite.

**Done when:**
- Every "repository-standard suite" reference in the four execution surfaces is either policy-qualified or removed; the two stack consumer surfaces, the glossary, and the worker evidence contract (`agents/skills/execute-plan/agent-logs.md`) contain no occurrence of the phrase; and the operative stack-task dispatch template (`agents/skills/execute-plan/subagent-prompts.md`) no longer orders a complete repository-standard command set at the boundary.
- The run's final stack-task boundary carries the policy's final-boundary obligation and an unresolvable policy blocks claim release, stated in both execute-plan surfaces and the stack consumer, each witnessed by its own dedicated positive stop pin in the Validation Commands; the release block verifies the final boundary's returned complete-suite evidence, not merely a statement of carriage.
- The two-obligations rule's text lives in `agents/skills/plans/validation-authoring-rules.md` (the rules' content home, which the `## Validation Commands (authoring rules)` pointer section in `agents/skills/plans/SKILL.md` loads on demand) and both surfaces carry the distinction.
- `projects/.ai-playbook/coding_guidelines.md` states this repository's `focused-never-full` policy and the primary checkout's gitignored `.ai-playbook/facts.md` carries the `test_suite_policy` key (a local runtime declaration; verified in both the primary checkout and the execution worktree's transferred copy, riding no commit).

**Ship when:**
- None: repository-internal skill and guidance text only; no deployment or external-owner condition applies.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope when valid.

**Production code:** none; the plan changes skill text and project guidance only.

**Documentation:**
- `agents/skills/execute-plan/SKILL.md` (Task 1)
- `agents/skills/execute-plan/runtime-contract.md` (Task 2)
- `agents/skills/execute-plan/subagent-prompts.md` (Task 2)
- `agents/skills/execute-plan/agent-logs.md` (Task 2)
- `agents/skills/execute-plan-stack/SKILL.md` (Task 2)
- `agents/skills/plan-stack/SKILL.md` (Task 2)
- `docs/maintenance/glossary.md` (Task 2)
- `README.md` (Task 2)
- `agents/skills/plans/SKILL.md` (Task 3)
- `agents/skills/plans/validation-authoring-rules.md` (Task 3)
- `projects/.ai-playbook/coding_guidelines.md` (Task 4)
- `docs/history/backlog/` successor-review row (Task 4)

**Plan-related extension:** review or execution may update adjacent prose in the touched files when a stale reference to the removed universal mandate sits beside an edited span. Findings that keep the four execution surfaces consistent or keep the extracted module byte-synced are in scope; unrelated skill-body rewrites are rejected with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md` runtime optimization, harness speedups, and language ports; owned by `docs/history/plans/2026-11-06-test-suite-runtime-reduction.md`.
- New validators, registries, locks, or scripts enforcing the policy; machinery admission names no witnessed incident for one.
- The bootstrap profile interview and company-project onboarding surfaces; repositories without the key resolve through guidance or surface to the operator, which needs no bootstrap change.

## Validation Commands

Run from the repository root with bash (the fenced language is normative; under zsh the unquoted list variable does not word-split and the existence pre-check fails closed with a confusing message). These commands prove the text contracts: each surface that must carry a phrase carries it through a dedicated pin for that obligation (per-file checks, never a multi-file union; multi-word spans chosen so deleting the guarded sentence breaks its pin), the two stack consumer surfaces, the glossary, and the worker evidence contract are fully free of the removed phrases, the dispatch template is free of the command-set order and the both-sets repair order, the runtime contract is free of the removed repair span and the legacy guidance-inventory mandate sentences, the two execute-plan surfaces are free of the removed mandate fragments (region-specific removed spans, distinct from the policy-qualified prose that may legitimately retain the suite phrase), the stack consumers are free of the removed checks/validation phrases and of the two-set wording, the catalog rows carry the suite-policy wording, the fail-loud stop wording and the stack final-boundary ordering exist where the tasks prescribe them, the two-obligations rule exists in both authoring surfaces, and the local declaration exists in both trees. Every positive and forbidden grep flattens newlines before matching (multi-word prose phrases can be line-wrapped; a line-based grep false-passes on a wrapped remnant), with the forbidden arms keeping the three-way rc split so a tool error fails closed. The em-dash scan uses the whole-file `file` mode over the edited surfaces, and the em-dash and hygiene gates share one path-list variable with an existence pre-check so a missing or renamed surface fails both gates; the maintenance pins suite runs so a rewrite that breaks a pinned span in the edited surfaces cannot land green. Authoring preflight executed 2026-11-07 with the flattened forms: the forbidden arms fired RED on their target files ("repository-standard suite" one occurrence in each of its four targets, "repository-standard command set" one, "complete standard set" one, "repository-standard checks" one, "repository-standard validation" one, "both validation sets" two in execute-plan/SKILL.md and two in execute-plan-stack/SKILL.md, one in subagent-prompts.md, zero in runtime-contract.md and agent-logs.md, "both sets to pass" one in runtime-contract.md, "rerun both sets" one in each of subagent-prompts.md and agent-logs.md, the four removed mandate fragments one each in their two execute-plan surfaces, plus the legacy Phase 2 repair tail "leave Phase 2 incomplete; after repair, rerun the complete suite" once in execute-plan/SKILL.md), every positive grep found no policy or stop wording yet, the expected RED-today state for both arms; the two facts-key greps own their RED state until Task 4, and at earlier boundaries they are recorded as deferred to Task 4; the rule-41 external pin-suite sweep over the touched literals recorded zero pin collisions; the whole-file em-dash scan returned rc 0 over the eleven surfaces, the public-hygiene `--files` scan returned pass, and `plan_readiness.py --pre-round` returned pass.

```bash
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
for spec in \
  "agents/skills/execute-plan/SKILL.md:test_suite_policy" \
  "agents/skills/execute-plan/runtime-contract.md:test_suite_policy" \
  "agents/skills/execute-plan/SKILL.md:full-before-final" \
  "agents/skills/execute-plan/runtime-contract.md:full-before-final" \
  "agents/skills/execute-plan/SKILL.md:focused-never-full" \
  "agents/skills/execute-plan/runtime-contract.md:focused-never-full" \
  "agents/skills/execute-plan/SKILL.md:unresolvable" \
  "agents/skills/execute-plan/runtime-contract.md:unresolvable" \
  "agents/skills/execute-plan/SKILL.md:resolved once at Phase 0" \
  "agents/skills/execute-plan/runtime-contract.md:resolved once at Phase 0" \
  "agents/skills/execute-plan/SKILL.md:final stack-task boundary" \
  "agents/skills/execute-plan/runtime-contract.md:final stack-task boundary" \
  "agents/skills/execute-plan/SKILL.md:to the operator before the command runs" \
  "agents/skills/execute-plan/SKILL.md:before the command runs at this boundary" \
  "agents/skills/execute-plan/SKILL.md:Phase 2 stays incomplete" \
  "agents/skills/execute-plan/SKILL.md:at whichever boundary first reaches it" \
  "agents/skills/execute-plan/SKILL.md:explicit key wins over guidance" \
  "agents/skills/execute-plan/SKILL.md:attributes it to the target repository" \
  "agents/skills/execute-plan/SKILL.md:quotes the attributing sentence" \
  "agents/skills/execute-plan/SKILL.md:blocks claim release" \
  "agents/skills/execute-plan/runtime-contract.md:blocks claim release" \
  "agents/skills/execute-plan/SKILL.md:Suite policy resolved at Phase 0 and stack-task boundaries" \
  "README.md:suite policy" \
  "agents/skills/execute-plan-stack/SKILL.md:returned evidence names the complete-suite commands" \
  "agents/skills/execute-plan/subagent-prompts.md:suite policy" \
  "agents/skills/execute-plan/subagent-prompts.md:complete-suite" \
  "agents/skills/execute-plan/agent-logs.md:suite policy" \
  "agents/skills/execute-plan/agent-logs.md:complete-suite" \
  "projects/.ai-playbook/coding_guidelines.md:focused-never-full" \
  "projects/.ai-playbook/coding_guidelines.md:full-before-final" \
  "projects/.ai-playbook/coding_guidelines.md:ai-playbook skills repository" \
  "projects/.ai-playbook/coding_guidelines.md:pins suite" \
  "projects/.ai-playbook/coding_guidelines.md:public-hygiene scan" \
  "agents/skills/execute-plan-stack/SKILL.md:suite policy" \
  "agents/skills/execute-plan-stack/SKILL.md:final stack-task boundary" \
  "agents/skills/execute-plan-stack/SKILL.md:before the draft PR" \
  "agents/skills/execute-plan-stack/SKILL.md:unresolvable" \
  "agents/skills/execute-plan-stack/SKILL.md:blocks the release" \
  "agents/skills/plan-stack/SKILL.md:suite policy" \
  "agents/skills/plans/SKILL.md:project-wide final validation" \
  "agents/skills/plans/validation-authoring-rules.md:project-wide final validation" \
  "agents/skills/plans/validation-authoring-rules.md:before certification"; do
  f="${spec%%:*}"; p="${spec#*:}"
  tr '\n' ' ' < "$f" | tr -s ' ' | grep -q "$p" || { echo "missing '$p' in $f" >&2; exit 1; }
done
for spec in \
  "agents/skills/execute-plan-stack/SKILL.md:repository-standard suite" \
  "agents/skills/plan-stack/SKILL.md:repository-standard suite" \
  "docs/maintenance/glossary.md:repository-standard suite" \
  "agents/skills/execute-plan/agent-logs.md:repository-standard suite" \
  "agents/skills/execute-plan/subagent-prompts.md:repository-standard command set" \
  "agents/skills/execute-plan/runtime-contract.md:complete standard set" \
  "agents/skills/execute-plan-stack/SKILL.md:repository-standard checks" \
  "agents/skills/plan-stack/SKILL.md:repository-standard validation" \
  "agents/skills/execute-plan/SKILL.md:both validation sets" \
  "agents/skills/execute-plan/runtime-contract.md:both validation sets" \
  "agents/skills/execute-plan/runtime-contract.md:both sets to pass" \
  "agents/skills/execute-plan/subagent-prompts.md:both validation sets" \
  "agents/skills/execute-plan/agent-logs.md:both validation sets" \
  "agents/skills/execute-plan-stack/SKILL.md:both validation sets" \
  "agents/skills/execute-plan/subagent-prompts.md:rerun both sets" \
  "agents/skills/execute-plan/agent-logs.md:rerun both sets" \
  "agents/skills/execute-plan/SKILL.md:from authoritative repository test guidance and inventory" \
  "agents/skills/execute-plan/SKILL.md:resolved from authoritative target-repository guidance and inventory" \
  "agents/skills/execute-plan/SKILL.md:leave Phase 2 incomplete; after repair, rerun the complete suite" \
  "agents/skills/execute-plan/runtime-contract.md:resolve the suite from authoritative repository test guidance and inventory" \
  "agents/skills/execute-plan/runtime-contract.md:repository-standard suite, and parent-owned light boundary" \
  "agents/skills/execute-plan/runtime-contract.md:complete repository-standard suite after all tasks pass" \
  "agents/skills/execute-plan/subagent-prompts.md:from authoritative guidance and inventory" \
  "agents/skills/execute-plan/agent-logs.md:the authoritative guidance and inventory" \
  "README.md:repository-suite evidence"; do
  f="${spec%%:*}"; p="${spec#*:}"
  tr '\n' ' ' < "$f" | tr -s ' ' | grep -qi "$p"; rc=$?
  if [ "$rc" -ne 1 ]; then echo "forbidden phrase '$p' present or tool error in $f (rc=$rc)" >&2; exit 1; fi
done
grep -q 'test_suite_policy = "focused-never-full"' .ai-playbook/facts.md || { echo "missing focused-never-full key in the run tree facts" >&2; exit 1; }
PRIMARY="$(cd "$(git rev-parse --path-format=absolute --git-common-dir)/.." && pwd)"
grep -q 'test_suite_policy = "focused-never-full"' "$PRIMARY/.ai-playbook/facts.md" || { echo "missing focused-never-full key in the primary checkout facts" >&2; exit 1; }
bash scripts/check_maintenance_pins.sh || exit 1
EM_DASH_FILES="agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md agents/skills/execute-plan/subagent-prompts.md agents/skills/execute-plan/agent-logs.md agents/skills/execute-plan-stack/SKILL.md agents/skills/plan-stack/SKILL.md agents/skills/plans/SKILL.md agents/skills/plans/validation-authoring-rules.md projects/.ai-playbook/coding_guidelines.md docs/maintenance/glossary.md README.md"
for f in $EM_DASH_FILES; do test -f "$f" || { echo "missing edited surface $f" >&2; exit 1; }; done
bash scripts/check-no-em-dash.sh file $EM_DASH_FILES || exit 1
PUBLIC_HYGIENE_REPO_ROOT="$REPO" bash scripts/scan-public-hygiene.sh --files $EM_DASH_FILES || exit 1
```

### Task 1: Resolve the suite policy in execute-plan Phase 2 and the stack-task entry

Context surface: the plan's Terms, this task, and the Assumptions scope ledger.

Files:
- `agents/skills/execute-plan/SKILL.md`

- [ ] Given Phase 2 step 2, expects resolution of the target's `test_suite_policy` from `.ai-playbook/facts.md` (explicit key wins over guidance), the guidance fallback when absent, and one treatment for unrecognized, missing, or conflicting guidance: unresolvable, Phase 2 stays incomplete under the existing stop semantics, the gap surfaced before Phase 2 completes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given policy-resolution timing, expects the target's `test_suite_policy` resolved once at Phase 0 run setup in both modes (explicit key wins over guidance), so an unresolvable policy stands the run down before any task work, and a boundary that still cannot resolve the policy blocks claim release. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the run's final stack-task boundary under `full-before-final`, expects that boundary to carry the policy's final-boundary obligation (the complete repository-standard suite once, recorded like the Phase 2 run) before the stack claim is released, never at intermediate boundaries; the final boundary is the one whose selected task is the stack plan's last task (no unchecked later task at invocation time). [class: IMPLEMENTATION_REQUIRED]
- [ ] Given `full-before-final`, expects Phase 2 to run the complete repository-standard suite once, recording every command and fresh result, with missing guidance, incomplete inventory, unavailable commands, or failures leaving Phase 2 incomplete until repair. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given `focused-never-full`, expects Phase 2 to run the plan's validation commands, the relevant focused regression suites, and the named repository gates, never the whole suite, and to surface a plan command invoking the whole test inventory (a whole-test-directory run or whole-suite command) to the operator before the command runs, at whichever boundary first reaches it. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the policy-resolution arm, expects guidance documents that name conflicting policies to route to the same operator surface as missing guidance: the policy is unresolvable and the gap is surfaced before Phase 2 completes. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the guidance fallback, expects a guidance policy to bind only when a declared test-guidance document attributes it to the target repository: value mentions in neutral or other-repository-attributed sentences never resolve, so a shared file carrying both tokens resolves as no declaration when neither mention attributes a value, unresolvable and surfaced. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a guidance-resolved policy, expects the Phase 0 resolution record to quote the attributing sentence and surface the resolved value before task work begins. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the stack-task entry paragraph, expects the complete-suite requirement removed from the boundary: the boundary runs the worker, required review, task-specific validation, and scope-intersecting plan commands, deferring the suite to the policy's final boundary; a whole-suite plan command here is a conflict surfaced to the operator before the command runs at this boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the stack-task entry's second paragraph, expects its "both validation sets" return wording rewritten to the policy-qualified sets the boundary returns. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the skill's `## Configuration (from facts document)` table, expects a `test_suite_policy` row registered with purpose cell "Suite policy resolved at Phase 0 and stack-task boundaries", the accepted values `full-before-final` and `focused-never-full`, and the guidance fallback with unresolvable surfacing to the operator. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the shared skill text's named-gates wording, expects the named repository gates resolved from the same authoritative test-guidance documents as the policy and no repository-specific gate name in the shared text; this repository's concrete gate names stay in the Task 4 guidance statement (naming review-enforced; a whole-file sweep is unsatisfiable against legacy telemetry prose). [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `execute-plan: resolve the target suite policy instead of a universal complete-suite mandate` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Sync the runtime contract and the stack consumer skills

Context surface: the plan's Terms, this task, and the Assumptions scope ledger. The runtime-contract twin is intentionally staged one task behind Task 1; recovery from an interruption after Task 1's commit must complete this task before any execution reads the pair.

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`
- `agents/skills/execute-plan-stack/SKILL.md`
- `agents/skills/plan-stack/SKILL.md`
- `docs/maintenance/glossary.md`
- `README.md`

- [ ] Given the runtime contract stack-task entry paragraph, expects it to mirror Task 1 with the literal tokens `test_suite_policy`, `full-before-final`, and `focused-never-full`: the one-boundary mode runs task-specific and scope-intersecting validation, applying the suite policy instead of a universal complete-suite requirement. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the ordinary lifecycle paragraph rewrite, expects the removal to cover the "after repair, rerun the complete standard set, and in stack-task mode rerun task-specific validation too" span, sentence terminator included. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the step 5 to 6 advancement, expects the final boundary's complete-suite evidence required before the draft PR under `full-before-final` (a policy-qualified step 5 requirement); step 8 stays as the backstop. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the runtime contract's stack-task paragraph, expects the one-boundary mode to carry the same final-boundary and unresolvable arms as Task 1 (policy resolved once at Phase 0; the final stack-task boundary runs the final-boundary suite under `full-before-final` before claim release; a boundary whose suite policy is unresolvable blocks claim release). [class: IMPLEMENTATION_REQUIRED]
- [ ] Given that same stack-task paragraph, expects the resolution home named by reference, not the value semantics restated. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the ordinary lifecycle paragraph, expects Phase 2 to read as plan validation commands plus the project-wide final validation the resolved policy requires, unresolvable-policy gap surfaced to the operator. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the `subagent-prompts.md` stack-task template, expects its "complete repository-standard command set" order replaced by the policy-qualified obligation (the literal phrases "suite policy" and "complete-suite"; "rerun both sets" must not survive) with the evidence part stating the final boundary's complete-suite recording under `full-before-final`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the `agent-logs.md` stack-task evidence contract, expects its "Repository-standard suite" command/result list order replaced by the policy-qualified evidence obligation (the literal phrases "suite policy" and "complete-suite") so the worker is never ordered to produce prohibited evidence; rerun-both-sets repair wording aligned. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given `execute-plan-stack/SKILL.md`, expects its delegation sentence to name the suite policy's obligation (the literal phrase "suite policy"), its adjacent "repository-standard checks" phrasing removed, and its step 7 and Integration Points "both validation sets" wording rewritten to the policy-qualified sets the boundary runs. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given that same file's step 8 claim release, expects it to verify, not state, that the run's final stack-task boundary carried the final-boundary obligation: under `full-before-final` the orchestrator checks the returned evidence names the complete-suite commands with fresh passing results. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given that same step 8 ordering, expects step 8 to say `blocks the release` when, under `full-before-final`, the final boundary's complete-suite evidence is absent, or when the suite policy is unresolvable, gap surfaced to the operator. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given `plan-stack/SKILL.md`, expects the per-task witness to read as task-specific checks plus the suite policy's per-task requirement (the literal phrase "suite policy"), with its adjacent "repository-standard validation" phrasing removed, not an unconditional suite pass. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the README's `execute-plan` and `execute-plan-stack` catalog rows, expects any per-task repository-suite verification wording qualified to the suite policy's per-task requirement (the literal "suite policy"). [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the glossary's "Independent task branch" definition, expects the suite phrase removed so the glossary matches the narrowed stack-task boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `stack surfaces: apply the resolved suite policy at task boundaries` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Separate the two validation obligations in plan authoring rules

Context surface: the plan's Terms, this task, and the Assumptions scope ledger.

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/plans/validation-authoring-rules.md`

- [ ] Given `agents/skills/plans/validation-authoring-rules.md` (the content home the `## Validation Commands (authoring rules)` pointer section in `agents/skills/plans/SKILL.md` loads on demand), expects a new numbered rule stating plan-specific validation commands and project-wide final validation as separate obligations, each with its own boundary, and that the two lists are never conflated. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a plan instruction that conflicts with the target suite policy (a whole-suite requirement for a `focused-never-full` repository, or the reverse), expects the new rule to route the exact conflict to the operator before certification, never silently run or dropped. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the pointer section's load-on-demand line in `agents/skills/plans/SKILL.md`, expects that line extended to name the plan-specific versus project-wide final validation distinction so the stub summarizes what the module owns; the module stays the rules' content home and the stub stays a pointer, never a second rule body. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `plans: state plan-specific and project-wide validation as separate authoring obligations` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Declare this repository's policy and record the liveness coverage disposition

Context surface: the plan's Terms, this task, and the Assumptions scope ledger. The executing run's own Phase 2 remains governed by the deployed pre-change skill text; the operator should expect the universal-mandate suite invocation at this plan's Phase 2 and stop it or sanction the focused substitution, recording the disposition in run evidence; an unattended run stands down at Phase 2 with the disposition note recorded, or records the sanctioned focused substitution before Phase 2 begins.

Files:
- `projects/.ai-playbook/coding_guidelines.md`
- `docs/history/backlog/` (the dated successor-review backlog row this task files)

- [ ] Given `projects/.ai-playbook/coding_guidelines.md`, expects a short policy statement carrying the literal `focused-never-full`: the ai-playbook skills repository's execution validation never runs its whole suite and instead runs plan-specific commands, the relevant focused regression suites (the liveness pin suite included when its pinned surfaces are touched), and the named repository gates (this repository's pins suite and public-hygiene scan). [class: IMPLEMENTATION_REQUIRED]
- [ ] Given that same statement, expects a neutral two-value recognition sentence carrying `full-before-final`: a repository declaring `full-before-final` runs the complete suite at its final boundary; one declaring `focused-never-full` never runs it. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given that same statement, expects the recognition sentence to precede the ai-playbook-specific mandate (ordering review-enforced), so a declarer's own attributed statement resolves to either value and the shared file's two-value structure never reads as a consuming-repository prohibition. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given that same statement, expects it to land as the next free numbered clause in the file (44 at the authoring base `f89e9583`; re-derive the number from the target file's committed clause list at execution) whose heading names the ai-playbook skills repository, so the per-repository scope is self-evident and instruction files can reference the clause number, never the reader-relative "this repository". [class: IMPLEMENTATION_REQUIRED]
- [ ] Given the gitignored `.ai-playbook/facts.md`, expects the executor to add `test_suite_policy = "focused-never-full"` inside the opening TOML block (the fenced toml block the other facts keys occupy) of the PRIMARY checkout's copy (the durable declaration home future worktree transfer-in copies from) and of the execution worktree's transferred copy, both as local runtime configuration steps recorded in the run evidence, riding no commit. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: given Task 3's stub edit on `agents/skills/plans/SKILL.md`, expects the liveness pin suite (`PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_authoring_plans_liveness.py -q`) to pass, confirming the targeted coverage that motivated the full-suite requirement survives as the named focused suites inside the `focused-never-full` set. [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the focused suites pinning the Task 1 and Task 2 surfaces (`PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_quota_wall_doctrine.py scripts/test_execute_plan_referral_contract.py scripts/test_worktree_closeout_migrate.py scripts/test_harness_policy_contract.py -q`) pass, so no pinned span in the rewritten execute-plan surfaces broke. [class: REPOSITORY_TEST]
- [ ] Given the successor review schedule, expects the same commit to file a dated backlog row under `docs/history/backlog/` carrying the successor arms' review obligation (next review 2026-11-29 or after the first company-keyed execution, whichever is later), naming this plan as witness; the filed row rides the em-dash and hygiene scans at this task's boundary. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `guidelines: declare the focused-never-full suite policy for this repository` [class: IMPLEMENTATION_REQUIRED]

## Residual findings (cap closure)

Operator authorization recorded 2026-11-07 (interactive session sess_e0d1f436-011c-430a-9f85-4db92acea660) at the r9 reflection checkpoint: the loop's non-convergence triggers are mechanically active and the terminal shape closes the series. Every staged finding of the cap round r9 was resolved in-round by accepted edits in commit `4a185fd41d9b85f3976ce6ba1b3310b1f18216bd`; the dispositions below carry each pattern id beside its disposition.

- security#release-block-unconditional-reading: disposition folded
- consistency#validation-pin-aliasing: disposition folded
- consistency#removal-probe-inventory-gap: disposition folded
- testing#ungated-removal-span: disposition folded
- security#final-boundary-evidence-order-unpinned: disposition folded
- security#guidance-fallback-misattribution-prose-only: disposition folded
- security#readme-qualification-presence-only: disposition folded
- testing#unpinned-policy-arms: disposition folded
- testing#precheck-after-loops: disposition folded
- implementation#acceptance-arm-ambiguity: disposition folded
- implementation#pin-distinctiveness: disposition folded
- documentation#ambiguous-term-definition: disposition folded
- consistency#cross-task-semantics-tension: disposition folded
