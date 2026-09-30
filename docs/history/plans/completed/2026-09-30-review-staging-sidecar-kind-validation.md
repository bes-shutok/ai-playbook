# Review-staging gate validates a claimed `.stats.json` candidate through its markdown twin, never as markdown

[github: https://github.com/admitriev/ai-playbook] Origin: docs/history/backlog/2026-09-30-done-sweep-gates-review-staging-sidecar-markdown-validation.md

Plan review: docs/reviews/2026-09-30-plan-review-review-staging-sidecar-kind-validation-r1.md (r1 verdict ready=yes, zero blocking)

## Gist TLDR

The done run-manifest writer tells runs to claim their own staging artifacts (`--owned-review <path>`), and a run that produces review sidecars claims the `.stats.json` paths too. The review-staging gate then feeds every owned candidate to `validate_review_staging.py --hard` as a MARKDOWN staging document, so a sidecar candidate fails on three wrong-shape checks (missing Metadata lines that exist as JSON fields, a demanded `.stats.stats.json` twin, agreement checks run against JSON). The witnessed result: claiming your own sidecars is unsatisfiable, and every run is pushed toward leaving sidecars unclaimed. Fix: the gate branches on candidate kind - a candidate whose name ends in `.stats.json` is validated through its markdown twin (the same `--hard <md>` invocation, which already covers sidecar schema, agreement, and digest for the pair), and an owned sidecar whose markdown twin is absent fails closed naming the sidecar. Markdown candidates are unchanged.

## Outcome + Gate delta

Witnessed 2026-09-30: a done run's manifest claimed six `.stats.json` sidecars (each pair schema-valid via `--hard` over its markdown twin) and the review-staging gate failed on exactly the three error classes above per sidecar; re-running the identical write with the sidecars unclaimed passed the gate unchanged.

One correction to the origin item's root-area note, recorded here so the fix matches the actual mechanism: the staging-path predicate `is_staging_review_path` requires a `.md` suffix and does NOT accept `.stats.json` paths; sidecars enter the candidate list through the manifest branch's existence-only rule (an owned path that exists on disk is validated on `is_file` alone, deliberately over-validating claimed artifacts). The gate's validation loop is therefore the single branching point: it is where candidate kind must be resolved before the validator invocation.

After this plan:

- A manifest-owned `.stats.json` candidate with an existing markdown twin produces exactly one validator invocation, over the twin's path (the invocation log names the `.md` file, never the `.stats.json`), and the gate passes when the twin validates.
- An owned `.stats.json` candidate whose markdown twin is absent fails the gate naming the sidecar (fail-closed: an owned half-pair is an incomplete artifact this run claimed, not something to skip silently).
- Markdown candidates take the existing path unchanged; the fallback window arm's candidates are all `.md` by the predicate and are untouched by the branch.

Out of scope: the validator itself (its markdown path already validates the pair), the run-manifest writer's claim syntax, the foreign-preservation reporting, and any broaden of what the Step 0 enumeration accepts.

## Terms

- **Sidecar candidate**: a review-staging candidate whose filename ends in `.stats.json` (the validator's own sidecar naming: the staging markdown's `.md` suffix replaced by `.stats.json`).
- **Markdown twin**: the sidecar's paired staging document, the candidate's filename with the trailing `.stats.json` removed and `.md` appended.
- **Wrong-shape checks**: the three failure classes the markdown validator produces against a JSON sidecar (missing `- Last fix commit:`/`- Record kind:` Metadata lines, the `.stats.stats.json` twin demand, agreement checks against JSON).

## Assumptions

- Twin-resolved validation is the remedy (the origin's first Expected option): running `--hard` over the twin reuses the existing pair validation (schema, agreement, digest) with no new validation mode; the alternative (excluding sidecars while requiring the twin be owned) would need a second ownership bookkeeping path for no extra rigor.
- A missing twin fails closed because the manifest branch's own asymmetry principle says over-validation can only over-check a claimed artifact: an owned sidecar without its markdown is at minimum a stale or partial claim, and silently passing it would weaken the claim discipline the Step 0 writer just introduced.
- The branch keys on the `.stats.json` filename suffix (the validator's canonical sidecar naming) rather than on `is_staging_review_path`, which cannot recognize sidecars at all.

Decision points requiring a grill: none - the origin prescribes the twin-validation remedy and the failure class falls out of the fail-closed ownership rule the manifest branch already states.

### Task 1 - Pin the sidecar-kind contract (RED)

Files:
- `scripts/test_done_sweep_gates_lib.py`

- [ ] Add tests patterned on `test_review_staging_unseen_candidate_reported_foreign` (the `write_stub_review_staging_validator` subprocess seam, `_seed_run_manifest`, `make_marker`, `run_gate`): (a) `test_review_staging_sidecar_candidate_validates_markdown_twin` - a manifest owning `docs/reviews/<date>-own-review-r1.stats.json` with the twin `<date>-own-review-r1.md` present expects rc 0 and the stub invocation log to contain the twin's `.md` path and NOT the `.stats.json` path; (b) `test_review_staging_sidecar_candidate_missing_twin_fails_closed` - the same manifest claim with no twin on disk expects rc 1 naming the `.stats.json` sidecar; (c) `test_review_staging_markdown_candidate_validated_directly` - a manifest owning a plain `.md` staging doc expects the invocation log to contain that `.md` path (guards the branch against misrouting markdown). Run the three against the unmodified lib and verify (a) fails (the stub log names the `.stats.json`, and the stub exits 1 only on `invalid` names so the wrong-shape failure is simulated by the log assertion) and (b) fails before the fix. [class: REPOSITORY_TEST]

### Task 2 - Gate: branch on candidate kind (GREEN)

Files:
- `scripts/done_sweep_gates_lib.py`

- [ ] In `gate_review_staging`'s validation loop: for each candidate, when the candidate's filename ends in `.stats.json`, resolve the markdown twin (filename minus the trailing `.stats.json`, plus `.md`; string slicing, not `Path.with_suffix`, which would replace only the final `.json`); when the twin exists as a file, invoke the validator with the twin's path; when it does not, append the sidecar's path to the failed list with a `(sidecar without markdown twin)` note and continue. Non-sidecar candidates keep the existing invocation unchanged. [class: IMPLEMENTATION_REQUIRED]

### Task 3 - Validation

- [ ] All checks in Validation Commands pass from the worktree root. [class: REPOSITORY_TEST]

## Evaluation Criteria

- A claimed sidecar candidate with a present markdown twin is validated exactly once, through the twin (stub invocation log evidence), and the gate passes; a claimed sidecar without its twin fails closed naming the sidecar; a claimed markdown candidate is validated directly as today.
- The full `scripts/test_done_sweep_gates_lib.py` suite passes with a checked exit code.

## Review Scope

Files: `scripts/done_sweep_gates_lib.py` (the `gate_review_staging` validation loop only), `scripts/test_done_sweep_gates_lib.py` (the three new tests only). Contract files referenced read-only: `scripts/validate_review_staging.py` (`is_staging_review_path`, the sidecar naming convention, the `--hard <md>` pair validation), the origin backlog item.

## Validation Commands

Run from the worktree root:

1. `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q` - full lib suite green with a live exit code.
2. `TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"; [ -x "$TEST_PY" ] || TEST_PY="$(command -v python3)"; "$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -k sidecar_candidate -q` - the new sidecar tests selected and passing.
3. `grep -c "DIFF_CONTENT_PATTERNS" scripts/done_sweep_gates_lib.py` - prints 0 (the split from the visibility plan stays intact; guards against an accidental revert during the edit).
4. `git diff main --stat -- scripts/done_sweep_gates_lib.py scripts/test_done_sweep_gates_lib.py` - only the two in-scope files changed.
5. `bash scripts/scan-public-hygiene.sh && bash scripts/check-no-em-dash.sh touched` - both exit 0.
