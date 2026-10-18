# Done emit arm classifies without a run-start marker in a fresh done-session directory

Slug: done-emit-prelock-classification
Budget: 1.5h authoring; declared execution budget 1.5h (one precondition arm + fixtures + one ordering sentence + row dispositions)

## Backlog origins (scope of record)

- docs/history/backlog/2026-10-07-done-emit-foreign-candidates-under-enumerates.md (the still-open marker-prerequisite facet; the enumeration facet is covered by c4cac4594)
- docs/history/backlog/2026-10-06-done-boundary-review-candidates.md (triage and disposition only; no omnibus rework)

## Terms

- Emit arm: a `write-manifest --emit-foreign-candidates <file>` invocation; it enumerates the staging candidates the run does not own, writes them one per line sorted, and exits 0 without writing a manifest.
- Run-start marker: a content-confirmed marker under the done-session directory; the newest confirmable marker anchors the session window (`derive_session_window`).
- Fresh-directory shape: a done-session directory holding zero confirmable markers.
- Pre-lock classification: the done Step 0 owned-versus-foreign decision taken before the done lock, consuming the emit arm's file.
- Partial-setup receipt path: the post-lock classification that happens when the pre-lock ordering could not run; the writer's own refusal names the unclassified slice and the recovery is marker, then one `--foreign-review-from` write.

## Why

Three dated witnesses in the origin row (2026-10-07, 2026-10-09, 2026-10-14 appends) record the same facet: the emit arm refuses before enumeration when the done-session directory holds no marker (`no content-confirmed run-start marker under ...` fires before the emit block for every write-manifest invocation), so the pre-lock classification cannot run in a fresh checkout and lands after the lock through the partial-setup receipt path. The recovery is self-healing but repeats per run. The row's original enumeration defect is already repaired: the emit arm and the claim-or-foreign gate call the same `_all_staging_review_paths(ctx)` (exact-set contract, c4cac4594), so this plan addresses only the still-open sequencing cost.

## Gist & Examples

TLDR: a bare emit-only invocation completes without a run-start marker when the done-session directory holds none, so Step 0 classification runs before the lock; every manifest-writing invocation keeps the marker requirement byte-identical (reliability).

Before: a fresh worktree closeout runs the pre-lock emit first; the invocation refuses on the missing marker; the run takes the lock, writes the marker, and classifies through the partial-setup receipt path, one extra writer invocation per run (the 10-07, 10-09, and 10-14 witnesses).

After: the same emit invocation in the zero-marker shape enumerates, prints the enumerated repo root beside the summary, and writes the sorted file; the operator classifies pre-lock and the real write proceeds with `--foreign-review-from`. A directory holding any confirmable marker keeps today's newest-anchor binding unchanged.

## Outcome

The pre-lock classification ordering is reachable in a fresh checkout without weakening the content-confirmed marker on any state-writing path.

- The emit arm completes in the fresh-directory shape: same enumerator, same subtraction, same sorted one-per-line output, same roundtrip refusal; the summary names the repo root the enumeration ran against (the 10-14 cross-checkout footgun stays visible).
- Every manifest-writing invocation (real writes, adoption, finalize) keeps the marker requirement and refusal text byte-identical; a zero-marker emit does not create or mutate done-session state.
- A regression fixture pins the fresh-directory emit and the unchanged writer refusal; the emit-versus-gate exact-set parity is pinned by a fixture over one corpus (or the existing determinism pin is extended if parity is already covered).
- The done skill's Step 0 ordering sentence names the reachable pre-lock shape and keeps the partial-setup receipt path as the fallback for other refusal classes.
- The origin rows are dispositioned per the section below; no residual is folded into an omnibus.

Gate delta: removes one arm's share of an existing refusal (the emit arm's no-marker refusal in the zero-marker shape; fix-class, origin-cited: the row carries the three dated witnesses), keeps the marker refusal on every manifest-writing invocation byte-identical, adds no new gate, fence, protocol layer, or schema field; the candidate universe is unchanged (the same shared enumerator); no task pauses dispatch or later work.

## Assumptions

