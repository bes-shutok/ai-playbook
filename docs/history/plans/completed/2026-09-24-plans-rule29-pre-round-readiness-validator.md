# Plan: plans rule 29 pre-round readiness validator

Backlog origin: docs/history/backlog/2026-09-21-plans-rule29-pre-round-readiness-validator.md
Driving force: efficiency

## Terms

- **Pre-round invocation**: the authoring-time call `python3 scripts/plan_readiness.py --pre-round <plan-path>` introduced by this plan; runs before the first review-plan round.
- **Structural probe**: a validator check that reads only the plan bytes (plus, for file-existence checks, the repo root): `decision_marker_problem`, `review_scope_problem`, `plan_ownership_problem`, `scope_classification_problem`. A probe never reads a review record.
- **Review record**: the latest review Markdown plus its `.stats.json` sidecar for the plan's feature slug; the exit gate's digest, schema, verdict, and blocking bindings all live there.
- **Stats sidecar**: the `<review>.stats.json` file produced beside each review round; its absence pre-round is the tolerated failure class.
- **Classification tag**: the `[class: IMPLEMENTATION_REQUIRED]` or `[class: REPOSITORY_TEST]` marker every task checklist item must carry; enforced by `scope_classification_problem`.
- **Decision-points trailer**: the plain `Decision points requiring a grill:` line inside `## Assumptions`; enforced by `decision_marker_problem`.
- **Digest binding**: the sidecar `source_digest` must equal the SHA-256 of the current plan bytes; any post-certification byte change forces a fresh certification round.

## Assumptions

- assume the pre-round invocation is a new `--pre-round` CLI mode rather than a tolerance wrapper over the full gate; basis: in `evaluate_readiness` the review-record checks (steps 2 through 5) run before the structural probes (steps 6 through 8) and the probes are sidecar-date-gated, so a pre-round full-gate call always fails at the no-review-artifact step and can never report a structural defect; the recommended shape was accepted under the standing pre-authorization (user dispatch, 2026-09-24).
- assume the pre-round scope is all four structural probes, including `plan_ownership_problem`, not only the three named in the backlog parenthetical; basis: the backlog's operative rule reads "structural checks that do not depend on a review record" and the parenthetical is illustrative; accepted under the standing pre-authorization (2026-09-24).
- assume the deployed home fallback `~/.ai-playbook/scripts/plan_readiness.py` stays a symlink to this repo's copy; basis: verified on disk 2026-09-24 (symlink into the primary checkout, same for `validate_review_staging.py` and `facts_paths.py`); the done skill's deployment-gap remedy already preserves symlinks (`cp -P`).
- assume `evaluate_readiness` is left untouched; the pre-round path is an additive branch in `main()` plus one new function; basis: conservative choice for a certified fail-closed gate, accepted under the standing pre-authorization (2026-09-24).
- assume P51 and P55 executions may later edit the same surfaces (plans SKILL.md, the validator); basis: dispatch constraint of record; this plan's execution re-baselines through the standard digest re-certification on drift, no file-level conflict resolution is prescribed.

Decision points requiring a grill: pre-round invocation shape: new `--pre-round` structural-only CLI mode, full gate cannot report structural defects pre-round (repo evidence in evaluate_readiness ordering; recommended option accepted per standing pre-authorization, user dispatch 2026-09-24); probe scope: all four review-record-independent probes including plan ownership (operative backlog rule text; accepted per standing pre-authorization 2026-09-24); deployed-copy policy: keep the home fallback a symlink, no dereferenced copy and no second sync path (on-disk verification 2026-09-24; accepted per standing pre-authorization 2026-09-24); exit-gate refactor: none, additive branch only (conservative choice; accepted per standing pre-authorization 2026-09-24)

## Design Invariants (CR Guard)

1. `evaluate_readiness` and the full-gate CLI contract stay behavior-identical for every existing input; the pre-round path is additive (one argparse flag, one dispatch branch, one new function, one selftest family). Reject any task or review change that refactors the shared gate.
2. The pre-round mode never reads `reviews_dir` contents or any sidecar; the tolerated no-review-artifact class is respected by construction (no consultation), never by swallowing a failure after the fact.
3. The four probe functions remain the single owners of their checks; `run_pre_round` calls them in gate order and never re-implements probe logic.
4. The sibling compatibility handshake keeps running before every CLI mode, including `--pre-round`.
5. `--pre-round` composes with neither `--selftest` nor `--sweep`; the combination is a `parser.error` (exit 2), decided at parse time.
6. The deployed home copy is the symlink; this plan introduces no dereferenced copy and no second deployment path.

