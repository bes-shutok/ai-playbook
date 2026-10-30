# Backlog: Replay executes digest-verified sources live (TOCTOU)

Driving force: code-quality
Cluster: release privacy gate diagnostics

release-diagnostic-replay.sh digests the scanner and patterns at their live paths and then executes those same paths, leaving a concurrent-modification window after verification. Copy both into the replay temp dir after digesting, as the release rewrite does.
