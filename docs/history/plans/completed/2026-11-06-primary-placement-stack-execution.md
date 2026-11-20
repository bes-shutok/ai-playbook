# Plan: honor primary placement in execute-plan-stack

Backlog origin: docs/history/backlog/2026-11-04-execute-plan-stack-primary-placement.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-primary-placement-stack-execution-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 2h total, largest task 1h
Executed: yes (862f3e1ce)

Authoring claim: 2026-11-04-execute-plan-stack-primary-placement.md (session sess_94c2ac9f-d3cc-4209-a889-ff30aad2d42d)

## Terms

- primary placement: the execute-plan placement resolution under which a project's facts declare `worktree_policy = "primary"` and the run works in the primary checkout with no run worktree; a company-profile run records the operator's chosen or created task branch and its start commit, and the manifest identity's `run_worktree` carries the no-worktree primary form.
- worktrees resolution: the placement resolution under which ad-hoc worktrees are enabled and the run works in its registered worktree on its own branch.
- company task branch: the branch a company-profile primary-placement run keeps current or creates from the current HEAD, recorded in the execution claim and the manifest identity block beside its start commit.
- stack-task entry: the explicit `execute-plan --stack-task <plan-path> --task <N>` one-boundary mode an existing stack run enters with its transition receipt.
- stack branch transition row: the recorded row naming the old branch, new branch, predecessor, and task that authorizes the stack-task entry's adoption of an intentionally switched branch.
- continuity probe: `scripts/check_run_continuity.py check`, run at task boundaries over the run's recorded identity; on a primary-placement run it takes `--skip-worktree-checks`.
- retained-placement exception: the adoption rule that lets a resume or stack-task entry keep an established run's placement instead of re-consulting; it prevents duplicate ownership and never authorizes refusing an operator's current placement direction.
- fresh-config consult: re-reading the project facts immediately before provisioning when a placement question is outstanding, so a bootstrap answer never rides a stale earlier snapshot.
- primary resolution: the Project worktree policy paragraph's own name for the primary placement; this plan uses the two forms interchangeably, matching the paragraph's wording.

## Why

`execute-plan-stack` step 2 requires an established registered worktree and step 4 binds branch transitions to the retained run worktree, while the shared execute-plan contract resolves placement from repository facts and explicitly supports company-profile primary placement. A repository with `worktree_policy = "primary"` therefore has a valid execute-plan placement that the stack skill's wording appears to forbid: the witnessed operator had to correct a proposed worktree after the target facts specified primary placement. A second witness added an instruction-precedence failure: a stale facts snapshot rode through an outstanding bootstrap question, and the retained-placement exception was then treated as authority to disregard the operator's explicit placement direction.

## Gist & Examples

TLDR: the stack workflow resolves placement through execute-plan's Worktree-first policy and runs every step in the resolved placement, so a primary-placement repository executes stacks without a prohibited worktree (driving force: code-quality).

**Before (today):** a company repository declares `worktree_policy = "primary"`. A stacked execution reads execute-plan's Phase 0, sees the valid primary placement, then reads `execute-plan-stack` step 2 ("adopt the established worktree") and proposes a worktree; the operator must correct the placement mid-run. In the second witness, the run also kept a pre-update facts snapshot across a pending bootstrap question and later cited the retained-placement exception against the operator's explicit direction, incurring a worker stop, source and artifact transfer, claim rebinding, and fixture relocation.

**After (this plan):** the stack skill adopts the resolved placement by reference: under the worktrees resolution it keeps today's registered-worktree flow unchanged; under the primary resolution it uses the recorded primary checkout and company task branch, performs the retained-run branch transition there, passes the continuity probe with `--skip-worktree-checks`, and carries the no-worktree primary form in the manifest identity. The stack-task entry's adoption wording accepts the recorded primary placement beside the worktree form, with the transition receipt requirement unchanged. The policy paragraph states the fresh-config consult and explicit-direction precedence in plain wording. Claim serialization, the transition receipt, predecessor order, task boundaries, and draft PR checks are preserved as they are.

**Edge cases:** an initially configured primary project takes the primary lane from the first stack step. A configuration change landing while a bootstrap placement answer is outstanding takes the fresh-config re-read, never the stale snapshot. An operator direction to relocate a provisioned run outranks the retained-placement exception, proceeding under the existing serialization refusal and resume stand-down safeguards. A worktrees-resolution repository keeps the registered-worktree flow byte-for-byte.

