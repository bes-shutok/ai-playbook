# Plan: Release privacy gate diagnostics and replay

Backlog origin: `docs/history/backlog/2026-10-26-release-privacy-gate-failure-report-unactionable.md`
Driving force: efficiency + code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-26-plan-review-release-privacy-gate-diagnostics-and-replay-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1.5h
Authoring claim: docs/tmp/authoring-claims/release-privacy-gate-report-and-scan-scope-parity.md (session `01a1638f-189d-7b02-9cf8-0990eb6f3dfd`)

## Terms

- **FAIL block:** the scanner's `FAIL: files` heading followed by `path:line:content` rows.
- **Locator:** a parsed `path:line` prefix from a FAIL row, with control bytes escaped and matched content removed.
- **Locator helper:** a streaming process that keeps at most 65,536 bytes of scanner stdout while parsing locators.
- **Trap-owned directory:** a temporary directory the release rewrite's exit trap removes.
- **Release draft:** the user-authored temporary input whose `release-groups:` block supplies proposed commit messages and grouping.
- **Diagnostic replay:** an operator-invoked helper that reproduces the failed scan and writes raw output to a mode-0600 file only when requested.
- **Source tip:** the commit at the start of the failed release rewrite.
- **Tracked regular blob:** a Git tree entry with mode `100644` or `100755`; symlinks and gitlinks have no scannable file content.

## Why

A release privacy refusal currently discards scanner findings and prints the full input path list, so the operator cannot locate the refusal without reconstructing the scan.

## Gist & Examples

TLDR: Improve efficiency by showing safe hit locators and offering exact scan replay on request.

**Before (today):** When the scanner flags `docs/example.md` at line 12, the refusal lists every scanned path, hides the hit, and removes the inputs needed to reproduce it.
**After (this plan):** For that same hit, the failure message lists `docs/example.md:12`; an operator can request an exact replay whose raw output is saved only to a mode-0600 file.
Edge cases: Reject malformed or ambiguous rows, bound retained scanner output, refuse replay after input drift, and preserve scanner exit classes.

## Outcome

Make release privacy refusals actionable while keeping detailed scanner output available only on explicit request.

- The bounded failure message names only safe locators derived from scanner FAIL rows.
- An operator can replay the exact failed scan without leaving raw output behind automatically.
- Release authorization, scanner exit behavior, and successful rewrite behavior remain stable.

Gate delta: no new blocking gate, validator, lock, fence, state field, or review duty; this adds an optional operator-facing replay command with checks for the original source, patterns, and release groups. The witnessed 2026-10-26 refusal required five manual commands and a materialized tree to diagnose; locators and exact replay remove that diagnosis cost without automatic raw-output retention.

## Assumptions

- assume the scanner's existing `FAIL: files` block remains the only source for safe locators, parsed against the exact input-path set; basis: `scripts/scan-public-hygiene.sh` emits `path:line:content` rows and both paths and content can contain colons.
- assume matched content must stay out of terminal and release-summary output; basis: the FAIL rows include the exact content the gate protects.
- assume exact raw scanner output should be available only after an explicit operator request; basis: automatic output retention stores matched content without an owner or retention boundary.
- Decision receipt: revise this origin's raw-output acceptance from automatic survival to opt-in replay. Keep locator and replay work in one plan because both edit the same release rewrite, selftest, and release skill, and the duplicate-origin coverage gate allows one active plan to own this row; source: review-reconciliation after rounds r1-r5; 2026-10-26; Tasks 1-2.

Decision points requiring a grill: none remain.

## Standing constraints

- Preserve release authorization, compare-and-swap update, remote-write behavior, and publish behavior.
- Do not change deny patterns, exclusions, or scanner success behavior.
- Never print scanner-matched content to the terminal or release summary.

## Evaluation Criteria

**Quality dimensions:**
- correctness: failure-message locators correspond only to FAIL rows; replay inputs match the failed scan or refuse before scanning.
- privacy: matched content is absent from terminal output; raw output is retained only on request and scanner stdout parsing stays within a fixed 65,536-byte bound.
- usability: one checked replay command reproduces the exact release scan without materializing the rewritten tree.

**Done when:** release tests cover locator boundaries, bounded output, terminal safety, scanner exits, replay input drift, draft lifecycle, output permissions, and no content leakage; the release skill documents locators, replay, and draft lifecycle; scoped checks pass.

**Ship when:** none; evidence owner: repository author; closure condition: the release selftest and scoped repository checks pass for both tasks.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/release-rewrite.sh` (Task 1)
- `scripts/release-privacy-locators.py` (Task 1) *(new)*
- `scripts/release-diagnostic-replay.sh` (Task 2) *(new)*

**Tests:**
- `scripts/test_release_skill_selftest.py` (Task 1)

**Documentation:**
- `agents/skills/release/SKILL.md` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above when they complete this plan's behavior or close implied wiring/documentation; weak or speculative links are out of scope.

**Out of scope; reject unless plan-related:**
- `scripts/scan-public-hygiene.sh`; Task 1 consumes its existing FAIL-row format and does not change scanner behavior.
- `AGENTS.md`; scanner default-scope policy belongs to the separate scope-parity plan.
- `scripts/release-authoring.sh`; this plan changes rewrite-time failure reporting only.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_release_skill_selftest.py'
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file scripts/release-rewrite.sh scripts/release-privacy-locators.py scripts/release-diagnostic-replay.sh scripts/test_release_skill_selftest.py agents/skills/release/SKILL.md
bash scripts/scan-public-hygiene.sh --files scripts/release-rewrite.sh scripts/release-privacy-locators.py scripts/release-diagnostic-replay.sh scripts/test_release_skill_selftest.py agents/skills/release/SKILL.md
```

