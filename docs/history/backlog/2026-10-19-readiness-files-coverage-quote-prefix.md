# The readiness FILES-COVERAGE matcher misses commands quoted with a leading interpreter word

- **Filed:** 2026-10-19, learn Step 1.9 capture from the smme strand-recovery session
- **Status:** open
- **Workflow:** backlog
- **Priority:** moderate (warning-only today, but it fires on every pre-round whose capture command quotes the interpreter word, training authors to ignore readiness warnings)
- **Origin class:** validator false positive witnessed at certification
- **Class:** fix-class
- **Skill/step:** `scripts/plan_readiness.py` (the FILES-COVERAGE warning arm)
- **Driving force:** reliability (readiness warnings must mean what they say)

## Problem

The readiness gate's FILES-COVERAGE warning compares command-like spans in acceptance items against the tasks' Files: lists, but the matcher does not strip a leading interpreter word: an item quoting `bash scripts/check_maintenance_pins.sh > /tmp/capture.txt 2>&1` reports the script as undeclared even though the task's Files list declares `scripts/check_maintenance_pins.sh`. Witnessed on the smme plan at every pre-round and at the final readiness gate (warning-only, exit 0), with the r6 contract worker independently classifying it a validator false positive and the overflow disposition noting the bash-prefixed quote as the trigger.

## Expected

The matcher tokenizes the quoted command's leading interpreter word (`bash`, `python3`, `sh`, or equivalent) away before matching the declared-path set, so a declared script quoted behind its interpreter does not warn; the fix is matcher-side, never a rule that authors stop quoting the interpreter word.

## Why not fixed now

Warning-only and pre-existing; the certifying round carried it as overflow. The matcher fix is a guard-bearing validator change and routes through the plans machinery rather than an ad-hoc edit.
