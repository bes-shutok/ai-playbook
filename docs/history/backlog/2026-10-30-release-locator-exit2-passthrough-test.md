# Backlog: Add locator-helper exit-2 passthrough selftest case

Driving force: code-quality
Cluster: release privacy gate diagnostics

The helper passthrough test covers rc 0/1/3 but not 2 (test_clean_output_and_exit_passthrough); rewrite-level 2-to-3 is already covered by test_scanner_exit_two_aborts. Add the helper-level rc 2 passthrough case.
