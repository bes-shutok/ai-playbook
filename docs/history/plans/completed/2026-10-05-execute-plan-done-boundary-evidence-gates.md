# Plan: execute-plan done boundaries carry complete evidence

Backlog origins (scope of record):
- `docs/history/backlog/2026-10-05-execute-plan-doc-registry-review-fix-override.md`
- `docs/history/backlog/2026-10-05-execute-plan-scope-evidence-drift.md`
- `docs/history/backlog/2026-10-05-execute-plan-r5-review-log-finalization.md`

Driving force: reliability and correctness (three witnessed 2026-10-05 STORY-KEY execution failures on one shared surface, the evidence an execute-plan run carries across its done boundaries: a review fix to a registered frozen artifact was refused at the commit gate because the authorization and its cleanup were never discoverable mid-run, and the refusal's ownership recovery was undocumented; a task whose scope included a contract-claiming doc reached its done boundary while a stale absence claim in that doc passed unnoticed because the plan's validation command for it was not required task-owned evidence; and two separate rounds launched the done worker against missing or heartbeat-only review logs, stranding verified work behind avoidable refusals)

Plan review record: the staging series docs/reviews/2026-10-05-plan-review-execute-plan-done-boundary-evidence-gates-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Terms

- Done boundary: an execute-plan step where the done skill runs (Step 1.4 per task, Step 3.4 per review iteration); its gates refuse commits whose preceding-step evidence is incomplete.
- Preceding-step log paths: the per-step log files passed into a done sub-agent per agent-logs.md; for a review round the review log `{tmp_dir}/execute-plan/<PLAN_SLUG>/review-r<R>-doing-code-review.log.md` (always) and the address log `review-r<R>-receiving-review.log.md` (when Step 3.3 ran).
- Heartbeat: the `in_progress` Pass block a log owner appends before waiting on workers (agent-logs.md Heartbeat section); it proves liveness, never completion.
- Terminal pass: the log's final Pass block recording Status `success` or `blocked`; a log whose last Pass block is still `in_progress` is heartbeat-only.
- Consolidated round record: any single combined log or record a run writes at a path outside agent-logs.md's path table (witnessed: `review-r<R>.log.md`); it never substitutes for a per-step contract path.
- Plan validation command: an entry under the plan's `## Validation Commands` section; its subject paths are the file paths its command text names or greps.
- Scope-intersecting validation command: a plan validation command whose subject paths intersect a task's declared file scope (the task's Files list); every intersecting boundary accounts for the command per the Bound task rule. Today nothing requires such a command to run as task-owned evidence at the done boundary: Step 1.2 already hands implement workers the plan's Validation Commands and requires their task-local commands to pass, but the captured task-local set is undetermined and can omit the scope-intersecting command, and the only enforced whole-set run is Phase 2 validation, after every task boundary.
- Bound task: the task whose completion establishes a scope-intersecting command's expected post-state. Every intersecting task's boundary accounts for the command (the obliged set is selected by scope intersection alone): the boundary records the command green when it exits zero, records it deferred with the owning task named when it exits non-zero and a later task's Files list intersects the command's subject paths (the owning task is the earliest such later task), and records it blocked when no later intersection and no in-task passing re-run exists; the owning task's own boundary requires the green run.
- Registry audit-note override: doc-hierarchy's dated `user-approved YYYY-MM-DD:` note on a completed-history registry row licensing an otherwise immutable write; doc-hierarchy requires its removal after the licensed write lands. Plan-scope naming triggers the duty to surface the override and obtain the explicit user confirmation the token asserts; it never substitutes for the confirmation, and a self-minted note licenses nothing.
- Licensed write: the minimal plan-scoped edit the audit note authorizes; its landing is the event after which the note must be cleared.
- Cleanup owner: the named runner of the note-clearing commit: the same review-fix run when a boundary can carry it, else a recorded follow-up naming the owning run and its receipt.
- Mid-session-created path: a file created after the done Step 0 porcelain snapshot, so no `--owned-path` claim can name it; it passes the foreign-staging gate (not start-dirt) and refuses post-landing-staging when staged (staged requires ownership).
- Boundary adoption: the documented recovery where a fresh done boundary passes `--adopt <run_id>` under the Step 0 adopt clause's operator authorization and re-derives the full owned-path set including the prior boundary's uncommitted output; the operator-authorized cross-session arm keeps the adopted run's own uncommitted output per the existing adoption re-derivation record.

## Why