## Outcome

A stack run's placement follows the target repository's declared policy end to end, so company projects configured for primary-checkout execution run stacks without a disallowed worktree and without an operator correction.

- A primary-placement repository executes the stack workflow entirely in its recorded primary checkout and company task branch.
- The second witnessed failure class closes: a pending bootstrap placement answer triggers a fresh-config re-read before provisioning, and an explicit operator placement direction outranks the retained-placement exception.
- The stack-task entry adopts the recorded primary placement with the same receipt, claim, manifest, and probe evidence the worktree lane already uses.
- No second placement protocol, gate, or validator is introduced; execute-plan's existing contract stays the single placement source.

Gate delta: none (no gate, validator, lock, ledger, or fence added or removed; the tasks reword existing skill text to reference execute-plan's existing placement resolution and add span-pin regression coverage, so no refusal surface or checked set grows; the origin row records the misdirected-placement witness and the rejected alternative of a second protocol).

## Assumptions

- assume the stack skill adopts execute-plan's Worktree-first policy by reference and defines no placement logic of its own; basis: the origin row's Expected paragraph and its "do not add another placement gate or duplicate policy" instruction.
- assume the transition mechanics (the stack branch transition row, the claim refresh, the manifest `run_branch` update, the continuity probe) stay unchanged; basis: the PLAN-PROMPTS entry `primary-placement-stack-execution`'s Continuity disposition line, which retains the same transition and continuity evidence (the backlog row states the same substance in its Expected paragraphs).
- assume the policy-paragraph amendment is wording-only (fresh-config consult and explicit-direction precedence), never a new gate; basis: the origin row's Investigation extension ("without adding another gate or placement protocol").
- assume primary-placement serialization stays the execution-claim and serialization arm's existing shape; basis: the PLAN-PROMPTS entry `primary-placement-stack-execution`'s Continuity disposition line (retain the primary-checkout serialization claim and identity checks).
- assume no examples, runtime tests, or bootstrap guidance encode a worktree-only stack assumption requiring correction; basis: the authoring investigation checked `agents/skills/bootstrap-ai-playbook/SKILL.md` on disk and found `worktree_policy` documented as a two-value interview output with an illustrative (not default) example, and no other guidance or example surface carries a worktree-only stack assumption; the origin row's examples-and-guidance audit disposition is recorded here with no task needed.
Decision points requiring a grill: none remain.

## Standing constraints

- Python test conventions per `projects/.ai-playbook/python_guidelines.md`; the new suite follows `scripts/test_maintenance_runtime_scope.py`'s stated convention (a Markdown policy pinned by normative tokens inside the owning span), and every pin literal is copied from Task 2 to Task 4's prescribed insertion wording so the RED suite matches the GREEN text exactly.
- Anti-growth: operative skill text carries the rule, not the story; the witness narrative stays in the origin row; the byte-budget gate (run by `scripts/check_maintenance_pins.sh` where the amended file is pinned) is recorded per grown file and any breach report takes the pay-for-growth response or the recorded advisory.
- Pinned files: the amended skills are covered by the repository pins and hygiene suites; additions sit beside pinned spans and never mutate them.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a primary-placement repository can follow stack steps 2 and 4 verbatim with no worktree step (span pins prove the resolution-neutral wording exists in both steps and in the stack-task adoption wording)
- consistency: the stack skill names execute-plan's policy as the single placement source and adds no second protocol (span pins prove the by-reference citation)
- safety: the fresh-config consult and explicit-direction precedence clauses exist in the policy paragraph while the serialization refusal and resume stand-down safeguards stay pinned byte-identical

**Done when:**
- `python3 -m pytest scripts/test_stack_primary_placement.py -q` passes (span pins of the resolution-neutral wording, the primary-adoption wording, and the two policy clauses)
- `bash scripts/check_maintenance_pins.sh` exits 0 (the byte-budget gate's output recorded in the run log)
- `bash scripts/scan-public-hygiene.sh` exits 0 (tracked hits outside agents/skills and projects report only)
- `bash scripts/check-no-em-dash.sh added-lines --base <branch point this run started from>` exits 0

**Ship when:**
- a company repository configured `worktree_policy = "primary"` completes a stacked execution with no proposed worktree and no operator placement correction (operations evidence; no checklist item)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan-stack/SKILL.md` (Task 2)
- `agents/skills/execute-plan/runtime-contract.md` (Task 3)
- `agents/skills/execute-plan/SKILL.md` (Task 3) *(partially in scope: the Stack-task entry point section only; all other sections are frozen; reject any review finding that touches them)*
- `agents/skills/execute-plan/worktree-first.md` (Task 4)

**Tests:**
- `scripts/test_stack_primary_placement.py` (Task 1) *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md` sections outside the Stack-task entry point; reason: the shared contract already supports primary placement and this plan changes no shared-contract behavior
- `scripts/execution_claim.sh` and `scripts/check_run_continuity.py`; reason: both already expose the primary-placement shapes (`--start-commit` claim flag, `--skip-worktree-checks`) this plan references; changes there are only plan-related if a Task 2 to 4 wording error contradicts their real interfaces
- `agents/skills/github-pr-workflow/` and `agents/skills/update-stacked-branches/`; reason: adjacent stack lifecycle skills this plan does not touch

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_stack_primary_placement.py -q
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base <branch point this run started from>
```

### Task 1: Regression coverage pinning primary placement in the stack workflow

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_stack_primary_placement.py` *(new)*

Primary class anchors:
- `Workflow` in `agents/skills/execute-plan-stack/SKILL.md`

- [x] New unittest suite following `scripts/test_maintenance_runtime_scope.py`'s stated convention (a Markdown policy pinned by normative tokens inside the owning span) [class: REPOSITORY_TEST]
- [x] The same suite extracts `execute-plan-stack` step 2 and pins the by-reference policy citation copied verbatim from Task 2's insertion: the citation naming the execute-plan Worktree-first policy [class: REPOSITORY_TEST]
- [x] The same suite pins, inside the step 2 span, the primary-resolution adoption tokens copied verbatim from Task 2: the resolved-placement adoption span and the span naming the recorded primary checkout and company task branch [class: REPOSITORY_TEST]
- [x] The same suite extracts step 4 and pins the transition-in-resolved-placement tokens copied from Task 2: the continuity probe span carrying `--skip-worktree-checks` on a primary-placement run, the manifest span carrying the no-worktree primary form in `run_worktree`, and the preservation span stating the transition row, claim refresh, predecessor order, and probe evidence unchanged [class: REPOSITORY_TEST]
- [x] The same suite extracts the Stack-task entry point section from `agents/skills/execute-plan/runtime-contract.md` and the `Stack-task entry point` section from `agents/skills/execute-plan/SKILL.md`, and pins Task 3's primary-adoption tokens: the adoption span accepting the recorded primary placement beside the worktree form and the unchanged-receipt span keeping the transition receipt, claim agreement, and probe requirements [class: REPOSITORY_TEST]
- [x] The same suite extracts the Project worktree policy paragraph from `agents/skills/execute-plan/worktree-first.md` as the owning span every Task 4 pin reads inside [class: REPOSITORY_TEST]
- [x] The same suite pins the fresh-config consult span copied verbatim from Task 4's insertion: re-reading the project facts immediately before provisioning when a placement question is outstanding, covering an initially configured primary project and a configuration change landing while the answer is pending [class: REPOSITORY_TEST]
- [x] The same suite pins the explicit-direction precedence span copied verbatim from Task 4's insertion: the operator's current placement direction outranking the paragraph's resumed-run adoption rule, retained-run identity preventing duplicate ownership and never authorizing a refused relocation [class: REPOSITORY_TEST]
- [x] The same suite pins, byte-identical to today's text and anchored only on spans no task rewrites, the step 4 branch-selection sentence (serial task branches from the immediate predecessor, first task on the configured base) and the transition-row span naming the old branch, new branch, predecessor, and task [class: REPOSITORY_TEST]
- [x] The same suite pins the policy paragraph's serialization-refusal span byte-identical ("a fresh run in the primary checkout refuses to start while another live execution claim or recorded witness occupies the primary checkout"), so the suite fails if a later edit weakens it [class: REPOSITORY_TEST]
- [x] Run → expect RED: the suite fails at the current tree because every Task 2 to Task 4 token is absent from the current skill text; the safety-preservation pins are expected to pass at RED [class: REPOSITORY_TEST]
- [x] Commit: `test: pin stack primary-placement wording` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Placement resolution in the stack workflow steps

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan-stack/SKILL.md`

Primary class anchors:
- `Workflow` in `agents/skills/execute-plan-stack/SKILL.md`

- [x] Step 2: reword the adoption sentence to resolve the placement through execute-plan's Worktree-first policy by reference (the policy paragraph in `agents/skills/execute-plan/worktree-first.md`), adopting the established registered worktree, run context, and claim under the worktrees resolution and the recorded primary checkout, company task branch, and run context under the primary resolution [class: IMPLEMENTATION_REQUIRED]
- [x] Step 2: the stability requirements stay as written with the placement identity (the registered worktree, or the recorded primary checkout and company task branch) replacing the worktree-only token in the stability list (`run_session_id`, plan path, placement identity) [class: IMPLEMENTATION_REQUIRED]
- [x] Step 4: reword the transition to run in the resolved placement: the continuity probe verifies the current placement and recorded branch, taking `--skip-worktree-checks` on a primary-placement run; the claim refresh and manifest identity update stay as written, with the manifest's `run_worktree` carrying the no-worktree primary form under the primary resolution; the transition row, predecessor order, and pre-worker probe stay as written [class: IMPLEMENTATION_REQUIRED]
- [x] Both steps keep the worktrees-resolution flow byte-identical for repositories that select worktrees, so the witnessed worktree lane changes nothing [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 1 step 2 and step 4 pins pass against the amended text [class: REPOSITORY_TEST]
- [x] Run the maintenance pins suite (the byte-budget gate over the amended file rides it where pinned) and the hygiene scan, expect exit 0 on both, and record the byte-budget gate's output in the run log [class: REPOSITORY_TEST]
- [x] Commit: `docs: resolve stack workflow placement through the execute-plan policy` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Primary adoption in the stack-task entry wording

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md`

Primary class anchors:
- `Stack-task entry point` in `agents/skills/execute-plan/runtime-contract.md`
- `Stack-task entry point` in `agents/skills/execute-plan/SKILL.md`

- [x] In the runtime-contract Stack-task entry point section, reword the caller-adoption sentence to accept the recorded primary placement (the primary checkout, company task branch, and no-worktree `run_worktree` form) beside the registered worktree form, so the entry's "ordinary Phase 0 placement" language and the adoption arm cover both resolutions [class: IMPLEMENTATION_REQUIRED]
- [x] In the execute-plan SKILL.md Stack-task entry point section, apply the same placement-neutral adoption wording to the "adopt its registered worktree" sentence, keeping the transition receipt requirement, claim and manifest agreement, continuity probe, Inclusion Hard Gate, and validation duties byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 1 Stack-task entry pins pass against both amended sections [class: REPOSITORY_TEST]
- [x] Run the maintenance pins suite and the hygiene scan, expect exit 0 on both [class: REPOSITORY_TEST]
- [x] Commit: `docs: accept recorded primary placement in stack-task adoption` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Fresh-config consult and explicit-direction precedence in the policy paragraph

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/execute-plan/worktree-first.md`

Primary class anchors:
- `Project worktree policy` in `agents/skills/execute-plan/worktree-first.md`

- [x] In the Project worktree policy paragraph, add the fresh-config consult as plain wording: when a placement question is outstanding (a bootstrap answer pending), re-read the project facts immediately before provisioning, covering both an initially configured primary project and a configuration change landing while the answer is pending; the consult restates the existing policy-consult duty at its decision point and adds no gate [class: IMPLEMENTATION_REQUIRED]
- [x] In the same paragraph, add the explicit-direction precedence clause with its antecedent named inline: an operator's current placement direction outranks the paragraph's resumed-run adoption rule (the exception that keeps an established run's placement across a resume or stack-task adoption); retained-run identity prevents duplicate ownership and never authorizes refusing an operator-directed relocation [class: IMPLEMENTATION_REQUIRED]
- [x] The same clause names the honoring state path: the execution claim's branch and the manifest identity fields (`run_branch`, `run_worktree`) refresh to the operator-directed placement and the continuity probe re-runs in the new placement's mode before work continues, with the existing serialization refusal and resume stand-down safeguards unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 1 policy-paragraph pins pass against the amended paragraph [class: REPOSITORY_TEST]
- [x] Run the maintenance pins suite and the hygiene scan, expect exit 0 on both [class: REPOSITORY_TEST]
- [x] Commit: `docs: state fresh-config consult and placement-direction precedence in the worktree policy` [class: IMPLEMENTATION_REQUIRED]