### Task 1: Emit bounded safe release privacy locators

Execution estimate: 1.0h

Context surface: the plan's Terms and this task.

Files:
- `scripts/release-rewrite.sh`
- `scripts/release-privacy-locators.py` *(new)*
- `scripts/test_release_skill_selftest.py`
- `agents/skills/release/SKILL.md`

Primary class anchors:
- `invoke_scanner` in `scripts/release-rewrite.sh`

Evidence:
- `invoke_scanner` currently redirects scanner stdout to `/dev/null`, captures stderr inside the trap-owned run directory, and prints all input paths on any non-zero result.
- The scanner emits FAIL rows as `path:line:content`; matched content must not enter the release transcript.
- The release selftest already drives rewrite behavior with scanner fixtures and verifies exit mapping.

- [ ] Given scanner output of exactly 65,536 bytes, expect the helper to parse and emit valid deduplicated locators. Accept `path:line:content` rows only when the prefix identifies one exact requested path; accept ripgrep's `line:content` form only when exactly one input path was scanned, assigning that sole path. Reject pathless rows in multi-path scans, malformed rows, unrequested paths, and ambiguous prefixes without a locator. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given scanner output of 65,537 bytes or more, expect the helper to drain and discard excess bytes, emit no locators, and report the bounded-output fallback without changing the scanner exit class. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the scanner through the locator helper without writing full stdout to disk; retain at most 64 KiB for parsing. Preserve hit exit 1, map scanner exits 2 or 3 to rewrite exit 3, and emit no failure message on success. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the release selftest for multiple hits, malformed and absent rows, no-hit behavior, deduplication, overlapping colon paths, `:digits:` content, a single-file `line:content` hit, an unrequested path, and output at exactly 65,536 and 65,537 bytes; assert ambiguous rows yield no locator and no matched content is printed. [class: REPOSITORY_TEST]
- [ ] Test a hit path with a terminal control byte and a fixture scanner exit of 3; expect an escaped locator with no raw control byte and rewrite exit 3. [class: REPOSITORY_TEST]
- [ ] Pin the release remote and helper-script environment settings in the selftest; assert the fixture scanner is invoked under those settings. [class: REPOSITORY_TEST]
- [ ] Update `agents/skills/release/SKILL.md` Step 2 to describe the locator-only failure message and the exit-3 mapping for scanner exits 2 and 3. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `fix: make release privacy failures actionable`. [class: IMPLEMENTATION_REQUIRED]

### Task 2: Reproduce the exact release scan on request

Execution estimate: 1.5h

Context surface: the Release draft, Diagnostic replay, and this task.

Files:
- `scripts/release-rewrite.sh`
- `scripts/release-diagnostic-replay.sh` *(new)*
- `scripts/test_release_skill_selftest.py`
- `agents/skills/release/SKILL.md`

Primary class anchors:
- `invoke_scanner` in `scripts/release-rewrite.sh`

Evidence:
- The rewrite scans tracked regular blobs from its verified source tree plus generated group messages, using scanner and effective-pattern copies.
- The EXIT trap removes the scanner, pattern, groups, and run-directory copies; the release skill currently removes the draft before invoking the rewrite.
- The rewrite verifies the rewritten tree equals the source tip, allowing replay against a clean tracked checkout without materializing the tree.

- [ ] Copy the effective default or override pattern file into the trap-owned run directory and run the original scan against that immutable copy; preserve the existing missing-pattern refusal and exit mapping. [class: IMPLEMENTATION_REQUIRED]
- [ ] Pass the Release draft path to the rewrite; retain it and list it in the report-only inventory after failure, remove it only after successful rewrite, and delete only a regular `release-draft.*` file directly under the canonicalized temp root. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a privacy hit, expect no persistent raw-output file; the failure message names the source tip, retained draft path, scanner source and digest, effective-pattern source and digest, exact serialized release-group digest, and a shell-safe one-command replay invocation. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given a replay request, expect the helper to verify `HEAD` equals the recorded source tip, the tracked worktree is clean, scanner and effective-pattern source match recorded digests, and reconstructed group input from the retained draft matches the recorded digest; any mismatch refuses before scanning. [class: IMPLEMENTATION_REQUIRED]
- [ ] Given valid replay inputs, expect a scan of tracked regular blobs plus reconstructed release-group messages; save raw stdout to a mode-0600 file and print only its path and scanner outcome. [class: IMPLEMENTATION_REQUIRED]
- [ ] Extend the release selftest to cover default and override pattern copies, draft retention and removal, preservation of outside-root and nonmatching files during cleanup, no automatic raw file, exact-tip and clean-tree refusals, scanner/pattern/group digest-mismatch refusals before scanning, group reconstruction, output permissions, and no content leakage. [class: REPOSITORY_TEST]
- [ ] Update `agents/skills/release/SKILL.md` Step 2 to pass `RELEASE_DRAFT_PATH`, retain the draft on failure and remove it after success, describe replay output, add draft paths to the report-only inventory, and preserve the scanner exit mapping. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `fix: add opt-in release privacy diagnostics`. [class: IMPLEMENTATION_REQUIRED]
