# Plan: writer-declared expected-bytes advisory for declared rolling-log paths

Backlog origins (scope of record):
- docs/history/backlog/2026-11-17-declared-log-path-foreign-unstaged-byte-carry.md

Driving force: reliability
Plan review record: the staging series .ai-playbook/reviews/*-plan-review-declared-log-path-foreign-unstaged-byte-carry-r*.md (any date prefix; the highest rN for this source-plan path is authoritative)
Execution budget: 1h total, largest task 0.5h
Executed: yes (285c51cde4e4bc82a3e8b4390e719feab3065b2c)
Authoring claim: declared-log-path-foreign-unstaged-byte-carry.md (session sess_2ef2f7d4-cfc2-4dac-8d4b-fde95273bf35)

## Terms

- declared owned log path: a rolling prompt log passed to the done_run.sh commit transaction through --stage, whose unstaged worktree delta the transaction stages as the writer's own.
- declared expected blob id: the full 40-hex sha1 `git hash-object` id of a declared owned log path's bytes as the writer authored them at its final edit (its final read plus its own entry), computed before the commit — never by hashing the file at commit time, which would absorb pre-declaration foreign bytes — and passed per path through the `--log-expected` operand; the logs are LF-only today, so raw hash-object matches staging's normalization.
- actual staged blob id: the blob id the transaction's own staging records for the declared owned log path; the compare keys on it at the transaction's staged-blob binding point (the authorized-restoration idiom) — the strongest in-transaction anchor, whose residual pre-write-tree window matches the exposure the transaction's existing binding already accepts.
- foreign bytes: staged bytes beyond the writer's declared expectation on a declared owned log path; a mismatch names both blob ids as a divergence signal, never an authorship finding.
- advisory line: the single-line stderr notice a mismatch emits; it never blocks the commit (warning-only posture).
- reconciliation: content recovery from the advisory's two named blob ids (`git cat-file` the actual staged blob — it is in the landed commit — diffed against the writer's authored bytes); the carried foreign bytes' removal or retention stays operator-gated under the Write boundary rule's foreign-bytes posture (never handled autonomously) — the plan routes no disposition through the rule's refusal-keyed remedy steps, whose entry condition cannot arise in an advisory flow.

## Why

A declared owned log path's unstaged worktree bytes are staged verbatim by the captured-tree transaction, so whatever a parallel emitter wrote into that file between the writer's final read and the commit rides the writer's commit under the writer's subject. Witnessed: commit 985d37130 (2026-11-17 03:04) carried a parallel harvest session's unstaged investigate entry inside its declared EXEC-PROMPTS path; the attribution chain broke silently and recovered only by a later tree re-derivation. The landed guards cover staged foreign deltas (refusal) and undeclared paths (set-aside); the declared path's unstaged delta remained trusted as the writer's own.

## Gist & Examples

TLDR: the writer declares each declared owned log path's expected post-edit blob id and the transaction compares it against the staged blob id after its own staging; on a mismatch it emits a warning-only advisory naming both blob ids — foreign bytes become visible at commit time instead of riding silently.

Before: a parallel emitter's unstaged entry rides a closeout's declared log commit unnoticed; the writer's subject claims bytes it never authored and attribution recovers by accident.

After: a writer that declares its expected post-edit blob id gets one advisory line naming expected and actual staged blob ids when the commit carries more; the commit proceeds and reconciliation runs from the two named blob ids, the carried foreign bytes' disposition staying operator-gated under the Write boundary rule's foreign-bytes posture.

## Outcome

The done_run.sh commit transaction gains a writer-declared expected-bytes check for declared owned log paths: the writer declares each declared owned log path's expected post-edit blob id, the transaction compares it against the staged blob id after its own staging (the authorized-restoration binding point), a mismatch emits a warning-only advisory naming both blob ids with reconciliation running from the two named ids and the carried foreign bytes' disposition operator-gated under the Write boundary rule's foreign-bytes posture, and the machinery registry carries the check's admission row.

- Decidability: the discriminator's independent source is the writer's declaration — the r1 four-worker finding that an in-band writer-vs-foreign discriminator is circular is resolved by construction, and whole-blob compare leaves no hunk granularity for foreign bytes to hide inside (r1 findings 1-2).
- Posture: warning-only per the frozen PLAN-PROMPTS entry's Machinery admission paragraph (warning-only first, promotion only on a second true catch, review 2027-02-17 — the entry prunes at this landing; the durable admission home is the registry row's note); the plan's own evidence form for a true catch: a dated line on a tracked surface naming the advisory's two blob ids and the landed commit, falsifiable because the named commit's blob is checkable against its tree; a spurious advisory costs one stderr line, never a refused commit (r1 findings 4, 14; r2 findings 1, 7; r3 findings 4, 7).
- Coverage: declared expectations on the pair-carrying transaction (--expected-ref/--expected-oid, the rolling-log mode the Write boundary rule routes primary log writes through); the witnessed carry rode a closeout's declared EXEC-PROMPTS path (985d37130; the commit records no invocation mode, so coverage keys on declared expectations in the mode the check rides, not on the incident's inferred flags); a writer that declares no expectation is uncovered by construction and a declared expectation outside the pair-carrying mode is refused, recorded in the registry row's note (r1 finding 6; r2 findings 4, 5; r3 finding 10).
- Recovery: the advisory names expected and actual staged blob ids, making reconciliation mechanical — the actual blob is in the landed commit, so `git cat-file` plus a diff against the writer's authored bytes recovers the foreign content, and the carried foreign bytes' disposition stays operator-gated under the rule's foreign-bytes posture (never handled autonomously); the plan routes no disposition through the rule's refusal-keyed remedy steps, whose entry condition cannot arise in an advisory flow (r1 finding 3; r2 finding 2; r3 finding 1).
- The suite's existing rolling-log guard cells stay green: test_guard_refuses_staged_foreign_path, test_foreign_staged_path_refuses_before_git_add, and test_foreign_path_in_capture_window_refuses_and_cleans_owned_delta in scripts/test_done_run_wrapper.py (r1 finding 13's named referents).

Gate delta: one optional repeatable CLI operand (`--log-expected PATH=BLOB_ID`) and one advisory line emitted after the transaction's own staging, inside its existing lock span; the advisory's mismatch finding adds no refusal gate (the mismatch stays advisory) — the operand's usage arms (malformed id, duplicate PATH, undeclared path, non-pair mode) are usage-class refusals priced in the registry note beside the advisory line; no new lock, no schema field, no dispatch-condition change; the check is writer-side only, and a call without the operand behaves byte-identically to today.

## Assumptions

- assume the check compares whole blobs, never hunks: the declared expected blob id against the actual staged blob id, one equality per declared owned log path, anchored post-add at the transaction's own staged-blob binding point. Basis: r1 findings 1-2 (the hunk discriminator is circular and hunk-keying evadable, verified) and r2 finding 3 (the guard-span compare is TOCTOU-racy; the staged-blob binding idiom is the sound anchor).
- assume the writer's expected bytes are NOT derivable in-band and must be declared: the transaction's verified arg surface (--stage, --subject, --expected-ref/--expected-oid, --untrack) carries no baseline or authorship input, and at the pre-stage point the index equals HEAD, so HEAD-to-worktree is one combined delta. Basis: r1 finding 1's verified arg surface; the declaration duty lands in the Write boundary rule sentence (Task 2).
- assume the machinery-registry rows land in the same change as the check, in the registry's real schema: one `keep` row (kind `protocol`, empty paths, the wrapper suite in tests, witness class `incident` resolving to the tracked origin row) whose note carries the admission fields and pre-registered removal criteria in the registry note's established shape — no separate removals-list row, which the inventory check would fail (r1 findings 5, 7).
- assume the Write boundary rule's alignment is a byte-budgeted one-sentence edit inserted between the rule span's pinned needles: the rule names the declaration duty and the advisory's recovery routing. Basis: the rule-span pins are fixed-needle presence greps (prune_range_pin in scripts/check_maintenance_pins.sh) that additions between spans cannot break (r1 finding 9).
- assume one optional CLI operand: the prior no-API-change assumption is flipped — r1 finding 1 proves no in-band discriminator source exists, so the minimal decidability input is a writer declaration; the operand is optional, validated, and non-adopting flows stay byte-identical (marked decision receipt below).

Decision points requiring a grill: refusal-vs-warning-only: no-grill, warning-only per the frozen PLAN-PROMPTS entry's Machinery admission paragraph (warning-only first, promotion only on a second true catch, review 2027-02-17), correcting r1 finding 4's unmarked inversion and r2 finding 1's citation home, with the evidence form and durable-home distinction per r3 findings 4 and 7, 2026-11-18, Outcome; mechanism (declared-expectation whole-blob compare against the staged blob id post-add, replacing the origin row's word-diff hunks): no-grill, r1 findings 1-2 verified the hunk discriminator circular and hunk-keying evadable, r2 finding 3 located the anchor at the transaction's staged-blob binding point, and r3 finding 1 re-homed the disposition on the rule's foreign-bytes posture, 2026-11-18, Assumptions; CLI addition flipping the prior no-API-change assumption: no-grill, authorized by the operator-directed completion of this paused run (2026-11-18 self-heal direction) on r1 finding 1's verified evidence, 2026-11-18, Assumptions.

## Evaluation Criteria

**Quality dimensions:**
- correctness: a mismatch advisory names path, expected blob id, and actual staged blob id as a divergence signal and never blocks; a matching expectation passes silently; a declared expectation outside the pair-carrying mode is refused; a declared owned log path staged as a deletion emits the deletion-shape advisory; a call without the operand is byte-identical to today; the named existing guard cells stay green.
- anti-growth: PLAN-PROMPTS.md measured 175,592 bytes in this worktree at fold time (the primary checkout reads lower; this plan's freeze added the entry) against the 262,144-byte informational tool hard cap (the skill_text_budget ROLLING_LOGS row; the blocking single-read ceiling binds skill files, not the logs), re-derived from the execution tree at task time; scripts/done_run.sh carries no byte cap — it is the pins home, and Task 1's insertion rewrites no pinned needle (verified 2026-11-18 against scripts/skill_text_budget.py and scripts/check_maintenance_pins.sh).
- executability: each task names its insertion site as a verified current anchor in the target file.

**Done when:**
- the transaction compares a declared expected blob id against the staged blob id after its own staging, emits the warning-only advisory naming both blob ids on mismatch, refuses a declared expectation outside the pair-carrying mode, and passes matching or undeclared paths untouched.
- the machinery registry carries the check's schema-valid keep row with its admission fields and pre-registered removal criteria in the note.
- the Write boundary rule names the declaration duty and the advisory's recovery routing.
- the fixture cells pass and the named existing guard cells stay green.

**Ship when:**
- none (repository-internal advisory check; no external release condition).

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_run.sh` (Task 1)
- `scripts/machinery_registry.json` (Task 1)
- `docs/history/backlog/PLAN-PROMPTS.md` (Task 2)
- `scripts/test_done_run_wrapper.py` (Task 1)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/AGENTS.md`; reason: repository-guideline text is cross-project canon, outside this repository-internal advisory check.

## Validation Commands

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_done_run_wrapper.py scripts/test_done_sweep_gates_lib.py -q
bash scripts/check_maintenance_pins.sh
python3 scripts/machinery_inventory.py --check
python3 scripts/skill_text_budget.py --check --suite
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh
```

### Task 1: the declared expected-bytes check, its registry row, and its fixtures

Context surface: the origin row, this task, and the done_run.sh commit path between the rolling-log pre-stage guards and the captured-tree staging.

Files:
- `scripts/done_run.sh`
- `scripts/machinery_registry.json`
- `scripts/test_done_run_wrapper.py`

Primary class anchors:
- `rolling-log-pre-stage-guard` in `scripts/done_run.sh`

- [x] The commit parser accepts a repeatable `--log-expected PATH=BLOB_ID`: PATH must be a declared `--stage` rolling-log path and BLOB_ID a full 40-hex sha1 blob id; a path outside the declared set, a malformed id, a duplicate PATH, or a non-pair-carrying expectation refuses (`commit_die 3`) — an expectation the transaction would silently decline is refused, never skipped. [class: IMPLEMENTATION_REQUIRED]
- [x] After the transaction's own staging of the declared paths (the authorized-restoration binding point), each declared owned log path carrying a declared expectation has its staged blob id read from the index and compared against the expected blob id; an equal check passes silently; a declared path staged as a deletion (no index entry) emits the deletion-shape advisory (the expected blob id, no staged content); no refusal added. [class: IMPLEMENTATION_REQUIRED]
- [x] A mismatch emits one single-line advisory on stderr naming the path, the expected blob id, and the actual staged blob id as a divergence signal, never an authorship finding; reconciliation runs from the two named ids and the carried foreign bytes' disposition stays operator-gated under the Write boundary rule's foreign-bytes posture (PLAN-PROMPTS.md Standing rules); the commit proceeds: warning-only, never blocking. [class: IMPLEMENTATION_REQUIRED]
- [x] A declared path with no declared expectation is unchecked, and a call with no `--log-expected` at all behaves byte-identically to today: the flag is optional and adoption-soft, and non-rolling-log transactions are untouched. [class: IMPLEMENTATION_REQUIRED]
- [x] scripts/machinery_registry.json gains one schema-valid keep row for the advisory check (kind `protocol`, `paths` empty, `tests` [`scripts/test_done_run_wrapper.py`], witness class `incident` whose ref resolves to the tracked origin row named in this plan's header). [class: IMPLEMENTATION_REQUIRED]
- [x] The row's note carries the duty text and opens its admission fields in the registry note's established shape: incident commit 985d37130; expected catch every pair-carrying closeout whose writer declared expectations and whose window carries foreign bytes (no declaration uncovered by construction; zero catch reads as non-adoption, not safety). [class: IMPLEMENTATION_REQUIRED]
- [x] The row's note carries the false-positive field: one spurious advisory line that never blocks, plus the usage arms' deterministic writer-error refusals at the adoption boundary. [class: IMPLEMENTATION_REQUIRED]
- [x] The row's note closes the admission fields: warning-only posture with promotion only on a second true catch, evidenced by a dated tracked-surface line naming the advisory's two blob ids and the landed commit (falsifiable against the commit's tree); review 2027-02-17; removal criteria pre-registered; the witness re-point duty at the origin row's execution fold. [class: IMPLEMENTATION_REQUIRED]
- [x] Fixture cells in scripts/test_done_run_wrapper.py: a mismatch cell drives a pair-carrying commit whose declared path stages bytes beyond the writer's declared expectation and asserts the advisory on stderr naming both blob ids with exit 0 and the commit landed; a pass cell drives a matching expectation and asserts no advisory. [class: REPOSITORY_TEST]
- [x] A usage cell drives a malformed blob id and asserts the exit-3 refusal with nothing staged or committed; a deletion-shape cell stages the declared log path as a deletion (worktree-absent tracked path) and asserts the deletion-shape advisory with exit 0 and the commit landed. The named existing guard cells stay green. [class: REPOSITORY_TEST]
- [x] Run the required suite over the touched test files, the maintenance pins suite, machinery_inventory.py --check (green at fold time), the budget gate's `--check --suite` (exit 0; the pre-existing report-only rows — EXEC-PROMPTS LOG OVER, advisory BREACH/CAPS GAP/PILOT — are expected output), and the hygiene scan, expects all green. [class: REPOSITORY_TEST]
- [x] Commit: `done: add the writer-declared expected-bytes advisory for declared owned log paths (--log-expected staged-blob compare; warning-only mismatch advisory naming both blob ids; admission registry row; fixtures pin the cells)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Write boundary rule alignment

Context surface: this task and the Write boundary rule's Standing rules block.

Files:
- `docs/history/backlog/PLAN-PROMPTS.md`

Primary class anchors:
- `Write boundary rule` in `docs/history/backlog/PLAN-PROMPTS.md`

- [x] The Write boundary rule's declared-path text gains one sentence inside the existing bullet, inserted at the end of the sentence carrying the staged-delta refusal text (before the set-aside arm text) without rewriting any pinned needle. [class: IMPLEMENTATION_REQUIRED]
- [x] The added sentence: the writer declares each declared owned log path's expected post-edit blob id (`--log-expected`, computed over the authored bytes before the commit, never by hashing the file at commit time); a mismatch advisory names both blob ids as a divergence signal with reconciliation running from them, the carried foreign bytes' disposition staying operator-gated under this rule's foreign-bytes posture. [class: IMPLEMENTATION_REQUIRED]
- [x] The advisory line Task 1 adds names the Write boundary rule (docs/history/backlog/PLAN-PROMPTS.md Standing rules) as its recovery home, so the rule and the advisory cite each other. [class: IMPLEMENTATION_REQUIRED]
- [x] Run the maintenance pins suite and the budget gate's `--check --suite` over the changed tree: the rule-span pins are fixed-needle presence greps, so the insertion between pinned spans draws no new PIN WARN naming the rule span, and the PLAN-PROMPTS informational row stays under the 262,144-byte tool hard cap at the execution tree's measured size (the pre-existing report-only rows — EXEC-PROMPTS LOG OVER, advisory BREACH/CAPS GAP/PILOT — are expected output). [class: REPOSITORY_TEST]
- [x] Commit: `plan-prompts: Write boundary rule names the declared-path expected-bytes declaration duty and its advisory recovery routing` [class: IMPLEMENTATION_REQUIRED]

## Integration Points

- The done skill and every log-writing session are consumers of the check through the Write boundary rule: Task 2's sentence names the declaration duty and the advisory's recovery routing, so the rule and the advisory cite each other; no separate Integration Points edit is needed beyond that sentence.

## Disposition of migrated backlog items

The origin row `docs/history/backlog/2026-11-17-declared-log-path-foreign-unstaged-byte-carry.md` is deleted covered by this executed plan (Executed: yes (285c51cde4e4bc82a3e8b4390e719feab3065b2c)). Its durable content moved with the landing: the advisory check and its usage arms live in `scripts/done_run.sh` (`--log-expected`), the admission record (incident 985d37130, expected catch, false-positive cost, warning-only posture with promotion evidence form, review 2027-02-17, pre-registered removal criteria) is the machinery registry row `protocol:log-expected-staged-blob-advisory` note (the witness ref re-pointed here per the row's witness re-point duty), and the writer-side declaration duty is the Write boundary rule sentence in `docs/history/backlog/PLAN-PROMPTS.md`. The review residual (fixture cells for the three unpinned usage-refusal arms; refusal-echo newline hygiene) is the open row `docs/history/backlog/2026-11-19-log-expected-usage-arm-fixture-cells.md`.
