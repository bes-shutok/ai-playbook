# Plan: live claims-directory sweep exemption and authoring-claim refresh mechanics

Language guidelines: `projects/.ai-playbook/python_guidelines.md` (the touched script is Python; plain `python3` for repo-local trusted scripts).

Backlog origin: docs/history/backlog/2026-11-12-authoring-claim-sweep-exemption-and-refresh-recipe.md
Driving force: efficiency
Plan review record: the staging series {reviews_dir}/2026-11-13-plan-review-authoring-claim-sweep-exemption-and-refresh-recipe-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1h
Executed: no

Authoring claim: 2026-11-12-authoring-claim-sweep-exemption-and-refresh-recipe.md (session sess_bcd3b5a1-8c74-472d-aeb0-dd9272ac4431)

## Terms

- docs/tmp sweep: the `docs-tmp-sweep` landing gate (`gate_docs_tmp_sweep` and its helpers in `scripts/done_sweep_gates_lib.py`) that prunes `docs/tmp` scratch at done boundaries.
- drain arms: the never-synced scratch retention arms of the docs/tmp sweep whose unlinking is decided by the posture knob below.
- drain posture: the `docs_tmp_drain_arms` facts knob (report-only | on | off) deciding whether the drain arms unlink or only report.
- authoring claim: the five-frontmatter-line file under `docs/tmp/authoring-claims/` that keys a plan-authoring run to a session (`session:`/`item:`/`created:`/`updated:`/`runtime_id:`).
- execution claim: the same-lifecycle sibling file under `docs/tmp/execution-claims/` for plan-execution runs.
- refresh: the duty every authoring session follows of updating the claim file's `updated:` line at plan writes, review-round boundaries, and phase boundaries.
- ownership-checked rebuild: the repair for a failed claim shape check, performed only by the session owning the claim: recreate the claim noclobber preserving the original `created:`, or rebuild the five lines in place after re-reading the `session:` line; never a foreign session's repair.
- claim discovery guards: the checkers that read live claims to decide liveness and freshness (the authoring-plans liveness checker, the closeout migrate reader).
- freeze transaction: the done-boundary commit that lands a PLAN-PROMPTS entry's `Frozen:` line (the log's write boundary rule transaction).
- noclobber-create contract: the claim create's O_EXCL-style create that refuses when the file already exists, preserving a foreign writer's witness.
- staleness horizon: the freshness bound (one cadence period) after which a claim stops reading as live to the discovery guards.
- protected scratch: the docs/tmp entries kept by name in the sweep's retention policy (the existing prefix/directory predicate).
- marker pruning: the run-start marker cleanup the docs/tmp sweep performs under the done-session directory.
- byte payment: the anti-growth rule that a change growing a capped skill file deletes equivalent bytes in the same change.

## Why

An authoring run's claim file is the freshness witness the claim discovery guards read, but the docs/tmp sweep's retention policy has no named entry for the two live claims directories: their survival rides an unnamed catch-all, so retention is incidental and a retention-policy change (the drain posture, the horizon) can reclassify them as deletable, which the origin row witnessed as a mid-run claim removal. Separately, the claim duty prescribes the refresh fields but no refresh mechanics, so every session improvises line surgery on the same five lines; twice in the witnessed window a refresh corrupted the frontmatter and needed a manual rebuild.

## Gist & Examples

TLDR: the docs/tmp sweep keeps the live claims directories by name and the authoring-claim refresh prescribes exact line-replace-plus-shape-assert mechanics, removing the witnessed claim-loss and frontmatter-corruption repairs from every authoring run (efficiency).

Before: a claim created at 12:55Z is gone by 13:17Z because sweep legs classified it as ownerless tmp content, and a refresh writes a second `updated:` line over the `runtime_id:` line; both losses surface only when a guard or the session notices, and each costs a manual recreate or an ownership-checked rebuild.

After: the sweep reports the claims directories as kept with a named claims-directory reason and never enumerates inside them under either drain posture; a refresh substitutes exactly the `updated:` line in place and asserts the five-line frontmatter shape before returning, so a corrupted refresh is caught at the refresh boundary instead of by a later guard.

