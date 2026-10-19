# Plan: extract the heaviest stable protocol block from each skill monolith

Backlog origin: docs/history/backlog/2026-10-04-skill-monolith-module-extraction.md
Driving force: efficiency + token-usage
Plan review record: the staging series {reviews_dir}/*-plan-review-skill-monolith-module-extraction-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 3h total, largest task 1.5h
Execution dependency: satisfied (the gating byte-binding relaxation plan landed; docs/history/plans/completed/2026-10-04-review-cert-graded-binding.md)

Authoring claim: docs/tmp/authoring-claims/2026-10-04-skill-monolith-module-extraction.md (session sess_9f5841ba; session-scoped and untracked; the durable record is the review-record series above)

## Terms

- monolith: the two oversized skill bodies, agents/skills/plans/SKILL.md and agents/skills/execute-plan/SKILL.md, whose inline stable protocol blocks every loading session pays for.
- module: a referenced Markdown file beside a skill's SKILL.md carrying one extracted stable protocol block as provenance header plus body (the body excludes the section heading, which stays in the spine).
- tranche: this plan's two extractions, one per monolith; later blocks ride the same precedent in later plans.
- validation authoring rules: the numbered Validation Commands authoring-rules block in agents/skills/plans/SKILL.md (the rules governing how a plan's Validation Commands section is authored; the block the readiness pre-round chain and review panels read).
- Worktree-first standard: the execute-plan section owning ad-hoc worktree setup, adoption, fail-closed stand-downs, and closeout migration, referenced by name from the maintenance blueprints' payloads and multiple skills.
- spine: the SKILL.md after extraction: the phase content with the extracted block replaced by its heading plus a load-on-demand reference to the module.
- reference hub: the spine's retained section heading and one-line pointer; it keeps every cross-file prose reference naming the SKILL.md section true without a corpus-wide re-aim.
- verbatim relocation: the moved bytes leave the spine and enter the module with no wording change; only the surrounding section framing differs.
- pins re-aim: pointing a check_maintenance_pins.sh row whose target literal moved at the module path beside its provenance comment; never weakening or deleting the pin.
- dormant pins checkpoint: the check_maintenance_pins.sh mid-suite checkpoint that trips on the recorded baseline failures and leaves the rows after it unexecuted while the baseline stands.
- vendored-sync landing path: the repository AGENTS.md's sanctioned alternative to same-run twin landing: a backlog item naming the changed files so the runtime twins are a tracked handoff instead of orphan dirt.

## Why

The two skill monoliths dominate session context on every authoring, execution, and review turn that loads them, and the origin row's cluster witnesses the failure mode: an 807-line skill load truncated mid-file and the session ran on the partial contract. Stable protocol blocks sit inline in the same bytes as the phase spines, so a session that needs one section pays for all of them; the heaviest stable block of each monolith is pure context tax for every phase that does not need it.

## Gist & Examples

TLDR: each skill monolith's heaviest stable protocol block moves verbatim into a referenced module file beside it, with the pins rows re-aimed beside provenance; driving force efficiency and token-usage.

Before: a session loading agents/skills/plans/SKILL.md for Phase 0 authoring pays for the 44-rule validation authoring-rules block it will not read until the Validation Commands step, and an execution session pays for the full Worktree-first standard it consults once at setup.

After: agents/skills/plans/validation-authoring-rules.md and agents/skills/execute-plan/worktree-first.md carry the moved bytes verbatim; each SKILL.md keeps its section heading as a reference hub with a one-line pointer; the pins rows whose literals moved point at the module paths beside their provenance; a vendored-sync backlog item tracks the runtime twins.

Edge cases: a pin whose literal lives in both the spine and the module (a repeated span) resolves to the module where the moved region lives and stays untouched where the spine retains it, and a split count re-aim checks both legs and preserves the pre-extraction total, recorded as both locations by the enumeration witness, the re-derived count being the value the per-row verification owns; a pins row grepping a THIRD file's content (a blueprint body naming the SKILL.md path in prose) stays untouched because the reference hub keeps those references true; the extraction never edits inside the moved bytes, so a review finding on moved content is a relocation defect, not a content defect; spine-local anchors inside moved bytes (the Writing section, the plan template, the Phase 0 identity block) resolve via the sibling SKILL.md through the hub pointer and are not relocation defects.

## Outcome

Loading either skill for a single phase no longer pays for that skill's heaviest stable protocol block.

- The validation authoring rules load on demand from agents/skills/plans/validation-authoring-rules.md when a plan's Validation Commands section is authored or reviewed.
- The Worktree-first standard loads on demand from agents/skills/execute-plan/worktree-first.md when a worktree setup, adoption, or closeout decision is made.
- The pins failure set stays byte-identical to the recorded baseline with every moved literal's pin re-aimed beside provenance, and the runtime twins are a tracked handoff rather than orphan dirt.

Gate delta: none; the change relocates existing prose into module files and re-aims existing pins rows beside provenance; no new refusal class, hard gate, fence, protocol layer, or schema field; no removed refusal, check, or field; the pins rows remain the same gates with re-aimed targets.

## Assumptions

- assume the tranche is one block per monolith, the heaviest stable block of each: the validation authoring rules for plans and the Worktree-first standard for execute-plan; basis: the origin row's delegation to the plan's design on evidence (the decision-points trailer's recorded resolution) and the largest-self-contained-frozen-rules-block evidence: the validation authoring rules are the plans spine's largest self-contained frozen-rules block and the Worktree-first standard the execute-plan spine's (the larger Plan Quality Gate and Phase 3 regions embed sub-agent prompt templates and ride the phase spine).
- assume the spine keeps each section heading as the reference hub so cross-file prose naming the SKILL.md section (the Worktree-first span the pins grep shows in the maintenance blueprint bodies) stays true without a corpus-wide re-aim; basis: the pins rows grep third-file content whose literals name the SKILL.md path.
- assume pins rows whose target literals moved are re-aimed at the module path beside their provenance comments, never weakened or deleted; basis: the origin row's companion rule.
- assume the runtime twins land through the tracked vendored-sync landing path (a backlog item naming the two module files), not in this run; basis: the repository AGENTS.md vendored-sync rule's tracked-landing-path arm; the origin row's named shared-body runtime-neutrality gate no longer exists in the tree, the live REPO_SKILL_SURFACES enumeration in scripts/test_harness_policy_contract.py asserts spans outside the moved regions, and the module files join no enumeration this tranche.
- assume Phase 1 confirmation is satisfied by the operator's standing pre-authorization for authoring runs, with the PLAN-PROMPTS entry prompt as the scope of record; basis: the authoring dispatch template's standing pre-authorization.

Decision points requiring a grill: module tranche selection: resolved by the origin row's delegation to the plan's design on evidence (docs/history/backlog/2026-10-04-skill-monolith-module-extraction.md Fix shape, 2026-10-04, sequencing note 2026-10-13); affected plan sections: Terms, Gist, Tasks 1-2; reference-hub shape: resolved at authoring on the pins evidence (cross-file prose literals name the SKILL.md path); affected plan sections: Gist, Tasks 1-2.

## Standing constraints

- The moved bytes relocate verbatim: no task edits wording inside a moved region; a review finding on moved content is a relocation defect and restores the spine's prior bytes.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each module's content equals the removed spine bytes verbatim apart from the section framing, provable by a diff between the pre-extraction spine region and the module.
- compatibility: the pins failure set is byte-identical to the execution-start pins capture; no pin weakened, deleted, or left pointing at a moved-away literal.
- readability: each spine's hub carries the heading plus a one-line load-on-demand reference naming the module path.

**Done when:**
- agents/skills/plans/validation-authoring-rules.md and agents/skills/execute-plan/worktree-first.md exist with verbatim content; both spines carry the hubs; the pins failure set is byte-identical to the execution-start pins capture and every re-aimed row passes its per-row verification; the bootstrap companion suite exits 0 and the readiness compatibility class keeps its recorded baseline status; the vendored-sync backlog item exists naming the two module files; no file beyond the enumerated Review Scope set plus this plan file changed.

**Ship when:** none; the change is repository-verifiable only.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/validation-authoring-rules.md` *(new)*
- `agents/skills/execute-plan/worktree-first.md` *(new)*
- `agents/skills/plans/SKILL.md` (only the validation authoring rules region and its replacement hub; all other regions are frozen; reject any review finding that touches them)
- `agents/skills/execute-plan/SKILL.md` (only the Worktree-first standard region and its replacement hub; all other regions are frozen; reject any review finding that touches them)
- `scripts/check_maintenance_pins.sh` (only rows whose target literals live in the moved regions; all other rows are frozen; reject any review finding that touches them)
- `scripts/test_execute_plan_worktree_bootstrap.py` (all SKILL_PATH readers of the moved Worktree-first region: the Transfer-in recipe source resolution, the stranded-input pre-pass literal assertions, and the closeout-migration block lead-in search)
- `scripts/test_plan_readiness.py` (only the execute-plan profile/policy compatibility test's extraction source)

**Documentation:**
- `docs/history/backlog/` *(new vendored-sync landing-path item only)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- the moved regions' content wording; reason: verbatim relocation is the standing constraint; content findings restore prior bytes.
- any further block extraction (budget gate, plan format, sub-agent templates); reason: later tranches ride this precedent (incremental per-module moves keep each intermediate module boundary explicit).
- the runtime twins' actual sync; reason: the tracked landing path owns it (assumption).

## Validation Commands

Authoring-time rule 29 record: the no-em-dash scan, the public-hygiene scan, the readiness pre-round invocation, the rule 19 RED-today probes, and the rule 22 mechanical audit (each pinned span exactly once in its owning snippet, plus `bash -n` over this block) run over these bytes before round 1, and their outcomes append below as Recorded lines.

Recorded 2026-10-14 (authoring session sess_9f5841ba, over the v1 bytes on branch authoring/skill-monolith-module-extraction): fix_plan_em_dashes.py 0 substitutions; em-dash touched scan exit 0; public-hygiene scan final line OUTCOME: pass; python3 scripts/plan_readiness.py --pre-round exit 0 OUTCOME: pass on the first run; rule 19 RED-today evidence: the module-existence probes exit 1 today (both module files absent), the spine-reference greps exit 1 today (no load-on-demand pointers yet), and the vendored-item probe exits 1 today; rule 22 mechanical audit PASS: each pinned span occurs in its Validation grep and its owning task text, and bash -n over the extracted block passes; pins baseline evidence: bash scripts/check_maintenance_pins.sh at the v1 base commit exits 1 with 21 PIN FAIL lines ending OUTCOME: fail, matching the tracked baseline docs/history/backlog/2026-10-12-pins-suite-main-baseline-21-failures.md whose repair plan (docs/history/plans/2026-10-13-red-on-main-baseline-repair-and-auto-demote.md) is open; the pins gates in this plan are therefore baseline-comparison gates (no new failures, none fixed, re-aimed rows individually verified), not suite-green gates; the readiness compatibility class ExecutePlanProfilePlacementCompatibilityTest likewise exits 1 at the base tree (failures=1, an untracked pre-existing content assertion on the policy paragraph's wording, recorded 2026-10-14), so its gate is a status-comparison (the class keeps its baseline status through the re-point; a broken extraction would flip it to an error), not a suite-green gate; if the baseline repair lands before execution, re-derive the baseline pins count and the compatibility class status (exit 1, failures=1) at execution start and record both in the execution manifest; the plans spine's moved region carries exactly one pins-row literal (the graded post-certification rule row, pins script line 2587, needle at agents/skills/plans/SKILL.md line 502), so Task 1 expects that one re-aim beside its provenance; the failure-set diff gate catches re-aim misses only ahead of the dormant pins checkpoint, so the per-row and enumeration witnesses own the dormant tail, and the spine complement's freeze rests on the Review Scope's frozen-region rejection plus the pins coverage rather than a second diff gate.

```bash
test -f agents/skills/plans/validation-authoring-rules.md || { echo "plans module missing"; exit 1; }

test -f agents/skills/execute-plan/worktree-first.md || { echo "execute-plan module missing"; exit 1; }

grep -q "validation-authoring-rules.md" agents/skills/plans/SKILL.md || { echo "plans spine lacks the load-on-demand reference"; exit 1; }

grep -q "worktree-first.md" agents/skills/execute-plan/SKILL.md || { echo "execute-plan spine lacks the load-on-demand reference"; exit 1; }

grep -q "^## Validation Commands (authoring rules)" agents/skills/plans/SKILL.md || { echo "plans spine dropped the reference hub heading"; exit 1; }

grep -q "^## Worktree-first standard" agents/skills/execute-plan/SKILL.md || { echo "execute-plan spine dropped the reference hub heading"; exit 1; }

grep -q "Transfer-in implementation (how step 2 runs)" agents/skills/execute-plan/SKILL.md && { echo "execute-plan spine still carries the moved region (copy-not-move)"; exit 1; }
grep -q "Self-match immunity for embedded gates" agents/skills/plans/SKILL.md && { echo "plans spine still carries the moved region (copy-not-move)"; exit 1; }

BASE_FILE=/tmp/smme-exec-base.rev
BASE=$(cat "$BASE_FILE")
git show "$BASE":agents/skills/plans/SKILL.md | sed -n '/^## Validation Commands (authoring rules)$/,/^## Budget gate/p' | sed '1d;$d' > /tmp/plans-region.txt
tail -n +2 agents/skills/plans/validation-authoring-rules.md > /tmp/plans-module.txt
diff /tmp/plans-region.txt /tmp/plans-module.txt > /dev/null || { echo "plans module body is not a verbatim relocation"; exit 1; }

git show "$BASE":agents/skills/execute-plan/SKILL.md | sed -n '/^## Worktree-first standard$/,/^## Phase 0: Run Setup/p' | sed '1d;$d' > /tmp/ep-region.txt
tail -n +2 agents/skills/execute-plan/worktree-first.md > /tmp/ep-module.txt
diff /tmp/ep-region.txt /tmp/ep-module.txt > /dev/null || { echo "execute-plan module body is not a verbatim relocation"; exit 1; }

git show "$BASE":scripts/check_maintenance_pins.sh | grep -oE "'[^']{4,}'|\"[^\"]{4,}\"" | sort -u > /tmp/smme-enum-lits.txt
: > /tmp/smme-enum-witness.txt
while IFS= read -r lit; do
  case "$lit" in
    '"'*) lit="${lit#\"}"; lit="${lit%\"}" ;;
    *) lit="${lit#\'}"; lit="${lit%\'}" ;;
  esac
  hit=""
  for f in agents/skills/plans/validation-authoring-rules.md agents/skills/execute-plan/worktree-first.md agents/skills/plans/SKILL.md agents/skills/execute-plan/SKILL.md; do
    grep -qF -- "$lit" "$f" && hit="$hit $f"
  done
  if [ -n "$hit" ]; then
    echo "$lit ->$hit" >> /tmp/smme-enum-witness.txt
  elif git show "$BASE":agents/skills/plans/SKILL.md | grep -qF -- "$lit" || git show "$BASE":agents/skills/execute-plan/SKILL.md | grep -qF -- "$lit"; then
    echo "ENUM MISS (moved bytes lost): $lit" >&2; exit 1
  else
    echo "$lit ->absent-by-design" >> /tmp/smme-enum-witness.txt
  fi
done < /tmp/smme-enum-lits.txt
[ -s /tmp/smme-enum-witness.txt ] || { echo "enumeration witness is empty"; exit 1; }
echo "enumeration witness recorded"

bash scripts/check_maintenance_pins.sh > /tmp/pins-after.txt 2>&1
grep "PIN FAIL" /tmp/smme-pins-base.txt | LC_ALL=C sort > /tmp/pins-base-sorted.txt
grep "PIN FAIL" /tmp/pins-after.txt | LC_ALL=C sort > /tmp/pins-after-sorted.txt
diff /tmp/pins-base-sorted.txt /tmp/pins-after-sorted.txt > /dev/null || { echo "pins failure set changed vs the execution-start capture"; exit 1; }
echo "pins failure set matches the execution-start capture (authoring-recorded baseline 21; re-derive per the Recorded line if the baseline repair landed)"

python3 scripts/test_execute_plan_worktree_bootstrap.py > /dev/null 2>&1 || { echo "bootstrap suite broke"; exit 1; }
python3 scripts/test_plan_readiness.py ExecutePlanProfilePlacementCompatibilityTest > /tmp/compat-after.txt 2>&1
grep -q "FAILED (failures=1)" /tmp/compat-after.txt || { echo "readiness compatibility class status changed vs its recorded baseline (exit 1, failures=1)"; exit 1; }

test -f docs/history/backlog/2026-10-14-vendored-sync-module-twins.md || { echo "vendored-sync landing item missing"; exit 1; }
grep -q "validation-authoring-rules.md" docs/history/backlog/2026-10-14-vendored-sync-module-twins.md || { echo "vendored item omits the plans module"; exit 1; }
grep -q "worktree-first.md" docs/history/backlog/2026-10-14-vendored-sync-module-twins.md || { echo "vendored item omits the execute-plan module"; exit 1; }
grep -qi "rsync" docs/history/backlog/2026-10-14-vendored-sync-module-twins.md || { echo "vendored item omits the sync rule"; exit 1; }

CHANGED=$(git diff --name-only "$BASE" | LC_ALL=C sort)
EXPECTED=$(printf '%s\n' \
"agents/skills/execute-plan/SKILL.md" \
"agents/skills/execute-plan/worktree-first.md" \
"agents/skills/plans/SKILL.md" \
"agents/skills/plans/validation-authoring-rules.md" \
"docs/history/backlog/2026-10-14-vendored-sync-module-twins.md" \
"docs/history/plans/2026-10-14-skill-monolith-module-extraction.md" \
"scripts/check_maintenance_pins.sh" \
"scripts/test_execute_plan_worktree_bootstrap.py" \
"scripts/test_plan_readiness.py" | LC_ALL=C sort)
[ "$CHANGED" = "$EXPECTED" ] || { echo "changed-file set differs from the declared scope"; exit 1; }
echo "changed-file set matches the declared scope"

test -z "$(git status --porcelain)" || { echo "working tree carries untracked or uncommitted residue"; exit 1; }
echo "working tree clean after all task commits"
```

### Task 1: extract the validation authoring rules from the plans spine

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/plans/validation-authoring-rules.md` *(new)*
- `agents/skills/plans/SKILL.md`
- `scripts/check_maintenance_pins.sh`

- [ ] Execution-start capture: before any task edits, record `git rev-parse HEAD` into /tmp/smme-exec-base.rev and run `bash scripts/check_maintenance_pins.sh > /tmp/smme-pins-base.txt 2>&1`; the verbatim, changed-file, and pins gates read these captures, never a moving branch ref [class: IMPLEMENTATION_REQUIRED]
- [ ] `agents/skills/plans/validation-authoring-rules.md` carries the validation authoring rules block relocated verbatim from agents/skills/plans/SKILL.md (the region spans the `## Validation Commands (authoring rules)` heading through the line before the `## Budget gate` heading; the module body excludes the heading itself), with a one-line provenance header naming the origin section and this plan's slug [class: IMPLEMENTATION_REQUIRED]
- [ ] the plans spine's region is replaced by the reference hub: the same section heading plus a one-line load-on-demand pointer naming agents/skills/plans/validation-authoring-rules.md, and no other spine byte changes [class: IMPLEMENTATION_REQUIRED]
- [ ] verbatim witness: a diff of the pre-extraction spine region against the module body (excluding the provenance header) is empty [class: REPOSITORY_TEST]
- [ ] pins re-aim: every check_maintenance_pins.sh row whose target literal lives in the moved region is re-aimed at the new module path beside its provenance comment, and rows whose literals live elsewhere (third-file prose, retained spine bytes) are untouched [class: IMPLEMENTATION_REQUIRED]
- [ ] pins baseline: the pins failure set after the extraction is byte-identical to the execution-start pins capture (authoring-recorded baseline 21 failures, docs/history/backlog/2026-10-12-pins-suite-main-baseline-21-failures.md; no new failures, none fixed) [class: REPOSITORY_TEST]
- [ ] Safety witness (no-weakening): the fenced enumeration loop's recorded output is the shared witness covering agents/skills/plans/SKILL.md targets: each harvested literal located (re-aimed module path, retained spine bytes, or split across both with the pinned count re-derived beside provenance and the retained leg preserved) or classified absent-by-design; any literal present at base in a moved region and absent everywhere post fails the run [class: REPOSITORY_TEST]
- [ ] per-row verification: each re-aimed row's grep or scan executes verbatim against the module path (expect pass) and once against a scratch copy with the span stripped (expect fail; absence rows invert the expectation), both outcomes recorded, including rows behind the dormant pins checkpoint that the suite does not reach while the baseline is red [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the module file does not exist and the spine still carries the inline block [class: REPOSITORY_TEST]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the module exists, the spine carries the hub, the verbatim witness is empty, and the pins failure set is byte-identical to the baseline [class: REPOSITORY_TEST]
- [ ] Commit: `plans: extract the validation authoring rules into a referenced module` [class: IMPLEMENTATION_REQUIRED]

### Task 2: extract the Worktree-first standard from the execute-plan spine

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/execute-plan/worktree-first.md` *(new)*
- `agents/skills/execute-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`
- `scripts/test_execute_plan_worktree_bootstrap.py`
- `scripts/test_plan_readiness.py`

- [ ] `agents/skills/execute-plan/worktree-first.md` carries the Worktree-first standard relocated verbatim from agents/skills/execute-plan/SKILL.md (the region spans the `## Worktree-first standard` heading through the line before the `## Phase 0: Run Setup` heading; the module body excludes the heading itself), with a one-line provenance header naming the origin section and this plan's slug [class: IMPLEMENTATION_REQUIRED]
- [ ] the execute-plan spine's region is replaced by the reference hub: the same section heading plus a one-line load-on-demand pointer naming agents/skills/execute-plan/worktree-first.md, and no other spine byte changes [class: IMPLEMENTATION_REQUIRED]
- [ ] verbatim witness: a diff of the pre-extraction spine region against the module body (excluding the provenance header) is empty [class: REPOSITORY_TEST]
- [ ] pins re-aim: every check_maintenance_pins.sh row whose target literal lives in the moved region is re-aimed at the new module path beside its provenance comment; rows grepping third-file prose (the blueprint bodies naming the SKILL.md path) stay untouched because the reference hub keeps them true; the pins failure set after the extraction is byte-identical to the execution-start pins capture (no new failures, none fixed) [class: IMPLEMENTATION_REQUIRED]
- [ ] Safety witness (no-weakening): the fenced enumeration loop's recorded output is the shared witness covering agents/skills/execute-plan/SKILL.md targets, with the same located-or-absent-by-design arms and the same moved-loses failure [class: REPOSITORY_TEST]
- [ ] per-row verification: each re-aimed row's grep or scan executes verbatim against the module path (expect pass) and once against a scratch copy with the span stripped (expect fail; absence rows invert the expectation), both outcomes recorded, including rows behind the dormant pins checkpoint [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the module file does not exist and the spine still carries the inline section [class: REPOSITORY_TEST]
- [ ] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [ ] companion re-point: every scripts/test_execute_plan_worktree_bootstrap.py SKILL_PATH reader of the moved region (Transfer-in recipe source, stranded-input pre-pass literals, closeout-migration block lead-in) reads agents/skills/execute-plan/worktree-first.md, and the suite's module docstring recipe-home naming plus the extraction helper's stale fence comment update in the same edit [class: IMPLEMENTATION_REQUIRED]
- [ ] companion gates: scripts/test_plan_readiness.py's execute-plan profile/policy compatibility test reads the moved literals from the module; the bootstrap suite exits 0 and the readiness compatibility class keeps its recorded baseline status (exit 1, failures=1) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the module exists, the spine carries the hub, the verbatim witness is empty, the pins failure set is byte-identical to the baseline, the bootstrap companion suite exits 0, and the readiness compatibility class keeps its recorded baseline status [class: REPOSITORY_TEST]
- [ ] Commit: `execute-plan: extract the Worktree-first standard into a referenced module` [class: IMPLEMENTATION_REQUIRED]

### Task 3: the tracked vendored-sync landing path

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `docs/history/backlog/2026-10-14-vendored-sync-module-twins.md` *(new)*

- [ ] docs/history/backlog/2026-10-14-vendored-sync-module-twins.md exists as the tracked vendored-sync landing path naming the two module files (agents/skills/plans/validation-authoring-rules.md and agents/skills/execute-plan/worktree-first.md), their runtime twin destinations, and the sync rule (rsync semantics per the repository AGENTS.md vendored-sync rules), keyed to this plan's landing as the trigger [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the item exists at the backlog top level naming both module paths [class: REPOSITORY_TEST]
- [ ] Commit: `backlog: track the vendored-sync landing path for the extracted module twins` [class: IMPLEMENTATION_REQUIRED]
