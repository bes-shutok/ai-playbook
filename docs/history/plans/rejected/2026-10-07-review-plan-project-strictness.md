# Plan: review-plan project strictness from user facts

Backlog origin: docs/history/backlog/2026-10-07-review-plan-project-strictness-from-user-facts.md
Driving force: code-quality
Plan review record: the staging series docs/history/reviews/2026-10-07-plan-review-review-plan-project-strictness-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1.0h
Execution dependency: docs/history/plans/2026-10-07-plan-detail-boundary.md (landing; shared-file seam rule: that plan's Task 2 queues edits to agents/skills/review-plan/SKILL.md and agents/skills/plans/SKILL.md, files this plan also edits, so this plan's execution waits on that landed branch through the parked-dependency machinery)
Authoring claim: docs/tmp/authoring-claims/2026-10-07-review-plan-project-strictness-from-user-facts.md (session sess_72b1f155-dee1-439a-916f-fcc26d801c74)

## Terms

- strictness class: the review-loop policy class a repository resolves to; the closed set `personal`, `company`, `standard`, `unresolved`.
- user facts document: the user-level facts file configured as `user_facts_path` (typically `~/.ai-playbook/facts.md`), holding the markdown table rows `personal_projects_root` and `company_projects_root`; never a tracked file.
- owning checkout: the primary checkout a linked worktree shares its git object store with; resolved from the git common dir (the toplevel itself when the common dir lies inside the toplevel, otherwise the common dir's parent when that parent is itself a checkout root, otherwise the toplevel when the toplevel is not itself a linked worktree, where the toplevel is a linked worktree exactly when its .git file's gitdir target sits under the common dir's worktrees directory and a separate-git-dir primary's .git file points at the common dir itself and is therefore not a linked worktree; a linked-worktree toplevel whose owning checkout cannot be resolved returns the unresolved owning-checkout arm).
- resolver: `resolve_project_class(start_dir, user_facts)`, the new `scripts/facts_paths.py` function; the mechanical procedure of record for class resolution.
- unresolved: the visible outcome when the user facts roots or the owning checkout cannot be resolved, or the checkout lies inside both roots; carries a closed-vocabulary reason and is never silently mapped to `standard`.
- component-wise containment: realpath containment compared per path segment, never a raw string prefix, inclusive of the equal path.
- Design Invariant 11: the `scripts/facts_paths.py` module rule that facts-driven resolution imports the single entry point instead of re-parsing facts formats.
- cap-closure terminal shape: the operator-authorized loop closure at the configured round cap recorded through the sidecar's `extensions.cap_closure` declaration (review-plan, Iteration Discipline rule 8).
- PLAN-PROMPTS: the tracked rolling log of ready-to-dispatch plan-creation prompts under the backlog directory; this plan's dispatch entry lives there.
- round record: the staged review record (markdown plus sidecar) a review round writes; the unresolved class condition records in its Metadata block.
- fence-class: the backlog triage class for guards against a witnessed failure class; fence-class arms may add checks only when the origin cites its completed failure.
- project facts: the repository-local facts document at `.ai-playbook/facts.md`, whose keys never feed class resolution; the confusable twin of the user facts document.

## Why

The strictness resolver reads `personal_projects_root` from project-local facts and silently maps every miss to `standard`. The authoritative workspace roots live in the user facts document, and a linked worktree's temporary path can sit outside them while its owning checkout sits inside. This repository was witnessed resolving to the wrong class on 2026-10-07, which changes review round limits and triage policy.

## Outcome

Review-plan strictness classes resolve from the user facts workspace roots and the owning repository checkout, so every repository and linked worktree applies the review policy its configuration actually declares.

- A linked worktree classifies by its owning checkout, never its temporary path.
- A company workspace resolves `company` visibly and keeps the standard round budgets.
- Facts or repository identity that cannot be resolved return visible `unresolved` with a reason, never a silent `standard`.

Gate delta: adds twenty-one selftest arms in `scripts/facts_paths.py`, seven pins rows in `scripts/check_maintenance_pins.sh` (six presence and one absence), and the suite header invariant list line (each grown check prices itself by the reworded contract sentence it guards); adds the `class` subcommand on the `facts_paths` CLI as the invocation surface for the procedure of record; widens the class set from two to four values in the review-plan contract prose; adds no refusal class, hard gate, fence, protocol layer, or schema state field. The origin is fence-class with its completed failure cited in the origin body (the 2026-10-07 wrong-class conclusion for this repository), which prices the additions.

