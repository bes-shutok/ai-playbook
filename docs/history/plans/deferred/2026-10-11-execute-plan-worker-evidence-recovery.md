# Plan: execute-plan-worker-evidence-recovery

- Date: 2026-10-11
- Execution budget: 2h (per directive D-8 this declares 2 full-panel review rounds)
- Change class: verifier-seeding correction inside the existing discovery path, the launch contract's criterion-id publication, and the matching skill-text surfaces; no new gate, receipt kind, driver operation, or recovery route

## Terms

- Verification contract: the per-task `verification_commands` list the manifest seed writes, each command carrying `id`, `argv`, `criteria`, and `selected_tests` (`_discovery_verification_commands`, `scripts/execute_plan_runtime.py`).
- Witness mapping *(new)*: the seed-time rule that a command claims exactly the criteria whose own text names the command's selected target (test module or path), derived from the task's `required_criteria` strings; the mapping is total - every worker-owned criterion must name at least one seeded target, and the seed's consumers enforce that totality unchanged (the digest's union-equality check at create, load, refresh, and recovery, and the done boundary's subset check). A criterion no command can prove is expressed as a parent-owned `Commit:` box, which never seeds a worker criterion and whose receipt route is the parent's existing verification operation - the entry's parent-verification arm, honored structurally rather than by the mapping.
- Unmapped-criterion refusal: what happens when a criterion's text names no seeded target: the unchanged `evidence_contract_digest` union-equality check raises `required criteria and command criteria must match` at create, refresh, and recovery, refusing the contract before any bytes are written. The check is not edited; it is the enforcement that makes plan authors write path-citing criteria - the incident's actual lesson. One earlier refusal exists for the fully-unmapped shape: a task whose every criterion maps nowhere seeds no command at all and discovery's standing empty-contract check refuses first, so the digest refusal is the mixed-shape arm of the same fail-closed posture.
- Generic keyword probe: the current content-witness command whose witness token comes from the task's first behavior token (`tokens[0]`) or, failing that, the first criterion's lowered text - the single-token substring shape that claimed all five criteria in the witnessed incident.
- Criterion-id map: the stable `c001...` identifiers `evidence_criterion_ids` builds from the sorted task criteria (`scripts/runtime_capabilities.py`), the ids the launch envelope (once published, see Task 2), the worker's coverage field, and the receipt pair share.

## Why

Manifest seeding generated one verifier per selected file whose body tested almost nothing - `ast.parse` on anchors and a single-token substring probe on the rest - while every command carried the task's full criteria list, so one passing probe stamped complete criterion coverage: three `python3 -c` commands checking only for the substring `review` claimed criteria c001-c005 without testing any of them (docs/history/backlog/2026-10-10-execute-plan-discovered-verifier-quality.md). The same run's worker returned implementation prose without the criterion-coverage field, the driver refused `malformed-result` twice, and the bounded corrected-submission route exhausted, stranding verified work for operator adjudication (docs/history/backlog/2026-10-10-execute-plan-worker-evidence-envelope.md). The root defect is the seed's claim semantics, not a missing recovery path: the run recovered through the existing operations at generation 9.

## Gist & Examples

The seed maps each command to the subset of criteria whose text names the command's selected target: a unittest discovery command over `test_worker_registry.py` claims the criteria that cite that module; a content-witness probe over `docs/x.md` claims the criteria that cite `docs/x.md`; an `ast.parse` anchor command claims the criteria that cite its anchor path. The mapping is total under the unchanged enforcement, split by shape: a task whose every criterion names no seeded target seeds no command and refuses at discovery's standing empty-contract check, while a mixed task (at least one command still seeds) refuses at create with the unchanged union-equality digest check - either way the contract never writes, and the teaching force is the same: checkbox criteria must cite the witnesses that prove them. The keyword probe loses both unrelated-token arms: its witness token is drawn from its own mapped criteria's text, and a selected path with no mapped criterion seeds no witness command at all, and the same rule covers the other command kinds: a test module or anchor no criterion cites seeds no command, because an unclaimed run adds nothing honest to the contract. A named residual of citation semantics: a criterion whose text names several seeded targets is claimed by each of them, and the done boundary accepts a criterion on any single claiming command's passing receipt, so incidental citations stay the plan author's honesty obligation - the same surface the refusal teaches. Example: in the incident shape, the three `review` probes claim zero criteria, no command seeds at all, discovery's empty-contract check refuses, and the plan author rewrites the five checkbox criteria to cite their actual witnesses - the false complete pass becomes an unrepresentable contract rather than a caught one. The worker prompt's coverage bullets (single-task and batch) name the criterion-id map as the concrete field, and the launch contract now publishes that map, so the initial return carries per-criterion coverage keyed to ids the worker can actually see.

