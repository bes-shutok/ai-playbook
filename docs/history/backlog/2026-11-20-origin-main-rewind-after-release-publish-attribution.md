# Backlog: the 2026-11-08 release pushed the full local main and origin was rewound on operator order

- **Filed:** 2026-11-20, operator-directed push-attribution ask and origin rewind order
- **Status:** closed - executed on operator direction 2026-11-20 (tip untrack `4c604ecad`; dated acceptance below); the PLAN-PROMPTS entry retains only the checker-review agenda arm
- **Priority:** high
- **Origin class:** witnessed full-main publish and operator-directed origin rewind
- **Class:** record / decision
- **Dedup probe:** searched open backlog filenames and bodies for publish-scope, force-push, leak, and origin rewind; every hit carries Status: covered (the 2026-11-08 publish-scope pair, the same-day regrowth sibling, the 2026-10-18 privacy row), so this row is single-origin.

## Problem

The operator asked which session pushed all local main commits to origin and ordered the origin reset back. Attribution chain, each leg re-derived on disk 2026-11-20:

- The origin/main remote-tracking reflog (`.git/logs/refs/remotes/origin/main`) records exactly four update-by-push entries; the last two are 2026-11-08 15:07:33 UTC (to `c5a3f3e7`) and 2026-11-08 15:27:51 UTC (to `8fe42f5d6`, a forced update during the charter repair).
- The local main reflog places main at `c5a3f3e7` at 15:07:03 and at `8fe42f5d6` at 15:26:51, so each push published the entire local main tip of its moment.
- The ZCode session store shows one active session across the whole window: `sess_4be8a30b-3575-4675-aef4-99d5d5de9692`, "Release Skill Invocation" (created 13:58:55, last activity 15:55:34); the same session's durable record filed the same-day publish-scope rows (`eec3bebb4`).
- Backup refs `refs/release-backup/pre-release-2026-11-08` and `-2` plus `refs/recovery/pre-charter-repair-main-2026-11-08` corroborate the release-then-repair sequence; no automation run fired that day; the interactive shell history holds no main push.

Verdict: not a rogue session - the release run made the first push, and the second push was the operator-directed charter-repair force-push already documented by the covered 2026-11-08 rows.

The rewind executed the same turn as this row, on operator order: origin/main forced `8fe42f5d6` back to `284f89a7` (the 2026-11-01 release tip, the last pre-anomaly published state), verified by a fresh ls-remote; the rewound-away tip is preserved at `refs/release-backup/pre-origin-reset-2026-11-20`.

## Residual (the open decision)

- The carrier commits `0fd467947` and `8da90594b` (the two `.ai-playbook/reviews/` records) remain ancestors of main; the publish delta is now 666 commits; the next release republishes them.
- The landed publish-scope checker reads the net delta file list and tip tracked-ignored state; both records are untracked at the tip and net-absent from the name-only delta, so the checker cannot see the carriers and the republish passes every current gate.
- Release-time resolution path (re-derived 2026-11-20 from `scripts/release-rewrite.sh`): the release's gated rewrite squashes the delta with a byte-identical final-tree gate, and dirt added-and-cleaned inside the pile never reaches the final result (operator directive 2026-09-27); but each squashed group's tree equals its source tip's tree, so a group boundary landing inside the 2026-11-02 to 11-08 span would still carry the blobs in one intermediate pushed commit. Authoring the Step 1 grouping so one group spans the add-to-untrack span drops them entirely - no separate ancestry rewrite is needed; only the tip untrack of the 18 currently tracked-ignored `.ai-playbook/` files stays required before the release.
- Operator disposition, dated 2026-11-20: acceptance - the two ancestry carriers republish at the next release (contents scanned clean of deny patterns per `a9c0c680e`); the grouping condition above is the standing release-time instruction; the tip untrack of the 18 tracked-ignored files (2 review-certs + 16 reviews, dated 2026-11-09 to 11-19) executed as `4c604ecad` the same day with disk copies kept under the wholesale ignore.

## Expected

The operator-chosen disposition lands before the next release: the ancestry rewrite executed with backup and recovery refs, or a dated acceptance note; no new gate.

## Suggested investigation and direction

Route the decision through a plans session pricing both dispositions with evidence (the `a9c0c680e` content-clean scan and the 2026-10-18 out-of-scope-by-design precedent); fold the delta-commits scope question into the publish-scope checker's 2026-12-08 review as an agenda line.
