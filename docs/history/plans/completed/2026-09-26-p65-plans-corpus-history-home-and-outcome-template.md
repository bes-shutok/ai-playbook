# Plan: plans corpus reader Outcome template, history-tree home, and closure conventions (P65)

Backlog origins (scope of record):
- `docs/history/backlog/2026-09-26-plans-plain-outcome-summary.md`
- `docs/history/backlog/2026-09-25-plans-home-into-history-tree.md`
- `docs/history/backlog/2026-09-24-plans-rule36-fold-remove-count-obligations.md`
- `docs/history/backlog/2026-09-25-teach-origins-checker-fold-then-delete.md`

Backlog origin context: the first two origins are medium operator directives (simplicity); the last two are low code-quality folds whose task cluster is shared (Task 4).
Plan review: docs/reviews/2026-09-26-plan-review-2026-09-26-p65-plans-corpus-history-home-and-outcome-template-r1.md (r1, ready=no, 18 findings folded) · docs/reviews/2026-09-26-plan-review-2026-09-26-p65-plans-corpus-history-home-and-outcome-template-r2.md (r2, ready=no, 11 findings folded) - docs/reviews/2026-09-26-plan-review-2026-09-26-p65-plans-corpus-history-home-and-outcome-template-r3.md (r3, ready=no, 9 findings folded) - docs/reviews/2026-09-26-plan-review-2026-09-26-p65-plans-corpus-history-home-and-outcome-template-r4.md (r4, ready=no, 7 findings folded incl. 2 overflow rows) - docs/reviews/2026-09-26-plan-review-2026-09-26-p65-plans-corpus-history-home-and-outcome-template-r5.md (r5, ready=yes, 2 low findings folded; final round)

Driving force: simplicity (secondary: code-quality)
Force note: the two medium origins are direct operator directives for a simpler corpus shape and a reader-facing summary element; the two low origins ride the same closure story from the rule side and the verifier side, so code-quality is the ranked secondary, and park-triage would take the plan on the directives alone.

## Outcome

Move the plans corpus under the history tree, give every plan a plain-language Outcome summary, and let plan-closure tooling understand dispositions whose backlog files were deliberately deleted, so readers can classify any plan from its first lines and the survey machinery stops warning on work that is actually done.

- After execution the plans home and the backlog home share one history-tree layout, and the path keys, code defaults, test fixtures, catalogs, and archive instructions all resolve the new home.
- Every new plan opens with a self-contained Outcome section, so queue triage answers "what do I get if this executes" without parsing Terms or Tasks.
- The origins checker stops warning on origins whose dispositions were folded into completed plans and registry audit rows, while genuinely orphaned origins still warn.
- Folds that remove a count obligation re-simulate the surviving gate set, so stale count gates fail at review time instead of at execution time.

## Terms

- **Plans home**: the directory resolved from the facts key `plans_dir` (with its `completed/`/`deferred/`/`rejected/` archive siblings under `plans_completed_dir` and the conventional sibling names). Today `docs/plans/`; this plan moves it to `docs/history/plans/`.
- **Outcome section**: the new first required plan section (`## Outcome`): one plain-globish aim sentence plus two to four result bullets, enforced like any other required element.
- **Migrated-origin consult**: the origins checker's two new resolution arms for an origin whose per-item backlog file no longer exists because the fold-then-delete policy deleted it: the plan's own `## Disposition of migrated backlog items` section, and a document-registry migration-audit cell.
- **Migration-audit cell**: shorthand for a document-registry.md ROW whose notes cell carries both the `user-approved` token and the `migration audit` marker and whose cells (the src cell included) carry the former item's path or basename; the corpus precedent rows keep the basename in the src cell, not the notes cell.
- **Consumer sweep**: the enumerated skills, scripts, tests, catalogs, and templates that mention the plans home and must agree with the moved layout.

## Assumptions

- assume the history-tree origin's scope decision resolves to the FULL home move (active plans at the `docs/history/plans/` root, `completed/`/`deferred/`/`rejected/` siblings), not archives-only; basis: the repo's own schema already prescribes it (`agents/skills/doc-hierarchy/migration-map.md` maps `docs/plans/` to `history/plans/`; the layout gate's `docs/plans still at root` rule in `agents/skills/doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh:88` prescribes the history home, though that script's repo-class guard refuses to run on this repository so the prescription binds by rule text rather than by a local run; `agents/skills/execute-plan/SKILL.md` already treats `docs/history/plans/` as the post-migration `{plans_dir}`; `bootstrap-ai-playbook` teaches the history map as the greenfield canonical), and the consumer sweep found no consumer pinning `docs/plans/` as a stable cross-repo contract; confirmed by the standing pre-authorization (accept all recommended options, task directive 2026-09-26).
- assume the Outcome element is a dedicated `## Outcome` section placed as the FIRST section immediately after the header metadata block (before optional Terms and required Assumptions), not a Gist extension; basis: the origin requires "the first thing read", self-containment, and gate enforcement like any other required element, all of which a dedicated section satisfies mechanically while a Gist extension would blur the existing TLDR-line contract; confirmed by the standing pre-authorization.
- assume the origins checker's corpus warn arm gains both migrated-origin consults (disposition section and migration-audit cell) while the plan-mode archive gate gains ONLY the disposition consult, scoped like the corpus arm to origins classified `missing`, per the origin's non-goals sentence ("no change to the plan-mode gate behavior beyond the disposition consult; no registry format change"); confirmed by the standing pre-authorization.
- assume the backfill arm and the execution-serialization gate are worded against "plans open at execution time"; at authoring (main 114e8098, 2026-09-26) the plans root held TWO open plans: the shadow plan (`2026-09-25-docs-branch-shadow-candidate-inclusion-and-completed-corpus-deletion.md`, execution scheduled 08:19 local that day) and this plan itself, which is therefore always a member of the execution-time open set; zero OTHER open plans at execution time is a legitimate outcome (the layer2 plan is already archived at `docs/plans/completed/2026-09-25-layer2-origin-acceptance-rewrite.md`); basis: on-disk survey plus the origin wording.
- assume the local gitignored `.ai-playbook/facts.md` value updates (`plans_dir`, `plans_completed_dir`) are an execution-session action of Task 2 in the run's own worktree, and a completion-side action re-points the PRIMARY checkout's copy after the landing (Ship when); basis: the facts file is machine-local by design (gitignored), and every facts-consuming surface reads the keys dynamically.
- assume historical citations keep their then-current paths: the lessons and guidelines corpora under `projects/.ai-playbook/`, dated supersession-chain prose in `agents/skills/maintenance/SKILL.md`, and hook README provenance citations are immutable history; operative defaults, selftest fixtures, live pointers, and revival instructions all update; basis: history-is-immutable convention plus the inventory-scope statement in Validation Commands.
- assume the corpus `git mv` includes this plan file itself (it is an active plan at the plans root at execution time); Tasks after the move and the completion archive address it under `docs/history/plans/`.
- assume `agents/skills/docs-branch/SKILL.md` edits serialize after the open shadow plan's execution completes (its Tasks 1-5 edit the same file); basis: the queue-order serialization requirement in the history-tree origin plus the on-disk evidence that both plans touch that file.
- assume the docs-branch sync is ADD-ONLY by design: it never treats a missing on-disk file as a deletion, and its restore arm re-materializes branch-tracked paths absent from disk unless they were explicitly deleted in the latest docs commit; basis: the skill's own invariant text, which is why Task 2 pairs the sync with an explicit branch-side deletion.
- assume `scripts/check_maintenance_pins.sh` pin literals that quote maintenance text changed by Task 2 update in the same task, together with the script's citation comments and live sweep root, so the pins suite stays green; basis: the pins are expectations over skill bytes this plan changes.
- assume the dormant neighbor `2026-09-23-rejected-archive-dir-hardcoded-consumers` is NOT triggered by this plan: updating existing hardcoded rejected-archive paths to the moved location is not a sixth consumer; that item stays dormant on its own trigger, and the contradiction neighbor `2026-09-25-completed-archive-fold-then-delete-contradiction` resolves via the open shadow plan's Task 6, not here; the placement-test, assumption-breadcrumb, and archive-policy-r5-lows micros are out of this surface; basis: the group directive's exclusion list.
Decision points requiring a grill: Outcome element shape and placement (dedicated `## Outcome` section first after the header metadata block) - resolved by standing pre-authorization accepting the recommended option, task directive 2026-09-26; affects Plan Format wording and review-plan Step 8; History-tree move scope (full home move to `docs/history/plans/` over archives-only) - resolved by standing pre-authorization plus repo schema evidence (doc-hierarchy migration map, layout gate rule text, execute-plan prose already prescribe the history home), 2026-09-26; affects Task 2; Origins-checker consult semantics (corpus mode gains both consults, plan mode gains the disposition consult only scoped to missing origins, no registry format change) - resolved by standing pre-authorization on the origin's non-goals reading, 2026-09-26; affects Task 4; Backfill and serialization targets worded against plans open at execution time (always including the executing plan itself) - resolved by standing pre-authorization, 2026-09-26; affects Tasks 2 and 3

