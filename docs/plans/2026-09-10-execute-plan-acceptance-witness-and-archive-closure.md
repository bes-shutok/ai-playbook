# Plan: Bind plan acceptance to executable evidence and gate archive closure

Backlog: `docs/history/backlog/2026-09-10-execute-plan-acceptance-witness-and-archive-closure.md` (scope of record)
Plan review: `docs/reviews/2026-09-10-plan-review-execute-plan-acceptance-witness-and-archive-closure-r*.md` (latest ready round)

## Terms

- **Acceptance criterion**: a plan statement of an observable outcome that must hold when the plan is done: an Evaluation Criteria **Done when** item or a task-level acceptance item.
- **Observable artifact**: the evidence an acceptance criterion names: a discriminating test assertion, a validation command, or a bounded repository-local structural check.
- **Discriminating assertion**: an assertion that fails when the required behavior is absent or wrong, not a test class or method name, a test count, a status code, or a green build.
- **Acceptance-to-evidence mapping (the mapping)**: the recorded list pairing every acceptance criterion with its observable artifact and the fresh verification output for that artifact.
- **Completion gate**: the Phase 2 boundary in execute-plan that blocks Phase 3 and archival until the mapping is complete and freshly verified.
- **Acceptance-evidence record**: the mapping as carried forward: the `manifest.md` section during execution and the `acceptance_evidence` field of the machine terminal receipt at completion. The machine gate verifies presence and shape only; completeness per criterion and discrimination are enforced by the Phase 2 prose gate and the review lenses.
- **Terminal receipt**: the `terminal_receipt` record inside `runtime_state.json` proving `workflow_state: complete` (schema owned by `agents/skills/execute-plan/runtime-contract.md`).

## Assumptions

- assume the machine gate binds at the driver terminal transition (`mark_terminal`); basis: the runtime contract names `terminal`/`mark_terminal` as the terminal operation and the terminal receipt as the machine completion proof (`agents/skills/execute-plan/runtime-contract.md` operation table), and backlog fix points 4 and 5 require the lifecycle transition itself to be machine-preventable.
- assume the record rides the existing terminal `--input` payload as `acceptance_evidence` (a list of criterion/artifact pairs); no new CLI operation; basis: the existing terminal payload shape in `scripts/execute_plan_runtime.py` (`archived_plan_path`, `last_commit_sha`, `phase5_checklist`).
- assume the completion receipt carries the mapping (machine `terminal_receipt` plus the human `manifest.md` section) and the review staging doc keeps its existing obligations; where a staging doc already carries a mutator failure-mode matrix or Witness ledger, those rows satisfy the mapping for the criteria they cover and the new lens reports gaps only for uncovered criteria; basis: the backlog acceptance line says "the review staging or completion receipt records the acceptance-to-evidence mapping", and adding a required review-staging schema field would expand scope beyond the backlog Location list.
- assume the activation fixture copy under `scripts/testdata/execute-plan/activation/loaded/` is a probe fixture that is NOT byte-synced with the source driver; only its own probes must stay green; basis: the `activation.json` role map plus the absence of any source-versus-fixture byte comparison in the test suites (grepped 2026-09-10).
- assume `scripts/plan_readiness.py` gains no mechanical acceptance-evidence check in this plan; authoring-time enforcement is the review-plan audit plus the executor gates; basis: the backlog Location names the four skill surfaces and "runtime or validator self-tests", not the readiness validator.
- assume "blocks Phase 3 and archival" maps to prose hard gates in execute-plan Phase 2 and Phase 4, while the machine gate prevents `workflow_state: complete` without the record; basis: backlog fix points 2 and 4 mapped onto the existing phase structure.

Decision points requiring a grill: none remain.

## Gist & Examples

What changes: plan acceptance criteria become executable obligations at three layers. Authoring (plans skill) requires every acceptance criterion to name an observable artifact. Execution (execute-plan skill) gains a Phase 2 completion gate that enumerates the criteria, verifies each artifact against the current tree with fresh output, and records the acceptance-evidence record; the Phase 4 archive move and the Phase 5 terminal receipt consume that record. Machine (runtime driver) refuses the terminal transition when the record is missing or malformed. Review (review-plan at authoring time; testing and correctness lenses at execution time) inspects the mapping instead of trusting a green build.

