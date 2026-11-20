# Plan: Authoring-run continuation ownership order

Backlog origin: docs/history/backlog/2026-11-04-authoring-continuation-owner-attribution.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-authoring-continuation-owner-attribution-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1.75h total, largest task 1h
Executed: yes (pre-squash tip 141dbb9055, landing 6b97eb59bf)
Authoring claim: 2026-11-04-authoring-continuation-owner-attribution.md (session sess_61c999ba-9ade-4347-b200-decc795184d0)

## Terms

- Authoring-run continuation: a session resuming, mutating, or completing an existing authoring run it did not start in this session; the run's plan file, claim file, worktree, or authoring branch already exist when the session enters.
- Durable provenance: the plan header's permanent `Authoring claim:` line, written once at the first plan-file write and unchanged through certification, landing, and archival; it names the originating run's session.
- Current-ownership record: the live claim file's `session:` frontmatter line, already the key the AUTHORING CLAIM procedure's ownership re-checks use for refresh and delete rights.
- Placement evidence: the run worktree registration and the `authoring/<claim-file-stem>` branch; they locate the run's work and never prove who owns it.
- Ownership order: the continuation source-of-truth precedence: durable provenance first, current-ownership record second, placement evidence never.
- Owner-recognized transfer: authorization to continue that comes from either the operator's explicit transfer direction recorded beside the run, or the claim lifecycle's own hand through the stale-foreign-claim takeover path; never from conversation context or the user's request to finish the plan.
- Ambiguous ownership: the state where none of the ownership order's records names this session and no owner-recognized transfer exists.
- Preserve-and-route: the ambiguous-ownership outcome: the run's work stays untouched and the session reports the provenance evidence and routes to the transfer or operator decision.
- Cadence period: the 2-hour freshness bound shared by the claim gate, the G1a discovery arm, and the freeze rule.

## Why

