# Plan: the post-landing-staging gate learns the declared worktree placement

Backlog origin: docs/history/backlog/2026-10-05-post-landing-staging-owned-plan-refusal.md
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-10-05-plan-review-post-landing-staging-placement-awareness-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Post-landing-staging gate: the done pre-commit gate `gate_post_landing_staging` in scripts/done_sweep_gates_lib.py (landed 4f1d095a as the squash-landing-failure-path-guard plan's Task 3) that inspects the primary checkout's index and tracked modifications after a landing: staged paths must be empty or manifest-owned, unstaged tracked modifications only the record-only allowlist, untracked reported-not-failing.
- Placement: the project facts document's declared `worktree_policy` key, whose spelled value set is exactly three forms per the owning policy paragraph (agents/skills/execute-plan/SKILL.md, the Worktree-first standard): `primary` (the default; the primary project checkout runs ordinary work and named lanes stop with a conflict), `primary-execution` (authorizes exactly one named lane, the plan-execution lane, to run in the primary checkout), and `worktrees` (ad-hoc worktrees allowed for non-lane work); a value outside the three spelled forms is treated as unconfigured. The key resolves through `facts_paths.resolve_toml_key_raw(start_dir, key)`, the invocation precedent being the plans-archive-twin gate's facts read in the same library.
- Primary-resident placement: a facts document whose resolved `worktree_policy` value is `primary` or `primary-execution`; in either placement the primary checkout is an authorized execution surface, so the run's own unstaged plan and review edits there are structural run state, not landing residue. `primary-execution` is the witnessed placement: the origin row's refusal ran on a repository declaring it (the primary-execution placement landing 3c03a222).
- Non-primary reading: an absent key, an unreadable facts file, a malformed or out-of-vocabulary value, or a resolution failure; in these readings the primary checkout should carry none of the run's edits, so an unstaged manifest-owned path there is the misdirected-write signature the strict unstaged leg exists to catch.
- Ownership set: the same manifest union the staged leg already exempts (`owned_paths` plus `owned_plan_paths` plus `owned_review_paths`, normalized through `_manifest_review_rel`); an unresolvable run manifest means no owned set and no widening anywhere in the gate, under every placement.
- Widened count set: the post-allowlist intersection `(unstaged - RECORD_ONLY_ALLOWLIST) & owned`, so an owned path that the record-only allowlist already permits is counted exactly once in the allowlist clause and never in the owned-unstaged clause.
- Remedy split: the refusal text's two shapes, composed only in the rc-1 message assembly (the shared `residue_render` feeding the rc-2 indeterminate arms stays untouched); unowned residue keeps today's refusal verbatim (the land_squash.sh probe-then-reland recipe and the guarded operator escape for dead residue), while a residue class containing manifest-owned paths names the misdirected-write check first (verify the run's worktree copy is authoritative before any restore), names staging the owned path as the sanctioned resolution for the owned class (staging clears both legs under any placement, per the origin row), and never presents the bare restore escape or the reland path for an owned path.
- Informational count: a pass-message clause naming the permitted paths, the same shape the gate already prints for record-only allowlist paths and manifest-owned staged paths.

## Why

The gate exempts manifest-owned paths on its staged leg but not on its unstaged leg, and it predates the primary-resident placements: in a repository declaring `worktree_policy = "primary-execution"` (the witnessed STORY-KEY placement, landing 3c03a222) or `primary`, every closeout carrying the run's own unstaged plan edits refuses, and both documented remedies (the probe-then-reland reland path, the git restore operator escape) would reland against or destroy the run's live work. The witnessed closeout was saved only by an undocumented in-session stage-the-file workaround, and the defect re-exposes on every primary-resident closeout until the gate learns the placement.

## Outcome

The gate reads the declared placement before judging the unstaged leg: under a primary-resident placement the unstaged leg mirrors the staged leg's ownership exemption (manifest-owned unstaged paths pass and are counted informationally), under every other reading the strict unstaged leg stands byte-for-byte, and the refusal text splits by ownership class so no owned path is ever offered a destructive remedy.

- In scripts/done_sweep_gates_lib.py, `gate_post_landing_staging` resolves the project facts' `worktree_policy` key through `facts_paths.resolve_toml_key_raw(ctx.repo_root, key)` once per run; a resolution of exactly `primary` or `primary-execution` widens the unstaged leg's exemption set to include the ownership set (the dirty-residue computation becomes `unstaged - RECORD_ONLY_ALLOWLIST - owned` when the manifest resolves, unchanged otherwise), counts the widened count set in the pass message, and leaves the record-only allowlist and untracked-warning arms untouched.
- The pass message's base parenthetical is amended in the same edit (to "no unowned staging, no unallowlisted unowned tracked modification") so the assembled message cannot self-contradict on the widened state, and the widened case's full message is pinned.
- An absent key, an unreadable facts file, a malformed or out-of-vocabulary value, and a resolution failure keep today's strict unstaged leg byte-for-byte; an unresolvable run manifest keeps strict too under every placement (no owned set, no widening; the existing unresolvable-manifest fixture stays green unchanged).
- The indeterminate arms are byte-identical for a residue composition that survives the widening (the shared `residue_render` is untouched); the reachable population changes by design: an owned-unstaged-only residue state that would today reach the held-lock rc-2 arm passes under a primary-resident placement, and mixed states still reach the arms with the owned paths absent from the evidence. The remedy split lives only in the rc-1 message assembly.
- The refusal text splits in the same edit per the Remedy split term: unowned residue verbatim; an owned class gets the misdirected-write check first, staging named as the sanctioned resolution, and never a destructive remedy. This supersedes, and records as superseded, the origin row's runtime-fact keying ("when the inspected checkout is the execution checkout") in favor of the declared-value keying, which is the mechanically decidable surface; the row's staging-remedy element is honored inside the owned-class text.
- The done skill's pre-commit sweep gates paragraph (between Step 2.75 and Step 3) gains the placement-aware permit and the remedy split in its post-landing-staging parenthetical in the same landing, and both placements are pinned as named fixtures beside the seven existing ones.

Gate delta: one new facts read and one conditional widening inside an existing gate (restrictive in direction: it can only reclassify an unstaged owned path from residue to permitted, never the reverse), one base-message amendment, one remedy split in the rc-1 assembly, one contract-text sync, and named new fixtures. No new gate, no new state field, no validator change.

## Assumptions

- assume the placement predicate is membership in the two primary-resident spelled forms (`primary`, `primary-execution`) of the facts key `worktree_policy`, read through `facts_paths.resolve_toml_key_raw(ctx.repo_root, "worktree_policy")`; basis: the owning policy paragraph's three-form value set and its "outside the three spelled forms is treated as unconfigured" clause (agents/skills/execute-plan/SKILL.md), and the same library already resolving facts keys through that reader in the plans-archive-twin gate; the frozen log entry's two-form naming ("worktree_policy = primary") predates the third form and is corrected here.
- assume a declaration error (an unreadable facts file, a malformed value, any value outside the spelled set) reads as unconfigured and keeps the strict leg; basis: the policy paragraph's own outside-vocabulary clause and the fail-closed reader convention.
- assume the ownership set is the staged leg's existing union and normalization, recomputed identically for the unstaged leg; basis: the gate's own staged-leg code in scripts/done_sweep_gates_lib.py.
- assume the unresolvable-manifest strict path is placement-independent: no manifest means no owned set, so the widening is inert even under a primary-resident placement; basis: the gate's ownership-narrowing skip arm, which keeps the strict staged-empty comparison with the unresolvable record named.
- assume the refusal split keys on the residue class composition, not the placement: an owned path in the residue means the misdirected-write check first and staging named as the sanctioned resolution, whatever the placement (under a primary-resident placement the widening makes this shape unreachable, which is the point); basis: the origin row's remedy demands ("probe-then-reland must be reserved for residue the run manifest does not own") and its staging remedy for the owned class.
- assume the keying supersedes the row's runtime-fact wording deliberately and visibly: the plan keys on the declared facts value because it is the mechanically decidable surface the gate can read, and records the supersession here; basis: the row's Expected block wording versus the gate's consumption surface.
- assume the adjacency holds unchanged: pending works edit the same sweep-gate library seam (the awaiting-execution done-lifecycle-recovery-gaps plan; the review-staging fence already landed in main), so anchors re-derive from live bytes at execution and a moved anchor re-keys its pin in the same edit; basis: the frozen entry's adjacency sentence and the plans root.
- assume authoring runs under the standing D-4 authoring directive plus the live operator order to continue authoring without stops, so the plans skill's Phase 1 confirmation is satisfied by the frozen entry's validated record; basis: the maintenance loop's authoring blueprint under the standing operator directive.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: the post-landing-staging gate stops refusing the run's own unstaged plan edits in a primary-resident repository, a code-quality classification fix for a witnessed false-block whose remedies were both destructive.

Before (today): a `primary-execution` closeout carrying the run's own unstaged plan edits refuses with the probe-then-reland recipe and the git restore escape; the first would reland against the live work, the second would destroy it, and the operator's only exit was an undocumented manual staging step.

After (this plan): the same gate reads `worktree_policy` first. Primary-resident (`primary` or `primary-execution`): the unstaged owned paths pass with an informational count in the pass message, exactly like the staged leg's owned exemption. Non-primary reading: byte-identical strict refusal for unowned residue, and an owned unstaged path in the residue gets a refusal naming the worktree-authority check first and staging as the sanctioned resolution, never a destructive remedy for the owned path.

Edge cases pinned: an absent `worktree_policy` key, an unreadable facts file, a malformed value, and any value outside the three spelled forms all keep the strict unstaged leg; an unresolvable run manifest keeps strict under every placement (no owned set, no widening), including a declared-primary variant; a residue class mixing owned and unowned paths refuses with the misdirected-write check first and staging named for the owned path while the unowned paths keep today's recipe naming; an owned path that also sits on the record-only allowlist is counted once in the allowlist clause and never double-named; the record-only allowlist paths stay permitted and counted under both placements; the untracked-warning arm behaves identically under both placements; the indeterminate arms are byte-identical for a residue composition that survives the widening, and an owned-unstaged-only state that today reaches the held-lock rc-2 arm passes under a primary-resident placement by design; the staged owned-path permit and the pass-message counting shapes stay exactly as they are except for the amended base parenthetical.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the widening fires only on the exact resolved values `primary` and `primary-execution` with a resolvable manifest; every other reading is byte-identical to today; the witnessed `primary-execution` closeout shape passes with the informational count; the widened count set never double-counts an allowlisted owned path.
- fail-closed placement: declaration errors read as unconfigured (strict); the widening can only reclassify an unstaged owned path from residue to permitted, never suppress a check for unowned residue; the unresolvable-manifest strict path is placement-independent; the indeterminate arms' shared render is untouched.
- observability: the pass message counts the permitted owned-unstaged paths and its base text stays truthful on the widened state; the refusal names the ownership class and the correct remedy per class (misdirected-write first and staging for owned, today's recipe for unowned); the indeterminate arms report unchanged for surviving compositions.
- maintainability: one facts read through the existing reader at one site, reusing the staged leg's ownership set; the contract text sync is a sentence-scoped edit in the pre-commit sweep gates paragraph; both placements pinned as named fixtures; the count-gated done-skill pin survives via key-free wording.

**Done when:**
- all task boxes checked; the sweep-gate suite passes under the venv pytest runner (`"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -q` exits 0, bare `python3` off-venv fails with rc 1 and a pytest import error, fail-closed rather than vacuous); the pins suite exits 0 (OUTCOME: pass); the em-dash added-lines scan and the public hygiene scan exit 0; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-post-landing-staging-placement-awareness.md` exits 0 on the final bytes.

**Ship when:**
- a `primary-execution` closeout carrying the run's own unstaged plan edits passes the post-landing-staging gate with the informational count, and an unconfigured repository's closeout behavior is byte-identical to today.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (the `gate_post_landing_staging` function span only)
- `agents/skills/done/SKILL.md` (the pre-commit sweep gates paragraph's post-landing-staging description span only)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (new named placement fixtures beside the seven existing `test_post_landing_staging_*` fixtures)
- `scripts/check_maintenance_pins.sh` (only if a re-derived anchor forces a pin re-key, in the same edit as the span move)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `scripts/facts_paths.py`: the reader is consumed, never changed.
- the other done gates and the gates runner: untouched.
- the awaiting-execution done-lifecycle-recovery-gaps plan's surfaces and the landed review-staging fence beyond the shared file: adjacency only; anchors re-derive, no pre-coordination edits.
- the record-only allowlist's membership: the allowlist is read, never redefined.
- the state schema and every other production script: no field grows, no tool changes.

## Validation Commands

```bash
# Sweep-gate suite (new placement fixtures; the venv runner is the
# canonical invocation; bare python3 off-venv fails rc 1 with a pytest
# import error, fail-closed rather than vacuous)
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -q
# Pins: the done-skill gates-order span keeps the post-landing-staging
# gate id literal, the done-skill Step 2 count pin (exactly 2
# worktree_policy occurrences) survives via key-free synced wording, and
# a moved anchor re-keys its pin in the same edit
bash scripts/check_maintenance_pins.sh
# Added-lines em-dash scan over the changed set (added-lines, never argless)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Readiness (fail-closed; outcome contract); RED at authoring until the
# staging review series lands under docs/reviews, green from r1 on
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-post-landing-staging-placement-awareness.md
```

### Task 1: Placement-aware unstaged leg and remedy split in the gate

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/check_maintenance_pins.sh` (conditional, pin re-key only)

Evidence:
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers every criterion below at the task boundary (bare `python3` off-venv fails rc 1 with a pytest import error)
- `grep -c "worktree_policy" scripts/done_sweep_gates_lib.py`; covers the facts-read presence (RED at authoring: zero hits)
- `grep -c "misdirected-write" scripts/done_sweep_gates_lib.py`; covers the remedy-split presence (RED at authoring: zero hits)

- [x] Re-derive the anchors from live bytes: the `gate_post_landing_staging` function (its staged-leg ownership set and `_manifest_review_rel` normalization, the dirty-residue computation, the shared `residue_render`, the indeterminate arms, the refusal message, the pass-message assembly and its base parenthetical), the `facts_paths.resolve_toml_key_raw` reader and the plans-archive-twin invocation precedent, the owning policy paragraph's three-form value set and its outside-vocabulary clause, and the pins suite's done-enumeration pin and done-skill Step 2 count pin (exactly 2 `worktree_policy` occurrences); if any anchor moved from the bytes this plan quotes, update the owning pin in the same edit [class: IMPLEMENTATION_REQUIRED]
- [x] Resolve the project facts' `worktree_policy` key once per run through `facts_paths.resolve_toml_key_raw(ctx.repo_root, "worktree_policy")` in `gate_post_landing_staging`; on the exact resolved value `primary` or `primary-execution`, widen the unstaged leg's exemption to include the staged leg's ownership set (the dirty-residue computation becomes `unstaged - RECORD_ONLY_ALLOWLIST - owned` when the manifest resolves, unchanged otherwise), count the widened count set `(unstaged - RECORD_ONLY_ALLOWLIST) & owned` in the pass message with the same clause shape the record-only allowlist and staged-owned counts use (an allowlisted owned path is counted once, never in both clauses), amend the pass message's base parenthetical to "no unowned staging, no unallowlisted unowned tracked modification" so the widened state cannot read self-contradictory, and leave the shared `residue_render`, the indeterminate arms' code, the record-only allowlist arm, and the untracked-warning arm byte-identical; on an absent key, an unreadable facts file, a malformed value, any value outside the three spelled forms, or a resolution failure, keep the strict unstaged leg byte-for-byte; an unresolvable run manifest keeps strict under every placement [class: IMPLEMENTATION_REQUIRED]
- [x] Split the refusal text by ownership class in the same edit, composed only in the rc-1 message assembly: unowned residue keeps today's refusal verbatim (the land_squash.sh probe-then-reland recipe, the guarded operator escape for dead residue, the record-only never-escapable clause); any residue class containing manifest-owned paths names the misdirected-write check first (verify the run's worktree copy is authoritative before any restore), names staging the owned path as the sanctioned resolution for the owned class, and never presents the bare restore escape or the reland path for an owned path, while unowned paths in the same class keep today's recipe naming [class: IMPLEMENTATION_REQUIRED]
- [x] Update the gate's docstring with the primary-resident placement predicate (both spelled forms), the fail-closed declaration-error reading, the placement-independent unresolvable-manifest strictness, the composition-conditional indeterminate behavior, and the remedy split so the function documents its own placement contract [class: IMPLEMENTATION_REQUIRED]
- [x] Run → GREEN: the sweep-gate suite OK under the venv runner with the seven existing fixtures green unchanged [class: REPOSITORY_TEST]
- [x] Commit: `fix: post-landing-staging gate exempts manifest-owned unstaged paths under primary-resident placement` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Contract text sync and named both-placements pins

Files:
- `agents/skills/done/SKILL.md`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `bash scripts/check_maintenance_pins.sh`; covers the done-enumeration pin criterion (the gates-order span keeps the post-landing-staging gate id literal) and the done-skill Step 2 count pin (the synced span is key-free, so exactly 2 `worktree_policy` occurrences still hold)
- `grep -c "exempts manifest-owned unstaged paths" agents/skills/done/SKILL.md`; covers the contract-text sync presence (RED at authoring: zero hits; the skill's two existing `worktree_policy` mentions are the docs-branch sync section, a different surface, so the generic key grep is not red and is not the evidence needle)
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers the fixture criteria

- [x] Sync the done skill's pre-commit sweep gates paragraph's (between Step 2.75 and Step 3) post-landing-staging description with the placement-aware permit and the remedy split, amending only that gate's description span and keeping the wording key-free (no `worktree_policy` literal, so the done-skill Step 2 count pin holds): the gate exempts manifest-owned unstaged paths under a primary-resident facts placement (`primary` or `primary-execution`), counts them informationally, keeps the strict unstaged leg under every other reading, and splits the refusal remedies by ownership class so an owned path is offered the misdirected-write check and staging, never a destructive remedy [class: IMPLEMENTATION_REQUIRED]
- [x] Pin the placements as named self-contained test items in scripts/test_done_sweep_gates_lib.py beside the seven existing `test_post_landing_staging_*` fixtures, reusing the suite's helpers (`sweep_env`, `mktemp_repo`, `post_landing_allowlist_file`, the manifest seeding helper, the primary-resolution fixture's shape; facts files are written manually as established fixture practice): [class: REPOSITORY_TEST]
- [x] `test_post_landing_staging_primary_owned_unstaged_pass`: given declared-`primary` facts and a manifest-owned unstaged plan path, expects rc 0 with the informational count naming the path and the amended base parenthetical [class: REPOSITORY_TEST]
- [x] `test_post_landing_staging_primary_execution_owned_unstaged_pass`: given declared-`primary-execution` facts (the witnessed placement) and the same owned unstaged state, expects rc 0 with the same message shape [class: REPOSITORY_TEST]
- [x] `test_post_landing_staging_unconfigured_owned_unstaged_refusal`: given no facts file and the same owned unstaged state, expects rc 1 with the misdirected-write check first, staging named as the sanctioned resolution, and neither the bare restore escape nor the reland path for the owned path [class: REPOSITORY_TEST]
- [x] `test_post_landing_staging_mixed_residue_refusal_split`: given an owned and an unowned unstaged path in one closeout under a non-primary reading, expects rc 1 naming the owned path with the owned-class remedies and the unowned path with today's recipe [class: REPOSITORY_TEST]
- [x] `test_post_landing_staging_malformed_policy_strict`: given a facts file declaring an out-of-vocabulary `worktree_policy` value and an owned unstaged path, expects rc 1 (strict) [class: REPOSITORY_TEST]
- [x] `test_post_landing_staging_primary_unresolvable_manifest_strict`: given declared-`primary` facts and no resolvable run manifest, expects rc 1 strict with the unresolvable-record warning, unchanged from the existing strict fixture's shape [class: REPOSITORY_TEST]
- [x] `test_post_landing_staging_owned_allowlist_overlap_single_count`: given an owned unstaged path that also sits on the record-only allowlist under declared-`primary` facts, expects rc 0 with the path named exactly once in the allowlist clause and never in the owned-unstaged clause [class: REPOSITORY_TEST]
- [x] The seven existing fixtures stay green unchanged (the clean pass, staged refusal, dirty refusal, untracked warning, primary resolution, unresolvable strict, and lock-held indeterminate fixtures carry no facts file today and keep today's strict behavior) [class: REPOSITORY_TEST]
- [x] Run → GREEN: the sweep-gate suite OK, the pins suite exits 0 with OUTCOME: pass, the em-dash added-lines scan exits 0, the public hygiene scan exits 0, and `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-post-landing-staging-placement-awareness.md` exits 0 on the final bytes [class: REPOSITORY_TEST]
- [x] Commit: `fix: post-landing-staging gate placement documented and pinned for all worktree policy forms` [class: IMPLEMENTATION_REQUIRED]

## Disposition

- Outcome: executed; the landing squash commit is the landing witness on main.
- Tasks 1-2 complete; all checkboxes ticked; implementation commits 8b5face9 (Task 1: placement-aware unstaged leg, informational counting, amended base parenthetical, rc-1 remedy split, docstring contract) and 7a917d63 (Task 2: key-free done-skill sync, seven new named fixtures).
- Exec review: r4 fresh adversarial ready=yes zero blocking (two Low non-blocking observations recorded: the plan's "seven existing fixtures" names a subset of nine on live bytes, all green unchanged; a checkbox-marker-only owned plan path can be named in two pass-message clauses under a primary-resident placement, both statements true and plan-conformant); the readiness digest-stale reading on the ticked bytes is the designed mid-loop state resolved by this plan's r5 digest-binding probe; records + sidecars at docs/reviews/2026-10-05-plan-review-post-landing-staging-placement-awareness-r{4,5}.md.
- Gates on the exec bytes: sweep suite 182 passed + 3 subtests under the venv runner; pins OUTCOME: pass (no re-key, done-skill worktree_policy count holds at 2); em-dash added-lines exit 0; hygiene OUTCOME: pass.
- Deferred residuals: none.
