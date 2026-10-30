# Backlog: Disambiguate replay helper exit 2 between refusal and scanner exit 2 passthrough

Driving force: code-quality
Cluster: release privacy gate diagnostics

scripts/release-diagnostic-replay.sh:27,249 - scanner exit 2 (retired environment-error class) passes through as the replay's reserved refusal code 2; the transcript disambiguates but a mapping or doc note would remove the ambiguity. Map the scanner exit classes explicitly or document the collision in the replay usage text.