## Gist & Examples

TLDR: the readiness validator gains a structural-only `--pre-round` authoring gate wired into plans rule 29, so missing classification tags and sibling structural defects die at authoring time instead of burning a certification round, for efficiency.

Today the readiness validator only runs at the execute and done boundaries, and its structural probes are gated on the latest review round's date, so they never run before a review record exists. Three witnessed authoring runs executed the em-dash and hygiene scans faithfully, passed full review panels, and were then failed by the validator at done time on missing classification tags (twelve task items in the 2026-09-20/21 quota-aware authoring; all 21 items in the 2026-09-22 priority-profiles authoring, which burned a 19-minute r1 panel on a defect the validator reports instantly; five per-task Commit lines in the 2026-09-22 executed-origin-strays authoring, where reviewers read Commit lines as bookkeeping rather than task items). Each recurrence cost one extra certification round after a tag-only fold, exactly the avoidable-recertification cost rule 29 exists to prevent.

After this plan, the authoring run's pre-round gate sequence is: no-em-dash scan, public-hygiene scan, then `python3 scripts/plan_readiness.py --pre-round docs/plans/<plan-file>.md`. The pre-round mode runs the four structural probes unconditionally (no sidecar-date gate: the plan under authoring is new, so no retrofit exemption applies) and never consults the review record. Exit 0 means structurally clean; exit 1 names the first failing probe on stderr as `readiness PRE-ROUND FAILED: <problem>` and blocks round 1 exactly like a hygiene-scan hit. The no-review-artifact/missing-sidecar condition is the only tolerated failure class, and the pre-round mode is immune to it by construction because it never reads the review record. A structural-clean pre-round pass converts the done-time exit gate into a pure review-record binding check (sidecar schema, source_kind, digest, verdict, zero blocking).

Example: an authoring run writes a plan whose five per-task Commit checklist lines carry no `[class: ...]` tag. Pre-round, `--pre-round` exits 1 in well under a second with `readiness PRE-ROUND FAILED: task checklist item ... carries no classification tag`, the author folds the tags, and round 1 launches against clean bytes. Without the gate, the same defect survives seven clean review rounds and fails at done time, forcing a blind re-certification round.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every structural failure class the probes detect blocks the pre-round invocation with exit 1 and a named problem; the tolerated class never blocks; the three witnessed failure classes (task-item tags, all-item tags, per-task Commit-line tags) are covered by the same classification probe, demonstrated by the blocking selftest arm using a Commit-line fixture.
- compatibility: `--selftest` and full-gate behavior on all pre-existing fixtures is unchanged (the dispatcher gains one family; `evaluate_readiness` is untouched); `--sweep` untouched.
- performance: the pre-round invocation is pure in-memory text probing plus at most repo-root file-existence checks; sub-second on this repo's plans.
- maintainability: probe functions stay the single check owners; no duplicated probe logic; the selftest family follows the existing fixture-family conventions.

**Done when:**
- `python3 scripts/plan_readiness.py --selftest` exits 0 with the new `_selftest_pre_round` family passing its four checks (structural-only pass, missing-sidecar tolerated, structural failure blocking, mutual exclusion) and every pre-existing family unchanged.
- `python3 scripts/plan_readiness.py --pre-round docs/plans/2026-09-24-plans-rule29-pre-round-readiness-validator.md` exits 0 against this plan's own bytes (self-application).
- plans SKILL.md rule 29 names the pre-round invocation, its tolerated class, its blocking semantics, and the Validation-preamble recording duty; the Plan Quality Gate names the pre-round role beside the exit-gate role; done Step 1.5's plan-readiness bullet notes the authoring-time pre-round role; README's scripts catalog carries the `plan_readiness.py` row with the mode.
- the no-em-dash scan and the public-hygiene scan exit 0.

