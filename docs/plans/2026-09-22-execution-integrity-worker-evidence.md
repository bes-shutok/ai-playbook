# Plan: execution integrity: worker evidence, claim duty, manifest status

Backlog origins: `docs/history/backlog/2026-09-22-execute-plan-worker-evidence-verification-gate.md`, `docs/history/backlog/2026-09-22-authoring-payload-omits-claim-duty.md`, `docs/history/backlog/2026-09-22-execute-plan-runtime-state-untracked-litter.md`.

## Terms

- **Evidence envelope**: the machine-verifiable return a worker must supply on `status=success`: validating command identity, working directory, exit status, output identity, selected test identities, changed paths against the launch baseline, and plan-criterion coverage. Normative home: `agents/skills/execute-plan/runtime-contract.md` "Worker execution contract" principle 3.
- **AUTHORING CLAIM duty**: the write/refresh/delete lifecycle of the claim file `docs/tmp/authoring-claims/<backlog-item-basename>.md` (frontmatter `session:`, `item:`, `created:`, `updated:`) that makes an authoring session visible to the maintenance G1a lane guard.
- **Payload tail**: the "Schedule at {schedule_time} the following task:" paragraph of the authoring blueprint (the payload sentence plus its tail sentences: pre-authorization, session constraints, review/done, migration, self-landing). The maintenance Step 5 authoring slice documents the WHOLE fenced body as the scheduled prompt, but observed dispatch practice (the automation-197f75a7 witness in the origin, and the automation-ae88c54e run that authored this plan) transmitted only this paragraph; the plan's payload-side duties target it for exactly that reason.
- **Machine manifest**: the runtime driver's structured state file `runtime_state.json` (plus its `runtime_state.json.lock`), the sole machine-state source for an execute-plan run; canonical home `{tmp_dir}/execute-plan/<plan-slug>/`.

## Assumptions

- assume the evidence envelope already landed on main (commit 8a77ec46) and this plan closes the acceptance-completeness residue, not the envelope itself; basis: authoring-time read of runtime-contract.md principle 3, SKILL.md Step 1.2 evidence bullet, subagent-prompts.md Evidence envelope section at main 50cf6e20.
- assume agent-logs.md is in scope: its envelope sentence is a near-verbatim mirror of contract principle 3 (two known pre-existing wording deltas: `its working directory` vs `the working directory it ran in`, and `the output identity of the captured result` vs `of the captured output`) and would drift if only the contract changed; basis: side-by-side read at authoring (agent-logs.md line ~127); the pre-existing paraphrase deltas are frozen context, not defects this plan reconciles.
- assume the payload-tail insert uses the literal repository-relative `docs/tmp/authoring-claims/` path and introduces no new `{brace}` fill-in placeholders; basis: the pins suite pins each blueprint body's placeholder set exactly (scripts/check_maintenance_pins.sh placeholder-set pin) and child payloads are self-contained by design (ledger line 20 precedent in prompt-templates.md).
- assume the executing session must not edit runtime driver scripts or add runtime enforcement hooks; driver-side validation and the done-blocking hook stay owned by the separate runtime implementation plan; basis: origin 3's explicit routing ("Not a contract-text defect and not runtime enforcement"), origin 1's capture note, and the live codex-reconciliation execution holding the runtime scripts.
- assume a peer execution may land changes on these surfaces between this plan's certification and its execution: the executor repeats the Phase 0 drift check on the five skill surfaces plus the pins suite before starting Task 1 and re-certifies on drift; basis: dispatcher caution (codex-reconciliation execution live on the same runtime surfaces).
- assume the ledger-deviation bullet convention applies: every amendment to a blueprint body gets a dated ledger entry in prompt-templates.md; basis: lines 5-41 of that file, every prior amendment documented.