Edge cases: a symlink named like a claims directory stays on the conservative catch-all path (never followed, never opened); a genuinely abandoned run's claim-shaped litter is retained by the drain arms, which is the origin row's recorded bounded false-positive cost (the staleness horizon the discovery guards already apply bounds the litter's influence).

## Outcome

The live claims directories become named-retention surfaces in the docs/tmp sweep, and claim refreshes carry prescribed mechanics.

- An authoring run's claim file survives the freeze transaction's sweep legs under both drain postures.
- A corrupted refresh fails the five-line shape assert at the refresh boundary and is repaired by the ownership-checked rebuild, never discovered by a later guard.
- The exemption is a static directory predicate named beside the drain-arms policy knobs, so future drain-arm evolution cannot silently reclassify the claims directories as deletable.

Gate delta: one deletion-set narrowing in the docs/tmp sweep (the two live claims directories leave the sweep's would-be deletion surface by name, replacing the unnamed catch-all keep) and one prose-only requirement addition to the existing claim-refresh recipe (in-place `updated:` line substitution plus the five-line shape assert), priced by the origin row's witnessed evidence (observed item 1: the mid-run claim removal; observed item 2: two frontmatter corruptions needing manual rebuilds). The origin body records the class-default alternatives as open options; this plan refuses them because: adoption-instead-of-exemption needs new claim-to-session matching logic while the exemption is the static predicate the retention policy already supports; a sweep-side-only fix (refresh recipe without the sweep arm) leaves the sweep defect armed for every future run; claims-directory relocation out of docs/tmp turns per-run ephemeral state into repo residue and breaks the noclobber-create contract. Extension of `PROTECTED_SCRATCH_DIRS` is likewise refused: that constant also gates the never-synced regular-file arm, so folding the claims names in would newly protect claim-named top-level regular files from the drain, while the claims exemption is directory-only with its own operator-facing keep reason. One pinned-span expectation moves in the same change (the checkpoint-duty pin count in `scripts/check_maintenance_pins.sh` re-homes from 2 to the post-fold 1). No gate, validator, lock, ledger, refusal class, or required ceremony is added, and none is removed.

## Assumptions

- assume the exemption lands in the top-level entry classification of `_gate_docs_tmp_sweep_with_window`; basis: source read 2026-11-13, the main loop at `scripts/done_sweep_gates_lib.py` keeps unknown top-level directories at the unnamed catch-all ("unclear ownership or active work") and the drain arms enumerate only top-level regular files, so one named directory arm covers both postures.
- assume the witnessed deletion's exact historical leg is not re-derivable from current code; basis: the origin row's observed item 1 (witnessed 2026-11-10 through 2026-11-12, the retention policy evolving in that window) plus the source read above; this plan names the exemption so no present or future leg classifies the claims directories as deletable, rather than re-deriving the historical leg.
- assume the refresh mechanics insert immediately after the refresh-cadence sentence of the AUTHORING CLAIM duty paragraph; basis: the paragraph's own ordering (refresh duty sentence, then the delete-boundary sentence whose text must survive verbatim as the insertion tail).
- assume the byte payment deletes the standalone CONTEXT CHECKPOINTS paragraph (a second statement of the same duty the template block already carries), folding its unique clause (recording `no-primitive` when no executable meter is exposed) into the in-block sentence; basis: byte comparison of the two spans in `agents/skills/maintenance/template-authoring.md`, 2026-11-13.
- assume no documentation impact beyond the touched skill file; basis: the sweep's keep-reason strings are operator-facing console output only, and no README or registry row carries the claims-directory retention contract.

Decision points requiring a grill: none remain.

## Standing constraints

- Skill text anti-growth rules bind this plan's Task 3: the change that grows `agents/skills/maintenance/template-authoring.md` past its cap deletes equivalent bytes in the same change; `scripts/skill_text_budget.py --check` (blocking posture, exit 0) is the enforcing gate, and the file's byte count must not exceed its pre-change value.
- Task 3 touches a pinned file: `bash scripts/check_maintenance_pins.sh` (exit 0 required) runs at the Task 3 boundary with the pin re-homing in the same commit, so the tree never carries the broken intermediate state.
- Every changed file stays inside the Review Scope's explicit must-fix set; the drain arms' existing refusal semantics (bounded retry, keep-when-uncertain, quarantine-then-restore) are frozen.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the sweep keeps both claims directories with the named reason under the report-only and on postures, and never enumerates inside them; the focused suite selectors pass.
- regression safety: the pre-existing sweep behaviors (protected scratch, never-synced drain, marker pruning) keep their tests green; the catch-all keep still applies to everything the named arms do not match.
- byte payment: `scripts/skill_text_budget.py --check` exits 0 and `agents/skills/maintenance/template-authoring.md` byte count does not exceed its pre-change value.

**Done when:**
- `pytest scripts/test_done_sweep_gates_lib.py -q -k docs_tmp_sweep` exits 0 with the three new exemption tests included.
- `pytest scripts/test_done_sweep_gates_lib.py -q -k "never_synced or drain"` exits 0.
- `pytest scripts/test_worktree_closeout_migrate.py` and `pytest scripts/test_parallel_work_regressions.py` exit 0 (both invoke the modified gate directly).
- `pytest scripts/test_authoring_plans_liveness.py -q` exits 0.
- `python3 scripts/skill_text_budget.py --check` exits 0 with template-authoring.md byte count at or below its pre-change value.
- `bash scripts/check_maintenance_pins.sh` exits 0 (the re-homed pin included).
- The em-dash added-lines scan and the public hygiene scan exit 0 over the changed set.

**Ship when:**
- none (repository-internal change; no deployed or human-owned release surface).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (Task 2)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (Task 1)

**Skill text:**
- `agents/skills/maintenance/template-authoring.md` (Task 3)

**Pins suite:**
- `scripts/check_maintenance_pins.sh` (Task 3)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/worktree_closeout_migrate.py`; reason: it only reads the claims directories keep-side for worktree liveness (no deletion leg), and its reader contract is unchanged.
- `scripts/check_authoring_plans_liveness.py`; reason: review-only reference for the five-line shape the recipe asserts; the checker is unchanged by this plan.
- `scripts/done_sweep_gates.sh`; reason: thin execution wrapper over the lib; no policy lives there.
- `docs/maintenance/demoted-sweep-arms.md`; reason: records other gates' demotion history; untouched.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
( cd "$REPO" && PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q -k docs_tmp_sweep ) || { echo "sweep suite selector failed"; exit 1; }
( cd "$REPO" && PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q -k "never_synced or drain" ) || { echo "drain-arm neighborhood failed"; exit 1; }
( cd "$REPO" && PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_worktree_closeout_migrate.py -q ) || { echo "closeout migrate suite failed"; exit 1; }
( cd "$REPO" && PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_parallel_work_regressions.py -q ) || { echo "parallel work regressions failed"; exit 1; }
( cd "$REPO" && PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_authoring_plans_liveness.py -q ) || { echo "claim liveness suite failed"; exit 1; }
( cd "$REPO" && python3 scripts/skill_text_budget.py --check ) || { echo "byte-budget gate failed"; exit 1; }
CURRENT=$(wc -c < "$REPO/agents/skills/maintenance/template-authoring.md"); test "$CURRENT" -lt 54277 || { echo "template-authoring.md must stay below run-start base: $CURRENT >= 54277"; exit 1; }
( cd "$REPO" && bash scripts/check_maintenance_pins.sh ) || { echo "maintenance pins suite failed"; exit 1; }
( cd "$REPO" && bash scripts/scan-public-hygiene.sh ) || { echo "hygiene scan failed"; exit 1; }
( cd "$REPO" && bash scripts/check-no-em-dash.sh added-lines --base 2d77380f76db68d11d71c43efa49ed39e8599e3f ) || { echo "em-dash added-lines scan failed"; exit 1; }
grep -qF 'DOCS_TMP_LIVE_CLAIMS_DIRS' "$REPO/scripts/done_sweep_gates_lib.py" || { echo "named exemption constant missing"; exit 1; }
grep -qF 'replace exactly the `updated:` line in place' "$REPO/agents/skills/maintenance/template-authoring.md" || { echo "refresh mechanics sentence missing"; exit 1; }
grep -qF 'delete that primary-checkout claim file only at the placement' "$REPO/agents/skills/maintenance/template-authoring.md" || { echo "insertion tail lost"; exit 1; }
grep -qF 'no-primitive' "$REPO/agents/skills/maintenance/template-authoring.md" || { echo "no-primitive clause lost in byte payment"; exit 1; }
if grep -qF 'CONTEXT CHECKPOINTS, a standing duty for every step block of this run' "$REPO/agents/skills/maintenance/template-authoring.md"; then echo "duplicate standalone checkpoint paragraph still present"; exit 1; fi
```

(The strict `<54277` byte-count check uses template-authoring.md's pre-change size at this run's recorded base commit `bc7ea61687309b529f29da744bc670eec1abebae`, re-derived during execution after the authoring-time 51559 value at `303fc9321` proved stale. Task 3 still requires a net-negative byte delta against this base. The em-dash base is this worktree's verified merge-base `2d77380f76db68d11d71c43efa49ed39e8599e3f`; re-derive it with `git merge-base HEAD main` if the base moves before execution.)


Execution-time record (2026-11-18, resume session sess_0df7e07a, worktree 2026-11-16-live-claims-sweep): full Validation Commands battery over branch tip 464015b1b, all GREEN - sweep selector 58 passed; never_synced-or-drain 15 passed; test_worktree_closeout_migrate 448 passed + 43 subtests; test_parallel_work_regressions 3 passed; test_authoring_plans_liveness 13 passed; skill_text_budget --check blocking posture OUTCOME: pass (advisory ratchet rows pre-existing); template-authoring.md measured 54211 bytes < 54277 run-start base (net-negative delta held); check_maintenance_pins.sh exit 0; scan-public-hygiene.sh exit 0; check-no-em-dash.sh added-lines --base 2d77380f76db68d11d71c43efa49ed39e8599e3f exit 0 (merge-base re-derived fresh at execution time, matches the recorded base); all four post-state pins present; duplicate-paragraph grep absent.

## Validation preamble (authoring-time record)

Execution-time correction (2026-11-16): the original 51559-byte value is confirmed at `303fc9321`, but the recorded execution base `bc7ea61687309b529f29da744bc670eec1abebae` and the current file both measure 54277 bytes; `main` has no later delta to this file. The Task 3 edit projects to 54211 bytes (54,277 - 531 deleted + 389 inserted + 13 field-list bytes + 63 folded-clause bytes), so it remains net-negative. The command and Task 3/4 criteria now enforce a final count below 54277. The em-dash validation base was separately corrected to this worktree's verified merge-base `2d77380f76db68d11d71c43efa49ed39e8599e3f` after review found that `303fc9321` was only the earlier authoring-worktree base.

Rule 29 preflight executed 2026-11-13 from the authoring worktree, base `303fc9321`, before the first review round. Recorded outcomes: `pytest -k docs_tmp_sweep` exit 0 (55 collected, all pre-existing green); `pytest -k "never_synced or drain"` exit 0 (14 collected); `pytest scripts/test_authoring_plans_liveness.py` exit 0; `skill_text_budget.py --check` exit 0 (0 ceiling breaches, blocking posture; template-authoring.md at exactly 51559 bytes); byte-count bound check pass (51559 <= 51559); `scan-public-hygiene.sh` exit 0 (`OUTCOME: pass`); `check-no-em-dash.sh added-lines --base 303fc9321` exit 0 (0 substitutions). Post-state pins executed RED-today per rule 19: `DOCS_TMP_LIVE_CLAIMS_DIRS` absent (expected RED until Task 2); the refresh-mechanics span absent (expected RED until Task 3); the tail span `delete that primary-checkout claim file only at the placement` present (GREEN, pre-existing); the negated duplicate-paragraph grep fires today (expected RED until Task 3's deletion); the `no-primitive` survival pin is GREEN today (the clause lives in the paragraph Task 3 deletes, so the pin stays GREEN only when the fold lands in the same change as the deletion). Rule 22 mechanical audit: `bash -n` over the extracted Validation Commands block clean; each pinned span extracted and verified to occur in its prescribed task snippet (the Task 3 quoted span carries the exact grep pin text; the byte-count bound's derivation noted beside the command). Pins suite at authoring time: not run (the authoring delta is the plan file only); the suite's Task-3-boundary mandate is carried by Standing constraints and Task 3's re-home item, and the suite's checkpoint-duty pin count is 2 today, flipping to 1 through Task 3's same-change re-home. Pre-round gate outcome over the current bytes: exit 0, final line `OUTCOME: pass`, verdict `readiness PRE-ROUND OK`, warning-only FILES-COVERAGE rows only, measured against the plan digest recorded in the round staging sidecar (`source_digest`), which is the bytes binding for this outcome; any later fold re-runs the gate and the fresh round sidecar digest carries the new binding.


### Task 1: RED, pin the claims-directory exemption in the sweep suite

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `gate_docs_tmp_sweep` in `scripts/done_sweep_gates_lib.py`

- [x] Add `test_docs_tmp_sweep_keeps_live_claims_directories_by_name` beside the existing docs-tmp-sweep tests, using the file's existing `make_repo`/`write_facts`/`sweep_env`/`ctx_for`/`run_gate` harness. [class: REPOSITORY_TEST]
- [x] That test: given `docs/tmp` carries `authoring-claims/` (fresh five-line claim inside) and `execution-claims/` (stale claim inside) with the drain posture at its report-only default, expects exit 0, both directories kept with the live-claims-directory reason, and no removed row under either directory. [class: REPOSITORY_TEST]
- [x] Add `test_docs_tmp_sweep_drain_posture_on_never_enumerates_claims_directories` beside them with the same harness. [class: REPOSITORY_TEST]
- [x] That test: given the facts knob `docs_tmp_drain_arms = "on"` with a stale never-synced top-level scratch file plus stale claim files inside both claims directories, expects the scratch removed per the posture, every claim file inside the claims directories surviving, and no gate row naming a path under either claims directory. [class: REPOSITORY_TEST]
- [x] Build that test on the sibling drain-test setup so its removal expectation is deterministic on birthtime and non-birthtime platforms: `_write_facts_with_knob` for the knob, `_seed_never_synced_window`, `_add_docs_branch_files`, `_seed_stale_survivor`, and the same `_entry_birth_epoch` -> `st_mtime` monkeypatch the sibling drain-on test carries. [class: REPOSITORY_TEST]
- [x] That test also pins the discriminating reason: both directory kept rows carry the live-claims-directory reason and the catch-all reason string does not appear for them, so a partial implementation keeping the dirs via the unnamed catch-all fails. [class: REPOSITORY_TEST]
- [x] Add `test_docs_tmp_sweep_symlink_named_like_claims_dir_keeps_catch_all_path` (a green-at-RED regression pin, sibling of the suite's existing top-level-symlink test, on the same `make_repo`/`write_facts`/`sweep_env`/`ctx_for`/`run_gate` harness): given `docs/tmp/authoring-claims` is a symlink to an external sentinel directory, expects exit 0, the link still a symlink, the sentinel bytes intact, and the kept row carrying the catch-all reason rather than the claims-directory reason. [class: REPOSITORY_TEST]
- [x] Run → expect RED: the whole `docs_tmp_sweep` selector reports tests 1 and 2 failing at their reason pins (the exemption arm does not exist: the directories land in the unnamed catch-all with a different keep reason) while the symlink test passes as its green-at-RED regression pin and every pre-existing test in the selector stays green. [class: REPOSITORY_TEST]
- [x] Commit: `test: pin the live claims directories' named exemption in the docs/tmp sweep` [class: REPOSITORY_TEST]

### Task 2: GREEN, implement the named exemption

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/done_sweep_gates_lib.py`

Primary class anchors:
- `gate_docs_tmp_sweep` in `scripts/done_sweep_gates_lib.py`
- `_gate_docs_tmp_sweep_with_window` in `scripts/done_sweep_gates_lib.py`

- [x] Add the named constant `DOCS_TMP_LIVE_CLAIMS_DIRS = ("authoring-claims", "execution-claims")` beside the drain-arms policy knobs block, with a one-line comment citing the origin row as the witnessed incident and naming the order contract: index `[1]` is the spelling `EXECUTION_CLAIMS_REL` derives, so keep `execution-claims` last. [class: IMPLEMENTATION_REQUIRED]
- [x] Rewrite the module's existing `EXECUTION_CLAIMS_REL` to derive its final path segment from `DOCS_TMP_LIVE_CLAIMS_DIRS[1]` so the module carries one spelling of the execution-claims directory name (import-order safe: the constant block executes before the existing definition). [class: IMPLEMENTATION_REQUIRED]
- [x] In `_gate_docs_tmp_sweep_with_window`'s main entry loop, add one directory arm before the protected-scratch arm: a top-level entry that is a directory (through the loop's existing no-follow stat) whose name is in `DOCS_TMP_LIVE_CLAIMS_DIRS` is appended to `kept` as `<rel> (live claims directory; retained by name; the owning session deletes its files at closeout and stale claims decay via takeover)` and the loop continues without enumerating into it. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a symlink named `authoring-claims` at the tmp top level, expects it stays out of the named arm (the no-follow stat does not classify it as a directory), is never opened or followed, and lands on the existing conservative keep path; Task 1's third test pins this witness. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the whole `docs_tmp_sweep` selector passes with the two Task 1 reason-pinned tests flipped and the symlink regression pin still green; the `never_synced or drain` selector passes (15 collected after Task 1's additions). [class: REPOSITORY_TEST]
- [x] Commit: `feat: exempt the live claims directories from the docs/tmp sweep deletion set` [class: IMPLEMENTATION_REQUIRED]

### Task 3: prescribe the claim-refresh mechanics with the same-change byte payment

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/maintenance/template-authoring.md`
- `scripts/check_maintenance_pins.sh`

Primary class anchors: none, this task edits skill text in one file and pays the byte budget in the same file.

- [x] In the AUTHORING CLAIM duty paragraph, locate the insertion point immediately after the refresh-cadence sentence ending `without a refresh;`; the tail beginning `delete that primary-checkout claim file only at` must survive verbatim after the insertion (rule 40 boundary: the Validation Commands block pins both spans). [class: IMPLEMENTATION_REQUIRED]
- [x] Insert there one sentence carrying this exact span: "replace exactly the `updated:` line in place (one targeted substitution keyed on the line's `updated: ` prefix, never a whole-file rewrite, never a second `updated:` line), then assert the five-line frontmatter shape (session:, item:, created:, updated:, runtime_id:, each exactly once, in that order) before returning; an assert failure is repaired by the ownership-checked rebuild first." [class: IMPLEMENTATION_REQUIRED]
- [x] Byte payment in the same file and change: fold the standalone duty paragraph's unique clause (recording `no-primitive` when no executable meter is exposed) into the in-block CONTEXT CHECKPOINTS sentence, then delete the standalone paragraph beginning `CONTEXT CHECKPOINTS, a standing duty for every step block of this run:` in its entirety. [class: IMPLEMENTATION_REQUIRED]
- [x] In the template block's compact AUTHORING CLAIM DUTY field list, add `runtime_id:` so the payload-side summary carries the same five-field contract the inserted assert pins (the byte delta stays net-negative). [class: IMPLEMENTATION_REQUIRED]
- [x] Re-home the pins suite's checkpoint-duty pin in the same commit: the pin counting the checkpoint telemetry span in `agents/skills/maintenance/template-authoring.md` moves from expecting 2 occurrences to expecting 1 (the in-block sentence), its comment naming the folded paragraph as the removed occurrence. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the byte-budget gate exits 0 with the file's byte count strictly below the run-start base of 54277 with a net-negative same-change delta; the pins suite exits 0 (the re-homed pin included); the pinned spans and the negated duplicate-paragraph grep from the Validation Commands block pass against the edited file. [class: REPOSITORY_TEST]
- [x] Commit: `maintenance: prescribe claim-refresh mechanics, re-home the checkpoint pin, pay the byte budget` [class: IMPLEMENTATION_REQUIRED]

### Task 4: full validation battery

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files: none (validation and recording only).

Primary class anchors: none, this task runs the Validation Commands block and records outcomes.

- [x] Run the full Validation Commands block from the worktree root; record every command's outcome in the Validation preamble, including the pins suite and the two gate-invoking suites. [class: REPOSITORY_TEST]
- [x] Verify the recorded template-authoring.md byte count is strictly below the run-start base of 54277 and note the actual number beside the outcome. [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

Origin row `docs/history/backlog/2026-11-12-authoring-claim-sweep-exemption-and-refresh-recipe.md` (Status was covered-pending-execution): executed and landed by resume run 20261118T171526Z-ae444672cd61 (sess_0df7e07a), landing commit 78f2c5368 — the sweep keeps the live claims directories by name with a live-claims-directory reason and never enumerates inside them under either drain posture; the authoring-claim refresh prescribes exact `updated:`-line substitution plus the five-line frontmatter shape assert with the ownership-checked rebuild remedy. Row deleted covered by this archived twin; the sibling cluster row 2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md's Cluster pointer tidied in the same pass.
