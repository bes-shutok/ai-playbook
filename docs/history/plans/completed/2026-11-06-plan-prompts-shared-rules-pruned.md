# Plan: Restore the shared prompt-log standing rules preamble

Backlog origin: docs/history/backlog/2026-11-05-plan-prompts-shared-rules-pruned.md
Secondary origin: docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md (item 2 only)
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-06-plan-review-plan-prompts-shared-rules-pruned-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 2.5h total, largest task 1h
Executed: yes (2026-11-08, execution landing of branch exec-plan-prompts-shared-rules; pre-squash branch tip ff800c026)

## Terms

- Standing rules block: the shared prose contract of `docs/history/backlog/PLAN-PROMPTS.md` (twelve rule bullets: Order, Prune rule, Coverage and removal rule, Freeze rule, Not a backlog item, targeted-section edits, drift re-read and retry, same-turn commit, Write boundary rule, repo-relative paths, prompt-not-dispatch, receipt vocabulary), removed from its post-first-entry position by commit `dd1803d2c8` on 2026-11-05 and re-added by `838972c99` byte-identical but still inside a dispatch entry's heading range (the first entry's range at current HEAD).
- Preamble: the region of the rolling log between the title line and the first `## ` entry heading; content there is outside every entry range, so no entry-range prune can remove it.
- Entry range: the span from one `## <slug>` entry heading to the next `## ` heading (or end of file); the unit a prune removes.
- Own-entry binding: the coverage binding where a plan's filename stem (date prefix removed) equals an entry slug, the entry's `Frozen:` witness names the plan's authoring claim, and the entry's `Origins:` includes the plan's source backlog origin.
- Write boundary rule: the restored rule that a primary-checkout log write acquires the primary done lock and commits through the runner's ref-bound captured-tree transaction; worktree-branch log writes stay isolated under the existing merge-lock guard instead.
- Rolling log: either tracked prompt-queue file (`PLAN-PROMPTS.md` or `EXEC-PROMPTS.md`); an ordered dispatch surface, not a backlog item.
- Receipt: the `PLAN-PROMPTS-PRUNE: <slug> -> <witness>` line recording an entry removal; the Prune rule pins receipt preservation across every prune.
- Scope arm: one numbered implementation option recorded in a log entry's Scope arms list, each carrying its own rejection or selection rationale.
- Entry freeze paragraph: the `agents/skills/plans/SKILL.md` paragraph that owns authoring-run freeze placement and cites the log's Freeze rule.
- Pins suite: `scripts/check_maintenance_pins.sh`, the repository's warning-only presence-grep suite over pinned skill-text spans.

## Why

The rolling log's shared write, freeze, prune, and recovery contract was pruned away together with the first dispatch entry it sat inside (`dd1803d2c8`), re-added byte-identical by `838972c99` but still inside the first entry's heading range, and the skills that consume it (investigate, plans, maintenance) cite rule labels whose shared block sits one first-entry prune away from a third loss. Restoring the block in the preamble puts the contract where no entry-range prune can reach it and makes the dangling citations resolve against a durable home.

## Gist & Examples

TLDR: Move the log's Standing rules block into the preamble region where entry-range prunes cannot reach it, and repoint the consumers that cite its rule labels, because the block sits one first-entry prune away from being lost a third time.

Before: commit `dd1803d2c8` pruned the `stacked-pr-review-size-policy` entry and removed the `Standing rules:` block with it; `838972c99` re-added the block byte-identical but inside the `plan-prompts-shared-rules-pruned` dispatch entry's heading range (the exact rejected shape the entry's scope arm 3 records). `agents/skills/investigate/SKILL.md`, `agents/skills/plans/SKILL.md`, and `agents/skills/maintenance/` cite the `Write boundary rule`, `Freeze rule`, `Prune rule`, and `Coverage and removal rule` labels; the block's only copies sit inside an entry range, so the next first-entry prune removes the shared contract again.

After: the log preamble carries the block, byte-identical to the pre-prune text, headed by one orientation line naming it the canonical home outside every entry range, and no copy remains inside any entry range; a regression in the log's own suite proves that pruning the first dispatch entry preserves the preamble bytes, pins the placement and uniqueness invariants, and pins the anti-shape; the consumers' citations resolve against the restored block, and the older bundle's freeze-placement citation residual (item 2) resolves because the restored Freeze rule carries the placement clause.