## Assumptions

- assume company-class projects retain the standard round budgets and the cap-closure terminal shape, with no new company cap; basis: the dispatch prompt's explicit direction "do not introduce a new company cap by assumption" (PLAN-PROMPTS entry review-plan-project-strictness, 2026-10-07) and no witnessed company-cap failure.
- assume an `unresolved` resolution runs the standard branch's budgets with the condition recorded in the round record, and keeps the cap-closure terminal shape unavailable like `personal`; basis: the origin's Expected text ("report that condition rather than silently treating it as standard") requires visibility, not different budgets, and no evidence supports tightening on unresolvable configuration; the cap-closure withholding is the r1 fold of review finding F10 (withholding the operator-gated terminal shape on an unresolved class closes the bypass where a genuinely personal repo transiently resolves unresolved, without changing any budget).
- assume the resolver lives in `scripts/facts_paths.py` beside `resolve_projects_roots` and reuses it, honoring Design Invariant 11; basis: the module's single-entry-point docstring and the dispatch prompt's reuse direction.
- assume execute-plan (review-budgets paragraph) and receiving-review (ordinary-findings advisory) need no edits: both render only the personal package or a class-agnostic referral and remain accurate under the widened class set; basis: read of both spans at authoring time.
- assume the personal-only cap-closure renderings in review-plan Iteration Discipline rule 8 and the execute-plan review-budgets paragraph are known mirrors to be carried by a later plan; basis: both spans are frozen or out of scope for this plan (the r3 fold of review finding F4), and the authoritative withholding lives in the Project strictness classes section this plan amends; the mirror carries and the deferred Low residuals land as the follow-up backlog row this plan's landing rider files (the r5 record's deferred residual roster is the roster of record).

Decision points requiring a grill: company-class round-limit mapping: no new company cap, company retains standard budgets (source: PLAN-PROMPTS entry review-plan-project-strictness Prompt, 2026-10-07, Project strictness classes); unresolved mapping: visible-unresolved with standard budgets (source: backlog row Expected section, 2026-10-07, Assumptions).

## Standing constraints

- Configured root values and machine-specific paths never enter tracked files; every fixture builds its own temp tree and tears it down.
- Shared-body gate: the prescribed insertion into `agents/skills/plans/SKILL.md` must pass `test_shared_skill_bodies_remain_runtime_neutral`; its text was swept against the forbidden-term tuple at authoring time and is clean.
- Frozen regions: `agents/skills/review-plan/SKILL.md` outside the Project strictness classes section is frozen; `agents/skills/plans/SKILL.md` outside the rule 16 class sentences is frozen; both files' remaining regions, including the plan-detail regions (behavior-decision prose, Gist placement guidance, review closure inventory audit, paired review-policy examples) owned by the execution-dependency plan, are frozen; reject any finding touching them. Both this plan and the execution-dependency plan add rows to `scripts/check_maintenance_pins.sh`; its rows are append-only across the two plans, never overlapping edits to the same lines.

## Gist & Examples

TLDR: strictness classes resolve from user facts and the owning checkout, so the right review policy applies, fixing the witnessed wrong-class fallback.

Before (today): the reviewer session for this repository read `personal_projects_root` from the project facts document, found the key absent (project facts never carry it), and silently concluded `standard`; the personal round budgets and the personal cap-closure exclusion never applied. The same read classifies a linked worktree by its temporary path, so a worktree created outside the workspace root misclassifies even when the primary checkout sits inside it.

After (this plan): the reviewer session invokes `resolve_project_class(start_dir, user_facts)`. A linked worktree `/tmp/wt-abc` whose owning checkout is `~/Projects/myrepos/ai-playbook` under the configured personal root resolves `personal`; a checkout under the company root resolves `company` and keeps the standard budgets with the cap-closure terminal shape available; a checkout outside both roots resolves `standard`; a missing or malformed user facts document resolves `unresolved` with reason `user-facts-unresolvable`, recorded in the round record, still running the standard budgets. Project-local facts are never consulted for class resolution.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every resolver mapping arm is proven by an executed selftest assertion (twenty-one arms, real temp git repos and worktrees).
- reliability: unresolvable states return the visible `unresolved` class with a closed-vocabulary reason, never silent `standard`.
- maintainability: class resolution keeps one owner (review-plan prose + one resolver); consumer text refers, never re-resolves.

