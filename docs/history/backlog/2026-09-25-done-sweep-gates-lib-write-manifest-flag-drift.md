# Backlog: deployed done_sweep_gates_lib.py predates the done SKILL.md write-manifest bulk flags

- Priority: high
- Status: open
- Workflow: backlog
- Scope: `agents/skills/done/SKILL.md` Step 0 "Run manifest" recipe; runtime-home deployment of `scripts/done_sweep_gates_lib.py`
- Owner: playbook maintenance
- Source: learned 2026-09-25 during a per-task `done` run (execute-plan Task 1 finalize) in a personal-repo worktree
- Driving force: reliability, secondary: observability

## Observed versus expected

The done skill's Step 0 run-manifest recipe documents two bulk affordances for the claim-or-foreign classification: `--claim-none` (assert no owned staging doc, mark every unclaimed candidate foreign) and `--foreign-review-from <file>` (bulk-load foreign paths). The deployed runtime-home copy of `done_sweep_gates_lib.py` (a regular file under `~/.ai-playbook/scripts/`, deployed earlier the same day) does not accept either flag: `write-manifest --owned-plan <plan> --claim-none` exits 2 with `error: unrecognized arguments: --claim-none` and a usage line naming only `--owned-plan`, `--owned-review`, `--foreign-review`, and `--adopt`. The canonical repo copy (committed, clean tree) contains the flags, so the skill text and the repo source agree; only the deployed copy lags.

## Reproduction (trimmed)

```text
$ python3 ~/.ai-playbook/scripts/done_sweep_gates_lib.py write-manifest \
    --owned-plan docs/history/plans/<slug>.md --claim-none
usage: done_sweep_gates.py write-manifest [-h] [--owned-plan PATH]
                                          [--owned-review PATH]
                                          [--foreign-review PATH]
                                          [--adopt RUN_ID]
error: unrecognized arguments: --claim-none
```

## Environment context

- Runtime home `scripts/` mixes symlinked entries (repo updates propagate) with regular-file copies (they never do); `done_sweep_gates_lib.py` and `done_sweep_gates.sh` are regular files.
- A prior manual redeploy left a `done_sweep_gates_lib.py.bak-<date>` sibling beside the live copy, establishing the redeploy precedent for this family.
- Workaround used this run: enumerate `--foreign-review` once per candidate (248 review files) with the deployed lib; the manifest wrote correctly, so the gap is an affordance lag, not a blocker.

## Suspected root area

Runtime-home deployment lag for the sweep-gates lib family. The done skill's stale-deployment remedies name the gate validators (`plan_readiness.py`, `doc_registry_validator.py`) but not the Step 0 lib, so nothing routes its refresh when the skill text gains new flags.

## Suggested fix

1. Redeploy `scripts/done_sweep_gates_lib.py` from the repo to the runtime home (repo is the source, runtime home is the destination, never the reverse), preserving the `.bak-<date>` precedent.
2. Consider a symlink deployment for the sweep-gates script/lib pair so repo commits propagate without a manual copy step, coexisting with whichever single deployment convention the deferred deployment-step decision settles on.
3. Optionally widen the done stale-deployment signature: an argparse `unrecognized arguments` error naming a flag the done SKILL.md itself documents is a stale-runtime-home signature with a copy remedy, not a lib bug to investigate.

## Re-affirmation

2026-09-26: re-hit at the next per-task done boundary of the same execution run (Task 2 finalize, personal-repo worktree). The deployed copy still rejects `--foreign-review-from`; the repeated-`--foreign-review` workaround again wrote a correct manifest (248 candidates). Priority re-affirmed: high.

2026-09-26: re-hit at the Task 4 finalize boundary of the same execution run (verification-only task, personal-repo worktree). First attempt used `--claim-none` and got `error: unrecognized arguments: --claim-none`; the repeated-`--foreign-review` workaround again wrote a correct manifest (252 candidates). Priority re-affirmed: high.

2026-09-26: re-hit at the r1 code-review address done boundary of the same execution run (personal-repo worktree). The deployed copy still accepts only the four base flags; the repeated-`--foreign-review` workaround again wrote a correct manifest (253 candidates). Priority re-affirmed: high.

2026-09-26: re-hit at the r3 residual-acceptance verification done boundary of the same execution run (personal-repo worktree). First attempt used `--foreign-review-from <file>` and got `error: unrecognized arguments: --foreign-review-from`; the repeated-`--foreign-review` workaround again wrote a correct manifest (255 candidates). Priority re-affirmed: high.
