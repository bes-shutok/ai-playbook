# AI Harness Friction Audit

## Baseline

**Window:** 2026-08-25 through 2026-09-23 inclusive (30 local calendar dates in Europe/Lisbon), captured at 2026-09-23 14:02 local time. The final date was still in progress at capture. This is the completed baseline inventory for the implementation plan. Both configured workspace roots were readable. The scan found 52 unique Git repositories represented by 57 checkout roots; all 57 were scanned for accessible audit artifacts, with zero filesystem traversal errors. Repeated review sidecars were deduplicated by SHA-256 content before counting. The report records no project names, repository paths, account or employee identifiers, customer data, prompt text, task titles, or source excerpts.

### Source census

| Source | Coverage found | Limits |
|---|---|---|
| Workspace roots and Git repositories | 2 of 2 roots readable; 52 unique Git repositories and 57 checkout roots scanned; zero traversal errors | Generated build and dependency directories and Git metadata were excluded from artifact search. A scanned repository can have no runtime artifacts for this window. |
| Review sidecars | 6,935 dated candidate files collapsed to 1,434 unique content records | Sidecars measure review activity and runtime attempts, not ordinary-work policy blocks. |
| Local event store | 357,766 event rows in the fixed window | Free-form log text is not a structured decision ledger; keyword matches were not counted as stop events. |
| Local task history | 3,500 turns at capture | Several turn outcomes do not have a cause that can be attributed to a rule or hook. |
| Hook log | 4,808 lines on 15 of the 30 dates | No consistent per-event allow/block result and reason. |
| Host-wide runtime aggregate | One available aggregate for 2026-08-24 through 2026-09-23 | It spans 31 dates, includes one date before this baseline, and aggregates parallel work. |

### Measurement method and provenance

The companion machine-readable snapshot is `docs/maintenance/ai-harness-friction-audit.snapshot.json`. Its `content_sha256` (`e98fd39f93e451c373e3a29da41399de9adc56a1d101f34c0ce71f78d42f84ab`) is SHA-256 over the sorted, compact JSON snapshot before adding the `content_sha256` field. Source labels S1-S5 identify data types only; they do not identify projects or repositories.

- **S1, local event store:** count rows whose event timestamp falls in the half-open local-time window `[2026-08-25 00:00 Europe/Lisbon, 2026-09-24 00:00 Europe/Lisbon)`. Free-form message, target, and module text was not used to attribute stops.
- **S2, local task history:** count turns whose start timestamp falls in the same half-open window, grouped by stored turn status. No message body, user request, title, or failure text was included.
- **S3, local hook log:** count lines whose first ISO calendar date falls from 2026-08-25 through 2026-09-23 inclusive; count the distinct dates with at least one such line. The available format has no consistent decision result or reason field.
- **S4, review sidecars:** recursively select candidate sidecar files with an ISO date in the filename within the inclusive window, excluding Git metadata and generated build/dependency directories. Count file copies, then deduplicate by SHA-256 content. Within unique versioned coverage records, count each `coverage.attempts[]` outcome and `failure_class`; elapsed values use seconds from those same attempt records. The 29 failure classes partition attempts with outcome `failed` or `timeout`.
- **S5, host-wide runtime aggregate:** preserve the already-published 31-date aggregate as a related timing context; do not subtract or proportionally reallocate its values to claim an exact 30-day cause ranking.

### Measured runtime failure ranking (not a policy-stop ranking)

| Observed class | Count | Source and denominator | Attribution |
|---|---:|---|---|
| Orchestrator wait timeout | 10 | One failure class within the 29 failed or timed-out attempts among 887 attempts across 1,434 unique sidecars | High; runtime wait failure, not a policy block |
| Orchestrator output capture | 6 | One failure class within that same 29-attempt subset | High; runtime capture failure |
| Worker timeout | 5 | One failure class within that same 29-attempt subset | High; worker lifecycle/runtime failure |
| Provider inactivity timeout | 3 | One failure class within that same 29-attempt subset | High; provider/runtime failure |
| Provider unavailable | 2 | One failure class within that same 29-attempt subset | High; provider admission failure |
| Provider timeout | 2 | One failure class within that same 29-attempt subset | High; provider/runtime failure |
| Provider rate limited | 1 | One failure class within that same 29-attempt subset | High; provider capacity failure |

The unique sidecars recorded 887 review attempts: 857 completed, 17 timed out, 12 failed, and 1 was cancelled. These numbers rank observed review execution failures only. They do not show that review instructions or security checks caused those failures. Across the same sidecars, 820 attempts had elapsed-time values; the median was 10 seconds and the 90th percentile was 18 seconds. Summed worker elapsed time is not user wall-clock delay because attempts can overlap.

