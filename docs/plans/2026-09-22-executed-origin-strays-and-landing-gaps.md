# Plan: executed-origin strays and landing gaps

Backlog origins (scope of record): `docs/history/backlog/2026-09-19-selection-helper-suffix-shadowing.md`, `docs/history/backlog/2026-09-19-schedule-vs-execute-verb-contract.md`, `docs/history/backlog/2026-09-19-scheduler-toolset-precheck-before-dispatch.md`, `docs/history/backlog/2026-09-20-default-branch-merge-serialization-lock.md`, `docs/history/backlog/2026-09-17-execute-plan-worker-deadline-contract.md`, `docs/history/backlog/2026-09-17-execute-plan-interruption-root-cause-inventory.md`, `docs/history/backlog/2026-09-19-b2p2-remaining-origin-item-closure.md`, `docs/history/backlog/2026-09-18-execute-plan-sidecar-boundary-sentence-dedup.md`, `docs/history/backlog/2026-09-18-execute-plan-recurrence-relay-consumer-seam.md`. Nine consumed origins: this plan closes each with delivery evidence and moves it under `docs/history/backlog/completed/`.

Consulted, disposition keep-open (not consumed, not in the closure scope): the three tail items named in Task 4 and the deferred sibling named in Task 3. Four further items are verification-only rows (Task 1 final block): they already sit under `completed/` with done statuses and are only re-verified, never edited.

## Terms

- **Stray**: a backlog item left open at the top level after the plan that delivered its fix has executed and archived.
- **Disposition ledger**: the per-item evidence table in Gist & Examples; each row carries the authoring-time probe, the delivery evidence, and the disposition this plan executes.
- **Consumed origin**: an origins-block item this plan closes: it receives a closure line and moves under `completed/`.
- **Closure line**: the plain top-of-file form `Status: closed (<evidence>, verified <date>)`; when an item carries no top-of-file status line, one is inserted directly under the title heading.
- **b2p2**: batch-2 phase-2, the execute-plan driver residuals contract-prose plan archived at `docs/plans/completed/2026-09-19-execute-plan-driver-residuals-batch-2-phase-2-contract-prose.md`.

## Assumptions

- The dispatch payload is the scope of record; no separate backlog file exists for the plan title (verified by recursive search of the backlog tree, 2026-09-22). Basis: dispatch text plus search.
- The dispatch annotation that the selection-helper item "is real, keep" disambiguates the file's name and location and records the item's state when the dispatch was written; the fixed-versus-keep disposition still follows the dispatch's own disposition-check rule and the current-tree probe. The probe shows the anchored pair grammar delivered by 37877753, so the plan closes the item and records the superseded expectation in its closure line. Basis: dispatch text plus `scripts/review_record_selection.py` probe (see ledger row 1).
- The plan consumes exactly the nine origins-block items; the four verified-closed items and the keep-open tails stay outside the block so the archive-time origin-closure gate passes. Basis: `scripts/check_plan_origins_closed.py` extraction semantics (backtick spans ending in `.md` between the header line and the first blank line; a missing origin fails closed).
- Authoring ran as a scheduled session with standing pre-authorization and no interactive user; Phase 1 confirmation is granted by that pre-authorization and every disposition below is probe-gated so execution re-verifies each one against the tree it acts on. Basis: dispatch text.

Decision points requiring a grill: none remain.

## Gist & Examples

Fourteen backlog items are disposition-checked against the current tree: every disposition is derived from a probe of today's bytes, never from the dispatch's claims alone. The plan performs backlog bookkeeping only: status-line edits, short appended disposition notes, and `git mv` moves into `completed/`. No skill text, script, or guideline file changes; no fixes are implemented for the keep-open items.

Disposition ledger (authoring-time probes, 2026-09-22, worktree at main 8f1de5bc):