**Done when:**
- `python3 scripts/facts_paths.py --selftest` exits 0 with all new arms passing.
- `bash scripts/check_maintenance_pins.sh` exits 0 with the seven new rows present.
- `python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies` exits 0 (plans SKILL.md insertion clean).
- `bash scripts/check-no-em-dash.sh added-lines --base main` exits 0.
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` exits 0.
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-07-review-plan-project-strictness.md` exits 0 with `OUTCOME: pass`.

**Ship when:**
- None; the change is repository-internal.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/facts_paths.py`
- `agents/skills/review-plan/SKILL.md` (Project strictness classes section only; frozen elsewhere per Standing constraints)
- `agents/skills/review-loop/SKILL.md` (the mechanical class sentence only)
- `agents/skills/plans/SKILL.md` (the rule 16 class sentences only; frozen elsewhere per Standing constraints)
- `agents/skills/review-staging/SKILL.md` (the cap-closure class sentence only)
- `scripts/check_maintenance_pins.sh` (new rows and the header invariant list line only)

**Tests:**
- none separate; the resolver's test surface is the in-file `selftest()` of `scripts/facts_paths.py`, covered by the Production code entry above

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`; verified accurate under the widened class set (see Assumptions) and shared-file live with two in-flight peer executions.
- `agents/skills/receiving-review/SKILL.md`; class-agnostic advisory referral, accurate as-is.
- plan-detail regions of `review-plan` and `plans`; owned by the execution-dependency plan.

## Validation Commands

```bash
python3 scripts/facts_paths.py --selftest
bash scripts/check_maintenance_pins.sh
python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies
bash scripts/check-no-em-dash.sh added-lines --base main
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-07-review-plan-project-strictness.md
```

## Test Pins

- Pin A (Task 2): the amended class-resolution paragraph names the mechanical resolver; the literal `resolve_project_class` appears in `agents/skills/review-plan/SKILL.md`, zero-hit in the pre-change bytes.
- Pin B (Task 2): the amended class-resolution paragraph carries the project-facts independence statement; the literal `never need to duplicate` appears in `agents/skills/review-plan/SKILL.md`, zero-hit in the pre-change bytes.
- Pin C (Task 3): the amended mechanical sentence carries the company mapping; the literal `standard- and company-class projects` appears in `agents/skills/review-loop/SKILL.md`, zero-hit in the pre-change bytes.
- Pin D (Task 1): project-facts independence is witnessed executably by the selftest arm that configures a project-local `personal_projects_root` naming the checkout while the user facts roots exclude it and asserts `standard` (not a grep pin; the arm is the witness).
- Pin E (Task 2): the amended class-resolution paragraph carries the unresolved recording surface; the literal `Class resolution: <class>(<reason>)` appears in `agents/skills/review-plan/SKILL.md`, zero-hit in the pre-change bytes.
- Pin F (Task 3): the plans rule 16 insertion is pinned; the literal `an \`unresolved\` resolution is recorded in the round record` appears in `agents/skills/plans/SKILL.md`, zero-hit in the pre-change bytes.
- Pin G (Task 3): the review-staging insertion is pinned; the literal `never closes through this shape either` appears in `agents/skills/review-staging/SKILL.md`, zero-hit in the pre-change bytes.
- Pin H (Task 2, absence): the replaced silent-standard clause is fenced against resurrection; the literal `or an unresolvable facts document, resolves \`standard\`` is zero-hit in `agents/skills/review-plan/SKILL.md` after the replacement (and present before it).

