# Plan: Plans system-under-test naming rule for wrapper-converted results

Backlog origin: docs/history/backlog/2026-09-28-plans-sut-naming-rule-for-wrapper-converted-results.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-plans-sut-naming-authoring-rule-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The plans skill's Validation authoring rules gain an explicit system-under-test naming rule (rule 43) and the review-agents testing lens gains the matching pattern, so a plan whose behavior is observable at two layers pins each expectation to the layer that can produce it.

- A test expectation written against a pure reducer while the codebase's wrapper structurally downgrades that outcome is caught at plan review by a named authoring rule and a named lens pattern, instead of costing three re-derivation rounds (the origin's witnessed r2-r4 churn: five staged findings across four workers, all one missing rule).
- Wrapper-level expectations state the wrapper's actual post-conversion outcome with their own assertion; reducer-level expectations that today's wrapper already satisfies are labeled green-at-RED regression pins, never RED targets.

Gate delta: one authoring rule and one lens pattern are added - prose rules, no gate, refusal class, fence, or schema field. The addition is priced by the origin's own witness: a learned-skill-defect capture whose recorded cost is the witnessed review churn (five findings across three rounds of the execute-plan-codex-worker-terminal-recovery plan), the completed-integrity-failure form the rule-pricing bar accepts; there is no false positive to remove and no smaller exit (the rules currently cover task coupling and gate states but not layer-pinned expectations, per the origin's root-area paragraph).

## Terms

- **System under test (SUT)**: the layer a test item's expectation is written against, named in the item.
- **Wrapper-converted result**: an outcome a wrapper post-processes or can veto relative to the lower layer's (reducer's) result, so the two layers can disagree at the same seam.
- **Green-at-RED regression pin**: an expectation that today's code already satisfies at the lower layer, labeled as a regression pin rather than a RED target.

## Assumptions

- assume the rule lands as rule 43 in `agents/skills/plans/SKILL.md`'s Validation Commands (authoring rules) list (the list's last rule is 42, verified on this tree), with the wording taken from the origin's Suggested fix; basis: the origin's Which-skill-and-step and Suggested-fix paragraphs.
- assume the lens pattern lands in `agents/skills/review-agents/testing.md` as the next numbered pattern with the id `testing#sut-naming-wrapper-converted-results`, following that catalog's existing numbered-pattern shape; basis: the origin's note that review-plan's panel catalogs have no matching pattern, and the catalog's on-disk convention (numbered entries with `testing#...` pattern ids).
- assume the origin's classification: the header declares `Origin class: learned-skill-defect` with no bare `Class:` token; the body is judged fix-class at authoring (a missing enforcement artifact whose cost is witnessed review churn), and that judgment is recorded here per the filing-class rule; basis: the origin header and body.
- assume touching `agents/skills/review-agents/` requires the repository's two portability gates (scripts/check_review_agent_portability.py and scripts/test_review_agent_doors.py, exit 0) in this plan's Validation Commands; basis: the repository guidelines' review-agents mandate.
- assume the plans skill body is covered by the shared-body runtime-neutrality gate (test_shared_skill_bodies_remain_runtime_neutral sweeps agents/skills/plans/SKILL.md), so the Validation Commands run that gate over the amended file; basis: the gate's own shared_files tuple and the plans authoring rule requiring a plan to run the shared-body gate it could break.
- assume rule 43's prose avoids every forbidden term of that neutrality gate (the rule speaks of reducers and wrappers; no runtime names, hook names, or format tokens), so the insertion passes the gate without a sanctioned-term amendment.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: plans Validation authoring rules gain rule 43, and the testing lens gains the matching pattern, so layer-ambiguous test expectations are named and pinned at authoring time; the driving force is code-quality (an expectation must be falsifiable at the layer it names).

Before (today): a plan writes "reconcile returns `available` with the worker active" without naming the layer. The pure reducer returns `available`; the driver wrapper structurally cannot (it downgrades any available result behind an active worker). Three review rounds re-derive the same defect in different words - unreachable fixture, dead guard code, unfalsifiable canary - before someone names the seam. This is the origin's witnessed r2-r4 churn.

After (this plan): rule 43 requires each test item to name its SUT whenever a wrapper transforms or can veto the lower layer's result; the wrapper's actual post-conversion outcome carries its own assertion; and the reducer-level expectation that today's wrapper already satisfies is labeled a green-at-RED regression pin. The testing lens pattern gives review panels the named check.

## Evaluation Criteria

**Quality dimensions:**
- correctness: rule 43 carries all three obligations from the origin's fix shape (SUT naming, the wrapper's own post-conversion assertion, the green-at-RED labeling) and sits at number 43 contiguous with rule 42.
- regression safety: the shared-body neutrality gate and the two review-agents portability gates stay exit 0; the testing catalog's numbering stays contiguous.
- maintainability: the lens pattern's id and shape follow the catalog's existing conventions so panels can load and cite it.

**Done when:**
- Rule 43 exists in the plans skill with the origin's three obligations; the testing.md pattern exists with the catalog's numbering shape; all Validation Commands exit 0.