| # | Item | Now | Probe evidence | Disposition |
|---|------|-----|----------------|-------------|
| 1 | selection-helper-suffix-shadowing | top-level open | `_pair_pattern` anchored to the literal `REVIEW_KIND_INFIXES` set with pinned shadowing semantics and documented residual alias (`scripts/review_record_selection.py:141-194`); the loose prefix is gone; delivered by 37877753 whose subject names the grammar anchor; `scripts/test_review_record_selection.py` exists | close as fixed; the dispatch's "keep" expectation is recorded as superseded by the probe |
| 2 | schedule-vs-execute-verb-contract | top-level open | `AGENTS.md` carries the "Scheduling asks (verb contract)" standing rule; the `{schedule_time}`/`{backlog_item}` template ships in `agents/skills/maintenance/prompt-templates.md` (authoring blueprint) and `agents/skills/maintenance/zcode.md`; 37877753 names the verb contract | close as fixed |
| 3 | scheduler-toolset-precheck-before-dispatch | top-level open | `agents/skills/maintenance/zcode.md` "Ladder precheck (added 2026-09-19)" prescribes `turn_error: clocked-primitives-absent`, lane-scoped stand-down, zero listings, park or retain per the trap rule; child-side twins ride the re-arm and successor duty paragraphs in `prompt-templates.md` | close as fixed |
| 4 | worker-deadline-contract | top-level open | explicit `deadline_seconds` plumbing and a "launch deadline exceeded" outcome with `preserve-and-reconcile` and `resume_allowed` exist in `scripts/execute_plan_runtime.py`; 760cd932 records the deadline-baseline parity probe repointed to the codex adapter profile | re-scope: residual owned by the codex runtime reconciliation effort and the open sibling item named in Task 2 (the durable top-level pointer; branch names are ephemeral once a landing deletes them) |
| 5 | interruption-root-cause-inventory | top-level open | matrix rows landed across worker liveness 76b4e984 (receipt refusal, stall timeout protocol), the agent-aware contract 8a77ec46 (receipts, coherence tests), and the mechanics plan 466a0820; the open residual is user-interruption reconciliation, owned by the same codex reconciliation effort and its 2026-09-22 sibling item | re-scope: superseded by the landed slices; residual re-homed to the live owner |
| 6 | plans-review-subagent-anti-idle-discipline | completed/, done | the anti-idle runtime-discipline paragraph is required text in the plans skill's Plan Quality Gate sub-agent template | verified closed, no action |
| 7 | plans-watcher-schedule-payload-contract-ambiguity | completed/, done | the plans skill Budget gate pins the full probe report JSON plus `plan_path`, never a subset | verified closed, no action |
| 8 | default-branch-merge-serialization-lock | top-level open | `scripts/done-lock.sh` carries the merge-* mode (`MERGE_LOCK_ROOT`, `merge-wait-acquire`, `merge-release-repo`); both blueprints in `prompt-templates.md` mandate the lock around the landing critical section; `scripts/check_maintenance_pins.sh` pins it | close as fixed |
| 9 | vendored-runtime-catalog-landing-gap | completed/, done | the repo's vendored-asset sync rules carry the landing-path clause; the mechanical gate family landed in 59f65154 | verified closed, no action |
| 10 | merge-dirt-regression-gate | completed/, done | `scripts/dirt_regression_gate.py` plus tests landed in 59f65154; the witnessed dirt regression was repaired out-of-band on 2026-09-21 (a working-tree restore of the stale deployed copy; this is not a git-history claim) | verified closed, no action |
| 11 | b2p2-remaining-origin-item-closure | top-level open | the archived b2p2 plan exists; two of its three siblings are open at the top level; the third sits in `deferred/` as a round-cap deferral | execute: close and move the two open siblings, record the deferred sibling's lapse, close and move the b2p2 item |
| 12 | bootstrap-doc-hierarchy-greenfield-path-ordering (tail) | top-level open | the bootstrap skill's greenfield fallback still seeds non-canonical `docs/plans/` and `docs/reviews/` TOML keys | keep open with a one-line disposition note; real gap, unchanged |
| 13 | cache-breakpoint-overflow-token-cost (tail) | top-level open | no repo-side fix exists; the overflowing breakpoint count is produced by the agent harness context assembler, not by this repository; the repo carries a prompt-caching reference document only | keep open with a one-line disposition note naming the harness owner |
| 14 | edit-failure-churn-read-discipline (tail) | top-level open | no read-before-edit pins exist in the execute-plan or done skill text | keep open with a one-line disposition note; unfixed, real |

Example of the bookkeeping shape: an item that reads `Status: open` at the top level gains the closure line `Status: closed (fixed by 37877753; verified 2026-09-22)` plus a one-line `Disposition (2026-09-22):` note naming the evidence, and moves to `docs/history/backlog/completed/`. A re-scoped item reads `Status: closed (re-scoped 2026-09-22: residual owned by <live owner>)`. A keep-open tail keeps `Status: open` and gains only the disposition note.