The existing host-wide runtime aggregate for 2026-08-24 through 2026-09-23 records 4,877 agent-delegation calls, 261 errors, and 1,717,199 seconds of joined tool time. Its largest duration category is agent delegation, followed by result polling, interactive prompts, unattributed shell execution, and named shell-command groups. The report's scriptable-candidate checks found none that passed its judgment-free threshold. Tool-call duration can include work, parallel execution, or waiting and does not identify a stop cause. This aggregate also includes one date outside the baseline window.

### Policy stop causes remain unrankable

- **Instruction, skill, and hook blocks:** no available source records a consistent structured event with the deciding rule, allow/block result, and reason. The accessible hook log contains 4,808 lines across 15 of the 30 dates but has no usable per-event policy disposition. Therefore there is no defensible count or elapsed-time ranking for policy, skill, or hook causes.
- **Task interruptions:** the local task-history store contained 3,500 turns at capture: 2,931 completed, 428 interrupted, 132 failed, and 9 still in progress. The interruption/failure records do not consistently identify whether a user, provider, runtime, instruction, or hook caused the outcome. Treating all interrupted turns as policy stops would be incorrect.
- **Generic log keyword hits:** the local event store contains free-form rows, not a structured stop ledger. Phrase matches overlap and are not distinct events or causal attributions, so they are not reported as stop counts.
- **Workspace review data:** 1,434 unique review sidecars were found after content deduplication. Review verdicts, finding totals, and elapsed time measure review activity and quality, not whether a policy prevented ordinary work.

### Decisions supported by this baseline

1. Keep provider capacity, worker liveness, output capture, and orchestration failures separate from policy changes. The structured review records identify those runtime causes; they do not justify weakening a policy gate.
2. Do not claim that any specific security instruction or verification check was the most frequent stop. Available telemetry cannot establish that conclusion.
3. Remove malicious co-user defenses because the single-operator scope is an explicit user decision, not because these incomplete metrics prove their frequency.
4. Preserve task-owned data, same-path conflict reporting, protections against unintended external actions, and application-code security.
5. Require a local reproduction or direct policy-to-outcome evidence before narrowing another check. No additional examples from other project checkouts are needed to execute this plan.

### Reconciliation and privacy check

The source census reconciles 2 readable workspace roots, 52 unique Git repositories, 57 scanned checkout roots, and zero traversal errors. Review-sidecar content digests were counted once even when the same record appeared in multiple checkouts. Attempt outcomes sum to 887 (857 + 17 + 12 + 1); the 29 timed-out or failed attempts equal the seven structured failure-class totals above. Turn statuses sum to 3,500. Raw transcripts and source content were not copied into this report.

Repeatable aggregate and digest check (prints only `PASS` or failing check names, never metric values):

