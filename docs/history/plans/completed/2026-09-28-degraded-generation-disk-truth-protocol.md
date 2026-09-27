# Plan: Degraded-generation disk-truth protocol for long orchestrator sessions

Backlog origin: `docs/history/backlog/2026-09-27-degraded-generation-disk-truth-protocol.md`
Driving force: code-quality
Plan review record: the staging series docs/reviews/2026-09-28-plan-review-degraded-generation-disk-truth-protocol-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Give every long-running orchestrator session (plan authoring, plan execution, review loops, maintenance turns) a standing disk-truth protocol: a disk-written state record is the session's only trusted state, every precision-critical value is re-derived from disk before use, and a detected garble stops the session before it can corrupt a landing.

- A session that resumes after hours of loop operation (review rounds, fold batches, a budget pause and resume, sub-agent restarts) resumes from a fixed-name state record on disk instead of trusting its own conversation summary, which is the one input source the current gate corpus leaves unvalidated and which two witnessed sessions on 2026-09-27 fabricated from under load.
- A degrading session can no longer quote a plausible-but-false digest, path, flag, or identifier into a new command: the protocol makes disk re-derivation a required step before every precision-critical write, so the failure mode surfaces as a cross-check mismatch instead of a corrupted landing.
- A session that detects a garble or a cross-check mismatch stops before commits, landing, or lock handling and hands off to a fresh session that resumes from the disk record, instead of improvising per-turn mitigations that the resume session cannot inherit.

## Terms

- **Degraded generation:** the witnessed failure mode where a long-running session's own output becomes plausible-but-false under load (invented script paths and flags, a fabricated automation id, misrendered digests), with no tool or infrastructure fault.
- **Disk-truth record:** the fixed-name session state file on disk whose required-fields header block (plan path, recomputed source digest, completed rounds with verdicts, open finding counts, pending next step, last-updated timestamp) is rewritten at each phase boundary while its boundary-event entries stay append-only, and which a long session treats as its only trusted state.
- **Phase boundary:** a loop boundary where the session's next step changes class: review-round launch, fold batch, budget pause or resume, task completion, and the done or landing handoff.
- **Precision-critical step:** any write whose corruption silently invalidates the deliverable: a commit, a landing or squash, lock acquire or release, a digest verification, a manifest or state-file mutation, an automation create or update.
- **Cross-check mismatch:** any disagreement between a value quoted from conversation context and the same value re-derived from disk (sha256 recomputation, directory listing, file read, gate exit code).
- **Fresh-context sub-agent:** a sub-agent launched with no carry-over of the orchestrator's conversation state, whose outputs land as files on disk rather than only in the orchestrator's context.

## Assumptions