Documentation impact: none beyond the backlog moves. The maintenance survey reads the top level directly, so the moves are the update; no README, guideline, or registry edit belongs to this plan.

## Evaluation Criteria

**Quality dimensions:**

- correctness: every ledger disposition is backed by a pinned probe command executed against the tree, with the observed evidence recorded in the execution log; no disposition is inherited from the dispatch text without its own probe (ledger row 1 records the one superseded expectation explicitly)
- consistency: every consumed origin sits under `completed/` carrying the plain `Status: closed` line; none remains at the top level; every keep-open tail remains at the top level carrying its disposition note; the deferred sibling stays in `deferred/`
- mechanical gates: the origin-closure gate archive arm exits 0 on this plan; the public hygiene scan exits 0; the no-em-dash scan over touched paths exits 0

**Done when:**

- the nine consumed origins sit under `docs/history/backlog/completed/` with closure lines naming their delivery evidence
- the three tail items remain at the top level with `Disposition (2026-09-22):` notes
- the deferred sibling is byte-untouched in `docs/history/backlog/deferred/`
- the full Validation Commands block exits 0

**Ship when:**

- the next maintenance survey reads the intended open counts (repo-consumed automatically, no action)
- the verb contract's zero-corrections acceptance is measured by the next user-correction mining pass; time-gated and human-owned, prose only

## Review Scope

**Explicit must-fix; findings on these paths are always in scope (review and fix if valid):**

**Production code (documentation):**

- `docs/plans/2026-09-22-executed-origin-strays-and-landing-gaps.md` *(new)*
- `docs/history/backlog/2026-09-19-selection-helper-suffix-shadowing.md`
- `docs/history/backlog/2026-09-19-schedule-vs-execute-verb-contract.md`
- `docs/history/backlog/2026-09-19-scheduler-toolset-precheck-before-dispatch.md`
- `docs/history/backlog/2026-09-20-default-branch-merge-serialization-lock.md`
- `docs/history/backlog/2026-09-17-execute-plan-worker-deadline-contract.md`
- `docs/history/backlog/2026-09-17-execute-plan-interruption-root-cause-inventory.md`
- `docs/history/backlog/2026-09-19-b2p2-remaining-origin-item-closure.md`
- `docs/history/backlog/2026-09-18-execute-plan-sidecar-boundary-sentence-dedup.md`
- `docs/history/backlog/2026-09-18-execute-plan-recurrence-relay-consumer-seam.md`
- `docs/history/backlog/2026-09-19-bootstrap-doc-hierarchy-greenfield-path-ordering.md`
- `docs/history/backlog/2026-09-19-cache-breakpoint-overflow-token-cost.md`
- `docs/history/backlog/2026-09-19-edit-failure-churn-read-discipline.md`

Freeze note: for each touched backlog item, only the top-of-file status line and a short appended `Disposition` paragraph may change; problem statements, acceptance sections, and all other content are frozen. After a `git mv`, the file's path changes and its frozen content must not.

**Tests:** none; this plan changes no code.

**Out of scope; reject unless plan-related:**

- `docs/history/backlog/deferred/2026-09-18-execute-plan-contract-requiredness-wording.md`; reason: round-cap deferral owned elsewhere; this plan only records its lapse inside the b2p2 item
- the four verification-only items under `completed/` (anti-idle, watcher payload, vendored landing gap, merge dirt gate); reason: verified closed, never edited
- `agents/`, `scripts/`, `docs/maintenance/`; reason: no code, skill, or guideline text changes belong to this plan
- every other backlog item at the top level; reason: not named by the dispatch scope

## Validation Commands

