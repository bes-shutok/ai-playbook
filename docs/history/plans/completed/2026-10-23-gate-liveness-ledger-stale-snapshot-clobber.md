# Plan: Prevent Stale Snapshot Overwrites in the Gate Liveness Ledger

Backlog origin: none
Driving force: code-quality
Plan review record: .ai-playbook/reviews/YYYY-MM-DD-plan-review-gate-liveness-ledger-stale-snapshot-clobber-p2e5e021e-r*.md
Execution budget: 1.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/gate-liveness-ledger-stale-snapshot-clobber.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Loaded snapshot:** The exact ledger bytes read by one `record` command before it adds a row.
- **Stale snapshot:** A loaded snapshot whose bytes no longer match the ledger at the command's freshness check.
- **Bounded retry:** One re-read and replay of the same requested row after a stale-snapshot mismatch; a second mismatch returns a tool error.

## Why

The ledger writer reads the whole JSON document, appends to an in-memory copy, and atomically replaces the file. Atomic replacement prevents torn reads, but it does not prevent a writer holding an older snapshot from replacing a peer's completed append. This happened on 2026-10-23 and removed a durable ledger row from the working tree.

## Gist & Examples

TLDR: Detect stale ledger snapshots and retry once, protecting completed peer appends through code quality.

Before: Writer A loads the ledger. Writer B appends `execution-claim-gateway`. Writer A later replaces the file from its older snapshot, silently removing B's row.

After: Before replacing the ledger, A checks whether its loaded bytes are still current. If they changed, A reads the latest file and reapplies its requested row once. If the file changes again before the retry can save, A returns a tool error and preserves the peer's current bytes for an operator retry.

The check addresses a completed peer write that is visible before A's freshness check. It does not serialize two writers that both pass their checks before either replacement; cross-process serialization would require a separate coordination design, which this plan does not introduce under the origin's no-lock-file boundary.

## Outcome

The ledger recorder detects an already-stale snapshot, retries one append against the fresh document, and refuses to replace the file after a second detected conflict.

- A delayed writer cannot silently replace a peer row that landed before its freshness check.
- Repeatedly changing input produces an actionable `tool_error` and leaves the latest ledger bytes intact.
- The whole-file JSON format, schema, and atomic replacement remain in place, and done closeout continues when an advisory append fails.

Gate delta: add a stale-snapshot byte check and one bounded retry in the recorder; a second detected conflict returns `tool_error` for that append, which the existing done closeout reports as advisory and continues past; remove the silent stale-snapshot replacement path; add no lane-blocking gate, hard gate, fence, protocol layer, lock file, schema field, or dispatch-pausing condition; no blocking review-layer duty is added.

## Standing constraints

- Keep the tracked whole-file JSON shape, the existing atomic replacement, and the current ledger schema. Do not add a lock file or convert the ledger to JSONL. Apply these constraints in the implementation and its tests.

## Assumptions

- The reconciliation requested by the origin is already complete: the current ledger contains both the `post-landing-staging` incident row dated 2026-10-22 and the `execution-claim-gateway` change row dated 2026-10-23. Do not append either row again. Basis: both rows are present in the current tracked file; the latter was restored by commit `8f967b726` after the incident row landed in `8a131767f`.
- `record` remains advisory to `done_run.sh`: an append failure emits the existing warning and does not stop closeout. Basis: `done_run.sh` finalize `advisory-appends` stage.
- One retry is sufficient for the observed delayed-snapshot shape. A second detected change returns the existing exit-3 `tool_error` contract with a re-run instruction; it does not keep retrying without a bound.
- The freshness check is scoped to a peer change already visible at the check. The explicit no-lock-file constraint leaves the check-to-replace interleaving window outside this plan; the plan does not claim process-wide serialization.
- Maintenance-selected decision receipt: use one re-read and retry, then refuse the append with `tool_error` on a second detected conflict; source: this entry's required scope arms and the observed stale-snapshot loss; date: 2026-10-23; affected sections: Outcome, Evaluation Criteria, Review Scope, Task 1.
- Machinery admission: incident: the 2026-10-23 stale-snapshot overwrite recorded in this entry; expected catch frequency: low, only when a concurrent ledger writer changes the file between load and save; false-positive cost: one re-read and retry, followed by a warning-only failed advisory append if conflict persists; sunset or review: first false positive or alongside the landing that closes `docs/history/backlog/2026-10-20-finalize-ledger-append-after-landing-strands-dirt.md`; posture: the recorder refuses a conflicted append, while the caller remains warning-only and continues.
- Sources inspected: this entry's witnessed origin and rejected alternatives; `scripts/gate_liveness_ledger.py` (`load_ledger`, `save_ledger`, and `cmd_record`); `scripts/done_run.sh` finalize `advisory-appends`; `scripts/gate_liveness_ledger.json`; `docs/history/backlog/2026-10-20-finalize-ledger-append-after-landing-strands-dirt.md`; current ledger rows and commits `8a131767f`, `8f967b726`, and `1763c1601`.
Decision points requiring a grill: Use one bounded re-read and retry, then return `tool_error` if the next freshness check also detects a change; source: origin's stale-snapshot arm and required posture decision; date: 2026-10-23; affected sections: Outcome, Evaluation Criteria, Review Scope, Task 1.