**Ship when:**
- on hosts whose `~/.ai-playbook/scripts/plan_readiness.py` is the symlink, the mode is live at landing with no operator action (human-owned verification on each host; prose only).
- on hosts with a dereferenced real-file copy, the operator re-runs the done skill's documented deployment-gap remedy (copy the script plus its two siblings, preserving symlinks) before the next done run; prose only.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/plan_readiness.py`; in scope only for: the `main()` argparse surface and dispatch, the new `run_pre_round` function, the new `_selftest_pre_round` family, and the `run_selftest` registration line. All other functions in this file are frozen; reject any review finding that touches them.

**Documentation:**
- `agents/skills/plans/SKILL.md`; in scope only for the rule 29 bullet in "Validation Commands (authoring rules)" and the validator-role paragraph in the Plan Quality Gate section. All other content is frozen.
- `agents/skills/done/SKILL.md`; in scope only for the plan-readiness bullet under the pre-docs sweep gates. All other content is frozen.
- `README.md`; in scope only for the scripts catalog table row insertion. All other content is frozen.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/validate_review_staging.py`; shared sidecar authority consumed read-only via its public helpers; frozen by Design Invariant 1.
- `scripts/facts_paths.py`; stdlib leaf used as-is for project-key and path resolution.
- `agents/hooks/skill-gate/`; the marker project-key fix is owned by a separate backlog item and plan.
- `docs/maintenance/development_lessons.md`; the lessons corpus is learn-owned, not a plan deliverable.

## Validation Commands

Gate states recorded at authoring time (2026-09-24, pre-change authoring-worktree bytes): no-em-dash scan exit 0; public-hygiene scan exit 0; `python3 scripts/plan_readiness.py --selftest` exits 0 ALL PASS on the baseline tree, with the four new `_selftest_pre_round` checks vacuously absent (they arrive with Task 1, so the selftest cannot yet observe them); `--pre-round` exits 2 with argparse "unrecognized arguments" (the mode this plan adds does not exist yet); each rule-29, Plan Quality Gate, done, and README span probe reports 0 matches today (the amended text does not exist yet); each def and message count pin reports 0 today; the pre-round CLI over this plan exits 2. The four structural probes were additionally exercised against this plan's own bytes via direct function calls (`decision_marker_problem`, `review_scope_problem`, `plan_ownership_problem`, `scope_classification_problem`): all clean at authoring time. First actually-failing gate of the block today: gate 5, the pre-round CLI (exit 2, unrecognized option), per authoring rule 19 execution discipline; every later gate that depends on this plan's own deliverables is recorded as failing or vacuous as listed above.

```bash
REPO="$(git rev-parse --show-toplevel)" || { echo "FAIL: not inside a git repo"; exit 1; }
PLAN_REL="docs/plans/2026-09-24-plans-rule29-pre-round-readiness-validator.md"

# Gate 1: no-em-dash over the plan bytes (the only file this plan creates;
# the edited files' prescribed insertions are embedded verbatim below and
# are em-dash-free by construction, while their legacy content is frozen).
bash scripts/check-no-em-dash.sh file "$PLAN_REL" \
  || { echo "FAIL: em dash in plan bytes"; exit 1; }

# Gate 2: public-hygiene scan, anchored at the repo root.
( cd "$REPO" && bash scripts/scan-public-hygiene.sh ) \
  || { echo "FAIL: public hygiene scan"; exit 1; }

# Gate 3: validator compiles.
python3 -m py_compile scripts/plan_readiness.py \
  || { echo "FAIL: plan_readiness does not compile"; exit 1; }

# Gate 4: validator selftest, including the new pre-round family.
( cd "$REPO" && python3 scripts/plan_readiness.py --selftest ) \
  || { echo "FAIL: plan_readiness selftest"; exit 1; }

# Gate 5: the pre-round structural gate over this plan's own bytes.
( cd "$REPO" && python3 scripts/plan_readiness.py --pre-round "$PLAN_REL" ) \
  || { echo "FAIL: pre-round structural gate over the plan"; exit 1; }

# Gate 6: rule 29 carries the pre-round invocation duty (spans quoted
# verbatim from Task 3's prescribed snippets; bracket escapes in needles
# are intentional self-match immunity, do not normalize them).
SKILL="$REPO/agents/skills/plans/SKILL.md"
test "$(grep -cF 'structural-only pre-round invocation' "$SKILL")" -eq 1 \
  || { echo "FAIL: rule 29 pre-round invocation span missing or duplicated"; exit 1; }
