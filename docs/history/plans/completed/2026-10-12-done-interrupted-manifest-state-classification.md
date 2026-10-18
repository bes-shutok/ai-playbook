# Plan: done setup consumes the canonical manifest-state classification

Backlog origins (scope of record):
- docs/history/backlog/2026-10-09-done-interrupted-root-label-ambiguity.md
- docs/history/backlog/2026-10-09-done-worktree-shadow-manifest-disposition.md
- docs/history/backlog/2026-10-12-done-setup-ignores-dispositioned-manifest-state.md

Driving force: efficiency + simplicity
Plan review record: the staging series {reviews_dir}/2026-10-12-plan-review-done-interrupted-manifest-state-classification-r*.md (the highest rN is the authoritative record, including any deferred-residual list)
Execution budget: 4h total, largest task 1.5h

## Terms

- `classify_partial`: the shell classifier in `scripts/done_run.sh` that setup consults before writing a fresh boundary; today it treats the lexicographically newest run manifest as an interrupted boundary regardless of the record's state.
- `canonical classification`: the schema-validated manifest-state semantics owned by `scripts/done_sweep_gates_lib.py` (the `RunManifest` parse plus the orphan filter of `_detect_interrupted_runs`): a run is terminal when it is finalized (`complete` true), adopted (another manifest's `adopted_from` link names its run id), or dispositioned (a `dispositioned` record is stamped on one of its files); everything else with `complete` false is an unresolved orphan.
- `terminal state`: finalized, adopted, or dispositioned; a closed boundary that setup must not refuse on.
- `shadow copy`: a `run-manifest-*.json` file whose payload `run_id` equals another file's `run_id` but whose filename is not that run's canonical `run-manifest-<run_id>.json`; a duplicate view of one run's boundary, typically left by a worktree-scoped closeout.
- `run identity`: the payload `run_id`; all files sharing it are one run's records, whichever checkout wrote them.
- `content-confirmed marker`: a `run-start-*` marker whose recorded repo-root digest matches the current checkout (the existing `marker_confirms` arm).
- `root match`: the manifest's recorded `repo_root` matches the current checkout through either arm of the existing match helper; a repository-identity fact that says nothing about whether a process or lock is active.
- `done-session dir`: the facts-resolved `done-session` directory under `{tmp_dir}` holding run-start markers and run manifests.

## Why

done setup stops on already-closed interruptions: its shell classifier reads only whether a newest manifest exists, so a finalized, adopted, or dispositioned record, including the four witnessed dead-root dispositions, blocks a fresh closeout and forces the recorded continuation-checkout workaround. The repository already owns a schema-validated classifier with exactly these terminal states; setup does not consult it.

## Gist & Examples

TLDR: setup classifies the newest run manifest through the canonical terminal states instead of its own state-blind newest-file check, and the interrupted-run reports separate repository identity from process liveness, so closed boundaries stop blocking fresh closeouts.

Before (today): a previous closeout finalized its manifest, or a dead-root run was dispositioned. A new `done_run.sh setup` in the same checkout finds that record as the lexicographically newest manifest, prints the interrupted-boundary remedies, and exits 2. The only recorded paths forward are re-entering a finished boundary or the continuation-checkout workaround, witnessed four times on 2026-10-12 alone.

After (this plan): the same setup classifies the record through the canonical owner, prints one note naming the terminal state and run id, and proceeds to a fresh marker and manifest. The prior record stays byte-identical on disk. An unresolved orphan still refuses with today's remedies, and explicit `--from-manifest` re-entry is unchanged.

Identity example: `list-interrupted-manifests` prints `root=live` today, which one consumer read as "the prior task is still running" and stopped at a recoverable manifest. After this plan it prints `root_matches_current_repo=yes` beside a separate lock-state column plus one guidance line: a matching root is an identity fact, and the lock status command carries liveness.

Shadow example: a worktree-suffixed copy of a manifest shares the canonical record's run id. Today the scanners count it as a second independent boundary and `disposition-manifest` cannot close it, because it accepts only a run id and reads the canonical filename. After this plan the reports bind the copy to its run as `shadow-of`, and `disposition-manifest --manifest-file` closes that copy after verifying that copy's own deliverables.

## Outcome

done setup, the interrupted-run inventory, and manifest disposition agree on one schema-validated definition of a closed boundary.

- A finalized, adopted, or dispositioned newest manifest no longer blocks `done_run.sh setup`; setup continues with a fresh boundary and a one-line note, and the witnessed workaround stops recurring.
- `list-interrupted-manifests` and the setup remedies never use a liveness word for a repository-identity fact, and the report carries the lock state beside the identity state.
- Worktree shadow manifests stay visible as bound copies of their run, and each copy can be dispositioned through its own verified evidence without hand-editing manifests.

Gate delta: no counted-class additions and no removals. The one refusal-surface change is a sanctioned exit added to the existing recovery command (`disposition-manifest --manifest-file`), priced by Rule 42's origin-cited justification: origin 2 is fix-class and its body records the alternatives (hand-editing or renaming the copies) with the reason each is impossible (both bypass the verifier or hide the record), so the sanctioned exit is the class-default arm. The setup change removes no refusal: the unresolved-orphan refusal and both marker refusals are preserved byte-identically. The report-column growth in `list-interrupted-manifests` is priced by origin 1's witnessed misclassification incident (docs/history/backlog/2026-10-09-done-interrupted-root-label-ambiguity.md).

## Assumptions

- assume setup reuses the library's parser and classification semantics by invoking the repo-local `scripts/done_sweep_gates_lib.py` module from the shell classifier, anchored to the runner's own directory and never re-implementing the state predicates in bash; basis: the origin prompt's reuse rule and the library's existing Step 0 ownership.
- assume a run's terminal state is read at run identity: grouping every `run-manifest-*.json` record sharing the newest file's payload run id, so a terminal record on any of the run's files closes the boundary whichever file is newest (the witnessed flow where a newest worktree-suffixed copy closes through its canonical twin, and the mirrored flow where a copy-only disposition closes a run whose unresolved canonical record sorts before the copy); dispositioning a copy still verifies that copy's own deliverables (Task 3), so closure evidence is never borrowed across runs; basis: origin 2's evidence that copies shared run id and owned deliverables, and the prompt's mismatched-canonical-file guard.
- assume the finalized case is in this plan's scope (it is one of the three canonical terminal states the prompt names), and the live sibling authoring claim `docs/tmp/authoring-claims/2026-10-12-done-setup-mistakes-finalized-manifest-for-partial-boundary.md` (the frozen PLAN-PROMPTS entry `done-finalized-manifest-classification`, read 2026-10-12) composes with or narrows against whatever is landed when its own authoring resumes; its origin row is not among this plan's origins, so origin coverage does not collide; basis: the frozen entry's prompt text and the coverage gate's first-landed-wins rule.
- assume explicit `--from-manifest` re-entry keeps today's semantics, including re-entering a terminal record when the operator names it, with the one shared exception that a corrupt record takes Task 1's fail-closed refusal line on the explicit path too; otherwise only the automatic no-flag classification changes; basis: the prompt's preserve-list and the frozen sibling entry's scope arms.
- assume the corrupt-record arm tightens: today an unparseable newest manifest is classified as a stale-marker boundary with an unknown id; after this plan it refuses fail-closed naming the record, matching the library's F10 posture that a corrupt record is reported, never silently skipped; basis: the `_detect_interrupted_runs` warnings contract.

Decision points requiring a grill: none remain.

## Standing constraints

- Every changed or added diagnostic line stays ASCII, em-dash-free, and free of machine-specific paths; the interrupted-run vocabulary (`terminal state`, `shadow-of`, `root_matches_current_repo`) is the shared naming across setup, the inventory, and the disposition command.
- The pins suite is red on main by a recorded 21-failure baseline (docs/history/backlog/2026-10-12-pins-suite-main-baseline-21-failures.md; the failing set is confined to execute-plan SKILL.md spans per that row and per the authoring-time capture recorded in the Validation preamble); the plan's pins check asserts no NEW failing description versus that recorded set, and any pin whose literal lives in a region a task edits is re-aimed beside its provenance comment in the same edit.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every terminal case (finalized, adopted, dispositioned, shadow-closed) proceeds past setup with the prior records byte-identical; every unresolved case (orphan, marker-only, corrupt) refuses with a named remedy; each witness is verified against a real fixture session directory at execution.
- simplicity: the shell classifier holds no state predicates of its own; the terminal verdict comes from the library module; no second parser, schema field, validator, ledger, gate, or recovery command is added.
- observability: the inventory line's identity field is unambiguous (`root_matches_current_repo=yes|no`), liveness has its own column and guidance line, and shadow copies render as bound copies of their run, never as independent boundaries.
- maintainability: the existing parser and deliverable-witness helpers are reused unchanged in shape, and the compare-and-swap stamping helper is reused with a targeted stamp path (a path parameter), never a duplicated stamp loop; new behavior is reachable through the existing commands and their suites.

**Done when:**
- `done_run.sh setup` over a fixture session directory whose newest manifest is terminal proceeds to a fresh marker and manifest and prints the terminal-state note, for all three terminal states plus the shadow-closed arm.
- The unresolved-orphan and marker-only refusals print today's remedy lines unchanged (the corrupt-record arm tightens per Task 1), and `--from-manifest` re-entry behaves as today.
- `list-interrupted-manifests` prints the renamed identity field, the lock column, and the liveness guidance line, and never renders the identity value `live`.
- `disposition-manifest --manifest-file` closes a verified shadow copy without touching the canonical record, refuses a payload-run-id mismatch, and the interrupted-run reports label shadows as `shadow-of` instead of independent boundaries.
- The focused wrapper and library suites pass, the pins suite shows no new failing description against the recorded baseline, and the public-hygiene scan passes.

**Ship when:**
- A real closeout on this repository runs setup past a pre-existing terminal record without the continuation-checkout workaround (operational evidence, next closeout that meets the case).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_run.sh`
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

**Tests:**
- `scripts/test_done_run_wrapper.py`
- `scripts/test_done_sweep_gates_lib.py`

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/docs_branch_sync.sh` and the docs-branch sync surface; reason: the sync's restore arm is owned by docs/history/backlog/2026-10-12-docs-archive-doubled-reviews-prefix.md, not by manifest classification.
- Any change to the manifest schema, the adoption protocol, or the recovery commands' existing flag semantics; reason: the origin prompt's preserve-list.

## Validation Commands

Authoring-time rule 29 record: the no-em-dash scan, the public-hygiene scan, the readiness pre-round invocation, the rule 19 RED-today probes, and the rule 22 mechanical audit (each pinned span exactly once in its owning snippet, plus `bash -n` over this block) run over these bytes before round 1, and their outcomes append below as Recorded lines.

Recorded 2026-10-12 (authoring session no-session, over these v1 bytes on branch authoring/done-interrupted-manifest-state-classification): fix_plan_em_dashes.py 0 substitutions; `bash scripts/check-no-em-dash.sh touched` exit 0; public-hygiene scan final line `OUTCOME: pass`; the readiness pre-round invocation exits 0 `OUTCOME: pass` with one non-blocking warning (the declared 4h budget over the 3.0h cap; the four tasks share two production files and one classification owner, so a split would cut the setup arm from the report and disposition arms that consume its verdict); the gate caught two real v1 defects fixed in the same authoring pass (the decision-points trailer sat as a list item, and the boilerplate checklist items carried no classification tags); rule 19 RED-today evidence: the identity and shadow positive gates fail against today's library bytes, and the negative rendering gate fires today on exactly its four forbidden forms (two docstring or usage occurrences of `root=<live|dead>`, the `"live"` state literal, and the `root={root_state}` rendering); the pins regression guard passes against the current tree (21 current failing descriptions, byte-identical set to the recorded 21-line baseline captured in this worktree at its base commit on 2026-10-12, derivation `bash scripts/check_maintenance_pins.sh`); rule 22 mechanical audit PASS (`bash -n` over the Validation block; the baseline heredoc byte-equal to the captured baseline; no exact-text pin against a task snippet exists yet, so the span check is that heredoc equality). Round-start state for r1: the bytes at the commit carrying this preamble.

Recorded 2026-10-12, r1 fold re-run (session no-session, over the post-fold bytes): the r1 panel's four staged non-blocking findings folded (the Done-when bullet scoped to the unresolved-orphan and marker-only arms with Assumption 4 naming the corrupt refusal as the one shared change; the maintainability bullet reworded to the targeted-stamp-path shape; the lock column's held-versus-free predicate pinned to the lock script's own status semantics with a meta-less-leftover witness added; the Task 3 usage-and-docstring checkbox added). The delta classifier refused the corrections path over all six hunks (content rewords and added lines, none exempt), so this fold is round-launching and the fresh focused round below is the certification path. Battery over the amended bytes: fix_plan_em_dashes.py 0 substitutions; em-dash touched exit 0; hygiene `OUTCOME: pass`; the readiness pre-round invocation exits 0 `OUTCOME: pass` (the recorded non-blocking budget warning stands); rule 22 audit PASS (`bash -n` over the Validation block; the pins regression guard passes, 21 current failing descriptions byte-identical to the recorded baseline); all five fold receipts verified as landed (each fixed span occurs exactly once in the amended bytes). Round-start state for the focused round: the bytes at the fold commit carrying this preamble.

Recorded 2026-10-12, r2 fold re-run (session no-session, over the post-fold bytes): the focused round r2 verified every r1 fold resolved and staged three new non-blocking findings, folded here (the lock-column predicate and its witness re-anchored to the column's own incomplete-age and dead-holder arms, dropping the false status-command agreement claim the round refuted against `status_report`; Assumption 2 and the Task 1 grouping witness generalized to all run-identity records whichever file sorts newest; the Task 3 binding witness extended with the post-copy-disposition closed-run-history rendering). Battery over the amended bytes: fix_plan_em_dashes.py 0 substitutions; em-dash touched exit 0; hygiene `OUTCOME: pass`; the readiness pre-round invocation exits 0 `OUTCOME: pass` (the recorded non-blocking budget warning stands); `bash -n` over the Validation block PASS; all three fold receipts verified as landed. Round-start state for the focused round: the bytes at this fold commit.

Recorded 2026-10-12, r4 fold re-run (session no-session, over the post-fold bytes): r4 verified the Task 1 split preserved acceptance coverage and staged one blocking finding - two more criteria over the 512-byte item cap (Task 2 first at 888 bytes, Task 3 fourth at 522), unmasked because the gate short-circuits on the first failing task. Fixed per the non-monotonic reconciliation rule in one comprehensive fold: the Task 2 criterion split into the identity-column, lock-column-mapping, and held-or-free-predicate criteria, and the Task 3 criterion split at its two-arm seam (shadow binding; post-closure closed-run history); every checklist item in the plan then measured against the cap with a whole-file sweep (zero items over). Battery over the amended bytes: fix_plan_em_dashes.py 0 substitutions; envelope sweep clean; the full readiness gate now reaches only its review-record binding check (stale sidecar digest), which the fresh certification round below resolves. Round-start state for the focused round: the bytes at this fold commit.

Recorded lines follow.

```bash
python3 scripts/test_done_run_wrapper.py

python3 scripts/test_done_sweep_gates_lib.py

tmp="$(mktemp -d)"
bash scripts/check_maintenance_pins.sh > "$tmp/pins.txt" 2>&1
grep "^PIN FAIL" "$tmp/pins.txt" | sed 's/^PIN FAIL: //' | sort > "$tmp/now.txt"
cat > "$tmp/base.txt" <<'PIN_BASELINE'
claim-less end derives from stop lines
contract derives the claim-less case from stop lines
contract mirrors the claim boundary
dispatch_failed record literal
dispatch_failed tracking-list entry head
post-backoff success writes a recovery marker
preservation: Resume carrier fallback ordering heading span count 0 != 1
preservation: OffPeakCreate pause rung span count 0 != 1
preservation: OffPeakCreate prompt contract span count 0 != 1
preservation: canonical carrier-aware record span count 0 != 1
preservation: canonical lineage-cap branch span count 0 != 1
preservation: launchd wired mark span count 0 != 1
rate-limited end resolves its open claim
resume backoff carries a floor
resume-fit --fire-at check at resume-scheduling boundaries
resume-pricing defers to the reported defer_to
serialized cap doubles the Step 3.1 bound
serialized cap doubles the intermediate-panel bound
serialized cap doubles the omnibus bound
state table derives the claim-less case
stop line token format pinned
PIN_BASELINE
sort -o "$tmp/base.txt" "$tmp/base.txt"
if comm -13 "$tmp/base.txt" "$tmp/now.txt" | grep -q .; then
  echo "new pin failure outside the recorded 21-line main baseline (docs/history/backlog/2026-10-12-pins-suite-main-baseline-21-failures.md)"
  exit 1
fi
rm -rf "$tmp"

( cd "$(git rev-parse --show-toplevel)" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" )

grep -q "root_matches_current_repo" scripts/done_sweep_gates_lib.py || { echo "identity column missing from the inventory"; exit 1; }
grep -q "shadow-of" scripts/done_sweep_gates_lib.py || { echo "shadow binding label missing from the reports"; exit 1; }
rc=0
grep -nE 'root=<live|root=\{root_state\}|"live"' scripts/done_sweep_gates_lib.py || rc=$?
if [ "$rc" -ge 2 ]; then echo "tool error sweeping the identity rendering"; exit 1; fi
if [ "$rc" -eq 0 ]; then echo "the inventory still renders or documents the liveness word for a root match"; exit 1; fi
```

The pins block is a regression guard against the recorded main baseline, checked against the current tree's bytes per the Validation preamble's rule 22 carve-out. The three literal gates sweep `scripts/done_sweep_gates_lib.py` only, so the plan's own text naming those literals is not a self-match; the plan file is outside every swept set.

### Task 1: setup classifies the newest manifest through the canonical terminal states

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/done_run.sh`
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `classify_partial` in `scripts/done_run.sh`
- `_detect_interrupted_runs` in `scripts/done_sweep_gates_lib.py`

- [x] `done_sweep_gates_lib` delivers `classify_run_boundary`: given a session directory and a manifest path, expects a verdict naming terminal (finalized, adopted, or dispositioned), shadow-closed, orphan, or unreadable, derived only through the existing `RunManifest` parse and the directory's adopted set [class: IMPLEMENTATION_REQUIRED]
- [x] `classify_run_boundary` reads the verdict at run identity: given a session directory holding several records of one run, expects the verdict grouped over every `run-manifest-*.json` record sharing the newest file's payload run id, so a terminal record on any of the run's files closes the boundary whichever file is newest [class: IMPLEMENTATION_REQUIRED]
- [x] `classify_partial` consumes that verdict: given a fixture session directory whose newest manifest is finalized and bound to the newest content-confirmed marker, expects setup proceeds to a fresh marker and manifest, prints one note naming `finalized` and the run id, and the prior manifest stays byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] given an adopted and a dispositioned newest record (a dead-root disposition included), expects the same fresh-boundary continuation with the state named in the note [class: IMPLEMENTATION_REQUIRED]
- [x] given a non-canonical newest copy whose canonical twin carries the terminal record, expects continuation with `shadow-closed` named in the note [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given an unresolved orphan (complete false, unadopted, undispositioned) whose marker matches the newest content-confirmed marker, expects today's current-boundary remedy lines byte-identically and the refusal exit, and given a stale-marker or markerless orphan, expects today's stale remedy lines byte-identically and the refusal exit [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a corrupt (unparseable) newest manifest, expects a fail-closed refusal naming the record and no fresh boundary written [class: IMPLEMENTATION_REQUIRED]
- [x] given a content-confirmed marker with no manifest, and given no marker and no manifest, expects today's behavior unchanged (the marker-only remedy refusal; the fresh-setup return) [class: IMPLEMENTATION_REQUIRED]
- [x] given explicit `--from-manifest` naming the newest record's run id, whether terminal or orphan, expects today's re-entry exports unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the terminal-case, shadow-closed, and corrupt-case witnesses fail against today's state-blind newest-file classifier [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the wrapper and library suites pass with the new witnesses [class: REPOSITORY_TEST]
- [x] Commit: `feat: done setup consumes the canonical manifest-state classification` [class: IMPLEMENTATION_REQUIRED]

### Task 2: identity and liveness separate in the interrupted-run reports

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `_cmd_list_interrupted_manifests` in `scripts/done_sweep_gates_lib.py`

- [x] `list-interrupted-manifests` renders `root_matches_current_repo=yes|no`, and the identity value `live` is never rendered for a root match [class: IMPLEMENTATION_REQUIRED]
- [x] `list-interrupted-manifests` renders a `lock=held|free|unknown` column derived read-only from the checkout-keyed done-lock directory: a fingerprint root maps to its lock directory under the done-lock root, honoring the done-lock root environment override; unknown for a non-fingerprint root or an unreadable lock root [class: IMPLEMENTATION_REQUIRED]
- [x] the lock column pins held and free from the column's own semantics: held when the lock directory carries live holder metadata, free when it is absent or a meta-less directory past the lock script's crash-leftover rule, with the status command's raw held line for a meta-less directory being the documented divergence the column resolves by applying the incomplete-age rule, and free also for a present-meta hold whose recorded holder is verified dead [class: IMPLEMENTATION_REQUIRED]
- [x] given at least one root-matching record, expects one guidance line stating that a matching root is a repository identity fact and naming the lock status command as the liveness check [class: IMPLEMENTATION_REQUIRED]
- [x] given a meta-less leftover lock directory past the crash-leftover rule, expects the column to report `free` under the column's own incomplete-age arm (the status command's raw held line for the same directory is the documented divergence the column resolves, never an agreement claim), and given a present-meta hold whose recorded holder is verified dead, expects the column to report `free` [class: IMPLEMENTATION_REQUIRED]
- [x] the command usage text and the command docstring describe the new columns and the guidance line [class: IMPLEMENTATION_REQUIRED]
- [x] the done skill's Step 0 setup paragraph states in one sentence that the interrupted-run report's root match is repository identity, not process or lock liveness [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the column and guidance witnesses fail against today's `root=<live|dead>` rendering [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: separate repository identity from liveness in the interrupted-run report` [class: IMPLEMENTATION_REQUIRED]

### Task 3: shadow copies bind to their run and close through their own evidence

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `_cmd_disposition_manifest` in `scripts/done_sweep_gates_lib.py`
- `_detect_interrupted_runs` in `scripts/done_sweep_gates_lib.py`

- [x] `disposition-manifest` accepts `--manifest-file <bare filename>`: given a worktree-suffixed copy whose payload run id matches `--run-id`, expects the existing deliverable witness verified against that copy's owned paths and the `dispositioned` record stamped on that copy only, through the existing compare-and-swap stamping re-reading that file, with the canonical record untouched [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a `--manifest-file` whose payload run id differs from `--run-id`, expects a named refusal and no mutation, so a copy can never be closed through a mismatched canonical record [class: IMPLEMENTATION_REQUIRED]
- [x] given a copy that is complete, adopted by another manifest, live-rooted, already dispositioned, or outside the session directory or the `run-manifest-*.json` glob (a non-bare or traversing name), expects the canonical arm's named refusals, with the idempotent reprint arm for an already-stamped copy [class: IMPLEMENTATION_REQUIRED]
- [x] the interrupted-run reports bind copies: given a shadow copy sharing a canonical record's run id, expects the write-manifest interrupted-run report and `list-interrupted-manifests` to render that file as a `shadow-of <run_id>` line naming the filename, never as an independent boundary [class: IMPLEMENTATION_REQUIRED]
- [x] given a copy closed through `--manifest-file`, expects the reports to render the run's remaining records as the closed run's history (no open-boundary line), matching the Terms' run-identity closure [class: IMPLEMENTATION_REQUIRED]
- [x] the disposition-manifest usage text and docstring describe `--manifest-file`, its payload-run-id match requirement, and the copy arm's refusals [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the copy-arm and binding witnesses fail against today's run-id-only disposition and per-file boundary rendering [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN [class: REPOSITORY_TEST]
- [x] Commit: `feat: shadow manifests bind to their run and disposition through their own evidence` [class: IMPLEMENTATION_REQUIRED]

### Task 4: full validation pass

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/done_run.sh`
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`

Primary class anchors:
- `classify_partial` in `scripts/done_run.sh`

- [x] Run the full Validation Commands block from the repository root; expects the two suites green, the pins failing-description set a subset of the recorded baseline, the hygiene scan ending `OUTCOME: pass`, and the three literal gates green [class: REPOSITORY_TEST]
- [x] Sweep the pins suite for touched literals in `scripts/done_run.sh`, `scripts/done_sweep_gates_lib.py`, and `agents/skills/done/SKILL.md`; expects every pin whose literal lives in an edited region re-aimed beside its provenance comment in the same edit, with no new failing description versus the recorded baseline [class: REPOSITORY_TEST]
- [x] Commit: `test: full validation pass for the manifest-state classification plan` [class: IMPLEMENTATION_REQUIRED]