## Gist & Examples

TLDR: the plans corpus moves its home into the history tree, every plan gains a plain-language Outcome section up top, and plan-closure tooling learns the fold-then-delete disposition, so one simple layout and one readable summary serve readers, reviewers, and the survey machinery alike.

What changes, in three moves. First, the plans skill's template gains a required `## Outcome` section as the first thing a reader sees: one sentence saying what the plan is for, two to four bullets saying what works after execution, written in plain words with no internal codenames. A reader triaging the queue classifies a plan from that section alone; today that same question requires reading Terms, Assumptions, and Tasks (the origin's witness: classifying the docs-branch shadow plan required the whole file). Second, the whole plans home moves from `docs/plans/` to `docs/history/plans/` (active plans at the root, `completed/`/`deferred/`/`rejected/` siblings), matching the backlog tree one floor up; every default path constant, selftest fixture, catalog line, pin, and revival instruction that names the old home moves with it, the registry's path cells re-point, and the layout gate's `docs/plans`-at-root failure no longer applies to this tree. Third, the closure conventions catch up with the fold-then-delete policy the corpus already follows: `check_plan_origins_closed.py` stops warning on migrated origins whose per-item files were deliberately deleted after their dispositions were folded into completed plans and registry audit notes, rule 36's joint count-gate duty widens to folds that REMOVE a count obligation, and the review-plan mirror picks up the rule-36 widening.

Example of the Outcome bar: `## Outcome` for a plans-home move reads "Move the plans corpus under the history tree so plans and backlog follow one archive layout; after execution the layout gate's docs-plans-at-root failure no longer applies to this tree, every path consumer resolves the new home from one facts key, and the docs branch mirrors a single history root." It does not read "P65 Task 2 discharges the plans_dir migration arm per the MLOG ledger" (codenames, task jargon, no positive results).

Example of the migrated-origin consult: the completed plan `2026-09-19-context-budget-and-telemetry-long-running-skills.md` lists the deleted origin `2026-09-18-context-budget-and-telemetry-long-running-skills.md` as a plain-text bullet under `## Disposition of migrated backlog items` (disposition-anchored), and the deleted origin `2026-08-28-summarizer-cli-followups.md` warns today via `2026-09-01-summarizer-publish-lock-hardening.md` and is registry-anchored at ROW scope: its registry row's notes cell carries the `user-approved ...: migration audit` token pair while the row's src cell carries the former item's path; today the corpus scan warns on both; after Task 4 both resolve through their consults. Conversely the origins of `2026-09-25-rearm-form-field-writer-attribution.md` and `2026-09-25-stale-branch-diff-restaging-reverse-squash-guard.md` appear in neither kind of anchor, so their warns legitimately survive: they are the live faces of the genuine-straggler arm the fix must keep.

Example of the rule-36 widening: a fold deletes a sentence an older validation gate counts (a count-1 pin over a phrase the fold removes). Today the joint-duty text triggers only when a fold "adds or moves" a count obligation, so the remaining gate set is never re-simulated and the stale count gate fails deterministically at execution. After Task 4 the duty covers removals: the file's complete remaining count-gate set is re-simulated in the same mechanical-audit pass.

## Evaluation Criteria

