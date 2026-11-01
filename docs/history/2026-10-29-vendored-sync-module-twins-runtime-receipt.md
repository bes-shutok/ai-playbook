# Runtime sync receipt: vendored-sync module twins

state: complete
Plan: docs/history/plans/completed/2026-10-29-vendored-sync-module-twins.md (archived by this plan's completion pass)
Origin row: docs/history/backlog/2026-10-14-vendored-sync-module-twins.md (covered; deleted by the completion pass — durable home is the archived plan)
Created: 2026-11-01 by the plan's Task 2 in the execution worktree (branch `2026-11-01-vendored-sync-module-twins`, base HEAD `be559d30ae3219f8ff567ad147ffe79fac4a33d9`)

## Purpose

Tracked post-landing handoff (plan Ship when, class EXTERNAL_RELEASE_GATE). After the source changes land on `main`: resolve the registered primary checkout as `primary` and the managed registry root as `destination` from the runtime layout and configured agent link, failing closed on disagreement or ambiguity; if `realpath "$primary/agents/skills"` equals `realpath "$destination"`, record the verified same-realpath no-op and reuse this receipt's source hygiene evidence for the identical bytes; otherwise prove, before any `rsync --delete`, that `destination` is exactly the configured registry root and is contained under its expected resolved parent, record the resolved target relative to its verified parent and the parent-containment result below, then capture the pre-sync itemized checksum dry-run inventory (`rsync -ainc --delete --itemize-changes`), apply `rsync -ac --delete`, and require the repeat dry-run empty. Every post-landing field below stays a placeholder until then; if a gate fails, this receipt stays `pending` naming the failed check and the external Ship condition is not complete.

## Patterns file (source, destination, and receipt scans)

- Path (`$HOME`-relative): `~/.ai-playbook/public-hygiene.patterns`
- SHA-256: `77b1482ed4fd3d287d1aaaed099cfd13a9bea5665103569ec1a0293ce9288c14`
- Resolved from the user facts key `public_hygiene_patterns_file`. If this digest changes after Task 2, the landing reruns the source scan over the recorded source path set with the current patterns file and updates this receipt before continuing.

## Configured destination (`$HOME`-relative)

- `~/.agents/skills` (the shared skills registry; the runtime agent surfaces reach it through their symlinks per `projects/.ai-playbook/agent-runtime-layout.md`).

## Task 2 source changed-file set

The exact path set the Task 2 boundary commit `ae87ada92` landed (10 paths; statuses as committed). At capture time (2026-11-01, untracked-inclusive `git status --short` in the execution worktree after all Task 2 source edits) the set was the first 8 rows below, with this receipt its only untracked (`??`) entry; the boundary commit added the last two rows — the plan's Task 2 checkbox flips and the r1 residual-sites backlog row.

| Status | Path |
|---|---|
| M | agents/skills/maintenance/decisions.md |
| M | agents/skills/maintenance/template-execution.md |
| M | agents/skills/maintenance/template-unblock.md |
| M | docs/history/backlog/2026-10-14-vendored-sync-module-twins.md |
| M | docs/maintenance/development_lessons.md |
| M | scripts/reconcile_post_landing.py |
| M | scripts/reverse_squash_guard.py |
| A | docs/history/2026-10-29-vendored-sync-module-twins-runtime-receipt.md |
| A | docs/history/backlog/2026-11-01-worktree-first-reaim-residual-sites.md |
| M | docs/history/plans/2026-10-29-vendored-sync-module-twins.md |

Deletions: none. Every entry was individually inspected; all are Task 2 reference re-aims, the origin-row handoff update, the plan's Task 2 checkbox flips, the r1 residual-sites backlog row, and this receipt.

## Source hygiene (Task 2)

- Input: every existing repo-relative path in the pre-boundary set above (8 paths at scan time — the 7 modified files plus this receipt, before the boundary commit added the plan's checkbox flips and the r1 residual-sites backlog row), scanned with `PUBLIC_HYGIENE_REPO_ROOT="$PWD"` and `PUBLIC_HYGIENE_PATTERNS_FILE` pointing at the patterns file above via `bash scripts/scan-public-hygiene.sh --files ...`.
- Result: `source hygiene: pass` (exit 0, final row `OUTCOME: pass`, 2026-11-01). The final receipt-inclusive rerun over the same 8 pre-boundary paths after this recording also exits 0 before the boundary commit; no source or receipt edits followed it before `ae87ada92`. The two boundary-added paths (plan checkbox flips, residual-sites backlog row) were hygiene-scanned separately, exit 0.

## Post-landing evidence (placeholders; filled only after landing on `main`)

- Landed source commit on `main`: 55aff4c1f73487faa93231714334a7d10a36c348 (squash landing 2026-11-01, branch 2026-11-01-vendored-sync-module-twins, 12 files, base c5c31e9d6f35dd444eb627a2ad2ea594a1de6dd0).
- Same-realpath check (`realpath "$primary/agents/skills"` vs `realpath "$destination"`): verified equal (both resolve to the primary checkout's `agents/skills`; `~/.agents/skills` is the configured agent link onto it). Verified same-realpath no-op per the Ship-when no-op branch; Task 2's source hygiene evidence above covers the identical bytes.
- Resolved target relative to its verified parent: N/A — no-op branch taken, no `rsync` ran.
- Parent-containment result (destination exactly the configured registry root, contained under its expected resolved parent; proven before any `rsync --delete`): N/A — same-realpath no-op; containment proof obligation applies only to the distinct-destination branch.
- Pre-sync itemized checksum dry-run inventory (add/update/delete, entry type, mode, content, symlink differences): N/A — same-realpath no-op; the runtime tree is the landed source tree, parity is structural.
- Sync apply (`rsync -ac --delete` over the same verified roots): N/A — same-realpath no-op; the runtime tree is the landed source tree, parity is structural.
- Post-sync itemized checksum dry-run (required empty): N/A — same-realpath no-op; the runtime tree is the landed source tree, parity is structural.
- Destination hygiene scan (`PUBLIC_HYGIENE_REPO_ROOT="$destination"`, every existing destination-relative changed file from the pre-sync inventory; deleted paths retained in the inventory but never passed as missing; an empty existing set is recorded as such and cites this receipt's source-hygiene result for the matching bytes): N/A — same-realpath no-op; the runtime tree is the landed source tree, parity is structural.
- Patterns-file digest recheck at landing time (source rerun required on change): re-derived at landing 2026-11-01, unchanged (`77b1482ed4fd3d287d1aaaed099cfd13a9bea5665103569ec1a0293ce9288c14`); no source rerun required.
- Final receipt scan (`--files` over this file with `PUBLIC_HYGIENE_REPO_ROOT="$primary"`, then `state: complete`) and the commit trailers (`Runtime-Receipt`, `Runtime-Receipt-SHA256`, `Runtime-Receipt-Hygiene: pass`, `Runtime-Hygiene-Patterns-SHA256`): recorded by the landing session 2026-11-01 — the exact bytes of this completed receipt were scanned (pass) and their SHA-256 bound in the landing commit's trailers, with no further edits after the scan.
