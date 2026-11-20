# Backlog: session scratch writes landing in the primary checkout root

Driving force: hygiene

Origin: the 2026-11-09 attribution pass over uncommitted main dirt (this session). Two witness strands, both from earlier sessions:

- The 2026-11-08 capacity-aware-chaining arc session (sess_8ed699c9) left its ad-hoc investigate EXEC-PROMPTS entry (capacity-aware-chaining-phase3-residuals) and a 28-row backlog Cluster cross-link tidy uncommitted on the primary checkout; stranded for ~10 hours until this session landed them.
- A probe fixture git repository (synthetic commits, author `f <f@f>`, `docs/history` skeleton matching the backlog-completed-dir-regrowth corpus sweep domain) was created at `s1-prescribed-order/` in the primary checkout root on 2026-11-09 05:13, during the one-shot-auth-20261109-0307 authoring run, instead of a temp directory; removed unlanded by this session.

The unlanded strand is disposed of by the same commit that files this row; the row stays open for the fixture-placement class, which recurs (see the docs/tmp retention redesign row, docs/history/backlog/2026-11-01-docs-tmp-retention-redesign.md): probe and fixture artifacts built by runs must go to a temp directory, never the primary checkout.
