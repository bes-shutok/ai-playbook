## stranded-pointer-pairing-vintage

Added: 2026-11-02, doing-code-review r1/r2 panels over the stranded-doc-pointer-edit-orphan ad-hoc landing (r1 finding F8; r2 finding F2)

Cluster: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md (stranded-doc-pointer-edit-orphan family record)

Status: open, Priority: medium, Class: fix-class

Witness: .ai-playbook/reviews/2026-11-02-stranded-doc-pointer-edit-orphan-code-review-r1.md; .ai-playbook/reviews/2026-11-02-stranded-doc-pointer-edit-orphan-code-review-r2.md

The pairing text's vintage is unspecified and the probe reads the primary's working tree: a primary not yet fast-forwarded reports rows introduced by the landing as absent (r1's stale-working-tree shape), and uncommitted dirt that DELETES the landed row makes the check print "no docs/AGENTS.md index row references it (no pairing to strand)" while suppressing the WARN - the deletion sub-shape of the exact incident class, worker-verified, which can never generate the true-catch witness the admission protocol requires.

Scope arm: pair against the landing-side index text (git show <landing>:docs/AGENTS.md, base fallback when absent), reword the informational line to name which text it probed, pin the row-deletion-dirt shape asserting the WARN and the stale-primary shape.
