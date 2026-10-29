# Plan: Complete the extracted vendored module sync and residuals
Backlog origin: docs/history/backlog/2026-10-14-vendored-sync-module-twins.md
Driving force: token-usage
Plan review record: the staging series .ai-playbook/reviews/2026-10-29-plan-review-vendored-sync-module-twins-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2.5h total, largest task 1.25h
Authoring claim: docs/tmp/authoring-claims/2026-10-14-vendored-sync-module-twins.md (session 01a1875f-5fcf-74f2-8a58-18f079231711)

## Terms

- **Managed skills registry:** the resolved runtime skill tree whose relative paths mirror `agents/skills/`.
- **Canonical primary checkout:** the registered checkout for the repository's `main` branch, used as the source of truth after plan changes land.
- **Skill spine:** a top-level skill file that remains as a navigation hub after detailed content moves to a separate module.
- **Runtime twin:** a file with the same relative path in the managed registry as a source file in the primary checkout.
- **Moved-content reference:** prose that says a detailed procedure still lives inside the spine after it has moved to a module.
- **Scoped cap seed:** a ratchet invocation that adds cap entries for exactly the two extracted modules.
- **Post-landing sync gate:** the existing runtime sync obligation, completed after this plan's source changes land on `main`.
- **Runtime sync receipt:** a tracked record created with the source changes that carries the pending sync handoff into the landing and records its final parity and hygiene evidence afterward.
- **Patterns file:** the hygiene deny-pattern file resolved from the user facts key `public_hygiene_patterns_file`; record its `$HOME`-relative path and SHA-256 with each scan.

## Why

The monolith extraction landed its source modules but left the runtime sync handoff, two missing module byte caps, and references that still describe moved worktree-first content as spine-internal. Finish the source updates first, then synchronize the landed tree so runtime copies include every change, improving token usage.

## Gist & Examples

TLDR: Seed two advisory module caps and re-aim stale references, then sync the landed tree to complete the token-usage cleanup.
Title: Complete the extracted vendored module sync and residuals

Before: The extraction's source files are present, but the runtime handoff is open, the new modules lack caps, and some references still point to the old spine location.

After: The two modules have advisory caps, moved-content references point to their module homes, and the managed registry matches the final landed source tree.

Edge cases: A same-realpath runtime mapping is a verified no-op after landing. A distinct mapping receives a full-tree sync from current `main` only after every in-scope source edit has landed. An unsuccessful source hygiene scan leaves the source changes uncommitted and the sync gate pending.

## Outcome

The extracted modules have scoped advisory caps, cross-corpus pointers describe their current homes, and the managed runtime tree matches the final landed source.

- The two extracted modules have byte caps without changing the warning-only budget policy.
- Readers find moved procedures at their module homes while spine hub pointers remain navigable.
- Runtime consumers receive all landed skill changes together, or the exact same-tree case is recorded as a no-op.

Gate delta: Makes explicit the origin's one-time post-landing sync and its fail-closed source and destination checks; it adds no persistent gate or sync machinery. The [tracked origin](docs/history/backlog/2026-10-14-vendored-sync-module-twins.md) records runtime twins left behind by the extraction landing. Expected catch frequency is one; a false positive costs a fresh source and destination resolution followed by retry. Current guard-liveness ledger ratio: 29:48. Review by 2026-11-29; remove the source and destination checks if the runtime mapping binds both roots immutably. This plan replaces the original handoff with one plan-specific tracked sync receipt and removes stale procedural pointers. The byte budget remains warning-only.

## Assumptions

- Build and review source changes in the plan worktree. Do not sync runtime files from that worktree. The post-landing gate resolves the current primary checkout from Git worktree registration, pins the `main` commit, and checks that `HEAD` and the local `main` ref match and that the `agents/skills/` subtree has no staged, modified, or untracked entries.
- The cap tool's `--ratchet` seeds every file it scans. A temporary skills tree directly under the repository root, with symlinks to only the two modules, makes its resolved parent-parent the repository root and resolves cap keys back to the intended source paths.
- Re-derive reference sites at execution time. Change only claims that moved detail remains in `execute-plan/SKILL.md`; retain valid spine hubs and unrelated matches.
- Maintenance selected this bounded work under the user's standing authorization to continue authoring plans; the sole unresolved operation is the post-landing sync gate.