Example: an authoring landing prunes its own frozen entry; the removal range starts at the entry heading, so the preamble block above it stays untouched, and the prune audit accepts the removal with its receipt exactly as before the loss.

## Outcome

The rolling log's shared contract is durably readable at the source every consumer cites, and no entry-range operation can remove it.

- A writer following `agents/skills/investigate/SKILL.md`, `agents/skills/plans/SKILL.md`, or the maintenance monitor duties to the log finds the Standing rules block in the preamble, with all twelve rule bullets present exactly once in the whole file and none inside any entry range.
- Pruning the first dispatch entry leaves the preamble bytes untouched, proven by a regression test that reads the real log bytes, simulates the documented prune with its receipt preservation, and re-verifies the invariant after the run's own landing.
- The freeze-placement citation residual (`2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md` item 2) resolves: the restored Freeze rule carries the placement clause the Entry freeze paragraph cites.

Gate delta: none (relocates previously lost prose contract bytes and adds test-only coverage in an existing suite; no gate, fence, refusal path, schema field, protocol layer, or blocking review-layer duty is added or removed).

## Assumptions

- The canonical text to relocate is the `Standing rules:` block verbatim from the immediate pre-prune revision of the log (`git show dd1803d2c8^:docs/history/backlog/PLAN-PROMPTS.md`, the block the removal commit carried away), twelve bullets from `Order:` through the receipt-vocabulary bullet; the identical bytes are also readable in the in-range copy at current HEAD, so the move needs no historical recovery when HEAD carries them; basis: verified directly at `dd1803d2c8^` during this plan's authoring session, and the log entry's Orientation line names a pre-prune revision (`8830daca17`) whose block bytes are identical to `dd1803d2c8^`.
- One orientation line is added above the relocated block naming it the canonical home outside every dispatch-entry range; the rule bullets themselves stay byte-identical to the pre-prune text; basis: the entry's Scope arm 1 ("preserve the current canonical rule text and keep entry-range pruning disjoint from it") and the discoverability gap the row records.
- The preamble placement (block after the title line, before the first `## ` entry heading, no `## ` headings of its own, exactly one copy in the whole file) is the design that makes entry-range prunes structurally unable to remove it; the placement failure has now repeated (`dd1803d2c8` removed the block, `838972c99` re-added it into an entry range), recorded here as the second witness; the no-new-gate posture stands on the entry's recorded scope arms with this plan's regression as the named coverage, and any future checker remains gated on a post-move repeat; basis: the origin row's Machinery admission line and the two witnessed commits.
- The older bundle's item 2 is in scope because the restored Freeze rule carries the placement clause the Entry freeze paragraph cites ("goes directly under the entry's heading"); verified in the pre-prune text during authoring; basis: the log entry's Scope-line resolution rule ("include the older residual's item 2 only if the canonical Freeze rule can resolve its placement citation"). Items 1 and 3 through 6 of that bundle stay open and are out of scope.
- Scope extensions (grilled): none proposed.

Decision points requiring a grill: preamble placement inside the log (scope arm 1) over a separate shared instruction file (scope arm 2) - resolved by the entry's recorded scope arms, which select arm 1 as recommended and record arm 2's discoverability trade-off; standing authorization receipt, 2026-11-06, affected sections: Terms, Assumptions, Tasks 1 through 3.
Sources inspected: not a tracker-linked request.

## Standing constraints