- assume the driving force is declared `code-quality` (primary) while the origin item says `correctness`; basis: the plans skill's closed driving-force taxonomy has no correctness tag, and the defect class is the operational discipline quality of the skill corpus's long-session loops, which the taxonomy's code-quality tag covers; the origin's framing is preserved in the Gist and Outcome.
- assume the protocol is prose discipline that binds four duties to existing boundaries, not a new script, hook, or mechanical gate; basis: the origin's own scope note excludes duplicating existing gates, and the mitigations that held under fire in both witnessed sessions were existing mechanical gates plus from-disk re-derivation; the missing piece was the standing protocol binding them per boundary, not a missing detector.
- assume the placement follows the origin's Suggested fix: the plans skill's Plan Quality Gate area (beside the Budget gate) hosts the full protocol; `review-plan`'s Iteration Discipline, `review-loop`'s per-round iteration, `execute-plan`'s setup phase, and the `maintenance` skill's Step 0 carry surface-bound pointers; the repository AGENTS.md Agent-Specific Runtime Safety section carries the one-line rule; basis: the origin names these homes and the dispatching directive names the four long-session skills.
- assume the disk-truth record promotes the existing plan-requirements buffer idiom (`{tmp_dir}/plan-requirements-<slug>.md`; witnesses on disk include `docs/tmp/plan-requirements-ai-harness-friction.md` and `docs/tmp/plan-requirements-codex-execute-plan-runtime-reconciliation.md`) instead of inventing a new file or format; basis: the origin's Suggested fix says to promote the idiom from improvised practice to a required per-round record with a fixed name and required fields; existing gitignored buffers are session scratch and are not migrated. The promotion preserves the Budget gate's append-only event semantics on the same file: the per-boundary update rewrites the required-fields header block and appends one boundary line, never truncating or rewriting existing event records (`budget_pause`, `budget_skip`, and their resume read-backs), and a `.json` machine-state twin (where a resume watcher consumes one) stays the machine-authoritative form for that watcher.
- assume a surface that already owns per-boundary disk artifacts binds the protocol to those artifacts instead of growing a second record: review-loop's staging docs and `.stats.json` sidecars, execute-plan's run manifest and per-task state records, and the maintenance scheduler state file are each their surface's disk-truth records; the fixed-name plan-requirements record is the plans authoring loop's home for the required fields; basis: the origin's "without duplicating existing gates" scope note and the per-surface artifacts already mandated by each skill.
- assume insertions into `agents/skills/plans/SKILL.md` and `agents/skills/execute-plan/SKILL.md` avoid every term of the shared-body forbidden tuple (`codex`, `cursor`, `claude`, `zcode`, `opencode`, `copilot`, `gemini`, `antigravity`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `JSONL`, `MCP`, `--json`) enforced by `test_shared_skill_bodies_remain_runtime_neutral` (scripts/test_execute_plan_runtime.py); basis: the plans skill's shared-body forbidden-term precheck rule (P51 origin 4); the prescribed insertion texts in the tasks below were swept against that tuple at authoring time.
- assume no vendored-sync handoff arises from this plan; basis: this repository is the skill library itself (`agents/skills/` is the canonical layer), so the edited skill files are the canonical copies, and consumer repositories pick them up on their next vendored sync as the Ship-when condition.
Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: a standing disk-truth protocol binds long orchestrator sessions to per-boundary state records, disk re-derivation of every precision-critical value, file-landing fresh-context sub-agents, and a stop-and-hand-off rule on mismatch, because two 2026-09-27 sessions degraded mid-loop and only mechanical cross-checks caught the fabrications before they corrupted a landing.

The four duties (from the origin item, kept verbatim in intent):

1. **Write the record:** at each phase boundary, write the disk-truth record (fixed name, required fields) and treat that record, not the conversation summary, as the only trusted session state.
2. **Re-derive, never quote:** never carry a digest, hex string, path, flag, or identifier from conversation context into a new command; re-derive it first (sha256 tool, directory listing, file read, script help text, listing).
3. **Route generation through fresh context:** generation-heavy review rounds are produced by fresh-context sub-agents whose outputs land as files on disk, and every fold batch is verified against those files, the staging docs are re-read and the digest recomputed before and after the batch; the orchestrator reads the files instead of trusting its own in-loop prose.
4. **Stop on mismatch:** on a detected garble or cross-check mismatch, stop precision-critical steps (commits, landing, lock handling) immediately and hand off to a fresh session that resumes from the disk record.

Examples of the protocol binding to a host loop:

- A resumed authoring session does not quote the plan digest from its continuation summary; it recomputes the sha256 of the plan file, matches it against the latest review sidecar's `source_digest`, and only then launches the next round, the same re-cert discipline the Step 0.5 gate already enforces at execution start, now required at every authoring phase boundary.
- A fold batch launches only after the disk-truth record on disk names the open findings from the staging doc; the orchestrator does not fold "from memory" of the round's findings.
- A maintenance turn takes an automation id from the create response or a fresh listing, never from a prior turn's prose, and its scheduler state file remains the disk record it already is, the protocol binds the re-derivation and stop rules to it rather than adding a second record.
- A landing sequence stops the moment a quoted digest and the recomputed one disagree, leaves the worktree and branch in place, and records the stop for the hand-off session, the hand-off reads the disk-truth record and the staging artifacts, not the degraded session's chat.

## Evaluation Criteria

**Quality dimensions:**

