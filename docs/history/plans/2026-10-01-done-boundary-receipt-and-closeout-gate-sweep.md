# Plan: Done-boundary receipt and closeout gate sweep

Backlog origins (scope of record): `docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md`, `docs/history/backlog/2026-09-29-p79-gates-no-r1-fix-behavior-pins.md`, `docs/history/backlog/2026-09-29-emit-roundtrip-vt-ff-unreachability.md`, `docs/history/backlog/2026-09-29-step1-ledger-tmp-dir-loss-residual.md`, `docs/history/backlog/2026-09-29-em-dash-gate-run-backlog-candidates.md`
Driving force: reliability
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-done-boundary-receipt-and-closeout-gate-sweep-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The done boundary mechanically enforces the completion ceremony it today only describes, and the five residual hardenings in the sweep roster land with suite-level pins.

- A plan archive the new gate's derivation surfaces (a staged same-run rename, a committed rename since the session-window anchor, or a stale deliverables line) fails the pre-commit phase when its boxes are unchecked or its exec-review record is missing, instead of presenting as done (twice witnessed as 0/10 and 0/12 archives with reviews existing on no branch).
- A write-manifest invocation refuses while an interrupted run boundary under this checkout's done-session directory is neither adopted nor dispositioned, instead of printing a passive report nobody consumes.
- A vertical-tab or form-feed named ignored review candidate is caught by the emit roundtrip abort (today the term is unreachable because the ignored-path enumeration never unquotes git's C-style escapes), the p79 r1-fix behaviors carry suite-level pins, the Step 1 ledger recipe guards a lost TMP_DIR, and the em-dash gate's partition property gains a standing canary plus the fail-closed ls-files polarity.

Gate delta: three refusal-class additions, each with its cited completed-integrity-failure witness: the archive-ceremony gate (new gate id in the pre-commit phase) carrying two checked conditions over the same archive derivation, checkbox completeness and exec-review coverage (witness: the two 2026-09-30 unchecked-archive landings 21178a3f and 66b91d23 with claimed-but-absent exec reviews and the batch-wide staging-transfer skip), and the write-manifest undisposed-interrupted refusal (new checked condition on the existing passive report, witness: manifest run-manifest-20260930T125655Z-681b1860d42e sitting complete:false with nothing consuming the signal; the refusal is bounded by the done-lock's per-checkout exclusivity, so a complete:false manifest under this checkout's done-session directory is a past interrupted run, never a live sibling). Fix-class additions priced by their origins: the unquoter gains the two missing short escapes and the ignored-path enumeration applies it (the false-negative removal is the origin's own first remedy; the alternative drop-the-term arm is rejected because the term becomes reachable); the Step 1 recipe gains the TMP_DIR presence guard beside the existing RUN_ID guard (the origin's named sharp-edge removal); the em-dash ls-files polarity hardening is the origin's candidate 1 with candidate 4's cosmetic downgrade noted. No gate, field, or refusal surface is removed.

## Terms

- Done-sweep gates: the thirteen (fourteen after this plan) absorbed gates of `scripts/done_sweep_gates.sh`, implemented in `scripts/done_sweep_gates_lib.py`, run in the pre-docs and pre-commit phases of a done run.
- Archive-ceremony gate: the new pre-commit gate this plan adds; for every plan archive its derivation surfaces it checks checkbox completeness and exec-review coverage.
- Exec-review record: a staging doc under the resolved reviews home whose name ends `-exec-r<N>` and names the plan slug in a `-plan-review-` series; the execution run's review of record for the plan's final bytes.
- Closure stray: an origin whose substance already landed in earlier work while its backlog file still reads open; this plan flips each one to a dated done receipt instead of re-implementing it.
- Interrupted-run boundary: a run manifest with `complete: false`; adoption (`--adopt`) continues it, `disposition-manifest --run-id` closes it.
- Roundtrip abort term: the emit-foreign-candidates guard refusing candidate paths that cannot survive one-per-line emission, including the `[\v\f]\.md$` arm.

## Assumptions

- Arm 1 (archive-gate receipt existence) and the backfill arm of the log entry are already delivered by the peer-landed `2026-10-01-cited-review-receipt-integrity` plan (squash 58d56a97; the receipts origin reads done with that receipt), so this plan neither re-implements nor cites that origin. (Basis: the completed plan's Gate delta and the origin's Status line, read today.)
- The peer plan's two prose duties (archive step's cited-receipt check, closeout's exec-receipt check) are the session-level layer; this plan's gate arms are the mechanical net that catches a session skipping the prose. The surfaces compose and do not overlap. (Basis: the peer plan's Gate delta states "no script ... both checks are guidance-level fail-closed duties".)
- Ceremony items 4-6 (queue enumeration, stale-base landing guard, payload-level skill binding) stay out of scope per the log entry's own coordination note. (Basis: the entry's Prompt arm 4.)
- Receipt scoping and the emit echo-capture duty among the p79 r1-fix behaviors are already pinned or documented; the plan records those dispositions with named probes instead of duplicating pins. (Basis: manifest payload assertions near scripts/test_done_sweep_gates_lib.py:1350 and done SKILL.md Step 0's echo-capture paragraph.)
- Suite tests run through the ai-playbook-test venv with a system-python3 fallback. (Basis: completed plan 2026-10-01-disposition-cas-coverage-and-parse-path Validation Commands.)
- The em-dash origin's candidate 2 (plan-prose count drift) is a process note with no code surface; recorded as no-action. (Basis: the origin body.)
- Honest derivation scope for the new gate: it surfaces staged same-run renames, committed renames into the archive directories since the session-window anchor, and stale plan-deliverables lines. An execute-plan archive landed before the done session starts is bounded by the peer plan's closeout prose duty and the later-run stale-line arm, not by this gate; the Outcome bullets claim only the timing delivered. (Basis: pre-docs runs before the mid-run archive and plan-readiness is pre-docs-only, verified against the phase lists this cycle.)

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: The done boundary gains the three witnessed ceremony gates and the five residual hardenings, and three already-landed strays get dated done receipts; force: reliability.

Today a session can archive a plan with every task box unchecked, claim an exec review that exists on no branch, and finalize a new run manifest while an interrupted run's boundary sits undisposed: each failure already happened (the two 2026-09-30 archive landings, the batch-wide staging-transfer skip, the manifest that sat complete:false for hours) and each passes every current gate because the gates check trees, not ceremony. After this plan the archive-ceremony gate requires checkbox completeness and an exec-review record for the archives its derivation surfaces, and write-manifest turns its interrupted-run report into a bounded refusal. The residual half fixes the emit enumeration's blind spot for control-character filenames (the unquoter learns the two missing short escapes and the ignored-path arm finally applies it), pins the unpinned p79 behaviors at suite level, guards the Step 1 ledger recipe against a lost TMP_DIR, and gives the em-dash partition property a standing canary.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each new refusal fires on its witnessed failure shape and passes its sanctioned-exit shape (checked boxes or marked backfill, present exec-review record or reconstruction, adopted or dispositioned boundary).
- Consistency: the new gate composes with the existing absorbed gates (same GateContext, GateResult, phase wiring, usage text); both of its checks live in one gate, not a second gate.
- Simplicity-priced additions: every addition cites its completed-failure witness in Gate delta; no refusal surface removed anywhere.

**Done when:**
- The full gates suite and wrapper suite pass under the venv runner, every Validation Commands line exits 0, and the three stray origins carry dated done receipts.

**Ship when:**
- The next done run that archives a plan or finalizes a manifest exercises the new refusals in vivo (operator-observed; external condition, no checklist item).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py`
- `scripts/done_sweep_gates.sh`
- `agents/skills/done/SKILL.md`

**Tests:**
- `scripts/test_done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_wrapper.py`

**Docs (origin files):**
- `docs/history/backlog/2026-09-30-execution-ceremony-prevention-witnesses.md`, `docs/history/backlog/2026-09-29-p79-gates-no-r1-fix-behavior-pins.md`, `docs/history/backlog/2026-09-29-emit-roundtrip-vt-ff-unreachability.md`, `docs/history/backlog/2026-09-29-step1-ledger-tmp-dir-loss-residual.md`, `docs/history/backlog/2026-09-29-em-dash-gate-run-backlog-candidates.md` (the cited origins; status flips only where a task prescribes one)
- `docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md`, `docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md`, `docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md` (the Task 8 strays; dated done receipts only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/history/backlog/2026-09-30-plan-archive-cited-review-receipts.md`; reason: done by the peer landing (Assumptions), cited nowhere.
- `agents/skills/plans/SKILL.md`, `agents/skills/execute-plan/SKILL.md`; reason: the peer plan owns the prose layer there; this plan touches neither.
- ceremony items 4-6 surfaces (maintenance payload templates, queue enumeration, landing critical sections); reason: the entry's coordination note.
- `scripts/scan-public-hygiene.sh` and deny patterns; reason: no scanner surface in this sweep.

## Validation Commands

```bash
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo FAIL: gates suite; exit 1; }
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_wrapper.py -q || { echo FAIL: wrapper suite; exit 1; }
bash scripts/done_sweep_gates.sh list-gates | grep -q "archive-ceremony" || { echo FAIL: ceremony gate wired; exit 1; }
grep -c "test_archive_checkbox_gate_refuses_unchecked_archive" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: checkbox pin; exit 1; }
grep -c "test_archive_ceremony_gate_requires_exec_review" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: coverage pin; exit 1; }
grep -c "test_write_manifest_refuses_undisposed_interrupted_boundary" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: interrupted pin; exit 1; }
grep -qF "write-manifest: undisposed-interrupted:" scripts/done_sweep_gates_lib.py || { echo FAIL: interrupted refusal; exit 1; }
grep -c "test_run_manifest_created_epoch_float_accepted_bool_never_coerces" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: float pin; exit 1; }
grep -c "test_sanitize_manifest_error_value_strips_control_characters" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: sanitize pin; exit 1; }
grep -c "test_repo_root_matches_value_digest_and_path_arms" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: repo-root pin; exit 1; }
grep -cF 'replace("\\v", "\v")' scripts/done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: unquoter v-escape; exit 1; }
grep -cF 'replace("\\f", "\f")' scripts/done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: unquoter f-escape; exit 1; }
sed -n '/^def _ignored_paths/,/^def [a-z_]*(/p' scripts/done_sweep_gates_lib.py | grep -q "_unquote_porcelain_path" || { echo FAIL: ignored-path unquote; exit 1; }
grep -c "test_emit_roundtrip_rejects_vertical_tab_ignored_candidate" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: roundtrip pin; exit 1; }
grep -c "test_em_dash_partition_property_full_stdout" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: partition canary; exit 1; }
grep -c "test_em_dash_ls_files_failure_treats_hits_untracked" scripts/test_done_sweep_gates_lib.py | grep -q -v "^0$" || { echo FAIL: polarity pin; exit 1; }
grep -qF '[ -z "${TMP_DIR:-}" ]' agents/skills/done/SKILL.md || { echo FAIL: tmp-dir guard; exit 1; }
grep -qF "archived-plan review-coverage" scripts/done_sweep_gates_lib.py || { echo FAIL: coverage arm token; exit 1; }
grep -q "neither adopted nor dispositioned" agents/skills/done/SKILL.md || { echo FAIL: step-0 doc arm; exit 1; }
grep -qi "^Status: done (2026-10-01" docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md || { echo FAIL: stray 1 receipt; exit 1; }
grep -qi "^Status: done (2026-10-01" docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md || { echo FAIL: stray 2 receipt; exit 1; }
grep -qi "^Status: done (2026-10-01" docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md || { echo FAIL: stray 3 receipt; exit 1; }
bash scripts/check-no-em-dash.sh file scripts/done_sweep_gates_lib.py scripts/done_sweep_gates.sh agents/skills/done/SKILL.md docs/history/plans/2026-10-01-done-boundary-receipt-and-closeout-gate-sweep.md || { echo FAIL: em-dash; exit 1; }
# hygiene note: scripts/done_sweep_gates_lib.py and agents/skills/done/SKILL.md are deliberate
# excludes on the scanner's GLOB_EXCLUDES list, so no --files line can scan them; the exclusion
# is the sanctioned posture, not a skipped scan.
```

### Task 1: archive-ceremony gate with the checkbox check in the pre-commit phase

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/done_sweep_gates.sh`
- `agents/skills/done/SKILL.md`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `bash scripts/done_sweep_gates.sh list-gates`; covers the new gate id registered and listed
- `"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k archive_checkbox -q`; covers the refusal and its exemption/backfill exits

- [ ] Run → expect RED: `grep -c "test_archive_checkbox_gate_refuses_unchecked_archive" scripts/test_done_sweep_gates_lib.py` returns 0 [class: REPOSITORY_TEST]
- [ ] Add `gate_archive_ceremony(ctx)` to the lib with its archive derivation carrying three shapes, each with its own byte source, under the comment marker `archive-ceremony derivation`: (a) staged or worktree rename rows over the plans pathspec (the `R old -> new` rows `_porcelain_lines` returns; bytes read from the index or worktree file at the new path, which exists at both pre-commit invocations), (b) committed renames into `plans_completed_dir` since this run's manifest boundary (a `git diff --find-renames <base>..HEAD --name-status` over the plans pathspec where `<base>` is the active run manifest's `start_commit` with the gate_doc_registry precedent's `ORIG_HEAD` fallback when absent; when neither resolves, shape (b) surfaces nothing this run and the gate notes the skip; bytes from the HEAD blob at the archived path; note every existing name-status diff in the lib deliberately uses `--no-renames`, so this gate's diff is the first rename-detecting one), and (c) stale plan-deliverables lines whose recorded plan path no longer exists because it now sits archived (bytes from the archive twin at HEAD). No existing helper provides shape (b); derive it inside the gate [class: IMPLEMENTATION_REQUIRED]
- [ ] Checkbox check in the same gate: fail when a derived archive's plan bytes carry any `- [ ]` unchecked task box; the failure names the plan, the unchecked count, and the two sanctioned exits (check the boxes after verified work, or land a marked backfill completion record per the archive-correction exception the cited-review-receipt-integrity plan added to the plans skill) [class: IMPLEMENTATION_REQUIRED]
- [ ] Register the gate id `archive-ceremony` in the lib's gate mapping and `PRE_COMMIT_GATES`; update the wrapper usage heredoc's pre-commit line (adding the new id, and the `description-length` id that line already omits), fix both stale `twelve` counts in the wrapper (the usage comment and the heredoc), add the `archive-ceremony` id to the done SKILL.md `## Pre-commit sweep gates` section's prose list (the `## Pre-docs sweep gates` list needs no edit), and bump the test suite's `EXPECTED_GATE_ORDER` registry pin [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_archive_checkbox_gate_refuses_unchecked_archive` (fixture: a staged-rename archive with an unchecked box fails with the named remedy) and `test_archive_checkbox_gate_passes_checked_or_backfilled` (fixture: a fully checked archive and a backfill-marked archive pass) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: the Evidence commands; suite green [class: REPOSITORY_TEST]
- [ ] Commit: `done-sweep: archive-ceremony gate refuses unchecked archives` [class: IMPLEMENTATION_REQUIRED]

### Task 2: exec-review coverage check in the archive-ceremony gate

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `grep -c "test_archive_ceremony_gate_requires_exec_review" scripts/test_done_sweep_gates_lib.py`; covers the arm's fixture
- `"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k requires_exec_review -q`; covers refusal plus reconstruction exit

- [ ] Run → expect RED: the Evidence grep returns 0 [class: REPOSITORY_TEST]
- [ ] In `gate_archive_ceremony`, after the checkbox check passes for a derived archive, require the exec-review record under the comment marker `archived-plan review-coverage`: any file under the resolved reviews home whose name contains `-plan-review-`, contains the archived plan's slug (the file stem minus its leading date prefix; the slug form is what real records use), and ends `-exec-r<N>`; when absent, fail naming the plan, the missing series, and the reconstruction remedy (produce the exec-review record; a marked reconstruction is valid per the cited-review-receipt-integrity precedent). The derivation's three shapes bound the check's reach per the Assumptions scope note [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_archive_ceremony_gate_requires_exec_review` (fixture: a derived archive with no exec record fails with the remedy; adding a minimal `-exec-r1` staging doc whose name follows the slug convention turns the gate green) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: Evidence commands; suite green [class: REPOSITORY_TEST]
- [ ] Commit: `done-sweep: archived plans need an exec-review record at the archive-ceremony gate` [class: IMPLEMENTATION_REQUIRED]

### Task 3: write-manifest refuses undisposed interrupted boundaries

Files:
- `scripts/done_sweep_gates_lib.py`
- `agents/skills/done/SKILL.md`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `grep -c "test_write_manifest_refuses_undisposed_interrupted_boundary" scripts/test_done_sweep_gates_lib.py`; covers the refusal fixture
- `"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k undisposed_interrupted -q`; covers refusal, adopt exit, disposition exit

- [ ] Run → expect RED: the Evidence grep returns 0 [class: REPOSITORY_TEST]
- [ ] In the write-manifest command after the interrupted-run report loop: when any orphan remains that this invocation neither adopted nor recognized as dead-root-dispositioned, return the named failure `write-manifest: undisposed-interrupted:` listing each remaining manifest filename with the remedies its root state supports (a live-root boundary: `--adopt <run_id>` to continue it or `finalize-manifest --run-id <id>` to close it, since disposition-manifest refuses live roots; a dead-root boundary: `disposition-manifest --run-id <id>` only, matching the report lines); keep the existing report lines (the refusal adds the bounded decision, it does not replace the report); the refusal sits before the emit-foreign-candidates arm, so an emit-only invocation also requires the classification first, deliberately; the done-lock's per-checkout exclusivity is why no liveness probe is needed, stated in the arm's comment [class: IMPLEMENTATION_REQUIRED]
- [ ] done SKILL.md Step 0: in the flags paragraph carrying the `--adopt` sentence (the Run manifest block), ADD one sentence after it (Step 0 carries no existing report sentence to extend): an interrupted boundary under this checkout's done-session directory that is neither adopted nor dispositioned refuses a new write-manifest invocation, and the report line's remedies are the exits; the doc arm must read as the same behavior the lib implements [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_write_manifest_refuses_undisposed_interrupted_boundary` (fixture: a complete:false manifest in the window fails the write with both remedies named; after `--adopt` the write succeeds; after `disposition-manifest` on a dead-root fixture the write succeeds) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: Evidence commands; suite green [class: REPOSITORY_TEST]
- [ ] Commit: `done-sweep: write-manifest refuses undisposed interrupted boundaries` [class: IMPLEMENTATION_REQUIRED]

### Task 4: suite-level pins for the unpinned p79 r1-fix behaviors

Files:
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k "float_accepted_bool or sanitize_manifest_error or repo_root_matches_value" -q`; covers the three new pins
- the named probes below; covers the two recorded dispositions (receipt scoping pinned, echo-capture documented)

- [ ] Run → expect RED: `grep -c "test_run_manifest_created_epoch_float_accepted_bool_never_coerces" scripts/test_done_sweep_gates_lib.py` returns 0, and likewise for the other two new names [class: REPOSITORY_TEST]
- [ ] Add `test_run_manifest_created_epoch_float_accepted_bool_never_coerces` beside the bool twin, pinning the real residual behavior: a float `created_epoch` stays accepted (the writer itself stamps `time.time()`, so a float-refusing schema would reject every manifest the tool writes) while a bool never coerces through the int-or-float arm (`True`/`False` refuse, the F3 guard the origin names) [class: REPOSITORY_TEST]
- [ ] Add `test_sanitize_manifest_error_value_strips_control_characters` (direct unit over `_sanitize_manifest_error_value`: control characters stripped and truncation at 64 characters render newline/CR line forgery inert in the output; printable characters including quotes survive by contract) [class: REPOSITORY_TEST]
- [ ] Add `test_repo_root_matches_value_digest_and_path_arms` (both arms route through `_repo_root_matches_value`: the 64-hex root digest matches, the legacy raw resolved path matches, a wrong digest and a wrong path refuse) [class: REPOSITORY_TEST]
- [ ] Record the two dispositions in the task log: receipt scoping is pinned by the manifest payload assertions asserting `owned_review_paths`/`foreign_review_paths` roundtrip (probe: `grep -n "owned_review_paths" scripts/test_done_sweep_gates_lib.py`), and the echo-capture duty is documented prose in done SKILL.md Step 0's capture block (an empty captured `MANIFEST` or `RUN_ID` must abort Step 0) and is agent-side recipe text no suite exercises (probe: `grep -n "echo" agents/skills/done/SKILL.md | head`); neither gets a duplicate pin [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: Evidence commands; suite green [class: REPOSITORY_TEST]
- [ ] Commit: `done-sweep: suite pins for the unpinned p79 r1-fix behaviors` [class: IMPLEMENTATION_REQUIRED]

### Task 5: emit enumeration unquotes C-escaped ignored candidates

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `grep -c "test_emit_roundtrip_rejects_vertical_tab_ignored_candidate" scripts/test_done_sweep_gates_lib.py`; covers the formerly unreachable term
- `sed -n '/^def _ignored_paths/,/^def [a-z_]*(/p' scripts/done_sweep_gates_lib.py | grep -c unquote`; covers the enumeration-side application

- [ ] Run → expect RED: the two Evidence probes return 0 [class: REPOSITORY_TEST]
- [ ] Extend `_unquote_porcelain_path` with the two missing C-style short escapes, inserted immediately after the existing `\r` replacement and before the null-sentinel restore `.replace("\x00", "\\")` (the sentinel shield must stay over `\v` and `\f` sequences, so a literal backslash followed by v or f survives as text) [class: IMPLEMENTATION_REQUIRED]
- [ ] Apply `_unquote_porcelain_path` to each line in `_ignored_paths`' returned list, so the ignored arm of the enumeration matches the ordinary arm's quoting discipline; the emit roundtrip abort's `[\v\f]\.md$` term becomes reachable and stays (the origin's drop-the-term alternative is rejected) [class: IMPLEMENTATION_REQUIRED]
- [ ] Record the probe correction in the task log: git emits the short escapes `\v` and `\f` (not octal) for vertical tab and form feed, correcting the origin's octal shorthand; octal applies only to other control bytes [class: REPOSITORY_TEST]
- [ ] Add `test_emit_roundtrip_rejects_vertical_tab_ignored_candidate` (fixture: an ignored reviews-home candidate whose name ends in a vertical tab before the extension; the emit invocation aborts with the named roundtrip error listing it; a control-free ignored candidate still emits) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: Evidence commands; suite green [class: REPOSITORY_TEST]
- [ ] Commit: `done-sweep: unquote C-escaped ignored candidates so the roundtrip term is reachable` [class: IMPLEMENTATION_REQUIRED]

### Task 6: Step 1 ledger recipe guards a lost TMP_DIR

Files:
- `agents/skills/done/SKILL.md`

Evidence:
- `grep -cF '[ -z "${TMP_DIR:-}" ]' agents/skills/done/SKILL.md`; covers the guard landing beside the RUN_ID guard

- [ ] Run → expect RED: the Evidence grep returns 0 [class: REPOSITORY_TEST]
- [ ] In the Step 1 owned-commits ledger recipe block, extend the existing guard to `[ -z "${RUN_ID:-}" ] || [ -z "${TMP_DIR:-}" ]` with the skip note naming both inputs (a lost TMP_DIR misassigns the ledger path to `/done-session/...` under bash 3.2 `set -u`, and the run then fails at the redirect after the commit landed); the Step 3 site inherits the guard by its apply-the-Step-1-rule wording, so one edit covers both append sites [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Evidence grep [class: REPOSITORY_TEST]
- [ ] Commit: `done skill: ledger recipe guards a lost TMP_DIR beside the RUN_ID guard` [class: IMPLEMENTATION_REQUIRED]

### Task 7: em-dash gate standing partition canary and ls-files polarity

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Evidence:
- `"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k em_dash -q`; covers the canary and the polarity arm

- [ ] Run → expect RED: `grep -c "test_em_dash_partition_property_full_stdout" scripts/test_done_sweep_gates_lib.py` returns 0, and likewise for the polarity pin [class: REPOSITORY_TEST]
- [ ] Add `test_em_dash_partition_property_full_stdout` (standing canary for the anti-mutation property: a fixture probe whose stdout carries more than ten hits across the tracked/untracked split is partitioned completely, never to the last-ten tail; assert every hit is classified) [class: REPOSITORY_TEST]
- [ ] In `gate_em_dash_scan`, when the `ls-files --others --exclude-standard` probe fails, treat every hit as untracked (fail-closed polarity, the origin's candidate 1; candidate 4's residual-harm note is recorded here as the reason the arm is small rather than load-bearing) [class: IMPLEMENTATION_REQUIRED]
- [ ] Add `test_em_dash_ls_files_failure_treats_hits_untracked` (fixture: probe failure classifies all hits untracked with the untracked marker, none as pre-existing) [class: REPOSITORY_TEST]
- [ ] Record candidate 2 as no-action in the task log (plan-prose count drift is a process note; future plans re-derive counts at execution time) [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: Evidence commands; suite green [class: REPOSITORY_TEST]
- [ ] Commit: `done-sweep: em-dash partition canary and fail-closed ls-files polarity` [class: IMPLEMENTATION_REQUIRED]

### Task 8: closure-stray done receipts for the three already-landed origins

Files:
- `docs/history/backlog/2026-09-28-done-lock-one-shot-reclaim-releases-documentation.md`
- `docs/history/backlog/2026-09-28-write-manifest-legacy-foreign-bulk-load.md`
- `docs/history/backlog/2026-09-29-done-sweep-consumes-run-tmp-before-worktree-migration.md`

Evidence:
- the three Validation Commands receipt greps; covers each stray carrying its dated done receipt

- [ ] Verify before flipping: the done skill's one-shot-reclaim paragraph (the origin's Expected text verbatim in shape), the first-finalize bulk-load paragraph with the claim-none conflict note, and the sweep lib's closeout-baseline freshness exemption (remedy (c), age-bounded) each exist at their named homes today [class: REPOSITORY_TEST]
- [ ] Flip the done-lock-reclaim origin by replacing its plain `Status: open` line's value, keeping the file's plain metadata-block form: `Status: done (2026-10-01; the done skill's one-shot holders and peer reclaim paragraph carries the lifecycle and the token-mismatch-is-expected-witness adjudication)` [class: IMPLEMENTATION_REQUIRED]
- [ ] Flip the write-manifest origin the same plain-form way: `Status: done (2026-10-01; the done skill's first-finalize bulk-load sequence and the claim-none conflict note carry the canonical invocation and the conflict surface)` [class: IMPLEMENTATION_REQUIRED]
- [ ] Flip the run-tmp origin by adding a `Status: done (2026-10-01; remedy (c) landed: the sweep exempts archived-plan sessions holding a fresh closeout-baseline.json, age-bounded by the stale-baseline grace window)` line directly under its title (the file carries no metadata block today) [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `backlog: dated done receipts for the three landed closure strays` [class: IMPLEMENTATION_REQUIRED]
