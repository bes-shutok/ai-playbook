# gate-removal refuses forever on never-verifiable header citations with a migrate remedy that cannot help
- **Cluster:** docs/history/backlog/2026-10-08-gate-removal-residual-fail-open-shapes.md; docs/history/backlog/2026-10-08-gate-removal-usage-doubled-token.md; docs/history/plans/completed/2026-10-18-closeout-gate-series-token-infix.md; docs/history/backlog/2026-10-19-gate-removal-squash-accounting-requires-archive-twin.md; docs/history/backlog/2026-10-19-gate-removal-manifest-lookup-skips-branch-closeout.md

Driving force: automation (secondary: observability)
Date filed: 2026-10-07
Origin: code review r1 address round (worktree-removal-migration-gate), backlog instruction of the receiving-review pass, deferred per the recorded triage disposition
Severity: low (the gate's fail-closed direction is correct and no records are at risk; the cost is a futile remedy loop an agent dutifully repeats)
Source reference: r1 round of docs/history/plans/2026-10-07-worktree-removal-migration-gate.md (staging doc docs/history/reviews/2026-10-07-worktree-removal-migration-gate-code-review-r1.md is synthesized after the address pass; this row records the pass's backlog instruction); capture hygiene: scan-public-hygiene --files pass (run at capture time, recorded below)

## Finding

A plan header citation that can never verify under the primary reviews home puts `scripts/worktree_closeout_migrate.py gate-removal` into an unremediable refuse loop: an absolute header citation is always refused by design (its pathlib join would discard the home), and a relative citation whose filesystem-resolved home join escapes the home with no basename twin is refused too, but every refusal prints the single `_GATE_REMEDY_LINE` remedy ("run capture then migrate ... then re-run gate-removal"). No amount of migrating lands a record that satisfies such a citation, so a session following the remedy loops migrate (a no-op) then gate (the same refusal) forever, and the output never distinguishes this never-verifiable refusal class from the fixable missing-records class the remedy was written for.

Round-2 addition (2026-10-07 fix pass): the class list gains the operand shapes; a `--worktree` operand resolving equal to or nested with the `--target` checkout, and a resolved reviews home anchoring inside the `--worktree` tree (a symlinked home component staging the records the removal would destroy), are refused with an operand-specific remedy naming the operand fix (use a worktree outside the primary checkout), never the migrate line, because no migrate run can clear operand nesting.

Exact location: `scripts/worktree_closeout_migrate.py` `cmd_gate_removal` refusal printing (the shared `_GATE_REMEDY_LINE` emitted for `refused_citations` and `refused_claims` beside the `missing` lines).

## Suggested direction

Distinguish the unattainable case in the output, per label citation: render a refusal-specific remedy for the never-verifiable classes (an absolute citation, a relative citation whose resolved home join escapes the home without a basename twin), naming the citation text as the thing to correct in the plan header (re-point it repo-relative or fix the path), and keep the migrate remedy for the missing-records and symlinked-record classes migration can actually close; alternatively scope the per-label extraction decision so the refuse line itself carries the class. Suite witnesses: an absolute header citation whose file exists gets the citation-fix remedy and never the migrate line.

## Why not fixed now

Received in the r1 address round as an explicit backlog instruction, not a fix-round item; the remedy rework is a new output-contract change (the migrate remedy line is quoted in the suite and prose homes) and sits outside this round's enumerated fix scope.

Class: fix-class (the gate failed closed correctly but the only sanctioned exit it names is unattainable for this input class, forcing a manual workaround; acceptance names the block that disappears: a session holding a never-verifiable header citation gets a refusal whose remedy terminates the loop instead of inviting a futile migrate re-run; a fix-class origin must not add refusal paths, and this row adds none)
Dedup probe: keyword search `remedy|refuse forever|deadlock|unattainable|gate-removal` over docs/history/backlog/*.md; nearest items are 2026-10-08-gate-removal-usage-doubled-token.md (same subcommand, different defect: the doubled usage token, not the refusal remedy semantics) and 2026-10-05-done-interrupted-manifest-recovery.md (an unrelated done-boundary remedy gap); distinct from both.
Origin class: self-serving