```bash
python3 - <<'PY'
import hashlib
import json
from pathlib import Path

path = Path("docs/maintenance/ai-harness-friction-audit.snapshot.json")
data = json.loads(path.read_text())
claimed_digest = data.pop("content_sha256")
actual_digest = hashlib.sha256(
    json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
coverage = data["coverage"]
sources = data["sources"]
sidecars = sources["S4_review_sidecars"]
outcomes = sidecars["attempt_outcomes"]
turns = sources["S2_local_task_history"]
classes = sidecars["failure_class_counts"]
report_text = Path("docs/maintenance/ai-harness-friction-audit.md").read_text()
host = sources["S5_host_runtime_aggregate"]
published_values = [
    f"| Workspace roots and Git repositories | {coverage['workspace_roots_readable']} of {coverage['workspace_roots_found']} roots readable; {coverage['unique_git_repositories']} unique Git repositories and {coverage['checkout_roots_scanned']} checkout roots scanned; zero traversal errors |",
    f"| Review sidecars | {sidecars['dated_file_copies']:,} dated candidate files collapsed to {sidecars['unique_content_records_sha256']:,} unique content records |",
    f"| Local event store | {sources['S1_local_event_store']['row_count']:,} event rows in the fixed window |",
    f"| Local task history | {turns['turn_count']:,} turns at capture |",
    f"| Hook log | {sources['S3_local_hook_log']['line_count']:,} lines on {sources['S3_local_hook_log']['dates_with_entries']} of the {sources['S3_local_hook_log']['window_dates']} dates |",
    f"The unique sidecars recorded {sidecars['attempt_count']} review attempts: {outcomes['complete']} completed, {outcomes['timeout']} timed out, {outcomes['failed']} failed, and {outcomes['cancelled']} was cancelled.",
    f"within the {sidecars['failed_or_timed_out_attempts']} failed or timed-out attempts among {sidecars['attempt_count']} attempts across {sidecars['unique_content_records_sha256']:,} unique sidecars",
    f"Across the same sidecars, {sidecars['attempts_with_elapsed_seconds']} attempts had elapsed-time values; the median was {sidecars['elapsed_median_seconds']} seconds and the 90th percentile was {sidecars['elapsed_p90_seconds']} seconds.",
    f"the local task-history store contained {turns['turn_count']:,} turns at capture: {turns['status_counts']['completed']:,} completed, {turns['status_counts']['interrupted']:,} interrupted, {turns['status_counts']['failed']:,} failed, and {turns['status_counts']['in_progress']:,} still in progress.",
    f"| Orchestrator wait timeout | {classes['orchestrator_wait_timeout']} |",
    f"| Orchestrator output capture | {classes['orchestrator_output_capture']} |",
    f"| Worker timeout | {classes['worker_timeout']} |",
    f"| Provider inactivity timeout | {classes['provider_inactivity_timeout']} |",
    f"| Provider unavailable | {classes['provider_unavailable']} |",
    f"| Provider timeout | {classes['provider_timeout']} |",
    f"| Provider rate limited | {classes['provider_rate_limited']} |",
    f"| Host-wide runtime aggregate | One available aggregate for {host['window_start']} through {host['window_end']} |",
    "Its largest duration category is " + host["largest_duration_categories"][0]
    + ", followed by " + ", ".join(host["largest_duration_categories"][1:-1])
    + ", and " + host["largest_duration_categories"][-1] + ".",
]
checks = {
    "digest": actual_digest == claimed_digest
    and claimed_digest == "e98fd39f93e451c373e3a29da41399de9adc56a1d101f34c0ce71f78d42f84ab",
    "coverage": coverage["workspace_roots_found"]
    == coverage["workspace_roots_readable"] == 2
    and coverage["unique_git_repositories"] == 52
    and coverage["checkout_roots_scanned"] == 57
    and coverage["filesystem_walk_errors"] == 0,
    "attempt-outcomes": sum(outcomes.values()) == sidecars["attempt_count"] == 887,
    "failure-classes": sum(classes.values())
    == sidecars["failed_or_timed_out_attempts"]
    == outcomes["failed"] + outcomes["timeout"] == 29,
    "turn-statuses": sum(turns["status_counts"].values()) == turns["turn_count"] == 3500,
    "published-counts": all(value in report_text for value in published_values),
    "host-aggregate": all(
        value in report_text
        for value in (
            f"{host['agent_delegation_calls']:,} agent-delegation calls",
            f"{host['errors']:,} errors",
            f"{host['joined_tool_seconds']:,} seconds of joined tool time",
            (
                f"{host['scriptable_candidates_passing_threshold']} that passed its judgment-free threshold"
                if host["scriptable_candidates_passing_threshold"]
                else "none that passed its judgment-free threshold"
            ),
        )
    ),
}
failed = [name for name, passed in checks.items() if not passed]
print("FAIL " + ",".join(failed) if failed else "PASS")
raise SystemExit(bool(failed))
PY
```

Repeatable privacy scan (prints only `PASS` or failing category names, never matched values):