### Task 1: resolver and selftest arms

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/facts_paths.py`

Evidence:
- `python3 scripts/facts_paths.py --selftest`; covers all twenty-one arms below

- [ ] RED: add twenty-one selftest arms to `selftest()` calling `resolve_project_class(start_dir, user_facts)` before the function exists; run `python3 scripts/facts_paths.py --selftest` and expect the run to abort with a NameError traceback (undefined name), recording the observed failure in the task log; every fixture git invocation (init, commit, worktree add) runs with a scrubbed environment (GIT_-prefixed variables removed), GIT_CONFIG_GLOBAL and GIT_CONFIG_SYSTEM pointed at the null device, and identity via the `-c user.email` and `-c user.name` overrides [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_personal_primary`; given a temp workspace root W, a git repo R inside it, and a user facts file whose `personal_projects_root` table row names W, expects `("personal", "")` [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_worktree_owning_checkout`; given a primary repo P inside personal root W with one commit (identity via `-c user.email` and `-c user.name` overrides), and a linked worktree created at an absolute path in a second temp directory outside W via `git -C P worktree add <absolute-path-outside-W> -b wt`, expects `("personal", "")`, proving the owning checkout classifies the worktree [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_company_containment`; given a repo inside the `company_projects_root` row's directory, expects `("company", "")` [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_company_worktree`; given a primary repo P inside company root C with one commit and a linked worktree created at an absolute path outside both roots, expects `("company", "")` [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_outside_both_roots`; given a repo outside both configured roots, expects `("standard", "")` [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_sibling_prefix`; given the personal root W as the only configured root and a repo under the unconfigured sibling W2 whose name extends W's final path segment as a string (W2 is outside W component-wise though W2 startswith W as a string), repo at W2/repo, expects `("standard", "")`, proving containment is per path segment, never a raw string prefix [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_root_equal`; given the repo whose path equals the personal root itself, expects `("personal", "")`, pinning containment as inclusive of the equal path [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_missing_user_facts`; given a `user_facts` path with no file, expects `("unresolved", "user-facts-unresolvable")` [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_rows_absent`; given a user facts file without either root row, expects `("unresolved", "user-facts-unresolvable")` [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_malformed_row`; given a user facts file whose `personal_projects_root` row's value cell strips to empty (a single-space value cell) and which carries no company root row, expects `("unresolved", "user-facts-unresolvable")` [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_one_member_drop`; given a user facts file whose `personal_projects_root` row's value cell strips to empty (a single-space value cell) beside a resolvable `company_projects_root` row whose directory contains the repo, expects `("company", "")`, proving a None member drops only that root [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_decode_failure`; given a user facts file carrying non-UTF-8 bytes, expects `("unresolved", "user-facts-unresolvable")`, proving the never-raise contract survives decode failure [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_stale_root`; given a user facts file whose `personal_projects_root` row names a directory that does not exist and which carries no company root row, expects `("unresolved", "user-facts-unresolvable")`, proving a stale root path resolves visibly unresolved rather than silently standard [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_one_stale_root`; given a user facts file whose `personal_projects_root` row names a directory that does not exist beside a resolvable `company_projects_root` row whose directory contains the repo, expects `("unresolved", "user-facts-unresolvable")`, proving a misconfigured root forces visible unresolved even beside a valid root [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_compound_worktree`; given a linked worktree whose primary uses a separate git dir and has one commit so the common dir's parent is not a checkout root, expects `("unresolved", "owning-checkout-unresolvable")`, proving a linked-worktree toplevel never falls back to itself as the owning checkout [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_git_leg_totality`; given the subprocess seam patched to raise ValueError via the module's own raiser-patch fixture idiom, expects `("unresolved", "owning-checkout-unresolvable")`, proving the owning-checkout leg's total mapping absorbs out-of-family exceptions [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_ambiguous_containment`; given nested roots (personal W, company W/proj) and a repo at W/proj/inner, expects `("unresolved", "ambiguous-root-containment")` [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_separate_git_dir`; given a checkout whose git dir lives outside its toplevel (separate-git-dir layout) with the toplevel inside personal root W, expects `("personal", "")`, proving the conditional falls back to the toplevel when the common dir's parent is not itself a checkout root [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_project_facts_independence`; given a project facts file in the repo carrying `personal_projects_root` naming the containing directory while the user facts roots exclude the repo, expects `("standard", "")`, proving project facts are never consulted [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_non_repo_directory`; given a plain temp directory with no git repository and a `user_facts` path with no file, where the fixture first asserts that git discovery fails in the temp directory (so the arm cannot inherit an enclosing checkout through the ancestor chain), expects `("unresolved", "owning-checkout-unresolvable")`, proving the owning-checkout leg resolves first and its reason wins when both legs are unresolvable [class: REPOSITORY_TEST]
- [ ] `selftest` arm `resolve_class_cli_subcommand`; given the module invoked as `python3 scripts/facts_paths.py class <start-dir> <user-facts-path>`, expects stdout `<class>` then a tab then the reason with exit 0 for a resolved repo, and the unresolved row for a missing facts path [class: REPOSITORY_TEST]
- [ ] GREEN: implement `resolve_project_class` in `scripts/facts_paths.py`: owning checkout via `git -C <start_dir> rev-parse --path-format=absolute --git-common-dir` plus the toplevel via `git -C <start_dir> rev-parse --path-format=absolute --show-toplevel`, both with a scrubbed environment (GIT_-prefixed variables removed from the child env; list argv, `shell=False`, `timeout=RESOLVER_GIT_TIMEOUT_S`, capture); each leg's resolution is wrapped so that ANY failure maps to that leg's unresolved arm (an exception of any type, a nonzero exit, or empty output included; the wrapping is a total per-leg mapping, never an enumerated catch list; the parent checkout-root check rides the owning-checkout leg's scrubbed, timeout-bounded, total-mapping resolution), and the owning-checkout leg resolves first with its reason winning when both legs are unresolvable; the owning checkout is the toplevel when the common dir lies inside the toplevel, otherwise the common dir's parent when that parent is itself a checkout root, otherwise the toplevel when the toplevel is not itself a linked worktree (the toplevel is a linked worktree exactly when its .git file's gitdir target sits under the common dir's worktrees directory; a separate-git-dir primary's .git file points at the common dir itself and is therefore not a linked worktree), and a linked-worktree toplevel whose owning checkout cannot be resolved returns the unresolved owning-checkout arm; roots via the existing `resolve_projects_roots(user_facts)` under the same any-exception mapping to the unresolved user-facts arm (both members None is the same arm; a None member drops only that root from containment; a row that parses but whose directory does not exist forces the unresolved user-facts arm even when the other root resolves, while an absent row and an empty-value-cell row still drop as legitimately unconfigured); the table parser hardened in the same task so a row whose value cell strips to empty returns None (one line in `_resolve_table_key_in_file`); component-wise realpath containment (per path segment, never a raw string prefix, inclusive of the equal path; inside both roots is `unresolved` with reason `ambiguous-root-containment`), never raising; add the `class <start-dir> [user-facts-path]` subcommand to `main()` printing `<class>` then a tab then the reason and exiting 0 (the user-facts default is the same `~/.ai-playbook/facts.md` default, expanduser-applied), and update the `main()` usage line for the new subcommand in the same task; extend the module docstring so its opening title line and responsibilities count name the class-resolution responsibility (three responsibilities) with the reads-no-facts claim scoped to the keying half, and extend `resolve_projects_roots`'s docstring consumer sentence to name the class resolver beside the summarizer; run the selftest and expect all arms GREEN [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `python3 scripts/facts_paths.py --selftest` exits 0 with every existing arm still passing [class: REPOSITORY_TEST]
- [ ] Commit: `facts-paths: resolve project strictness class from user facts and owning checkout` [class: IMPLEMENTATION_REQUIRED]

### Task 2: canonical class-resolution contract and its pins (strictly after Task 1)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-plan/SKILL.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the four new rows and suite green
- Pin A, Pin B, and Pin E zero-hit verification: each literal grepped against the pre-change bytes of agents/skills/review-plan/SKILL.md before the task's edit, then exactly-once after, recorded in the task log

- [ ] Replace the class-resolution paragraph (the paragraph beginning `Class resolution: read \`personal_projects_root\` from the opening TOML block of the project facts document.` and ending `the value lives only in the local facts document.`) with the user-facts contract: the resolver `resolve_project_class(start_dir, user_facts)` in `scripts/facts_paths.py` is the mechanical procedure of record, invoked as `python3 scripts/facts_paths.py class <start-dir> [user-facts-path]` printing the class then a tab then the reason; it resolves the owning repository checkout (the toplevel when the git common dir lies inside the toplevel, otherwise the common dir's parent when that parent is itself a checkout root, otherwise the toplevel when the toplevel is not itself a linked worktree, where the toplevel is a linked worktree exactly when its .git file's gitdir target sits under the common dir's worktrees directory and a separate-git-dir primary's .git file points at the common dir itself and is therefore not a linked worktree, and a linked-worktree toplevel whose owning checkout cannot be resolved returns the unresolved owning-checkout arm; so a linked worktree classifies by its owning checkout, never its temporary path), reads the workspace roots from the user facts document (`user_facts_path`, typically `~/.ai-playbook/facts.md`; project facts never need to duplicate these roots and are never consulted), and classifies by component-wise realpath containment: `personal` under the personal root, `company` under the company root, `standard` outside both; facts or repository identity that cannot be resolved return the visible `unresolved` class with a reason from the closed set `owning-checkout-unresolvable`, `user-facts-unresolvable`, `ambiguous-root-containment`; `unresolved` is never silently mapped to `standard`; every resolution records as a `Class resolution: <class>(<reason>)` line in the round record's Metadata (the reason segment empty for resolved classes), carried by the resolving session into every round record it stages; an `unresolved` resolution runs the standard branch's budgets and keeps the cap-closure terminal shape unavailable, like `personal`; never hardcode a workspace directory in shared prose; the values live only in the user facts document [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert the company branch paragraph after the Personal strict package block and before the Standard branch paragraph: a `company`-class project keeps the standard branch's budgets and the cap-closure terminal shape, no company-specific cap exists, the company class is recorded in the round record so company-specific triage and consultation policies can key on it, and introducing a company-specific cap is a separate operator-directed decision [class: IMPLEMENTATION_REQUIRED]
- [ ] Add four pins rows to `scripts/check_maintenance_pins.sh` in the suite's existing row style: presence with exactly-once count for `resolve_project_class` over `agents/skills/review-plan/SKILL.md` (Pin A), presence for `never need to duplicate` over the same file (Pin B), presence with exactly-once count for `Class resolution: <class>(<reason>)` over the same file (Pin E, the recording surface), and one absence row for `or an unresolvable facts document, resolves \`standard\`` over the same file failing when the replaced silent-standard clause returns (Pin H); extend the suite header's invariant list with one line naming the strictness-class contract family [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` exits 0 [class: REPOSITORY_TEST]
- [ ] Commit: `review-plan: resolve strictness class from user facts and owning checkout` [class: IMPLEMENTATION_REQUIRED]

### Task 3: consumer class-keyed sentences (strictly after Task 2)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/review-loop/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-staging/SKILL.md`
- `scripts/check_maintenance_pins.sh`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the Pin C, Pin F, and Pin G rows going green against their target sentences
- Pin C, Pin F, and Pin G zero-hit verification: each literal grepped against the pre-edit bytes of its target file, expecting zero, recorded in the task log
- `python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies`; covers the plans SKILL.md insertion

- [ ] Add three pins rows to `scripts/check_maintenance_pins.sh` in the suite's existing row style: presence for `standard- and company-class projects` over `agents/skills/review-loop/SKILL.md` (Pin C), presence for `an \`unresolved\` resolution is recorded in the round record` over `agents/skills/plans/SKILL.md` (Pin F), presence for `never closes through this shape either` over `agents/skills/review-staging/SKILL.md` (Pin G) [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/review-loop/SKILL.md`, replace the mechanical sentence tail `; \`max_full_panel_rounds\` keeps its default for standard-class projects.` with `; \`max_full_panel_rounds\` keeps its default for standard- and company-class projects, and an \`unresolved\` resolution records its condition in the round record, runs the standard branch's budgets, and keeps the cap-closure terminal shape unavailable.` [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/plans/SKILL.md` rule 16, insert after the sentence ending `escalates to simplify-or-rewrite instead.` and before the sentence beginning `The cap-closure terminal shape's mechanics`: `A \`company\`-class plan keeps the standard branch's budgets and the cap-closure terminal shape; an \`unresolved\` resolution is recorded in the round record, runs the standard branch's budgets, and keeps the cap-closure terminal shape unavailable.`; the tail sentence beginning `The cap-closure terminal shape's mechanics` survives verbatim after the insertion [class: IMPLEMENTATION_REQUIRED]
- [ ] In `agents/skills/review-staging/SKILL.md`, append after the sentence ending `(class resolution: \`review-plan\`, Project strictness classes).`: `An \`unresolved\` resolution never closes through this shape either.` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh` exits 0 and `python3 scripts/test_execute_plan_runtime.py -k shared_skill_bodies` exits 0 [class: REPOSITORY_TEST]
- [ ] Commit: `skills: carry the company and unresolved class mapping into consumer sentences` [class: IMPLEMENTATION_REQUIRED]