Decision points requiring a grill: none remain.
Scope extensions (grilled): omit-extension (maintenance-selected arm).
Sources inspected: not a tracker-linked request.

## Evaluation Criteria

- **Cap scope:** Only the two extracted modules gain cap entries; no existing value changes and warning-only behavior remains.
- **Reference accuracy:** Every changed reference is a verified moved-content claim and points to the module; valid hub navigation and unrelated references remain intact.
- **Runtime parity:** After the plan changes land, every source tree path, entry type, file content, symlink target, and executable bit matches the managed registry; no destination-only entries remain.
- **Hygiene:** Source changes pass the repository public-hygiene scan before commit; every existing changed runtime file passes that scan after sync, and deleted paths remain in the parity receipt.
- **Done when:** Both repository tasks and their validation pass, Task 2 creates the runtime sync receipt in `pending` state with its source hygiene input and result, and normal Plan Lifecycle marks the origin covered and folds its disposition into the archived plan before deleting it. The post-landing Ship condition remains tracked in the receipt.
- **Ship when:** [class: EXTERNAL_RELEASE_GATE] After the source changes land on `main`, resolve the registered primary checkout as `primary`, pin its landed `main` commit, and resolve the intended managed registry root as `destination` from the runtime layout and configured agent link. Fail closed on disagreement or ambiguity. If `realpath "$primary/agents/skills"` equals `realpath "$destination"`, record the verified same-realpath no-op and use the Task 2 hygiene evidence for the identical bytes. Otherwise, before any `rsync --delete`, prove `destination` is exactly the configured registry root and is contained under its expected resolved parent. Capture the pre-sync itemized checksum dry-run with `rsync -ainc --delete --itemize-changes "$primary/agents/skills/" "$destination/"`; this is the full add/update/delete inventory, including entry-type, mode, content, and symlink differences. Apply `rsync -ac --delete` with those same roots, then repeat the itemized checksum dry-run and require empty output; `-a` checks archive attributes and symlinks, `-c` checks file content, and `--delete` exposes destination-only entries. Record the source commit and both dry-run outputs in the receipt. Resolve the patterns file from the user facts key `public_hygiene_patterns_file` and set `PUBLIC_HYGIENE_PATTERNS_FILE="$patterns_file"` for both source and destination scans. Record its `$HOME`-relative path and SHA-256. If its digest changed since Task 2, rerun the source scan over the recorded source path set with the current patterns file and update the receipt before continuing. For a distinct destination, set `PUBLIC_HYGIENE_REPO_ROOT="$destination"` and run `scan-public-hygiene.sh --files` with every existing destination-relative changed file from the pre-sync inventory; retain deleted paths in the inventory but do not pass missing paths. If no existing destination files changed, do not pass an empty `--files` list; record that empty scan input and cite the receipt's source-hygiene result for the matching bytes. Prepare the final receipt candidate with `state: complete` and all source/destination evidence. Scan that exact file with `PUBLIC_HYGIENE_REPO_ROOT="$primary"`, the pinned `PUBLIC_HYGIENE_PATTERNS_FILE`, and `--files docs/history/2026-10-29-vendored-sync-module-twins-runtime-receipt.md`; do not write the receipt scan result into the scanned file. If the scan finds a sensitive or absolute path, return the candidate to `pending`, redact or hash that inventory value while retaining parity evidence, then prepare and scan the corrected final bytes. After a passing scan, hash the exact receipt bytes and commit them without further edits; include trailers `Runtime-Receipt: docs/history/2026-10-29-vendored-sync-module-twins-runtime-receipt.md`, `Runtime-Receipt-SHA256: <digest>`, `Runtime-Receipt-Hygiene: pass`, and `Runtime-Hygiene-Patterns-SHA256: <digest>`. The commit message is the durable receipt-scan result bound to the final file and patterns digests. The receipt always records Task 2's exact source changed-file set and hygiene result, the patterns-file path and digest for source, destination, and receipt scans, the configured destination in `$HOME`-relative form, the resolved target relative to its verified parent, the parent-containment result when syncing, sync outcome, complete parity inventory, destination scan root and input set, and source and destination scan results. Task 2 creates the receipt in `pending` state; prepare it as `complete` only after source and destination hygiene plus parity checks pass, then commit only after the final receipt scan passes. The commit trailers hold the final receipt-scan result without changing the scanned bytes. The receipt remains the tracked handoff after normal Plan Lifecycle covers the original origin, folds its disposition into the archived plan, and deletes it. If a gate fails, leave the receipt `pending` with the failed check; the plan may complete its repository tasks, but do not report the external Ship condition complete.