```bash
python3 - <<'PY'
import re
from pathlib import Path

text = "\n".join(
    Path(path).read_text()
    for path in (
        "docs/maintenance/ai-harness-friction-audit.md",
        "docs/maintenance/ai-harness-friction-audit.snapshot.json",
    )
)
checks = {
    "absolute-path": r"/(?:Users|home)/[^\s`]+",
    "email": r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
    "url": r"https?://",
    "ticket-id": r"\b(?!SHA-)[A-Z]{2,10}-\d{3,}\b",
    "uuid": r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    "windows-path": r"\b[A-Za-z]:\\[^\s`]+",
}
failed = [name for name, pattern in checks.items() if re.search(pattern, text, re.I)]
print("FAIL " + ",".join(failed) if failed else "PASS")
raise SystemExit(bool(failed))
PY
```

For each report or snapshot edit, also review only the changed content for workspace/project names, account details, task titles, or copied source text. Do not reopen project sources for this scan. The baseline capture was authored from aggregate values, then the snapshot arithmetic and name/path scan were reconciled without retaining matched sensitive strings.

### Synthetic example

Suppose one session's completion check sees a scratch artifact created by another session. If neither session owns the artifact and no same-path edit is at risk, the shared-workspace observation alone should not stop completion. If both sessions edit the same file, keep the existing write-conflict behavior; the audit does not add merge or recovery behavior. This example is illustrative only; it does not describe an observed project incident.

## Final implementation record

Recorded 2026-09-23 on the audit execution branch. The baseline above remains unchanged as the pre-change comparison. Item-by-item lifecycle decisions live in the implementation plan and the normal archive locations; this record keeps anonymized categories and aggregate counts only.

### Evidence-backed decisions

1. **Malicious co-user defense removal.** The inventoried active surfaces (shared instruction entrypoints, six skill surfaces, and the registered hook adapters) contained exactly one control whose sole purpose is hostile co-user defense: the threat-model rationale paragraph in the skill consent gate's documentation. The paragraph was removed from that hook's documentation; the consent gate itself stays with its workflow-consent rationale ("did the required authoring skill run?"), and its "not a security boundary" scoping stays in agent-agnostic wording. A corpus search confirmed no duplicated wording elsewhere. Reintroduction is gated by a new policy contract test suite (six tests) pinning: no co-user-only controls on active surfaces, draft-only Slack outbound, authorization-gated external writes, one agent-agnostic shared policy source with adapter-specific mapping only where required, no operational reference to the removed control, and absence of the removed wording from every configured entrypoint. Contract result: 2 of 6 tests RED against the reproduced pre-removal state, exactly on the removed control; 6 of 6 GREEN after removal, with the unauthorized Slack send contract draft-only throughout.
2. **Unrelated-peer false block fix.** The dirt regression gate reproduced one false block on ordinary parallel work: a peer's staged whole-file deletion of their own unrelated file aborted a pass-shaped run with a misclassified git-environment error (exit 2) instead of being classified. The fix is minimal: a path absent from both the worktree and the index is checked against HEAD, and HEAD-tracked paths proceed to the normal diff classification. The gate's intentional data-loss protection is unchanged: staged deletions of post-base content still classify as regressions with the file named, and never-tracked ghost paths still fail closed. Two regression probes pin the fix.
3. **Rejected archive lifecycle.** Rejected plan and backlog archive destinations now exist with READMEs that require preserved source content, a decision date, and a decision reason. Registry validation, origin closure, active-plan readiness, the done sweep, the docs-branch certified-plan guard, and the backlog duplicate sweep recognize rejected records as closed surface, and moves happen only as visible git renames. Six new lifecycle tests are green while all completed and deferred controls stay green. The reconciliation produced zero reject decisions, so the archives ship exercised by tests, not by occupied rows.

### Affected adapters

Adapter behavior changed nowhere. The only adapter-surface edit is the documentation rationale removal in one hook's shared README, which serves that hook's per-harness recipes without changing any recipe's behavior. One classification script (the dirt gate) changed as described above. The instruction-entrypoint inventory confirmed every active surface resolves to the canonical shared rules, so no entrypoint copy needed an edit.

### Stop categories before and after

| Category | Before | After |
|---|---|---|
| Hostile co-user controls on active surfaces | 1 (documentation rationale) | 0; reintroduction test-gated |
| Reproduced unrelated-peer false blocks | 1 class (peer staged deletion misclassified) | 0; classified and regression-pinned |
| Structured runtime failure classes | 7 classes over 29 of 887 deduplicated review attempts | unchanged; runtime-owned, out of policy scope |
| Policy, skill, and hook stop ranking | unrankable | unrankable; the attribution boundary stands |
| Rejected archive lifecycle support | absent | present in both archives; zero rejects recorded |

### Preserved safeguards

- Accidental data loss: done sweep baseline gates, foreign and peer-session staging refusals, dirt regression classification, and same-path write-conflict handling are unchanged.
- External-action authorization: git push, Slack outbound actions, remote documentation pages owned by someone else, and remote actions on personal projects remain explicitly authorization-gated, now pinned by the contract suite.
- Product and application-code security: untouched by this plan; review security catalogs and adversarial review personas remain in place.
- Worker liveness and cleanup fences: an unresolved worker is never read as free capacity and never permits a second claim; a timed-out worker with unverified cleanup stays fenced with relaunch prohibited. Both fences are pinned by characterization tests.

### Unresolved runtime-only causes

The attribution boundary stands: available hook logs still carry no structured allow or block dispositions, so policy stop causes remain unrankable until the hook-visibility follow-up lands; that follow-up stays live. Provider capacity, worker timeout, output capture, and orchestration wait failures remain runtime classes owned by the runtime reconciliation workstream. Five backlog items in that family stay live and are deliberately not routed by this plan: that workstream is active in a separate checkout of this repository and owns their disposition.

### Lifecycle and validation outcome

One superseded origin moved to the backlog completed archive with this plan recorded as successor; three already-implemented origins moved there with the implementing completed plan recorded as execution reference; zero rejects. Final validation on the execution branch: policy contract suite 6 of 6 GREEN; rejected archive, origin closure, plan guard, and dedupe suites 32 tests GREEN; parallel-work and done-sweep suites 23 tests GREEN; runtime fence characterizations GREEN; registry validator 0 hard findings with the living audit row accepted; origins corpus scan 0 unresolved origins across 116 archived plans; the embedded aggregate reconciliation and privacy scans both PASS.
