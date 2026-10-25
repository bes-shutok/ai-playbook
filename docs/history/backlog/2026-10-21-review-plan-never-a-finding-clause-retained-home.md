# Review-plan lost its only "their absence is never a finding" clause for guessed inventory

Cluster: docs/history/backlog/2026-10-25-review-plan-nonconvergence-recovery.md (shared review-plan defect surface: both origins concern unsupported reviewer findings that add churn; this origin witnesses the missing clause)

- **Filed:** 2026-10-21, execute-plan Phase 3 r1 review of plan-validation-command-undefined-repo (finding cd1)
- **Status:** covered (docs/history/plans/2026-10-25-review-plan-nonconvergence-disposition.md)
- **Workflow:** backlog
- **Priority:** low
- **Origin class:** self-serving
- **Class:** fix-class (remove a false-positive path: without the clause a reviewer may stage absent guessed inventory as an ordinary finding; readiness and blocking behavior are unchanged)
- **Driving force:** consistency (primary), simplicity (secondary)
- **Skill/step:** `agents/skills/review-plan/SKILL.md` Step 1 item 6 and the Readiness boundary paragraph
- **Source reference:** Task 2 intermediate review correctness-completeness F1 (left-as-is, recorded for Phase 3) and `.ai-playbook/reviews/2026-10-21-plan-validation-command-undefined-repo-code-review-r1.md` finding cd1 (Low, non-blocking, confidence likely); capture hygiene: `scan-public-hygiene.sh --files` pass
- **Why not fixed now:** an in-run restoration mutates reviewed source scope and would require a fresh targeted review round for a Low residual with no behavior change; the byte-neutral ceiling (64158) leaves 6 bytes of headroom, so the clause needs a paired deletion; deferred by the execute-plan orchestrator at Phase 3 r1 triage
- **Dedup probe:** searched open backlog filenames and Problem text for `never a finding`, `test identities`, `guessed inventory`, `readiness boundary`; nearest: `docs/history/backlog/2026-10-21-plan-review-validation-block-check-pinned-mirror.md` (same landing, different subject: a cross-reference between two live clauses versus a deleted clause's missing half); no merge

## Problem

Task 2's byte-neutral deletions removed the Step 1 item 6 sentence that priced absent test identities, supporting path inventories, schema resources, and exact task commands as never a finding. The recorded retained home, the Readiness boundary paragraph's "a behavior-complete plan is ready without test identities, supporting path inventories, fixture details, or exact task commands" sentence, carries only the readiness half (never a blocker); no surviving text in the file prices their absence as never a finding (`grep -c 'never a finding' agents/skills/review-plan/SKILL.md` is 0 at the landed bytes). A reviewer consulting item 6 or the boundary paragraph regains license to stage missing-inventory findings as ordinary findings, reintroducing the review churn the deleted sentence pinned away. Three of five Phase 3 lenses read section 6's exhaustive finding enumeration plus the BOUNDARY-READY-FIXTURE judgment as sufficient retention, so the gap is arguable; the two independent sightings (Task 2 intermediate review, Phase 3 r1) make it worth a durable decision.

## Suggested fix

Either restore a short clause at the boundary paragraph ("; their absence is never a finding") paying the bytes with an equivalent deletion in the same file, or record in the file that section 6's enumeration is the exhaustive finding vocabulary and absent guessed inventory sits outside it. One sentence, no gate.