```bash
#!/usr/bin/env bash
# Run from any worktree of the repository after all tasks complete.
set -u
fail() { echo "FAIL: $*" >&2; exit 1; }
ROOT="$(git rev-parse --show-toplevel)" || fail "not inside a git tree"
cd "$ROOT" || fail "cd to repository root failed"

MOVED="2026-09-19-selection-helper-suffix-shadowing.md 2026-09-19-schedule-vs-execute-verb-contract.md 2026-09-19-scheduler-toolset-precheck-before-dispatch.md 2026-09-20-default-branch-merge-serialization-lock.md 2026-09-17-execute-plan-worker-deadline-contract.md 2026-09-17-execute-plan-interruption-root-cause-inventory.md 2026-09-19-b2p2-remaining-origin-item-closure.md 2026-09-18-execute-plan-sidecar-boundary-sentence-dedup.md 2026-09-18-execute-plan-recurrence-relay-consumer-seam.md"
KEPT="2026-09-19-bootstrap-doc-hierarchy-greenfield-path-ordering.md 2026-09-19-cache-breakpoint-overflow-token-cost.md 2026-09-19-edit-failure-churn-read-discipline.md"

for f in $MOVED; do
  p="docs/history/backlog/completed/$f"
  test -f "$p" || fail "expected under completed/: $f"
  grep -q "^Status: closed" "$p" || fail "no plain 'Status: closed' line in completed/$f"
  test ! -e "docs/history/backlog/$f" || fail "still at the top level: $f"
done

for f in $KEPT; do
  p="docs/history/backlog/$f"
  test -f "$p" || fail "keep-open item missing from the top level: $f"
  grep -q "Disposition (2026-09-22)" "$p" || fail "no disposition note in $f"
done

test -f "docs/history/backlog/deferred/2026-09-18-execute-plan-contract-requiredness-wording.md" || fail "deferred sibling must stay in deferred/"

python3 scripts/check_plan_origins_closed.py --plan docs/plans/2026-09-22-executed-origin-strays-and-landing-gaps.md || fail "origin-closure gate failed on this plan"

FILES="docs/plans/2026-09-22-executed-origin-strays-and-landing-gaps.md"
for f in $MOVED; do FILES="$FILES docs/history/backlog/completed/$f"; done
for f in $KEPT; do FILES="$FILES docs/history/backlog/$f"; done
bash scripts/scan-public-hygiene.sh --files $FILES || fail "public hygiene scan failed over the touched set"
bash scripts/check-no-em-dash.sh file $FILES || fail "no-em-dash scan failed over the touched set"

echo "ALL VALIDATIONS PASSED"
```

Authoring-time execution of this block against the pre-execution tree records the expected RED state: the first failing gate is the completed/-presence check for the selection-helper item (nothing has moved yet); every later gate is unreachable until the earlier ones pass. The block goes GREEN exactly when all tasks are done.

### Task 1: Close the four landed-fix strays

Files:
- `docs/history/backlog/2026-09-19-selection-helper-suffix-shadowing.md`
- `docs/history/backlog/2026-09-19-schedule-vs-execute-verb-contract.md`
- `docs/history/backlog/2026-09-19-scheduler-toolset-precheck-before-dispatch.md`
- `docs/history/backlog/2026-09-20-default-branch-merge-serialization-lock.md`

