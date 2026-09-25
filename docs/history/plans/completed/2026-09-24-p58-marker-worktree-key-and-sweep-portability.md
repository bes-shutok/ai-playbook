# Plan: P58 skill-gate marker worktree keying and host-sweep portability

Backlog origin: docs/history/backlog/2026-09-23-skill-gate-marker-worktree-project-key.md; docs/history/backlog/2026-09-23-host-entrypoint-sweep-portability.md
Driving force: efficiency + code-quality (primary + secondary; the HIGH origin's blocked-write diagnosis loop is the efficiency half, and the LOW origin's guard portability plus externalized configuration is the code-quality half; the LOW origin's own note names "testability, maintainability", which maps into code-quality as the closest closed-taxonomy member)

## Terms

- Skill-gate marker: the per-(project, session) freshness marker at `~/.ai-playbook/runtime/skill-invoked/<class>.<project>.<session>.marker`; an ABSENT or stale marker blocks a gated write; written and refreshed by the owning skill before every gated write per the README's Marker WRITE RECIPE.
- Project key: the 16-hex-char project component of the marker filename, derived by `facts_paths.resolve_project_key(start_dir)`: `sha1(realpath(git toplevel of start_dir))[:16]`, falling back to `sha1(realpath(start_dir))[:16]` with a `keying=no-anchor` log line when git fails.
- Ad-hoc worktree: a linked git worktree an authoring or execution session creates before any plan work (`git worktree add -b <branch> <sibling-path> <default-branch>`); a worktree root is NOT the primary checkout root for project-key derivation, so primary and worktree derive DIFFERENT keys.
- Marker WRITE RECIPE: the single-source recipe in `agents/hooks/skill-gate/README.md` ("Marker WRITE RECIPE (plans class)"); the plans skill's Writing paragraph references it instead of restating constants.
- Empty-cwd fallback: the existing keying behavior of the Claude and Cursor adapters (witness: `agents/hooks/skill-gate/claude.sh`, `agents/hooks/skill-gate/cursor.sh`): when the hook payload carries no cwd, the adapter keys the consult from the write target's dirname instead of the hook process cwd; the agy and Codex adapters extract no payload cwd at all, so their consults key from the core's process cwd (the `start_dir = Path.cwd()` fallback in `scripts/skill_gate.py` main).
- Host-surface sweep: `test_removed_controls_absent_from_active_entrypoints` in `scripts/test_harness_policy_contract.py`, which asserts the removed-control signatures are absent from the operator's active home entrypoints and registered hook configs, skipping with a recorded message when those surfaces are absent.

## Assumptions

- assume the authoring baseline is the main snapshot this worktree branched (`a3424f3e`, the P57 plan landing, 2026-09-24); main advances independently during authoring (observed at `390da9df` by r2 and `5c9bad22` after it, with `a3424f3e` no longer an ancestor under squash landings), and no plan gate reads main's head; the four target files were verified byte-identical across the branch point and main at r2; basis: authoring worktree survey 2026-09-24 plus the r2 reviewer's `git log main` probe.
- assume the P57 dependency from the dispatch prompt is satisfied and surfaces do not overlap: main HEAD `a3424f3e` IS the P57 plan landing, and P57's marker references are zcode fleet markers in `agents/skills/maintenance/*`, not the skill-gate recipe; basis: `git log main` and a grep of the P57 plan bytes, 2026-09-24.
- assume the core already accepts `--cwd` for BOTH consultation and `--write-marker` (`start_dir = Path(ns.cwd) if ns.cwd else Path.cwd()`, applied by the write-marker branch), so the recipe's mechanical alternative needs NO core code change; basis: `scripts/skill_gate.py` lines 947-1013 and 1015-1028, read 2026-09-24.
- assume the regression tests belong in `scripts/skill_gate.py`'s selftest suite (the gate's canonical black-box harness, where the existing sibling-worktree keying tests live, run via `python3 scripts/skill_gate.py --selftest` with the `--selftest#<name>` filter convention); basis: the file's existing `project_not_aliased_across_sibling_worktree` and `project_stable_across_sibling_cwd_in_worktree` tests, read 2026-09-24.
- assume the origin-2 keys are TOML arrays read from the repo-scoped gitignored `.ai-playbook/facts.md` TOML fence by a test-local fence-extraction plus `tomllib` loader, and the shared parser `facts_paths.resolve_toml_key_raw` stays untouched (it is docstring-pinned as the SINGLE parser for the scalar `key = "value"` fence format and handles only quoted scalars); basis: `scripts/facts_paths.py` lines 105-142, read 2026-09-24.
- assume the fallback default keeps the current five-entry lists in the public script (renamed `DEFAULT_*`), because the origin's fix shape explicitly prescribes "the current list as the fallback default"; the externalization value is that a per-host override exists outside the public script; basis: origin 2's suggested fix, read 2026-09-24.
- assume `~/.agents/skills` symlinks into this repository's `agents/skills`, so landing the SKILL.md edit updates the runtime twin with no vendored-sync stranding; basis: `readlink ~/.agents/skills`, 2026-09-24.
- assume `python3` with `tomllib` (3.11+) is the suite runtime; basis: `scripts/runtime_capabilities.py` already imports `tomllib` on main.
- assume plan number P58 (next after landed P57); basis: `docs/plans/` listing, 2026-09-24.
Decision points requiring a grill: marker-recipe sentence placement: step 4 of the plans-class recipe carries the project-key prescription because it is the derivation step (and the learn-class recipe's step 4 already inherits by reference, "same `project`/`session` derivation as plans", so no learn-class edit is needed), while step 5's CLI line gains the `--cwd` pass-through as the origin's explicitly optional mechanical alternative which the core already implements; the origin delegates this choice ("step 4 or 5") and the dispatch task's standing pre-authorization accepts the recommended shape; source: origin fix shape plus the dispatch prompt's standing pre-authorization; 2026-09-24; affected: Task 1; origin-2 key encoding and scope: the two keys are optional TOML arrays in the repo-scoped gitignored `.ai-playbook/facts.md` TOML fence read by a test-local loader with the current lists as fallback defaults, because the origin names the key pair but not the encoding and the recommended shape follows the repo's TOML-fence configuration convention and the test's existing `REPO_ROOT` anchor; source: origin 2's suggested fix plus the dispatch prompt's standing pre-authorization; 2026-09-24; affected: Task 3.

## Gist & Examples

TLDR: the marker recipe and the plans skill name the WRITE TARGET's project derivation (the worktree) as the keying authority so ad-hoc-worktree authoring stops tripping the gate (efficiency), and the host-surface sweep's hardcoded path lists move behind optional facts keys with in-script fallback defaults so the guard stays honest off-host and operator paths leave the public script (code-quality).

**Before (today), HIGH origin:** the marker WRITE RECIPE is silent about which cwd keys the marker. In an ad-hoc-worktree authoring session the recipe gets executed from the primary checkout's cwd (the session shell resets cwd between calls, and the natural habit is to run the documented one-liner from the checkout root). The marker lands keyed to the PRIMARY project key; the gated Write targets the worktree, whose directory walk derives a DIFFERENT project key; the consult finds no fresh marker under the worktree key and blocks the plan-file write. The witnessing P51 authoring session recovered only after diagnosing the mismatch from the marker directory listing and re-running the write from inside the worktree.

**After (this plan), HIGH origin:** recipe step 4 states the prescription (the project key MUST come from the WRITE TARGET's project derivation; the consult keys from the directory its adapter supplies: the hook payload's cwd with the Claude and Cursor dirname fallback, else the core's process cwd), step 5 documents the already-existing `--cwd` pass-through, and the plans skill's marker duty repeats the prescription in one sentence. A linked-worktree selftest pins the semantics end to end: a marker keyed to the primary does NOT admit a worktree consult, a marker keyed to the worktree does, and `--write-marker --cwd <worktree>` keys the worktree directly. Gate code does not change: today's gate already behaves correctly; the defect is that the documented recipe steers sessions into the wrong keying.

**Before (today), LOW origin:** `HOME_ENTRYPOINT_FILES` and `HOME_HOOK_CONFIG_FILES` hardcode this operator's five home entrypoint files and five hook-config paths with an exists-then-skip design. On any other machine every path is absent, the test skips, and the reintroduction guard silently covers only repo surfaces. The operator-specific path list also lives in a public repo script rather than externalized configuration.

**After (this plan), LOW origin:** the sweep reads optional `home_entrypoint_files` / `home_hook_config_files` TOML-array keys from the repo-scoped gitignored `.ai-playbook/facts.md` fence, falling back to the in-script `DEFAULT_*` lists when the file, the fence, or the keys are absent (and when a present value is malformed, with a stderr warning naming the key). The skip stays recorded and disclosed exactly as today. On this operator's host the suite keeps sweeping the real surfaces; on any other machine the skip now names the externalization as the remedy. Loader unit tests pin override, fallback, and malformed-input behavior.

Non-goals: no gate-core or adapter code change (the empty-cwd fallback and `--cwd` already exist; this plan documents and pins them), no change to the learn-class recipe text (its step 4 inherits the derivation prescription by reference), no removal of the exists-then-skip design (the repo-side twin carries the always-on coverage), and no backlog-file moves (both items stay in `docs/history/backlog/` while this plan is open).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the linked-worktree selftest reproduces the HIGH origin's three-step scenario and pins all three observable outcomes (primary-keyed DENY, worktree-keyed ALLOW, CLI `--cwd` keying); the loader unit tests pin override, fallback, and malformed-input fallback as three separate witnesses.
- maintainability: both doc prescriptions have the README recipe as their single authority; the loader mirrors the existing fence-walk precedent instead of widening the shared scalar parser; every new prose element carries dated P58 attribution the way P57's edits do.
- validation: the skill-gate selftest suite and the harness policy contract suite exit 0 on the final tree, `scripts/plan_readiness.py` exits 0 on the final plan bytes, the hygiene scan exits 0, and the Task 1 polarity probes are demonstrated RED on today's tree before they flip GREEN.

**Done when:**
- All tasks checked; the full Validation Commands block exits 0 on the final tree (the readiness gate passes only after the review sidecar for the final bytes exists).
- `git diff --name-only` over the branch lists exactly the four declared surface files plus this plan file and no runtime driver or adapter script.
- The authoring-time execution record in the session notes shows: selftest and contract suites GREEN today, the three Task 1 spans RED today (absent), the Task 3 loader absent today (Task 3 gates RED until implemented), and the readiness gate failing only for the absent review sidecar.

**Ship when:**
- The next ad-hoc-worktree authoring session runs the marker write keyed to the worktree (from inside it or via `--cwd`) without a blocked-write diagnosis loop; observed by that session's marker filename carrying the worktree project key. Operational adoption evidence; prose only, no checklist item.

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code:**
- `agents/skills/plans/SKILL.md` (marker duty sentence only; the rest of the skill is frozen)
- `agents/hooks/skill-gate/README.md` (plans-class Marker WRITE RECIPE steps 4 and 5 only; the learn-class recipe and wiring sections are frozen)

**Tests:**
- `scripts/skill_gate.py` (selftest additions only, inside `selftest()`; ALL other functions and constants in the file are frozen; reject any review finding that touches them)
- `scripts/test_harness_policy_contract.py` (the externalized loader plus the three new loader unit tests and the rename rewiring; the single scope row for this file lives here, not under Production code)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/hooks/skill-gate/*.sh` adapters; reason: the empty-cwd fallback they implement is referenced as expected behavior, not edited.
- `scripts/facts_paths.py`; reason: the shared scalar fence parser is deliberately not widened; a finding demanding its widening is a design decision for a separate plan.
- `docs/history/backlog/2026-09-23-skill-gate-marker-worktree-project-key.md` and `docs/history/backlog/2026-09-23-host-entrypoint-sweep-portability.md`; reason: both items stay in place while this plan is open; they move to completed only at execution closeout.
- `agents/hooks/skill-gate/README.md` learn-class recipe and host-wiring sections; reason: unchanged by this plan.

## Validation Commands

```bash
set -u
REPO="$(git rev-parse --show-toplevel)" || exit 1
cd "$REPO" || exit 1
fail() { echo "VALIDATION FAIL: $1"; exit 1; }
# Exactly-once presence with the three-way exit split (rule 10): rc 0 = matched,
# rc 1 = clean no-match (fails the count), rc >= 2 = tool error (fails loud).
# The grep result is captured through a temp file so the exit code is read
# directly ($?) and never through PIPESTATUS, which is unbound after a
# command substitution under set -u (r1 F1/F5).
expect_once() {
  [ -f "$2" ] || fail "missing presence-check target: $2"
  hits=$(mktemp) || fail "mktemp failed"
  grep -oF -- "$1" "$2" >"$hits" 2>/dev/null
  rc=$?
  n=$(wc -l <"$hits" | tr -d ' ')
  rm -f "$hits"
  if [ "$rc" -ge 2 ]; then fail "grep tool error rc=$rc on $2: $1"; fi
  if [ "$n" -ne 1 ]; then fail "span not exactly once in $2 (n=$n): $1"; fi
}
# At-least-once presence, same polarity split and same direct-rc capture.
expect_present() {
  [ -f "$2" ] || fail "missing presence-check target: $2"
  hits=$(mktemp) || fail "mktemp failed"
  grep -oF -- "$1" "$2" >"$hits" 2>/dev/null
  rc=$?
  n=$(wc -l <"$hits" | tr -d ' ')
  rm -f "$hits"
  if [ "$rc" -ge 2 ]; then fail "grep tool error rc=$rc on $2: $1"; fi
  if [ "$n" -lt 1 ]; then fail "span absent from $2: $1"; fi
}
# Region-scoped exactly-once: the region extractor must produce non-empty
# output (fail-closed anchor), then the span is counted inside it; temp files
# are removed on every path (r1 F1/F5: direct rc capture, no PIPESTATUS).
expect_once_region() {
  [ -f "$3" ] || fail "missing region-check target: $3"
  region=$(mktemp) || fail "mktemp failed"
  spans=$(mktemp) || { rm -f "$region"; fail "mktemp failed"; }
  awk "$1" "$3" >"$region"
  if [ ! -s "$region" ]; then rm -f "$region" "$spans"; fail "region extraction empty in $3 (broken anchor)"; fi
  grep -oF -- "$2" "$region" >"$spans" 2>/dev/null
  rc=$?
  n=$(wc -l <"$spans" | tr -d ' ')
  rm -f "$region" "$spans"
  if [ "$rc" -ge 2 ]; then fail "grep tool error rc=$rc in region of $3: $2"; fi
  if [ "$n" -ne 1 ]; then fail "span not exactly once in region of $3 (n=$n): $2"; fi
}
# Forbidden regex with the three-way split: rc 0 = forbidden match (fail),
# rc 1 = clean absence (pass), rc >= 2 = tool error (fail loud).
expect_absent_re() {
  [ -f "$2" ] || fail "missing absence-check target: $2"
  grep -qE -- "$1" "$2" 2>/dev/null
  rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden pattern present in $2: $1"; fi
  if [ "$rc" -ge 2 ]; then fail "grep tool error rc=$rc on $2"; fi
}

# 1. Skill-gate selftest suite, including the two new worktree-keying selftests
#    (Task 2). The full suite is the gate; the new tests' labels must appear in
#    its output, which rules out a vacuous filter pass.
SELFTEST_OUT="$(python3 scripts/skill_gate.py --selftest 2>&1)" || fail "skill_gate selftest suite exited non-zero"
printf '%s\n' "$SELFTEST_OUT" | grep -qF "project_worktree_target_not_admitted_by_primary_marker" \
  || fail "linked-worktree keying selftest label missing from selftest output"
printf '%s\n' "$SELFTEST_OUT" | grep -qF "write_marker_cli_cwd_passthrough_keys_worktree" \
  || fail "write-marker CLI --cwd selftest label missing from selftest output"
printf '%s\n' "$SELFTEST_OUT" | grep -qE "^FAIL: " \
  && fail "selftest output reports a failed check"

# 2. Harness policy contract suite, including the three new loader unit tests
#    (Task 3); green on hosts without the optional facts keys (fallback path).
CONTRACT_OUT="$(python3 scripts/test_harness_policy_contract.py -v 2>&1)" || fail "harness policy contract suite exited non-zero"
printf '%s\n' "$CONTRACT_OUT" | grep -qF "test_home_surface_lists_override_from_facts_keys" \
  || fail "loader override test missing from contract suite output"
printf '%s\n' "$CONTRACT_OUT" | grep -qF "test_home_surface_lists_fallback_defaults" \
  || fail "loader fallback test missing from contract suite output"
printf '%s\n' "$CONTRACT_OUT" | grep -qF "test_home_surface_lists_rejects_malformed_values" \
  || fail "loader malformed-input test missing from contract suite output"
printf '%s\n' "$CONTRACT_OUT" | grep -qE "^(FAIL|ERROR): |^FAILED" \
  && fail "contract suite reports a failure or error"

# 3. Marker-keying prescriptions landed (Task 1): one dedicated probe per
#    surface. README probes are region-scoped to the plans-class recipe so the
#    untouched learn-class text can never satisfy them.
PLANCLASS_AWK='/^## Marker WRITE RECIPE \(plans class\)/{f=1;next} /^## Marker WRITE RECIPE \(learn class\)/{f=0} f'
expect_once "keyed to the WRITE TARGET's project derivation" agents/skills/plans/SKILL.md
expect_once "never from the session's default or primary-checkout cwd" agents/skills/plans/SKILL.md
expect_once_region "$PLANCLASS_AWK" "never the session's default or primary-checkout cwd" agents/hooks/skill-gate/README.md
expect_once_region "$PLANCLASS_AWK" "falling back to the write target's dirname when the payload carries none" agents/hooks/skill-gate/README.md
expect_once_region "$PLANCLASS_AWK" "--cwd <write-target project root>" agents/hooks/skill-gate/README.md

# 4. Host-sweep externalization landed (Task 3): renamed fallback constants,
#    the optional facts keys, the loader helper, and the recorded skip are all
#    present; the bare pre-rename constant assignments are gone (negated).
expect_once "DEFAULT_HOME_ENTRYPOINT_FILES = [" scripts/test_harness_policy_contract.py
expect_once "DEFAULT_HOME_HOOK_CONFIG_FILES = [" scripts/test_harness_policy_contract.py
expect_present "home_entrypoint_files" scripts/test_harness_policy_contract.py
expect_present "home_hook_config_files" scripts/test_harness_policy_contract.py
expect_present "_load_home_surface_lists" scripts/test_harness_policy_contract.py
expect_present "skipTest" scripts/test_harness_policy_contract.py
expect_absent_re "^HOME_ENTRYPOINT_FILES = \[" scripts/test_harness_policy_contract.py
expect_absent_re "^HOME_HOOK_CONFIG_FILES = \[" scripts/test_harness_policy_contract.py

# 5. Readiness gate on the final plan bytes (requires the latest review round's
#    .stats.json sidecar with a matching source_digest).
python3 scripts/plan_readiness.py docs/plans/2026-09-24-p58-marker-worktree-key-and-sweep-portability.md \
  || fail "plan readiness gate"

# 6. Public-hygiene scan over the full tracked tree (anchored to this repo).
bash scripts/scan-public-hygiene.sh || fail "public hygiene scan"
```

### Task 1: Prescribe the worktree keying in the marker surfaces

Files:
- `agents/skills/plans/SKILL.md`
- `agents/hooks/skill-gate/README.md`

Non-behavior doc edits; the exact prescribed insertions follow. They add one prescriptive sentence to the plans skill's marker duty and one to the README recipe's step 4, plus the `--cwd` pass-through mention in step 5's CLI line (the mechanical alternative, already implemented by the core). No em-dashes; the wording is byte-pinned by the Validation Commands probes.

- [x] In `agents/skills/plans/SKILL.md`, inside the **Writing** paragraph's marker-duty sentence, immediately after "not only at create-only Phase 0." and before "This skill and the gate adapter share", insert exactly: [class: IMPLEMENTATION_REQUIRED]

```
In an ad-hoc-worktree session the marker MUST be keyed to the WRITE TARGET's project derivation (the worktree root): run the recipe CLI from inside the worktree or pass `--cwd <write-target project root>`, never from the session's default or primary-checkout cwd.
```


- [x] In `agents/hooks/skill-gate/README.md`, Marker WRITE RECIPE (plans class) step 4, append to the end of the step-4 item exactly (leading space): [class: IMPLEMENTATION_REQUIRED]

```
 In an ad-hoc-worktree session the project key MUST come from the WRITE TARGET's project derivation (the worktree root), never the session's default or primary-checkout cwd; the gate consult keys from the directory its adapter supplies (Claude and Cursor pass the hook payload's cwd, falling back to the write target's dirname when the payload carries none; agy and Codex pass none and the core keys from its own process cwd), so the marker write must key the same write-target derivation the consult will use.
```


- [x] In `agents/hooks/skill-gate/README.md`, same recipe step 5, replace the CLI line and its parenthetical exactly: [class: IMPLEMENTATION_REQUIRED]

```
5. CLI: `python3 ~/.ai-playbook/scripts/skill_gate.py --write-marker [--cwd <write-target project root>] [--session-id "$SID"]`
   (bare `--write-marker` defaults to the plans class; `--cwd` keys the marker to an explicit project root such as an ad-hoc worktree, independent of the invoking shell's cwd - the core already accepts it for both consult and write).
```


- [x] Run → expect RED before the edits and GREEN after (these three spans are the probes; the authoring-time record shows them RED today): `grep -oF "never from the session's default or primary-checkout cwd" agents/skills/plans/SKILL.md | wc -l` returns 0 before, 1 after; the two README region probes behave the same against the plans-class recipe region [class: REPOSITORY_TEST]
- [x] Run → expect GREEN (unchanged by this task, recorded as the no-regression witness): `python3 scripts/skill_gate.py --selftest` exits 0 [class: REPOSITORY_TEST]
- [x] Commit: `docs: key the plans skill-gate marker to the write target's project (P58)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pin the worktree keying semantics with linked-worktree selftests

Files:
- `scripts/skill_gate.py` (new selftest branches inside `selftest()` only; everything else in the file is frozen)

These selftests pin CURRENT gate semantics (the HIGH origin's defect is doc-side), so they are GREEN on arrival; they are the regression fence against a future keying "fix" that aliases a worktree to its primary or drops the `--cwd` pass-through. Reuse the existing in-`selftest()` helpers (`make_git_repo`, `isolated_home`, `run_consult`, `write_marker_at`, `check`); fixture placement is inside `tempfile.TemporaryDirectory()` (teardown by the context manager; no host-tree leakage).

- [x] Add selftest `project_worktree_target_not_admitted_by_primary_marker`; given a temp git repo with `docs/plans/` committed and a LINKED worktree created via `git -C <primary> worktree add <wt>` (not a second standalone repo), when a marker is written keyed to the PRIMARY root (`write_marker_at(start_dir=<primary>)`, session `sess-WT`) and a consult runs for `<wt>/docs/plans/new.md` started from `<wt>` with the same session, expect DENY (the primary-keyed marker does not admit the worktree target); then when a second marker is written keyed to `<wt>` (`write_marker_at(start_dir=<wt>)`), the same consult expect ALLOW; and expect that neither resolve logged `keying=no-anchor` (both git anchors resolved, discriminating linked-worktree keying from the non-git fallback) [class: REPOSITORY_TEST]
- [x] Add selftest `write_marker_cli_cwd_passthrough_keys_worktree`; given the same linked-worktree fixture under an isolated `HOME`, when the CLI runs as a subprocess `[sys.executable, <CORE>, "--write-marker", "--cwd", str(<wt>), "--session-id", "sess-WTCLI"]` with the subprocess `HOME` set to the isolated home, expect exit 0 and a marker under `<home>/.ai-playbook/runtime/skill-invoked/` whose filename carries `sha1(realpath(<wt>))[:16]`, and a subsequent in-process consult for `<wt>/docs/plans/new.md` started from `<wt>` with session `sess-WTCLI` expect ALLOW with no second write [class: REPOSITORY_TEST]
- [x] Run → expect GREEN on arrival (pins current semantics, including the existing `--cwd` flag): `python3 scripts/skill_gate.py --selftest` exits 0 AND its output lists both new check labels [class: REPOSITORY_TEST]
- [x] Commit: `test: pin skill-gate worktree keying and the --cwd write-marker pass-through (P58)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Externalize the host sweep's surface lists to optional facts keys

Files:
- `scripts/test_harness_policy_contract.py`

The rename, loader, and unit tests land together; the sweep test body keeps working through the module-level names. The loader is test-local: it mirrors `facts_paths.py`'s first-```toml fence walk (opening fence to its closer) and parses the block with `tomllib`; it does NOT import or widen `facts_paths.resolve_toml_key_raw` (scalar-only, docstring-pinned single source). The skip design and its recorded message stay exactly as today.

- [x] Rename `HOME_ENTRYPOINT_FILES` to `DEFAULT_HOME_ENTRYPOINT_FILES` and `HOME_HOOK_CONFIG_FILES` to `DEFAULT_HOME_HOOK_CONFIG_FILES` (contents unchanged); bind module-level `HOME_ENTRYPOINT_FILES` / `HOME_HOOK_CONFIG_FILES` to the loader results so `test_removed_controls_absent_from_active_entrypoints` needs no body change [class: IMPLEMENTATION_REQUIRED]
- [x] Add `_load_home_surface_lists(facts_path=None)`: read the repo-scoped `.ai-playbook/facts.md` (default `REPO_ROOT / ".ai-playbook" / "facts.md"`; the parameter exists for the unit tests), extract the FIRST TOML-fenced block, `tomllib.loads` it, and read optional array keys `home_entrypoint_files` / `home_hook_config_files`; a missing file, missing fence, or missing key falls back to the corresponding `DEFAULT_*` list; a PRESENT but malformed value (not a non-empty list of non-empty strings) is also ignored with a one-line stderr warning naming the key and the fallback, so a typo'd override cannot silently no-op; the loader never raises [class: IMPLEMENTATION_REQUIRED]
- [x] `HarnessPolicyContractTest#test_home_surface_lists_override_from_facts_keys`; given a temp facts file whose TOML fence sets `home_entrypoint_files = ["~/zcode/AGENTS.example.md"]` and `home_hook_config_files = ["~/agents/hooks.example.json"]`, the loader returns exactly those two lists (tilde expansion stays the sweep's job via the existing `_home_files`) [class: REPOSITORY_TEST]
- [x] `HarnessPolicyContractTest#test_home_surface_lists_fallback_defaults`; given a nonexistent facts path, a facts file with NO TOML fence at all, and a facts file whose fence omits both keys, the loader returns the `DEFAULT_HOME_ENTRYPOINT_FILES` and `DEFAULT_HOME_HOOK_CONFIG_FILES` lists unchanged in all three cases [class: REPOSITORY_TEST]
- [x] `HarnessPolicyContractTest#test_home_surface_lists_rejects_malformed_values`; given keys bound to a bare string and to a list containing a non-string element, the loader falls back to the defaults instead of raising AND its stderr carries the warning naming the offending key [class: REPOSITORY_TEST]
- [x] Update the module docstring's inventory paragraph and the constants' comments: the surface lists are externalizable via the two optional facts keys, the in-script lists are the fallback default, and the exists-then-skip with its recorded message is unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: `python3 scripts/test_harness_policy_contract.py -k home_surface_lists` passes all three new tests, then the full file suite exits 0 (on this host the entrypoint sweep still runs for real; off-host it still skips with its recorded message) [class: REPOSITORY_TEST]
- [x] Commit: `feat: externalize host-sweep surface lists to optional facts keys (P58)` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Final validation

Files: none (verification only; no commit belongs to this task)

- [x] Run → expect GREEN (all gates, final tree; the readiness gate passes here because the review sidecar for the final bytes exists by this point): the full `## Validation Commands` block exits 0 [class: REPOSITORY_TEST]
- [x] Record the receipts (suite outputs, probe counts, readiness verdict, hygiene exit code) in the session notes beside the authoring-time execution record [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- docs/history/backlog/completed/2026-09-23-host-entrypoint-sweep-portability.md: disposition folded into 2026-09-24-p58-marker-worktree-key-and-sweep-portability.md (2026-09-25); per-item file deleted.