## Review Scope

**Production:**
- `agents/skills/` (landed source tree and post-landing runtime parity)
- `agents/skills/plans/SKILL.md` (extracted module pointer)
- `agents/skills/execute-plan/SKILL.md` (spine hub and moved-content reference target)
- `agents/skills/plans/validation-authoring-rules.md` (extracted module and cap target)
- `agents/skills/execute-plan/worktree-first.md` (extracted module, cap target, and reference target)
- `agents/skills/maintenance/template-unblock.md` (verified reference site)
- `agents/skills/maintenance/decisions.md` (verified reference site)
- `agents/skills/maintenance/template-execution.md` (verified reference site)
- `scripts/skill_text_budget.py` (existing ratchet and relative-key behavior)
- `scripts/skill_text_budget_caps.json` (two cap entries)
- `scripts/reconcile_post_landing.py` (verified reference site)
- `scripts/reverse_squash_guard.py` (verified reference site)
- `docs/maintenance/development_lessons.md` (verified reference site)
- `projects/.ai-playbook/development_lessons.md` (verified reference site)

**Tests and checks:**
- `scripts/check_maintenance_pins.sh` (preserve source placement pins)
- `scripts/gate_liveness_ledger.json` (register used by maintenance pins)
- `scripts/scan-public-hygiene.sh` (scan exact source and destination changed-file sets)
- Public-hygiene scan over every existing source path in the untracked-inclusive changed set before commit and every existing runtime path in the sync receipt after landing

**Records:**
- `docs/history/backlog/2026-10-14-vendored-sync-module-twins.md` (origin; normal Plan Lifecycle covers it at landing, then folds its disposition and deletes it during completion)
- `docs/history/2026-10-29-vendored-sync-module-twins-runtime-receipt.md` (new tracked handoff; created pending before source landing and updated with post-landing sync evidence)

**Exclusions:**
- Unrelated byte-cap gaps or warning-policy changes
- General rewrites of references that mention a spine without claiming moved content remains inline
- New sync scripts, persistent gates, registries, or recurring machinery

## Validation Commands

```bash
python3 scripts/skill_text_budget.py --check &&
tmp="$(mktemp -d)" && pin_date="$(date +%F)" && { PINS_RECORDED_RED_REGISTER="$PWD/scripts/gate_liveness_ledger.json" PINS_RECORDED_RED_AS_OF="$pin_date" PINS_DUPLICATE_ROOT="$PWD" TMPDIR="$tmp" bash scripts/check_maintenance_pins.sh; result=$?; rmdir "$tmp" || exit; printf 'PINS_RECORDED_RED_AS_OF: %s\nremoved TMPDIR: %s\n' "$pin_date" "$tmp"; exit "$result"; }
```

### Task 1: Add advisory caps for only the two extracted modules

Context surface: `scripts/skill_text_budget.py`, the cap file, and the two module paths.

Files:
- `scripts/skill_text_budget.py`
- `scripts/skill_text_budget_caps.json`
- `agents/skills/plans/validation-authoring-rules.md`
- `agents/skills/execute-plan/worktree-first.md`

