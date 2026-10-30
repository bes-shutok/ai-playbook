# Plan: Hygiene scanner default scope parity

Backlog origin: `docs/history/backlog/2026-10-26-commit-scan-scope-release-gate-scope-parity.md`
Driving force: efficiency + code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-26-plan-review-hygiene-scanner-default-scope-parity-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 3.0h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/release-privacy-gate-report-and-scan-scope-parity.md (session `01a1638f-189d-7b02-9cf8-0990eb6f3dfd`)

## Terms

- **Tracked regular blob:** a Git tree entry with mode `100644` or `100755`; symlinks and gitlinks have no scannable file content.
- **Shared exclusions:** the existing scanner exclusion patterns, including the `GLOB_BODIES` policy.
- **Report-only scope:** tracked regular blobs outside the existing blocking roots are scanned; only deny-pattern matches are reported, without failing the default invocation.
- **Report record:** a `PUBLIC_HYGIENE_REPORT:` line for a matching path under Report-only scope, carrying an ASCII-only JSON-quoted path for every filename byte, or a fixed enumeration warning, or a fixed scope-unavailability warning (`patterns-unavailable`, direct invocation only); the done gate forwards only these lines as warnings.

## Why

The default commit-time hygiene scan checks only `agents/skills` and `projects`, while the release scan checks every published regular file. A green default scan can therefore miss a tracked file that the release gate later rejects.

## Gist & Examples

TLDR: Align scanned files with the release gate while keeping new default-scope matches report-only.

**Before (today):** The default scan omits tracked files under `docs/` and `scripts/`, although the release scan includes them.
**After (this plan):** The default scan covers tracked regular blobs; matches outside its current roots are reported without failing the commit scan.
Edge cases: Skip symlinks and gitlinks, keep explicit modes unchanged, and surface enumeration warnings through the done report without blocking.

## Outcome

Scan the release gate's tracked regular-file scope by default while preserving the existing blocking behavior.

- Tracked regular blobs outside the existing roots receive report-only scanning under shared exclusions; the old roots keep their current blocking and untracked-file behavior.
- Symlinks and gitlinks stay outside the scannable file set.
- Explicit `--files` and `--changed-from` behavior remains unchanged.

Gate delta: old roots keep their existing blocking behavior; tracked paths outside them are report-only, and Git enumeration failure warns while the old scan still runs. Release `--files` stays blocking. Incident: `docs/maintenance/development_lessons.md` #237; expected catches are matching tracked paths on each default scan, and the measured base had zero hits under `docs/` and `scripts/`. False positives cost operator review; review the expanded scan and false positives 90 days after landing (target 2027-01-24). No new blocker or gate machinery is added; exclusions remain unchanged.

## Assumptions

- assume the explicit `--files` mode and shared exclusions remain the release scan's scope contract; basis: `release-rewrite.sh` enumerates regular tree blobs and passes them to `scan-public-hygiene.sh --files`, while the shared exclusion source supplies the exclusions.
- assume only the default mode widens to repository-wide tracked regular blobs; `--changed-from` retains its current scope and behavior; basis: the validated requirements buffer excludes changing `--changed-from`, while the origin offers default-root widening as a parity arm.
- assume the current zero-hit base measurement is a baseline and does not make the historical release leak moot; basis: lesson 237 records six leaked receipts and the current tree has since been masked.
- Decision receipt: keep the two existing roots as blocking scans, then scan tracked regular blobs outside them in report-only mode; this avoids an unapproved blocker increase while meeting the origin's “reported” outcome. Preserve untracked files under the old roots. The home-path-only alternative misses other deny patterns; a separate publish mode duplicates caller policy; excluding `docs/history/` hides the receipts; a scheduled scan adds machinery. A bypass is unnecessary for report-only paths; removing false positives is inapplicable to the zero-hit base; retaining only two roots leaves the leak unreported. Later confirmed examples use shared exclusions. Review 90 days after landing (target 2027-01-24); source: backlog origin and `docs/maintenance/development_lessons.md` #237; 2026-10-26; Tasks 1-2.

Decision points requiring a grill: none remain.

## Standing constraints

- Do not change deny patterns or exclusions to make the scan pass.
- Keep matched content masked, not excluded, under the current scanner policy.
- Do not add a scan mode, scheduled carrier, gate, lock, ledger, or closeout ceremony.
- Preserve `--files` and `--changed-from` behavior.

## Evaluation Criteria

**Quality dimensions:**
- coverage: default scan checks release `--files` tracked blobs under unchanged exclusions, while preserving untracked files in the old roots.
- compatibility: explicit file-list and changed-from invocations retain their existing semantics.

**Done when:** scanner selftests prove tracked scope, old-root blocking/untracked behavior, report-only output, exclusions and path safety; done-sweep results surface warnings without blocking; `AGENTS.md` matches; scoped checks pass.

**Ship when:** none; evidence owner: repository author; closure condition: both tasks' scanner and done-sweep checks plus scoped repository checks pass.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/scan-public-hygiene.sh` (Task 1)
- `scripts/done_sweep_gates_lib.py` (Task 1)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (Task 2)

