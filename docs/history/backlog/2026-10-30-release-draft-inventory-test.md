# Backlog: Assert the release-draft inventory entry on failure

Driving force: code-quality
Cluster: release privacy gate diagnostics

Task 2 requires the retained draft be listed in the report-only inventory after failure, but no selftest asserts the release-draft.* inventory entry appears in a failed run's output. Add the assertion.