Primary class anchors: `main` in `scripts/skill_text_budget.py` (CLI behavior) and `skill_files` (file selection), if those anchors remain present at execution time.

- [ ] Confirm current ratchet file-selection and symlink-path semantics from source before constructing the scoped input tree. [class: IMPLEMENTATION_REQUIRED]
- [ ] Create a temporary directory directly under the repository root with a `skills` subdirectory and symlinks to only the two modules; verify the resolved skills directory's parent-parent is the repository root. [class: REPOSITORY_TEST]
- [ ] Run the ratchet against that scoped tree, verify exactly the two intended repository-relative keys, then remove the exact temporary directory and confirm it is absent. [class: REPOSITORY_TEST]
- [ ] Verify the cap JSON diff adds exactly those two keys and changes no existing value. [class: REPOSITORY_TEST]
- [ ] Confirm `--check` remains advisory and adds no blocker. [class: REPOSITORY_TEST]
- [ ] Commit: `docs: add caps for extracted skill modules` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Re-aim verified references and prepare the post-landing receipt

Context surface: Cross-corpus claims that moved worktree-first detail remains in the spine, valid module hub pointers, and the tracked origin row.

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/maintenance/template-unblock.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/template-execution.md`
- `scripts/reconcile_post_landing.py`
- `scripts/reverse_squash_guard.py`
- `scripts/scan-public-hygiene.sh`
- `scripts/gate_liveness_ledger.json`
- `docs/maintenance/development_lessons.md`
- `projects/.ai-playbook/development_lessons.md`
- `docs/history/backlog/2026-10-14-vendored-sync-module-twins.md`
- `docs/history/2026-10-29-vendored-sync-module-twins-runtime-receipt.md` *(new)*

Primary class anchors: none, this task edits references and a tracked backlog receipt.

- [ ] Re-scan the corpus for the origin's named sites and new matches; verify each candidate's actual claim before editing. [class: REPOSITORY_TEST]
- [ ] Re-aim only stale moved-content claims to `agents/skills/execute-plan/worktree-first.md`; preserve valid hub pointers and unrelated references. [class: IMPLEMENTATION_REQUIRED]
- [ ] Update the origin row with the post-landing trigger, leaving status changes and origin deletion to normal Plan Lifecycle. Create `docs/history/2026-10-29-vendored-sync-module-twins-runtime-receipt.md` in `pending` state as the tracked post-landing handoff; include only the path-safe fields named in Ship when. [class: IMPLEMENTATION_REQUIRED]
- [ ] Resolve `public_hygiene_patterns_file` from user facts; record its `$HOME`-relative path and SHA-256. Re-derive the untracked-inclusive `git status --short` path set, inspect every entry, and record it in the pending receipt. [class: REPOSITORY_TEST]
- [ ] Scan every existing repo-relative changed path with `scripts/scan-public-hygiene.sh --files`, setting `PUBLIC_HYGIENE_REPO_ROOT="$PWD"` and `PUBLIC_HYGIENE_PATTERNS_FILE="$patterns_file"`; record the path set and patterns digest in the receipt. Keep deletions in the receipt without passing missing paths. [class: REPOSITORY_TEST]
- [ ] After the scan passes, record `source hygiene: pass` in the receipt, re-derive the final changed set, and rerun the scan over every existing path including the updated receipt. Require exit 0 and make no further source or receipt edits before commit. If either scan fails, correct the source or receipt, rerun, then record the result and repeat the final check. [class: REPOSITORY_TEST]
- [ ] Run maintenance pins with `PINS_RECORDED_RED_REGISTER` set to `scripts/gate_liveness_ledger.json`, `PINS_RECORDED_RED_AS_OF` set to the captured execution date, and `PINS_DUPLICATE_ROOT` set to the repository root; capture the command output, record the exact date and exit result, and verify it reports the captured `TMPDIR` removed. [class: REPOSITORY_TEST]
- [ ] Commit the reference changes and pending sync receipt as `docs: re-aim extracted module references`. [class: IMPLEMENTATION_REQUIRED]
