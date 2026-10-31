# Plan: Make the docs-branch runner report its Python runtime floor

Backlog origin: `docs/history/backlog/2026-10-11-docs-branch-python-runtime-floor.md`
Driving force: simplicity + code-quality
Plan review record: `.ai-playbook/reviews/2026-10-28-plan-review-docs-branch-supported-python-runtime-pe333ca80-r*.md` (highest round for this source path is authoritative)
Execution budget: 1.5h total, largest task 1.0h
Authoring claim: `docs/tmp/authoring-claims/docs-branch-supported-python-runtime.md` (session `01a17c5b-bdc9-7781-86f5-38e0cd2c16dd`)

## Terms

- **Canonical runner**: `bash scripts/docs_branch_sync.sh`, the one supported entry point for docs-branch synchronization.
- **Python runtime floor**: Python 3.11, the first Python release that includes the standard-library `tomllib` module used by the runner.
- **Resolved interpreter**: the `python3` executable found on `PATH` when the shell runner starts; the same executable performs the version check and runs the embedded sync program.

## Why

The canonical runner currently invokes `python3` and imports `tomllib`. On Python 3.9 it stops with a raw `ModuleNotFoundError` before synchronization begins. The same command works when a supported Python is first on `PATH`. The runner should state its actual runtime floor at startup and tell operators how to select a supported interpreter.

## Gist & Examples

TLDR: Report the docs-branch runner's Python 3.11 floor early, improving simplicity by using the existing `PATH` choice instead of adding runtime configuration.

Before: Python 3.9 reaches the embedded program and fails at `import tomllib` with a traceback. After: the runner checks the version of the `python3` executable it resolved, reports the detected version and the Python 3.11 requirement when unsupported, and exits before acquiring the sync lock or reading project facts. A supported executable performs both the check and the sync.

Edge cases: Python 3.11 and newer continue through the existing sync path. Python 3.10 and older receive the actionable diagnostic. A missing `python3` continues to fail at command resolution with the shell's existing error.

## Outcome

The canonical docs-branch runner checks its resolved Python interpreter before starting the sync program and explains how to select Python 3.11 or newer when the check fails.

- Unsupported versions exit nonzero before the runner acquires its lock, reads project facts, or changes the docs ref.
- Supported versions retain the existing sync and witness behavior.
- The docs-branch skill names Python 3.11+ and the existing `PATH` selection beside the canonical command.

Gate delta: zero new maintenance gates, locks, registries, or state fields; the existing unsupported-runtime failure becomes an earlier, actionable diagnostic, preserving the same nonzero outcome without entering sync work.

## Assumptions

- `tomllib` is the runtime-floor dependency for the embedded runner; source evidence: `scripts/docs_branch_sync.sh` imports it, and Python's standard-library documentation lists it from Python 3.11.
- Selecting an installed supported interpreter by putting it first on `PATH` remains the operator remedy; source evidence: the backlog origin records a successful run with Python 3.14 first on `PATH`.
- No project facts setting is needed because the runner already resolves `python3` through `PATH`; the same resolved executable can be retained for the preflight and sync invocation.
Decision points requiring a grill: choose the 3.11+ early diagnostic over configured-interpreter discovery: maintenance-selected source comparison, 2026-10-28, Assumptions, Gate delta, and Tasks.
Scope extensions (maintenance-selected arm): configured interpreter discovery; installer or version-manager support; global Python or PATH changes; a second sync runner: omit-extension.

## Evaluation Criteria

- **Correctness:** Python below 3.11 exits nonzero with a diagnostic naming the required and detected versions before synchronization side effects; Python 3.11+ uses the same executable for the check and sync.
- **Usability:** the error tells operators to put a supported `python3` first on `PATH`; the skill documents the same remedy beside the one canonical command.
- **Compatibility:** supported sync, witness, locking, and docs-ref behavior remain unchanged.
- **Done when:** the runner preflight and focused regression cover both unsupported and supported runtimes, the skill documents the floor without net byte growth, and the plan passes readiness and review.
- **Ship when:** no separate deployment or human-owned prerequisite applies; the change lands through the repository's normal plan closeout.

## Review Scope

**Explicit must-fix:**

**Production:**
- `scripts/docs_branch_sync.sh` (Task 1)

**Documentation:**
- `agents/skills/docs-branch/SKILL.md` (Task 2)

**Tests:** behavior of the canonical wrapper when the resolved interpreter is below the floor and when it is supported; reviewers may select existing or new focused test carriers from repository evidence.

**Plan-related extension:** files required to implement and verify these two tasks.

**Out of scope; reject unless plan-related:**
- Project facts or user facts for interpreter selection; the existing `PATH` choice already selects the executable.
- Installing Python, changing global configuration, or adding another runner; none is needed to report the existing `tomllib` requirement.
- Changes to archive formats, witness semantics, lock behavior, or docs-ref updates; those are existing sync behavior outside this runtime startup fix.

## Validation Commands

- `bash -n scripts/docs_branch_sync.sh`
- `PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_docs_branch_sync.py'`
- `python3 scripts/plan_readiness.py docs/history/plans/2026-10-28-docs-branch-supported-python-runtime.md`

### Task 1: Check the Python floor before starting synchronization

Files:
- `scripts/docs_branch_sync.sh`

Primary class anchors:
- `docs_branch_sync_main` in `scripts/docs_branch_sync.sh`, which resolves and invokes the Python interpreter for the canonical sync.

- [x] Given the resolved Python is 3.10 or older, expect the wrapper to report the required minimum and detected version, exit nonzero, and leave the sync lock, project-facts reads, and docs ref untouched; the error tells the operator to put a supported `python3` first on `PATH`. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the resolved Python is 3.11 or newer, expect the same resolved executable to perform the preflight and embedded sync, with existing sync and witness outcomes preserved. [class: IMPLEMENTATION_REQUIRED]
- [x] Exercise the below-floor and supported outcomes with test-controlled `PATH` values so the host machine's Python selection cannot change either regression result. [class: IMPLEMENTATION_REQUIRED]
- [x] Given the version command cannot provide a usable version, expect a clear nonzero preflight error before synchronization work begins. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs-branch: report unsupported Python runtime early` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Document the runtime floor beside the canonical command

Files:
- `agents/skills/docs-branch/SKILL.md`

- [x] Given an operator follows the canonical command instructions, expect the text to state Python 3.11 or newer and explain that putting a supported `python3` first on `PATH` selects it. [class: IMPLEMENTATION_REQUIRED]
- [x] Replace existing command-introduction prose so the skill file has no net byte growth; preserve the single canonical command. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs-branch: document the Python runtime requirement` [class: IMPLEMENTATION_REQUIRED]

## Plan invariants

- A supported Python runtime keeps the existing synchronization and witness behavior.
- An unsupported runtime fails before acquiring the sync lock, reading facts, or changing the docs ref.
- The runner uses one canonical entry point and does not install or configure Python.

## Disposition of migrated backlog items

- Origin `docs/history/backlog/2026-10-11-docs-branch-python-runtime-floor.md` (Status: covered flipped by the authoring closeout) is deleted by this landing; this completed plan is the durable witness. Executed 2026-10-31, landing commits: preflight `50800afd1`, skill doc `9017abf2f` (branch `2026-10-28-docs-branch-python-runtime-floor`).