Why: an execute-plan run can produce a blocking-clean code review while a plan acceptance criterion has no proof that its test exists, runs, and discriminates the required behavior. The document-lifecycle work already defines how an eligible plan archives; this plan adds the preceding eligibility proof so the archive mechanics cannot close a plan whose implementation evidence is incomplete.

**Before (today)**: every task checkbox is `[x]`; Phase 2 re-runs the plan Validation Commands and they pass; a Done-when item saying "malformed rows are rejected with a per-row error" has no test that discriminates it, and no step notices. Phase 3 reviews the code diff and finds no blocking issue because the diff looks complete. Phase 4 archives the plan; the unproven criterion survives closure and the lifecycle state says complete.

**After (this plan)**: Phase 2 runs the completion gate after validation: it enumerates every acceptance criterion, names each one's artifact, and verifies it with fresh output, recording the acceptance-evidence record in `manifest.md`. The criterion above must name, for example, a test whose assertion fails when per-row error attribution disappears; if it names nothing, or the named artifact is missing or non-discriminating, the gate fails and the run returns to a fix iteration: Phase 3, the Phase 4 archive move, and tmp cleanup are unreachable. At the end, a driver terminal call without a complete `acceptance_evidence` record returns a blocked `done-pending` outcome with `workflow_state` still active, so no run can reach `workflow_state: complete` without the record. The machine gate is a structural floor (presence and shape of the record); completeness per criterion and discrimination are enforced by the Phase 2 prose gate and the review lenses.

Edge cases: a criterion proven by a validation command is satisfied by item 1's fresh Phase 2 validation output, which is recorded as its receipt (no second identical run); a criterion proven by a bounded structural check is verified by re-running the check; a criterion whose named test exists but asserts nothing discriminating fails the gate (the assertion, not the test name, is the evidence).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the driver blocks a missing, empty, or malformed record and accepts a complete one, proven by named hermetic tests (Task 1); the prose gates make the unchecked-criterion path unreachable in the same order (Phase 2 gate before Phase 3, precondition before the Phase 4 move, record required at the terminal receipt).
- completeness: every backlog Acceptance bullet maps to a task artifact (table below), with each artifact proving exactly the half it can prove.
- maintainability: the contract is stated once per layer with pointers between peers (plans owns the authoring rule and the artifact taxonomy, and its not-evidence list is the superset peers point at; execute-plan owns the executor gates; runtime-contract owns the machine schema); no duplicated normative prose.
- tool-neutrality: the shared skill bodies stay runtime-neutral (enforced by the existing `test_shared_skill_bodies_remain_runtime_neutral`, which the suite runs on every change).
- hermeticity: new driver tests run in temp directories under the suite's existing ambient-input pinning; no network, no cwd dependence, no real plan files; the one deliberate exception is the prose-pinning test, which read-only opens real repository skill files resolved from the test module location.

**Backlog acceptance coverage:**

| Backlog acceptance bullet | Proving artifact in this plan |
|---|---|
| Unchecked or evidence-free criterion fails the gate, plan stays on the active path | `test_terminal_requires_acceptance_evidence` proves the evidence-free half (blocked, workflow_state active); the unchecked-criterion half is enforced by the Phase 2 item 4 prose gate, since the machine gate verifies record presence and shape only |
| Complete plan passes only with present, discriminating artifacts | `test_terminal_receipt_carries_acceptance_evidence` plus Phase 2 item 3 fresh-output verification (discrimination itself is review-enforced per the structural-floor bound) |
| Receipt records the acceptance-to-evidence mapping, not a test count | `terminal_receipt.acceptance_evidence` pairs; `manifest.md` Acceptance evidence section with the prescribed per-criterion line shape (Phase 2 item 3) |
| Completion gate invokes existing archive checks only after the contract passes | Phase 4 acceptance-evidence precondition preceding the archive completeness checks |
| Success path records final validation output and the mapping before archive and cleanup gates | Phase 2 record plus Phase 5 checklist item 6 and terminal receipt field |
| Tool-agnostic, no private names or machine paths | runtime-neutral suite gate; hygiene scan in Validation Commands |