All three defects sit on the same seam, the evidence contract between execute-plan and its done boundaries, witnessed within one consumer run on 2026-10-05. The registry fix was authorized by plan and review yet refused by the commit gate, and the sanctioned recovery (close the boundary, adopt it fresh with the registry path in the re-derived set) exists in the manifest paragraph but is named nowhere the refusal or the skills point to, so the run rediscovered it live. The stale architecture pointer survived a task boundary because no gate requires a scope-intersecting plan validation command to run as task-owned evidence, so the gap between the undetermined task-local command set and the enforced Phase 2 whole-set run is exactly where the stale claim hid. The review-log refusals fired twice (rounds 5 and 7) because nothing in the orchestration finalizes the heartbeat or validates the contract log paths before launching done, and a consolidated record at a non-contract path let the run believe the evidence existed. One plan keeps the three fixes coherent on the one surface they share.

## Outcome

- A review fix whose plan scope names a registered completed-history artifact discovers the frozen state before implementation regardless of migration signal or plan age, runs under the documented audit-note lifecycle (explicit user confirmation obtained, note added before the licensed write, cleared by a cleanup commit with a named owner and receipt after the landing), and a mid-session-created registry path that a landing must stage has one documented recovery, named by the post-landing-staging refusal itself: close the boundary and reopen under adoption, per the Step 0 adopt clause's operator authorization, with the re-derived set naming only paths that boundary's own session created (the operator-authorized cross-session arm keeps the adopted run's own uncommitted output per the existing adoption re-derivation record). The manifest stays non-extendable in place.
- A scope-intersecting plan validation command runs as task-owned evidence at its bound task's done boundary, on the implement pass: the implement log's envelope names it and its exit status, a missing run or a recorded non-zero exit with no recorded passing re-run routes the return to blocked, a deferral at a non-owning intersecting boundary is witnessed with the owning task named, and the Step 1.4 verification gate refuses a silent advance.
- The orchestration finalizes every review-round log it owns (terminal pass, never round-end on `in_progress`) and validates every preceding-step log path (exists at the exact contract path, final pass not `in_progress`) before launching done, reconstructing only from durable records that actually exist and re-running the round when none carries the findings; a consolidated record at any other path never substitutes.

Gate delta: two new refusal classes plus one grown refusal surface, priced by witnessed failures. The Step 1.4 verification gate item refuses a task closeout whose bound scope-intersecting command did not run or failed with no recorded passing re-run (priced by the stale-pointer row, where the defect surfaced only at supplemental validation after the boundary). The Step 3.4 launch validation refuses a done launch onto a missing or heartbeat-only preceding-step log (priced by the two witnessed rounds, where done's own gate refused and stranded verified work behind an avoidable interruption). The grown surface is the evidence envelope's route-to-blocked set, which gains the unrun-or-failed scope-intersecting command beside the existing uncovered-acceptance-criterion route (same pricing: the priced defect ships when only the missing-run arm exists, because a recorded failing run would still advance the task). Task 1 adds no gate and no refusal class: the lib edit appends remedy text to an existing refusal, and the skill edits document an existing lifecycle; the registry gate's hard-fail set, the validator's behavior, and the manifest writer's contract are unchanged.

## Assumptions

- assume authoring runs unattended under the standing operator directive, so the Step 1.4 confirmation is satisfied by the rows' validated records rather than a live interview, and this records substitution never covers an audit-note confirmation: that confirmation is satisfied only through Task 1's escape arm (the standing operator directive explicitly naming dated audit-note overrides for plan-scoped corrections), otherwise the run stops and asks; basis: the maintenance loop's authoring blueprint (loop_mode dual, continuous pacing amendment 2026-09-30).
- assume the venv pytest runner (`$HOME/.agents/venvs/ai-playbook-test/bin/python`) is an external prerequisite: on a host without it, create the venv or fall back to `python3 -m pytest` with the deviation recorded in the session notes, mirroring the receipt shape the readiness line carries; basis: the validation commands' canonical-invocation comments.
- assume the audit-note lifecycle stays documentation-level in this plan: no new validator flag, no new machinery script; doc_registry_validator.py's closed behavior (hard-fail set, note parsing) is unchanged, and the explicit user confirmation the token asserts remains a doc-hierarchy-owned duty the validator cannot and does not replace; basis: origin row 1's Expected asks for discoverability, lifecycle documentation, and surfacing, all of which the existing validator surfaces and skill text can carry.
- assume the run manifest stays non-extendable in place; the boundary-adoption recovery is the sanctioned path for a mid-session-created path a landing must stage, under the Step 0 adopt clause's existing operator authorization; basis: origin row 1's evidence ("the documented adoption contract permits copying a prior interrupted run boundary; it does not permit silently extending an active manifest") and the STORY-KEY run's own witnessed recovery.
- assume Task 2's rule keys mechanically: a plan validation command is scope-intersecting when its command text names a path that also appears on the bound task's Files list, with the bound task resolved by the Terms' binding rule; commands with no intersection stay plan-level; basis: origin row 2's rejected alternative against broadening every task's scope.
- assume Task 3's required-path set stays exactly the existing pass list: the review log always, the address log when Step 3.3 ran (per-worker fan-out logs per the existing fan-out rule); no new required artifact is invented; basis: agent-logs.md's path table and the Step 3.4 pass list, and origin row 3's "validate both required paths".
- assume the done skill's own preceding-step-log gate stays the backstop and is not edited; the fix is upstream of it, in the orchestration that launches done; basis: origin row 3's Effect line credits the done gate's refusal as correct.
- assume the four execute-plan/SKILL.md edit sites (Step 0.4b; Step 1.4 and the Phase 0 machine-manifest seeding derivation sentence, both Task 2's; Steps 3.1/3.4) and the two agent-logs.md edit sites (evidence envelope, Heartbeat section) are disjoint spans; Tasks 1, 2, 3 declare their own and never touch another task's span; basis: the shared-file seam rule.

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: an execute-plan run stops learning about frozen-registry conflicts, stale contract claims, and heartbeat-only review logs at its done boundaries; the discovery, the evidence, and the launch validation move upstream to where they are cheap, and the one refusal that has no in-place fix names its documented recovery.

Before (today): a review fix to a registered frozen file fails the pre-docs registry gate at commit time, and nothing before implementation surfaces the frozen state (the pre-Phase-1 checkpoint that does exist skips itself for post-migration plans and signal-less repos); the run improvises the recovery. A task scoped to `docs/architecture/integrations.md` commits while the plan's negated grep proving the architecture pointer is current is not required task-owned evidence (Step 1.2's task-local command set is undetermined), and the enforced run of the whole set waits for Phase 2. A round's review log sits at `in_progress`, or the only record is a consolidated `review-r5.log.md` at a path no contract names, and done refuses; the orchestration has no validation to catch either shape before launch.

After (this plan): the pre-Phase-1 checkpoint gains an unconditional registry-scope check (its own trigger, exempt from the migration gating) that surfaces frozen targets with the audit-note duty, its explicit user confirmation, and its cleanup owner before implementation starts; the done skill's registry bullet and doc-hierarchy's audit-note paragraph carry the same lifecycle (confirmation before the note, note before licensed write, cleanup commit with named owner and receipt after landing, standing notes surfaced with their owner); the post-landing refusal names the adoption recovery for a staged mid-session creation, bounded to paths the adopting boundary's own session created. A task's evidence envelope is complete only when every bound scope-intersecting plan validation command ran inside the task on the implement pass, and the Step 1.4 gate refuses the close otherwise. A round cannot hand done a heartbeat-only or missing contract-path log: Step 3.1 closes its logs with terminal passes and Step 3.4 validates each path it is about to pass, reconstructing only from durable records that exist, with the consolidated record explicitly a non-substitute.

Edge cases pinned: a plan validation command whose subject paths miss the bound task's Files list stays plan-level (no widening); a task with no Files intersection has no new obligation; an intersecting command failing at a non-owning boundary with a later-task intersection is deferred with the owning task named and is not a blocked route, while the owning boundary requires the green run; a recorded non-zero exit with no recorded passing re-run and no later-task intersection blocks exactly like a missing run; the address log is validated only when Step 3.3 ran; a fan-out round validates the base address log plus every per-worker log per the existing pass list; a log at the exact contract path with final Status `blocked` passes the launch validation (blocked is terminal, and done's own gate owns the consequence); a registry note whose licensed write has landed but whose cleanup commit never ran is a standing note, surfaced with its cleanup owner, not a hard failure; a mid-session-created path that the landing never stages trips nothing new, and the adoption remedy never renders in the no-manifest arm.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the scope-intersection and binding rule is decidable from the plan text and the tasks' Files lists alone; the launch validation reads only the exact contract paths and the log files' final Pass status; the registry discovery reads only the plan's declared paths against the registry table, independent of the migration signal.
- fail-closed shape: every new check refuses (never silently passes) on its defect shape, and every refusal names its remedy: the adoption recovery for the staged mid-session creation (bounded and operator-authorized), the rerun-or-fix instruction for the unrun or failed bound command, the finalize-or-reconstruct instruction for the heartbeat-only log with its no-fabrication bound.
- observability: the evidence envelope names the covered commands, so an auditor can diff declared validation coverage against executed evidence; the refusal texts are greppable literals pinned by tests and validation commands.
- maintainability: all three fixes are text-plus-one-message edits on skills that already own the concepts; no new script, flag, schema field, or gate runner entry.

**Done when:**
- all task boxes checked; the sweep-gates suite and the shared-skill contract suites pass under the venv pytest runner; each pinned grep flips as its task records; the em-dash added-lines scan and the public hygiene scan exit 0; `python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-execute-plan-done-boundary-evidence-gates.md` exits 0 on the final bytes.

**Ship when:**
- an execute-plan run whose plan scope names a frozen registry artifact, a contract-claiming doc, and a review round finishes each done boundary with the authorization, the scoped validation evidence, and the finalized logs already in place, and when the registry path is created mid-session the refusal names the recovery instead of the run improvising it.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (the `gate_post_landing_staging` rc-1 message assembly only)
- `agents/skills/done/SKILL.md` (the Step 0 manifest paragraph's ownership-claims sentence span; the pre-docs sweep gates section's doc-registry bullet only)
- `agents/skills/doc-hierarchy/SKILL.md` (the `audit` column description row, the Corruption override paragraph, and the Integration Points rows for `plans`/`execute-plan` and `done`/`docs-branch` only)
- `agents/skills/execute-plan/SKILL.md` (Step 0.4b one numbered check and its skip-sentence narrowing; the Step 1.4 verification gate list and the Phase 0 machine-manifest seeding derivation sentence; the Step 3.1 log-ownership and verification-gate spans; the Step 3.4 launch block)
- `agents/skills/execute-plan/agent-logs.md` (the machine-verifiable evidence envelope paragraph; the Heartbeat section's existing closing paragraph)
- `agents/skills/execute-plan/subagent-prompts.md` (the Implement Task template's `## Validation Commands (must all pass before you return)` block only)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` (new assertions beside the existing post-landing-staging fixtures)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change, or contradicts a contract the plan changed.

**Out of scope; reject unless plan-related:**
- `scripts/doc_registry_validator.py`: its closed behavior (hard-fail set, note parsing, check-writes union) is unchanged by this plan; adjacency only.
- the sweep-gates gate semantics beyond the rc-1 message text (the staged/unstaged legs, the placement widening landed by the post-landing-staging placement plan): frozen; this plan's lib edit is message-only and must not perturb the widened-unstaged leg.
- `scripts/review_record_selection.py` and the reviews-corpus staging-doc contract: the canonical-record tooling the STORY-KEY resume used is adjacent context, not an edit surface.
- the done skill's preceding-step-log gate and sweep-gate runner wiring: the backstop stays byte-identical.
- the consumer STORY-KEY repository: this plan changes the shared skills only; the witnessed run's own recovery is history, not a task.

## Validation Commands

```bash
# Sweep-gates suite (new refusal-text assertions beside the existing
# post-landing fixtures; the venv runner is the canonical invocation)
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -q
# Shared-skill contract suites over the exact bytes Tasks 2 and 3 edit
# (shared-body runtime neutrality and pinned-span assertions)
"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_runtime_capabilities.py scripts/test_execute_plan_runtime.py -q
# Task 1 pins (each literal is contained verbatim in the checkbox text
# that prescribes it; all six verified zero hits at authoring, fresh
# greps recorded 2026-10-05)
grep -F "whose re-derived owned-path set names only paths that adopting boundary's own session created" scripts/done_sweep_gates_lib.py
grep -F "refuses post-landing-staging when staged" agents/skills/done/SKILL.md
grep -F "names its cleanup owner at add time" agents/skills/doc-hierarchy/SKILL.md
grep -F "cleanup owner and receipt duty" agents/skills/doc-hierarchy/SKILL.md
grep -F "standing note observed past its licensed write's landing" agents/skills/done/SKILL.md
grep -F "registry-authorization duty" agents/skills/execute-plan/SKILL.md
# Task 2 pins (verified zero hits at authoring, fresh greps recorded)
grep -F "scope-intersecting" agents/skills/execute-plan/SKILL.md
grep -F "scope-intersecting" agents/skills/execute-plan/agent-logs.md
# Task 3 pins (verified zero hits at authoring, fresh greps recorded)
grep -F "closed by a terminal" agents/skills/execute-plan/agent-logs.md
grep -F "never substitutes for the per-step contract paths" agents/skills/execute-plan/SKILL.md
# Added-lines em-dash scan over the changed set (added-lines, never argless)
bash scripts/check-no-em-dash.sh added-lines --base main
# Public hygiene scan (fail-closed; outcome contract)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
# Readiness (fail-closed; outcome contract); RED at authoring until the
# staging review series lands under docs/reviews; green once the
# authoritative (highest-rN) review record's source_digest matches the
# current plan bytes (the r1, r2, and r3 records review earlier digests;
# green arrives from the first record whose source_digest matches these
# bytes, the r4 record or its successor)
python3 scripts/plan_readiness.py docs/history/plans/2026-10-05-execute-plan-done-boundary-evidence-gates.md
```

### Task 1: the registry-override lifecycle is discoverable and its recovery is named

Files:
- `agents/skills/done/SKILL.md` (Step 0 manifest paragraph ownership-claims sentence; the pre-docs sweep gates section's doc-registry bullet)
- `agents/skills/doc-hierarchy/SKILL.md` (audit column row; Corruption override paragraph; Integration Points rows for `plans`/`execute-plan` and `done`/`docs-branch`)
- `agents/skills/execute-plan/SKILL.md` (Step 0.4b: one numbered check plus the skip-sentence narrowing)
- `scripts/done_sweep_gates_lib.py` (rc-1 message assembly only)
- `scripts/test_done_sweep_gates_lib.py` (new assertions)

Shared-file seam: this task owns Step 0.4b in execute-plan/SKILL.md; Tasks 2 and 3 own other spans of the same file and neither may edit this span.

Evidence:
- `grep -F "whose re-derived owned-path set names only paths that adopting boundary's own session created" scripts/done_sweep_gates_lib.py`; covers the refusal remedy (RED at authoring: zero hits, fresh grep recorded 2026-10-05; re-pinned in review r2 to a contiguous span of checkbox 6's dictated remedy text)
- `grep -F "refuses post-landing-staging when staged" agents/skills/done/SKILL.md`; covers the Step 0 recovery clause (RED at authoring: zero hits, fresh grep recorded 2026-10-05; the old `mid-session creations pass the foreign-staging gate` pin was retired in review r1 because it matched the pre-existing anchor sentence)
- `grep -F "names its cleanup owner at add time" agents/skills/doc-hierarchy/SKILL.md` and `grep -F "cleanup owner and receipt duty" agents/skills/doc-hierarchy/SKILL.md`; covers both doc-hierarchy lifecycle edits (RED at authoring: zero hits, fresh greps recorded 2026-10-05)
- `grep -F "standing note observed past its licensed write's landing" agents/skills/done/SKILL.md`; covers the Step 2 bullet (RED at authoring: zero hits, fresh grep recorded 2026-10-05)
- `grep -F "registry-authorization duty" agents/skills/execute-plan/SKILL.md`; covers the Step 0.4b check (RED at authoring: zero hits, fresh grep recorded 2026-10-05)
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_done_sweep_gates_lib.py -q`; covers the refusal-text assertions at the task boundary
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_runtime_capabilities.py scripts/test_execute_plan_runtime.py scripts/test_harness_policy_contract.py scripts/test_lessons_recovery_contract.py -q`; covers the shared-skill and done-contract suites over the skill bytes Task 1 edits (green at authoring; must stay green after the edits)

- [x] In doc-hierarchy's audit column row (the row beginning `| \`audit\` | optional free-text note;`), after the existing hard-fail sentence ending `a self-minted note licenses nothing`, append the review-fix lifecycle: a review fix whose plan scope names the row's path triggers the duty to surface the override and obtain the explicit user confirmation the token asserts (plan-scope naming never substitutes for the confirmation, and under an unattended directive the run stops and asks unless the standing operator directive explicitly names dated audit-note overrides for plan-scoped corrections to completed-history rows); the confirmed fix adds the dated note BEFORE the licensed write, the note names its cleanup owner at add time (the same run when a boundary can carry the clearing commit, else the recorded follow-up run), and the cleanup commit removes the note after the licensed write lands, with the clearing receipt recorded in the clearing run's session notes [class: IMPLEMENTATION_REQUIRED]
- [x] In doc-hierarchy's Corruption override paragraph, in the sentence ending `and is removed after the licensed write lands so the guard does not stay disarmed`, extend the removal clause to read: the note names its cleanup owner at add time and the cleanup owner and receipt duty recorded at add time is discharged by the clearing commit after the licensed write lands, so the two sites state one lifecycle [class: IMPLEMENTATION_REQUIRED]
- [x] In doc-hierarchy's Integration Points rows, append to the `plans`, `execute-plan` row the new consumer duty (execute-plan's pre-Phase-1 registry-authorization discovery) and to the `done`, `docs-branch` row the standing-note owner reporting duty, so the provider skill names both consumers [class: IMPLEMENTATION_REQUIRED]
- [x] In the done skill's pre-docs sweep gates section's doc-registry bullet, directly after the existing sentence fragment `report them, and clear a standing-override's audit note after the licensed write lands`, append: a plan-scoped correction to a completed-history path runs on the dated audit-note lifecycle doc-hierarchy defines, with the explicit user confirmation obtained before the note is added and its cleanup owner named at add time; a standing note observed past its licensed write's landing is reported together with that recorded owner (or, when none was recorded, with the direction that the next run clearing it records the receipt) [class: IMPLEMENTATION_REQUIRED]
- [x] In the done skill's Step 0 manifest paragraph, in the sentence containing `mid-session creations pass the foreign-staging gate without claims`, extend the parenthetical's clause so the paragraph states the full gate picture: a mid-session-created path passes foreign-staging (it is not start-dirt) and refuses post-landing-staging when staged (staged requires ownership), and a mid-session-created path a landing must stage is recovered only by closing this done boundary and opening a fresh adopting boundary, per this Step 0 adopt clause's operator authorization, whose re-derived owned-path set names only paths that adopting boundary's own session created (the re-derivation record names the authoring evidence per adopted path; any other staged residue keeps the refusal; the operator-authorized cross-session arm keeps the adopted run's own uncommitted output per the existing adoption re-derivation record); the active manifest is never extended in place [class: IMPLEMENTATION_REQUIRED]
- [x] In `gate_post_landing_staging`'s rc-1 GateResult message assembly, when `staged_residue` is non-empty AND the run manifest resolved for the session window (`owned` is not None), append the mid-session-creation remedy to the message text: a staged path created after Step 0 (absent from every manifest claim set) is recovered by closing this done boundary and opening a fresh adopting boundary, per the Step 0 adopt clause's operator authorization, whose re-derived owned-path set names only paths that adopting boundary's own session created (the operator-authorized cross-session arm keeps the adopted run's own uncommitted output per the existing adoption re-derivation record), never by widening the active manifest in place; the no-manifest arm's rc-1 message, the indeterminate arms' shared render, and every other gate leg stay byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] In `scripts/test_done_sweep_gates_lib.py`, beside the existing post-landing-staging fixtures, add: an assertion that a staged-unowned residue with a resolved manifest (the mid-session-creation shape) produces the rc-1 refusal naming the adopting-boundary remedy; a negative-direction assertion that the adopting-boundary remedy literal is absent from the unstaged-only refusal message; a held-lock plus staged-residue arm using the existing `acquire_merge_lock_for_gate` helper asserting exit 2 with the remedy literal absent from the indeterminate message; and an assertion that the no-manifest arm's rc-1 message stays byte-identical to today's text [class: REPOSITORY_TEST]
- [x] In execute-plan Step 0.4b, add a fourth numbered check with its own unconditional trigger, reading: regardless of the migration-complete signal or the plan's age, when the plan's Files lists name paths under `docs/` that the document registry registers completed or immutable, surface the registry-authorization duty (doc-hierarchy's dated audit-note override, its explicit user confirmation, and its cleanup owner) before implementation starts, so the commit-gate discovery never lands mid-run; and narrow the section's skip sentence so it exempts this check (`Skip checks 1 through 3 on repos without the migration-complete signal, or when the grep returns clean (plan post-dates the migration); check 4 runs whenever its trigger holds`) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the six greps flip from zero to positive hits; the sweep-gates suite and the shared-skill and done-contract suites pass under the venv runner with the existing fixtures unchanged; the em-dash added-lines scan and the public hygiene scan exit 0 [class: REPOSITORY_TEST]
- [ ] Commit: `fix: registry override lifecycle gains discovery, cleanup owner, and named adoption recovery` [class: IMPLEMENTATION_REQUIRED]

### Task 2: scope-intersecting plan validation commands are task-owned evidence

Files:
- `agents/skills/execute-plan/SKILL.md` (Step 1.4 verification gate list and the Phase 0 machine-manifest seeding derivation sentence only)
- `agents/skills/execute-plan/agent-logs.md` (the machine-verifiable evidence envelope paragraph only)
- `agents/skills/execute-plan/subagent-prompts.md` (the Implement Task template's `## Validation Commands (must all pass before you return)` block only)

Shared-file seam: this task owns Step 1.4 and the Phase 0 machine-manifest seeding derivation sentence in execute-plan/SKILL.md, the evidence-envelope paragraph in agent-logs.md, and the Implement Task template's `## Validation Commands (must all pass before you return)` block in subagent-prompts.md; Tasks 1 and 3 own other spans and neither may edit these.

Evidence:
- `grep -F "scope-intersecting" agents/skills/execute-plan/SKILL.md`; covers the gate item pin (RED at authoring: zero hits, fresh grep recorded 2026-10-05)
- `grep -F "scope-intersecting" agents/skills/execute-plan/agent-logs.md`; covers the envelope pin (RED at authoring: zero hits, fresh grep recorded 2026-10-05)
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_runtime_capabilities.py scripts/test_execute_plan_runtime.py -q`; covers the shared-skill contract suites over the edited bytes (green at authoring; must stay green after the edits)

- [x] In agent-logs.md's evidence envelope paragraph (the paragraph at the `A worker pass that reports \`success\` records the machine-verifiable evidence envelope` anchor), extend the coverage obligation so it reads: for the implement pass, the coverage must be complete across the task's acceptance criteria the implement step owns AND across every scope-intersecting plan validation command for the implement pass (a `## Validation Commands` entry whose subject paths intersect the task's declared file scope; every intersecting boundary accounts for the command per the Bound task rule, which decides only the green-run versus witnessed-deferral arm), with each such command's identity and exit status recorded in `Commands run`; an implement-owned criterion without a coverage mapping routes the return to blocked exactly as today, a scope-intersecting command with no recorded run routes the same way, and a scope-intersecting command recorded with a non-zero exit routes the same way unless a later re-run of the same command inside the task is recorded in `Commands run` with exit zero; a non-zero exit at a boundary whose later task's Files list intersects the command's subject paths is recorded as deferred with the owning task named in `Commands run` (the earliest such later task owns the green run), and the witnessed deferral is not a blocked route; review-iteration passes are unchanged by this clause [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 1.4 verification gate list, add item 5: every scope-intersecting plan validation command (a `## Validation Commands` entry whose subject paths intersect the completed task's declared file scope) is accounted for on the implement pass, witnessed by the implement log's `Commands run` section: the green run at the owning boundary, else a witnessed deferral naming the owning task; a missing run, or a recorded non-zero exit with no recorded passing re-run and no later-task intersection, relaunches done or a fix sub-agent before Task N+1 opens, never a silent advance [class: IMPLEMENTATION_REQUIRED]
- [x] In subagent-prompts.md's Implement Task template, at the `## Validation Commands (must all pass before you return)` block, add one sentence: the prompt's command set includes the task's bound scope-intersecting plan validation commands explicitly, so the worker runs them as task evidence rather than inferring the task-local set [class: IMPLEMENTATION_REQUIRED]
- [x] In the Phase 0 machine-manifest seeding paragraph, replace the derivation sentence (the span beginning `Before invoking create, derive the task-to-evidence mapping only from each task's own \`Evidence:\` declaration`) so it reads: derive the task-to-evidence mapping from each task's own `Evidence:` declaration plus its mechanically derived scope-intersecting set, the plan's `## Validation Commands` entries whose subject paths intersect that task's declared file scope, with the Bound task rule deciding the green-run versus witnessed-deferral arm at each boundary; checklist prose, worker summaries, and the global validation block never seed a contract; the set derives from the plan's own declared command lists per the Terms rule, never from prose, and is never a clone of the global block, so a driver-built child prompt carries the obliged set in structured launches exactly as the implement template's sentence provides it in prompt-built launches [class: IMPLEMENTATION_REQUIRED]
- [x] Re-derive all anchor spans from live bytes before editing and verify the surrounding text survives byte-identical outside the appended and inserted clauses [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both greps flip to positive hits; the shared-skill contract suites still pass; the em-dash added-lines scan and the public hygiene scan exit 0 over the changed set [class: REPOSITORY_TEST]
- [ ] Commit: `fix: plan validation commands scoped to a task run as its evidence` [class: IMPLEMENTATION_REQUIRED]

### Task 3: review logs finalize before done launches, and the launch validates the contract paths

Files:
- `agents/skills/execute-plan/SKILL.md` (Step 3.1 log-ownership and verification-gate spans; the Step 3.4 launch block)
- `agents/skills/execute-plan/agent-logs.md` (the Heartbeat section's existing closing paragraph)

Shared-file seam: this task owns Steps 3.1/3.4 in execute-plan/SKILL.md and the Heartbeat closing paragraph in agent-logs.md; Tasks 1 and 2 own other spans and neither may edit these.

Evidence:
- `grep -F "closed by a terminal" agents/skills/execute-plan/agent-logs.md`; covers the closing-duty pin (RED at authoring: zero hits, fresh grep recorded 2026-10-05; the literal is part of the dictated sentence below)
- `grep -F "never substitutes for the per-step contract paths" agents/skills/execute-plan/SKILL.md`; covers the non-substitution pin (RED at authoring: zero hits, fresh grep recorded 2026-10-05; the old `never substitutes` pin was retired in review r1 because it matched an unrelated pre-existing sentence)
- `"$HOME/.agents/venvs/ai-playbook-test/bin/python" -m pytest scripts/test_runtime_capabilities.py scripts/test_execute_plan_runtime.py -q`; covers the shared-skill contract suites over the edited bytes (green at authoring; must stay green after the edits)

- [x] In agent-logs.md's Heartbeat section, fold the closing duty into the existing paragraph that begins `When the staging doc is written, append a final Pass` (edit that paragraph in place rather than appending a parallel one): retrigger it to `when the owning step ends (workers returned, staging doc synthesized) and before the Step 3.1 verification gate evaluates item 2`, and extend it to read: the owner appends the terminal pass to the same log, so the log is closed by a terminal pass (Status `success` or `blocked`) and a round never ends with `in_progress` as the file's last Pass status; an `in_progress` heartbeat that is still the last pass at done-launch time is the defect shape the Step 3.4 launch validation refuses [class: IMPLEMENTATION_REQUIRED]
- [x] In Step 3.1, in the parent-ownership paragraph (the `**Default:** the parent writes \`<REVIEW_LOG_PATH>\`` anchor), extend the parent's duty by round shape: on a fanned address round the parent appends the merge pass that closes the base address log itself (the base log is parent-owned there); on a single-worker address round the parent holds a verification duty only (the receiving-review worker owns and closes the log, and the Step 3.4 launch validation refuses a heartbeat-only worker-owned log); the same paragraph gains one sentence: a consolidated round record written at any path outside agent-logs.md's path table never substitutes for the per-step contract paths [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 3.1 verification gate list, extend item 2 so it reads: `<REVIEW_LOG_PATH>` exists and is non-empty AND its final Pass block records terminal Status `success` or `blocked`, never `in_progress` [class: IMPLEMENTATION_REQUIRED]
- [x] In the Step 3.4 launch block, before the `Launch a sub-agent` sentence, insert the launch validation: for every preceding-step log path this launch will pass, verify the file exists at its exact contract path and its final Pass block's Status is not `in_progress`; a missing or heartbeat-only log stops the launch; the parent finalizes the log from the round's durable records that actually exist (the staging doc, the worker returns), marking the reconstruction and any missing raw worker evidence in the log body, and where no durable record carries a worker's findings the log is not reconstructed: the round re-runs per the review-round contract and the refusal stands until a genuinely produced log exists; worker output is never synthesized; a consolidated record at any non-contract path never satisfies this validation, and the required set stays the existing pass list (review log always; address log, base plus per-worker fan-out logs, when Step 3.3 ran) [class: IMPLEMENTATION_REQUIRED]
- [x] Re-derive all anchor spans from live bytes before editing and verify the Step 3.4 pass list, the fan-out rule, and the done sub-agent verification gate below the insertion stay byte-identical [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: both greps flip to positive hits; the shared-skill contract suites still pass; the em-dash added-lines scan and the public hygiene scan exit 0 over the changed set [class: REPOSITORY_TEST]
- [ ] Commit: `fix: execute-plan finalizes review logs and validates them before done` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

The origin rows `docs/history/backlog/2026-10-05-execute-plan-scope-evidence-drift.md` and `docs/history/backlog/2026-10-05-execute-plan-r5-review-log-finalization.md` are covered in full by this plan and are deleted in the same completion pass: the registry-override lifecycle, scope-intersecting evidence contract, and review-log finalization duties are landed across the done, doc-hierarchy, and execute-plan skills (commits d18158dd, 38339145, 8ba57657), certified by the Phase 3 five-lens panel (zero blocking) and review-plan r6 (ready=yes).
`docs/history/backlog/2026-10-05-execute-plan-doc-registry-review-fix-override.md` is likewise covered in full by the landed registry-override lifecycle (Task 1's audit-row review-fix duty, the Corruption-override cleanup-owner clause, and the done skill's plan-scoped-correction bullet) and is deleted in the same completion pass.
