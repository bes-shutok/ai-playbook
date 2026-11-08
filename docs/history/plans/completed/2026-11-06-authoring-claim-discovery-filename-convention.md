# Plan: Authoring-claim discovery matches both filename conventions

Backlog origin: docs/history/backlog/2026-11-04-authoring-claim-discovery-filename-convention.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-authoring-claim-discovery-filename-convention-p274940d2-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Executed: yes (c26a2b7b2, final pre-squash tip after two mid-landing rebases; the originally recorded bf39b860 was the pre-rebase tip of the same run)
Authoring claim: 2026-11-04-authoring-claim-discovery-filename-convention.md (session sess_47f41ee9-0c03-416b-9227-174a626f326f)

## Terms

- claim file: the five-frontmatter-line marker an authoring session writes under `docs/tmp/authoring-claims/` (procedure of record: the AUTHORING CLAIM paragraph in `agents/skills/maintenance/template-authoring.md`).
- claims directory: the primary checkout's facts-resolved `{tmp_dir}/authoring-claims/` (default `docs/tmp/authoring-claims/`).
- entry slug: the dispatch entry's heading slug in `docs/history/backlog/PLAN-PROMPTS.md`; for a target backlog row it is read from the entry whose `Origins:` list names that row, falling back to the row basename with its leading date prefix stripped when no entry names it.
- origin row basename: the target backlog row's file basename with its `.md` extension stripped (this origin's is `2026-11-04-authoring-claim-discovery-filename-convention`).
- filename stem: a claim file's basename with `.md` stripped.
- item: line: the claim frontmatter line naming the target backlog row path; every conforming claim carries it regardless of its filename; the match compares both sides resolved to the facts-resolved repo-relative row path, and a nonconforming line matches nothing.
- three-key match: the discovery match rule this plan lands: with an unfiltered claims-directory listing, a claim file matches the target when its filename stem equals the origin row basename, or its filename stem equals the entry slug (vacuous when the target has no dispatch entry), or its `item:` line equals the target backlog row path under the comparison form above.
- foreign claim: a claim file naming a session id other than the checking session's (the AUTHORING CLAIM gate's foreign rules, including the no-parseable-session-line rule).
- fresh: a claim whose `updated:` timestamp is within one cadence period (2 hours).
- collision disposition: stand down (the fresh-foreign-claim refusal), adopt (the stale-foreign-claim takeover), or raced-pick continuation, run before authoring starts; first-landed-wins is not a pre-authoring arm: it stays the landing-time resolution of the duplicate-origin coverage gate.
- first-landed-wins: the landing-time resolution the duplicate-origin coverage gate applies when two series for one origin both exist.
- duplicate-origin coverage gate: the landing-time gate that refuses a second authoring series for one origin; unchanged by this plan.
- fresh-foreign-claim refusal: the gate arm that stands a session down, writing nothing, when a fresh matching foreign claim exists.
- stale-foreign-claim takeover: the arm that deletes a foreign claim stale past one cadence period and then proceeds with the normal claim create.
- raced-pick continuation: the arm that records raced-(b) with the foreign session id and continues the selection walk to the next available entry when a fresh-foreign-claim refusal hits an already-picked target.
- `G1a`: the authoring-lane occupancy guard in `agents/skills/maintenance/guards.md` whose discovery arm reads the claims directory.
- noclobber create: the create-if-absent claim write (`set -C` plus one printf redirection; the redirection failure is the refusal path).
- AUTHORING CLAIM gate: the foreign-claim fire-time gate inside the AUTHORING CLAIM paragraph that refuses a fresh foreign claim before the claim create.
- D2 consult: the fresh-foreign-claim consult inside `D2 (author)` in `agents/skills/maintenance/decisions.md` that skips an occupied target at selection.
- survey arm: the Authoring-claim consult bullet in `agents/skills/maintenance/survey-arms.md`.
- Top-level presence probe: the survey-arms presence arm that classifies a top-level entry live when a fresh authoring claim naming the entry exists.
- pins suite: `scripts/check_maintenance_pins.sh`.
- the 2026-11-03 twin-carrier collision: the witnessed authoring race this plan prices against (the origin row's twin 18:13 auth carriers over one PLAN-PROMPTS entry; the loser's r1-r4 series burned).

## Why