Decision points requiring a grill: origin-1 enforcement depth: contract/parent-gate prose only, driver and hook enforcement routed to the separate runtime implementation plan; decision: standing pre-authorization accepting the recommended contract-level option; source: automation-ae88c54e payload; 2026-09-22; affected: Gist, Review Scope, out-of-scope list; origin-2 fix shape: payload-tail compact claim paragraph per the origin's suggested fix rather than dispatcher-owner reassignment; decision: standing pre-authorization; source: same payload; 2026-09-22; affected: Task 3; origin-3 remedy: documentation-first declaration (the origin's remedy (a), "any one suffices") with the gitignore alternative declined as misuse-masking; decision: standing pre-authorization; source: same payload; 2026-09-22; affected: Task 4.

## Certification surface baselines

sha256 of each in-scope surface, captured at certification time (the surfaces are independent of the plan's own bytes; the certified plan digest lives in the final review round's `.stats.json` sidecar `source_digest` field, never in this file, because quoting it here would go stale on the next fold). Task 1's pre-step compares the execution-start digests against these lines; a mismatch means the surface changed since certification (peer landing on the shared runtime surfaces) and triggers the re-read/re-cert arm before any edit.

```
b0ab96887005614d2fb8d60851f8b8b8a5143b05f89fc2a497af7841b3ddb117  agents/skills/execute-plan/SKILL.md
841d52733f75662197c70e8a150e5f1663ca658d44b2cf4cf9bb66e2edeb60e3  agents/skills/execute-plan/runtime-contract.md
242acc1023141a071098bf63322be4c90f008389892a34dd04ed8c68366d7a1e  agents/skills/execute-plan/subagent-prompts.md
ea07aaa5c5eab68430b4f4efd3eee147aedc6aea9880cb687b1d7d6aefb4f73d  agents/skills/execute-plan/agent-logs.md
5d8d06cf4a55a1be9c356def32d9aaa7437a1a8cbf609d14b966c6493cb9773d  agents/skills/maintenance/prompt-templates.md
f3d1a6d0efa25506401cab76ec0a8c2b09de9f300d9cf4a8d00ecf4a4116142b  scripts/check_maintenance_pins.sh
```

## Gist & Examples

Three documentation-and-gate gaps let execution-integrity failures slip through unseen. This plan closes all three in the contract/gate prose layer, where the surfaces live, and routes runtime enforcement out.

1. **Worker evidence acceptance (high).** A worker returned a success narrative with test counts and scope claims; independent review then found the claimed coverage did not exercise the new code, the migration did not implement the stated transition, and required test partitions were absent. The envelope contract exists (landed by the agent-aware contract plan the same day the origin was captured), but the parent's acceptance gate only requires the envelope to be *carried*. A coverage matrix filled with plausible prose passes it. Example: a task with three acceptance criteria and an envelope whose plan-criterion coverage names only criterion 1 is accepted today, because no gate compares the coverage against the task's checklist. The fix makes acceptance a verification duty: the parent maps every acceptance criterion of the task against the envelope's selected test identities and coverage claims, refuses success when a criterion has no mapping, and resolves every output identity to a fresh captured section in the task's implement log. Refusals reuse the contract's existing fail-closed shapes (malformed receipt refuses as `blocked`/`error`, never a degraded success).

