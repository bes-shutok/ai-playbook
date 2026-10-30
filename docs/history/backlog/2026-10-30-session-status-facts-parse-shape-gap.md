# Session-status provider cannot parse the fence-wrapped facts file it reads

- Cluster: dead-run-resume-claim-conversion
- Cluster: docs/history/backlog/completed/2026-10-25-dead-run-conversion-zcode-runtime-gap.md (covered plan owning the channel/provider reachability boundary; this row owns the facts-file parse shape that survives it)
- Cluster: docs/history/backlog/2026-10-23-dead-run-conversion-coverage-residuals.md (refusal-path test coverage sibling)
- Status: open
- Priority: normal
- Age: new (2026-10-30)

## What is owed

Witnessed 2026-10-30 attempting a stranded-run claim conversion (run parked per the recovery procedure's claim-preservation clause): the provider resolution in `scripts/session_status.py` reads the primary checkout's local facts file with `tomllib.load` and fails with `TOMLDecodeError ... Invalid statement (at line 1, column 1)` because `.ai-playbook/facts.md` is fence-wrapped markdown (the TOML body sits inside a code fence, so byte 1 is a fence marker). The provider gate therefore refuses on THIS repo's facts file unconditionally - not only while `session_status_command` is unconfigured (the covered plan's recorded external release gate), but structurally: even after the operator adds the key to the fence-wrapped file, the raw-TOML parse still fails at the first fence line. The conversion arm's diagnostic ("provider facts file unreadable or malformed") correctly reports the failure but the fix path it implies (add the key) cannot clear it.

## Why it matters

Every stranded-run claim conversion in this repo refuses at the provider gate for a reason configuration alone cannot fix, so the recurring night-run parking shape (exec carrier meets a quota-dead peer's near-finished run) keeps paying full re-execution cost, per the covered row's own motivation.

## Shape of the fix

Runtime-configuration owner decision, one of: (a) point `session_status_command` at an executable that serves the status itself and stop parsing the markdown facts file for the key; (b) extend the provider resolution to strip the TOML code fence from the markdown facts file before parsing; or (c) document that the provider facts source must be a plain-TOML file and separate it from the human-readable facts document. Whichever shape lands, add a refusal-path suite cell pinning the fence-wrapped-markdown input so the regression class stays fenced. No gate or validator was edited during the witness; the claim was preserved per the recovery procedure.

## Dedupe note

Searched open backlog rows for provider/facts parsing gaps: the covered runtime-gap row and its test-coverage sibling own the channel derivation and refusal-path coverage, but no open row owns the parse-shape mismatch between raw-TOML parsing and the fence-wrapped markdown facts file. First witness 2026-10-30.
