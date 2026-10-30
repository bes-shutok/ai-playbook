# Backlog: Replay input fidelity blind spot for skip-worktree drift

Driving force: code-quality
Cluster: release privacy gate diagnostics

release-diagnostic-replay.sh verifies a tracked-clean tree (git status --porcelain --untracked-files=no) and scans live worktree files, but porcelain-clean cannot detect skip-worktree/assume-unchanged drift, so replayed scan bytes can differ from the failed run's HEAD-blob bytes. Enumerate skip-worktree paths in the refusal or scan from a fresh git archive of HEAD.