A claim-presence check that keys only the checking session's own filename convention reports a clean race while a convention-divergent foreign claim sits in the same directory, so two sessions author competing plans for one origin and the loser spends a full review series on text that can never land. The 2026-11-03 twin-carrier collision witnessed exactly this loss, and lesson 393 records the rule: match both keys that exist in practice, never the checking session's own key alone.

## Gist & Examples

TLDR: the three discovery surfaces apply the three-key match, so a convention-divergent foreign claim (either filename convention, or a conforming `item:` line under any filename) refuses or skips the target before authoring starts, fixing the witnessed race that burned a loser's review series.

Today the AUTHORING CLAIM gate checks exactly `<backlog-item-basename>.md`; a foreign session that wrote `authoring-claim-discovery-filename-convention.md` (entry-slug convention) is invisible to that check, and the D2 consult and survey arm read the same surface with the same single-key assumption. After this plan each surface lists the claims directory unfiltered and applies the three-key match: the loser's re-check finds the winner's origin-basename claim, a slug-keyed claim is found by an origin-basename checker and vice versa, and a conforming `item:` line matches under any filename.

## Outcome

An authoring race is caught at claim or selection time instead of at the landing-time coverage gate, so no session spends a review series on text that can never land.

- A fresh foreign claim is found regardless of which filename convention its session used, or when its filename matches neither convention but its `item:` line is conforming.
- The collision disposition runs before authoring starts, reusing the existing refusal, takeover, and raced-pick continuation arms.
- The landing-time duplicate-origin coverage gate and its first-landed-wins resolution stay byte-unchanged as the backstop.

Gate delta: checked-set widening only, no new refusal class: the fresh-foreign-claim refusal's discovery scan widens from the single canonical filename to the three-key match at three existing read-only surfaces; no gate, fence, refusal class, schema field, or protocol layer is added or removed; the widening is priced by the 2026-11-03 twin-carrier collision (origin row and lesson 393), with expected catch frequency two witnessed authoring races over one origin (2026-09-30 and 2026-11-03), false-positive cost a misjudged match refusing or skipping a free target bounded by the raced-pick continuation's recorded walk and the stale-foreign-claim takeover, and review at the next witnessed authoring race or 2027-05-06, whichever first; the pin family's false-positive cost on the amended gate paragraph is bounded by the pins suite's existing region-scoped, wrap-tolerant fragment mechanism. Accepted residual: the widened scan is check-then-act while the noclobber create stays filename-guarded, so a convention-divergent foreign claim created between the listing and the create falls in a seconds-wide window back to the landing-time duplicate-origin coverage gate; this residual is priced, not fixed, by this plan.

## Assumptions

- assume the AUTHORING CLAIM duty's procedure home is `agents/skills/maintenance/template-authoring.md`; the origin row and entry cite `agents/skills/maintenance/prompt-templates.md`, which is pointer stubs since the 2026-10-10 split; this stale-citation acceptance is an interpretive rule for reading the origin, not a task editing the origin row or the PLAN-PROMPTS entry; basis: `agents/skills/maintenance/prompt-templates.md` read 2026-11-06, the plans skill's re-home note.
- assume `scripts/check_authoring_plans_liveness.py` needs no change: it already scans the claims directory unfiltered and matches plan identity against claim text; basis: source read 2026-11-06.
- assume the `G1a` discovery arm needs no byte change in this plan, but its item-matching span is ambiguous between content-keyed and filename-stem-keyed readings, so Task 2 verifies the pairing under both conventions and records any stem-keyed limitation in the closeout note; basis: guards.md read 2026-11-06, the r1 risk finding.
- assume the create side stays filename-guarded: the noclobber create refuses on the canonical filename only, the pre-create gate supplies the origin-level refusal, and the seconds-wide gate-to-create window is the accepted residual priced on the Gate delta line; basis: the AUTHORING CLAIM paragraph's create recipe, read 2026-11-06.
- assume the collision disposition needs no new machinery: the fresh-foreign-claim refusal (stand down), the stale-foreign-claim takeover (adopt path), and the raced-pick continuation already dispose a found collision before authoring; basis: template-authoring.md read 2026-11-06.