- correctness: the plans skill section states the four duties once in full; each other surface's insertion binds the duties to that surface's own loop, the execute-plan subsection restates the four duties bound to execution boundaries (its readers act on it standalone), while review-plan, review-loop, maintenance, and AGENTS.md reference the protocol without restating its mechanics.
- simplicity: the plans skill section is the only full statement in the authoring loop; the other four surfaces get pointer-sized additions (one bullet or one short paragraph each) except the execute-plan subsection, which is duty-bound restatement sized to one short block; no new scripts, hooks, or state formats beyond the record's fixed name and field list.
- maintainability: the record's fixed name and required fields are defined in one place (the plans skill section) and referenced by path everywhere else; no numeric thresholds or duplicated mechanics that could drift from the existing gates.

**Done when:**

- All six files carry their prescribed insertion (the grep anchors in Validation Commands, presence checks, each succeed).
- `python3 scripts/plan_readiness.py docs/history/plans/2026-09-28-degraded-generation-disk-truth-protocol.md` exits 0.
- `bash scripts/check_maintenance_pins.sh` exits 0 (the maintenance insertion is additive and must not disturb pinned lines).
- The shared-body neutrality test passes (`PYTHONPATH=scripts python3 -m unittest -k shared_skill_bodies scripts.test_execute_plan_runtime`; measured 2026-09-28, pytest is absent from both the project venv and system python3, so the validation uses unittest directly).
- The hygiene scan exits 0 on the changed files (run by the pre-commit gate at landing).

**Ship when:**

- Consumer repositories that vendor these skills pick up the protocol on their next vendored sync (prose only; no deployment step in this repo).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code (skill corpus and repository instructions):**

- `agents/skills/plans/SKILL.md` *(edited: protocol section + record fields in the Plan Quality Gate area)*
- `agents/skills/review-plan/SKILL.md` *(edited: Iteration Discipline pointer paragraph)*
- `agents/skills/review-loop/SKILL.md` *(edited: per-round disk-truth paragraph)*
- `agents/skills/execute-plan/SKILL.md` *(edited: standing-discipline subsection after Step 0.6)*
- `agents/skills/maintenance/SKILL.md` *(edited: Step 0 protocol bullet)*
- `AGENTS.md` *(edited: one-line rule in Agent-Specific Runtime Safety)*

**Tests:**

- none *(this plan prescribes no new or changed test files; the validation commands run existing suites only)*

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `scripts/*`; reason: the protocol is prose discipline over existing mechanical gates, no new gate script, no gate edits (origin scope note).
- `docs/maintenance/document-registry.md` and other registry/doc surfaces; reason: no registry-row-bearing artifact is created or moved by this plan.
- Any other skill under `agents/skills/` not listed above; reason: the origin scopes the protocol to the long-session skills (plans, execute-plan, review-plan, review-loop, maintenance) plus the repository instructions file.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
PLAN="$REPO/docs/history/plans/2026-09-28-degraded-generation-disk-truth-protocol.md"

fail() { echo "VALIDATION FAILED: $1" >&2; exit 1; }

python3 scripts/plan_readiness.py "$PLAN" || fail "plan readiness"

bash scripts/check_maintenance_pins.sh || fail "maintenance pins suite"

( cd "$REPO" && PYTHONPATH=scripts python3 -m unittest -k shared_skill_bodies scripts.test_execute_plan_runtime ) || fail "shared skill bodies no longer runtime neutral"

grep -q 'Degraded-generation disk-truth protocol' "$REPO/agents/skills/plans/SKILL.md" || fail "plans host section"
grep -q 'disk-truth' "$REPO/agents/skills/review-plan/SKILL.md" || fail "review-plan pointer"
grep -q 'disk-truth' "$REPO/agents/skills/review-loop/SKILL.md" || fail "review-loop pointer"
grep -q 'Degraded-generation disk-truth protocol' "$REPO/agents/skills/execute-plan/SKILL.md" || fail "execute-plan subsection"
grep -q 'disk-truth' "$REPO/agents/skills/maintenance/SKILL.md" || fail "maintenance bullet"
grep -q 'disk re-derivation\|re-derive every digest' "$REPO/AGENTS.md" || fail "AGENTS.md rule"