## Evaluation Criteria

- **Data preservation:** When a peer append is visible before the freshness check, the stale writer does not replace it; after the single retry, both the peer row and requested row remain present exactly once.
- **Bounded failure:** A second detected conflict returns `OUTCOME: tool_error`, gives a re-run instruction, and leaves the newest on-disk bytes unchanged.
- **Compatibility:** Existing row fields, schema version, `show` behavior, atomic replacement, and the exit-3 error contract remain unchanged.
- **Advisory behavior:** A failed ledger append still produces the existing `done_run` warning and closeout continues.
- **Scope:** No lock file, JSONL conversion, ledger schema change, or per-guard policy change is introduced.

**Done when:** the focused ledger tests prove stale-snapshot retry and persistent-conflict refusal, preserve the latest peer rows, and pass with the existing ledger schema and CLI outcomes; public-hygiene and no-em-dash scans pass for changed files.

**Ship when:** the implementation is reviewed and landed; the witnessed rows remain present, and the sibling append-order backlog item is handled on its own plan or execution path.

## Review Scope

**Explicit must-fix:** findings on the paths below are always in scope.

**Production code:**
- `scripts/gate_liveness_ledger.py` (`load_ledger`, `save_ledger`, `cmd_record`, and the module's outcome contract only)

**Tests:**
- `scripts/test_gate_liveness_ledger.py` (freshness, bounded retry, and existing append behavior only)

**Plan-related extension:** include a directly related finding only when it is required to prevent a stale loaded snapshot from overwriting a completed append, preserve the error contract, or keep the closeout advisory.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh`; its existing append warning and continue behavior is inspected and preserved, not changed.
- `scripts/gate_liveness_ledger.json`; both missing-row witnesses are already present, so this plan does not rewrite or duplicate them.
- Lock-file coordination, storage-format conversion, ledger schema changes, and unrelated guard policies; the origin explicitly excludes them.

## Validation Commands

Run from the repository root:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_gate_liveness_ledger.py'
python3 scripts/gate_liveness_ledger.py show
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh --files scripts/gate_liveness_ledger.py scripts/test_gate_liveness_ledger.py
```

The focused tests must mutate the ledger after the first command has loaded its snapshot but before its save check. Cover one detected change followed by a successful retry and two detected changes followed by `tool_error`. Assert that the peer's row is never lost when its write precedes the check, the requested row appears only once after retry, and a persistent conflict does not replace the latest on-disk bytes. Retain positive controls for ordinary append, `show`, and existing invalid-input outcomes.

### Task 1: Reject and retry already-stale ledger snapshots

Context surface: this plan's Terms, Outcome, Standing constraints, Assumptions, and Evaluation Criteria; this entry's witnessed Origins, Scope arms, Machinery admission, and rejected alternatives; the sibling append-order backlog row's separate failure class.

Files:
- `scripts/gate_liveness_ledger.py`
- `scripts/test_gate_liveness_ledger.py`

Primary class anchors:
- `load_ledger` in `scripts/gate_liveness_ledger.py`
- `save_ledger` in `scripts/gate_liveness_ledger.py`
- `cmd_record` in `scripts/gate_liveness_ledger.py`

- [x] Preserve the exact bytes loaded for each record attempt and compare them with the current ledger bytes before replacement; when they differ, do not replace the file from that snapshot. [class: IMPLEMENTATION_REQUIRED]
- [x] On the first detected mismatch, re-read the latest ledger and replay the same requested row once; save only if the retry's loaded bytes still match at its freshness check. [class: IMPLEMENTATION_REQUIRED]
- [x] On a second detected mismatch, return exit 3 with `OUTCOME: tool_error` and a clear instruction to rerun the append; leave the latest on-disk bytes unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Add focused tests for one-conflict recovery and repeated-conflict refusal; assert both peer and requested rows remain after recovery, the requested row is present once, and a refused attempt never replaces the latest bytes. [class: REPOSITORY_TEST]
- [x] Retain the schema, whole-file JSON shape, `os.replace` atomic write, ordinary append, `show`, and current invalid-input outcomes; do not add a lock file or alter the existing advisory caller behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] Run -> expect RED: the stale-snapshot and repeated-conflict cases fail against the unconditional current `save_ledger` replacement. [class: REPOSITORY_TEST]
- [x] Run -> expect GREEN: the focused ledger test file passes with both conflict cases and existing controls. [class: REPOSITORY_TEST]
- [x] Commit: `fix: retry stale gate ledger appends once` [class: IMPLEMENTATION_REQUIRED]
