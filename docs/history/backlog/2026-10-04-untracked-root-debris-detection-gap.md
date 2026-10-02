# Backlog: untracked non-ignored debris at the repo root has no standing detector

- **Status:** open
- **Origin:** the same dirty-main flare 2026-10-04: four untracked root items (`h/` nested repo, `newfile.txt` "four", `nl.txt` "x", `s.txt` "s"; mtimes 2026-10-03 19:29) sat for twelve hours; no gate flagged them and the operator's flare ask was the only detector; `scripts/revert_set_classifier.py classify` degraded the whole verdict to `OUTCOME: indeterminate` rc=2 on the nested repo (`effective state failed for h/`, the `effective_state` failure return at scripts/revert_set_classifier.py:234-236) naming one path, and unblocked only after the debris moved
- **Driving force:** detection gap - the standing gates scan content, not presence: the hygiene scan covers untracked files only in `--changed-from` mode and only for pattern hits, the done sweep keys on `docs/tmp`, and the validators key on changed tracked files, so the presence of untracked non-ignored entries at the repo root waits for an operator flare; the one tool that classifies untracked paths (the revert-set classifier marks them "foreign ... untracked (never reversal damage)") fails them at state collection when a path is itself a repository, and the early return silences every later path's verdict
- **Cluster:** docs/history/backlog/2026-10-04-nested-git-debris-root-registration.md

## Outcome

A standing probe (a done-sweep or maintenance arm) enumerates untracked non-ignored top-level entries and adjudicates them against a small allowlist, so debris presence is named in a routine turn instead of waiting for a flare; the classifier keeps its fail-closed indeterminate outcome but reports every path it attempted before the collection failure, not only the first, and its selftest covers a nested-repository fixture.

Ship when: a routine turn surfaces untracked root debris by path without operator prompting; the classifier's indeterminate output names the full offender set; both behaviors are pinned by tests.
