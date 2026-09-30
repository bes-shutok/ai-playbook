# Plan: Orphaned-manifest disposition and survey arm

Backlog origin: docs/history/backlog/2026-09-29-interrupted-run-and-stranded-work-prevention-ideas.md (ideas B and D, the origin's own first value tier)
Driving force: automation
Plan review record: the staging series docs/reviews/2026-09-30-plan-review-orphaned-manifest-disposition-and-survey-arm-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

An unadoptable interrupted-run manifest can be closed through a sanctioned disposition operation, and the maintenance survey classifies unfinished manifests by derivable root liveness instead of re-reporting the advisory forever - so the witnessed 20260929T023532Z-3fb1c11bb98b incident class (a manifest bound to a deleted worktree root, unadoptable, re-reported by every later Step 0) ends in a machine-actionable record.

- A `disposition-manifest` writer operation marks an interrupted-run manifest as dispositioned with a reason and witness; the Step 0 report enumerates without the root-match filter and splits into interrupted, dispositioned, and foreign-or-gone channels, printing `dispositioned: <reason>` for the closed runs instead of re-reporting them as interrupted and surfacing foreign-root orphans as disposition-eligible at all.
- The maintenance survey gains a classification that proposes a resume dispatch for a this-checkout unfinished manifest (parked like other intents) and routes foreign-or-gone manifests to the operator-witnessed disposition (proposed once; the sibling-live-worktree caveat recorded).
- The other four ideas of the origin's value order (E, A, C, F) stay open at the origin for later plans, exactly as the origin's Suggested fix orders them.

Gate delta: one new writer operation (a disposition transition beside write-manifest and finalize-manifest) and one survey classification. The counted addition is priced by the origin's witnessed completed-integrity failure (the unadoptable manifest re-reported forever; disposition recorded only in session memory, invisible to later tooling) and by its paying sibling: the manifest already carries the adoption-suppression mechanism for one interruption shape, and the disposition is the corresponding record for the unadoptable shape the adoption path cannot reach.

## Terms

- **Unadoptable manifest**: an interrupted-run manifest (complete=false, unadopted) whose recorded root no longer exists, so neither adopt nor finalize can proceed.
- **Disposition record**: the manifest's additive `disposition` field: `{"reason": "...", "witness": "...", "date": "<iso>"}` written by the new operation; the Step 0 interrupted-run detection excludes dispositioned manifests.
- **Root liveness (derivable)**: the classification input computed from manifest state alone: a manifest whose recorded root digest equals this checkout's root digest is live (this repository, actionable); any other digest is foreign-or-gone (unresolvable from this checkout - it may be a deleted worktree or a sibling live checkout, which is why the disposition requires the operator's verified witness).

## Assumptions