**Documentation:**
- `AGENTS.md` (Task 1)

**Review-only:**
- `scripts/release-rewrite.sh` (review-only) - reference for regular-blob selection

**Plan-related extension:** implementation and review may change files not listed above when they complete this plan's behavior or close implied wiring/documentation; weak or speculative links are out of scope.

**Out of scope; reject unless plan-related:**
- `scripts/test_release_skill_selftest.py`; release refusal diagnostics are owned by the separate diagnostics plan.
- `agents/skills/release/SKILL.md`; this plan does not change release behavior.
- `scripts/done_run.sh`; its explicit changed-file scan is separate from the done sweep default scan.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_sweep_gates_lib.py -q
bash scripts/scan-public-hygiene.sh --selftest
bash scripts/check_maintenance_pins.sh
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/scan-public-hygiene.sh scripts/done_sweep_gates_lib.py scripts/test_done_sweep_gates_lib.py AGENTS.md
bash scripts/scan-public-hygiene.sh --files scripts/scan-public-hygiene.sh scripts/done_sweep_gates_lib.py scripts/test_done_sweep_gates_lib.py
```

### Task 1: Add non-blocking tracked-scope reporting

Execution estimate: 1.5h

Context surface: the plan's Terms and this task.

Files:
- `scripts/scan-public-hygiene.sh`
- `scripts/done_sweep_gates_lib.py`
- `AGENTS.md`

Primary class anchors:
- `cmd_full_tree` in `scripts/scan-public-hygiene.sh`

Evidence:
- Default mode currently scans `agents/skills` and `projects`, including untracked files there; `--files` supplies explicit regular file paths under shared exclusions.
- Release enumeration supplies tracked regular blobs, while the done sweep invokes the scanner with no arguments.
- At base `863b767c427bca2eb4d818095f0e8a653cf62953`, 1,347 regular blobs had zero hits under `docs/` and `scripts/`.

- [x] Given default invocation, keep both old roots as blocking directory scans including untracked files; separately enumerate tracked regular blobs outside them with NUL delimiters. [class: IMPLEMENTATION_REQUIRED]
- [x] Bind Git enumeration to `PUBLIC_HYGIENE_REPO_ROOT` and clear inherited Git repository overrides; pass enumerated paths after `--` so option-shaped names stay paths. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a tracked regular blob outside old roots that matches a deny pattern, emit `PUBLIC_HYGIENE_REPORT: path=<ASCII-only JSON-quoted path>` representing every filename byte, including undecodable bytes, without raw terminal controls or matched content; emit no path record for a clean file. Enumeration failure emits `PUBLIC_HYGIENE_REPORT: enumeration-unavailable` and skips only this scope while preserving old-root scan results. [class: IMPLEMENTATION_REQUIRED]
- [x] Propagate only `PUBLIC_HYGIENE_REPORT:` records through `GateResult.warnings`; ignore unrelated successful scanner output and preserve existing `FAIL:` handling and scanner result codes. [class: IMPLEMENTATION_REQUIRED]
- [x] Keep symlinks and gitlinks out of the new tracked-file set; preserve existing `--files` and `--changed-from` semantics. [class: IMPLEMENTATION_REQUIRED]
- [x] Update help text and revise the existing `AGENTS.md` scan instruction in place; keep operative text byte-neutral or shorter. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `fix: align hygiene scan with release scope`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Pin scan-scope and caller behavior

Execution estimate: 1.5h

Context surface: Task 1 behavior and the plan's Terms.

Files:
- `scripts/scan-public-hygiene.sh`
- `scripts/done_sweep_gates_lib.py`
- `scripts/test_done_sweep_gates_lib.py`

Primary class anchors:
- `cmd_selftest` in `scripts/scan-public-hygiene.sh`
- `gate_sensitive_data_scan` in `scripts/done_sweep_gates_lib.py`

- [x] Extend scanner selftests: old-root tracked and untracked hits still exit 1; a matching new-root tracked file emits a report record without content and exits 0, while a clean new-root tracked file emits no path record. [class: REPOSITORY_TEST]
- [x] Test newline, option-shaped, control-byte, and undecodable-byte paths; no raw control or matched content in report records; both symlink/gitlink exclusions; shared exclusions; and enumeration warning with old-root scanning. [class: REPOSITORY_TEST]
- [x] Pin `PUBLIC_HYGIENE_REPO_ROOT` and `PUBLIC_HYGIENE_SCAN_SCRIPT`; scrub `GIT_*`, set `GIT_CONFIG_NOSYSTEM=1`, and assert a decoy `GIT_DIR` cannot redirect enumeration. [class: REPOSITORY_TEST]
- [x] Pin the fixture scanner and assert its no-argument call; have it emit one prefixed report row and one ordinary row, assert only the prefixed row reaches warnings, and preserve the legacy `FAIL:` failing result. [class: REPOSITORY_TEST]
- [x] Assert explicit `--files` hits remain blocking and `--changed-from` keeps its prior selection semantics. [class: REPOSITORY_TEST]
- [x] Commit: `test: pin hygiene scan scope behavior`. [class: IMPLEMENTATION_REQUIRED]
