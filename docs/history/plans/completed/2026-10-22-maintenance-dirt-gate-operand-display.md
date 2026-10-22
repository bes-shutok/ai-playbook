# Plan: Fix the maintenance dirt-gate command example

Backlog origin: docs/history/backlog/2026-10-05-maintenance-templates-operand-free-dirt-display.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/YYYY-MM-DD-plan-review-maintenance-dirt-gate-operand-display-pbfa1176c-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: docs/tmp/authoring-claims/2026-10-05-maintenance-templates-operand-free-dirt-display.md (session 01a1638f-189d-7b02-9cf8-0990eb6f3dfd)

## Terms

- **Dirt regression gate:** `scripts/dirt_regression_gate.py`, which requires one or more paths after `--base`.
- **Modified path:** a working-tree file the gate is asked to classify.
- **Restore-touched file:** a file the dirt backup/restore touched when a restore ran.
- **Path array:** a Bash array in which each element is one literal file path passed to the gate.

## Why

The maintenance merge instructions show the dirt regression gate without the required path operands. A reader copying the displayed command gets a usage error instead of a result.

## Gist & Examples

TLDR: show the required path operands in the maintenance merge instructions to support code quality.

Before: The execution instructions show `python3 scripts/dirt_regression_gate.py --base <merge-base-sha>` and say the gate checks modified files, without showing how paths reach the command.

After: The instruction shows `python3 scripts/dirt_regression_gate.py --base <merge-base-sha> -- "${DIRT_PATHS[@]}"`. It tells the maintainer to replace the merge-base placeholder before running and safely populate `DIRT_PATHS` as a Bash array with one element per working-tree modified file plus every file the dirt backup/restore touched when a restore ran. It says to pass the array as separate quoted arguments, never to build or evaluate shell command text from raw path bytes, and that a base-only invocation is a usage error.

Edge cases: Include restore-touched files in the operands when a restore ran. Preserve the existing merge-base derivation and outcome handling; the changelog is historical context and is not an active command example.

## Outcome

The active maintenance merge instructions show shell-safe dirt-gate syntax with the required path operands and explain how to supply the merge-base and path values before execution.

- A reader can pass one operand per working-tree modified file and include every restore-touched file when a restore ran.
- The existing merge-base derivation and gate outcome handling remain intact.

**Gate delta:** none; no machinery, refusal class, hard gate, fence, protocol layer, schema field, or task condition is added, changed, or removed; blocking review-layer duties remain those of the existing plan review workflow.

## Assumptions

- The backlog names two former sites, while the current maintenance modules contain one active dirt-gate command display in `template-execution.md`; the other match is historical prose in `templates-CHANGELOG.md`. This plan updates the live display and leaves the changelog unchanged. Basis: a search of the current maintenance skill modules and a read of the active merge paragraph.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the displayed command supplies accepted path operands for working-tree modified files and restore-touched files.
- Clarity: the instructions explain that a base-only invocation is a usage error.

**Done when:**
- The active command example replaces raw path interpolation with the quoted Bash-array expansion `"${DIRT_PATHS[@]}"` and requires safely populating one array element per working-tree modified file plus every restore-touched file when a restore ran.
- The merge-base placeholder must be replaced before execution, and raw path bytes must not be interpolated into or evaluated as shell command text.
- The merge-base derivation and gate outcome handling are preserved.

**Ship when:** Routine completion condition; class: none; evidence owner: the plan author; closure evidence: after squash landing, the repository's base-branch `template-execution.md` contains the operand-bearing command and both path-set instructions.

## Review Scope

**Explicit must-fix:** findings that the command remains unusable when copied, or that changing it breaks the existing merge instructions.

**Documentation:**
- `agents/skills/maintenance/template-execution.md`

**Production code:** none (documentation-only change).

**Tests:** none; no test files are changed.

**Plan-related extension:**
- Change other files only when required to complete or correct the task above.

**Out of scope; reject unless plan-related:**
- `agents/skills/maintenance/templates-CHANGELOG.md`; it records historical design context, not an active command example.
- `scripts/check_maintenance_pins.sh`; no new blocking assertion is required for this documentation correction.

## Validation Commands

```bash
rg -nF 'python3 scripts/dirt_regression_gate.py --base <merge-base-sha> -- "${DIRT_PATHS[@]}"' agents/skills/maintenance/template-execution.md || { echo "shell-safe operand syntax missing"; exit 1; }
rg -nP '(?=.*\b(?:one|each|every)\b)(?=.*\b(?:path|operand|argument|element)s?\b)(?=.*\bworking[- ]tree\b)(?=.*\bmodified files?\b)(?=.*\b(?:per|for each|for every)\b)' agents/skills/maintenance/template-execution.md || { echo "one path per working-tree modified file is not stated"; exit 1; }
python3 scripts/dirt_regression_gate.py --base HEAD -- README.md
```

### Task 1: Display the required path operands

Context surface: Terms and this task.

Files:
- `agents/skills/maintenance/template-execution.md`

Evidence:
- `scripts/dirt_regression_gate.py` declares positional `paths` with `nargs="+"`.
- A probe with only `--base HEAD` exits 3 and reports `the following arguments are required: paths`; a probe with `--base HEAD -- README.md` returns `OUTCOME: pass`.
- A search of `agents/skills/maintenance/` finds one active command example in `template-execution.md`; the other match is historical changelog text.

Acceptance:
- [x] Show the sole active command display with `<merge-base-sha>` and `-- "${DIRT_PATHS[@]}"`, state that the base placeholder is replaced before execution, and require the array to be safely populated with one element per working-tree modified file plus every restore-touched file when a restore ran. [class: IMPLEMENTATION_REQUIRED]
- [x] Require the array expansion to pass each path as one literal argument and prohibit constructing or evaluating shell command text from raw path bytes. [class: IMPLEMENTATION_REQUIRED]
- [x] State that `--base` without path operands is a command-construction usage error. [class: IMPLEMENTATION_REQUIRED]
- [x] Preserve the existing merge-base derivation and four-outcome handling. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `maintenance: show dirt-gate operands` [class: IMPLEMENTATION_REQUIRED]
