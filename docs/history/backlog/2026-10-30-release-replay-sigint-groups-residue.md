# Backlog: Signal-interrupted replay leaves release-groups.txt residue

Driving force: code-quality
Cluster: release privacy gate diagnostics

bash does not run EXIT traps on untrapped SIGINT, so Ctrl-C during a replay scan leaves the reconstructed $top/release-groups.txt behind; the next replay refuses on the occupied path with a removal instruction. Trap SIGINT/TERM to run the same cleanup.