- assume the disposition rides the manifest JSON as an additive optional field read tolerantly (schema version unchanged; `from_dict` reads the field when present, ignores its absence), not a sidecar; basis: the manifest file already is the record other readers parse, a sidecar would duplicate the source of truth, and the tolerant-parse contract accepts records with missing optional fields.
- assume the disposition operation is a lib sub-command (`disposition-manifest --run-id <id> --reason <text> [--witness <text>]`) beside write-manifest and finalize-manifest, refusing a manifest that is complete or already dispositioned, and requiring an explicit reason; basis: the origin's idea B names the operation shape and the existing sub-command family is its home.
- assume the survey classification enumerates ALL manifests in the done-session directory WITHOUT the root-match filter (the detection functions' filter would exclude exactly the foreign-or-gone population the classification exists to reach) and classifies by derivable liveness (recorded digest equality with this checkout's root digest), exposed through a named CLI sub-command (`classify-interrupted-manifests`) the maintenance bullet invokes; the foreign class carries the sibling-live-worktree caveat and proposes disposition only through the operator-witnessed operation; basis: the r1 review's three code facts (digest-only root recording, the root-match filters in the detection and load paths, the missing invocation surface) and the origin's idea D intent.
- assume the origin's Class line (automation, from the header) and Driving force (reliability) agree with this plan's declared automation force: the machinery removes a recurring manual direction (the perpetual advisory a human must triage each Step 0); basis: the driving-force taxonomy's automation definition.
- assume ideas E, A, C, F stay at the origin (the origin's own ordering places them in later plans; the Family paragraph maps them to their extending items); the plan consumes only B and D.
- assume the repository's pytest-runner contract applies (venv interpreter first, ambient fallback with a version guard); basis: plan `docs/history/plans/completed/2026-09-30-done-sweep-closeout-baseline-exemption.md` Task 3 (Validation).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: interrupted-run manifests become dispositionable and the maintenance survey routes them by derivable root liveness (digest equality, foreign-or-gone for the rest), ending the perpetual advisory; the driving force is automation (the loop triages its own stragglers).

Before (today): a run's worktree is deleted before closeout; the manifest stays complete=false bound to a root digest that resolves to nothing. Every later Step 0 re-reports it as an interrupted run no tooling may resolve (adopt and finalize both refuse), and the only disposition lives in a human's memory. The maintenance survey has no classification for it, so the advisory repeats forever.

After (this plan): the same manifest is closed once - `python3 scripts/done_sweep_gates_lib.py disposition-manifest --run-id <id> --reason "work verified landed" --witness "<evidence>"` - and Step 0 reads it as dispositioned instead of interrupted. The maintenance survey classifies this-checkout unfinished manifests as resume proposals and foreign-or-gone ones as disposition proposals (operator-witnessed, once).

## Evaluation Criteria

**Quality dimensions:**
- correctness: a dispositioned manifest is excluded from the interrupted-run detection and named in the report as dispositioned; the operation refuses complete, already-dispositioned, and missing manifests; the survey classifier separates this-checkout from foreign-or-gone unfinished manifests, and complete manifests yield no proposal.
- regression safety: the manifest schema version is unchanged and every existing manifest parses unchanged; the full lib suite stays green.
- maintainability: the classification is a pure tested function; the skill bullets name the fields they read.

**Done when:**
- The `disposition-manifest` operation, the detection honor, and the survey classifier exist with tests; the Step 0 report and maintenance survey bullets carry the routing; all Validation Commands exit 0.

**Ship when:**
- The deployed lib twin (`~/.ai-playbook/scripts/done_sweep_gates_lib.py`, a real copy) refreshes from the repo copy at execution closeout with a digest receipt, and consumer runtimes receive both skills through their normal vendored-asset sync.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/SKILL.md`

**Tests:**
- `scripts/test_done_sweep_gates_lib.py`

**Documentation:**
- `docs/history/plans/2026-09-30-orphaned-manifest-disposition-and-survey-arm.md` *(this plan; Task 4's read-only extraction input)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Ideas E, A, C, F of the origin and their extending items; reason: the origin's own value order places them in later plans.
- The maintenance pins suite (scripts/check_maintenance_pins.sh); reason: the Step 1 bullet addition is new prose; the suite re-keys only if an existing count pin shifts, which Task 3 verifies and records in its commit message.

## Validation Commands

```bash
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest --version || { echo "no pytest-capable interpreter" >&2; exit 1; }

# 1. The lib suite passes with the new tests.
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo "FAIL: lib suite" >&2; exit 1; }

# 2. The disposition operation and detection honor are named in the source (dedicated pins).
grep -qF '"disposition-manifest"' scripts/done_sweep_gates_lib.py || { echo "FAIL: operation missing" >&2; exit 1; }
grep -qF 'dispositioned' scripts/done_sweep_gates_lib.py || { echo "FAIL: detection honor missing" >&2; exit 1; }
grep -qF '"classify-interrupted-manifests"' scripts/done_sweep_gates_lib.py || { echo "FAIL: classifier CLI surface missing" >&2; exit 1; }

# 3. The skills carry the routing (dedicated pins).
grep -qF 'dispositioned' agents/skills/done/SKILL.md || { echo "FAIL: Step 0 report routing missing" >&2; exit 1; }
grep -qF 'classify-interrupted-manifests' agents/skills/maintenance/SKILL.md || { echo "FAIL: survey invocation missing" >&2; exit 1; }

# 4. The maintenance pins suite stays green (Task 3 re-keys any shifted count).
bash scripts/check_maintenance_pins.sh || { echo "FAIL: pins suite" >&2; exit 1; }

