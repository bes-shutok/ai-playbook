# Run-start-marker execution review follow-ups (manifest root leak, lib hardening)

- **Filed:** 2026-09-27
- **Origin:** execution review r1 of docs/plans/2026-09-08-run-start-marker-content-hash.md (correctness + risk workers, zero blocking in the landing bytes)
- **Status:** open
- **Priority:** medium

## Findings deferred

1. **Medium - run-manifest JSONs re-introduce the raw repo root.** `RunManifest.repo_root` (scripts/done_sweep_gates_lib.py, `write_run_manifest`) serializes the absolute resolved repo root plus absolute `foreign_review_paths` into `run-manifest-<run_id>.json` under `{tmp_dir}/done-session/` - the same docs-branch shadow-synced directory the marker fix cleaned. Post-dates the plan's authoring (manifests appeared 2026-09-25), so out of its scope, but it defeats the plan's Outcome headline ("the docs branch no longer carries raw local paths") one file over. Fix shape: record the same digest in the manifest (with `_manifest_root_matches` gaining the identical two-arm rule), and digest or relativize `foreign_review_paths`.
2. **Low - lib digest-arm fallthrough hardening.** In `_parse_marker`, a 3-field marker whose 64-hex middle field fails the digest comparison falls through to the legacy `realpath` arm, resolving a relative hex name against process CWD. Not accident-reachable (absolute paths contain `/` and can never fullmatch hex), but returning None for a hex-mismatched field is strictly safer.
3. **Cosmetic - Step 2.62 wording.** "a marker whose recorded digest matching the SHA-256 hex digest ... is content-confirmable" reads awkwardly (the plan's own prescribed construction); reword at the next docs-branch/done open pass.
4. **Test polish - mixed-format window.** No test anchors a window from a legacy raw-path prev marker plus a digest-format current marker together; the arms are covered separately and are independent.

## Acceptance

Fix item 1 in a dedicated small plan (it touches the lib writer plus its tests); items 2-4 ride along.