A session directed to complete an authoring plan treated the user's request and the claim file it found as proof it owned a run whose plan header named another originating session, continued the work, and was corrected by the operator; the preserved branch carried the other run's work. The attribution lesson that covers exactly this read surface (`docs/maintenance/development_lessons.md` #229, attribute a run through the session store's message payload) was available but not applied, because no continuation-entry rule orders the durable records or binds continuation to them. The claim lifecycle already protects against concurrent writers and decays stale claims; what it does not own is the entry boundary where a new session picks up an existing run.

## Gist & Examples

TLDR: the plans skill gains an authoring-run continuation ownership rule that orders the run's durable provenance records and binds continuation to the recorded owner or an owner-recognized transfer, preserving ambiguous runs and routing them to the operator, because a user request to finish a plan is authorization for work, never proof of which run's records this session owns (code-quality).

Before (today): a session asked to complete an existing authoring plan reads the plan, finds a claim file and worktree, and continues; nothing at the continuation entry boundary requires the session to compare its own identity against the plan header's originating-session marker or the claim file's `session:` line, and a wrong attribution is stopped only by an operator correction after the foreign run's work has already been mutated.

After (this plan): before resuming or mutating an existing authoring run, the session proves ownership from the ownership order: the plan header marker names the originating run's session, the live claim's `session:` line names the current claim owner, and the worktree and branch are placement evidence only. Continuation proceeds when this session matches the marker, holds the current claim, or carries an owner-recognized transfer; otherwise the session preserves the run's work untouched, reports the provenance evidence, and routes to the transfer or operator decision per self-heal Recovery step 5, with lesson #229's session-store attribution as the tie-breaker on that ambiguous path when the surfaces disagree.

Example: a session is asked to finish a plan whose header carries `Authoring claim: 2026-11-04-example.md (session sess-other)`. The claim file found beside it names `sess-other` too and is fresh. Under this plan the session does not adopt the run: it reports the marker and claim session ids, the claim's `updated:` timestamp, and the worktree and branch, preserves every byte, and asks the operator for the transfer decision instead of continuing.

Edge cases: a continuation by the recorded owner is unchanged and needs no extra ceremony; a claim stale past one cadence period still takes the existing stale-foreign-claim takeover path, which is one of the recognized transfer forms; the fresh-foreign-claim refusal and the AUTHORING CLAIM ownership re-checks are preserved byte-for-byte; claim discovery for parallel-origin races and execute-plan resume selection stay in their separate contracts; a session-store attribution (lesson #229) resolves which session owns a worktree when the marker and claim disagree or a surface is missing, it never overrides a matching pair.

## Outcome

A session that enters an existing authoring run proves ownership from the run's durable records before touching anything, and an ambiguous run is preserved and routed instead of adopted.

- A plan whose durable provenance names another session is never continued by an unrelated session on conversation context alone; the session preserves the work and reports the evidence needed for the transfer decision.
- The three pass conditions (marker match, current-claim hold, owner-recognized transfer) are named in the owning skill text and pinned by regression coverage.
- The existing concurrent-writer refusal, stale-claim takeover, and mid-run ownership re-checks are preserved unchanged.
- Gate delta: none counted (protocol text at an existing entry boundary; the rule adds no refusal class, hard gate, fence, protocol layer, or schema field; its unmet outcome routes to the existing self-heal Recovery step 5 decision point, which already owns ambiguous-ownership asks, so no new stop surface is added and none is removed; the origin's Class: line is fence-class and this plan adds no fence, so no origin-cited completed failure is consumed; the origin's rejected alternatives record the new-ledger and blocking-validator arms as rejected for lack of a witnessed incident).

## Assumptions

- assume the plan header's permanent `Authoring claim:` line is the run's durable provenance; basis: the plans skill Phase 0 permanent-provenance rule (written once at the first plan-file write, unchanged through certification, landing, and archival).
- assume the live claim file's `session:` line is the current-ownership record; basis: the AUTHORING CLAIM procedure's ownership re-checks already key every refresh and delete to it.
- assume no new machinery; basis: the origin's Machinery admission record and its rejected new-ledger and new-validator alternatives, plus the origin's suggested direction preferring cross-references and a source-of-truth order.
- assume the stale-foreign-claim takeover is a legitimate transfer form; basis: the AUTHORING CLAIM procedure already routes a claim stale past one cadence period to delete-then-create, recording the takeover.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the ownership order names each record's role, the gate names exactly three pass conditions and one preserve-and-route outcome, and each is pinned inside its owning span by the regression suite
- minimality: no new gate, validator, lock, ledger, or required ceremony; the preserved refusal, takeover, and ownership re-check spans are pinned byte-for-byte
- observability: the preserve-and-route report names the provenance evidence needed to continue (marker session, claim session and `updated:`, worktree, branch)

**Done when:**
- the new spans exist with their normative tokens in `agents/skills/plans/SKILL.md` and `agents/skills/self-heal/SKILL.md`
- the regression suite passes and the persistence pins over the preserved spans hold
- the maintenance pins suite, the skill-text budget gate, the runtime-scope suite, the duplication gate, the public-hygiene scan, and the em-dash added-lines gate all exit 0

**Ship when:**
- none (repository-internal protocol text; no deployed or cross-team condition)

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md` (Task 2)
- `agents/skills/self-heal/SKILL.md` (Task 3)

**Tests:**
- `scripts/test_authoring_continuation_ownership.py` (Task 1) *(new)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/maintenance/development_lessons.md`; reason: the lesson corpus is cited read-only, lesson #229 already records the attribution rule, and no lesson edit is in scope
- `agents/skills/maintenance/template-authoring.md`; reason: the AUTHORING CLAIM procedure is preserved unchanged and pinned as a persistence witness, and the continuation entry boundary is owned by the plans skill's Phase 0
- `agents/skills/execute-plan/SKILL.md` and `agents/skills/execute-plan/worktree-first.md`; reason: execute-plan resume selection is a separate contract per the origin's scope boundary

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_authoring_continuation_ownership.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_maintenance_runtime_scope.py -q
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_skill_text_duplication.py -q
python3 scripts/skill_text_budget.py --check
bash scripts/check_maintenance_pins.sh
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base HEAD main)"
```

Validation preamble (authoring-time record, rule 29):
- skill_text_budget --check over the current tree: exit 0, OUTCOME: pass, 3 pre-existing advisory breaches in maintenance module files, none in the two edited files (recorded 2026-11-06).
- check_maintenance_pins.sh over the current tree: exit 0 (recorded 2026-11-06).
- scan-public-hygiene.sh over the current tree: exit 0 (recorded 2026-11-06).
- check-no-em-dash.sh touched over the plan bytes (authoring-time self-check form for a new file): exit 0 (recorded 2026-11-06).
- test_maintenance_runtime_scope.py and test_skill_text_duplication.py over the current tree: exit 0 (recorded 2026-11-06).
- scripts/test_authoring_continuation_ownership.py is stage-scoped to post-Task 1: the file does not exist at authoring time, so the interim tree cannot run this command (rule 16 staging).
- plan_readiness.py --pre-round over the plan bytes: exit 0, OUTCOME: pass, structural checks clean, zero warnings (recorded 2026-11-06 after three over-cap and trailer violations were fixed at composition time and two advisory files-coverage warnings were de-quoted).

### Task 1: Regression coverage pinning the continuation ownership rule and the preserved claim-duty spans

Context surface: the plan's Terms and this task.

Files:
- `scripts/test_authoring_continuation_ownership.py` *(new)*

Primary class anchors:
- `Authoring-run continuation ownership` in `agents/skills/plans/SKILL.md`
- `Recovery` in `agents/skills/self-heal/SKILL.md`

- [x] New unittest suite following the stated convention of the raced-pick regression suite (scripts/test_authoring_raced_pick_continuation.py; a Markdown policy pinned by normative tokens inside the owning span): extract the plans-skill Phase 0 paragraph beginning `**Authoring-run continuation ownership` with a paragraph-extraction helper that fails closed when the anchor paragraph is absent [class: REPOSITORY_TEST]
- [x] The same suite asserts, inside that paragraph span, the order tokens: `durable provenance`, `current-ownership record`, and the placement span `placement evidence only and never proof of ownership` [class: REPOSITORY_TEST]
- [x] The same suite asserts, inside that paragraph span, the gate tokens: the marker-match condition, the current-claim condition, the span `owner-recognized transfer`, and the preserve-and-route span `preserves the run's work untouched` [class: REPOSITORY_TEST]
- [x] The same suite asserts, inside that paragraph span, the routing and tie-breaker tokens: the ambiguous-path scoping span `no pass condition holds`, the self-heal citation `Recovery step 5`, the lesson citation development lesson #229, and the separate-contracts span `separate contracts` [class: REPOSITORY_TEST]
- [x] The same suite extracts the self-heal Recovery step 5 list item (the item beginning `5. If no safe action is possible`) and asserts, inside that span, the cross-reference tokens `authoring-run continuation` and `continuation ownership rule` [class: REPOSITORY_TEST]
- [x] The same suite pins the ownership re-check span `mutate it only while its session: line still names this session's id` as a persistence witness expected to pass at RED, scoped to the maintenance template's AUTHORING CLAIM paragraph (the paragraph beginning `AUTHORING CLAIM, the claim file this session writes`, agents/skills/maintenance/template-authoring.md) [class: REPOSITORY_TEST]
- [x] The same suite pins two further persistence witnesses expected to pass at RED, scoped to the maintenance template's pre-work gate paragraph (the paragraph beginning `Before writing anything: verify no merge or rebase is in progress`): the refusal span `refuse to start: stand down and write nothing` and the takeover token `Stale-foreign-claim takeover` [class: REPOSITORY_TEST]
- [x] The same suite pins two further persistence witnesses expected to pass at RED: the plans-skill Phase 0 authoring-claim token `create-if-absent noclobber create`, and the self-heal step 5 tail `Do not treat elapsed time or the user's silence as authorization` [class: REPOSITORY_TEST]
- [x] Run → expect RED: the suite fails at the current tree because every span-scoped assertion of a new-rule token fails inside the not-yet-existing owning spans; every persistence pin is expected to pass at RED [class: REPOSITORY_TEST]
- [x] Commit: `test: pin authoring continuation ownership tokens` [class: IMPLEMENTATION_REQUIRED]

### Task 2: The continuation ownership rule in the plans skill's Phase 0

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/plans/SKILL.md`

Primary class anchors:
- `Authoring-run continuation ownership` in `agents/skills/plans/SKILL.md`

- [x] Insert one new bolded paragraph titled `**Authoring-run continuation ownership (entry boundary):**` in Phase 0, directly after the `**Active-plan referral placement:**` paragraph and directly before the `**Entry freeze (entry-keyed authoring runs):**` paragraph, with the tail anchor `**Entry freeze (entry-keyed authoring runs):**` verified verbatim immediately after the insertion point so no tail bytes are dropped (rule 40) [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph states the ownership order: the plan header's permanent `Authoring claim:` line as durable provenance naming the originating run's session, the live claim file's `session:` line as the current-ownership record, and the worktree and authoring branch (named per the authoring/<claim-file-stem> convention) as placement evidence only and never proof of ownership [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph states that user authorization to work on a plan is a separate fact from run ownership and never substitutes for the ownership proof [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph states exactly three pass conditions: this session's id equals the header marker's session id; the live claim's `session:` line names this session; or an owner-recognized transfer exists, being either the operator's explicit transfer direction recorded beside the run or the claim lifecycle's own hand through the stale-foreign-claim takeover path (a claim stale past one cadence period, 2 hours) [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph states the ambiguous-ownership outcome: the rule fires at the continuation entry, before this session's own claim or worktree provisioning for the target; when it fires, the session preserves the run's work untouched (no adoption, no mutation of the run's records) and reports the provenance evidence needed to continue (marker session id, claim session id and `updated:` timestamp, worktree path, branch name) [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph routes the ambiguous outcome to the owner-recognized transfer or the operator decision per the self-heal skill's Recovery step 5 [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph scopes the tie-breaker to the ambiguous path: when no pass condition holds and the durable surfaces disagree or one is missing, attribute the run through the session store's message payload per development lesson #229 in the project lessons corpus to establish the evidence for the transfer or operator decision; a held pass condition is never re-adjudicated by the session store, and a session-store attribution never overrides a matching marker-and-claim pair [class: IMPLEMENTATION_REQUIRED]
- [x] The paragraph closes by holding the adjacent contracts: claim discovery for parallel-origin races and execute-plan resume selection stay within their separate contracts, this rule owning only the continuation entry boundary [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 1 suite's new-span assertions pass; the persistence pins still pass; the whole-suite state at this task point is Task 1 plus Task 2 green with the self-heal span assertion (Task 1's step-5 item) still RED until Task 3 lands [class: REPOSITORY_TEST]
- [x] Commit: `docs: bind authoring-run continuation to the durable ownership order in plans Phase 0` [class: IMPLEMENTATION_REQUIRED]

### Task 3: The self-heal Recovery step 5 cross-reference

Context surface: the plan's Terms and this task.

Files:
- `agents/skills/self-heal/SKILL.md`

Primary class anchors:
- `Recovery` in `agents/skills/self-heal/SKILL.md`

- [x] Append one sentence to the Recovery step 5 list item, directly after the sentence ending `Do not treat elapsed time or the user's silence as authorization.` with that tail verified verbatim immediately after the insertion point so no tail bytes are dropped (rule 40) [class: IMPLEMENTATION_REQUIRED]
- [x] The appended sentence states: an authoring-run continuation whose durable provenance names another session is ambiguous ownership, verify the plans skill's Phase 0 authoring-run continuation ownership rule before any step 3-4 workaround, and preserve the run's work while the owner-recognized transfer or operator decision is pending [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the Task 1 suite passes in full (new-span assertions and persistence pins); the interim whole-suite state before this task carried the self-heal span assertion RED per Task 2's gate line [class: REPOSITORY_TEST]
- [x] Commit: `docs: cross-reference the continuation ownership rule from self-heal recovery` [class: IMPLEMENTATION_REQUIRED]

## Disposition of executed deltas

Executed 2026-11-07 under the operator one-shot exec mandate automation-bcb796f1 (max 1, stop after 1st), resumed from the 2026-11-07 03:00/04:00 quota-walled runs' branch (Tasks 1-3 committed 17c9295b1/3f8996352/85474882d, not redone); stale foreign claim taken over and re-registered. Task deltas landed; the review rounds folded three wording deltas onto the landed spans, recorded here so the checkbox text and the landed bytes stay reconcilable: the entry boundary's takeover parenthetical "(a claim stale past one cadence period, 2 hours)" is carried by the AUTHORING CLAIM procedure of record instead of restated; the no-pass routing reads "routing to the operator decision (authorizing a transfer or declining)"; and a closed-runs out-of-scope clause (a run with no claim file, no run worktree, and no standing authoring branch remaining proceeds per its own contract: the update-round rule, Create vs update completion, or Active-plan referral placement) scopes the boundary to standing live state. The self-heal step 5 sentence classifies ambiguous ownership solely by the plans rule's pass conditions (review r1 finding F2 fix), and both skills record the pairing under Integration Points. r1 full five-worker panel 15 raw 11 staged, one High blocking cold-continuation trap folded at de153646e; r2 focused delta ready=yes zero blocking at digest b38adde7, three non-blocking residuals folded verbatim at 1d1274a59; review records .ai-playbook/reviews/2026-11-07-authoring-continuation-owner-attribution-code-review-r1.md and -r2.md validated OUTCOME: pass. Non-blocking deferred residuals: raced-pick entry classification (r1 F3), marker-match-outlives-takeover (r1 F4), pin-strengthening set (r1 F5/F8/F9), PreservedSpansTest redundancy (r1 F11, overflow).