# 5. Em-dash gate over the branch's added lines.
bash scripts/check-no-em-dash.sh added-lines --base main || { echo "FAIL: em-dash gate" >&2; exit 1; }
```

Authoring-time gate record (rule 29/19/22): the detection function (`_detect_interrupted_runs`, scripts/done_sweep_gates_lib.py ~740) and the manifest schema (`RunManifest.from_dict`, tolerant parse) were read on this tree at authoring time; the witnessed orphaned manifest (20260929T023532Z-3fb1c11bb98b) is recorded in the origin and memory with its disposition still memory-only. Feasibility note: the authoring draft defined root liveness as directory resolution from the recorded root, which the identity contract makes impossible (manifests record a 64-hex digest, not a path) and the detection filters make unreachable; the r1 review caught it and the r1 fold batch rewrote the classification onto derivable state (digest equality) with an unfiltered CLI enumeration. RED-today evidence, rule 19: Command 1's new tests do not exist (RED until Tasks 1-2); Command 2's operation and classifier-CLI pins are absent from the source today (verified zero hits, RED), while its `dispositioned` pin already passes via one prose comment mention today (a characterization presence pin - the functional detection honor is Command 1's new test); Command 3's skill pins are absent from both files today (verified); Command 4 is a characterization gate (suite green today, verified). Rule 22 mechanical audit: each Validation Command pin occurs once in its owning Task's prescription beside its Command occurrence (plan-wide mentions in Gist, Terms, and Assumptions are not pin sites); `bash -n` over this block passed.

### Task 1: Pin disposition and classification contracts (RED)

Files:
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers: the new tests exist and fail against the current lib.

- [ ] Add tests patterned on the file's existing manifest fixtures: `test_disposition_manifest_marks_and_refuses_repeats` (an interrupted-run manifest gains the disposition field through `main(["disposition-manifest", "--run-id", ..., "--reason", ..., "--witness", ...])`; a second identical call refuses; a complete manifest refuses; a missing run-id refuses); `test_report_splits_interrupted_and_dispositioned` (a dispositioned manifest prints a `dispositioned:` report line carrying its reason and no `interrupted run:` line, an undispositioned this-checkout manifest still prints `interrupted run:`, and a foreign-root undispositioned manifest prints the `foreign-or-gone:` line - the report-content witness covering all three channels); `test_survey_classifier_classifies_by_digest_equality` (over an injected manifest set without the root-match filter: a manifest whose digest equals the current checkout's classifies `resume-proposal`, a foreign undispositioned digest classifies `foreign-or-gone` with the sibling-live-worktree caveat in its reason, and a dispositioned manifest classifies `dispositioned` - never re-proposed; a complete=true manifest yields a `complete` census line and no proposal; reachable through the `classify-interrupted-manifests` CLI sub-command); `test_disposition_survives_as_dict_roundtrip` (a dispositioned manifest parsed and re-serialized keeps its disposition field). [class: REPOSITORY_TEST]
- [ ] Run → expect RED: the suite exits non-zero with the new tests failing (operation, honor, and classifier do not exist). [class: REPOSITORY_TEST]
- [ ] Commit: `test: pin manifest disposition and survey classification contracts (RED)` [class: REPOSITORY_TEST]

### Task 2: Implement disposition operation, detection honor, classifier (GREEN)

Files:
- `scripts/done_sweep_gates_lib.py`

Evidence:
- `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers: the whole lib suite green including the new tests.