**Quality dimensions:**
- correctness: after Task 2 every resolved-path consumer agrees with the moved home; the maintenance pins suite, the runtime-neutrality shared-body gate, the reverse-squash-guard suite, and the origins-checker suite all exit 0; `doc_registry_validator validate` exits 0 with exactly the 21 unregistered-completed-file warns of the landing-day baseline (execution-time correction: never-registered completed plans are out of this path-spellings-only scope; baseline re-pinned 19 to 21 at landing for peer landing 50f225ec); and `docs/maintenance/document-registry.md` carries zero old-home spellings.
- enforceability: a fresh plan authored after Task 1 cannot omit `## Outcome` without a blocking review finding (the review-plan declaration audit checks it like the Driving force line and the Gist opener), and the template text states the plain-globish bar.
- signal hygiene: after Task 4 the corpus warn arm stops warning on consult-anchored migrated origins (the disposition-anchored witness `2026-09-18-context-budget-and-telemetry-long-running-skills.md` and the registry-anchored witness `2026-08-28-summarizer-cli-followups.md`, both measured members of today's warned population, resolve) while origins with no anchor still warn (the two still-warn faces keep firing); the unresolved total drops strictly below the authoring-day pin of 119; the plan-mode gate is unchanged beyond the disposition consult.
- consistency: the post-move inventory of `docs/plans` mentions over the mutable operative surfaces (agents/, scripts/, README.md) contains only the sanctioned-remainder ledger entries, with the immutable-history trees excluded by pathspec.

**Done when:**
- `docs/plans/` is gone from the repo root; `docs/history/plans/` holds the active plans plus `completed/`/`deferred/`/`rejected/`; the archive-policy completed plan resolves at its new path.
- The local facts file resolves `plans_dir` to `docs/history/plans/` and `plans_completed_dir` to `docs/history/plans/completed/`, and a facts-driven consumer (the docs-branch ordering guard) demonstrably follows.
- Every file in Task 2's Files lists carries the new home in its live spans; only the sanctioned-remainder ledger entries retain old-home mentions (frozen citations and legacy teaching), per the pathspec-scoped inventory.
- The docs branch carries `docs/history/plans/` and zero `docs/plans` paths after the sync plus the branch-side deletion.
- The origins checker's new canaries pass: disposition-section resolution, registry migration-audit resolution, genuine-straggler warn retained, plan-mode boundary and positive arm, polarity corners.
- Both rule-36 mirrors say "adds, moves, or removes" and their old triggers are gone.
- The full Validation Commands battery exits 0; the public-hygiene scan exits 0; the plan bytes carry no em dash.

**Ship when:**
- The PRIMARY checkout's gitignored `.ai-playbook/facts.md` values are re-pointed to `docs/history/plans/` and `docs/history/plans/completed/` right after the landing, a facts-driven consumer (the docs-branch ordering guard or the origins checker) demonstrably resolves the new home there, and the docs branch is re-checked to carry `docs/history/plans/` with zero `docs/plans` paths after the primary checkout pulls the landing (a stale-checkout sync in the landing window can transiently re-add the old home; the next sync from a migrated tree self-heals it); until the re-point, primary-checkout consumers resolve the old (absent) home. [class: OPERATIONS_FOLLOW_UP; evidence owner: the landing session; closure condition: the primary facts values updated, one consumer verified, and the branch re-checked]
- Consumer playbook repos pick up the moved home at their next doc-hierarchy migration or fresh bootstrap (the bootstrap templates already teach the history map as canonical; no consumer-repo action is owed by this plan). [class: OPERATIONS_FOLLOW_UP; evidence owner: each consumer repo's own maintenance turn; closure condition: its facts keys re-pointed and its layout gate green]

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Moved corpus (Task 2):**
- `docs/plans/` *(moved wholesale to `docs/history/plans/` by Task 2; findings on moved corpus bytes are in scope at either path; the archive READMEs plus any Task 3 Outcome backfill targets are the only members that gain edits beyond the move)*
- `docs/maintenance/document-registry.md` *(path spellings only: every cell citing a moved plan re-points `docs/plans/` to `docs/history/plans/`, in src cells and audit-cell citations alike; `user-approved` tokens, dates, and all other cell content are frozen; Task 4 may append nothing here)*

**Skill and documentation files:**
- `agents/skills/plans/SKILL.md` (Task 1 Outcome element; Task 4 rule-36 widening; the line-8 legacy-fallback teaching phrase is frozen)
- `agents/skills/review-plan/SKILL.md` (Task 1 Step 8 declaration audit; Task 4 Step 5 amend item 5)
- `agents/skills/maintenance/SKILL.md` (live layout spans only: the facts-key table row, the survey example command, the deferred-README pointers, the never-auto-picked invariant; the dated supersession-chain citations are frozen)
- `agents/skills/maintenance/zcode.md` (the plans-dir default prose and both dated completed-plan citations)
- `agents/skills/maintenance/prompt-templates.md` (historical plan-path citations, mechanical)
- `agents/skills/docs-branch/SKILL.md` (the `_plans_dir_ord` fallback default line only; serialized after the shadow plan's execution)
- `agents/skills/bootstrap-ai-playbook/SKILL.md` (verify-only under Task 2; edit only if the Path Discovery check fails)
- `agents/hooks/skill-gate/README.md` (the gated-class description line)
- `docs/history/plans/deferred/README.md` and `docs/history/plans/rejected/README.md` *(moved by Task 2, then edited: revival targets)*
- `README.md` (the readiness-validator example path)

**Production code (scripts):**
- `scripts/check_plan_origins_closed.py` *(edited: Task 2 default, Task 4 consults)*
- `scripts/check_backlog_claimed.py` (default + docstring contract path)
- `scripts/doc_registry_validator.py` (default, layout prose, selftest fixtures)
- `scripts/reverse_squash_guard.py` (`ARCHIVE_DIRS`)
- `scripts/done_sweep_gates_lib.py` (fallbacks + references)
- `scripts/facts_paths.py` (fallback plans value)
- `scripts/skill_gate.py` (the default-suffix classification arm derives from the `DEFAULT_PLANS_DIR_SUFFIX` constant plus surrounding prose; a behavior change for facts-absent consumer repos on the old layout, whose Arm-2 `docs/plans` classification ends by design)
- `scripts/check_backlog_inbox_location.py` (selftest fixtures)
- `scripts/execute_plan_runtime.py` (selftest fixture literal; all other methods frozen)
- `scripts/docs_branch_plan_guard.py` (one live pointer comment; rest frozen)
- `scripts/plan_readiness.py` (one comment pointer; rest frozen)
- `scripts/check_maintenance_pins.sh` (pin literals over changed text, the FOUR citation comments (lines 77, 105, 778, 1132), the live sweep root, and the line-529 `expect_absent` needle's quoted span retyped to the moved-home spelling; the pin expectations otherwise stay frozen)
- `scripts/validate_review_staging.py` (fixture literals)
- `scripts/harness_detection.py` (docstring provenance line)
- `scripts/rearm_on_touch.py` (docstring plan pointer)

**Tests:**
- `scripts/test_check_plan_origins_closed.py` *(new canaries: Task 2 fixture literal, Task 4 consult canaries)*
- `scripts/test_execute_plan_runtime.py` (fixture literals + the moved-home shared-file set entries; all other tests frozen)
- `scripts/test_done_sweep_gates_lib.py`, `scripts/test_done_sweep_gates_wrapper.py`, `scripts/test_reverse_squash_guard.py`, `scripts/test_rejected_archive_lifecycle.py`, `scripts/test_execute_plan_worktree_bootstrap.py`, `scripts/test_execute_plan_resume_watcher.py`, `scripts/test_parallel_work_regressions.py`, `scripts/test_rearm_on_touch.py`, `scripts/test_migrate_backlog_completed.py`, `scripts/test_check_backlog_claimed.py`, `scripts/test_review_retention.py`, `scripts/test_docs_branch_plan_guard.py` (path-literal fixtures only)
- `docs/history/backlog/2026-09-26-plans-plain-outcome-summary.md`, `docs/history/backlog/2026-09-25-plans-home-into-history-tree.md`, `docs/history/backlog/2026-09-24-plans-rule36-fold-remove-count-obligations.md`, `docs/history/backlog/2026-09-25-teach-origins-checker-fold-then-delete.md` (existing origin witnesses; no task edits them; their completion-time disposition happens at the done boundary, not in a task)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Inventory scope and sanctioned remainder** (stated beside the G2 inventory gate): the zero-unclassified inventory sweeps the mutable operative surfaces only (`git grep` pathspec `agents scripts README.md`). The trees `docs/**` (the moved corpus's frozen bytes, the backlog tree, the registry, feature notes, this plan itself) and `projects/.ai-playbook/**` (guidelines and lessons corpora) are immutable-history surfaces excluded by pathspec, not sanctioned individually. Within the swept roots, only these ledger entries may carry `docs/plans` mentions after Task 2: `agents/skills/doc-hierarchy/SKILL.md`, `agents/skills/doc-hierarchy/migration-map.md`, `agents/skills/doc-hierarchy-migrate/SKILL.md`, `agents/skills/doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh` (legacy teaching, migration fixtures, and the layout gate itself), `agents/skills/how-to-write-skills/SKILL.md` and `agents/skills/rfc-design/SKILL.md` (anti-hardcode teaching lines), `agents/skills/execute-plan/SKILL.md` (legacy-compat teaching prose), `agents/skills/bootstrap-ai-playbook/SKILL.md` (deliberate legacy-layout example plus conflict warning), `agents/skills/plans/SKILL.md` (the line-8 legacy-fallback teaching phrase and the rule-29 mechanical-gates prose at line 536), `agents/skills/maintenance/SKILL.md` (dated supersession-chain citations only), and `agents/hooks/budget-guard/README.md` (provenance citation). Any post-move hit outside this ledger is a defect.

**Out of scope; reject unless plan-related:**
- `agents/skills/doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh` edits; the gate already targets the new layout and runs validation-only here
- `.ai-playbook/facts.md`; gitignored machine-local file (Task 2 updates local worktree values and the post-landing ops duty re-points the primary copy; not a landed or reviewable byte)
- `projects/.ai-playbook/**`; immutable history corpora (the guidelines and lessons corpora; pathspec-excluded from the inventory)
- `docs/tmp/**` scratch (the requirements buffer, the prompts scratch file)
- The five excluded neighbor backlog items named in Assumptions

## Validation Commands

Authoring-time record (updated at the r1 fold): the pre-round readiness invocation, the em-dash scan, and the public-hygiene scan exit clean over the plan bytes before round 1; the full battery was extracted and executed at authoring time with `bash -n` passing and the FIRST failing gate being G1 `missing '## Outcome' in agents/skills/plans/SKILL.md` (exit 1), exactly the pre-execution expectation; no gate passed vacuously before that point. Portability record: the ledger diff originally used a `case` inside a command substitution, which `bash -n` accepts but this host's bash 3.2 fails to parse at run time; it is a plain loop, executed once at authoring against a synthetic two-entry ledger (all-classified passes, a rogue entry is caught) before being pinned here. The battery below is the post-execution form: G1 gates flip green by Task 1, G2 by Task 2, G3 by Task 3, G4/G5 by Task 4. Interim per-task runs scope to the letter blocks named in that task's Run-expect lines (rule 21). Embedding note: the inventory ledger deliberately tolerates the legacy-teaching skill files listed in Review Scope because their `docs/plans` mentions are the sanctioned anti-hardcode teaching text; the plan's own file sits under the pathspec-excluded `docs/**` tree and is never swept.

```bash
#!/usr/bin/env bash
# P65 validation battery. Run from the repository root after the plan's tasks land.
set -u
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }
has() { grep -qF -- "$2" "$1" || fail "missing '$2' in $1"; }
lacks() { local rc=0; grep -qF -- "$2" "$1" || rc=$?; [ "$rc" -eq 0 ] && fail "forbidden '$2' still in $1"; [ "$rc" -eq 1 ] || fail "grep error rc=$rc on $1"; }
PLAN="docs/history/plans/2026-09-26-p65-plans-corpus-history-home-and-outcome-template.md"

# G1: Outcome element in the plans skill and its review mirror (Task 1)
has agents/skills/plans/SKILL.md '## Outcome'
has agents/skills/plans/SKILL.md 'first section immediately after the header metadata block'
has agents/skills/plans/SKILL.md 'two to four result bullets'
has agents/skills/plans/SKILL.md 'Every plan must include an **Outcome section**'
has agents/skills/review-plan/SKILL.md 'required `## Outcome` section'
has agents/skills/review-plan/SKILL.md 'plain-globish result bullets; findings on its absence or jargon density block like any other required element'
python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies 2>&1 | tail -1 | grep -q "OK" || fail "shared-body runtime-neutrality gate went red after the plans/review-plan edits"

# G2: plans home moved, consumers agree (Task 2)
[ ! -d docs/plans ] || fail "docs/plans still at root"
[ -d docs/history/plans ] || fail "docs/history/plans missing"
for d in completed deferred rejected; do [ -d "docs/history/plans/$d" ] || fail "missing docs/history/plans/$d"; done
[ -f docs/history/plans/completed/2026-09-25-backlog-completed-archive-policy.md ] || fail "archive-policy completed plan not at the new home"
has scripts/check_plan_origins_closed.py 'docs/history/plans/completed'
has scripts/check_backlog_claimed.py 'docs/history/plans'
has scripts/doc_registry_validator.py 'docs/history/plans/completed'
has scripts/reverse_squash_guard.py '"docs/history/plans/completed/"'
has scripts/done_sweep_gates_lib.py 'docs/history/plans'
has scripts/facts_paths.py 'docs/history/plans'
has scripts/skill_gate.py 'Path("docs") / "history" / "plans"'
has scripts/check_backlog_inbox_location.py 'docs/history/plans'
has scripts/execute_plan_runtime.py 'docs/history/plans/completed/selftest.md'
has scripts/docs_branch_plan_guard.py 'docs/history/plans/rejected/README.md'
has scripts/plan_readiness.py 'docs/history/plans/rejected/README.md'
has scripts/check_maintenance_pins.sh 'docs/history/plans'
has scripts/validate_review_staging.py 'docs/history/plans/sample-plan.md'
has scripts/harness_detection.py 'docs/history/plans/2026-09-18-harness-detection-and-budgeting-skip.md'
has scripts/rearm_on_touch.py 'docs/history/plans/2026-09-20-harness-triage-paperkeeping-dismantling-wall-clock.md'
has agents/skills/maintenance/SKILL.md '`docs/history/plans/`'
has agents/skills/maintenance/SKILL.md 'find docs/history/plans -maxdepth 1'
has agents/skills/maintenance/SKILL.md '`docs/history/plans/deferred/` plans are never auto-picked'
has agents/skills/maintenance/SKILL.md 'docs/history/plans/deferred/README.md'
has agents/skills/maintenance/zcode.md 'default `docs/history/plans/`'
has agents/skills/maintenance/prompt-templates.md 'docs/history/plans/'
has agents/skills/docs-branch/SKILL.md '_plans_dir_ord="docs/history/plans"'
has agents/hooks/skill-gate/README.md 'docs/history/plans/'
has README.md 'docs/history/plans/<plan>.md'
has docs/history/plans/deferred/README.md 'back to `docs/history/plans/`'
has docs/history/plans/rejected/README.md 'under `docs/history/plans/`'
for f in scripts/check_plan_origins_closed.py scripts/check_backlog_claimed.py scripts/doc_registry_validator.py scripts/reverse_squash_guard.py scripts/done_sweep_gates_lib.py scripts/facts_paths.py scripts/skill_gate.py scripts/check_backlog_inbox_location.py scripts/execute_plan_runtime.py scripts/docs_branch_plan_guard.py scripts/plan_readiness.py scripts/check_maintenance_pins.sh scripts/validate_review_staging.py scripts/harness_detection.py scripts/rearm_on_touch.py scripts/test_check_plan_origins_closed.py scripts/test_execute_plan_runtime.py scripts/test_done_sweep_gates_lib.py scripts/test_done_sweep_gates_wrapper.py scripts/test_reverse_squash_guard.py scripts/test_rejected_archive_lifecycle.py scripts/test_execute_plan_worktree_bootstrap.py scripts/test_execute_plan_resume_watcher.py scripts/test_parallel_work_regressions.py scripts/test_rearm_on_touch.py scripts/test_migrate_backlog_completed.py scripts/test_check_backlog_claimed.py scripts/test_review_retention.py scripts/test_docs_branch_plan_guard.py agents/skills/maintenance/zcode.md agents/skills/maintenance/prompt-templates.md agents/hooks/skill-gate/README.md README.md docs/history/plans/deferred/README.md docs/history/plans/rejected/README.md docs/maintenance/document-registry.md; do lacks "$f" 'docs/plans'; done
# Inventory over the MUTABLE operative surfaces only; docs/** and projects/.ai-playbook/** are
# immutable-history surfaces excluded by pathspec (Review Scope states this beside the gate).
LEDGER="agents/skills/doc-hierarchy/SKILL.md agents/skills/doc-hierarchy/migration-map.md agents/skills/doc-hierarchy-migrate/SKILL.md agents/skills/doc-hierarchy-migrate/scripts/verify-doc-hierarchy.sh agents/skills/how-to-write-skills/SKILL.md agents/skills/rfc-design/SKILL.md agents/skills/bootstrap-ai-playbook/SKILL.md agents/skills/execute-plan/SKILL.md agents/skills/plans/SKILL.md agents/skills/maintenance/SKILL.md agents/hooks/budget-guard/README.md"
hits="$(git grep -l 'docs/plans' -- agents scripts README.md || true)"
remainder=""
for f in $hits; do
  case " $LEDGER " in
    *" $f "*) ;;
    *) remainder="$remainder $f" ;;
  esac
done
[ -z "$remainder" ] || fail "unclassified docs/plans mentions outside the sanctioned ledger:$remainder"
test "$(grep -cF 'docs/history/plans/deferred/README.md' agents/skills/maintenance/SKILL.md)" -eq 2 || fail "maintenance/SKILL.md deferred-README pointers: expected both re-pointed (count 2)"
test "$(grep -c 'docs/plans' agents/skills/plans/SKILL.md)" -eq 2 || fail "plans/SKILL.md sanctioned literal count drifted (expected exactly 2: line-8 legacy phrase + rule-29 prose)"
grep -qF 'plans_dir = "docs/history/plans/"' .ai-playbook/facts.md || fail "local facts plans_dir not re-pointed (machine-local action of Task 2)"
grep -qF 'plans_completed_dir = "docs/history/plans/completed/"' .ai-playbook/facts.md || fail "local facts plans_completed_dir not re-pointed"
python3 -c "import sys; sys.path.insert(0, 'scripts'); import skill_gate as sg; assert sg._plans_path_matcher('/r/docs/history/plans/p.md', None), 'default suffix must classify the new home'; assert not sg._plans_path_matcher('/r/docs/plans/p.md', None), 'old home must no longer classify by default'" || fail "skill-gate default-suffix behavioral probe failed"
regout="$(python3 scripts/doc_registry_validator.py validate 2>&1)"; regrc=$?; [ "$regrc" -eq 0 ] || fail "doc_registry_validator validate exited $regrc"
# Execution-time correction: this plan's registry edits are path spellings only, so
# never-registered completed plans (19 warns at the pre-move baseline on main 0ba83acd)
# stay out of scope; the gate asserts equality with the landing-day baseline, re-pinned
# from 19 to 21 at landing 2026-09-26 because peer landing 50f225ec archived further
# unregistered completed plans (out of this plan's scope either way).
unreg="$(echo "$regout" | grep -c 'unregistered completed-history file: docs/history/plans/completed')"
[ "$unreg" -eq 21 ] || fail "unregistered completed warn count drifted from the landing-day baseline 21 (got $unreg)"
bash scripts/check_maintenance_pins.sh || fail "maintenance pins suite red after the maintenance text edits"
DB="${DOCS_BRANCH:-docs}"; git rev-parse --verify -q "refs/heads/$DB" >/dev/null || fail "docs branch $DB missing; run the Task 2 docs-branch sync and branch-side deletion first"
[ -z "$(git ls-tree -r --name-only "refs/heads/$DB" -- docs/plans)" ] || fail "docs branch still carries docs/plans (run the Task 2 branch-side deletion)"
git ls-tree -r --name-only "refs/heads/$DB" -- docs/history/plans | grep -q . || fail "docs branch missing docs/history/plans"

# G3: every open plan at the new home carries a real Outcome section (Task 3; zero OTHER open plans is a valid outcome, the task records the enumeration)
n=0; for p in docs/history/plans/*.md; do [ -f "$p" ] || continue; n=$((n+1)); grep -q '^## Outcome' "$p" || fail "open plan missing ## Outcome: $p"; done; echo "G3: $n open plan(s) checked (the executing plan satisfies this via its own r1-folded Outcome section; a grep may also match an embedded template fence, so the honest evidence is the executed backfill edits)"

# G4: origins checker consults + rule-36 widening (Task 4)
python3 scripts/test_check_plan_origins_closed.py || fail "origins-checker suite red (new consult canaries)"
has agents/skills/plans/SKILL.md 'adds, moves, or removes a count obligation'
lacks agents/skills/plans/SKILL.md 'adds or moves a count obligation'
has agents/skills/review-plan/SKILL.md 'adds, moves, or removes a count obligation'
lacks agents/skills/review-plan/SKILL.md 'adds or moves a count obligation'
has scripts/check_plan_origins_closed.py 'Disposition of migrated backlog items'
has scripts/check_plan_origins_closed.py 'migration audit'

# G5: corpus-scan witness + repo-wide gates (after Task 4)
out="$(python3 scripts/check_plan_origins_closed.py 2>&1)"
[ -n "$out" ] || fail "corpus scan produced no output"
if echo "$out" | grep -q 'origin 2026-08-28-summarizer-cli-followups.md unresolved'; then fail "registry-anchored witness still warns: summarizer-cli-followups"; fi
if echo "$out" | grep -q 'origin 2026-09-18-context-budget-and-telemetry-long-running-skills.md unresolved'; then fail "disposition-anchored witness still warns: context-budget-and-telemetry-long-running-skills"; fi
if ! echo "$out" | grep -q 'origin 2026-09-25-rearm-form-field-writer-attribution.md unresolved'; then fail "genuine-straggler face stopped warning (warn arm over-suppresses): rearm-form-field-writer-attribution"; fi
if ! echo "$out" | grep -q 'origin 2026-09-25-stale-branch-diff-restaging-reverse-squash-guard.md unresolved'; then fail "genuine-straggler face stopped warning (warn arm over-suppresses): stale-branch-diff-restaging-reverse-squash-guard"; fi
total="$(echo "$out" | sed -nE 's/.*corpus scan: [0-9]+ archived plan\(s\), ([0-9]+) unresolved origin.*/\1/p' | tail -1)"
[ -n "$total" ] || fail "could not parse the corpus scan unresolved total"
[ "$total" -lt 119 ] || fail "migrated-origin warns did not drop (total=$total; pin 119 measured at main 114e8098, 2026-09-26; re-pin through a plan correction, never edit this gate to chase the count)"
bash scripts/check-no-em-dash.sh file "$PLAN" || fail "em dash in the plan bytes"
bash scripts/scan-public-hygiene.sh || fail "public-hygiene scan red"
# Pre-round readiness passed pre-archive ("readiness PRE-ROUND OK" over the open plan
# bytes before the done-boundary archive move); it is not re-runnable against the
# completed-path archive (the sidecar digest binds the open-plan bytes), so it is
# retired from the post-archive form of this battery.
echo "pre-round readiness: passed pre-archive (see execution record)"
echo "P65 battery: all gates green"
```

### Task 1: Outcome template element in the plans skill and its review-gate mirror

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [x] In `agents/skills/plans/SKILL.md` Plan Format, add the required `## Outcome` section to the template between the metadata block and the optional `## Terms` heading, with this exact body shape and the placement rule as prose under it [class: IMPLEMENTATION_REQUIRED]

```markdown
## Outcome

<One plain sentence: the aim of this plan.>

- <Positive result of executing it: what works after that breaks or is missing today.>
- <Positive result.>
- <Optional positive result.>
```

- [x] In the same skill, add to the required-elements prose: "Every plan must include an **Outcome section** (`## Outcome`) as the first section immediately after the header metadata block: one plain-globish aim sentence plus two to four result bullets stating what works after execution; the summary is self-contained (understandable without Terms or Tasks), uses no internal codenames or task jargon, and is specific enough to classify the plan (what breaks today, what works after); the plans review flags its absence like any other required element." Keep the new text free of `docs/plans` literals [class: IMPLEMENTATION_REQUIRED]
- [x] In `agents/skills/review-plan/SKILL.md` Step 8 (Declaration audit), extend the audited declarations with: "and the required `## Outcome` section (first section after the header metadata block; one aim sentence plus two to four plain-globish result bullets; findings on its absence or jargon density block like any other required element)" [class: IMPLEMENTATION_REQUIRED]
- [x] `OutcomeSection#template_gate`; given the edited plans SKILL.md, expects the G1 greps of the Validation battery to pass (the exact-prescribed fragments found in the two skill files) [class: REPOSITORY_TEST]
- [x] `SharedSkillBodies#runtime_neutral`; given the edited skill bodies, expects `python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies` to stay green (the shared-body forbidden-term gate over the prescribed insertions) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the G1 block of the Validation battery (the other letter blocks stay red or unrun at this task point; scope the interim run to G1) [class: REPOSITORY_TEST]
- [x] Commit: `plans: require a plain-globish Outcome section as every plan's first section` [class: IMPLEMENTATION_REQUIRED]

### Task 2: plans home move into the history tree with the full consumer sweep

Files:
- `docs/history/plans/` (the corpus: this plan itself, `completed/` 155 files, `deferred/`, `rejected/`) *(moved here from `docs/plans/` by this task; the pre-move spelling is kept in the task prose as history)*
- `docs/maintenance/document-registry.md` (path spellings only)
- `scripts/check_plan_origins_closed.py`, `scripts/check_backlog_claimed.py`, `scripts/doc_registry_validator.py`, `scripts/reverse_squash_guard.py`, `scripts/done_sweep_gates_lib.py`, `scripts/facts_paths.py`, `scripts/skill_gate.py`, `scripts/check_backlog_inbox_location.py`, `scripts/execute_plan_runtime.py`, `scripts/docs_branch_plan_guard.py`, `scripts/plan_readiness.py`, `scripts/check_maintenance_pins.sh`, `scripts/validate_review_staging.py`, `scripts/harness_detection.py`, `scripts/rearm_on_touch.py`
- the fourteen test files named in Review Scope
- `agents/skills/maintenance/SKILL.md`, `agents/skills/maintenance/zcode.md`, `agents/skills/maintenance/prompt-templates.md`, `agents/skills/docs-branch/SKILL.md`, `agents/hooks/skill-gate/README.md`, `README.md`, `docs/history/plans/deferred/README.md`, `docs/history/plans/rejected/README.md`
- `.ai-playbook/facts.md` (local, gitignored: value update only, never committed)

- [x] Serialization pre-gate: resolve the PRIMARY checkout explicitly (the first `worktree` entry of `git worktree list --porcelain`) and check BOTH documented claim surfaces there: `docs/tmp/authoring-claims/*.md` (the authoring-claim files with `session:`/`item:`/`created:`/`updated:` frontmatter) and the execution-claims root `docs/tmp/execution-claims/` the execute-plan claim protocol documents; EXCLUDE the executing run's own claim (a claim whose `plan:` or `item:` resolves to this plan - its presence witnesses this run, not a concurrent one); if any OTHER claim's plan resolves under the plans home and its `updated:` is within one cadence period (a stale claim occupies nothing per the claim protocol), defer this task until that run lands, then proceed [class: IMPLEMENTATION_REQUIRED]
- [x] Move guard: before `git mv`, check the run manifest for a pending `resume_watcher` receipt whose `plan_path` sits under the old home; if one exists, stand it down or re-record it against the new path first (the receipt pins the plan path at schedule time and the pre-archive gate refuses on a mismatch); record the receipt's verified absence as this step's evidence when none is pending [class: IMPLEMENTATION_REQUIRED]
- [x] `git mv docs/plans docs/history/plans` (the whole home: active plans including this plan, `completed/`, `deferred/`, `rejected/`), then update the local gitignored `.ai-playbook/facts.md` values to `plans_dir = "docs/history/plans/"` and `plans_completed_dir = "docs/history/plans/completed/"` [class: IMPLEMENTATION_REQUIRED]
- [x] Re-point every old-home path spelling in `docs/maintenance/document-registry.md`: src cells and audit-cell citations alike change `docs/plans/` to `docs/history/plans/`; `user-approved` tokens, dates, and all other cell content stay byte-identical (a rename-follow, not a semantic row change) [class: IMPLEMENTATION_REQUIRED]
- [x] Update every script default, selftest fixture, and live pointer in the Production-code Files list to the moved home exactly as the G2 `has` gates pin them; in `scripts/skill_gate.py` the edit is NOT the constant alone (the constant is dead code: `_under_default_plans_suffix` hardcodes the ancestor name pair `plans` under `docs` and never reads it): rewrite the default-suffix arm to derive from `DEFAULT_PLANS_DIR_SUFFIX` by walking the target's ancestors and comparing the suffix parts tuple, preserving the docstring-pinned global-breadth and anti-evasion semantics, and update the surrounding prose; in operative code files, historical docstring citations update to the archive path too (uniform rule: scripts carry zero `docs/plans` mentions after this task) [class: IMPLEMENTATION_REQUIRED]
- [x] Update the fourteen test files' path-literal fixtures to the moved home, including the origins-checker test's facts-body fixture literal (frozen tests keep their logic; only path literals change) [class: IMPLEMENTATION_REQUIRED]
- [x] Update the skill and catalog surfaces: the maintenance facts-table row default, the survey example command, the deferred-README pointers, and the never-auto-picked invariant in `maintenance/SKILL.md`; all four `zcode.md` occurrences across three lines (the plans-dir default prose plus the dated completed-plan citations; line 60 carries two); all sixteen `docs/plans` occurrences in `prompt-templates.md` (fifteen lines); the `_plans_dir_ord` fallback in `docs-branch/SKILL.md`; the gated-class line in the skill-gate README; the readiness-validator example in `README.md`; the revival targets and arrival sentence in the two archive READMEs (all mentions; edited at their new paths after the move); update the pins script's pin literals over changed text, its FOUR citation comments (lines 77, 105, 778, 1132), and its live sweep root, and retype the line-529 `expect_absent` needle's quoted span to the moved-home spelling (it asserts absence of superseded wording, which holds under either spelling, so the pin stays green and meaningful; the pin expectations otherwise stay frozen) [class: IMPLEMENTATION_REQUIRED]
- [x] Verify `agents/skills/bootstrap-ai-playbook/SKILL.md` already teaches the history map as the greenfield canonical (record the Path Discovery evidence in the execution log); edit it only if the check fails [class: REPOSITORY_TEST]
- [x] Run the docs-branch skill's sync FROM THE EXECUTION WORKTREE (the moved tree; the skill's own ad-hoc-worktree rule names the main checkout, which still has the old layout and would fail the branch gates - this task's checkout choice overrides it deliberately), so the branch mirrors the moved tree (the skill's rogue-dir arm removes the non-canonical `docs/plans/` root from the branch when the syncing tree lacks it); THEN make the branch state deterministic with a conditional branch-side deletion: open the docs branch in a throwaway worktree (`git worktree add "<dir>" docs`, branch mode, fail-closed on an existing holder; on refusal run the skill's leaked-holder remedy `git worktree prune` and retry once), and ONLY if `git ls-tree -r --name-only refs/heads/docs -- docs/plans | grep -q .` run `git rm -r --ignore-unmatch docs/plans` and commit on the docs branch; `git worktree remove` the throwaway; expectation note: the zero-old-paths branch state is not durable across the landing window (a sync from any stale-disk checkout re-adds it until that checkout pulls the landing; the rogue-dir arm self-heals it at the first post-pull sync), so the post-landing ops duty re-checks it [class: IMPLEMENTATION_REQUIRED]
- [x] `ReverseSquashGuard#archive_dirs`; given the edited `ARCHIVE_DIRS`, expects `python3 scripts/test_reverse_squash_guard.py` green over the moved archive paths [class: REPOSITORY_TEST]
- [x] `MaintenancePins#suite`; given the edited maintenance text and pin literals, expects `bash scripts/check_maintenance_pins.sh` exit 0 [class: REPOSITORY_TEST]
- [x] `Registry#validate`; given the moved corpus and re-pointed registry, expects `python3 scripts/doc_registry_validator.py validate` exit 0 with exactly the 21-warn landing-day unregistered baseline (never-registered completed plans are out of scope; re-pinned at landing) [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the G2 block of the Validation battery (G1 already green; G3/G4/G5 not yet runnable at this task point) [class: REPOSITORY_TEST]
- [x] Commit: `plans: move the plans home into the history tree and re-point every consumer` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Outcome backfill for plans still open at execution time

Files:
- every open top-level plan under the resolved plans home at execution time, EXCLUDING the plan under execution *(other open plans may be zero)*

- [x] Enumerate the open top-level plans under `docs/history/plans/` (post-Task-2 home) at execution time, excluding this executing plan (its own Outcome obligation discharged by its r1-folded section and this plan's certification); if the enumeration is empty, record the empty listing as this task's completion evidence and skip the commit step [class: IMPLEMENTATION_REQUIRED]
- [x] For each enumerated open plan, add a real `## Outcome` section per the Task 1 template: one plain-globish aim sentence, two to four result bullets, self-contained, no codenames or task jargon, placed as the first section after the metadata block; the addition is a plan correction the owning loop's next review round re-certifies (a post-round edit fails the digest binding until that re-certification), so record in the execution log which enumerated plans sit between review rounds and note their next-round re-certification duty; note that G3's grep can also match an embedded template fence, so the honest evidence is these executed edits [class: IMPLEMENTATION_REQUIRED]
- [x] `OpenPlans#outcome_present`; given the post-backfill tree, expects the G3 loop of the Validation battery to pass with the checked count printed [class: REPOSITORY_TEST]
- [x] Run → expect GREEN: the G3 block (G1+G2 stay green) [class: REPOSITORY_TEST]
- [x] Commit (only when at least one plan was edited): `plans: backfill Outcome sections into the open plans remaining at execution time` [class: IMPLEMENTATION_REQUIRED]

### Task 4: origins-checker fold-then-delete consults and the rule-36 removal widening

Files:
- `scripts/check_plan_origins_closed.py`
- `scripts/test_check_plan_origins_closed.py`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [x] Extend the corpus warn arm with the disposition consult: when an origin classifies as `missing`, read the archived plan text's `## Disposition of migrated backlog items` section (case-insensitive heading match, styled like the existing dispositions-heading regex) and suppress the warn when the section body names the origin's basename via a boundary-anchored exact match over the `.md` path tokens it contains, regardless of backtick quoting (the corpus's 92 disposition sections carry 318 plain-text bullets and zero backtick-quoted origin spans; 82 of today's 108 distinct warned basenames are disposition-anchored); keep the existing `## Origins dispositions` undercount consult untouched (its backtick style has zero corpus instances and is not a precedent); if the plan text is unreadable, the consult is inert and the warn stays [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the corpus warn arm with the registry consult: when the origin classifies as `missing`, resolve `doc_registry_rel` from the repo facts (conventional default `docs/maintenance/document-registry.md`, same resolution style as the other dirs) and suppress the warn when one ROW jointly carries the anchor: the row's notes cell carries the `user-approved` token AND the `migration audit` marker, AND a boundary-anchored exact match on the origin's basename holds anywhere in that row (all cells, the src cell included - the corpus precedent rows keep the basename in the src cell; a `prefix-<basename>` cell does not resolve); if the registry is missing or unreadable, the consult is inert (warn retained, the corpus arm still exits 0, no exception escapes); no registry format change [class: IMPLEMENTATION_REQUIRED]
- [x] Leave the plan-mode archive gate's classification unchanged except for the disposition consult scoped like the corpus arm to origins classified `missing` (an origin listed in the plan's own disposition section passes; a registry-only origin still stragglers plan mode; a still-open origin named in a disposition section still stragglers); keep the genuinely-unresolved warn arm; landing note: verify the shadow plan's Task 6 wrote its six reconciled origins' audit cells WITH the `migration audit` marker, and if any landed without it, marker compliance is a recorded follow-up before the consult can resolve them [class: IMPLEMENTATION_REQUIRED]
- [x] `PlanOriginsClosedTest#test_corpus_scan_resolves_disposition_section_origin`; given an archived plan whose `## Disposition of migrated backlog items` section carries a plain-text bullet naming a deleted origin basename (fixture shape derived from the real bullets in `docs/history/plans/completed/2026-09-19-context-budget-and-telemetry-long-running-skills.md`) and no file exists under the backlog dir, expects the corpus scan emits no warning for that origin and exits 0 [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_corpus_scan_resolves_registry_migration_audit_origin`; given a registry row whose notes cell carries `user-approved` and `migration audit` and whose src cell carries the deleted origin basename (fixture shape derived from the real row `2026-08-28-summarizer-cli-followups.md` at `docs/maintenance/document-registry.md` row 120), expects the corpus scan emits no warning for that origin [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_registry_consult_row_scoped`; given a registry whose row A notes cell carries `user-approved` and `migration audit` while the deleted origin's basename appears only in row B's src cell, expects the warning stays (the anchor is row-joint, not registry-joint) [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_corpus_scan_still_warns_genuinely_unresolved_origin`; given an archived plan quoting a deleted origin named in neither a disposition section nor a migration-audit cell, expects the warning fires and the scan still exits 0 [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_plan_mode_disposition_section_origin_passes`; given plan mode over a plan whose deleted origin is named in the plan's own disposition section, expects `ok (1/1 origins closed)` and exit 0 (red today; fails if the consult is wired corpus-only) [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_plan_mode_registry_only_origin_still_stragglers`; given plan mode over a plan whose deleted origin is covered only by a registry audit cell and not by the plan's own disposition section, expects the straggler report and exit 1 [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_plan_mode_open_origin_named_in_disposition_still_stragglers`; given plan mode over a plan whose disposition section names an origin that still sits OPEN at the backlog top level, expects the straggler report (the disposition consult never rescues a live origin) [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_registry_consult_requires_token_and_basename`; given an audit cell naming the basename without the `migration audit` token, expects the warning stays [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_corpus_scan_open_origin_in_audit_cell_still_warns`; given an OPEN top-level backlog item whose basename appears in a `user-approved ... migration audit` registry cell, expects the corpus scan still warns for it and exits 0 (the consults never rescue a live origin) [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_corpus_scan_open_origin_in_disposition_section_still_warns`; given an OPEN top-level backlog item whose basename a completed plan names in its `## Disposition of migrated backlog items` section, expects the corpus scan still warns for it and exits 0 (the disposition consult never rescues a live origin in corpus mode either) [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_prefix_basename_near_miss_does_not_resolve`; given a disposition bullet or audit cell naming only `prefix-<basename>` for a deleted `<basename>`, expects the warning stays (boundary-anchored matching) [class: REPOSITORY_TEST]
- [x] `PlanOriginsClosedTest#test_missing_registry_leaves_consult_inert`; given the corpus scan with the registry file absent, expects no exception, the migrated-origin warns unchanged, and exit 0 [class: REPOSITORY_TEST]
- [x] Widen the rule-36 joint duty in `agents/skills/plans/SKILL.md` (the final sentence of Validation Commands rule 36): "a fold that adds or moves a count obligation on a file" becomes "a fold that adds, moves, or removes a count obligation on a file", with the re-simulation object reworded to "the file's complete remaining count-gate set" so a removal re-simulates what survives in the same mechanical-audit pass, the parenthetical generalized to "(the gates that survive the fold, plus any new one)", and the temp-copy tail neutralized to carry insertions or removals; prescribe the same tail change for the review-plan Step 5 item 5 sentence; keep the witness prose [class: IMPLEMENTATION_REQUIRED]
- [x] Mirror the same widening in `agents/skills/review-plan/SKILL.md` Step 5 amend item 5 (the parenthetical already cites plans Validation Commands rule 36) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the G4 block, then the G5 witness block (consult-anchored witnesses resolved, both still-warn faces firing, the unresolved total strictly below the pinned 119) [class: REPOSITORY_TEST]
- [x] Commit: `plans: teach the origins checker the fold-then-delete disposition` [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `plans: widen rule 36 to count-obligation removals` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-09-26-plans-plain-outcome-summary.md`: implemented by Task 1 (required Outcome section in the plans skill and its review mirror) and Task 3 (backfill into the open plans at execution time); per-item file deleted at the done boundary.
- `docs/history/backlog/2026-09-25-plans-home-into-history-tree.md`: implemented by Task 2 (full plans-home move into the history tree with the consumer sweep); per-item file deleted at the done boundary.
- `docs/history/backlog/2026-09-24-plans-rule36-fold-remove-count-obligations.md`: implemented by Task 4 (rule 36 widened to count-obligation removals in both mirrors); per-item file deleted at the done boundary.
- `docs/history/backlog/2026-09-25-teach-origins-checker-fold-then-delete.md`: implemented by Task 4 (disposition-section and registry migration-audit consults in the origins checker); per-item file deleted at the done boundary.