Decision points requiring a grill: matching strategy: two-key unfiltered matching chosen over canonical-convention enforcement; simplest-design comparison: widening existing read-only scan spans is prose-only with no creator migration, while canonical enforcement adds an enforcement duty and a same-change migration for zero additional catch beyond the scan widening; basis: maintenance-selected arm receipt 2026-11-06; affects Task 2. Key set: the claim's `item:` line joins the two filename keys because frontmatter-divergent claim files are a witnessed class (the no-parseable-session-line rule exists for that reason) and the read is already paid by the `G1a` arm; basis: maintenance-selected arm receipt 2026-11-06; affects Task 2. Name: the landed rule is named the three-key match (the origin row's two-key name covered only the filename keys); basis: r1 panel naming-consistency findings 2026-11-06; affects Terms, Task 2.

## Tasks

### Task 1: Pin the three-key match rule in the pins suite

Files:
- scripts/check_maintenance_pins.sh
- docs/history/plans/2026-11-06-authoring-claim-discovery-filename-convention.md (the amended gate paragraph draft this task derives its pin literals from; the plan file is the reviewed artifact, not an implementation target)

Evidence:
- Suite run before Task 2 reports the new cells as failing pins (RED), naming each missing span; the RED run's per-cell `PIN FAIL` lines are recorded verbatim, and every new cell must appear among them: a new cell absent from the RED list is a non-discriminating pin whose literal is re-derived before Task 2 starts.

Checklist:
- [x] Draft the amended gate paragraph first in this task and derive each pin literal as a contiguous span of that draft; use one bash `pin` cell per rule element (listing key, basename key, slug key, vacuous clause, resolution rule, `item:` key, comparison form, collision disposition) so one RED run names every missing span, and keep the new cells out of warning-only families. [class: REPOSITORY_TEST]
- [x] Pin the rule's one home (`template-authoring.md`) on the literals that carry the rule: the unfiltered claims-directory listing, the origin row basename key, the entry slug key with its vacuous clause and resolution rule, the `item:` line key with its comparison form, and the collision-disposition-before-authoring wording. [class: REPOSITORY_TEST]
- [x] Pin the two consult surfaces (`decisions.md`, `survey-arms.md`) on their by-reference citation anchors only (the citation span plus the home-path literal); presence cells pin citation anchors only, never restated constants. [class: REPOSITORY_TEST]
- [x] Pin the rule's one home and the two by-reference citations together against restatement: presence cells as above plus `expect_absent_flat` cells on both consults for the home's distinctive rule literals (the unfiltered-listing, vacuous-clause, and comparison-form fragments), so a consult that cites the gate and also restates the constants fails the suite. [class: REPOSITORY_TEST]
- [x] Pin the amended plans-skill sentence's three-key-reality fragment in `agents/skills/plans/SKILL.md`, so the amendment's presence and any later revert both fail the suite. [class: REPOSITORY_TEST]
- [x] Enumerate the pre-existing pins whose regions or fragments intersect the spans Task 2 amends: sweep the suite for every pin whose fragment or region intersects the four target files (the fragment pins on the authoring-template, decisions, and survey-arms variables, the region blocks over them, and the plans-skill variable), and list each hit. [class: REPOSITORY_TEST]
- [x] Record the reconciliation per enumerated hit: preserve the pinned fragment verbatim in the amended text or consciously update that pin in the same change. [class: REPOSITORY_TEST]
- [x] Run the pins suite and record the expected RED cell output before Task 2. [class: REPOSITORY_TEST]

### Task 2: Amend the discovery surfaces with the three-key match rule

Files:
- agents/skills/maintenance/template-authoring.md
- agents/skills/maintenance/decisions.md
- agents/skills/maintenance/survey-arms.md
- agents/skills/plans/SKILL.md

State the match rule once, in the AUTHORING CLAIM gate (the duty home), and cite it by reference from the two consults. The tmp_dir-override caveat on both consults stays.

Evidence:
- Pins cells from Task 1 pass against the amended bytes (GREEN).
- The three amended spans read as one rule: unfiltered listing, three match keys, fresh-foreign refusal unchanged.

