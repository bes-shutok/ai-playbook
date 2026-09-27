# Plan: Done-gate manifest root truth and deployed-lib refresh routing

Backlog origins (scope of record):
- docs/history/backlog/2026-09-25-done-sweep-gates-lib-write-manifest-flag-drift.md
- docs/history/backlog/2026-09-27-run-start-marker-exec-review-follow-ups.md

Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-27-plan-review-done-gate-manifest-deployed-lib-truth-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Make the done Step 0 run manifest and the run-start marker parser truthful about repo identity, and give the deployed sweep-gates lib lag a routed, self-diagnosing refresh remedy.

- Run manifests under `{tmp_dir}/done-session/` record the repo-root digest and repo-relative paths, so the docs-branch shadow sync never carries raw local paths inside them; this completes the run-start-marker plan's Outcome one artifact over (its review deferred the manifest leak to a dedicated small plan, which this is).
- A 3-field marker whose 64-hex identity token does not match this repo resolves to None directly, never through a CWD-dependent path-resolution fallback, in both parser arms.
- The done skill names the stale-deployment signature for the Step 0 lib (an `unrecognized arguments` error on a documented write-manifest flag) with the copy remedy, so the flag-drift incident class self-diagnoses and routes at the next done boundary instead of costing an investigation.
- A mixed-format session window (legacy raw-path previous marker plus digest-format current marker) is pinned by a test, closing the recorded coverage gap.

## Terms

- **Run manifest**: `run-manifest-<run_id>.json` under `{tmp_dir}/done-session/`; the done Step 0 ownership record written by `write-manifest` in `scripts/done_sweep_gates_lib.py`.
- **Run-start marker**: `run-start-<UTCtimestamp>` under `{tmp_dir}/done-session/`; current writers record a 64-hex SHA-256 digest of the trailing-slash-stripped resolved repo root as the middle field; legacy markers recorded the raw path.
- **Runtime home**: `~/.ai-playbook/scripts/`, the deployed-copy destination; the repo copy under `scripts/` is always the source, never the reverse.
- **Claim-or-foreign**: the Step 0 rule that every staging review candidate on disk is either claimed (`--owned-review`) or marked foreign (`--foreign-review`, `--foreign-review-from`, `--claim-none`).
- **Docs-branch shadow sync**: the flow that mirrors `{tmp_dir}/done-session/` artifacts onto the `docs` branch; raw local paths inside synced artifacts leak the host layout.
- **Staging doc**: a review artifact under `{reviews_dir}/` that a done run either finalizes (owned) or preserves as a peer's (foreign).

## Assumptions

- assume the manifest `repo_root` field content swaps to the same 64-hex digest the markers record and `MANIFEST_SCHEMA_VERSION` stays 1; basis: origin fix shape ("record the same digest in the manifest"), `RunManifest.from_dict` accepts any non-empty string, and `_manifest_root_matches` gaining the marker-identical two-arm rule keeps legacy raw-path manifests loadable.
- assume the manifest path lists (`foreign_review_paths`, `owned_review_paths`, `owned_plan_paths`) are relativized at write time, not digested; basis: the `--claim-none` branch already writes repo-relative foreign paths into the same field (existing convention and existing test `test_write_manifest_claim_none_marks_all_candidates_foreign` asserts relative paths), and the origin offers "digest or relativize" with relativize matching that convention.
- assume the runtime-home redeploy is a Ship-when operations condition, not an executable task; basis: the plans-skill checklist inclusion gate (a deployment to a target environment is exception-only) and the readiness validator's Ship-when-only classes (`OPERATIONS_FOLLOW_UP` may not sit on a task item); the widened stale-deployment signature routes the refresh inline at the next done boundary, exactly like the existing doc-registry remedy.
- assume the deployed lag covers both `done_sweep_gates_lib.py` and `done_sweep_gates.sh`; basis: authoring-time digest comparison against main 9071a1e8 on 2026-09-27 showed both deployed copies differ from the repo copies, and the deployed lib probe rejects `--claim-none` with `error: unrecognized arguments` (evidence recorded in the Gist).
- assume `_marker_records_other_repo` hardens together with `_parse_marker`; basis: both share the same hex-token fallthrough shape, and fixing one family member while the sibling keeps the CWD-dependent resolution would let the sibling re-mask the defect class.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: run manifests record a repo-root digest and repo-relative paths instead of raw local paths, the marker parser resolves hex mismatches directly instead of falling through to a CWD-dependent arm, and the done skill names the stale-lib signature while the deployed pair refresh becomes a routed operations condition, closing the write-manifest flag drift for code-quality.

