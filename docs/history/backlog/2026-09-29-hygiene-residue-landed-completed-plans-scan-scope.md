# Masked-ticket residue in landed and completed plan artifacts, and the scan scope that hides docs leaks

- **Filed:** 2026-09-29
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** witnessed-incident
- **Driving force:** reliability (privacy integrity); secondary simplicity
- **Source:** the 2026-09-29 hygiene-gate run during the skills-repo maintenance session. The default whole-repo scan passes while explicit `--files` mode fails on committed masked-prefix occurrences: the default scan scope covers only the strict trees, so everything under docs and scripts leaks invisibly unless the changed-files or explicit-files mode is invoked. Same-day remediation sanitized eleven files (the rolling prompt log, six open backlog origins, one test fixture, the document-registry audit note, the log's earlier entries); three artifacts remain and are protected by plan machinery, not by prose difficulty.

## Problem

The public-hygiene gate's own header states the policy: real identifiers outside the strict trees are masked, not excluded. Reality diverged: the default scan mode covers only the strict source trees, and committed files under docs and scripts accumulated employer ticket-prefix occurrences that no standing gate ever observes. Eleven files were sanitized to the user-approved generic form on 2026-09-29 (main commits through 4a60a5c4). Three remain:

- docs/history/plans/2026-09-29-execute-plan-task-local-verifier-declarations.md (the landed task-local-verifier plan): two witness-line occurrences. Its bytes are r5-review certified and digest-anchored; its execution has not started.
- docs/history/plans/completed/2026-09-28-execute-plan-codex-worker-terminal-recovery.md: four occurrences in an archived, completed-history artifact that conventions treat as immutable.

The published employer identifier in tracked files of a public repository is a completed integrity failure of the privacy gate; the mask exists precisely to prevent that publication. Under the incident-triage distinction (docs/history/backlog/2026-09-29-incident-origin-fix-class-fence-class-triage.md, filed, unlanded) this origin straddles both classes: the remediation half is fix-shaped (mask the residue), and the prevention half is fence-shaped (make the gate observe what it claims to policy) and must price its friction before landing.

## Expected behavior

- The landed plan carries the generic form through the smallest certified-plan byte change with re-certification recorded: substitute the two occurrences, re-derive and pin the fresh digest where the execution lane reads it, and let the execution-side stale-digest re-certification absorb the drift (execution has not started, so no live manifest binds the old bytes).
- The completed plan is either masked under a sanctioned completed-history exception (precedent: the document-registry row recording the user-approved 2026-09-27 generic-form masking of a ticket placeholder in a tracked doc) or explicitly allowlisted by operator decision as an archived record whose witness bytes cannot be reworded; silence is not a disposition.
- The scope question is decided explicitly, not by drift: either the done pre-commit sweep gains a changed-files hygiene arm covering docs and scripts paths it touches (fence-shaped; prices per-commit friction against the witnessed publication), or the default scope stays and the done runbook names the explicit changed-files invocation as the required pre-publish step (fix-shaped; names the manual step the operator accepted in the 2026-09-27 result-only scanning decision). Re-widening the default scope is operator direction, not a default.

## Dedup probe

The p90 certified-progress-sync entry (docs/history/backlog/2026-09-29-docs-branch-certified-plan-progress.md, logged) owns the certified-plan guard's receipt machinery, not hygiene masking; this origin's landed-plan arm is a one-token substitution with re-certification, not a guard change. The gate-delta symmetry origin (logged in the p100 group) prices future machinery additions and is the review lens for any scope-widening arm here. The 2026-09-27 release-gate adjudication set result-only scanning for the release skill's own gate, a different surface. No open item owns the hygiene residue or the scan-scope decision.

## Location

- docs/history/plans/2026-09-29-execute-plan-task-local-verifier-declarations.md: the two witness-line occurrences.
- docs/history/plans/completed/2026-09-28-execute-plan-codex-worker-terminal-recovery.md: the four occurrences.
- agents/skills/done/SKILL.md: the pre-commit sweep gate's scan invocation, where a changed-files arm or a runbook step lands.
- The machine-local scan script (facts key public_hygiene_scan_script): its default scope tuple and allowlist are the machine-side half of the scope decision; the repo-side skill text must name whatever is decided.

## Acceptance

- Zero masked-prefix occurrences remain in tracked files, verified by a full-tree pattern-file sweep rather than the default strict-tree scan.
- The landed plan's fresh digest is recorded where the execution lane reads it, and execution proceeds against the masked bytes.
- The scope decision is recorded as explicit operator direction in the done skill text, whichever way it goes; no silent scope drift.