test "$(grep -cF 'blocks round 1 exactly like a hygiene-scan hit' "$SKILL")" -eq 1 \
  || { echo "FAIL: rule 29 blocking semantics span missing or duplicated"; exit 1; }
test "$(grep -cF 'structural-only pre-round gate (rule 29)' "$SKILL")" -eq 1 \
  || { echo "FAIL: Plan Quality Gate pre-round role span missing or duplicated"; exit 1; }

# Gate 7: done Step 1.5 documents the pre-round role.
test "$(grep -cF 'structural-only pre-round gate (plans rule 29' "$REPO/agents/skills/done/SKILL.md")" -eq 1 \
  || { echo "FAIL: done pre-round role span missing or duplicated"; exit 1; }

# Gate 8: README scripts catalog carries the validator row.
test "$(grep -cF 'authoring-time structural gate' "$REPO/README.md")" -eq 1 \
  || { echo "FAIL: README validator row missing or duplicated"; exit 1; }

# Gate 9: exactly one pre-round function definition each, one dispatcher
# registration, and both CLI message constants (count pins, not presence).
test "$(grep -c '^def run_pre_round' scripts/plan_readiness.py)" -eq 1 \
  || { echo "FAIL: run_pre_round def count"; exit 1; }
test "$(grep -c '^def _selftest_pre_round' scripts/plan_readiness.py)" -eq 1 \
  || { echo "FAIL: _selftest_pre_round def count"; exit 1; }
test "$(grep -c '    _selftest_pre_round(root, plans_dir, reviews_dir, check)' scripts/plan_readiness.py)" -eq 1 \
  || { echo "FAIL: pre-round family registration count"; exit 1; }
grep -q 'readiness PRE-ROUND OK' scripts/plan_readiness.py \
  || { echo "FAIL: pre-round OK message missing"; exit 1; }
grep -q 'readiness PRE-ROUND FAILED' scripts/plan_readiness.py \
  || { echo "FAIL: pre-round FAILED message missing"; exit 1; }
```

### Task 1: Selftest arms for the pre-round invocation (RED)

Files:
- `scripts/plan_readiness.py`

Build the fixture text once inside the new family as a local helper (for example `_pre_round_clean_plan_text()`), mirroring the section order of the four existing fixture builders: a `# Plan:` title, an `## Assumptions` section closing with the plain trailer line `Decision points requiring a grill: none remain.`, the `### Task 1` section with its `Files:` list matching the Review Scope entries and checklist items that all carry a classification tag (including the per-task Commit line), and only then the `## Review Scope` section, whose explicit must-fix blocks list one `*(new)`-marked path under Production code and one `*(new)`-marked doc path under Documentation (the marker is what satisfies the ownership probe for both paths, since neither fixture path exists on disk). The order is load-bearing: `md_section` ends a `##` section only at the next `## ` heading, so a Review Scope section placed before the task section swallows it and the path-kind probe then misreads the Production-code path as Documentation-listed. Reuse the valid-fixture text patterns already proven by the `_selftest_decision_marker`, `_selftest_review_scope`, `_selftest_plan_ownership`, and `_selftest_scope_classification` families, and assert the composed text passes all four probes via direct function calls before wiring the CLI arms.

