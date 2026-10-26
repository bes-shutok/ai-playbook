# Backlog: release privacy gate failure line names every scanned path instead of the hits

- **Filed:** 2026-10-26, learn Step 1.8 over the 2026-10-26 release run (first rewrite attempt aborted at the privacy gate)
- **Status:** covered (docs/history/plans/2026-10-26-release-privacy-gate-diagnostics-and-replay.md)
- **Workflow:** backlog
- **Priority:** medium
- **Cluster:** docs/history/backlog/2026-10-26-commit-scan-scope-release-gate-scope-parity.md (same surface: the release privacy gate and the hygiene scanner it wraps)
- **Origin class:** self-serving
- **Class:** fix-class (the gate's failure sentinel substitutes its input list for the scanner's findings; default shape: carry the finding locators through)
- **Driving force:** operator time (primary), reliability (secondary)
- **Skill/step:** `agents/skills/release/SKILL.md` Step 2 (the rewrite step's privacy gate) as carried by `scripts/release-rewrite.sh` `invoke_scanner`
- **Source reference:** the 2026-10-26 release run's first `release-rewrite.sh` invocation: `PRIVACY GATE FAILED (scanner exit 1): offending paths: ...` followed by all 1342 scanned paths; the two real hits (one tracked ledger, one archived plan) were found only by re-materializing the tip tree and re-running the scanner by hand with stdout kept
- **Why not fixed now:** `scripts/release-rewrite.sh` is the release's gated rewrite (privacy gate plus compare-and-swap), a guard-bearing path the ad-hoc arm excludes; the fix needs a reviewed change with the reporting shape decided
- **Dedup probe:** searched open backlog filenames and Problem text for `release`, `privacy gate`, `offending paths`, `release-rewrite`; no open row owns the gate's failure report (the 2026-10-18 release-archive-privacy-cleanup row is closed and concerned archive content, not the report)

## Problem

`invoke_scanner` in `scripts/release-rewrite.sh` runs the hygiene scanner in explicit-paths mode with stdout discarded (its FAIL blocks echo file content) and stderr captured to a file inside the trap-owned run directory. On a non-zero scanner exit it prints `PRIVACY GATE FAILED (scanner exit N): offending paths: ${scan_call_paths[*]}`, that is, the whole input list, not the scanner's findings. The run directory is removed by the exit trap, so the captured stderr is gone too. The operator is left with a 88 KB line naming every file in the tree and no locator for the actual hit.

## Evidence

- `scripts/release-rewrite.sh`, function `invoke_scanner`: stdout redirected to `/dev/null`, stderr to `$run_tmp/scanner-stderr.txt`, only `skipped excluded path` lines re-emitted, and the sentinel built from `${scan_call_paths[*]}`.
- The 2026-10-26 release run: the first rewrite attempt exited 1 at the gate; the sentinel line was 88788 bytes long; the real findings were `docs/history/certification-seal-landing-diagnostics.md` lines 14-20 and one line of `docs/history/plans/completed/2026-10-18-review-runtime-sibling-module-deployment.md`, recovered by re-running `scan-public-hygiene.sh --files` over a `git archive` of the tip with stdout kept.
- The scanner's stdout FAIL block is already locator-shaped: a `FAIL: files` header then `path:line:content` lines, so the path and line are extractable without echoing content.
- The release skill text documents exit 1 as "a privacy hit (the `PRIVACY GATE FAILED` sentinel naming the offending paths)", which promises what the script does not deliver.

## Expected

The failure message names the files and lines the scanner flagged, never the whole input list, and omits matched content. When an operator requests diagnosis, a replay command reproduces the exact failed scan and writes its raw output to a mode-0600 file. Raw scanner output is not retained automatically after a refusal.

## Suggested direction

Show bounded, escaped `path:line` locators on refusal. Preserve the failed scan's inputs so an operator can explicitly request a replay; write raw output only to a mode-0600 file on that request. Reconcile the release skill's exit-code sentence with the delivered shape.

## Alternatives

- **Keep the sentinel, document that the operator must reproduce the scan by hand:** rejected; the reproduction took five commands and a materialized tree in the witnessed run, and the skill text already claims the sentinel names the offending paths (`agents/skills/release/SKILL.md`, Step 2 notes).
- **Print the scanner's stdout verbatim on failure:** rejected because the FAIL block echoes the matched content, which is the private data the gate exists to keep out of transcripts and logs (`scripts/release-rewrite.sh`, the `invoke_scanner` comment).
- **Persist raw scanner output automatically:** rejected because matched content would remain on disk without an explicit operator request or a bounded retention owner; the r4 review also showed that the full FAIL stream can be unbounded.
- **Have the scanner itself emit a locator-only summary line:** viable as a sibling arm; the scanner's stdout contract is owned by `scripts/OUTCOME_CONTRACT.md`, so the plan decides whether the extraction lives in the scanner or in the gate wrapper.

## Machinery assessment

No new gate, lock, or ledger. The change makes the existing failure report actionable and adds an operator-invoked replay; the gate's verdict and exit classes are unchanged, and raw scanner output is not retained automatically.