## Outcome

The discovered verification contract claims only criteria whose text names its target; the false complete pass is unrepresentable at seed time, and the worker's first return carries the coverage field the verifier demands, keyed to published ids. Gate delta: no new gate, ledger, receipt, driver operation, or recovery route - the mapping is a predicate inside the existing `_discovery_verification_commands` seed; the digest's union-equality check (`scripts/runtime_capabilities.py`) and the done boundary's subset check (`validate_adapter_result`) are byte-unchanged and are the totality enforcement; the refused return keeps its existing `malformed-result` route and corrected-submission bound. No machinery admission row is owed: the change replaces defective seed behavior (the incident class) and adds no enforceable surface. Origin dispositions: the discovered-verifier-quality and worker-evidence-envelope rows close as covered by this landing; the adjudication-recovery row closes as unnecessary per its own Expected arm (the run recovered through existing operations at generation 9; no new recovery route exists to adjudicate). The mapping is a discovery-seed property: declared contracts created without `--plan` keep the caller's honesty obligation, unchanged by this plan.

## Assumptions

- The two standing total-coverage invariants are preserved and do the refusal work: `evidence_contract_digest` raises on any union mismatch between required criteria and the union of command criteria (`scripts/runtime_capabilities.py`, called at create, load, refresh, and recovery), and `validate_adapter_result` refuses success unless the required criteria are a subset of the receipts' covered criteria (`scripts/execute_plan_runtime.py`). Because the mapping is total-or-refused, both checks pass exactly when every criterion is claimed by the commands that honestly witness it. Basis: the verified spans and the r1 panel's empirical probe (a faithful mapped seed over the unchanged machinery refuses unmapped-criteria contracts at seed - discovery's empty-contract check for the fully-unmapped shape, the digest at create for the mixed shape).
- The discovered-scope refresh already recomputes `criteria`, `verification_commands`, criteria-map entries, and `evidence_contract_digest` in one locked write, so re-seeded contracts re-digest with no new migration path; the refresh's own union check refuses a refresh that would unmapped-ify a criterion, keeping stored contracts loadable. Basis: the refresh spans in `scripts/execute_plan_runtime.py`.
- Publishing the criterion-id map in the launch contract is additive: `_worker_role_contract` already carries the task's raw criteria text and the launch prompt serializes it verbatim, so one id-map field reaches the worker without any new transport. Basis: the contract fields and serialization spans in `scripts/execute_plan_runtime.py`.

Decision points requiring a grill: none remain.

## Standing constraints

- No new gate, validator, receipt kind, driver operation, recovery route, or review step; `evidence_contract_digest` and `validate_adapter_result` are byte-unchanged; the corrected-submission bound and both recovery events stay byte-unchanged.
- The refusal at `required verification criteria missing` keeps its exact literal and recovery tail.
- Never push to origin; hygiene scan exit 0 before every commit; no em dashes; repo-relative paths only in landed text.

## Evaluation Criteria

1. A task whose criteria all cite seeded targets seeds commands claiming exactly their cited criteria; no command claims a criterion whose text names another path.
2. A selected documentation path whose criterion cites it seeds a witness probe claiming exactly that criterion, with the witness token drawn from that criterion's own text and no behavior-token fallback in the probe argv.
3. A task containing a criterion whose text names no seeded target refuses at seed - at discovery's empty-contract check when no command seeds, otherwise at create with the unchanged union-equality refusal; no fixture or code path narrows either check.
4. Both coverage bullets (single-task and batch member) name the criterion-id map identically, and the launch contract publishes the id map for the task.
5. The regression example fails against the old seed (a probe claiming unmapped criteria, a behavior-token probe argv) and passes against the new one; the runtime suite stays green.

## Review Scope

- Category: guard-bearing driver code, its fixtures, and the skill-text surfaces they bind: scripts/execute_plan_runtime.py, scripts/test_execute_plan_runtime.py, scripts/runtime_capabilities.py, agents/skills/execute-plan/subagent-prompts.md, agents/skills/execute-plan/runtime-contract.md. Single category (execute-plan runtime contract surfaces); every Files: path of every task is inventoried here.

## Validation Commands

- `python3 scripts/test_execute_plan_runtime.py` (unittest OK; suites require a Python 3.11+ interpreter for `tomllib`)
- `python3 scripts/test_execute_plan_runtime_codex.py` (unittest OK; same interpreter note)
- `python3 scripts/test_codex_execute_plan_hooks.py` (unittest OK; same interpreter note)
- `grep -c 'criteria\[0\]' scripts/execute_plan_runtime.py` (expect stdout `0`; grep exits 1 on zero matches - inverted-exit semantics)
- `! grep -q 'Plan-criterion coverage: which task criteria each changed path satisfies' agents/skills/execute-plan/subagent-prompts.md` (both coverage bullets reworded; inverted-exit assertion)
- `bash scripts/check-no-em-dash.sh file docs/history/plans/2026-10-11-execute-plan-worker-evidence-recovery.md`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh` (exit 0)

## Task 1: witness-mapped verifier seeding and the regression example

Files: scripts/execute_plan_runtime.py, scripts/test_execute_plan_runtime.py

Anchors:

- `_discovery_verification_commands` in `scripts/execute_plan_runtime.py`
- `evidence_contract_digest` in `scripts/runtime_capabilities.py`
- `ExecutePlanRuntimeTest` in `scripts/test_execute_plan_runtime.py`

- * [ ] (code): In `_discovery_verification_commands`, replace every command's full-list `criteria` with the witness mapping: the subset of the task's criteria whose text names that command's selected target (substring match on the target path or module name as it appears in the criterion), the unittest, anchor, and witness commands included; the docstring's full-list matched-pair sentence is reworded to the mapped-subset shape with the digest as the totality enforcement.
- * [ ] (code): Remove both unrelated-token arms of the witness probe: a content-witness command seeds only when at least one criterion maps to its path, and its witness token is the first whitespace token of the alphabetically-first mapped criterion's text (the id order `evidence_criterion_ids` assigns) that passes the discovery stopword filter with a casefolded comparison and a minimum length of four (mirroring `_DISCOVERY_STOPWORDS`, whose filter provably excludes articles and short stopwords from the behavior-token set - first-non-behavior-token would select `The` and recreate the content-free probe), falling back to the criterion's first token casefolded; the probe compares casefolded file text against the casefolded token; a selected path with no mapped criterion seeds no command, leaving the seed refusal to the two unchanged checks (discovery's empty-contract check when nothing seeds, else the digest at create).
- * [ ] (tests): Reword the affected discovery fixtures' synthetic criteria (`IMPL_CRITERION`, `DOC_CRITERION`, and their V2 twins) to name their command targets so every criterion stays claimed by exactly its citing command; the command-id assertions for the uncited `task-4.txt` probe drop its `-doc-` entry; no assertion is weakened.
- * [ ] (tests): Add the regression example in `ExecutePlanRuntimeTest`: a fixture task whose criteria cite one test module and one documentation path while a third selected path and one pathless criterion exist - with one fixture criterion opening with `The ` so the article-exclusion case is exercised (the probe token must be the casefolded distinctive word, never `the`), the seeded contract claims the cited criteria per command, the probe argv's token equals the criterion-derived value (asserting the value, not an absence - both seeds draw section tokens, so absence cannot discriminate), the create refuses the pathless criterion with the union-equality error, and the old full-list shape fails the claim assertions (the generic-keyword false pass and the seed refusal in one example).

## Task 2: the published criterion-id map and the aligned coverage bullets

Files: scripts/execute_plan_runtime.py, agents/skills/execute-plan/subagent-prompts.md, agents/skills/execute-plan/runtime-contract.md

Anchors:

- `_worker_role_contract` in `scripts/execute_plan_runtime.py`
- `Plan-criterion coverage` in `agents/skills/execute-plan/subagent-prompts.md`
- `capture_verification_evidence` in `scripts/execute_plan_runtime.py`

- * [ ] (code): Publish the task's criterion-id map in the launch contract: `_worker_role_contract` gains one field carrying the `c001...` map over the task's `required_criteria` (the same `evidence_criterion_ids` output the receipts use), serialized to the worker prompt with the existing contract fields.
- * [ ] (docs): Reword both coverage bullets (the Implement Task evidence envelope and the Implement Task Batch member evidence envelope) to the same id-keyed form: per-criterion coverage keyed to the published criterion ids, each changed path naming the ids it satisfies, an implement-owned criterion the return cannot satisfy routing to `status=blocked` with a Blockers entry naming the id - the existing route, now with the concrete key.
- * [ ] (docs): Reword the runtime contract's seeding span (the every-command-carries-the-full-criteria sentence) to the mapped-subset shape with the digest as the totality enforcement, and add one clause to the worker-result span that the coverage field is keyed to the published criterion ids.
- * [ ] (tests): Run the full sweep and record the outcomes in the task commit message: the three suites (Python 3.11+ interpreter), the two needle commands, the em-dash check over this plan, and the hygiene scan.