**Done when:**
- `python3 scripts/test_execute_plan_runtime.py` exits 0 including the new acceptance-evidence tests and the prose-pinning test.
- `python3 scripts/test_execute_plan_runtime_codex.py`, `python3 scripts/test_runtime_capabilities.py`, and `python3 scripts/execute_plan_runtime.py --selftest` exit 0.
- Every Validation Commands span probe finds its prescribed obligation (each probe lists the obligation it proves).
- `bash scripts/check-no-em-dash.sh` and `bash scripts/scan-public-hygiene.sh` exit 0 over the changed files.

**Ship when:**
- None; this is a repository-local workflow contract change with no deployment surface. Done is complete when the change is merged per the repository's normal workflow.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` *(Phase 2, Phase 4, Phase 5 Terminal receipt paragraph and the Terminal-response gate sentence in Runtime-neutral execution contract, success checklist, Integration Points "Consumes plans"; all other sections frozen)*
- `agents/skills/execute-plan/runtime-contract.md` *(the paragraph inserted directly after the CLI operation table in Driver entrypoint and reload contract; all other content frozen)*
- `agents/skills/plans/SKILL.md` *(Evaluation Criteria rule, structural failure-mode list, Integration Points "With execute-plan"; all other sections frozen)*
- `agents/skills/review-plan/SKILL.md` *(Step 1 audit item; all other sections frozen)*
- `agents/skills/doing-code-review/SKILL.md` *(Step 3 worker-instruction item 12 extension; all other sections frozen)*
- `agents/skills/review-agents/testing.md` *(new Acceptance-Evidence Mapping section; all other sections frozen)*
- `scripts/execute_plan_runtime.py` *(acceptance-evidence helper, `mark_terminal`, `terminal_result`, CLI terminal dispatch, module selftest; all other methods frozen)*

