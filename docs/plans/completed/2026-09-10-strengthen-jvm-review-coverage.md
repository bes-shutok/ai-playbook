# Plan: Strengthen JVM Review-Cycle Coverage

Backlog (scope of record): `docs/history/backlog/2026-09-10-strengthen-jvm-review-coverage.md`
Guideline SOT: `projects/.ai-playbook/java_guidelines.md` (numbered clauses; this plan appends rules #21-#25)
Plan review: `docs/reviews/2026-09-10-plan-review-strengthen-jvm-review-coverage-r<N>.md` (prefix glob; the latest round is the verdict of record)

## Terms

- **Guideline Pack**: the per-review bundle of shared language guideline paths plus section and rule hints that `doing-code-review` Step 2.5 attaches to worker prompts.
- **Clear-round quality bar**: the `execute-plan` Step 3.4 checklist a review round must satisfy before the Phase 3 loop may exit clean.
- **Risk-signal floor**: the `review-panel-selection` rule that escalates the worker set when the diff touches listed code-mutation surfaces.
- **Language overlay**: a stack-specific trigger file inside `doing-code-review` (`java-spring.md`) appended to worker prompts; the `review-agents` catalogs stay language-agnostic.
- **Census**: the branch-wide reference search over every added or changed declaration (`java_guidelines` #16).

## Assumptions

- assume backlog evidence classes 1-4 and 10 are already established as policy by commit 9ede3c1 and this plan closes only the delta (classes 5-9, census evidence, generic examples); basis: on-disk reads 2026-09-10 of `doing-code-review/SKILL.md` Step 2.5 Java paragraph, `java-spring.md` Review-wide Java checks, `review-panel-selection.md` risk-signal floor paragraph, `execute-plan/SKILL.md` Step 3.1 item 2 and Step 3.4 quality bar item 4, and `java_guidelines.md` rules #16-#20.
- assume the new rules take numbers #21-#25; basis: `java_guidelines.md` ends at #20 on disk.
- assume doc/skill-only plan conventions apply (the testing worker uses Validation Commands as primary evidence; no runtime scripts are introduced); basis: `doing-code-review` Doc/skill-only diffs boundary and `execute-plan` Step 3.1 item 5.
- assume the Kotlin overlay (`kotlin-spring.md`) stays unchanged; the scope of record names the Java/Spring overlay only; basis: the backlog Location list.
- assume the backlog item stays in place under `docs/history/backlog/` while this plan is open and moves to `docs/history/backlog/completed/` at plan completion; basis: `plans` Backlog origin and Plan Lifecycle.

Decision points requiring a grill: none remain.

## Gist & Examples

What changes: the Java/Spring review cycle gains five mandatory evidence classes, numbered `java_guidelines` rules #21-#25, wired through the same mechanism commit 9ede3c1 established for rules #16-#20: the overlay triggers them, the risk-signal floor pulls the `risk` worker in, both orchestrators hint them by rule number, and the clear-round quality bar lists their evidence surfaces. The simplification catalog additionally requires the declaration census to report its search evidence, and every new rule carries a generic worked example.

Traceability from the backlog Acceptance bullets:

- Staging record carries Guideline Pack paths plus applied rule hints: landed by 9ede3c1; Task 5 extends the hinted range to #16 through #25.
- Clear-round gate rejects missing Java review evidence when a listed surface is present: Task 5 extends the quality bar evidence list; Tasks 2 and 4 wire the triggers that make the surfaces detectable.
- Simplification worker stages unused changed declarations without treating compiler success as proof: Task 3 adds the census evidence requirement.
- Correctness and testing workers cover omitted, explicit-null, empty, and present states: landed (#17); unchanged by this plan.
- Risk worker checks error sinks, dependency coordinates, outbound URL schemes, readiness flags, and timeout resource lifecycle: sinks, coordinates, and schemes are landed (#18-#20); flag matrix and timeout lifecycle are new (Tasks 1, 2, 4, 5).
- Correctness worker verifies shared helpers preserve each raise-versus-degrade policy: new rule #21 (Tasks 1, 2, 5).
- Compatibility witness executes changed direct library calls: new rule #24 (Tasks 1, 2).
- Contract/docs worker reconciles living-documentation status claims and records deferrals as durable handoffs: new rule #25 (Tasks 1, 2, 5).
- A generic fixture demonstrates each check without real names: Task 1 examples, Task 2 trigger section, and the Validation Commands consistency probes.

**Before (today):** a Java/Spring branch reuses one shared row-mapping helper for a single-item route and a batch route; the batch route wraps the helper in try/catch and records failed rows as skipped. It ships a rollout flag, a per-request time budget, a minor dependency upgrade that calls a dependency API directly, and a living-doc paragraph still describing an integration as active. Rules #16-#20 force five evidence classes (unused declarations, nullable boundary states, error sinks, dependency advisories, outbound TLS), but no mandatory check asks whether the new caller changed the single-item route failure outcome from raise to degrade, whether an unrelated flag flips capability readiness, whether the budget can expire after the controller returns but before the serialized response is emitted, whether the upgraded dependency now rejects a value at runtime that compilation cannot catch, or whether the active claim has an executable consumer behind it. The panel can reach blocking-clean while all five gaps stay open.

**After (this plan):** the same branch cannot clear a round with those gaps unexamined. The overlay tells workers to trace every caller of the shared helper (#21), exercise the flag and configuration matrix (#22), verify the time budget at the last transport boundary and audit scheduled timeout resources (#23), demand an executable compatibility witness for the changed direct API usage (#24), and reconcile the living-doc status claim with implementation evidence, recording an intentional deferral as a durable handoff (#25). The risk-signal floor treats shared-helper reuse, flag wiring, and timeout boundaries as risk signals, and the Step 3.4 quality bar names all five evidence surfaces, so a round missing them is not clean.

Worked example for rule #21 (generic names only), showing the shape the new rules' examples take:

````markdown
```java
// Generic example for rule 21: one shared helper, two callers, different policies.
class OrderImportJob {
  // Single-item route: raises; the whole request fails on infrastructure errors.
  void importOne(Row row) {
    persist(mapRow(row));
  }

  // Batch route: degrades; only the offending item is recorded as skipped.
  BatchResult importBatch(List<Row> rows) {
    BatchResult result = new BatchResult();
    for (Row row : rows) {
      try {
        result.add(mapRow(row));
      } catch (RowLocalException e) {
        result.skipped(row, e);
      }
    }
    return result;
  }

  MappedRow mapRow(Row row) { /* shared conversion helper */ }
}
```
````

The review must catch a refactor that moves infrastructure-failure handling (connection loss, constraint violation) inside `mapRow` and has the batch route catch it: the single-item route then degrades where it previously raised, and rule #21 makes that a finding.

## Evaluation Criteria

**Quality dimensions:**

- correctness: every backlog Acceptance bullet maps to a task in the traceability list above; every rule number a consumer references resolves to a `java_guidelines.md` heading (consistency probes in Validation Commands).
- consistency: the evidence-surface and trigger wording across `doing-code-review` Step 2.5, `execute-plan` Step 3.1 and Step 3.4, `java-spring.md`, and `review-panel-selection.md` names the same five new surfaces (shared helpers, flag and configuration wiring, timeout boundaries, compatibility witness, living-doc claims).
- hygiene: no em dashes; no real service names, credentials, customer data, ticket identifiers, or internal URLs in new content; the public hygiene scan exits 0.
- maintainability: each new rule follows the existing numbered-clause format (imperative normative text plus a generic worked example; no project names).

**Done when:**

- All task checkboxes are checked and the Validation Commands block exits 0 on the changed tree.
- `scripts/check-no-em-dash.sh` and `scripts/scan-public-hygiene.sh` pass on the changed files.

**Ship when:**

- The next Java/Spring `execute-plan` Phase 3 or `doing-code-review` run consumes the updated overlay and records the new evidence classes in its staging Metadata; this is human-owned evidence from a future review run, tracked as prose here only.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**

- `projects/.ai-playbook/java_guidelines.md` (append rules #21-#25; rules #1-#20 are frozen)
- `agents/skills/doing-code-review/java-spring.md` (new trigger section plus Review-wide Java checks list extension and the ownership sentence extension; all other sections frozen)
- `agents/skills/review-agents/simplification.md` (unused-changed-declarations bullet extension only; rest frozen)
- `agents/skills/review-agents/review-panel-selection.md` (risk-signal floor Java paragraph extension only; rest frozen)
- `agents/skills/doing-code-review/SKILL.md` (Step 2.5 Java paragraph extension only; rest frozen)
- `agents/skills/execute-plan/SKILL.md` (Step 3.1 item 2 Java bullet and Step 3.4 quality bar item 4 extensions only; rest frozen)

**Tests:**

- None; this is a doc/skill-only change and the Validation Commands block is the testing evidence.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `agents/skills/doing-code-review/kotlin-spring.md`; reason: a Kotlin mirror is not in the scope of record; the backlog names the Java/Spring overlay. Accepted residual: rules #21-#25 stay unreachable from the Kotlin overlay under this plan; capture a backlog item for a Kotlin mirror only if execution review raises it as a valid unfixed finding.
- `agents/skills/review-agents/documentation.md`; reason: living-documentation reconciliation rides rule #25 and the overlay trigger; the documentation catalog stays language-agnostic and its existing living-doc gates are unchanged.
- `README.md`; reason: skill names, paths, and usage do not change.
- `docs/maintenance/document-registry.md`; reason: no documents are added, removed, or re-homed.

## Validation Commands

Task 6 executes this block in full after all edits land; no earlier task runs it, so the probes are expected to fail until then. Every positive probe aborts the run on a miss, so a partial implementation cannot pass.

```bash
#!/usr/bin/env bash
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }
expect() { # expect '<fixed-string>' <file> <label>
  grep -qF -- "$1" "$2" || fail "$3 (missing in $2)"
}

JG=projects/.ai-playbook/java_guidelines.md
OV=agents/skills/doing-code-review/java-spring.md
SIM=agents/skills/review-agents/simplification.md
RPS=agents/skills/review-agents/review-panel-selection.md
DCR=agents/skills/doing-code-review/SKILL.md
EP=agents/skills/execute-plan/SKILL.md

for f in "$JG" "$OV" "$SIM" "$RPS" "$DCR" "$EP"; do
  test -f "$f" || fail "missing expected file $f"
done

# Landed policy stays in place (guards against renumbering or removal)
expect '## 16. Review Every Changed Java Declaration for Unused Surface' "$JG" 'rule 16 heading'
expect '## 20. Enforce Required TLS at the Outbound Configuration Boundary' "$JG" 'rule 20 heading'

# New rules #21-#25 exist with their normative headings
expect '## 21. Preserve the Raise-versus-Degrade Policy of Every Caller in Shared Helpers' "$JG" 'rule 21 heading'
expect '## 22. Exercise the Feature-Flag and Configuration Matrix for Independent Readiness' "$JG" 'rule 22 heading'
expect '## 23. Enforce Time Budgets at the Last Transport Boundary and Audit Timeout Resource Lifecycles' "$JG" 'rule 23 heading'
expect '## 24. Add an Executable Compatibility Witness for Changed Direct API Usage' "$JG" 'rule 24 heading'
expect '## 25. Reconcile Living-Documentation Status Claims with Implementation Evidence' "$JG" 'rule 25 heading'

# Each new rule carries a generic worked example (marker line plus fenced block, generic names)
for n in 21 22 23 24 25; do
  sed -n "/^## $n\./,/^## /p" "$JG" | grep -q "Generic example for rule $n" || fail "rule $n has no generic worked example"
done

# Normative rule bodies are pinned (a rewritten or truncated body must fail)
expect 'only explicitly row-local problems may degrade' "$JG" 'rule 21 normative body'
expect 'must not become ready or unavailable through an unrelated flag' "$JG" 'rule 22 normative body'
expect 'must cover the final write to the client' "$JG" 'rule 23 normative body'
expect 'Compilation is not compatibility' "$JG" 'rule 24 normative body'
expect 'durable backlog item with an explicit owner and handoff' "$JG" 'rule 25 normative body'
expect 'accepted residual with its rationale' "$JG" 'rule 23 framework boundary qualifier'
expect 'must run hermetically' "$JG" 'rule 24 witness hermeticity'

# Overlay: Review-wide Java checks list extended, one bullet per new rule
expect '#21: raise-versus-degrade' "$OV" 'overlay rule 21 bullet'
expect '#22: flag and configuration matrix' "$OV" 'overlay rule 22 bullet'
expect '#23: time budgets at the last transport boundary' "$OV" 'overlay rule 23 bullet'
expect '#24: executable compatibility witness' "$OV" 'overlay rule 24 bullet'
expect '#25: living-documentation status claims' "$OV" 'overlay rule 25 bullet'
expect 'raise-versus-degrade tracing belongs to quality' "$OV" 'overlay ownership sentence'
expect 'the flag and configuration matrix and timeout lifecycle to risk' "$OV" 'overlay ownership sentence: flag and timeout owner'
expect 'the compatibility witness to implementation' "$OV" 'overlay ownership sentence: witness owner'
expect 'living-documentation reconciliation to documentation' "$OV" 'overlay ownership sentence: living docs owner'
expect '## Rollout, timeout, and shared-helper triggers (Spring)' "$OV" 'overlay trigger section'
expect 'apply #21 to every caller' "$OV" 'trigger section: shared helpers'
expect 'apply #22 to the flag and configuration matrix' "$OV" 'trigger section: flag matrix'
expect 'apply #23 at the last serialization and transport boundary' "$OV" 'trigger section: timeout boundary'
expect 'apply #24 alongside #19' "$OV" 'trigger section: witness'
expect 'apply #25 and reconcile with an executable consumer' "$OV" 'trigger section: living docs'
# The trigger section must follow the Review-wide Java checks section (ownership sentence inside it) and precede Message-driven handlers
awk 'index($0,"raise-versus-degrade tracing belongs to quality"){own=NR} index($0,"## Rollout, timeout, and shared-helper triggers (Spring)"){sec=NR} index($0,"## Message-driven handlers"){msg=NR} END{exit !(own>0 && sec>own && msg>sec)}' "$OV" || fail 'trigger section must follow the Review-wide Java checks section and precede Message-driven handlers'

# Simplification catalog: census evidence requirement
expect 'declaration census and report the reference-search' "$SIM" 'census evidence requirement'
expect 'compiler success is not proof of use' "$SIM" 'compiler-success disclaimer'

# Risk-signal floor: new mutation surfaces
expect 'Treat changed dependency coordinates, outbound service URL configuration, downstream error-response mapping' "$RPS" 'risk signal sentence opening'
expect 'shared conversion or persistence helpers reused across callers' "$RPS" 'risk signal: shared helpers'
expect 'feature-flag and configuration wiring' "$RPS" 'risk signal: flag wiring'
expect 'time-budget or timeout boundaries' "$RPS" 'risk signal: timeout boundary'

# Orchestrators: hint range extended and trigger lists wired (one commit so they cannot drift)
expect '#16 through #25' "$DCR" 'Step 2.5 hint range'
expect 'shared helpers reused across callers' "$DCR" 'Step 2.5 trigger list: shared helpers'
expect 'feature-flag and configuration wiring' "$DCR" 'Step 2.5 trigger list: flag wiring'
expect 'timeout or scheduled-executor boundaries' "$DCR" 'Step 2.5 trigger list'
expect 'living-documentation status claims' "$DCR" 'Step 2.5 trigger list: living docs'
expect '#16 through #25' "$EP" 'Step 3.1 hint range'
expect 'shared helpers reused across callers' "$EP" 'Step 3.1 trigger list: shared helpers'
expect 'feature-flag and configuration wiring' "$EP" 'Step 3.1 trigger list: flag wiring'
expect 'timeout or scheduled-executor boundaries' "$EP" 'Step 3.1 trigger list'
expect 'living-documentation status claims' "$EP" 'Step 3.1 trigger list: living docs'
expect 'shared-helper raise-versus-degrade tracing' "$EP" 'quality bar: shared helpers'
expect 'feature-flag and configuration matrix coverage' "$EP" 'quality bar: flag matrix'
expect 'scheduled timeout resource lifecycles' "$EP" 'quality bar: timeout lifecycle'
expect 'executable compatibility witnesses for changed direct API usage' "$EP" 'quality bar: witness'
expect 'living-documentation status reconciliation' "$EP" 'quality bar: living docs'
# Negative probes: the retired #16 through #20 range must not survive anywhere in either orchestrator
grep -qF '#16 through #20' "$DCR" && fail 'stale #16 through #20 range in doing-code-review'
grep -qF '#16 through #20' "$EP" && fail 'stale #16 through #20 range in execute-plan'

# Repository scans (the block already anchored itself to the repo root)
bash scripts/check-no-em-dash.sh file "$JG" "$OV" "$SIM" "$RPS" "$DCR" "$EP" || fail 'em dash found in changed files'
bash scripts/scan-public-hygiene.sh || fail 'public hygiene scan failed'

echo 'VALIDATION PASS: jvm review coverage wiring complete'
```

### Task 1: Add java_guidelines rules #21-#25 with generic worked examples

Files:
- `projects/.ai-playbook/java_guidelines.md`

- [x] Append `## 21. Preserve the Raise-versus-Degrade Policy of Every Caller in Shared Helpers` with this normative text: "Trace every shared conversion, mapping, or persistence helper to every caller in the changed branch. Each caller keeps its own raise-versus-degrade policy: infrastructure failures stay top-level failures, and only explicitly row-local problems may degrade to per-item results. When a helper is reused by a new caller, verify the reuse does not silently change an existing caller outcome from raise to degrade or the reverse. Add or verify a test per caller that proves a malformed infrastructure input fails the whole request where the caller raises, and only the offending item where the caller degrades."
- [x] Append `## 22. Exercise the Feature-Flag and Configuration Matrix for Independent Readiness` with this normative text: "When a change touches a rollout flag or its configuration, review the complete flag and configuration matrix, not only the default deployment mode. Enumerate the flag values and configuration profiles the changed scope can combine, and require a discriminating assertion per combination that matters for readiness. An independent capability must not become ready or unavailable through an unrelated flag."
- [x] Append `## 23. Enforce Time Budgets at the Last Transport Boundary and Audit Timeout Resource Lifecycles` with this normative text: "Verify time-budget enforcement at the last transport boundary: a budget can expire after the controller returns but before the serialized response is emitted, so the check must cover the final write to the client, not only the handler method (directly when the application owns serialization, or at the outermost application-owned boundary per the framework case below). Inspect scheduled executors, callbacks, and cleanup paths for per-request resources that outlive the request after a timeout, and require evidence they are released or bounded. When the application owns serialization or streaming, the budget check must cover the final write. When the framework performs serialization, require evidence that budget enforcement sits at the outermost application-owned boundary, such as a filter or interceptor, and record the framework-owned final write as an accepted residual with its rationale in the review's durable record, such as the staging doc's Release-gate ledger or a backlog item with an owner."
- [x] Append `## 24. Add an Executable Compatibility Witness for Changed Direct API Usage` with this normative text: "For every value shape that a changed direct call to a dependency API relies on, add a small executable compatibility witness: a test or scratch check that invokes the changed call against the upgraded dependency version. Compilation is not compatibility: a dependency can compile cleanly while rejecting a value at runtime because of reserved names, added validation, or changed default behavior. The witness must exercise the value shapes the change relies on and record the observed behavior. The witness must run hermetically: no live services and no paid APIs. When a dependency API cannot be exercised without real infrastructure, record a static compatibility analysis of the changed call, such as the upgraded artifact's source or changelog and rejection-path reading, as the evidence and note the residual runtime risk in the review's durable record, such as the Release-gate ledger or a backlog item with an owner. When a coordinate change alters many direct call sites, prioritize the value shapes the change relies on rather than every call site. See also #19 for the advisory audit."
- [x] Append `## 25. Reconcile Living-Documentation Status Claims with Implementation Evidence` with this normative text: "Reconcile every changed living-documentation status claim with implementation evidence: an integration described as active needs an executable consumer or producer, configuration, or an integration witness in the changed branch. When a status claim cannot be evidenced because scope is intentionally deferred, require a durable backlog item with an explicit owner and handoff instead of leaving the deferral only in review notes."
- [x] Each of the five rules embeds one generic worked example in a fenced block, using only generic names (for example `OrderImportJob`, `Row`, `BatchResult`), and each example block begins with the marker line `Generic example for rule 2N:` where 2N is the rule number (for example `Generic example for rule 21:` inside the fence); rule #21 uses the worked example from Gist & Examples; rule #22 shows a flag/profile combination flipping an unrelated capability; rule #23 shows a budget expiring between handler return and response serialization; rule #24 shows a reserved name accepted at compile time and rejected at runtime; rule #25 shows an active claim reconciled against an absent executable consumer with the deferral recorded as a durable handoff.
- [x] Commit: `docs: add java guidelines rules 21-25 for jvm review coverage`

### Task 2: Trigger the new rules in the Java/Spring overlay

Files:
- `agents/skills/doing-code-review/java-spring.md`

- [x] Extend the Review-wide Java checks list with five bullets after the existing `#20` bullet, in this exact form: `- \`java_guidelines.md\` #21: raise-versus-degrade policy of every caller at shared conversion and persistence helpers.` / `- \`java_guidelines.md\` #22: flag and configuration matrix coverage for independent capability readiness.` / `- \`java_guidelines.md\` #23: time budgets at the last transport boundary and scheduled timeout resource lifecycles.` / `- \`java_guidelines.md\` #24: executable compatibility witness for changed direct API usage.` / `- \`java_guidelines.md\` #25: living-documentation status claims reconciled with implementation evidence.`
- [x] Extend the ownership sentence at the end of the Review-wide Java checks section by appending: `Shared-helper raise-versus-degrade tracing belongs to quality; the flag and configuration matrix and timeout lifecycle to risk; the compatibility witness to implementation; living-documentation reconciliation to documentation.`
- [x] Add a new section `## Rollout, timeout, and shared-helper triggers (Spring)` immediately after the `## Review-wide Java checks` section (before `## Message-driven handlers (Spring Kafka)`), with Spring-specific triggers: shared `@Component` converters, mappers, or persistence helpers reused by a new caller (apply #21 to every caller); rollout flags, `@ConditionalOnProperty` wiring, or profile-specific configuration (apply #22 to the flag and configuration matrix); per-request time budgets, resilience timeout annotations, or `@Scheduled` cleanup (apply #23 at the last serialization and transport boundary and to scheduled resource lifecycles); changed direct dependency API usage, especially after a coordinate change (apply #24 alongside #19); changed living docs claiming an integration is active (apply #25 and reconcile with an executable consumer, producer, or witness).
- [x] Commit: `skills: trigger jvm coverage rules 21-25 in the java spring overlay`

### Task 3: Require census evidence in the simplification catalog

Files:
- `agents/skills/review-agents/simplification.md`

- [x] Extend the unused-changed-declarations bullet in the `delete:` checklist so it reads, after the existing sentence about the branch-wide reference search: "Run a complete changed-source declaration census and report the reference-search or static-analysis evidence with the finding; compiler success is not proof of use."
- [x] Commit: `skills: require census evidence for unused declaration findings`

### Task 4: Extend the risk-signal floor

Files:
- `agents/skills/review-agents/review-panel-selection.md`

- [x] Rewrite the first sentence of the risk-signal floor Java paragraph to exactly: `Treat changed dependency coordinates, outbound service URL configuration, downstream error-response mapping, shared conversion or persistence helpers reused across callers, feature-flag and configuration wiring that gates capability readiness, and time-budget or timeout boundaries as risk signals even when the diff is small.` Leave the paragraph's following sentence about the `risk` worker and the Java/Spring guideline checks unchanged.
- [x] Commit: `skills: treat shared helpers flag wiring and timeout boundaries as risk signals`

### Task 5: Wire the new evidence classes into both orchestrators

Files:
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/execute-plan/SKILL.md`

- [x] `doing-code-review` Step 2.5 Java paragraph: change the hinted range to `#16 through #25` and extend the trigger list so it ends: changed dependency coordinates, shared helpers reused across callers, feature-flag and configuration wiring, timeout or scheduled-executor boundaries, or living-documentation status claims.
- [x] `execute-plan` Step 3.1 item 2 Java bullet: change the applied range to `#16 through #25` and extend the changed-scope trigger list with the same four surfaces (shared helpers reused across callers, feature-flag and configuration wiring, timeout or scheduled-executor boundaries, living-documentation status claims).
- [x] `execute-plan` Step 3.4 quality bar item 4: extend the evidence list so it reads: changed declarations, nullable boundary states, downstream error payload sinks, changed dependency coordinates, outbound URL transport configuration, shared-helper raise-versus-degrade tracing, feature-flag and configuration matrix coverage, timeout transport boundaries and scheduled timeout resource lifecycles, executable compatibility witnesses for changed direct API usage (or the guideline #24 static-analysis fallback with its durable-record residual), and living-documentation status reconciliation, when those surfaces are present.
- [x] Both orchestrator edits land in the same commit so the two trigger lists cannot drift.
- [x] Commit: `skills: require jvm coverage evidence at the clear-round quality bar`

### Task 6: Final validation sweep

Files: none (verification only).

- [x] Run the Validation Commands block from the repo root; expect exit 0 with `VALIDATION PASS: jvm review coverage wiring complete`.
- [x] No commit; verification only.
