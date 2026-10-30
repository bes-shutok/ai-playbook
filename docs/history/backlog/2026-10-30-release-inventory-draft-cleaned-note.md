# Backlog: Fix report-only inventory wording for the in-flight release-draft entry

Driving force: code-quality
Cluster: release privacy gate diagnostics

scripts/release-rewrite.sh:209 vs :211 - the inventory header says "nothing below is cleaned by this run" while the in-flight `release-draft.*` entry is removed by a successful run's trap (SKILL.md documents the nuance). Reword the header or annotate the draft entry so the inventory is self-consistent.