2. **Authoring claim duty in the payload (medium).** The AUTHORING CLAIM duty lives in the blueprint body, but the payload-sentence paragraph is what scheduled sessions have actually received (observed dispatch practice diverges from the Step 5 authoring slice's whole-body wording; the origin's automation-197f75a7 witness and this plan's own authoring run both received only the payload paragraph), so payload-born authoring sessions never learn the duty: no claim file, no refreshes, no delete, invisible to the G1a discovery arm for their whole life (the automation-197f75a7 session wrote its claim only retroactively during done). The fix appends one compact claim paragraph to the payload paragraph, between the session constraints and the landing sentences: write before any plan work, refresh at boundaries, delete at closeout, all addressed to the primary checkout's `docs/tmp/authoring-claims/` in explicit-rooted form. A pins-suite pin guards the paragraph so the omission cannot regress silently.

3. **Runtime-state litter (low).** The driver keeps `runtime_state.json` and `runtime_state.json.lock` as untracked files, and a run may place them at the repo root via a relative `--manifest` path. A reviewer flagged such files as litter; only tribal knowledge says they are the live machine manifest. The fix declares the convention where the driver is documented: the manifest and its lock are intentionally untracked live run state, the canonical home is `{tmp_dir}/execute-plan/<plan-slug>/` (inside the gitignored `docs/tmp/`), a root-level manifest is live state too, and implement workers, reviewers, and done runs must never classify or delete these files as dirt. The `.gitignore` remedy is deliberately declined: hiding root-level manifests would mask the misuse that produced them.

Runtime enforcement (driver-side envelope validation, the done-blocking hook from origin 1's suggested fix 5) is out of scope: it belongs to the separate runtime implementation plan, and the codex-reconciliation execution currently owns the runtime scripts.

## Evaluation Criteria

**Quality dimensions:**

- correctness: the parent acceptance gate refuses success on an unmapped acceptance criterion or a dangling output identity, reusing the contract's existing fail-closed refusal semantics; a complete envelope passes unchanged.
- consistency: the NEW completeness-clause span stays literal-identical on its two pinned surfaces, the contract (SOT) and the agent-logs.md mirror (probe 6 pins the span `complete across the task's acceptance criteria` there); SKILL.md Step 1.2 and the worker templates carry the implement-owned scoping semantics witnessed by probes 3 and 5 without the exact span; the pre-existing paraphrase deltas between the surfaces are frozen context, not reconciliation work; the claim-duty paragraph mirrors the blueprint duty paragraph's frontmatter shape.
- regression-safety: `scripts/check_maintenance_pins.sh` exits 0 including the new payload-tail pin; the contract content-parity and runtime-capability doc-anchor tests still pass; the pinned `machine-verifiable evidence` anchor paragraph survives intact.
- minimality: no runtime script edits; no `.gitignore` change; no new fill-in placeholders in either blueprint body.

**Done when:**

- SKILL.md Step 1.2 acceptance bullet requires verification of complete plan-criterion coverage and resolvable output identity before `success` is accepted.
- runtime-contract.md principle 3 carries the completeness obligation and the `evidence` schema row points at it.
- Both worker templates (single task and batch member) demand complete coverage mapping with blocked-status routing for unsatisfiable criteria.
- agent-logs.md mirror sentence carries the same completeness clause.
- The authoring payload tail carries the compact claim paragraph; the ledger documents it; the pins suite asserts it.
- runtime-contract.md "Durable driver boundary" and agent-logs.md "Machine state and receipt ownership" declare the untracked-live-state convention with the do-not-delete duty.
- All Validation Commands pass on the executed tree.

**Ship when:** none; every outcome is repository-verifiable (documentation and pins only, no external gates).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/execute-plan/SKILL.md` (Step 1.2 worker completion evidence bullet only; all other sections frozen)
- `agents/skills/execute-plan/runtime-contract.md` (Worker execution contract principle 3, Normalized result schema `evidence` row, Durable driver boundary section only; all other sections frozen)
- `agents/skills/execute-plan/subagent-prompts.md` (Evidence envelope subsections of the Implement Task and Implement Task Batch templates only; all other sections frozen)
- `agents/skills/execute-plan/agent-logs.md` (worker success envelope sentence and Machine state and receipt ownership section only; all other sections frozen)
- `agents/skills/maintenance/prompt-templates.md` (authoring payload tail insert and one new ledger bullet only; the byte-identical re-arm parity paragraphs and every other pinned span frozen)
- `scripts/check_maintenance_pins.sh` (new payload-tail claim-duty pin only)

**Tests:**
- none added; the pins suite and existing doc-anchor tests are the verification surface

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Documentation:** production code and tests use the explicit list. Docs may also be in scope under plan-related extension when a change is substantively required to keep docs aligned with the feature; not every path needs listing upfront. A doc-closure task should include search/grep for stale references, not only pre-listed paths.

**Out of scope; reject unless plan-related:**
- `scripts/execute_plan_runtime.py`, `scripts/execute_plan_runtime_codex.py`, `scripts/runtime_capabilities.py` and their test files; reason: runtime enforcement owned by the separate runtime implementation plan, currently held by the live codex-reconciliation execution.
- `.gitignore`; reason: the gitignore remedy for origin 3 is declined (masks the misuse that produced root-level manifests).
- `docs/tmp/authoring-claims/` and other `docs/tmp/` scratch; reason: session scratch, never plan content.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"

# 1. Pins suite including the new payload-tail claim-duty pin (must exit 0)
( cd "$REPO" && bash scripts/check_maintenance_pins.sh ) || { echo "pins suite failed"; exit 1; }

# 2. Contract content-parity and runtime-capability doc-anchor tests (must pass; run from scripts/ cwd: the modules use bare sibling imports)
( cd "$REPO/scripts" && python3 -m unittest test_runtime_capabilities >/dev/null 2>&1 ) || { echo "runtime capabilities tests failed"; exit 1; }
( cd "$REPO/scripts" && python3 -m unittest test_execute_plan_runtime.ContractContentParityTest >/dev/null 2>&1 ) || { echo "contract parity tests failed"; exit 1; }

# 3. Parent acceptance gate: coverage-completeness and output-identity obligations present (each its own probe)
grep -qF "maps every acceptance criterion" "$REPO/agents/skills/execute-plan/SKILL.md" || { echo "SKILL.md missing coverage-completeness duty"; exit 1; }
grep -qF "resolves every output identity" "$REPO/agents/skills/execute-plan/SKILL.md" || { echo "SKILL.md missing output-identity duty"; exit 1; }

# 4. Contract completeness obligation present in the pinned anchor paragraph's file
grep -qF "coverage must be complete" "$REPO/agents/skills/execute-plan/runtime-contract.md" || { echo "contract missing completeness obligation"; exit 1; }

# 5. Worker templates demand complete mapping with blocked routing (both template sections must carry each clause)
f="$REPO/agents/skills/execute-plan/subagent-prompts.md"
test "$(grep -cF 'every acceptance criterion the implement step owns' "$f")" -ge 2 || { echo "worker templates missing complete-mapping clause (need both sections)"; exit 1; }
test "$(grep -cF 'never a silent omission' "$f")" -ge 2 || { echo "worker templates missing blocked-routing clause (need both sections)"; exit 1; }

# 6. agent-logs.md mirror carries completeness and manifest do-not-delete
grep -qF "complete across the task's acceptance criteria" "$REPO/agents/skills/execute-plan/agent-logs.md" || { echo "agent-logs mirror missing completeness clause"; exit 1; }
grep -qF "never delete" "$REPO/agents/skills/execute-plan/agent-logs.md" || { echo "agent-logs missing do-not-delete duty"; exit 1; }

# 7. Manifest convention declared in the contract's durable driver boundary
grep -qF "intentionally untracked live run state" "$REPO/agents/skills/execute-plan/runtime-contract.md" || { echo "contract missing untracked-live-state declaration"; exit 1; }

# 8. Payload tail carries the claim paragraph (distinct probe from the blueprint duty paragraph)
python3 - "$REPO" <<'EOF' || { echo "payload tail missing claim paragraph"; exit 1; }
import sys, pathlib
root = pathlib.Path(sys.argv[1])
lines = (root / "agents/skills/maintenance/prompt-templates.md").read_text(encoding="utf-8").split("\n")
anchor = "the following task: Using the plans skill"
hits = [ln for ln in lines if anchor in ln]
assert len(hits) == 1, f"payload paragraph anchor matched {len(hits)} lines, expected exactly 1"
payload = hits[0]
assert "docs/tmp/authoring-claims/" in payload, "payload tail lacks claim path"
assert "updated:" in payload and "refresh" in payload, "payload tail lacks refresh duty"
assert "closeout" in payload and "delete" in payload, "payload tail lacks delete duty"
EOF

# 9. Ledger entry documents the payload-tail amendment
grep -qF "authoring payload tail claim duty" "$REPO/agents/skills/maintenance/prompt-templates.md" || { echo "ledger entry missing"; exit 1; }

# 10. No runtime script or gitignore edits rode the branch
( cd "$REPO" && git diff --name-only main...HEAD -- scripts/execute_plan_runtime.py scripts/execute_plan_runtime_codex.py scripts/runtime_capabilities.py .gitignore | grep -q . ) && { echo "forbidden file changed"; exit 1; } || true
```

Note on probe 10: the `grep -q .` inverted form is intentional (empty diff is the pass condition; a non-empty listing must fail), and the trailing `|| true` belongs to the outer `&& {...} || true` guard so an empty diff exits 0.

### Task 1: Parent acceptance gate verifies coverage completeness (origin 1)

Files:
- `agents/skills/execute-plan/SKILL.md`
- `agents/skills/execute-plan/runtime-contract.md`

- [ ] Pre-step before any edit: compute each surface's sha256 and diff against its certification baseline recorded in the `## Certification surface baselines` section; on a mismatch the surface changed since certification (the codex-reconciliation execution may have landed), so re-read the touched sections, confirm this plan's edits still apply cleanly, and re-certify on drift before proceeding; record the outcome and the execution-start digests in manifest.md [class: REPOSITORY_TEST]
- [ ] In SKILL.md Step 1.2, extend the "Worker completion evidence is machine-verifiable, never narrative" bullet with two verification duties, keeping the existing sentence intact: the parent maps every acceptance criterion the implement step owns (each unchecked `- [ ]` checklist item except `Commit:` lines and other done-step-owned items) against the envelope's selected test identities and plan-criterion coverage claims before accepting `success`, and an implement-owned criterion with no mapping refuses success as a malformed receipt (`blocked`, corrected re-submission per the contract's refusal semantics), never a degraded success; and the parent resolves every output identity in the envelope to a fresh captured section in the task's implement log, and a reference that resolves to nothing is not evidence [class: IMPLEMENTATION_REQUIRED]
- [ ] In runtime-contract.md "Worker execution contract" principle 3, append after the existing refusal sentences (same paragraph block, preserving the `machine-verifiable evidence` anchor sentences byte-for-byte): the envelope's plan-criterion coverage must be complete across the task's acceptance criteria the implement step owns (`Commit:` lines and done-step-owned checklist items excluded), and a coverage set that omits an implement-owned acceptance criterion is a malformed receipt failing closed under the same refusal semantics [class: IMPLEMENTATION_REQUIRED]
- [ ] In runtime-contract.md "Normalized result schema", extend the `evidence` row to reference the completeness obligation in the Worker execution contract (one clause, no duplicated normative text) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: probes 3 and 4 of Validation Commands [class: REPOSITORY_TEST]
- [ ] Run → expect GREEN: contract content-parity and runtime-capability tests (probe 2) [class: REPOSITORY_TEST]
- [ ] Commit: `feat: parent acceptance verifies evidence coverage completeness` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Worker templates demand complete coverage mapping (origin 1)

Files:
- `agents/skills/execute-plan/subagent-prompts.md`
- `agents/skills/execute-plan/agent-logs.md`

- [ ] In the single-task Implement Task template's "Evidence envelope" section, extend the `Plan-criterion coverage` bullet: map every acceptance criterion the implement step owns; an implement-owned criterion this return cannot satisfy routes the return to `status=blocked` with a Blockers entry naming the criterion, never a silent omission [class: IMPLEMENTATION_REQUIRED]
- [ ] Mirror the same clause in the batch template's member "Evidence envelope" section (the active member's envelope) [class: IMPLEMENTATION_REQUIRED]
- [ ] In agent-logs.md, extend the worker success envelope sentence (the paragraph mirroring contract principle 3) with the completeness clause containing the exact span `the coverage must be complete across the task's acceptance criteria the implement step owns` [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: probe 5 and the agent-logs half of probe 6 [class: REPOSITORY_TEST]
- [ ] Commit: `feat: worker evidence envelope demands complete criterion coverage` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Authoring payload tail carries the claim duty (origin 2)

Files:
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/check_maintenance_pins.sh`

- [ ] In the authoring blueprint's payload paragraph (the "Schedule at {schedule_time} the following task:" line, after the branch-agnostic sweep sentence and before the review/ready=yes sentence), append the compact CLAIM DUTY sentences into that same paragraph (the payload body is a single line; the claim sentences join it, keeping probe 8's same-line assertion satisfiable), covering exactly these duties: write the claim file docs/tmp/authoring-claims/<backlog-item-basename>.md in the primary checkout (explicit-rooted form; frontmatter session:, item:, created:, updated:; create-if-absent) before any plan work; refresh its updated: line on every plan-file write, immediately before and after each review round, and at every phase boundary; delete it at closeout (the done handoff) and on any refusal stand-down this session already owned, re-reading the file before each refresh or delete and mutating it only while its session: line still names this session's id; a create refused by an existing claim file naming a foreign session id stands this session down before any plan work, reporting the foreign claim's session id and its updated: timestamp, never clobbering the foreign witness; a foreign claim stale past one cadence period (2 hours) is taken over instead of refused: delete the stale foreign claim file first (recording the takeover with the dead claim's session id and its stale updated: timestamp), then create this session's claim; the sentences use the literal repository-relative docs/tmp/authoring-claims/ path and introduce no new {brace} fill-in placeholders [class: IMPLEMENTATION_REQUIRED]
- [ ] Add one dated ledger bullet to the deviations list documenting the authoring payload tail claim duty addition (origin: docs/history/backlog/2026-09-22-authoring-payload-omits-claim-duty.md; not part of the backlog source text), so the bullet contains the literal span `authoring payload tail claim duty`, and noting the payload paragraph is what scheduled sessions have actually received (observed dispatch practice diverging from the Step 5 authoring slice's whole-body wording, per the origin's automation-197f75a7 witness) while the blueprint body duty paragraph is untouched [class: IMPLEMENTATION_REQUIRED]
- [ ] In scripts/check_maintenance_pins.sh, add one pin asserting the payload sentence region of the authoring blueprint carries the docs/tmp/authoring-claims/ literal (scoped to the Schedule-at paragraph, distinct from the existing whole-body pin), so the omission this origin captured cannot regress silently [class: IMPLEMENTATION_REQUIRED]
- [ ] Pin efficacy check: run the new pin against prompt-templates.md with the docs/tmp/authoring-claims/ literal stripped from the Schedule-at paragraph (strip in place, run, restore), expecting the pin to FAIL on the stripped copy and the full suite GREEN after the restore [class: REPOSITORY_TEST]
- [ ] Verify: neither re-arm duty paragraph is touched (byte-identical parity pin holds), the execution blueprint gains no authoring-claims literal, and the placeholder-set pin still passes [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: probes 1, 8, and 9 [class: REPOSITORY_TEST]
- [ ] Commit: `feat: authoring payload tail carries the claim duty with a regression pin` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Runtime-state manifest convention declaration (origin 3)

Files:
- `agents/skills/execute-plan/runtime-contract.md`
- `agents/skills/execute-plan/agent-logs.md`

- [ ] In runtime-contract.md "Durable driver boundary", add one declaration sentence after the authoritative-manifest sentence: the machine manifest `runtime_state.json` and its `runtime_state.json.lock` are intentionally untracked live run state wherever they live; the canonical home is `{tmp_dir}/execute-plan/<plan-slug>/` inside the gitignored docs/tmp/, and a manifest at the repository root (a relative `--manifest` path) is live state too; implement workers, reviewers, and done runs must never classify or delete these files as dirt or hygiene violations [class: IMPLEMENTATION_REQUIRED]
- [ ] In agent-logs.md "Machine state and receipt ownership", add one do-not-delete sentence containing the exact span `implement workers, reviewers, and done runs must never delete these files` and covering both files with the same root-level clarification [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: probe 7 and the do-not-delete half of probe 6 [class: REPOSITORY_TEST]
- [ ] Commit: `docs: declare runtime_state manifest intentionally untracked live state` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Full validation

Files:
- none (verification task)

- [ ] Run the complete Validation Commands block; expect all probes GREEN [class: REPOSITORY_TEST]
- [ ] Commit: none (verification only) [class: IMPLEMENTATION_REQUIRED]
