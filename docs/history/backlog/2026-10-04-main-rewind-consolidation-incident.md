# Main was rewound onto a freshly built consolidation lineage by a raw ref write, orphaning the granular wave
Cluster: docs/history/backlog/2026-10-03-maintenance-completion-arm-audit-duty.md

- **Filed:** 2026-10-04 (investigation turn, session-side witness)
- **Status:** covered (docs/history/plans/2026-10-04-main-rewind-bypass-fences.md)
- **Status note (2026-10-04, execution):** the detection half executed and landed (plans root archive `docs/history/plans/completed/2026-10-04-main-rewind-bypass-fences.md`, review record `../reviews/reviews` verdict ready=yes zero blocking, r1 minors folded): the raw-ref-write and amend-authorship bypass shapes are now named by standing audit arms; the row stays open for the operator lineage decision, deliberately session-untouched.
- **Workflow:** backlog
- **Priority:** high (operator decision required; recovery is deliberately operator-visible, never session-self-healed)
- **Origin class:** witnessed defect
- **Class:** fence-class (peer-safety; the base-branch-commit-immutability and cas-enforce-ref-moves classes, both with landed fences that this sequence bypassed)
- **Driving force:** reliability
- **Cluster:** the closed rows `docs/history/backlog/2026-10-02-base-branch-commit-immutability.md` and `docs/history/backlog/2026-10-03-cas-enforce-base-branch-ref-moves.md` (their fences are the ones bypassed); disposition sections for both live on `docs/history/plans/completed/2026-10-02-evidence-integrity-fences.md` and `docs/history/plans/completed/2026-10-03-ref-move-integrity-fences.md`
- **Cluster:** docs/history/backlog/2026-10-04-concurrent-scheduling-ask-dedup.md (same defect class, different surface: two concurrent sessions, the shared automation fleet, no creation-time coordination primitive)

## Witnessed sequence (main reflog, 2026-10-04, all times +0100)

- 07:52:35 ,  `af268a64` committed (the backlog fold-and-delete pass, this session).
- 07:53:14 ,  `commit (amend)` produced `600aa460`: a session OTHER than the author amended the landed base-branch commit (base-branch immutability violation, the rule's second witnessed instance).
- 08:05:58 / 08:10:30 ,  `0c7191ac` (changelog) and `7ea6123e` (hygiene masking) committed on top; the granular wave tip.
- 08:11:28 ,  `10a22175` ("machinery: complete the outcome-contract migration and landing guards") authored on a SIBLING lineage forked at `31e802bd` (parents `44eec2a7` -> `61e86897` -> `c4cac459` -> ...): a consolidation rebuild of the same period.
- 08:11:30 ,  main moved to `10a22175` by a ref write with an EMPTY reflog action description: no CAS old value, no fast-forward check, no parentage gate, no landing record. The move orphaned 734 granular commits (`git rev-list --count 10a22175..7ea6123e`), including every per-plan landing from 2026-09-28 forward (`2f272807`, `5a1f63ba`, `cb10de83`, `d31a4454`, `4f1d095a`, `74238cc2`, `c2fb302c`, `b8d20c6c`, the fold pass).
- 08:17:08 ,  this session's investigation-receipts commit `7e8d1cf3` landed on top of the rewound tip, before the rewind was noticed; re-derived from the reflogs afterward.

## Content verdict (re-derived from trees, not from the reflog alone)

`git diff --stat 7ea6123e 7e8d1cf3` is exactly the investigation commit's 7 files (+29/-1): the consolidation tree contains the granular wave's content, including the Codex-evidence row, the flare rows, the lessons capture, the changelog, the fold-pass content, and the landing guards. Nothing content-bearing is lost. The casualty is history-shaped: (a) the granular lineage survives only in the reflog (`main@{2}` = `7ea6123e`), subject to reflog expiry; (b) every full sha cited in durable records and memory notes for the 2026-09-28..2026-10-04 window is now UNREACHABLE from main, so the resolve-at-use rule's re-derivations fail for those citations until the lineage is restored or the citations are re-keyed to the consolidation shas.

## Expected

A base-branch move that replaces 734 commits is a deliberate, operator-visible, recorded operation with a CAS old value and a landing record; a consolidation landing is named as such in its message and its record; a landed base-branch commit is never amended by a session that did not author it in the same critical section. Both rules exist as landed fences (the amend guard's `check-head`, the parentage gate's pre-swap, the reflog-window audit arm); this sequence executed through paths none of them watch (a raw ref write, an amend inside a peer's window), so the follow-up work is closing the bypass, not re-proving the rules.

## Suggested fix shape

1. Operator lineage decision (the gate this row exists for): (a) accept the consolidation lineage and re-key stranded sha citations, or (b) restore the granular tip `7ea6123e` and re-apply `7e8d1cf3` on top (a 7-file commit), or (c) merge the two lineages so both histories stay reachable. Recommendation: (b) or (c); option (a) strands every cited sha in the window's durable records and memory notes.
2. Whatever the decision, land it as a recorded, operator-directed ref operation (the cas-enforce row's recorded-operation shape), never a silent session repair.
3. Fence the bypasses: extend the reflog-window audit to flag empty-description main reflog entries whose new tip is not a descendant of the previous entry (the raw-update-ref signature this incident produced), and extend the amend guard's post-hoc sweep to flag a `commit (amend)` entry whose amended commit was authored by a different session than the amender (the 07:53:14 shape).
4. The consolidation landing's own provenance (which session, which directive, whether the 08:05-08:10 window's author is the same session) is not re-derived in this row; the operator confirms it before the lineage decision.

## Why not fixed now

Both remedies move main or rewrite history-shaped state: exactly the operations that must be operator-directed and recorded (and the peer session may still be live; the last foreign action preceded this row's filing by minutes). The investigation turn files the witness and stops.
