# Execute-plan never names the exec-r pointer record the plans-egress gate demands

- **Filed:** 2026-10-21, execute-plan run of plan-validation-command-undefined-repo (landed 28127e322)
- **Status:** open
- **Workflow:** backlog
- **Priority:** moderate (every executed plan's landing carries the egress leg; the duty is discoverable only from a gate refusal or a sibling record)
- **Cluster:** docs/history/backlog/2026-10-21-execute-plan-phase2-staleness-remedy-pointer.md (same surface and defect class: execute-plan skill text omits a duty its landing gates enforce)
- **Origin class:** self-serving
- **Class:** fix-class (the landing gate demands a `-plan-review-<slug>-exec-r<N>` record carrying the egress bytes' sha256, but no skill text tells the orchestrator to produce it at Phase 4; default shape add the sanctioned exit's producer step beside the existing consumption)
- **Driving force:** consistency (primary), reliability (secondary)
- **Skill/step:** `agents/skills/execute-plan/SKILL.md` Phase 4 (Archive Plan); consumers today: `scripts/reverse_squash_guard.py` (the anchored record-name shape and the egress-bytes sha256 leg) and `scripts/done_sweep_gates_lib.py` `gate_archive_ceremony` (the exec-review filename-series arm beside the bound plan-review receipt)
- **Source reference:** `scripts/reverse_squash_guard.py` record-name grammar comment (`^<...>-plan-review-<slug>-exec-r<N>.md$`); the sibling precedent `.ai-playbook/reviews/2026-10-21-plan-review-readiness-files-coverage-quote-prefix-exec-r1.md` (a backfill record whose "Why this record exists" names the gate); this run wrote its pointer record before landing only after reading the guard; capture hygiene: `scan-public-hygiene.sh --files` pass
- **Why not fixed now:** skill-text edits land through the authoring loop; filed for routing
- **Dedup probe:** searched open backlog filenames and Problem text for `exec-r`, `backfill`, `plans-egress`, `egress bytes`; no open row owns the producer-duty gap (the gates' remedy text lives in the scripts); no merge

## Problem

The landing-side plans-egress gate refuses an archived plan whose reviews home carries no record named `<date>-plan-review-<slug>-exec-r<N>.md` witnessing the egress bytes' sha256, and the Phase 5 closeout has a matching exec-review receipt existence check. Nothing in execute-plan's Phase 4 (where the archive commit is composed) tells the orchestrator to produce that pointer record; both witnessed runs (the sibling's and this one) discovered the duty by reading the guard script or a sibling's backfill record. The gate's own remedy text names the record only at refusal time, after the landing attempt.

## Suggested fix

Add a Phase 4 step beside the archive commit: write the exec-r pointer record into the resolved reviews home before landing (name shape, the plan bytes sha256 at pre-archive, pointers to the exec-review record and its sidecar), and note when the bound plan-review receipt arm already satisfies the gate (a live plan-review record whose sidecar binds the plan identity, raw-byte digest, and yes verdict), so the pointer is produced when needed and not duplicated when not.
