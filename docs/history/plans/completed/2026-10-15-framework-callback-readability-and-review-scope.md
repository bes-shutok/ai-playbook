# Plan: shared JVM callback and method-shape readability rule

Backlog origin: docs/history/backlog/2026-10-14-framework-callback-readability-guidance.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-10-17-plan-review-framework-callback-readability-and-review-scope-pf2953df7-r*.md (the highest rN is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 0.75h
Authoring claim: docs/tmp/authoring-claims/2026-10-14-framework-callback-readability-guidance.md (session 1F0A2561-F4C2-4E03-8B32-435A23010905)

## Terms

- **Callback:** a function, lambda, or framework hook that is invoked by another component at a defined point in a flow.
- **Cognitive load:** reasoning required to understand a block's order, branches, captured state, or interaction with surrounding work.
- **Observable side effect:** a state change, I/O operation, event emission, metric write, or other effect visible outside the expression that performs it.
- **Method-local type:** a class, enum, or record declared inside a method body.
- **Loaded method-length limit:** the method line limit configured in the project's active guideline pack.
- **Changed-code signal:** a diff containing a callback or nested block with an observable side effect or substantial cognitive load, a method-local type, or a changed method at 80% or more of its loaded method-length limit.
- **Consumer project:** a separate application repository that loads and applies this repository's JVM guidance.
- **Residual:** follow-up work whose required source or evidence is outside this plan's repository scope.
- **True catch:** an adjudicated real issue found by the readability check, or an actionable issue found only by the recommended worker.

## Why

Anonymous callbacks can hide state changes or metrics. Shared Java and Kotlin guidance adds one extraction rule and focused signal while leaving pure mappings inline.

## Gist & Examples

TLDR: Put callback and method-shape readability rules in shared JVM guidance and connect the review checks, improving code-quality with a small, conditional review-scope addition.

**Before (today):** when a transaction completes, an anonymous metrics callback reads captured start-time and atomic-observation state and records several phases. The registration point is visible, but the state ownership and phase sequence are difficult to see inside the callback.

**After (this plan):** the same transaction-completion callback remains registered at the same point and delegates to an explicitly named helper or object that owns the captured state and names the metric phases. The call site makes the callback's purpose clear without changing its lifecycle or transaction boundary.

A pure mapping such as `value -> value.trim()` or `value?.trim()` stays inline; extract a callback that writes a metric, changes state, performs I/O, or coordinates phases into a named function. Compare concise maximum-selection forms with explicit comparisons while preserving null handling and the required one-microsecond increment.

Flag the profile-merge method (complexity 7, 65 counted lines, method-local record); leave a one-line pure callback inline.

## Outcome

Create one shared JVM rule and connect the language and review guides to it.

- Java and Kotlin guidance points to the same rule, with examples in both languages.
- The quality catalog names one method-readability check. Qualifying focused rounds receive an advisory to include the existing quality-owning worker when the selected panel would omit it; the advisory is warning-only until a true catch supports a separate reviewed promotion.
- The witnessed complex method is flagged, and simple pure callbacks remain inline.

Gate delta: Adds one warning-only, nonblocking method-readability check and one warning-only focused-panel selection advisory; neither affects review launch or readiness. The rule is centralized in the JVM guide, so Java and Kotlin guidance use pointers instead of future duplicate copies; the current language guides contain no duplicate rule to remove. The advisory applies only when the changed-code signal is present and may add one invocation of the existing `correctness-completeness` worker if followed; it adds no worker role or review round. The witness is the origin incident in `docs/history/backlog/2026-10-14-framework-callback-readability-guidance.md` and the explicit user decision on 2026-10-17. Expected frequency for both mechanisms is changed-code-signal rounds; the rate is unmeasured without consumer source. False-positive cost is one nonblocking finding for the check and, if the panel advisory is followed, one extra existing-worker invocation. At the 2027-04-15 review, promote a mechanism only after its own true catch in a separate reviewed change; remove each mechanism without its own catch, update the active entry, and retain the removals row with the sunset witness.

## Assumptions

- The shared JVM guide is the canonical home for rules applying to both Java and Kotlin; language-specific guides contain pointers and syntax-specific examples.
- The consumer project is outside this checkout. Adoption remains unverified because consumer source is absent from this repository and is recorded as residual work, not an implementation task or release condition.
- The existing `correctness-completeness` worker owns the quality lens, as documented in `agents/skills/review-agents/review-panel-selection.md`. The worker-selection recommendation and readability check are warning-only at landing; each may be promoted only in a separate reviewed change after its own true catch.

Decision points requiring a grill: extract callbacks or nested blocks with substantial cognitive load (user decision, 2026-10-16; Terms, Gist, Tasks, Evaluation Criteria); any observable side effect is sufficient for extraction, while pure one-line transformations and simple guards may stay inline (user decision, 2026-10-16; Gist, Tasks, Evaluation Criteria); method-local classes, enums, and records always move to enclosing class scope, with needed values passed explicitly (user decision, 2026-10-16; Terms, Tasks); 80% of the loaded method-length limit defines the near-limit signal (user decision, 2026-10-16; Terms, Tasks, Review Scope); the shared rule belongs in `jvm_guidelines.md` and both language guides point to it (user decision, 2026-10-16; Tasks); recommend the existing `correctness-completeness` worker for qualifying focused rounds, with an advisory-only warning posture until a true catch and a separate reviewed promotion (user accepted recommendation, 2026-10-17; Outcome, Tasks, Gate delta).

## Evaluation Criteria

**Quality dimensions:**
- Readability: reviewers can identify callback purpose and named phases at the call site; the witnessed multi-phase example is flagged and a simple pure callback is not.
- Correctness: nullable values and the exact required one-microsecond increment remain preserved in maximum-selection examples; transaction ownership and callback timing claims match primary Spring documentation for the API discussed.
- Scope: Java and Kotlin point to one shared JVM rule. When its signal is present, the review trigger recommends the existing worker; it is invoked only if the recommendation is followed.

**Done when:**
- The shared JVM section, Java and Kotlin pointers, quality check, warning-only focused-panel advisory, admission entry, and pre-registered removal row are present and cross-referenced.
- The required review-agent validation scripts and public-hygiene scan pass, and the execution record documents the witnessed cases and bounded overlap audit.

**Ship when:** No external release condition gates shipping from this repository. Non-gating operations follow-up: consumer-project adoption, per-registration isolation, exact lock-order verification, and candidate-level maximum-expression verification remain unverified because consumer source is absent from this repository [class: OPERATIONS_FOLLOW_UP]. Evidence owner: consumer-project owner. Closure: inspect adoption, registration-instance ownership, the original lock sequence, and the maximum-selection expression in a consumer checkout and record each result. This follow-up is outside repository implementation scope and does not gate shipping.

## Review Scope

**Explicit must-fix:** findings on these paths are in scope:

**Documentation:**
- `projects/.ai-playbook/jvm_guidelines.md`
- `projects/.ai-playbook/java_guidelines.md`
- `projects/.ai-playbook/kotlin_guidelines.md`
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/review-panel-selection.md`

**Machinery configuration:**
- `scripts/machinery_registry.json`

**Execution record:** the Phase 1 task 3 implement log named in the session manifest.

**Validation support (read-only):** `scripts/machinery_inventory.py` checks the tracked machinery registry.

**Validation carrier:** `scripts/test_framework_callback_readability_session.sh` reads the run-base and Task 3 log path from the session manifest, then runs the manifest, ancestry, and em-dash checks for this plan.

**Origin evidence (read-only):** `docs/history/backlog/2026-10-14-framework-callback-readability-guidance.md` supplies the callback and profile-merge witnesses for Task 3.

**Read-only audit:** inspect the JVM, Java, and Kotlin guides plus the two review-agent files listed above for overlapping callback, local-type, or method-length guidance. Record each file's verdict; any unlisted cleanup becomes a separate residual.

**Plan-related extension:** implementation and review may change files not listed above only when they fix a regression introduced by this plan or complete an explicit task above. Weak or speculative links are out of scope.

## Validation Commands

```bash
set -euo pipefail
python3 scripts/check_review_agent_portability.py
python3 scripts/test_review_agent_doors.py
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
git diff --check
bash scripts/test_framework_callback_readability_session.sh \
  --manifest docs/tmp/execute-plan/framework-callback-readability-and-review-scope/manifest.md
# All preceding checks must pass. The final inventory check is expected to exit 1 with exactly the 24 pre-existing diagnostics recorded in docs/tmp/execute-plan/framework-callback-readability-and-review-scope/phase-2-validation.log.md; any changed diagnostic set is unexpected. The block therefore exits 1 and is not a full validation-block pass.
python3 scripts/machinery_inventory.py --check
```

## Tasks

### Task 1: Add the shared Java and Kotlin readability rule

Files:
- `projects/.ai-playbook/jvm_guidelines.md`
- `projects/.ai-playbook/java_guidelines.md`
- `projects/.ai-playbook/kotlin_guidelines.md`

Primary class anchors:
- `jvm_guidelines` in `projects/.ai-playbook/jvm_guidelines.md`
- `java_guidelines` in `projects/.ai-playbook/java_guidelines.md`
- `kotlin_guidelines` in `projects/.ai-playbook/kotlin_guidelines.md`

- [x] Add JVM section #28 after section #27. State that section #27 owns recurring finite-vocabulary enum placement and cannot absorb callback extraction or method-length review. [class: IMPLEMENTATION_REQUIRED]
- [x] Extract callbacks or nested blocks with substantial cognitive load or any observable side effect into explicitly named functions or methods invoked at the original callback point. Preserve callback and registration lifecycle, captured-state ownership, transaction boundary, and lock order where applicable. Leave simple pure one-line transformations and guards inline. [class: IMPLEMENTATION_REQUIRED]
- [x] Declare every method-local class, enum, and record at enclosing class scope, passing needed values explicitly. [class: IMPLEMENTATION_REQUIRED]
- [x] Compare concise maximum-selection expressions with explicit comparisons. Preserve nullable behavior and the exact one-microsecond increment required by the source expression, and state that fewer lines alone do not establish clearer code. Add Java and Kotlin examples without duplicating the rule text in language guides. [class: IMPLEMENTATION_REQUIRED]
- [x] Explain that method length is considered alongside existing complexity checks; the existing cognitive-complexity criterion remains responsible for deep-nesting signals, with no separate nesting threshold. Include the witnessed method (complexity 7, 65 counted lines, method-local record) and the one-line pure negative example; point to primary Spring documentation for any framework-specific callback timing or registration claim. [class: IMPLEMENTATION_REQUIRED]
- [x] Add pointers from the Java and Kotlin guides to the new JVM section without duplicating rule text. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the witnessed method and a short single-side-effect callback or method-local type, expect a readability signal; given a one-line pure mapping, expect no extraction or review signal. [class: REPOSITORY_TEST]
- [x] Commit: `docs: add shared JVM callback readability guidance` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Connect the quality check and focused-panel selection

Files:
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `scripts/machinery_registry.json`

Primary class anchors:
- `Naming and Structural Clarity` in `agents/skills/review-agents/quality.md`
- `review-panel-selection` in `agents/skills/review-agents/review-panel-selection.md`

- [x] Add one `quality#<slug>` method-readability check for callbacks or nested blocks with substantial cognitive load or any observable side effect, method-local types, and methods at or above 80% of the loaded length limit. Point to the JVM rule and state its added coverage beyond existing complexity and single-responsibility checks; retain the existing cognitive-complexity criterion for deep-nesting signals without adding a second nesting threshold. [class: IMPLEMENTATION_REQUIRED]
- [x] Land the check warning-only: findings use `blocking: false` and cannot affect readiness. Promote only in a separate reviewed change after a true catch. [class: IMPLEMENTATION_REQUIRED]
- [x] Add a warning-only recommendation to select the existing `correctness-completeness` worker before launch when a focused round has a changed-code signal and the selected panel omits the quality lens; retain the current selection otherwise. Omitting the recommendation never blocks review launch or readiness. Add no worker role or review round. [class: IMPLEMENTATION_REQUIRED]
- [x] Add a warning-only admission entry and pre-registered removals row in `scripts/machinery_registry.json` for the check and selection advisory. Record the origin incident and separate expected frequency and false-positive cost (rates unmeasured; one nonblocking finding and one invocation if followed). [class: IMPLEMENTATION_REQUIRED]
- [x] Define true catches per mechanism: an adjudicated real issue found by the check, or an actionable issue found only by the recommended worker. At review on 2027-04-15, remove each mechanism without its own catch, update the active entry, and retain the removals row with its sunset witness. [class: IMPLEMENTATION_REQUIRED]
- [x] With a 30-line loaded limit and no other signal, expect a changed method with 24 counted lines to trigger the check and advisory, but one with 23 counted lines not to trigger either. Count using the active loaded guideline convention and record measured counts and outcomes. [class: REPOSITORY_TEST]
- [x] Given another qualifying signal and a focused panel that omits quality, expect the nonblocking advisory to recommend `correctness-completeness`; if declined, review launch and readiness still pass. If the quality worker is already selected, or no signal exists, expect no advisory and unchanged selection. Record the panel, signal, recommendation, and launch/readiness outcome for all scenarios. [class: REPOSITORY_TEST]
- [x] Commit: `review: retain readability quality lens for focused code changes` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Verify the rule against the witnessed cases and bounded audit

Files:
- `docs/history/backlog/2026-10-14-framework-callback-readability-guidance.md` *(read-only origin witness)*
- Phase 1 task 3 execution log, resolved through the session manifest (session-local; not a branch file)
- `projects/.ai-playbook/jvm_guidelines.md`
- `projects/.ai-playbook/java_guidelines.md`
- `projects/.ai-playbook/kotlin_guidelines.md`
- `agents/skills/review-agents/quality.md`
- `agents/skills/review-agents/review-panel-selection.md`
- `scripts/machinery_registry.json`
- `scripts/machinery_inventory.py` (validation only)

Task 3 evidence anchor: before Task 3 starts, assign its session-local log path to the manifest's Phase 1 task 3 row and create the log. Record the audit evidence there; tracked source anchors remain the files listed above.

- [x] Record that the profile-merge example (complexity 7, 65 counted lines, method-local record) meets a flagging condition; a short callback with one observable side effect and a method-local type each trigger the rule; and the simple pure callback remains inline. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a pure `shouldUseFallback(primary, secondary)` selector that branches on both inputs’ nullness, eligibility, and relative rank, expect a `blocking: false` quality finding for the nested decision path; given the one-line pure `value -> value.trim()` mapping, expect no finding. [class: REPOSITORY_TEST]
- [x] Verify from the in-repository origin witnesses that the named object owns its start time and atomic observation state, registration is separate, and the profile-merge extraction preserves its transaction boundary and uses ordered fact and seat locks. Per-registration isolation and the exact consumer lock sequence remain prose residuals. [class: IMPLEMENTATION_REQUIRED]
- [x] State which primary Spring API documentation supports any lifecycle claim and identify the source/version checked. [class: IMPLEMENTATION_REQUIRED]
- [x] Use the existing manifest `run_base` value for the pinned base and its `Phase 1 task 3` row as the execution record path. Record every Task 3 audit and command result in that task log, including that consumer adoption remains unverified because consumer source is absent from this repository. Keep the residual as prose, not an executable task. [class: IMPLEMENTATION_REQUIRED]
- [x] Verify the shared section number follows the JVM sequence, both language guides and review checks point to it, and no duplicated rule body was added. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the documented Java/Kotlin selection examples against temporary inputs and record inputs and outputs: all-null timestamps yield `null`; a null fact and candidate `t` yield `t + 1µs`; fact `t` with candidates `[t + 1µs, t - 1µs, null]` yields `t + 2µs`, proving maximum selection and the exact boundary increment. [class: IMPLEMENTATION_REQUIRED]
- [x] Record candidate-level maximum-expression verification as unverified: the origin backlog supplies the behavior witnesses but no source expression, and consumer source is absent from this repository. [class: IMPLEMENTATION_REQUIRED]
- [x] Inspect the five guidance and review files listed under Files for overlapping callback, local-type, or method-length guidance; for every overlap, identify the owning rule and whether the JVM section points to it or would duplicate it. [class: IMPLEMENTATION_REQUIRED]
- [x] Given a short side-effecting callback and an otherwise-simple pure callback, expect a `blocking: false` finding for the first and none for the second. Verify that removing the side-effect signal removes the finding. Record both outcomes. [class: REPOSITORY_TEST]
- [x] Apply the quality and panel-selection instructions to realistic samples: the witnessed method, method-local type, pure cognitively complex block, and one-line pure callback. Compare focused panels with and without a qualifying signal, including declining the advisory; record findings, recommendations, and launch/readiness outcomes. Run the Validation Commands block and record each command identity and result. [class: REPOSITORY_TEST]
- [x] Commit: none; the execution log is session-local and remains a closeout artifact. [class: IMPLEMENTATION_REQUIRED]

### Task 4: Keep session-bound validation in a runnable carrier

Files:
- `scripts/test_framework_callback_readability_session.sh`

Primary class anchors:
- `validate_session_evidence` in `scripts/test_framework_callback_readability_session.sh`

- [x] Move the manifest, run-base, execution-log, ancestry, and em-dash assertions into the test script. Accept the manifest path and read the run-base commit and Task 3 log path from it; allow explicit run-base and execution-log overrides only for refusal checks. Keep the hygiene scan and other independently runnable checks visible in the plan. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the test script with this session's manifest and verify it rejects an existing nonempty log path that differs from the manifest entry, and a valid non-ancestor run-base recorded in a disposable manifest copy, without changing repository state. [class: REPOSITORY_TEST]
- [x] Commit the carrier and plan update through the existing done boundary. [class: IMPLEMENTATION_REQUIRED]
## Disposition of migrated backlog items

The origin row `docs/history/backlog/2026-10-14-framework-callback-readability-guidance.md` is covered by this plan's shared JVM guidance and review-panel advisory. Consumer-project adoption remains an owner-side residual because no authorized consumer checkout is available.
