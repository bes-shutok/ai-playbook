# Done-run wrapper test fixtures inherit object-store and namespace Git selectors

- **Cluster:** docs/history/plans/completed/2026-10-22-done-dirt-regression-valid-correction-path.md (the fixture isolation work this run landed)
- Status: open
- Priority: normal
- Age: new (2026-10-23)

## What is owed

`scripts/test_done_run_wrapper.py`'s `HOST_GIT_SELECTORS` scrub covers `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_COMMON_DIR`, config selectors, and `GIT_EXTERNAL_DIFF`, but not `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, or `GIT_NAMESPACE`. A host exporting one of these redirects fixture object reads/writes or ref resolution away from the temporary repository; a green run there verifies nothing.

## Witness

2026-10-23 Task 1 intermediate review (correctness-completeness lens, Medium, environment-dependent-test class). The plan's named criterion ("repository and index selectors") is met; this extends the diff's own isolation goal.

## Suggested shape

Add the three selectors to the scrub list and to the poisoning witness test.

## Round-2 additions (2026-10-23, same run)

- The `GIT_CONFIG_KEY_/VALUE_{i}` scrub enumerates a hardcoded `range(10)`; derive it from the ambient `GIT_CONFIG_COUNT` (read before scrubbing) and extend the isolation witness to plant `COUNT=11` with an overriding `KEY_10`.
- Identity selectors (`GIT_AUTHOR_NAME/EMAIL`, `GIT_COMMITTER_*`, `*_DATE`) are also uncleared; a host value silently re-identifies fixture commits.