echo "ALL VALIDATIONS GREEN"
```

## Task 1: Plans skill, host the protocol beside the Budget gate

Files:
- `agents/skills/plans/SKILL.md`

- [x] In the `## Plan Quality Gate` section, insert immediately after the `**Budget gate:**` paragraph and before the `Before finalizing a new or updated plan, run the `review-plan` skill as a sub-agent:` line a new paragraph titled `**Degraded-generation disk-truth protocol:**` carrying the four duties bound to the authoring loop's phase boundaries (each review-round launch, each fold batch, each budget pause or resume, and the done handoff is a phase boundary); the paragraph states that the disk record, not the conversation summary, is the only trusted session state across compactions, budget pauses, and resumes.
- [x] The same paragraph defines the disk-truth record: fixed name `{tmp_dir}/plan-requirements-<slug>.md` (promoting the existing buffer idiom), updated at each phase boundary, with the required fields in a header block: plan path; source digest recomputed at record time (never quoted from context); completed rounds with their verdicts; open finding counts with the path of the authoritative staging artifact they summarize (the staging series stays the finding ledger of record; the counts are a pointer, not a second ledger); pending next step; last-updated timestamp. The header-block update is the only in-place rewrite: boundary-event entries on the same file (the Budget gate's `budget_pause` / `budget_skip` records and their resume read-backs) stay append-only and are never truncated or rewritten by the update, and a `.json` machine-state twin (where a resume watcher consumes one) stays the machine-authoritative form for that watcher. A fresh or resumed session reads this record to re-enter the loop. A surface that already owns per-boundary disk artifacts (review-loop staging docs and sidecars, execute-plan run manifests and per-task state records, the maintenance scheduler state file) binds the protocol to those artifacts instead of growing a second record; the fixed-name record is the plans authoring loop's home.
- [x] The same paragraph binds duty 2 (re-derive, never quote: every digest, path, flag, or identifier entering a new command is re-derived from disk first), duty 3 (review rounds are produced by fresh-context sub-agents whose findings land in the staging docs and sidecars, the loop's existing shape, and every fold batch is verified against those files, re-reading the staging doc and recomputing the digest before and after the batch), and duty 4 (on a detected garble or cross-check mismatch, stop before any precision-critical step, commits, landing, lock handling, record the stop in the disk-truth record, and hand off to a fresh session that resumes from it).
- [x] Sweep the inserted text against the shared-body forbidden tuple (see Assumptions); no tuple term appears.
- [x] Run → expect GREEN: `grep -q 'Degraded-generation disk-truth protocol' agents/skills/plans/SKILL.md`
- [x] Run → expect GREEN: `PYTHONPATH=scripts python3 -m unittest -k shared_skill_bodies scripts.test_execute_plan_runtime`
- [x] Append the plan-relative path of the edited file to the session's deliverables ledger per the plans skill writing rule.
- [x] Commit: `feat: plans skill hosts degraded-generation disk-truth protocol`

## Task 2: Review-plan skill, Iteration Discipline pointer

Files:
- `agents/skills/review-plan/SKILL.md`

- [x] In the `## Iteration Discipline (plans skill gate)` section, add one short paragraph after the numbered list (before `## Reconciliation gate`) so no numbered item is renumbered: long review loops run under the plans skill's degraded-generation disk-truth protocol, each round launch and each fold batch updates the disk-truth record, digests and sidecar values entering round commands are re-derived from the files on disk (the sidecar `source_digest` is recomputed, not quoted), worker findings land in the staging docs, and a detected garble or cross-check mismatch stops the loop before the next panel launch.
- [x] Run → expect GREEN: `grep -q 'disk-truth' agents/skills/review-plan/SKILL.md`
- [x] Commit: `feat: review-plan iteration discipline binds disk-truth protocol`

## Task 3: Review-loop skill, per-round disk-truth paragraph

Files:
- `agents/skills/review-loop/SKILL.md`

- [x] In the `## One iteration` section, add one short paragraph after the `**Context budget checkpoint (round boundary):**` paragraph (before `## Staging doc (required every round)`): each round boundary updates the loop's disk-truth record per the plans skill's degraded-generation disk-truth protocol (the round's staging doc and its `.stats.json` sidecar are the per-round disk artifacts; findings are read from those files, never from the loop's own prose), and a detected garble or cross-check mismatch stops the loop before the next round's fixes.
- [x] Run → expect GREEN: `grep -q 'disk-truth' agents/skills/review-loop/SKILL.md`
- [x] Commit: `feat: review-loop rounds read findings from disk artifacts`

## Task 4: Execute-plan skill, standing session discipline subsection

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Insert a new subsection `### Degraded-generation disk-truth protocol (standing session discipline)` between the `### Step 0.6: Predecessor verification (hard gate, before Phase 1)` block and the `## Configuration (from facts document)` heading. The subsection binds the four duties to the execution loop: task completions, budget pause or resume, and the landing sequence are phase boundaries (duty 1, the run manifest and the per-task state records are the disk record; the orchestrator re-reads them after any interruption instead of trusting context); duty 2, every digest, path, flag, or identifier entering a landing or manifest command is re-derived from disk first (sha256 through the branch ref, directory listing, validator output); duty 3, task workers and review rounds already run as fresh-context sub-agents writing files; keep it that way for any new generation-heavy step; duty 4, on a detected garble or cross-check mismatch, stop before the next commit, landing, or lock operation and record the stop so a fresh session can resume from the disk records.
- [x] Sweep the inserted text against the shared-body forbidden tuple (see Assumptions); no tuple term appears.
- [x] Run → expect GREEN: `grep -q 'Degraded-generation disk-truth protocol' agents/skills/execute-plan/SKILL.md`
- [x] Run → expect GREEN: `PYTHONPATH=scripts python3 -m unittest -k shared_skill_bodies scripts.test_execute_plan_runtime`
- [x] Commit: `feat: execute-plan binds disk-truth protocol to session discipline`

## Task 5: Maintenance skill, Step 0 protocol bullet

Files:
- `agents/skills/maintenance/SKILL.md`

- [x] In `### Step 0: context load`, append one final bullet binding the protocol to scheduler turns: long or resumed scheduler turns run under the plans skill's degraded-generation disk-truth protocol, the scheduler state file is the turn's disk-truth record (already mandated by the state-first duties), every automation id, digest, or path entering a primitive call or state edit is re-derived from the listing, the state file, or the payload copy on disk (never quoted from conversation context), and on a detected garble or cross-check mismatch the turn stops before any mutating emission and leaves the stop recorded through the standing state writers (`rearm_note`, `turn_error`).
- [x] Run → expect GREEN: `grep -q 'disk-truth' agents/skills/maintenance/SKILL.md`
- [x] Run → expect GREEN: `bash scripts/check_maintenance_pins.sh`
- [x] Commit: `feat: maintenance turns bind disk-truth protocol in Step 0`

## Task 6: Repository instructions, one-line agent-safety rule

Files:
- `AGENTS.md`

- [x] In `## Agent-Specific Runtime Safety`, append one bullet: `- A value quoted from conversation context is not evidence: before any precision-critical step (commit, landing, lock handling, digest verification), re-derive every digest, path, flag, or identifier from disk, and stop on a cross-check mismatch until it is resolved.`
- [x] Run → expect GREEN: `grep -q 'disk re-derivation\|re-derive every digest' AGENTS.md`
- [x] Commit: `feat: agent-safety rule for disk re-derivation`

## Disposition

Executed 2026-09-28: all six surfaces landed (plans, review-plan, review-loop, execute-plan, maintenance skills; AGENTS.md rule), validation block green, execution review r1 and focused re-cert r5 ready=yes zero blocking, squash main ad89376b. One non-semantic plan correction during the run aligned the Validation Commands AGENTS.md grep with Task 6 alternation (a1f1d65e); the r4 deferred Low residual carries unchanged. Origin item folded into this completed plan and deleted from the backlog per the plans completion step.