- `docs/history/backlog/PLAN-PROMPTS.md` is a rolling log: the write discipline a task must follow depends on where the write commits. A log write that commits in the primary checkout (a monitor prune, a freeze, a primary-placement checkpoint) acquires the primary done lock and commits through the runner's ref-bound transaction. This run's Task 2 writes the log from the execution run's ad-hoc worktree, so its bytes commit on the run's authoring branch under the existing merge-lock guard (the restored Write boundary rule's own worktree arm) and reach the default branch through the run's landing; the primary-checkout transaction is reserved for primary-checkout log writers.
- The drift-recovery fallback for an entry write (retry once from the fresh read, then a pure append at end of file) is entry-shaped and never applies to the preamble move: on drift after the single retry, Task 2 aborts and reports the exact intended preamble bytes instead.
- Ordering: if a monitor or peer prune removes the first dispatch entry (and the in-range block copy) before Task 2 executes, the task proceeds unchanged; the relocation source (`dd1803d2c8^`, an ancestor of HEAD) does not depend on the entry surviving, and Task 1's RED observation is re-derived from the then-current committed bytes.
- Authoring-landing state: this plan's own authoring landing pruned only its entry's prose and kept the former range's receipts and the Standing rules block, so at execution the block may already sit ahead of every entry heading without its orientation line; Task 2 then adds the orientation line directly above the block (no relocation), and Task 1's orientation-line pin supplies the RED.
- Skill-text edits follow the repository's anti-growth rules: the consumer repoints are one-line pointer corrections, never rule restatements; no rule text is duplicated into a skill.
- Every changed file passes the public hygiene scan and the em-dash added-lines gate before the run's landing.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the relocated block's bullets are byte-identical to the pre-prune text (diff-verified against `dd1803d2c8^`), and every rule label the consumers cite resolves in the preamble.
- Durability: the regression suite fails when the preamble block is absent, duplicated, misplaced after an entry heading, or removed by a first-entry prune, including after the run's own landing.
- Minimalism: consumers are repointed by citation, never by restating rule text; no new checker, gate, or module lands.

**Done when:**
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_prompt_log_origins.py -q` passes with the new regression tests green and the collected count equal to the suite's test-definition count.
- The real `docs/history/backlog/PLAN-PROMPTS.md` carries exactly one Standing rules block, in the preamble region, at its HEAD-committed bytes.
- The public hygiene scan and em-dash added-lines gate exit 0 over the run's changed files; `bash scripts/check_maintenance_pins.sh` exits 0 over the tree with the pin-span updates landed.

**Ship when:**
- No external conditions; the work is entirely repository-internal.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 2)
- `docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md` (Task 3)
- `agents/skills/investigate/SKILL.md` (Task 3)
- `agents/skills/plans/SKILL.md` (Task 3)
- `agents/skills/maintenance/decisions.md` (Task 3)
- `agents/skills/maintenance/zcode.md` (Task 3)
- `scripts/check_maintenance_pins.sh` (Task 3)

**Tests:**
- `scripts/test_check_prompt_log_origins.py` (Task 1) *(new tests and a docstring scope note only; no existing test's semantics change)*

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/guards.md` and `agents/skills/maintenance/prompt-templates.md`; reason: the older bundle's item 1 (stale AUTHORING CLAIM pointer), explicitly kept open by the entry.
- `agents/skills/plans/SKILL.md` primary-placement freeze citation (the Completion-claims paragraph); reason: the older bundle's item 3, explicitly kept open.
- `scripts/check_prompt_log_origins.py`; reason: the entry rejects new checker machinery; the audit script's semantics stay unchanged.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_check_prompt_log_origins.py -q
bash scripts/scan-public-hygiene.sh
bash scripts/check-no-em-dash.sh added-lines --base <merge-base>
bash scripts/check_maintenance_pins.sh
```

### Task 1: Regression proves the preamble placement invariant (TDD RED)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/test_check_prompt_log_origins.py` *(new tests appended to the existing suite, plus the module docstring scope note)*

Primary class anchors:
- `TestPromptLogStandingRulesPreamble` in `scripts/test_check_prompt_log_origins.py`

- [ ] `TestPromptLogStandingRulesPreamble` delivers the placement regression: given the real committed `docs/history/backlog/PLAN-PROMPTS.md` bytes read through `git show HEAD:<path>`, expects exactly one Standing rules block in the whole file, located in the preamble region (after the title line, before the first `## ` heading), and no `- Order:` bullet bytes anywhere after the first `## ` heading [class: REPOSITORY_TEST]
- [ ] `TestPromptLogStandingRulesPreamble` delivers the label-set regression: given the same committed bytes, expects the preamble block to carry all twelve rule bullets asserted as their leading-label set (Order, Prune rule, Coverage and removal rule, Freeze rule, Not a backlog item, targeted-section edits, drift re-read and retry, same-turn commit, Write boundary rule, repo-relative paths, prompt-not-dispatch, receipt vocabulary) [class: REPOSITORY_TEST]
- [ ] `TestPromptLogStandingRulesPreamble` delivers the hermeticity pins: given the test module, expects the repo root resolved as the suite file's grandparent directory and passed explicitly to git (never cwd-resolved), the real-repo read run under the suite's existing sanitized environment helper, and no write to the real repository from the new class [class: REPOSITORY_TEST]
- [ ] `TestPromptLogStandingRulesPreamble` delivers the prune-survival regression: given a scratch git repo built with the suite's existing sanitized-subprocess fixture pattern (pristine committed log bytes at the canonical log path as the `--base` commit, the mutated copy with its receipt as the HEAD commit), expects the preamble Standing rules bytes unchanged after the mutation and the prune-audit invocation over the mutated copy reporting the removal as witnessed [class: REPOSITORY_TEST]
- [ ] `TestPromptLogStandingRulesPreamble` delivers a non-vacuous survival check: given the pristine scratch-repo bytes, expects the preamble Standing rules block asserted present and non-empty before the mutation, so the survival assertion fails at RED rather than passing over an absent block [class: REPOSITORY_TEST]
- [ ] `TestPromptLogStandingRulesPreamble` delivers the receipt-preservation witness: given the same simulated prune of the first entry's heading range, expects every pre-existing receipt line relocated byte-for-byte and in original order outside the removed span, with the removal receipt added, before the prune-audit invocation [class: REPOSITORY_TEST]
- [ ] `TestPromptLogStandingRulesPreamble` delivers the anti-shape witness: given a fixture log whose Standing rules block sits inside the first entry's heading range (the witnessed pre-loss shape), expects that removing that entry's range removes the block bytes, pinning why the preamble placement is the fix [class: REPOSITORY_TEST]
- [ ] `TestPromptLogStandingRulesPreamble` delivers the orientation-line pin: given the committed bytes, expects the orientation line naming the block's canonical home outside every entry range on the line directly above `Standing rules:` [class: REPOSITORY_TEST]
- [ ] Run → expect RED: run the new tests under the collecting venv pytest runner and observe the orientation-line pin fail, plus the placement and prune-survival regressions against the then-current committed log bytes, when the block is absent from the preamble (absent entirely, or present only inside an entry range; re-derive from disk) [class: REPOSITORY_TEST]
- [ ] Amend the module docstring in the same change: the fixture-only subprocess contract scopes to the origin, prune-audit, receipt-repair, and collateral classes, and the new class reads committed repository log bytes directly, a conscious widening that accepts red on checkouts without the relocation [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `test: pin prompt-log standing-rules preamble placement, uniqueness, and prune survival (RED)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Move the Standing rules block into the log preamble (TDD GREEN)

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`

- [ ] Move the Standing rules block into the preamble directly after the log's title line, preceded by the one orientation line naming the canonical home, deleting the in-range copy from the first entry's heading range in the same write, so the finished file carries exactly one block with no `## ` headings introduced by the move [class: IMPLEMENTATION_REQUIRED]
- [ ] Ordering: when the in-range copy is absent at write time (a monitor prune landed first, per `## Standing constraints`), insert the preamble copy from the relocation source and record the ordering in the run log [class: IMPLEMENTATION_REQUIRED]
- [ ] Authoring-landing state: when the block already sits ahead of every entry heading (per `## Standing constraints`), add only the orientation line directly above it, leaving the block bytes in place, and record the state in the run log [class: IMPLEMENTATION_REQUIRED]
- [ ] Write lane and drift: the write commits on this run's authoring branch under the merge-lock guard (the worktree lane `## Standing constraints` prescribes); on drift after the single fresh-read retry it aborts and reports the exact intended preamble bytes instead of applying the entry-shaped end-of-file fallback [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: the Task 1 orientation-line pin, placement, and prune-survival regressions pass against the moved log, including the uniqueness assertion; the anti-shape witness still passes [class: REPOSITORY_TEST]
- [ ] Diff-verify: the twelve relocated bullets compare byte-identical to the pre-prune block (`git show dd1803d2c8^:docs/history/backlog/PLAN-PROMPTS.md`), with only the added orientation line, the in-range copy's deletion, and the relocation differing [class: REPOSITORY_TEST]
- [ ] Commit: `prompt-log: move standing rules block into the preamble outside entry ranges (GREEN)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Repoint the consumers, update the pinned spans, and resolve the older bundle's item 2

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `agents/skills/investigate/SKILL.md`
- `agents/skills/plans/SKILL.md`
- `agents/skills/maintenance/decisions.md`
- `agents/skills/maintenance/zcode.md`
- `scripts/check_maintenance_pins.sh`
- `docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md`

- [ ] Investigate skill delivers a resolvable write-rule citation: given the Stage 4 write-discipline bullet citing "the log's standing rules", expects the citation to name the log preamble's Standing rules block as the canonical home, by pointer, without restating rule text [class: IMPLEMENTATION_REQUIRED]
- [ ] Plans skill Entry freeze delivers a resolvable freeze-placement citation: given the restored Freeze rule's placement clause, expects the paragraph's citation to resolve against it (adjust the citation wording only if the restored text still does not supply the clause; no edit when it already resolves, recording the verification in the run log) [class: IMPLEMENTATION_REQUIRED]
- [ ] Maintenance monitor duties deliver resolvable prune/freeze/write citations: given the Rolling prompt log duties bullet and the runtime overlay's monitor-commit paragraph citing the `Prune rule`, `Coverage and removal rule`, and `Write boundary rule` labels, expects each citation to name the log preamble's Standing rules block as the block's home, by pointer [class: IMPLEMENTATION_REQUIRED]
- [ ] Pinned spans follow their reworded sources: given the four label-citing `prune_range_pin` spans (three decisions.md, one zcode.md), expects each updated to the repointed wording in the same change, plus any other span whose substring no longer appears verbatim in its source, so the pins suite's warning-only greps stay accurate [class: IMPLEMENTATION_REQUIRED]
- [ ] Consumer-label resolution witness: given the repointed consumers, expects every rule label they cite to resolve against the relocated block's own bullet texts, including the unedited citers `agents/skills/execute-plan/worktree-first.md` and `agents/skills/maintenance/template-authoring.md` [class: REPOSITORY_TEST]
- [ ] Older bundle item 2 disposition: given the restored Freeze rule supplying the placement clause, expects a dated resolution note on item 2 of `docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md` citing this plan as the resolving evidence, with items 1 and 3 through 6 untouched and the row's Status staying open [class: IMPLEMENTATION_REQUIRED]
- [ ] No rule text duplication witness: given the full diff of this task, expects no Standing rules bullet text restated inside any skill file (pointer corrections only) [class: REPOSITORY_TEST]
- [ ] Commit: `skills: repoint prompt-log rule citations to the preamble home and follow the pins` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Validation sweep

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:

- [ ] Full log suite green: the extended `scripts/test_check_prompt_log_origins.py` suite passes under the collecting venv pytest runner in full, with the pre-existing tests' outcomes unchanged [class: REPOSITORY_TEST]
- [ ] Hygiene and em-dash clean: the public hygiene scan exits 0 and the em-dash added-lines gate exits 0 over the run's changed files against the merge base [class: REPOSITORY_TEST]
- [ ] Pins suite green: `bash scripts/check_maintenance_pins.sh` exits 0 over the tree with the consumer repoints and pin-span updates landed [class: REPOSITORY_TEST]
- [ ] Post-landing placement re-verification (closeout step outside this task's commit): after the run's landing and its own-entry prune, the Task 1 placement regression is re-run against the landed, post-prune committed bytes and passes, so the landing's prune demonstrably preserved the preamble block [class: REPOSITORY_TEST]
- [ ] Commit (only when the sweep required incidental fixes; otherwise record the green sweep in the run log): `test: validation sweep green for prompt-log preamble relocation` [class: IMPLEMENTATION_REQUIRED]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-05-plan-prompts-shared-rules-pruned.md` (primary origin): covered by this plan's execution landing; flipped `Status: covered` in the same closeout pass.
- `docs/history/backlog/2026-10-22-claim-lifecycle-exec-residual-skill-text-polish.md` (secondary origin, item 2 only): item 2 resolved by Task 3's dated note citing this plan; items 1 and 3 through 6 remain open on the row, whose Status stays open.
