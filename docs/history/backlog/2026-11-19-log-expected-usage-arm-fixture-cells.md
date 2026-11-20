# Backlog: fixture cells for the --log-expected usage-refusal arms

Cluster: declared-log-path-foreign-unstaged-byte-carry
Status: open
Priority: low

The `--log-expected PATH=BLOB_ID` usage-refusal arms in `scripts/done_run.sh` (duplicate PATH, undeclared path outside the declared `--stage` set, non-pair-carrying mode) have no fixture cells in `scripts/test_done_run_wrapper.py`; only the malformed-id arm is pinned. A refactor of the parse loop or the rolling-log pre-stage guard that silently drops one refusal would not turn the suite red.

Trigger: any change touching the done_run.sh commit parser or the rolling-log guard should add the three cells (exit 3 before any staging/commit) or scope them into the touching plan.

Witness: execute-plan run declared-log-path-foreign-unstaged-byte-carry, code review r1 finding F4 (2026-11-19); plan checklist pinned only the malformed-id cell literally.