**Ship when:**
- Consumer runtimes pick both skills up through their normal vendored-asset sync; no further release action belongs to this plan.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-agents/testing.md`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- The test-item format template in the plans Plan Format section; reason: the rule binds through the authoring rules list; the format template's given/expects shape already accommodates naming the SUT in the given clause.

## Validation Commands

```bash
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest --version || { echo "no pytest-capable interpreter" >&2; exit 1; }

# 1. Rule 43 exists with its three obligations pinned (dedicated pins).
grep -qF '43. **System-under-test naming for wrapper-converted results:**' agents/skills/plans/SKILL.md || { echo "FAIL: rule 43 missing" >&2; exit 1; }
grep -qF 'names its system under test' agents/skills/plans/SKILL.md || { echo "FAIL: SUT-naming obligation missing" >&2; exit 1; }
grep -qF 'green-at-RED regression pin' agents/skills/plans/SKILL.md || { echo "FAIL: green-at-RED labeling missing" >&2; exit 1; }
[ "$(grep -n '^42\. \*\*' agents/skills/plans/SKILL.md | head -1 | cut -d: -f1)" -lt "$(grep -n '^43\. \*\*' agents/skills/plans/SKILL.md | head -1 | cut -d: -f1)" ] || { echo "FAIL: rule 43 not contiguous after rule 42" >&2; exit 1; }

# 2. The testing-catalog pattern exists with the catalog's id convention.
grep -qF 'testing#sut-naming-wrapper-converted-results' agents/skills/review-agents/testing.md || { echo "FAIL: lens pattern missing" >&2; exit 1; }

# 3. The shared-body runtime-neutrality gate passes over the amended plans skill.
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k shared_skill_bodies -q || { echo "FAIL: shared-body neutrality" >&2; exit 1; }

# 4. The review-agents portability and door gates pass (repository mandate for review-agents edits).
python3 scripts/check_review_agent_portability.py || { echo "FAIL: portability" >&2; exit 1; }
python3 scripts/test_review_agent_doors.py || { echo "FAIL: doors" >&2; exit 1; }

# 5. Em-dash gate over the branch's added lines.
bash scripts/check-no-em-dash.sh added-lines --base main || { echo "FAIL: em-dash gate" >&2; exit 1; }
```

Authoring-time gate record (rule 29/19/22): the rules list's last number (42) and the testing catalog's pattern-id convention were verified on this tree at authoring time. RED-today evidence, rule 19: Commands 1 and 2's spans are absent from both files today (verified), so the pins fail until Tasks 1-2 land; Commands 3-5 are characterization gates (they must stay green across the edits - verified green on the unamended tree before authoring). Rule 22 mechanical audit: each Validation Command pin occurs once in its owning Task's prescription beside its Command occurrence (plan-wide mentions in Gist, Terms, and Assumptions are not pin sites); `bash -n` over this block passed.

### Task 1: Add rule 43 to the plans Validation authoring rules (GREEN)

Files:
- `agents/skills/plans/SKILL.md`

Evidence:
- `grep -qF '43. **System-under-test naming for wrapper-converted results:**' agents/skills/plans/SKILL.md && grep -qF 'names its system under test' agents/skills/plans/SKILL.md && grep -qF 'green-at-RED regression pin' agents/skills/plans/SKILL.md`; covers: the rule exists with all three obligations.

- [ ] Append rule 43 to the Validation Commands (authoring rules) list immediately after rule 42, worded from the origin's Suggested fix: when a wrapper transforms or can veto a lower layer's result (a pure reducer versus a wrapper that post-processes or downgrades it), every test item names its system under test; the wrapper's post-conversion outcome gets its own named assertion; and any reducer-level expectation that today's wrapper already satisfies is labeled a green-at-RED regression pin rather than a RED target. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: Validation Command 1's three pins pass, and Command 3's shared-body gate stays exit 0. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: plans rule 43 names the system under test for wrapper-converted results` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Add the testing-lens pattern (GREEN)

Files:
- `agents/skills/review-agents/testing.md`

Evidence:
- `grep -qF 'testing#sut-naming-wrapper-converted-results' agents/skills/review-agents/testing.md && python3 scripts/check_review_agent_portability.py && python3 scripts/test_review_agent_doors.py`; covers: the pattern exists and the review-agents gates stay exit 0.

- [ ] Append the next numbered pattern to the testing lens catalog with the id `testing#sut-naming-wrapper-converted-results`, following the catalog's existing entry shape (default severity per its calibration references, and the finding form: an expectation whose named-or-implicit layer cannot produce the expected outcome at a wrapper-converted seam), citing plans rule 43 as the authoring-side rule. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: Validation Command 2's pin passes; Command 4's portability and door gates stay exit 0. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: testing lens pattern for wrapper-converted SUT naming` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Whole-plan validation gate

Files:
- `agents/skills/plans/SKILL.md`

Evidence:
- `awk '/^```bash$/{f=1;next}/^```$/{f=0}f' docs/history/plans/2026-09-30-plans-sut-naming-authoring-rule.md > "$TMPDIR/whole-plan-validation.sh" && bash "$TMPDIR/whole-plan-validation.sh"` (the block's own commands extracted and executed; the awk expression is described here because the literal sequence cannot appear inside this fenced block); covers: every criterion in Done when.

- [ ] Run the extracted Validation Commands block from the worktree root; every command exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `test: whole-plan validation for the SUT naming rule` [class: REPOSITORY_TEST]