- [ ] Probe the verb contract: `rg -n "Scheduling asks" AGENTS.md` expects the standing rule; `rg -n "schedule_time" agents/skills/maintenance/prompt-templates.md agents/skills/maintenance/zcode.md` expects the authoring-blueprint template hits. Record the output. [class: REPOSITORY_TEST] Review tier: L
- [ ] In `docs/history/backlog/2026-09-19-schedule-vs-execute-verb-contract.md`: replace `Status: open` with `Status: closed (fixed by 37877753 and the maintenance blueprint templates; verified <execution date>)`, append one `Disposition (2026-09-22):` line naming the AGENTS.md rule and the shipped template, then `git mv` the file into `docs/history/backlog/completed/`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Probe the toolset precheck: `rg -n "clocked-primitives-absent" agents/skills/maintenance/zcode.md` expects the ladder-precheck bullet with the prescribed turn_error token, zero-listing rule, and park path. Record the output. [class: REPOSITORY_TEST]
- [ ] In `docs/history/backlog/2026-09-19-scheduler-toolset-precheck-before-dispatch.md`: replace `Status: open` with `Status: closed (fixed by 37877753; ladder precheck live in the zcode overlay; verified <execution date>)`, append the one-line disposition naming the overlay bullet and the child-side twins, then `git mv` into `docs/history/backlog/completed/`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Probe the merge landing lock: `rg -n "LOCK_MODE|merge-wait-acquire" scripts/done-lock.sh` expects the merge mode; `rg -c "merge-wait-acquire" agents/skills/maintenance/prompt-templates.md` expects the blueprint mandate. Record the output. [class: REPOSITORY_TEST]
- [ ] In `docs/history/backlog/2026-09-20-default-branch-merge-serialization-lock.md`: replace `Status: open` with `Status: closed (fixed by the merge-landing-lock plan, commit 181af6cc; merge mode live in done-lock.sh and both blueprints; verified <execution date>)`, append the one-line disposition, then `git mv` into `docs/history/backlog/completed/`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Probe the selection-helper fix: `rg -n "REVIEW_KIND_INFIXES" scripts/review_record_selection.py` expects the literal infix set and the shadowing-semantics docstring; `git log --format="%h %s" -1 37877753` expects the grammar-anchor subject. Record the output. If instead the loose `(?:.+-)?` prefix is present again, STOP this item: leave the file at the top level, record the regression in the execution log, and continue with the rest of the plan. [class: REPOSITORY_TEST]
- [ ] In `docs/history/backlog/2026-09-19-selection-helper-suffix-shadowing.md`: replace `Status: open` with `Status: closed (fixed by 37877753, pair grammar anchored; supersedes the dispatch's keep expectation, which predates the anchor; verified <execution date>)`, append the one-line disposition, then `git mv` into `docs/history/backlog/completed/`. Skip this item when the probe above stopped it. [class: IMPLEMENTATION_REQUIRED]
- [ ] Verification-only rows, no file change: confirm each of `docs/history/backlog/completed/2026-09-20-plans-review-subagent-anti-idle-discipline.md`, `docs/history/backlog/completed/2026-09-20-plans-watcher-schedule-payload-contract-ambiguity.md`, `docs/history/backlog/completed/2026-09-21-vendored-runtime-catalog-landing-gap.md`, `docs/history/backlog/completed/2026-09-21-merge-dirt-regression-gate.md` carries its done status line, and record next to each row of the ledger the corroborating living-surface evidence (anti-idle paragraph in the plans skill template; full-probe-report payload pin in the Budget gate section; vendored landing-path clause in the repo guidelines; `scripts/dirt_regression_gate.py` present). [class: REPOSITORY_TEST]
- [ ] Commit: `backlog: close four landed-fix strays with delivery evidence` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Re-scope the two execute-plan runtime items

Files:
- `docs/history/backlog/2026-09-17-execute-plan-worker-deadline-contract.md`
- `docs/history/backlog/2026-09-17-execute-plan-interruption-root-cause-inventory.md`

- [ ] Probe the deadline plumbing: `rg -n "launch deadline exceeded" scripts/execute_plan_runtime.py` expects the timeout outcome with preserve-and-reconcile; `git log --format="%h %s" -1 760cd932` expects the subject recording the deadline-baseline parity probe repointed to the codex adapter profile. Record the output. [class: REPOSITORY_TEST] Review tier: L
- [ ] In `docs/history/backlog/2026-09-17-execute-plan-worker-deadline-contract.md`: insert directly under the title the closure line `Status: closed (re-scoped 2026-09-22: explicit runtime deadlines landed; the cross-runtime baseline residual is owned by the codex runtime reconciliation effort and its adapter profile; durable pointer: docs/history/backlog/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md)`, append a two-line `Disposition` paragraph naming the landed plumbing and the live owner, then `git mv` into `docs/history/backlog/completed/`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Probe the landed inventory slices: `git log --format="%h %s" -1 76b4e984` and `git log --format="%h %s" -1 8a77ec46` expect the worker-liveness and agent-aware-contract subjects; `test -f docs/history/backlog/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md` expects the live residual owner present. Record the output. [class: REPOSITORY_TEST]
- [ ] In `docs/history/backlog/2026-09-17-execute-plan-interruption-root-cause-inventory.md`: replace `Status: open` with `Status: closed (re-scoped 2026-09-22: matrix rows landed via 76b4e984, 8a77ec46, and 466a0820; the user-interruption reconciliation residual is owned by docs/history/backlog/2026-09-22-codex-interruption-recovery-must-reconcile-runtime-state.md and the codex runtime reconciliation)`, append the two-line disposition, then `git mv` into `docs/history/backlog/completed/`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `backlog: re-scope runtime deadline and interruption-inventory items to the live codex reconciliation` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Execute the b2p2 origin-closure item

Files:
- `docs/history/backlog/2026-09-19-b2p2-remaining-origin-item-closure.md`
- `docs/history/backlog/2026-09-18-execute-plan-sidecar-boundary-sentence-dedup.md`
- `docs/history/backlog/2026-09-18-execute-plan-recurrence-relay-consumer-seam.md`

