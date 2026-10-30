# Gate-report retention sweep polish family (r1 review residuals)

Driving force: code-quality

Origin: Phase 3 r1 fresh-adversarial panel (plan docs/history/plans/2026-10-29-done-gate-report-retention.md, run zcode-exec-automation-75d270c1-pick1, 2026-10-30). Zero blocking; three Low correctness findings and two docstring/wording precision items below.

Scope:
- Branch-name reuse over-retention (Low, done_sweep_gates_lib.py ~3040): the hold retains while ANY registered worktree holds the recorded branch; a surviving checkout on the same branch name after the closeout's worktree removal keeps cited reports retained past the plan's terminal condition. Bounded-storage erosion only.
- Deep-operand discovery bound (Low, done_sweep_gates_lib.py ~3009): the hold scans only execute-plan/*/*.json, execute-plan/*.json, done-session/*.json; a hand-placed deeper explicit operand keeps its gate-removal refusal alive while its cited report is pruned. Sanctioned producers all sit at scanned depths.
- Unbounded prune-warning emission (Low, done_sweep_gates_lib.py ~3016/3030): each unreadable/unsupported manifest appends a raw warning line while the kept family uses bounded_inline_listing; many corrupt files give an unbounded warning tail. Route through the bounded listing.
- Docstring precision (Low, done_sweep_gates_lib.py ~2895): "outside the span on each unverifiable path" is wrong for the two post-acquire unverifiable paths; the by-branch rule is a deliberate superset of the consumer's rule (say so); the scan is three fixed globs, not every JSON.
- Absorb from the sibling row (2026-10-30-done-skill-manual-scoped-copy-wording-retirement.md polish rider): worktree-first.md "appends nothing" -> "appends no migrated or renamed row"; collision rows land in `renamed`, so the "migrated entry" sentence should name both sections; inventory items are files-only (directory row fails as "missing source" - clarify or relabel).

Witness: r1 panel records in the run session dir; both lens verdicts backlogged-candidates.
