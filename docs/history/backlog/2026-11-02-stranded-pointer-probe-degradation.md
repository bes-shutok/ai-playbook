## stranded-pointer-probe-degradation

Added: 2026-11-02, doing-code-review r2/r3 panels over the stranded-doc-pointer-edit-orphan ad-hoc landing (r2 findings F1/G5, r3 finding F6)

Cluster: the EXEC-PROMPTS-PRUNE receipt at the top of docs/history/backlog/EXEC-PROMPTS.md (stranded-doc-pointer-edit-orphan family record)

Status: open, Priority: medium, Class: fix-class

Witness: .ai-playbook/reviews/2026-11-02-stranded-doc-pointer-edit-orphan-code-review-r2.md; .ai-playbook/reviews/2026-11-02-stranded-doc-pointer-edit-orphan-code-review-r3.md

Three probe-degradation arms: a failed docs/AGENTS.md status probe reads as clean (false-clean summary plus false informational line on the --changed route, worker-verified); no pin discriminates the status probe's docs/AGENTS.md pathspec scope (a whole-tree mutant firing spurious rows on unrelated dirt survived all twelve pins); and the changed-set diff probe parses name-only text output, silently dropping C-quoted exotic paths (the exact class the repo's -z convention pins elsewhere).

Scope arm: mirror the diff-probe arm's loud degradation for the dirt probe (WARN + early return, or a degraded summary marker); add the third-file-dirt inert pin; switch the changed-set probe to -z with NUL splitting matching the script family convention; pin all three.