- [ ] Read the archived plan `docs/plans/completed/2026-09-19-execute-plan-driver-residuals-batch-2-phase-2-contract-prose.md` and extract the delivery evidence for its contract-prose origins (landed commit subjects or the squash commit carrying it). Record the evidence per sibling. [class: REPOSITORY_TEST] Review tier: L
- [ ] In `docs/history/backlog/2026-09-18-execute-plan-sidecar-boundary-sentence-dedup.md`: replace its open status line (plain or bullet form) with `Status: closed (fixed by batch-2 phase-2, <evidence from the archived plan>; verified <execution date>)`, append the one-line disposition, then `git mv` into `docs/history/backlog/completed/`. [class: IMPLEMENTATION_REQUIRED]
- [ ] In `docs/history/backlog/2026-09-18-execute-plan-recurrence-relay-consumer-seam.md`: same flip with the phase-2 evidence, then `git mv` into `docs/history/backlog/completed/`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Confirm the deferred sibling `docs/history/backlog/deferred/2026-09-18-execute-plan-contract-requiredness-wording.md` is still present in `deferred/` and record inside the b2p2 item (before closing it) that this sibling's close-as-fixed instruction lapses: the item was deferred at the review round cap and stays in `deferred/` untouched. [class: REPOSITORY_TEST]
- [ ] In `docs/history/backlog/2026-09-19-b2p2-remaining-origin-item-closure.md`: replace `Status: open` with `Status: closed (executed by the 2026-09-22 executed-origin strays and landing gaps plan; both open siblings closed and moved, deferred sibling recorded; verified <execution date>)`, then `git mv` into `docs/history/backlog/completed/`. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `backlog: execute b2p2 origin closure, close siblings, record deferred lapse` [class: IMPLEMENTATION_REQUIRED]

### Task 4: Keep-open tail dispositions

Files:
- `docs/history/backlog/2026-09-19-bootstrap-doc-hierarchy-greenfield-path-ordering.md`
- `docs/history/backlog/2026-09-19-cache-breakpoint-overflow-token-cost.md`
- `docs/history/backlog/2026-09-19-edit-failure-churn-read-discipline.md`

- [ ] Probe bootstrap: `rg -n "plans_dir|reviews_dir" agents/skills/bootstrap-ai-playbook/SKILL.md` expects the greenfield fallback still seeding the non-canonical `docs/plans/` and `docs/reviews/` TOML keys (content-anchored, not line-anchored). Append to the item one `Disposition (2026-09-22):` line: probed, gap real and unchanged, no plan has executed for it. No status change, no move. [class: IMPLEMENTATION_REQUIRED] Review tier: L
- [ ] Probe cache breakpoints: `rg -ln "cache breakpoint" agents projects` expects exactly `agents/skills/agents-best-practices/references/prompt-caching-and-cost.md` (living-surface scope; a tree-wide sweep would match this plan's own probe text, which is the checker literal, not a stale reference); the breakpoint-overflowing assembler is harness-owned and outside this repository. Append the disposition line naming the harness owner. No status change, no move. [class: IMPLEMENTATION_REQUIRED]
- [ ] Probe read discipline: `rg -n "read-before-edit|modified since read" agents/skills/execute-plan agents/skills/done` expects no pins (a clean no-match is the expected outcome; if pins appear, the item got fixed meanwhile: record that and close it instead, mirroring Task 1's flip-and-move). Append the disposition line: unfixed, real, candidate for a future skill-pin plan. No status change, no move. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `backlog: record keep-open dispositions for the three tail items` [class: IMPLEMENTATION_REQUIRED]

### Task 5: Final validation

Files:
- `docs/plans/2026-09-22-executed-origin-strays-and-landing-gaps.md`

- [ ] Run the full Validation Commands block from the repository root; expect `ALL VALIDATIONS PASSED` with exit 0. [class: REPOSITORY_TEST] Review tier: L
- [ ] `git status --porcelain` shows exactly the paths this plan touched and nothing else: the nine moved items now under `completed/`, the three annotated tails, and this plan file. Any foreign path is peer dirt: leave it untouched, do not commit it, and name it in the execution log. [class: REPOSITORY_TEST]
- [ ] Commit only if any validation-driven correction was needed: `backlog: validation fixes for the strays disposition` [class: IMPLEMENTATION_REQUIRED]
