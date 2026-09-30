# Plan: Disposition stamp CAS: the two untested racing shapes and the shared parse path

[github: https://github.com/admitriev/ai-playbook] Backlog origin: `docs/history/backlog/2026-10-01-disposition-cas-coverage-and-parse-path.md`
Driving force: correctness; secondary simplicity

## Gist TLDR

TLDR: the disposition stamp's CAS gains its two missing suite arms - the post-check-adoption refusal and the dispositioned-race idempotent reprint (the finalize shape is already pinned) - and its fresh payload re-read is routed through the reader's parse contract (`_read_manifest_by_run_id`) instead of raw json.loads, so a divergent parse tolerance cannot let the stamp proceed over a payload the reader would refuse.

## Outcome + Gate delta

All three racing shapes the CAS handles carry suite arms: post-check finalize (existing), post-check adoption (a competing manifest's `adopted_from` link appearing between the initial read and the re-scan - the arm asserts the refusal names the post-check adoption and no `dispositioned` record lands), and the dispositioned race (a `dispositioned` record appearing - the arm asserts the idempotent reprint of the racer's record with exit 0). The CAS's fresh re-read uses the reader's parse path so absent, unreadable, and schema-mismatched fresh payloads all refuse identically to `_read_manifest_by_run_id`'s contract.

Gate delta: one re-read call rerouted through the existing reader helper (no behavior change for well-formed payloads - the helper parses the same file), two suite arms; removes nothing.

## Terms

- **Post-check adoption**: a competing manifest whose `adopted_from` names this run's boundary, appearing between the initial read and the CAS re-scan.
- **Dispositioned race**: a `dispositioned` record appearing on this manifest between the initial read and the stamp; the CAS reprints the racer's record idempotently.

## Assumptions

- The adoption-race arm hooks `_manifest_adopted_by_another` (seeding the competing manifest before the re-scan, or hooking the scan to seed on first call) - the same hook-the-read discipline the finalize race arm uses.
- The parse-path reroute is safe: `_read_manifest_by_run_id` returns a `RunManifest` or None; the CAS needs the racing shapes (complete, adopted_from is a directory scan; dispositioned presence), all carried on the RunManifest dataclass. A None re-read keeps the existing fail-closed refusal.
- `_manifest_adopted_by_another` on the seeded directory is the real helper (no stub), so the adoption arm exercises the production scan.

Decision points requiring a grill: none remain - the 1.2b candidates name both gaps verbatim; the reroute choice follows the candidate's "single shared parse path" fix.

### Task 1 - The two missing CAS arms (applied after Task 2's reroute)

- [x] DEPENDS ON TASK 2 (the dispositioned-race arm hooks `_read_manifest_by_run_id`, which only reaches the CAS's fresh read after the reroute). In `scripts/test_done_sweep_gates_lib.py`: two arms patterned on `test_disposition_stamp_cas_refuses_post_check_finalize` - (a) `test_disposition_stamp_cas_refuses_post_check_adoption`: seed the dead-root manifest plus a competing manifest whose `adopted_from` names the run; hook `_manifest_adopted_by_another` to seed-then-call-original on its SECOND invocation (the stamp-time re-scan) - the first invocation is the pre-check and must pass through unchanged, otherwise the pre-check refusal fires before the stamp and the post-check shape is never reached - asserting exit 1 with "post-check adoption" in stderr and no `dispositioned` record in the on-disk payload; (b) `test_disposition_stamp_cas_dispositioned_race_reprints_idempotent`: seed the dead-root manifest, hook `_read_manifest_by_run_id` so the CAS's fresh re-read (second call) sees a payload carrying a `dispositioned` record with the racer's date/note, asserting exit 0 with the racer's date and record JSON echoed and no new write (the on-disk payload unchanged). [class: IMPLEMENTATION_REQUIRED]

### Task 2 - The CAS re-read through the reader's parse contract (apply BEFORE Task 1)

- [x] In `scripts/done_sweep_gates_lib.py`, `_cmd_disposition_manifest`'s CAS: replace the raw `json.loads` fresh read with `_read_manifest_by_run_id(ctx.done_session_dir, manifest.run_id)`; a None return refuses fail-closed naming the post-check state loss (the same refusal the absent/unparseable case uses today). The racing-shape checks read the returned `RunManifest` (complete flag, dispositioned record) instead of raw payload keys. The adoption re-scan stays the directory scan. The plain-json failure arm and its test (if one asserts raw-json text) adjust to the helper's semantics. [class: IMPLEMENTATION_REQUIRED]

### Task 3 - Validation

- [x] Run every Validation Command below from the worktree root; each must pass against the amended tree. [class: REPOSITORY_TEST]

## Evaluation Criteria

- All three racing shapes carry suite arms; the adoption and dispositioned arms assert their refusal/reprint outcomes and on-disk effects.
- The CAS re-read refuses identically to `_read_manifest_by_run_id`'s contract for absent, unreadable, and schema-mismatched fresh payloads.
- The full lib suite passes.

## Review Scope

Editable regions: `scripts/done_sweep_gates_lib.py` (the CAS re-read only), `scripts/test_done_sweep_gates_lib.py` (the two new arms). Read-only: the origin backlog item; every other file.

## Validation Commands

Run from the worktree root; every check fails closed (a miss or an error aborts non-zero).

1. `grep -qF 'test_disposition_stamp_cas_refuses_post_check_adoption' scripts/test_done_sweep_gates_lib.py && grep -qF 'test_disposition_stamp_cas_dispositioned_race_reprints_idempotent' scripts/test_done_sweep_gates_lib.py || { echo FAIL: arms missing; exit 1; }` - both arms exist (absent on main).
2. `grep -qF '_read_manifest_by_run_id(ctx.done_session_dir, manifest.run_id)' scripts/done_sweep_gates_lib.py || { echo FAIL: parse path not rerouted; exit 1; }` and `grep -qF 'fresh = json.loads' scripts/done_sweep_gates_lib.py; st=$?; test "$st" -eq 1 || { echo "FAIL: raw fresh read survives (rc=$st)"; exit 1; }` - the CAS's fresh read uses the reader helper with the manifest.run_id argument (no existing call site uses that spelling, so the pin is discriminating) and the raw json.loads fresh read is gone.
3. `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q || { echo FAIL: suite; exit 1; }` - the full suite.
4. `bash scripts/check-no-em-dash.sh added-lines --base main || { echo FAIL: em dash; exit 1; }` and `bash scripts/scan-public-hygiene.sh || { echo FAIL: hygiene; exit 1; }` - both exit 0.