- [ ] Add the `disposition-manifest` sub-command to the CLI dispatch beside write-manifest and finalize-manifest: locate the manifest by run-id, refuse when complete or already dispositioned or missing, write the additive `disposition` field (`{"reason", "witness", "date"}`, the reason required) through the same atomic-write path the writer uses, and leave the schema version untouched. [class: IMPLEMENTATION_REQUIRED]
- [ ] Teach `RunManifest.from_dict` to read the optional `disposition` field tolerantly and `RunManifest.as_dict` to write it back (the round-trip keeps a later finalize's full-manifest write from dropping the disposition). [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `split_interrupted_and_dispositioned(done_session_dir, repo_root)` enumerating ALL manifests in the done-session directory WITHOUT the root-match filter (the witnessed incident class - a root gone with its worktree - manifests as a foreign digest and must reach the report), returning three channels: this-checkout interrupted (root digest equals this checkout, complete=false, undispositioned, and not adopted - the adopted-exclusion `_detect_interrupted_runs` applies survives so its existing suite stays green), dispositioned (any root, disposition present), and foreign-or-gone (any other digest, complete=false, undispositioned); keep `_detect_interrupted_runs` returning interrupted-only (its existing callers unchanged) by delegating to the split's first channel; rework the interrupted-run report loop inside `_cmd_write_manifest` (the inline loop consuming the detection list) to drive off the split, printing `dispositioned: <reason>` lines through the module's manifest-string sanitizer for the dispositioned channel and `foreign-or-gone: <run-id> (root not resolvable from this checkout; disposition eligible through disposition-manifest)` lines for the third. [class: IMPLEMENTATION_REQUIRED]
- [ ] Add the `classify-interrupted-manifests` CLI sub-command: enumerate ALL manifests in the done-session directory without the root-match filter and print one classification line per manifest (`resume-proposal` for a complete=false undispositioned manifest whose recorded digest equals this checkout's root digest; `dispositioned` for any manifest carrying a disposition - never re-proposed; `foreign-or-gone` with the sibling-live-worktree caveat for a complete=false undispositioned manifest with any other digest; `complete` for a complete=true manifest - no proposal, the census line only), so the maintenance consult has an invocation surface, a dispositioned manifest stops being proposed, and the finished-run majority never yields a proposal. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the lib suite exits 0. [class: REPOSITORY_TEST]
- [ ] Commit: `feat: manifest disposition operation, detection honor, survey classifier` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Skill routing prose (GREEN)

Files:
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/SKILL.md`

Evidence:
- `grep -qF 'dispositioned' agents/skills/done/SKILL.md && grep -qF 'classify-interrupted-manifests' agents/skills/maintenance/SKILL.md`; covers: both routing bullets.

- [ ] Amend the interrupted-run report guidance: a manifest closed through `disposition-manifest` reads as `dispositioned: <reason>` in the Step 0 report and is never re-reported as interrupted; a foreign-root orphan prints as `foreign-or-gone` (disposition eligible through `disposition-manifest` with the operator's verified witness - each owned deliverable checked landed - recorded in the field). [class: IMPLEMENTATION_REQUIRED]
- [ ] Amend the maintenance survey: the Step 1 consult invokes `python3 scripts/done_sweep_gates_lib.py classify-interrupted-manifests` and classifies unfinished manifests by derivable root liveness, proposing a resume dispatch for a this-checkout manifest (parked like other intents) and the operator-witnessed disposition for a foreign-or-gone manifest (the sibling-live-worktree caveat recorded with the proposal). The Task 3 fold owns the pins-suite re-key if any count shifts. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: Command 3's pins pass; Command 4's pins suite stays green (Task 3's fold above owns any re-key, recorded in the commit message). [class: REPOSITORY_TEST]
- [ ] Commit: `docs: route orphaned manifests through disposition and survey classification` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Whole-plan validation gate

Files:
- `docs/history/plans/2026-09-30-orphaned-manifest-disposition-and-survey-arm.md` *(read-only input: the block this task extracts and executes; no repository file is edited by this task)*

Evidence:
- `awk '/^```bash$/{f=1;next}/^```$/{f=0}f' docs/history/plans/2026-09-30-orphaned-manifest-disposition-and-survey-arm.md > "$TMPDIR/whole-plan-validation.sh" && bash "$TMPDIR/whole-plan-validation.sh"` (the block's own commands extracted and executed; the awk expression is described because the literal sequence cannot appear inside this fenced block); covers: every criterion in Done when.

- [ ] Run the extracted Validation Commands block from the worktree root; every command exits 0; the task's single commit records the validation evidence and touches no production file. [class: REPOSITORY_TEST]
- [ ] Commit: `test: whole-plan validation for orphaned-manifest disposition and survey arm` [class: REPOSITORY_TEST]


## Superseded (2026-10-01, first-landed-wins adjudication)

The duplicate-origin coverage gate refused this plan at execution readiness: its origin (`docs/history/backlog/2026-09-29-interrupted-run-and-stranded-work-prevention-ideas.md`, ideas B and D) is already covered by the first-landed plan `docs/history/plans/completed/2026-09-30-interrupted-run-disposition-and-survey-arm.md` (squash main 1aef6343, executed 2026-10-01), which delivers the same disposition operation, listing sub-command, detection widening, survey classification arm, and same-turn capture duty. This plan is rejected as superseded through the rejected archive per the coverage gate's remedy; its ideas A/F/C dispositions are recorded on the covering plan's origin fold.