Today the manifest writer stores `str(ctx.repo_root)` (absolute) plus verbatim `--foreign-review` inputs (absolute whenever they are answered from the claim-or-foreign error, which prints absolute candidate paths, because the enumeration universe is built from `ctx.repo_root / rel`). Example: a done run in a server checkout writes `"repo_root": "/opt/work/repos/proj"` into `run-manifest-<run_id>.json`, and the docs-branch shadow sync then carries that path; the run-start-marker plan removed exactly this leak class from the markers one artifact over. After this plan the same manifest records the 64-hex digest of the trailing-slash-stripped resolved root (the same value the marker's middle field carries) and repo-relative paths, and `_manifest_root_matches` accepts a manifest when its recorded digest matches or its legacy raw path matches, so pre-fix manifests stay loadable and adoptable; adopting a legacy manifest relativizes the inherited paths into the new record.

The parser hardening closes the same family: a 3-field marker whose middle field is a 64-hex token but not this repo's digest returns None directly; today it falls through to the legacy realpath arm and resolves the hex token against the process CWD (not accident-reachable today, since absolute paths contain `/` and cannot fullmatch hex, but strictly safer to close), and the sibling classifier `_marker_records_other_repo` gets the same short-circuit with the same classification outcome as today.

The deployment lag is observed, not hypothetical: the deployed runtime-home copy of the lib predates the F13 bulk flags. Probe recorded 2026-09-27: `python3 ~/.ai-playbook/scripts/done_sweep_gates_lib.py write-manifest --claim-none` exits 2 with `error: unrecognized arguments: --claim-none` and a usage line naming only the four base flags, while the repo copy's `write-manifest --help` lists `--foreign-review-from FILE` and `--claim-none`; the backlog origin re-hit this at four done boundaries of one execution run. The remedy routing lands in the done skill as a stale-deployment signature paragraph beside the Step 0 recipe, and the actual redeploy is the Ship-when condition below.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a digest-root manifest round-trips through `from_dict` and `load_run_manifest`; legacy raw-path manifests still load; foreign roots (absolute path or foreign digest) are rejected; adoption of a legacy manifest relativizes inherited paths.
- compatibility: existing marker semantics unchanged (`RunMarker` parsing, session-window anchoring, legacy acceptance); the full hermetic lib and wrapper suites stay green.
- observability: the manifest bytes carry zero absolute local paths for in-root inputs; out-of-root foreign inputs are recorded verbatim by prescription and stay outside this invariant; the docs-branch shadow sync inherits the in-root property automatically.
- documentation truth: the done skill's content-confirmation sentence is grammatical, and the stale-lib signature names the exact error text and the copy remedy with the `.bak-<date>` preservation.

**Done when:**
- All new and updated tests in `scripts/test_done_sweep_gates_lib.py` pass, and the full `scripts/test_done_sweep_gates_lib.py` plus `scripts/test_done_sweep_gates_wrapper.py` suites pass.
- The Validation Commands block exits 0 when run from the repository root after all tasks land.

**Ship when:**
- The runtime-home copies of the sweep-gates pair (`done_sweep_gates_lib.py`, `done_sweep_gates.sh`) are refreshed from the repo (repo is the source, the runtime home is the destination, never the reverse), preserving the `.bak-<date>` precedent by moving each live copy aside before the copy. Closure evidence: `python3 ~/.ai-playbook/scripts/done_sweep_gates_lib.py write-manifest --help` lists `--foreign-review-from FILE` and `--claim-none`, and the deployed pair digests equal the repo copies'. Evidence owner: the operator of the next done run in the primary checkout (the widened stale-deployment signature routes this refresh inline, the same way the doc-registry remedy works), or the user on any host where the runtime home exists. [class: OPERATIONS_FOLLOW_UP]

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (scoped: the new `_repo_root_digest` and `_repo_relative` helpers, `_marker_digest_matches`, `_parse_marker`, `_marker_records_other_repo`, `_manifest_root_matches`, the `RunManifest` docstring, and the `_cmd_write_manifest` write site plus its merge block; all other functions are frozen; reject any review finding that touches them)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (scoped: the tests named in the tasks plus their helpers; all other tests frozen)

**Documentation:**
- `agents/skills/done/SKILL.md` (two regions only: the docs-tmp-sweep content-confirmation sentence, and the new stale-deployment signature paragraph beside the Step 0 run-manifest recipe; all other content is frozen)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- Symlink deployment of the sweep-gates pair into the runtime home; reason: the single deployment convention is an open deferral the origin itself defers to, and the `.bak-<date>`-preserving copy remedy plus the widened signature cover recurrence until that decision lands.
- `agents/skills/done/SKILL.md` Step 0 echo paragraph content-confirmation construction ("content confirmation compares the marker's recorded digest against..."); reason: grammatical as written and not named by any origin.
- Stale-deployment signatures of other gates (doc-registry, plan-readiness); reason: each already carries its own remedy; this plan widens only the Step 0 lib's routing.

## Design Invariants (CR Guard)

- The manifest schema stays version 1: no `MANIFEST_SCHEMA_VERSION` bump; `from_dict` tolerant parsing is unchanged.
- Legacy acceptance is preserved: raw-path run-start markers keep anchoring windows, and raw-path manifests keep loading and adoptable, via the two-arm root match.
- The run-start marker format is untouched: field order (epoch, identity token, PID), digest derivation (`sha256` of the trailing-slash-stripped resolved root), and "the raw repo-root path is never recorded" stay exactly as the done Step 0 recipe prescribes.
- The claim-or-foreign matching semantics are unchanged: candidate matching keeps resolving through realpath, so relativizing stored paths never changes which candidates count as covered.

## Validation Commands

Preamble record (authoring time, main 9071a1e8 worktree bytes, 2026-09-27): the rule 29 pre-round mechanical gates ran over the final plan bytes: `bash scripts/check-no-em-dash.sh touched` exited 0, the public hygiene scan exited 0, and `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-09-27-done-gate-manifest-deployed-lib-truth.md` reported no structural problem (the no-review-artifact class is immune in pre-round mode by construction). The rule 22 mechanical audit (every pinned span below occurs in the plan's prescribed task text or in the target file's current bytes as a RED-today guard, with the G4 count pins collision-checked against the existing doc-registry label) and `bash -n` over this block both passed. The test commands resolve a pytest-capable interpreter (the repo's isolated test venv first, ambient python3 as fallback), because the ambient python3 on the authoring host carries no pytest. RED-today execution record (whole block against the current tree): G1 failed first, as required, with the selection empty (54 existing tests deselected: the Task 1 and Task 2 tests do not exist yet); G3 failed first at its `must_match` line (the matches-form is absent today) while its forbidden pin fired (the matching-form is present at the docs-tmp-sweep bullet) and its tail-survival count already reads 1 (it pins what must survive); G4 read 0 on all three count pins (expected 1 after Task 3); G5's forbidden pin fired (the writer literal is present today). G2 passed today (56 passed) and must stay green. The block was re-executed after the final fold touched the G1 selection, with the same observed outcomes. A later comprehensive fold (done-time sensitive-data scan fix moving the illustrative leak example to a non-machine path, plus the r3 Low folds scoping the observability invariant and pinning the mixed-format test's compare-side root convention) touched no validation gate line; the mechanical gates were re-run green on the resulting bytes before certification round 4.

```bash
# Run from the repository root. G1 proves the Task 1 and Task 2 behavior
# tests; G2 the full suites; G3-G5 the done-skill and writer contracts.
REPO_TOP="$(git rev-parse --show-toplevel)" || { echo "not a git repo" >&2; exit 1; }
cd "$REPO_TOP" || exit 1
SKILL="agents/skills/done/SKILL.md"
LIB="scripts/done_sweep_gates_lib.py"

fail() { echo "VALIDATION FAIL: $*" >&2; exit 1; }
must_match() { grep -qF -- "$2" "$1" || fail "required pattern absent from $1: $2"; return 0; }
no_match() {
  rc=0
  grep -qF -- "$2" "$1" || rc=$?
  if [ "$rc" -eq 0 ]; then fail "forbidden pattern present in $1: $2"; fi
  if [ "$rc" -ge 2 ]; then fail "grep error rc=$rc scanning $1"; fi
  return 0
}
count_is() { n="$(grep -oF -- "$2" "$1" | wc -l | tr -d ' ')"; [ "$n" -eq "$3" ] || fail "count of '$2' in $1 is $n, expected $3"; }

# Resolve a pytest-capable interpreter: the repo's isolated test venv first,
# then the ambient python3 (fail loud when neither carries pytest).
TEST_PY="$HOME/.agents/venvs/ai-playbook-test/bin/python3"
if [ ! -x "$TEST_PY" ]; then TEST_PY="$(command -v python3)"; fi
"$TEST_PY" -m pytest --version >/dev/null 2>&1 || fail "no pytest-capable interpreter (looked for the ai-playbook-test venv, then python3 -m pytest)"

# G1: new behavior tests (RED until the owning task lands)
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py -q -k "manifest_records_repo_root_digest or write_manifest_relativizes_absolute_foreign_input or write_manifest_relativizes_symlink_aliased_foreign_input or write_manifest_relativizes_inherited_paths_on_adopt or manifest_root_matches_digest_and_legacy_arms or load_run_manifest_accepts_digest_root_and_rejects_foreign_digest or parse_marker_hex_mismatch_returns_none_without_realpath or session_window_mixed_format_legacy_prev_digest_current" || fail "G1 new-behavior selection failed"

# G2: full hermetic suites (green today; must stay green)
"$TEST_PY" -m pytest scripts/test_done_sweep_gates_lib.py scripts/test_done_sweep_gates_wrapper.py -q || fail "G2 full suite failed"

# G3: content-confirmation sentence reworded (forbidden pin is RED-today proven)
must_match "$SKILL" "recorded digest matches the SHA-256 hex digest"
no_match "$SKILL" "digest matching the SHA-256"
count_is "$SKILL" "resolved repo root, computed as in Step 0, is content-confirmable" 1

# G4: stale-deployment signature paragraph present exactly once per span
must_match "$SKILL" "Stale-deployment signature (Step 0 lib)"
count_is "$SKILL" "Stale-deployment signature (Step 0 lib)" 1
must_match "$SKILL" "unrecognized arguments"
count_is "$SKILL" "unrecognized arguments" 1
must_match "$SKILL" ".bak-<date>"
count_is "$SKILL" ".bak-<date>" 1
must_match "$SKILL" "not a lib defect to investigate"

# G5: the writer no longer records the raw repo root (the plan embeds this
# literal as the checker string; the sweep targets the lib file only)
no_match "$LIB" 'repo_root=str(ctx.repo_root)'
```

### Task 1: Manifest records the digest root and repo-relative paths

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

- [x] Write the six new tests in `scripts/test_done_sweep_gates_lib.py`; every digest expectation and digest-format construction in them derives from the resolved root spelling `str(root.resolve())` (the spelling `GateContext.discover` records, since it `.resolve()`s `DONE_SWEEP_REPO_ROOT`; the raw `mktemp_repo`/mkdtemp spelling differs on macOS hosts, so a digest pinned from `str(root)` can never match the recorded one): `test_write_manifest_records_repo_root_digest` (given a `write-manifest` run in a fixture repo with a content-bearing marker, expects `payload["repo_root"]` to equal `hashlib.sha256(str(root.resolve()).rstrip("/").encode()).hexdigest()` and `str(root)` to be absent from the manifest bytes); `test_write_manifest_relativizes_absolute_foreign_input` (given `--foreign-review <absolute path under the fixture root>`, expects `foreign_review_paths == ["docs/reviews/<candidate>.md"]` and `str(root)` absent from the bytes); `test_write_manifest_relativizes_symlink_aliased_foreign_input` (given a symlink alias directory pointing at the fixture repo root, constructed as `alias = tmp_path / "alias-link"` then `alias.symlink_to(root, target_is_directory=True)`, and a `--foreign-review` input spelled through the alias as `str(alias / "docs" / "reviews" / "candidate.md")`, expects the stored path to be the repo-relative `docs/reviews/candidate.md`, which discriminates the resolve-first helper from a lexical containment check); `test_write_manifest_relativizes_inherited_paths_on_adopt` (given a seeded legacy manifest recording the absolute root plus an absolute owned review path and an absolute foreign path, when the new run adopts it and also passes `--foreign-review` naming the relative form of that same foreign path, expects the new manifest to record the digest root and repo-relative owned and foreign paths with the shared path recorded exactly once and `str(root)` absent); `test_manifest_root_matches_digest_and_legacy_arms` (given `_manifest_root_matches` called with the digest of `str(root.resolve())`, a legacy absolute path spelling, a foreign repo's digest, and a foreign absolute path, expects True, True, False, False); `test_load_run_manifest_accepts_digest_root_and_rejects_foreign_digest` (given a seeded manifest whose `repo_root` is the digest of `str(root.resolve())`, expects the loader to return it; given one seeded with a foreign repo's digest, expects None). Reuse the existing `mktemp_repo`, `make_marker`, `_seed_run_manifest`, and `DONE_SWEEP_REPO_ROOT` conventions. [class: REPOSITORY_TEST]
- [x] Update the existing `test_write_manifest_creates_atomic_v1_record` final root assertion from `payload["repo_root"] == str(root.resolve())` to the digest expectation computed from the same resolved root spelling, plus the same `str(root) not in text` assertion. [class: REPOSITORY_TEST]
- [x] Run → expect RED: the G1 selection fails on the new tests (the writer still records the absolute root and verbatim absolute foreign inputs, and `_manifest_root_matches` has no digest arm). [class: REPOSITORY_TEST]
- [x] Implement in `scripts/done_sweep_gates_lib.py`: add `_repo_root_digest(repo_root)` returning `hashlib.sha256(str(repo_root).rstrip("/").encode("utf-8")).hexdigest()` and refactor `_marker_digest_matches` to compare against it; add `_repo_relative(path, repo_root)` resolving the input through `os.path.realpath` first and returning its repo-relative form when the resolved path sits under the resolved root, returning the input verbatim when resolution or the containment comparison fails (resolve-first, never a lexical `Path.relative_to` against the unresolved input, so a symlink-aliased spelling of an in-repo staging doc still relativizes); in `_cmd_write_manifest`, record `repo_root=_repo_root_digest(ctx.repo_root)` and normalize each element of the three path lists through `_repo_relative` BEFORE `_dedup_preserving_order` runs (apply the helper to the combined pre-dedup lists in the merge block, adoption merge included, so inherited legacy absolute paths relativize and a mixed absolute plus relative spelling of one path dedups to a single relative record), replacing the `--claim-none` branch's nested `repo_relative` closure with the shared helper; give `_manifest_root_matches` the two-arm rule: a 64-hex recorded root compares by `hmac.compare_digest` against `_repo_root_digest`, anything else keeps the existing realpath comparison with its OSError guard. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the G1 selection passes and the G2 full suites pass (the only existing-suite edit is the Task 1 assertion update named above; no other existing test pins the absolute root form). [class: REPOSITORY_TEST]
- [x] Commit: `fix: done run manifests record digest root and repo-relative paths` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Marker parser hex-token hardening and mixed-format window test

Files:
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

- [x] Write the two new tests in `scripts/test_done_sweep_gates_lib.py`: `test_parse_marker_hex_mismatch_returns_none_without_realpath` (given a 3-field marker whose middle field is a 64-hex token that is not this repo's digest, with `lib.os.path.realpath` monkeypatched to raise, expects `_parse_marker` to return None and `_marker_records_other_repo` to return True with neither calling realpath; and given a digest-match marker, expects `_parse_marker` to succeed under the same raising monkeypatch); `test_session_window_mixed_format_legacy_prev_digest_current` (given a legacy raw-path previous marker and a digest-format current marker for the same repo, where the digest-format marker records the digest of the resolved root spelling `str(root.resolve())` and the legacy marker records that same resolved spelling verbatim, expects `derive_session_window`, invoked with the `ctx_for(root)` context root so the compare-side spelling matches the digest arm's derivation, to anchor with anchor equal to the legacy marker, current equal to the digest marker, and `start_epoch` equal to the legacy marker's epoch). [class: REPOSITORY_TEST]
- [x] Run → expect the canary RED and the window test GREEN: `test_parse_marker_hex_mismatch_returns_none_without_realpath` fails on the current tree because the hex-mismatch fallthrough calls realpath under the raising monkeypatch, while `test_session_window_mixed_format_legacy_prev_digest_current` passes immediately (it closes a coverage gap, not a behavior defect). [class: REPOSITORY_TEST]
- [x] Harden both family members in `scripts/done_sweep_gates_lib.py`: in `_parse_marker` and `_marker_records_other_repo`, when the marker has exactly 3 fields and the middle field fullmatches 64-hex, resolve identity only by the digest comparison (return the marker on match, None on mismatch in `_parse_marker`; report cross-repo True on mismatch in `_marker_records_other_repo`), never reaching the legacy realpath arm; the legacy raw-path arm keeps its current behavior for non-hex tokens. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both Task 2 tests pass and the G2 full suites pass. [class: REPOSITORY_TEST]
- [x] Commit: `fix: done marker parser resolves hex identity tokens directly` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Done skill wording and stale-deployment signature

Files:
- `agents/skills/done/SKILL.md`

- [x] Reword the docs-tmp-sweep content-confirmation sentence: replace the span `digest matching the SHA-256 hex digest` with `digest matches the SHA-256 hex digest`; the tail that follows the replaced span reads `of this repo's resolved repo root, computed as in Step 0, is content-confirmable;` and must survive verbatim. [class: IMPLEMENTATION_REQUIRED]
- [x] Insert a new paragraph immediately after the Step 0 run-manifest recipe paragraph that ends with `never leave the ledger append and the Step 6 finalize silently disabled.`, reading exactly: `**Stale-deployment signature (Step 0 lib):** an argparse unrecognized arguments error naming a write-manifest flag this skill documents (--claim-none, --foreign-review-from) is a stale runtime-home copy of the sweep-gates lib, not a lib defect to investigate: redeploy the sweep-gates script/lib pair from the repo (repo is the source, the runtime home is the destination, never the reverse), moving each live copy aside to a .bak-<date> sibling before the copy, then re-run Step 0; never route this signature to the investigate path or the recorded-stop exception.` In the skill file the flag names and the `.bak-<date>` token carry their inline backticks exactly as in this plan's G4 pins. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the G3, G4, and G5 lines pass (the G3 forbidden pin flips from firing to clean, the G4 count pins read 1, and G5 stays clean because Task 1 already removed the writer literal). [class: REPOSITORY_TEST]
- [x] Commit: `docs: done skill stale-lib signature and content-confirmation wording` [class: IMPLEMENTATION_REQUIRED]

## Completed-backlog dispositions (completion pass 2026-09-27)

| Former backlog path | Disposition |
|---|---|
| docs/history/backlog/2026-09-25-done-sweep-gates-lib-write-manifest-flag-drift.md | Closed by this plan: the stale-deployment signature paragraph (Task 3) names the `unrecognized arguments` error and the `.bak-<date>`-preserving copy remedy, and the Ship-when condition carries the runtime-home redeploy as an OPERATIONS_FOLLOW_UP with its evidence owner. |
| docs/history/backlog/2026-09-27-run-start-marker-exec-review-follow-ups.md | Closed by this plan: item 1 (manifest raw-root leak) by Task 1, item 2 (hex-mismatch fallthrough) by Task 2, item 3 (Step 2.62 wording) by Task 3, item 4 (mixed-format window test) by Task 2. |
