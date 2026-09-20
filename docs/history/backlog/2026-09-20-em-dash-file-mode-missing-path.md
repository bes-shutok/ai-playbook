# Backlog: check-no-em-dash file mode silently passes a nonexistent path

- **Status:** open
- **Class:** REPOSITORY_TEST
- **Discovered:** 2026-09-20, intermediate task review round 2 (focused re-review) of Task 3, plan `docs/plans/2026-09-19-scheduler-ops-contract-fix.md` (off-plan: pre-existing tooling, not causally tied to any plan task).
- **Finding:** `scripts/check-no-em-dash.sh` `file` mode begins `scan_file` with `[[ -f "$path" ]] || return 0`, so a nonexistent path exits clean (verified empirically: exit 0 for `/tmp/does-not-exist-xyz.md`). A typo'd or relocated path in a future gate list vacuously passes.
- **Driving force:** every em-dash gate built on `file` mode trusts exit 0 as "checked and clean"; a missing path converts the gate from a witness into a rubber stamp without any signal, so the failure it exists to prevent (em-dash landing in a gated file) becomes undetectable exactly when the gate list drifts.
- **Fix shape:** in `file` mode, fail (or at minimum warn to stderr with a nonzero warn-count exit contract) when a listed path does not exist; keep directory/list modes' current behavior aligned with the same rule; add a test asserting the missing-path refusal.
- **Trigger:** next edit to `scripts/check-no-em-dash.sh` or any new gate list relying on its `file` mode.
