# Plan: reconcile the done commit's declared stage set into the landing sweep's ownership

Authoring claim: docs/tmp/authoring-claims/2026-10-14-done-ownership-post-setup-learn-edits.md (session sess_17e58dd5-8e5f-4d81-bec6-330c62ac65e0)

Backlog origins (scope of record):
- docs/history/backlog/2026-10-14-done-ownership-contract-post-setup-learn-edits.md

Driving force: code-quality
(the plans-skill closed taxonomy tag; the motive is reliability - the witnessed refusal stops authorized closeout work - recorded here because the taxonomy has no reliability entry and the non-principle justification rule requires the motive on record)

Plan review record: the staging series .ai-playbook/reviews/*-plan-review-done-ownership-post-setup-learn-edits-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 2h total, largest task 1h

## Terms

- Declared set: the `--stage PATH...` vector `cmd_commit` accepts and stages by explicit pathspec (scripts/done_run.sh commit step 1), gitignored paths reported and never staged.
- Declared-stage channel: the environment input `DONE_SWEEP_DECLARED_STAGE_PATHS` that `cmd_commit` composes for its own landing-sweep invocation only (newline-separated declared paths; paths containing a newline excluded with one named warning line; actively unset for the subprocess when the declared set is empty), consumed by that invocation's `post-landing-staging` gate and nothing else; it cannot outlive the invocation, so no staleness, keying, or cross-run lifecycle exists.
- Primary checkout: the first `git worktree list --porcelain` entry, which `gate_post_landing_staging` inspects regardless of the invoking checkout; a closeout run in an ad-hoc worktree stages into that worktree's own index, which the primary's status never shows.
- Checkout-shape guard: the consumption condition this plan adds - the channel is read only when the gate's resolved primary checkout equals the gate context's repo root (the invoking checkout), the shape where the declared set is the shape the gate inspects; any other shape ignores the channel with one named warning line.
- Ownership union: the extension of `gate_post_landing_staging`'s owned computation (scripts/done_sweep_gates_lib.py): owned stays the manifest's union of `owned_paths`, `owned_plan_paths`, `owned_review_paths`, plus the channel's paths when the channel is set, a manifest resolved, and the checkout-shape guard holds; channel lines are normalized through the same repo-relative normalization the manifest claim legs receive (`_manifest_review_rel`), blank lines skipped, and the record-only allowlist is always subtracted.
- Record-only allowlist: the gate's `RECORD_ONLY_ALLOWLIST` (projects/.ai-playbook/development_lessons.md), the never-commit class that no landing or closeout step may stage, claim for staging, declare, or commit; the allowlist's only effect is keeping its unstaged dirt out of every refusal.
- Adopting-boundary sentence: the existing manifest-resolved refusal suffix that recovers a staged path created after Step 0 by closing and reopening the boundary.
- Post-setup live edit: a modification to a tracked file authored after the setup manifest was written (the documented learn step's normal product), which no manifest claim set can own because the manifest is fixed at write time.
- Manifest fixed-at-write-time property: the existing ownership contract that the setup manifest's claim sets are never widened in place; preserved unchanged (the channel is an invocation-scoped input, not a manifest mutation).
- Landing sweep: `done_sweep_gates.sh landing`, the closeout's one sweep run inside `cmd_commit` step 12, whose `post-landing-staging` gate refuses staged residue outside the owned set.
- Done boundary: the setup-to-finalize run fence one done closeout holds on a checkout; teardown is the finalize-step release.
- Strict leg: the `post-landing-staging` gate's staged-residue refusal arm (rc 1), the only leg demotion program change 7 kept refusing.
- Claims recovery: the existing sanctioned recovery for a manifest owned-set omission (unstage, close the boundary, reopen a fresh boundary with complete `--owned-path` claims); distinct from the refusal message's adopting-boundary sentence, which is the only close-and-reopen construction the current message text carries and which this plan preserves verbatim.
- Start-dirt: a tracked path already dirty and unclaimed at Step 0; `gate_foreign_staging` refuses staging such paths regardless of any later declaration, by design (start-dirt protection is not declaration-bypassable).
- Vendored twin: the runtime-side copy of the done skill at `~/.agents/skills/done/SKILL.md`, synced per the repository guidelines' Vendored Asset Sync Rules.

## Why

The done skill's documented order is setup, then learn, then the commit run. Learn-authored edits to pre-existing tracked files always postdate the setup manifest, and the manifest's claim sets are fixed at write time, so the landing sweep's `post-landing-staging` gate reads the run's own learn edits as staged residue and refuses with `nothing committed` (the origin row's witnessed 2026-10-14 incident). The refusal message names no fitting remedy for this shape: probe-then-reland addresses landing residue, the restore escape is for dead residue, and the adopting-boundary sentence addresses new files, not modified ones; the working recovery (finalize the empty boundary, unstage, reopen with `--owned-path`, re-run the commit) costs a full boundary teardown plus a second sweep and is discoverable only from the gate's source. The commit step already knows exactly which paths it stages; handing that set to the sweep it invokes makes the documented order work without any boundary ceremony.

## Gist & Examples

TLDR: the done commit hands its declared `--stage` set to the landing sweep through an invocation-scoped environment input and the `post-landing-staging` gate unions that input into its owned computation behind a checkout-shape guard, so learn edits authored after setup land on the first boundary; declared force code-quality, motivated by reliability (the witnessed refusal stops authorized closeout work).

Before: a closeout whose learn step appends a witness to a backlog row and tightens a lessons-corpus entry after setup refuses at the landing sweep (rc=1, `nothing committed`), and the only working recovery is the undocumented finalize-unstage-reopen-recommit sequence with a full boundary teardown.
After: the same closeout (paths not dirty at Step 0, the witnessed shape) passes the sweep when the learn-edited paths are declared to `commit` via `--stage` and the record-only corpus append is left unstaged (permitted-dirty under the allowlist; it lands on a later boundary's Step 0 claim - declaration never lands it); the declared set rides the invocation-scoped channel the gate unions into ownership; an undeclared staged path still refuses, and the refusal names the declared-stage re-run beside the preserved adopting-boundary sentence. A declared path that was start-dirt at Step 0 still refuses at the foreign-staging gate and takes the claims recovery - declaration never bypasses start-dirt protection.
Edge cases: the channel lives only for the sweep invocation that declares it and is actively unset when the declared set is empty, so a re-run with a narrowed or empty declared set cannot inherit a previous attempt's paths; the checkout-shape guard ignores the channel in any worktree-resident closeout (the primary index the gate inspects is not the index the run staged), so a peer's staged paths in the primary keep their strict refusal there; a declared gitignored path is still reported and never staged, so it never reaches the channel; the record-only allowlist is subtracted, so declaring it keeps the strict refusal; the strict leg is refusal-class identical for undeclared staged paths; no new refusal class exists.

## Outcome

- A closeout following the documented setup-then-learn-then-commit order lands its learn-edited tracked files on the first boundary by declaring them at commit.
- The sweep's strict refusal survives refusal-class identical for staged paths that are neither manifest-owned nor declared; its manifest-resolved refusal arm names the declared-stage re-run as the post-setup remedy beside the preserved adopting-boundary sentence, and the no-manifest arm's text stays byte-identical.
- The manifest stays fixed at write time; the channel is the commit invocation's own input, consumed by the sweep it invokes in the primary-resident shape and by nothing else.
- No new refusal class, gate, fence, protocol layer, schema field, validator roster entry, file artifact, or ceremony exists; the change strictly removes one false-refusal class from an existing promoted gate and is priced by the origin row's witnessed incident.

Gate delta: no gate is added or removed; one existing promoted gate's owned computation gains an invocation-scoped input behind a checkout-shape guard (a false-positive-cost reduction on the witnessed class, admission line: incident `docs/history/backlog/2026-10-14-done-ownership-contract-post-setup-learn-edits.md`, expected catch frequency = every closeout whose learn edits pre-existing tracked files without pre-declared claims (witnessed once, deterministic per the documented step order), false-positive cost = zero new refusals (the union only widens ownership), no sunset needed because no new blocker exists). Narrowed-catch pricing: (1) declaring a path whose content carries a live peer's post-Step-0 co-edit lands that co-edit inside this run's commit - the accepted disposition is the documented session-owned co-edit residual (the done skill's judgment gate owns content-level co-editing; the commit-time pathspec and the Step 0 claim judgment remain the other nets); (2) in a worktree-resident closeout the channel would exempt a concurrent peer's coinciding staged paths in the primary checkout - this shape is excluded by the checkout-shape guard (the channel is consumed only when the gate's repo root is the primary checkout), so no true-catch class narrows there.

## Review Scope

- scripts/done_run.sh (the `cmd_commit` flow: staging step 1, the landing-sweep invocation at step 12, the commit at step 16, the Env paragraph)
- scripts/done_sweep_gates_lib.py (`gate_post_landing_staging` and its owned computation; `RECORD_ONLY_ALLOWLIST`; the primary-checkout resolution)
- scripts/done_sweep_gates.sh (the landing phase interface, unchanged)
- agents/skills/done/SKILL.md (the commit-step duty line)
- `~/.agents/skills/done/SKILL.md` (the vendored twin, synced in-change)
- scripts/test_done_run_wrapper.py, scripts/test_done_sweep_gates_lib.py (the validation surfaces)
- Out of review scope: the done skill's Steps 0-2, the manifest writer, the docs-branch sync, all other sweep gates (behavior unchanged)

## Assumptions

- assume the env channel lands (the commit step hands its declared set to the sweep it invokes; the gate consumes it behind the checkout-shape guard) rather than the origin row's second arm (a Step 0 pre-declaration duty) or a persisted sidecar file; basis: the origin row's Expected names the commit-side reconciliation as its first acceptable arm, the channel is the only shape that removes the boundary-teardown recovery cost for arbitrary learn-edited paths (a pre-declaration duty cannot enumerate the backlog row a witness append will touch), and the r1 review's blocking findings (record staleness across re-runs, avoidable coordination structure) both dissolve when the channel cannot outlive its invocation. The dispatching PLAN-PROMPTS entry's rejected alternatives bar three things - the in-place manifest widening, the destroy-and-restore escape, and the learn-before-setup reordering; of these only the widening constrains this mechanism-shape choice, and this arm avoids it. The entry's "no new state surfaces" constraint is carried undefined; this plan reads it as targeting scheduler/state-schema surfaces (which it does not touch) - that gloss is this plan's interpretation.
- assume the channel is not a state surface; basis: it is an environment variable scoped to one subprocess invocation, leaving no artifact on disk (the reading recorded in the assumption above).
- assume the trust anchor for the channel is the runner process itself (the same process composes the commit and invokes the sweep); basis: the gate is a self-check inside the operator's own closeout boundary, the manifest's claim sets carry the same trust level, and the invocation scoping means a stale or foreign input cannot survive to another run.
- assume the gate consumes the channel only when a manifest resolved and the checkout-shape guard holds (the owned set exists and is inspected in the same checkout only in that case), keeping the no-manifest path byte-identical; basis: the gate's existing strict arm and its pinned-text test, plus the r2 cross-checkout finding (a worktree-resident run's staged set never appears in the primary index the gate inspects, so channel consumption there would only exempt coinciding peer paths).
- assume the refusal-message addition is one sentence inside the manifest-resolved refusal arm, and that the origin Expected's "the refusal message should name the claims remedy for post-setup modifications" clause is deliberately superseded by the declared-stage remedy (the claims recovery cannot be a message line for this shape because the witnessed recovery is the teardown sequence itself, which no refusal should direct an operator into when a one-flag re-run lands the same set); basis: the origin row's Expected intent (the recovery stops requiring gate-source reading) and the r1 review's stale-remedy-reference finding.
- assume the done skill text change is one duty line at the commit-composition step plus the vendored twin sync; basis: the origin row's Skill/step naming `agents/skills/done/SKILL.md` and the vendored-sync rules requiring the twin to land in the same change.
- assume the wrapper suite and the sweep-gates lib suite are the validation surfaces, the lib suite invoked through pytest; basis: scripts/test_done_run_wrapper.py (unittest) and scripts/test_done_sweep_gates_lib.py (pytest, no main block - the bare invocation runs nothing) are the existing suites covering `cmd_commit` and `gate_post_landing_staging`.
- assume the learned staged-set observation stays in the primary-resident shape only; basis: the origin incident was a primary-resident closeout (the manifest, the lock, and the staged residue all lived in the primary), and the r2 review verified the gate reads only the primary index.

Decision points requiring a grill: mechanism shape (persisted run-keyed sidecar vs invocation-scoped env channel): resolved to the env channel by review r1 findings F2 and F4 (stale-record ownership widening; yagni coordination structure), 2026-10-14, affected sections: Terms, Task 1, Task 2, Task 5; the recorded basis for accepting the panel's findings in place of a separate operator grill is the review panel substitution itself, marked here explicitly. Checkout-shape guard (consume the channel only when the gate's repo root is the primary checkout): resolved by review r2 findings F2 (two-worker convergent), 2026-10-14, affected sections: Terms, Task 2, Gate delta. Refusal-remedy vocabulary: resolved by review r1 finding F3 (the cited close-and-reopen sentence does not exist), 2026-10-14, affected sections: Terms, Task 3, Assumptions. None remain.

## Tasks

### Task 1: hand the declared set to the sweep invocation
Files:
- scripts/done_run.sh
- scripts/test_done_run_wrapper.py
Primary class anchors: cmd_commit in scripts/done_run.sh

- [x] [class: IMPLEMENTATION_REQUIRED] In `scripts/done_run.sh` `cmd_commit`, immediately before the landing-sweep invocation (step 12), compose `DONE_SWEEP_DECLARED_STAGE_PATHS` from the final DECLARED set (after the step-8 formatting revert has resolved it): one path per line, newline-terminated.
- [x] [class: IMPLEMENTATION_REQUIRED] Exclude any declared path containing a newline from the channel with one named warning line (the gate keeps strict behavior for it); when the declared set is empty, actively unset the variable for the sweep subprocess rather than skipping the assignment, so no ambient export can leak into a channel-free sweep.
- [x] [class: IMPLEMENTATION_REQUIRED] The channel composition is bookkeeping in the existing commit flow comment block (the numbered stage list gains the channel note beside the sweep step's entry, and the Env paragraph's passthrough claim gains a note naming this one composed variable) and never gates or refuses: a construction failure prints a warning line and continues with the channel unset.
- [x] [class: REPOSITORY_TEST] Validation: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py -q` exits 0 including the new cases: a commit invocation with `--stage A B` passes the sweep while a companion run with one declared member missing refuses naming that missing path (proving the carried set from the refusal side); a gitignored `--stage` path produces the step-1 "gitignored path not staged" report line and stays unstaged.

### Task 2: consume the declared-stage channel in the gate's ownership union
Files:
- scripts/done_sweep_gates_lib.py
- scripts/test_done_sweep_gates_lib.py
Primary class anchors: gate_post_landing_staging in scripts/done_sweep_gates_lib.py

- [x] [class: IMPLEMENTATION_REQUIRED] In `scripts/done_sweep_gates_lib.py` `gate_post_landing_staging`, when the manifest resolved (owned is not None), read `DONE_SWEEP_DECLARED_STAGE_PATHS` from the environment (the `os.environ` house-style the lib's other `DONE_SWEEP_*` overrides use) behind the checkout-shape guard: consume only when the gate's resolved primary checkout equals the gate context's repo root; any other shape ignores the channel with one named warning line.
- [x] [class: IMPLEMENTATION_REQUIRED] The guard's equality compares realpath-resolved paths on both sides (git's printed primary path is not canonical under symlink aliasing); an unresolvable comparison fails closed to ignoring the channel.
- [x] [class: IMPLEMENTATION_REQUIRED] When consumed: split on newlines, skip blank lines, normalize each line through the same repo-relative normalization the manifest claim legs receive, subtract `RECORD_ONLY_ALLOWLIST`, and union the result into `owned`; any other reading (unset, empty, unresolvable manifest, guard not holding) contributes nothing, never an error, and the no-manifest path keeps today's strict behavior byte-identical.
- [x] [class: IMPLEMENTATION_REQUIRED] When the channel contributes paths, append one informational line to the gate result naming the count and the normalized paths (mirroring the existing allowed-dirty reporting), and reword both informational clauses (the staged and the unstaged leg renders, whose existing verbatim pins ride the same suite) from "owned by the current session manifest" to "owned by the session manifest or the invocation's declared-stage channel".
- [x] [class: IMPLEMENTATION_REQUIRED] Update the gate's docstring ownership paragraph: the owned set is the manifest claim union plus the invocation's declared-stage channel behind the checkout-shape guard; the manifest fixed-at-write-time property is restated as preserved (the channel is invocation-scoped, never a manifest edit).
- [x] [class: IMPLEMENTATION_REQUIRED] Document the channel variable in scripts/done_sweep_gates.sh's usage Environment help beside the other DONE_SWEEP_* overrides (a direct landing invocation inherits ambient values; the help names the cmd_commit composition as the production writer).
- [x] [class: REPOSITORY_TEST] Add `DONE_SWEEP_DECLARED_STAGE_PATHS` to the lib suite's sweep-env scrub list and to the wrapper fixture's scrub list, so each test's channel state is set only by its own fixture.
- [x] [class: REPOSITORY_TEST] Validation: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q` exits 0 including: a declared post-setup staged path passes; an undeclared staged path still refuses refusal-class identical (same rc, residue paths, recipes); a declared allowlist path still refuses.
- [x] [class: REPOSITORY_TEST] The same command also covers: an absolute-path channel line normalizes and passes; the channel set at a non-primary checkout is ignored with the warning line and the strict refusal stands; the channel set with no manifest refuses with the byte-identical no-manifest text.

### Task 3: name the declared-stage re-run in the manifest-resolved refusal arm
Files:
- scripts/done_sweep_gates_lib.py
- scripts/test_done_sweep_gates_lib.py
Primary class anchors: gate_post_landing_staging in scripts/done_sweep_gates_lib.py

- [x] [class: IMPLEMENTATION_REQUIRED] In `gate_post_landing_staging`'s manifest-resolved staged-residue refusal arm (the same condition that appends the adopting-boundary sentence), add one sentence naming the post-setup remedy: a live edit authored after setup (the documented learn step's product) is landed by re-running the commit with the path declared via `--stage`; the adopting-boundary sentence survives verbatim and the no-manifest arm's text stays byte-identical.
- [x] [class: REPOSITORY_TEST] Add the pins beside the existing fragment assertions: the adopting-boundary sentence captured verbatim as a literal, and the no-manifest refusal text pinned byte-identical to today's (the existing pinned-text test already covers the no-manifest arm at the gate level; this pin rides the new suite cases).
- [x] [class: REPOSITORY_TEST] Validation: the lib suite asserts the new sentence appears in the manifest-resolved refusal, the adopting-boundary sentence survives verbatim, and the no-manifest refusal text is byte-identical to today's.

### Task 4: one done-skill duty line plus the vendored twin
Files:
- agents/skills/done/SKILL.md
Primary class anchors: the done skill's commit-step composition text

- [x] [class: IMPLEMENTATION_REQUIRED] In `agents/skills/done/SKILL.md`'s commit-step text, add one duty line: declare every live edit this run intends to land via `--stage`, including the surfaces the learn step authored after setup (the lessons corpora, tightened backlog rows); the declared set reconciles into the landing sweep's ownership behind the primary-checkout shape guard. No step reordering, no new subsection.
- [x] [class: IMPLEMENTATION_REQUIRED] The same duty line excepts the shared record-only corpus: never declared, never claimed for staging, never committed - leave it unstaged; the allowlist keeps its unstaged dirt out of every refusal.
- [x] [class: IMPLEMENTATION_REQUIRED] Sync the vendored twin copy at `~/.agents/skills/done/SKILL.md` in the same change (byte-equal after the edit), per the repository guidelines' Vendored Asset Sync Rules.
- [x] [class: REPOSITORY_TEST] Presence pin (fails before the edit, passes after): `grep -qF "reconciles into the landing sweep's ownership" agents/skills/done/SKILL.md && grep -qF "reconciles into the landing sweep's ownership" "$HOME/.agents/skills/done/SKILL.md"` exits 0.
- [x] [class: REPOSITORY_TEST] Validation: `diff agents/skills/done/SKILL.md "$HOME/.agents/skills/done/SKILL.md"` exits 0; `bash scripts/check_maintenance_pins.sh` failing set is byte-identical before and after the change (baseline captured green on 2026-10-14; the done-skill pins target untouched spans).

### Task 5: end-to-end recovery replay
Files:
- scripts/test_done_run_wrapper.py
- scripts/test_done_sweep_gates_lib.py
Primary class anchors: the cmd_commit drive in scripts/test_done_run_wrapper.py

- [x] [class: REPOSITORY_TEST] Add one wrapper-level regression: a commit run whose declared `--stage` path was modified after the manifest was written passes the landing sweep on the first boundary (the origin incident's shape, primary-resident, record-only append left unstaged).
- [x] [class: REPOSITORY_TEST] Negative arm (remedy), staged out-of-band: with NO `--stage` at all (empty declared set) and the learn-edited path staged via `git add`, the sweep refuses rc 1 naming the new remedy sentence (the empty declared set skips the step-6 staged-scope guard and reaches the sweep).
- [x] [class: REPOSITORY_TEST] Negative arm (no inheritance): a second invocation in the same boundary with an empty declared set does not inherit the first attempt's channel.
- [x] [class: REPOSITORY_TEST] Negative arm (no-manifest): a commit with `--stage <post-setup path>` and no prior setup (no manifest) refuses rc 1 with the byte-identical no-manifest text and does not name the declared-stage remedy.
- [x] [class: REPOSITORY_TEST] Negative arm (normalization): one declared path given as an absolute path passes through normalization.
- [x] [class: REPOSITORY_TEST] Validation: `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py scripts/test_done_sweep_gates_lib.py -q` exits 0.

## Evaluation Criteria

Done when: the wrapper suite and the sweep-gates lib suite are green under the pinned PATH including the new cases; the done skill and its vendored twin carry the duty line (the presence pin passes) byte-equal; the pins suite failing set is unchanged from the captured green baseline.
Ship when: all tasks' validation lines pass on the landed tree.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py scripts/test_done_sweep_gates_lib.py -q
diff agents/skills/done/SKILL.md "$HOME/.agents/skills/done/SKILL.md"
bash scripts/check_maintenance_pins.sh
```

## Out of scope

- No manifest schema change, no in-place manifest widening, no new `done_run.sh` or sweep flag surface, no learn/setup reordering, no persisted record file (the sidecar shape is rejected by review r1 F2/F4).
- No change to the unstaged legs' warning posture (demotion program change 7 stands).
- No new refusal class anywhere; the behavioral deltas are that declared post-setup edits stop refusing in the primary-resident shape and that the manifest-resolved refusal names the declared-stage remedy.
- No scheduler state file, machinery registry, or docs/maintenance/ operative-text changes beyond the one done-skill duty line.
- Mixed runner/lib deployment vintages are not handled beyond the same-change landing: a stale paired copy degrades to today's strict refusal (fail-closed), and the execution phase records the symptom note.