- [x] `_selftest_pre_round#structural_only_pass`; given the clean fixture plan written under plans_dir, expects `main(["--pre-round", str(plan)])` to return 0 with `readiness PRE-ROUND OK` on stdout [class: REPOSITORY_TEST]
- [x] `_selftest_pre_round#missing_sidecar_tolerated`; given the clean fixture plan with an emptied reviews dir, expects the `--pre-round` invocation to return 0 (the no-review-artifact/missing-sidecar class is tolerated) while the full-gate invocation over the same tree returns 1 with `no review artifact` on stderr [class: REPOSITORY_TEST]
- [x] `_selftest_pre_round#structural_failure_blocking`; given the clean fixture plan with the per-task Commit checklist line stripped of its classification tag, expects the `--pre-round` invocation to return 1 with `readiness PRE-ROUND FAILED` on stderr naming the classification-tag problem [class: REPOSITORY_TEST]
- [x] `_selftest_pre_round#mutual_exclusion`; given `--pre-round` combined with `--selftest`, and again with `--sweep`, expects exit 2 from `parser.error` naming the combination as invalid [class: REPOSITORY_TEST]
- [x] Add the family `_selftest_pre_round(root, plans_dir, reviews_dir, check)` following the existing fixture-family conventions (temp tree, shared `check` reporter, `_selftest_run_main` for CLI capture) plus a local SystemExit-capturing wrapper around every `main()` invocation whose argparse exit is asserted (argparse raises `SystemExit` through `_selftest_run_main`; the wrapper catches it and uses `exc.code` as the rc), and register the family in `run_selftest` between the `_selftest_scope_classification` and `_selftest_accepted_state` calls [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: `python3 scripts/plan_readiness.py --selftest` exits 1 with exactly the four `selftest#pre_round/...` arm checks failing on the unrecognized `--pre-round` option (each arm's rc capture yields 2 against its expected rc) while every pre-existing family check still passes [class: REPOSITORY_TEST]
- [x] Commit: `test: pre-round structural gate selftest arms` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The --pre-round structural-only mode (GREEN)

Files:
- `scripts/plan_readiness.py`

- [x] `main#pre_round_flag`; given `--pre-round` with a plan path, expects the dispatch branch placed after the shared facts resolution and the `plan_path` requirement, returning `run_pre_round(anchor_at_root(args.plan_path), plans_dir)`; the flag composes with neither `--selftest` nor `--sweep` (parse-time `parser.error`), and the sibling compatibility handshake still runs first [class: IMPLEMENTATION_REQUIRED]
- [x] `run_pre_round#probe_chain`; given plan bytes that decode, expects the four probes called in gate order (`decision_marker_problem`, `review_scope_problem`, `plan_ownership_problem(plan_text, repo_root(plans_dir.parent))`, `scope_classification_problem`) with no sidecar-date gating and no review-record consultation; first problem prints `readiness PRE-ROUND FAILED: <problem>` to stderr and returns 1; all clean prints `readiness PRE-ROUND OK: structural checks clean (review record not consulted)` and returns 0 [class: IMPLEMENTATION_REQUIRED]
- [x] `run_pre_round#path_semantics`; given a directory path, a missing file, a plan resolving outside plans_dir, and a plan under the plans `rejected/` directory, expects the same first-step failure reasons as `evaluate_readiness`, each surfaced as `readiness PRE-ROUND FAILED: <reason>` [class: IMPLEMENTATION_REQUIRED]
- [x] `run_pre_round#undecodable_bytes`; given plan bytes that are not valid UTF-8, expects exit 1 with `readiness PRE-ROUND FAILED` naming the unreadable plan bytes [class: IMPLEMENTATION_REQUIRED]
- [x] `run_pre_round#reviews_dir_independence`; given the facts TOML intact but the reviews dir absent from disk, expects the pre-round exit contract unchanged (0 on a clean plan, 1 only on a structural defect) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/plan_readiness.py --selftest` exits 0 ALL PASS with the four `selftest#pre_round/...` checks now passing and every pre-existing family check unchanged [class: REPOSITORY_TEST]
- [x] Run → expect unchanged: the full-gate fixtures elsewhere in the selftest suite report no new failures (gate behavior for existing inputs is untouched) [class: REPOSITORY_TEST]
- [x] Commit: `feat: plan_readiness --pre-round structural-only authoring gate` [class: IMPLEMENTATION_REQUIRED]

### Task 3: plans SKILL.md rule 29 and Plan Quality Gate

Files:
- `agents/skills/plans/SKILL.md`

Append to the rule 29 bullet (the item numbered 29 under "Validation Commands (authoring rules)", immediately after its final sentence "both witnessed occurrences (2026-09-04 and 2026-09-05 em-dash recerts) were avoidable by running the scan at authoring time.") the following verbatim text:

> After the em-dash and hygiene scans, run the readiness validator's structural-only pre-round invocation over the plan bytes: `( cd <repo-root> && python3 scripts/plan_readiness.py --pre-round docs/plans/<plan-file>.md )`. The invocation executes exactly the checks that do not depend on a review record (decision-points trailer, Review Scope path categories, plan-ownership static checks, classification tags) and never consults the review record; the deployed home fallback is a symlink to this repo's copy and inherits the mode at landing, so keep it a symlink. The only tolerated failure class is the no-review-artifact/missing-sidecar condition (the pre-round mode is immune to it by construction; when the full gate is invoked pre-round instead, its no-review-artifact/missing-sidecar reasons are the tolerated class). Any other structural failure blocks round 1 exactly like a hygiene-scan hit: fix before launching round 1. Record the pre-round gate outcome, and any failure class, in the plan's Validation preamble; a structural-clean pre-round pass converts the done-time exit gate into a pure review-record binding check (sidecar schema, source_kind, digest, verdict, zero blocking).

Append to the Plan Quality Gate validator-role paragraph (the sentence ending "...the self-check answers are negative by construction."), the following verbatim text:

> The same validator runs at authoring time as the structural-only pre-round gate (rule 29): the `--pre-round` invocation reports decision-trailer, Review Scope, plan-ownership, and classification-tag defects before the first review round launches, so no review round burns on a defect the validator reports mechanically; a green pre-round pass at authoring time means this boundary's gate re-proves only the review-record bindings.

- [x] Apply the rule 29 amendment verbatim (span probes: `structural-only pre-round invocation`, `blocks round 1 exactly like a hygiene-scan hit`; each exactly once in the file) [class: IMPLEMENTATION_REQUIRED]
- [x] Apply the Plan Quality Gate amendment verbatim (span probe: `structural-only pre-round gate (rule 29)`; exactly once in the file) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect: gate 6's three span pins flip from 0 matches to exactly 1; gates 1 through 5 stay green; gate 7 and gate 8 still report 0 matches (their files are edited at Task 4); gate 9 has been green since Task 2 [class: REPOSITORY_TEST]
- [x] Commit: `docs(plans): rule 29 pre-round readiness validator invocation` [class: IMPLEMENTATION_REQUIRED]

### Task 4: done Step 1.5 and README mentions

Files:
- `agents/skills/done/SKILL.md`
- `README.md`

Insert into the done skill's plan-readiness bullet (under "Pre-docs sweep gates"), immediately after "...passed, manifest-exempted, and archived plans have their deliverable lines pruned by the runner.", the following verbatim text:

> The same validator also runs at authoring time as the structural-only pre-round gate (plans rule 29, `--pre-round`); a structural-clean pre-round pass means this exit gate re-proves only the review-record bindings (sidecar schema, source_kind, digest, verdict, zero blocking).

Insert into README's scripts catalog table, directly after the `scripts/validate_review_staging.py` row, the following verbatim row:

> | `scripts/plan_readiness.py` | Fail-closed reviewed-plan readiness gate called by the execute-plan and done boundaries: sidecar schema, source_kind, digest, verdict, zero blocking, plus date-gated structural probes (decision-points trailer, Review Scope categories, plan ownership, classification tags). Run `python3 scripts/plan_readiness.py --pre-round docs/plans/<plan>.md` as the plans rule-29 authoring-time structural gate, `--selftest` for the built-in fixture families, `--sweep` for verdict-parse anomalies. |

- [x] Apply the done SKILL.md amendment verbatim (span probe: `structural-only pre-round gate (plans rule 29`; exactly once in the file) [class: IMPLEMENTATION_REQUIRED]
- [x] Apply the README catalog row verbatim (span probe: `authoring-time structural gate`; exactly once in the file) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect: gates 7 and 8 flip from 0 matches to exactly 1; gates 1 through 6 remain at their post-Task-3 states [class: REPOSITORY_TEST]
- [x] Commit: `docs(done,readme): document pre-round readiness gate role` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Full validation and self-application

Files:
- `scripts/plan_readiness.py`
- `agents/skills/plans/SKILL.md`
- `agents/skills/done/SKILL.md`
- `README.md`

- [x] Run the complete Validation Commands block from the repo root; expect every gate to exit 0, with gates 5 through 9 flipped GREEN relative to the states recorded in the section preamble [class: REPOSITORY_TEST]
- [x] Self-application witness: `python3 scripts/plan_readiness.py --pre-round docs/plans/2026-09-24-plans-rule29-pre-round-readiness-validator.md` exits 0 against this plan's own bytes, demonstrating the gate accepts a fully-tagged, trailer-complete, scope-consistent plan [class: REPOSITORY_TEST]
- [x] No commit expected in this task; any residue is a defect to fix in its owning task, not here [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-21-plans-rule29-pre-round-readiness-validator.md: disposition folded into 2026-09-24-plans-rule29-pre-round-readiness-validator.md (2026-09-25); per-item file deleted.
