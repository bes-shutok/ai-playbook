# Pre-archive gate crashes on non-Mapping claims container (r5 CC5-2, deferred at round cap)

Evidence: scripts/execute_plan_runtime.py ~:3745 manifest.get("claims", {}).items() only defaults on ABSENT key; "claims": null or a list/string passes load_manifest (validates only schema_version and tasks) and raises AttributeError in _pre_archive_gate; the CLI except tuple lacks AttributeError, so the operator sees a traceback instead of a blocked done-pending envelope. Fail-closed in effect (crash precedes any write). 1f718b8a added the row-level non-Mapping guard; this is the container-level sibling. The analogous non-Mapping task-value exposure via _task_complete is pre-existing on main.

Direction: bind claims = manifest.get("claims") and treat a non-Mapping container as a clean refusal naming the malformed claims shape (or empty mapping); consider adding AttributeError to the CLI except tuple.
