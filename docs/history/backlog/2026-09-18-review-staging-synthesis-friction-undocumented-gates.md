# Backlog: review-staging synthesis gates are documented too late (synthesizer rediscovers them every round)

Status: open
Priority: medium (re-affirmed by learn Step 1.8 witness 2026-09-18)
Workflow: backlog
Date: 2026-09-18
Class: review-staging / doing-code-review synthesis friction (skill documentation gap)
Origin: execute-plan run of docs/plans/2026-09-15-execute-plan-review-fix-pipeline-efficiency.md, seven synthesized staging docs (r1-r7). Every synthesis pass hit the same validator gates as surprises, costing a fix cycle per round: (1) confidence values are a closed enum (hypothesis / strong-evidence / verified) - worker-returned "high", "medium", "0.85" all fail; (2) the per-worker finding budget (all Critical + blocking expand; max 5 non-blocking High/Medium and 2 non-blocking Low per worker bucket, extras to overflow) is enforced mechanically; (3) overflow items live in the sidecar overflow list with their own dispositions, not in the findings conservation set; (4) the Markdown finding blocks must be `#### F<N>.` with `- **Severity**:` / `- **Blocking**:` bullets matching the sidecar exactly; (5) severity groups Critical/High/Medium/Low must exist and be ordered; (6) post-fix rounds need a populated Witness ledger; (7) risk_signals is a closed kebab-case tag set; (8) freshness Metadata lines (Review mode, Prior findings supplied as filter, Last fix commit) are required on/after EXTENDED_SIDECAR_MIN_DATE. Additionally, extracting a plan's Validation Commands bash block must strip the ``` fence lines or bash wedges inside a command substitution (r4 incident).

## Problem

The gates all exist in validate_review_staging.py and review-staging SKILL.md, but the synthesizing orchestrator meets them only as validator errors after writing a full doc. The skill's synthesis-facing summary does not enumerate the sidecar's hard structural requirements (closed enums, budgets, grouping, freshness lines, ledger), so each round pays the same discovery cost and risks mislabeling rather than fixing (e.g. "downgrading" a confidence instead of mapping it).

## Prevention

1. In review-staging SKILL.md, add a short "Synthesis-time hard gates" checklist at the point where the orchestrator writes the staging doc: closed enums (confidence, risk_signals, reason codes), the per-worker finding budget with overflow mechanics, the required Markdown block shape and severity groups, the freshness Metadata lines, the post-fix Witness ledger requirement, and the plan-Validation-block fence-stripping note.
2. Optionally extend validate_review_staging.py's error messages to name the remediation ("map to the closed confidence enum; overflow the extras") so a first failure is self-teaching.

## Evidence

r1-r7 synthesis passes in docs/tmp/execute-plan/2026-09-15-execute-plan-review-fix-pipeline-efficiency/ (session dir removed at Phase 5; the per-round staging docs under docs/reviews/ show the same fix cycles: confidence enum fixes in r2/r3/r4/r5/r7, finding-budget overflow moves in r2/r3/r4/r5/r6, review_mode enum fix in r7).

## Added witness (learn Step 1.8, 2026-09-18)

Independent confirmation from the learn-done-workflow-updates execute-plan run (five synthesized code-review staging docs, r1-r5, docs/reviews/2026-09-16-learn-done-workflow-updates-code-review-r*.md): every round's parent-synthesized doc failed `validate_review_staging.py --hard` at least once at the done Step 2.64 gate, and three of five rounds needed the done sub-agent to hand-complete the doc post-commit (Metadata freshness lines, `### Panel`/`### Counts`/`### Triage outcomes` sections, enum-only Review mode value, and the legacy-aggregate `.stats.json` sidecar whose required fields are documented only in the validator). Same root, same fix shape as the origin enumeration above; no new gate beyond those listed.