Checklist:
- [x] AUTHORING CLAIM gate: replace the single-filename existence check with the unfiltered three-key scan; a fresh matching foreign claim (or a matching claim with no parseable session line) refuses exactly as today, and a stale one follows the existing stale-foreign-claim takeover path. [class: IMPLEMENTATION_REQUIRED]
- [x] State the entry-slug key's vacuous clause (a target with no dispatch entry leaves the key unsatisfied and the match reduces to the other two keys) and its resolution rule (the entry whose Origins list names the row, date-stripped basename fallback) in the gate wording. [class: IMPLEMENTATION_REQUIRED]
- [x] State the `item:` line's comparison form (both sides resolved to the facts-resolved repo-relative row path; a nonconforming line matches nothing) in the gate wording. [class: IMPLEMENTATION_REQUIRED]
- [x] D2 consult in `decisions.md`: cite the gate's match rule by reference for what counts as a claim "sitting there"; no constants restated. [class: IMPLEMENTATION_REQUIRED]
- [x] Survey arm in `survey-arms.md`: same by-reference citation; the facts `tmp_dir` override caveat remains. [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the plans-skill sentence that promises plan-slug claims never match backlog-item targets so it states the three-key matching reality for a slug-coinciding claim, in the same change. [class: IMPLEMENTATION_REQUIRED]
- [x] No bytes change in the duplicate-origin coverage gate, the first-landed-wins resolution, the noclobber create recipe, or the takeover and raced-pick continuation arms. [class: IMPLEMENTATION_REQUIRED]
- [x] Closeout verification, recorded in the closeout note: the `G1a` arm explains its own pending child's claim under both filename conventions and under a missing `item:` line (fixing or recording a stem-keyed limitation if it does not); the Top-level presence probe's "naming the entry" matching is verified convention-independent or amended to cite the gate's match rule; the liveness checker verified convention-independent. [class: IMPLEMENTATION_REQUIRED]

### Task 3: Regression and integration validation

Files: none (verification only; no file bytes change in this task)

Evidence:
- All named suites exit 0 against the amended worktree.

Checklist:
- [x] `bash scripts/check_maintenance_pins.sh` exits 0 with `OUTCOME: pass`. [class: REPOSITORY_TEST]
- [x] `python3 scripts/check_authoring_plans_liveness.py --repo .` exits 0 with `OUTCOME: pass` on a clean checkout. [class: REPOSITORY_TEST]
- [x] The public hygiene scan exits 0 over the changed files. [class: REPOSITORY_TEST]
- [x] The implementation delta over the branch is exactly the three maintenance skill files plus `scripts/check_maintenance_pins.sh` plus the plans-skill amendment, checked by a path-scoped diff; the expected non-implementation riders (the plan file itself; at landing, the origin-row covered flip and the PLAN-PROMPTS prune receipt) are named expected changes, never violations. [class: REPOSITORY_TEST]

## Evaluation Criteria

- correctness: a slug-keyed foreign claim, an origin-basename-keyed foreign claim, and an item-line-only foreign claim (filename matching neither convention) are all matched by every amended surface; the pins cells fail on the pre-amendment bytes and pass on the amended bytes.
- consistency: the rule is stated once in the duty home under the three-key name and cited by reference from both consults; the pins refuse a restated copy of the constants.
- regression safety: the pins suite, the liveness checker, and the hygiene scan exit 0; the duplicate-origin coverage gate and first-landed-wins spans are byte-unchanged on the branch diff.

## Review Scope

The panel reviews the branch diff. The implementation inventory is `agents/skills/maintenance/template-authoring.md`, `agents/skills/maintenance/decisions.md`, `agents/skills/maintenance/survey-arms.md`, `agents/skills/plans/SKILL.md`, and `scripts/check_maintenance_pins.sh`; `docs/history/plans/2026-11-06-authoring-claim-discovery-filename-convention.md` is the reviewed artifact, not implementation scope, and the landing-time riders (the origin-row covered flip, the PLAN-PROMPTS prune receipt) are named expected non-implementation changes. Findings class to check: restated constants between the duty home and the consults, a match-key omission (any of the three keys), a refusal-semantics change beyond the discovery scan (create, takeover, raced-pick continuation, coverage gate), and pins cells that pin prose too loose to fail on the rule's removal. Plan-file review follows the plans skill's review contract; the staging series is the review record of record.

## Validation Commands

- `bash scripts/check_maintenance_pins.sh` (exit 0 required)
- `python3 scripts/check_authoring_plans_liveness.py --repo .` (exit 0 required)
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-11-06-authoring-claim-discovery-filename-convention.md` (no blocking warnings)
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` (exit 0 required, run from the repository root)