- The emit arm is read-only over done-session state: it writes only the caller-named output file and no manifest, so the content-confirmation the marker provides (state attribution to a confirmed run in a confirmed root) is not engaged by an emit-only invocation; the printed root provenance keeps the 10-14 cross-checkout misread detectable. Basis: the emit block writes the caller-named file and returns 0 (the first-finalize bulk load arm, `scripts/done_sweep_gates_lib.py`).
- Only the zero-marker shape relaxes; with any confirmable marker present the invocation binds to the newest anchor exactly as today, so no invocation can silently enumerate the wrong window. Basis: the window semantics (`derive_session_window`, the newest-anchor plus previous-run contract).
- The 2026-10-06 inventory residuals are triaged, not reworked: each verdict cites a dated supersession witness or names the narrow kept group; none is bundled into this plan's code change. Basis: the entry's rejected omnibus alternative.

Decision points requiring a grill: none remain: the origin row's Expected adjudicates emit-completes-prelock over a marker-first docs-only ordering (the cost recurs per run with three dated witnesses, and the fix is one arm's precondition, not a gate) and over exempting all write-manifest invocations (only the read-only emit shape relaxes; state-writing arms keep the marker).

## Standing constraints

- Never push to origin; stage by explicit path only; never amend a commit reachable from main.
- The hygiene scan (exit 0) runs before every commit; no em-dashes and no absolute personal home directory paths in committed files.
- Bounded repair only: never edit a gate or validator mid-lane to unblock the lane.
- Preserve the content-confirmed marker, lock ordering, ownership checks, and no-partial-manifest behavior; no second enumeration; no new guards; the candidate universe does not broaden.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the fresh-directory emit output equals the writer gate's candidate set minus owned claims on the fixture corpus; the existing determinism pin still holds.
- Preservation: all pre-change writer-arm refusal fixtures stay green byte-identically.
- Docs truthfulness: the Step 0 sentence names the ordering reachable post-change and no longer implies the emit needs a marker first.

**Done when:**
- The lib suite passes with the new fixtures (fresh-directory emit, unchanged writer refusal, emit-versus-gate parity or the extended existing pin).
- The wrapper suite passes; hygiene scan exit 0; no em-dashes in touched files.

**Ship when:**
- A fresh-checkout closeout runs its pre-lock classification without the extra post-lock writer invocation on the witnessed shapes.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/done_sweep_gates_lib.py` (the emit arm's marker-binding precondition and summary line only)
- `agents/skills/done/SKILL.md` (the Step 0 classification ordering sentence)

**Tests:**
- `scripts/test_done_sweep_gates_lib.py` *(new fixtures)*

**Docs / backlog surgery:**
- `docs/history/backlog/2026-10-07-done-emit-foreign-candidates-under-enumerates.md` (disposition)
- `docs/history/backlog/2026-10-06-done-boundary-review-candidates.md` (triage disposition)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/land_squash.sh`, `scripts/reconcile_post_landing.py`; different landing machinery, no done-session state.
- The claim-or-foreign gate's writer arms and the enumerator semantics; the exact-set contract is retained verbatim (c4cac4594).

## Validation Commands

Run from the repository root. The venv python runs the suite when present; the bare fallback is acceptable when the venv is absent.

- `$HOME/.agents/venvs/ai-playbook-test/bin/python3 -m pytest scripts/test_done_sweep_gates_lib.py` (fallback when the venv is absent: `python3 -m pytest scripts/test_done_sweep_gates_lib.py`)
- `$HOME/.agents/venvs/ai-playbook-test/bin/python3 -m pytest scripts/test_done_sweep_gates_wrapper.py` (fallback when the venv is absent: `python3 -m pytest scripts/test_done_sweep_gates_wrapper.py`)
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-16-done-emit-prelock-classification.md`
- `bash ~/.ai-playbook/scripts/scan-public-hygiene.sh`
- `bash scripts/check-no-em-dash.sh touched`

## Disposition of migrated backlog items

- 2026-10-07-done-emit-foreign-candidates-under-enumerates: closed as covered in two parts by this landing: the enumeration defect covered by c4cac4594's shared enumerator (verify and retain; the parity pin names it; c4cac4594 is that part's witness), the marker-prerequisite facet covered by this landing's emit arm change (the landing commit is that part's witness).
- 2026-10-06-done-boundary-review-candidates: triaged per the entry's narrow-groups arm, not folded here: each residual in the row gets a one-line dated verdict (superseded-by witness, or kept as a narrow row) recorded in the row itself during execution; the row is deleted only if every residual adjudicates superseded.
