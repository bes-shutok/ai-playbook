# Backlog: nested-git debris re-registers as a Git root wherever it lands

- **Status:** open
- **Origin:** dirty-main flare 2026-10-04 (session record docs/tmp/done-session/flare-20261004-dirty-main.md, gitignored): unattributed peer scratch (2026-10-03 19:29) left a nested git repository (`h/` with a live `.git` and `f.txt` "one") at the repo root; the operator's IDE registered `<Project>/h` as a Git root; the flare moved the debris intact under `docs/tmp/done-session/flare-20261004-root-debris/` and the operator reported the same registration symptom against the flare record minutes later (2026-10-04 07:41); remedy applied the same minute: `.git` renamed to `.git-deactivated` in the preserved copy, contents byte-preserved
- **Driving force:** tooling side effect - any `.git` directory inside the project tree is auto-detected and registered as a Git root by out-of-repo scanning (IDE family), and a disposition that moves nested-repo debris without disarming the embedded `.git` either leaves the registration dangling at the old path (the "registered as a Git root, but no Git repositories were found there" warning) or re-arms detection at the preserve location; `.idea/` is gitignored (`/.idea/`, `.gitignore` line 1), so the registration itself leaves no repo-side trace and cannot be repaired from repository state
- **Cluster:** docs/history/backlog/2026-10-04-untracked-root-debris-detection-gap.md

## Outcome

Debris disposition disarms nested repositories as it preserves them: relocating nested-repo debris renames the embedded `.git` (witnessed form `.git-deactivated`) so no scanner can register the copy, and the disposition rule has a repo home in the procedure text, including a post-move step that records the scanner-side remedy for an already-dangling registration (remove the stale root mapping in the scanner's version-control settings; the repo-side `.idea/vcs.xml` is an advisory check only). Current tree state: no detectable nested repository at either location; the residual work is the rule's durable home, not a live symptom.

Ship when: the disposition rule naming the `.git-deactivated` form lives in the procedure text that owns foreign-material handling; a fixture or witnessed run shows a moved nested repo with no detectable `.git`; the stale-registration remedy step is written down where the flare operator reads it.