**Tests:**
- `scripts/test_execute_plan_runtime.py` *(the new acceptance-evidence and prose-pinning tests plus the updated call sites named in Tasks 1 and 2; all other tests frozen)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime_codex.py` and `scripts/test_execute_plan_runtime_codex.py`; reason: the adapter owns worker launch/wait/resume and never calls the terminal transition (verified by symbol grep); its suite still runs as a regression guard.
- `scripts/testdata/execute-plan/activation/**`; reason: probe fixture loaded from its own copies; no source byte-sync obligation; its probes stay green via the codex suite.
- `scripts/plan_readiness.py`; reason: mechanical authoring-time enforcement is deferred (Assumptions); review-plan carries the authoring check.
- `README.md` and `docs/maintenance/glossary.md`; reason: no skill-catalog or vocabulary-surface change; terms live in this plan's Terms section and the edited skill surfaces.
- `agents/skills/review-agents/quality.md` and other lens catalogs; reason: the backlog Location names testing.md and doing-code-review for the review-side change.

## Design Invariants (CR Guard)

- The completion gate precedes the lifecycle transition and never re-implements or weakens the existing archive completeness checks or the ownership-registry row append; those stay the source of truth for the transition itself (lineage: `docs/history/backlog/completed/2026-09-08-document-ownership-and-archive-lifecycle.md`, ADR-0003 grill decisions).
- Fail-closed semantics: a missing or malformed acceptance-evidence record blocks the terminal transition (`done-pending`, `preserve-and-reconcile`); no warning-only degradation and no bypass flag.
- The driver owns the machine transition; `manifest.md` stays the human audit mirror and can never authorize a transition by itself (runtime contract ownership rule).
- Shared skill bodies stay runtime-neutral and tool-agnostic; prescribed snippets for the four scanned shared files (`execute-plan/SKILL.md`, `subagent-prompts.md`, `agent-logs.md`, `plans/SKILL.md`) carry no tool names or host-specific flags, enforced by `test_shared_skill_bodies_remain_runtime_neutral`; the runtime-contract paragraph and the review-surface snippets are kept neutral by authoring review (runtime-contract.md documents runtime specifics by design and is outside that scan).

## Validation Commands

```bash
set -e
REPO="$(git rev-parse --show-toplevel)"
cd "$REPO"
python3 scripts/test_execute_plan_runtime.py
python3 scripts/test_execute_plan_runtime_codex.py
python3 scripts/test_runtime_capabilities.py
python3 scripts/execute_plan_runtime.py --selftest
grep -q "Run the completion gate: enumerate every acceptance criterion" agents/skills/execute-plan/SKILL.md || { echo "missing: Phase 2 completion gate"; exit 1; }
grep -q "Phase 3 and Phase 4 archive stay blocked until the record is complete" agents/skills/execute-plan/SKILL.md || { echo "missing: Phase 2 block rule"; exit 1; }
grep -q "archive only after the Phase 2 completion gate passed" agents/skills/execute-plan/SKILL.md || { echo "missing: Phase 4 acceptance-evidence precondition"; exit 1; }
grep -q "the Phase 5 success checklist, and the acceptance-evidence record" agents/skills/execute-plan/SKILL.md || { echo "missing: Phase 5 terminal record argument"; exit 1; }
grep -q "the Phase 5 checklist, and the acceptance-evidence record" agents/skills/execute-plan/SKILL.md || { echo "missing: Terminal-response gate record argument"; exit 1; }
grep -q "consume the completion-evidence contract" agents/skills/execute-plan/SKILL.md || { echo "missing: execute-plan integration line"; exit 1; }
grep -q "a test count, a status code, a checkbox, or a green-build claim is not evidence" agents/skills/plans/SKILL.md || { echo "missing: plans observable-artifact rule"; exit 1; }
grep -q "Acceptance-evidence binding" agents/skills/plans/SKILL.md || { echo "missing: plans structural check"; exit 1; }
grep -q "terminal receipt consume the completion-evidence contract" agents/skills/plans/SKILL.md || { echo "missing: plans integration line"; exit 1; }
grep -q "Acceptance-evidence audit" agents/skills/review-plan/SKILL.md || { echo "missing: review-plan audit item"; exit 1; }
grep -q "inspect the acceptance-to-evidence mapping" agents/skills/doing-code-review/SKILL.md || { echo "missing: doing-code-review lens rule"; exit 1; }
grep -q "Acceptance-Evidence Mapping (plan-closing diffs)" agents/skills/review-agents/testing.md || { echo "missing: testing.md mapping section"; exit 1; }
grep -q "testing#acceptance-evidence-gap" agents/skills/review-agents/testing.md || { echo "missing: testing.md pattern id"; exit 1; }
grep -q "requires the acceptance-evidence record" agents/skills/execute-plan/runtime-contract.md || { echo "missing: runtime-contract terminal rule"; exit 1; }
CHECK_NO_EM_DASH_ALL=1 bash scripts/check-no-em-dash.sh file agents/skills/execute-plan/SKILL.md agents/skills/execute-plan/runtime-contract.md agents/skills/plans/SKILL.md agents/skills/review-plan/SKILL.md agents/skills/doing-code-review/SKILL.md agents/skills/review-agents/testing.md scripts/execute_plan_runtime.py scripts/test_execute_plan_runtime.py
bash scripts/scan-public-hygiene.sh
```

Scope notes: the four suite commands plus the module selftest prove the driver behavior and every updated call site behaviorally (a success-path call site left unupdated fails its suite against the new gate); each grep proves exactly one prescribed prose obligation from the task snippets below (the two terminal-argument probes are intentionally distinct: the Phase 5 paragraph uses "the Phase 5 success checklist", the Terminal-response gate sentence uses "the Phase 5 checklist"); the last two commands are the repository hygiene gates over the changed files. Task-scoped interim runs execute only the subset that exists at that stage, plus the suites.

### Task 1: Gate the runtime terminal transition on acceptance evidence

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_runtime.py`
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/SKILL.md` *(Phase 5 Terminal receipt paragraph and the Terminal-response gate sentence only)*

The driver change and the prose that drives the new argument land in this one commit on purpose: a driver gate without the orchestrator prose would lock any run reaching Phase 5 into a blocked loop until the next commit. Residual window: the Phase 2 completion gate that produces the record lands in Task 2, so a run reaching Phase 5 inside this window constructs the record per the runtime-contract paragraph (one criterion and artifact pair per acceptance criterion) and re-issues the terminal call; a run of a plan whose criteria name no observable artifacts stops and reports a hard gate instead of improvising pairs.

- [ ] `ExecutePlanRuntimeTest#test_terminal_requires_acceptance_evidence`; given a manifest whose tasks are all complete and a `mark_terminal` call with valid `archived_plan_path`, `last_commit_sha`, and `phase5_checklist` but no `acceptance_evidence`, expects a blocked `done-pending` outcome whose evidence names acceptance evidence, `workflow_state` still `active` in `runtime_state.json`, and `terminal_result()` returning `None`
- [ ] `ExecutePlanRuntimeTest#test_terminal_rejects_malformed_acceptance_evidence`; given `acceptance_evidence` that is an empty list, a non-list, a pair missing `criterion`, and a pair with a blank `artifact` (one case each), expects a blocked `done-pending` outcome every time and `workflow_state` still `active`
- [ ] `ExecutePlanRuntimeTest#test_terminal_receipt_carries_acceptance_evidence`; given a complete manifest and `acceptance_evidence` of one `{"criterion": ..., "artifact": ...}` pair, expects a success outcome, `terminal_receipt.acceptance_evidence` equal to the normalized pairs, and `terminal_result()` returning `acceptance_evidence` alongside `workflow_state: complete`
- [ ] `ExecutePlanRuntimeTest#test_terminal_result_over_legacy_complete_manifest`; given a manifest hand-written complete with a `terminal_receipt` that lacks `acceptance_evidence`, expects `terminal_result()` returning `None`; after `mark_terminal` is re-issued with the full record (idempotent overwrite), expects a success outcome and `terminal_result()` returning the complete receipt
- [ ] Update the success-path call sites for the required record: the module selftest call and the CLI terminal dispatch in `scripts/execute_plan_runtime.py`; in `scripts/test_execute_plan_runtime.py` the `mark_terminal` call in `test_driver_entrypoint_owns_transitions_across_reload`, the second (success) call in `test_active_manifest_suppresses_terminal_result`, and the `cli("terminal", ...)` payload in `test_cli_drives_claim_checkpoint_done_and_terminal` (add `acceptance_evidence` to the `--input` JSON). The two no-args blocked-path calls (the first call in `test_active_manifest_suppresses_terminal_result` and the call in the `conversational-permission-loop` replay handler) stay unchanged: they are blocked by the other required fields before evidence is checked
- [ ] Run → expect RED: `python3 scripts/test_execute_plan_runtime.py` fails all four new tests plus the two direct keyword call-site tests in `test_driver_entrypoint_owns_transitions_across_reload` and `test_active_manifest_suppresses_terminal_result` (`TypeError` on the unexpected keyword, plus blocked-versus-success and missing-receipt assertion failures); the CLI payload test in `test_cli_drives_claim_checkpoint_done_and_terminal` stays green at RED because today's dispatch drops unknown payload keys, and its discriminating power begins once the dispatch forwards the field; the remaining tests stay green
- [ ] Implement in `scripts/execute_plan_runtime.py`: one module-level validator that accepts only a non-empty list of mappings each carrying a criterion and an artifact that are non-blank after stripping whitespace; normalization keeps exactly the `criterion` and `artifact` keys per pair (extra keys are dropped); both `mark_terminal` and `terminal_result` call that same validator (the read-time re-check is deliberate tamper detection between write and read); `mark_terminal` returns the blocked `done-pending` outcome with evidence `acceptance evidence is required before terminal state` when validation fails, stores the normalized pairs in `terminal_receipt.acceptance_evidence`, and on a manifest whose `workflow_state` is already complete appends a `terminal-reissue` history event so an overwrite is auditable; `terminal_result` returns the pairs on success; the CLI terminal dispatch passes `payload.get("acceptance_evidence")`; the module selftest passes a complete record
- [ ] Document in `agents/skills/execute-plan/runtime-contract.md`, directly after the CLI operation table: one short paragraph stating that the terminal operation requires the acceptance-evidence record (one criterion and artifact pair per plan acceptance criterion), that the driver keeps `workflow_state` active and returns a blocked `done-pending` result when the record is missing or incomplete, that the machine gate verifies presence and shape only (completeness per criterion and discrimination are enforced by the Phase 2 prose gate and the review lenses), that a complete manifest whose receipt predates the record returns no receipt until the terminal operation is re-issued with the full record, and that a re-issue on an already-complete manifest appends a `terminal-reissue` history event and a recovery record reconstructed for a legacy run is retroactive and not machine-verified
- [ ] In `agents/skills/execute-plan/SKILL.md` Phase 5 Terminal receipt paragraph: change the call to pass the record, namely "with the archived-plan path, the last commit SHA, the Phase 5 success checklist, and the acceptance-evidence record"; add the sentence "The driver returns no terminal receipt while the acceptance-evidence record is missing or incomplete."; and extend the mirrored fields list with the acceptance-evidence record
- [ ] In `agents/skills/execute-plan/SKILL.md` Runtime-neutral execution contract, Terminal-response gate paragraph: amend the terminal-call field list to "with the archived plan path, the last commit SHA, the Phase 5 checklist, and the acceptance-evidence record"
- [ ] Run → expect GREEN: the four suite/selftest commands in Validation Commands exit 0 (span probes not yet all applicable at this stage)
- [ ] Commit: `feat: gate execute-plan terminal state on acceptance evidence`

### Task 2: execute-plan completion and archive gates

Files:
- `agents/skills/execute-plan/SKILL.md` *(Phase 2, Phase 4, success checklist, Integration Points)*
- `scripts/test_execute_plan_runtime.py` *(one new prose-pinning test)*

- [ ] In `## Phase 2: Plan Completion`, replace the three-item numbered list with:

```markdown
1. Run the plan's `## Validation Commands` once more from the main agent (fresh output).
2. If validation fails, treat as a new fix iteration (implement sub-agent on the failing scope) before entering Phase 3.
3. Run the completion gate: enumerate every acceptance criterion in the plan (the Evaluation Criteria **Done when** items plus task-level acceptance items). For each criterion, verify its named observable artifact against the current tree with fresh output, as the completion-evidence contract in the plans skill defines: exercise each artifact as its kind requires (run the named validation command, or run the named test and confirm the assertion that discriminates the criterion, or re-run the named structural check). A criterion whose artifact is a Validation Command is satisfied by item 1's fresh output; record that output as the receipt instead of re-running it. Record the acceptance-evidence record (one line per criterion: criterion, artifact, command or test identity, exit status, one-line output receipt) under an `## Acceptance evidence` heading in `manifest.md`.
4. If any criterion names no artifact, or its artifact is missing, unchecked, or non-discriminating, the completion gate fails: treat it as a new fix iteration. Phase 3 and Phase 4 archive stay blocked until the record is complete. Never mark a criterion complete without its artifact's fresh output. For a plan authored before the authoring-side binding whose criteria name no artifacts, stop and route the plan through the plans skill and a fresh plan review to retrofit artifacts; do not burn fix iterations on a gap that lives in the plan text. Treat that stop as a user-paused hard gate: record it in `manifest.md`, leave the machine manifest preserved, make no further driver calls, and resume only after the retrofit via the normal resume path against the re-reviewed plan.
5. If the completion gate passes, **proceed to Phase 3 immediately**; do not ask whether to start review.
```

- [ ] In `## Phase 4: Archive Plan`, insert directly before the `git mv` block:

```markdown
**Acceptance-evidence precondition (required):** archive only after the Phase 2 completion gate passed and the acceptance-evidence record in `manifest.md` is complete. If the record is missing or any criterion in it is open, stop and return to Phase 2; do not move the plan. The archive completeness checks below remain the source of truth for the transition itself.
```

- [ ] In `## Phase 5`, success checklist: add item "6. The acceptance-evidence record is complete (Phase 2 completion gate passed)."
- [ ] In `## Integration Points`, subsection "Consumes `plans` skill": append the sentence "Phase 2's completion gate, the Phase 4 archive precondition, and the Phase 5 terminal receipt consume the completion-evidence contract that `plans` owns (acceptance criteria bind to observable artifacts)."
- [ ] Add `ExecutePlanRuntimeTest#test_completion_gate_prose_is_pinned`; given the repository skill files resolved from the test module location (`Path(__file__).resolve().parents[1]`, matching the existing runtime-neutral scan), expects each pinned phrase to be present exactly in its owning file, and a missing or unreadable file fails the test (no skip): in `agents/skills/execute-plan/SKILL.md` the phrases "Run the completion gate: enumerate every acceptance criterion", "archive only after the Phase 2 completion gate passed", "the Phase 5 success checklist, and the acceptance-evidence record", and "the Phase 5 checklist, and the acceptance-evidence record"; in `agents/skills/execute-plan/runtime-contract.md` the phrase "requires the acceptance-evidence record", so post-archive paraphrase drift fails a suite instead of nothing
- [ ] Run → expect GREEN: the execute-plan span probes from Validation Commands, and all four suite/selftest commands still exit 0 (the runtime-neutral scan covers the edited skill files; the new prose-pinning test passes)
- [ ] Commit: `docs: gate execute-plan phases on acceptance evidence`

### Task 3: Authoring-side binding in plans and review-plan

Files:
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

- [ ] In `plans` Universal Patterns, extend the "Evaluation Criteria section" bullet with: "Every acceptance criterion (Done when items and task-level acceptance items) must name its observable artifact: a discriminating test assertion, a validation command, or a bounded repository-local structural check. A test class or method name, a test count, a status code, a checkbox, or a green-build claim is not evidence." This sentence is the owner of the artifact taxonomy and carries the full not-evidence list; peers point at it and never carry their own enumeration.
- [ ] In `plans` "Then verify these structural failure modes" list, add: "- **Acceptance-evidence binding:** every acceptance criterion names an observable artifact; flag criteria whose only proof is excluded by the not-evidence rule in Universal Patterns."
- [ ] In `plans` Integration Points "With `execute-plan` skill", append: "The executor completion gate and terminal receipt consume the completion-evidence contract that `plans` owns: acceptance criteria bind to observable artifacts per the Evaluation Criteria rules, and the artifact taxonomy is owned here."
- [ ] In `review-plan` Step 1, add item: "8. **Acceptance-evidence audit**: for every acceptance criterion in the plan (Evaluation Criteria Done when items and task-level acceptance items), verify it names an observable artifact per the completion-evidence contract owned by the plans skill, and that each artifact is exercised by the plan's Validation Commands or a named test; flag criteria whose proof the plans contract excludes for the correctness-completeness worker."
- [ ] Run → expect GREEN: the plans span probes and the review-plan span probe from Validation Commands, and all four suite/selftest commands still exit 0
- [ ] Commit: `docs: bind plan acceptance criteria to observable artifacts`

### Task 4: Review-lens inspection for plan-closing diffs

Files:
- `agents/skills/doing-code-review/SKILL.md`
- `agents/skills/review-agents/testing.md`

- [ ] In `doing-code-review` Step 3 worker-instruction item 12 (Structured evidence requirements), append: "When the reviewed diff closes an implementation plan, testing and correctness-completeness workers must additionally inspect the acceptance-to-evidence mapping (each plan acceptance criterion against the changed tests and commands) per `review-agents/testing.md` Acceptance-Evidence Mapping; a green build is not proof of complete acceptance coverage. Rows of the staging doc's mutator failure-mode matrix or Witness ledger satisfy the mapping for the criteria they cover."
- [ ] In `review-agents/testing.md`, insert a new section after "Coverage Claim Audit":

```markdown
## Acceptance-Evidence Mapping (plan-closing diffs)

When the reviewed diff closes an implementation plan (execute-plan Phase 3, review-loop, or a PR review of a plan branch):

1. Read the plan's acceptance criteria (Evaluation Criteria **Done when** items and task-level acceptance items). For each, locate the observable artifact in the diff, as defined by the completion-evidence contract in the plans skill.
2. The plans contract's not-evidence list applies: confirm the assertion would fail if the criterion's behavior regressed, including the negative path and at least one boundary state where applicable.
3. A criterion with no artifact in the diff is a finding: `testing#acceptance-evidence-gap`. Default Medium; blocking when the criterion is the plan's primary success criterion or guards a hard gate.
4. Findings about the mapping state the criterion, the missing or non-discriminating artifact, and the concrete assertion or command that would prove it; for in-flight reviews, check that any recorded acceptance-evidence receipt (staging doc or session manifest) names the concrete command or test it claims, not a batch summary (the archived machine receipt is presence-and-shape only).
5. For diffs that also carry a mutator failure-mode matrix or Witness ledger (per execute-plan Phase 3 and review-staging), those rows satisfy this mapping for the criteria they cover; report gaps only for acceptance criteria no row covers.
```

- [ ] Run → expect GREEN: the doing-code-review span probe and the two testing.md span probes from Validation Commands, and all four suite/selftest commands still exit 0
- [ ] Commit: `docs: inspect acceptance-evidence mapping in review lenses`

### Task 5: Final verification

Files: none new (verification only).

- [ ] Run the full Validation Commands block from the repository root; every command exits 0
- [ ] Confirm the two-tier Review Scope still matches the changed file set (`git status --short` shows only the files listed above)
