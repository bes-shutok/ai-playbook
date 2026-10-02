# Plan: Script outcome contract (pass, fail, indeterminate, tool error) for decision-making scripts

Backlog origin: docs/history/backlog/2026-10-02-script-indeterminate-results-and-agent-escalation.md
Driving force: code-quality (fix-class user-request riding the 2026-10-02 dirt-gate incident: an agent followed the gate's REGRESSION result and stopped closeout on moved imports and lines until the same-day known-case fix 46a91c91 landed; the structural residual stands in that gate and generalizes: a classifier that cannot model the observed shape still exits with a definitive verdict, so the agent's documented discipline faithfully follows the wrong part)
Plan review record: the staging series docs/reviews/2026-10-02-plan-review-script-outcome-contract-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

Decision-making scripts report one of four outcomes (pass; fail with the offending evidence identified; indeterminate, reporting what was observed and what could not be determined; tool error, never represented as a pass or a domain finding) through one machine-readable convention, and the highest-consequence script (the dirt regression gate) is migrated to it with its agent-facing callers branching explicitly on every outcome.

- `scripts/OUTCOME_CONTRACT.md` defines the four outcomes, the exit-code and final-`OUTCOME:`-line convention, the caller-obligation rule, the per-script operating-context assumption table, and the ranked migration inventory for the remaining decision scripts.
- `scripts/dirt_regression_gate.py` reports the four outcomes: its unmodeled-diff-shape arm (the witnessed residual: a binary or unrecognized restored file yields a hunk-less diff and today exits 0 PASS silently) becomes an explicit indeterminate outcome; its usage and git-environment errors become tool errors (exit 3); its known-case behavior from 46a91c91 (import-declaration and moved-line exclusions) stays deterministic and byte-for-byte the same verdicts.
- The agent-facing callers (`agents/skills/done/SKILL.md` pre-commit guard, `agents/skills/maintenance/prompt-templates.md` execution blueprint final-merge step) branch explicitly on every outcome and hand the evidence back to the agent when a decision is required; an indeterminate or tool-error result is never treated as pass or fail and never gates a continued destructive or landing action.

Gate delta: one new contract document plus outcome arms in one migrated script and its two callers, priced per the machinery delta doctrine (docs/history/plans/completed/2026-09-29-plans-machinery-delta-doctrine.md) on the witnessed incident as the recorded-failure witness (the 2026-10-02 dirt-gate closeout stop on moved imports and lines, fixed same-day by 46a91c91 for its two known shapes only, with the unmodeled-shape silent-PASS residual re-derived by this plan's authoring at scripts/dirt_regression_gate.py `_hunks`: a hunk-less non-empty diff is indistinguishable from a clean tree). The addition is a refusal-path conversion of existing error paths plus one new uncertainty arm, not a new enforcement layer; the class-default alternatives are addressed by the origin (removing the gate loses the squash-clobber catcher witnessed 2026-09-30 repair 455ed9ec; skill-prose-only fixes cannot distinguish a modeled certainty from an unmodeled guess per script). The remaining ranked scripts are recorded in the contract's migration table, with the tail-filing duty (one follow-up origin per queued script) owned by the execution completion pass per the Ship-when item, per the origin's own staged-migration scope warning.

## Terms

- **Outcome**: exactly one of `pass` (evidence satisfies the script's stated condition), `fail` (evidence establishes a modeled violation; the offending evidence is identified), `indeterminate` (available evidence is insufficient, contradictory, partially parsed, or outside the modeled cases; the script reports what it observed and what it could not determine and leaves the decision to the agent), or `tool error` (the script could not perform its check reliably: missing inputs, unsupported data, internal failure, or an unheld operating-context assumption). A tool error is never represented as a pass or as a domain finding.
- **The outcome convention**: the script's exit code (0 pass, 1 fail, 2 indeterminate, 3 tool error) plus a final stdout line `OUTCOME: <pass|fail|indeterminate|tool_error>`; human-readable evidence lines precede it. Callers parse the final `OUTCOME:` line and the exit code together.
- **Operating-context assumptions**: the conditions a script's result depends on (repository root and checkout context, branch or lock state, input presence and freshness, invocation outside the modeled context), declared per script in the contract's table; an unheld assumption classifies as tool error or indeterminate, never as a domain pass or fail.
- **Caller obligation**: an agent must not treat `indeterminate` or `tool error` as pass/fail, and must not continue a dependent destructive or landing action on that result; the agent reports the script's lines and re-derives the state from disk before proceeding.
- **The dirt gate**: `scripts/dirt_regression_gate.py` and its 15-test suite `scripts/test_dirt_regression_gate.py` (CLI-level fixtures, `_run_gate` subprocess shape), pinned by the pins suite only through its callers (check_maintenance_pins.sh lines 1440 and 1442 key caller text, not the gate's output), registered in the machinery inventory under `reverse-squash-dirt-gates`.

## Assumptions

- assume the convention is exit codes plus a final `OUTCOME:` line, not a shared result-type library; basis: the machinery cost-benefit adjudication (2026-09-28) caps machinery growth and the logged authoring prompt prices this addition on the witnessed incident, so the smallest sound shape is a documented convention the migrated script follows and later migrations reuse, with no new import surface; a library can be extracted later if a second migration needs it.
- assume the dirt gate migrates first, alone; basis: it is the witnessed incident's script (46a91c91 fixed its two known shapes the same day), its residual is re-derived by this plan's authoring (a hunk-less non-empty diff exits 0 PASS silently), and the origin's own scope warning ranks staged migration over a big-bang rewrite.
- assume the gate's old exit 2 (usage and git-environment errors) becomes 3 (tool error) and 2 is repurposed for indeterminate; basis: no caller branches on the gate's exit codes today (the done pre-commit guard keys on the named `dirt REGRESSION` lines and restores those files; the execution blueprint's final-merge step treats a finding as remediate-in-place and explicitly not a gate failure; both verified at the cited lines), and the two pinned literals key caller text that this plan does not change; the three existing exit-2 test assertions (test_dirt_regression_gate.py lines 183 and 193, test_parallel_work_regressions.py line 329) are updated in the same pass, and the contract's compatibility note records the old exit-2 meaning and the migration date.
- assume hunk-less modeled shapes stay clean; basis: a pure rename (`similarity index`/`rename from`/`rename to`) or pure mode change (`old mode`/`new mode`) carries no content the classifier models, so treating it as clean is today's behavior preserved for an explicitly classified known case, while the binary shape (`Binary files ... differ`) is the indeterminate class the contract exists to surface.
- assume the remaining ranked scripts are recorded in the contract's migration table with their follow-up origins filed by the execution completion pass per the Ship-when item, rather than migrated here; basis: the origin's Suggested fix ranks scripts by consequence and assumption volatility before defining the shape, and its own scope warning rejects a big-bang rewrite, so this plan lands the contract, the ranking, and the first migration.
- Sources inspected: `scripts/dirt_regression_gate.py` in full (read 2026-10-02, lines 1-265: `_hunks`, `_hunk_is_regression`, `classify_path`, `main`; the hunk-less silent-PASS residual re-derived at the `hunks = _hunks(diff_text)` call site); `scripts/test_dirt_regression_gate.py` (15 CLI-level tests; exit-2 asserts at lines 183 and 193); `scripts/test_parallel_work_regressions.py` (gate invocations at lines 296-329; exit-2 assert at line 329); the callers (`agents/skills/done/SKILL.md` pre-commit guard at line 427; `agents/skills/maintenance/prompt-templates.md` final-merge step at lines 282-289 and changelog duty at line 59); the pins suite's two gate literals (lines 1440, 1442); the machinery inventory's `reverse-squash-dirt-gates` entry; the incident fix 46a91c91 (diffstat: the gate plus its test plus the worktree-policy origin).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: a decision script that cannot model the observed shape still returns a definitive verdict and the agent's own discipline follows it; this plan defines the four-outcome contract (pass, fail, indeterminate, tool error) with one machine-readable convention, migrates the witnessed gate to it, and binds its callers to branch on every outcome (code-quality force).

Before (today): the dirt gate meets a restored binary file; `git diff` emits `Binary files ... differ`, `_hunks` returns an empty list, and the gate prints `dirt gate: PASS` and exits 0, indistinguishable from a clean tree. The closeout discipline stages the file. The same shape-generic gap exists in every decision script: nothing in their surfaces says "I could not tell".

After (this plan): the same binary restored file yields `dirt INDETERMINATE: app.txt (diff carries no classifiable hunks ...)` and `OUTCOME: indeterminate` with exit 2; the done pre-commit guard reads the outcome, stops the staging pass, reports the gate's lines, and re-derives from disk. Known cases keep their exact verdicts: the 46a91c91 import and moved-line exclusions are untouched, renames and mode changes stay clean, and every previously passing test still passes.

## Evaluation Criteria

**Quality dimensions:**
- correctness: the gate reports exactly one outcome per run, the witnessed unmodeled shape (binary dirt) surfaces as indeterminate with observed and could-not-determine lines, and every known-case verdict from 46a91c91 is preserved (Validation checks 4 and 5).
- caller coherence: both agent-facing callers branch on every outcome, and neither can treat indeterminate or tool error as pass/fail or continue a dependent staging, destructive, or landing action on it (Task 3's edits, witnessed by the pins suite staying green since both gate pins key caller text this plan preserves).
- migration honesty: the contract's compatibility note records the old exit-2 meaning and the migration date, and the ranked inventory names the not-yet-migrated scripts so the tail cannot silently claim coverage (Task 1's table).

**Done when:**
- The contract document, the migrated gate, the updated tests, and both caller edits land; the gate's suite passes with the ten new outcome fixtures (25 collected per Validation check 4); the pins suite stays green; all Validation Commands exit 0.

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] The runtime twins of the touched skills are refreshed per the operators' normal vendored-asset sync (the `~/.agents/skills/` copies of done and maintenance), so live sessions load the caller obligations; owner: the execution session's closeout sync step as the preferred first arm, and unconditionally a vendored-sync backlog item naming `agents/skills/done/SKILL.md` and `agents/skills/maintenance/prompt-templates.md` (left even when the sync step is claimed, closed only on grep evidence for the inserted obligation text in both twins AND for the contract advertising in the synced scripts copy (`grep -c 'OUTCOME:' <deployed dirt_regression_gate.py>` at least 1, so the caller text never outruns the gate binary it parses). Consumer repositories that run the skills receive them through their own sync.
- [class: OPERATIONS_FOLLOW_UP] The contract's queued migration rows receive one follow-up origin per queued script (naming the script, its consumers, and the contract row), filed by the execution session's completion pass even if no other migration starts this cycle; owner: the execution session's completion pass; closure evidence: each queued script's contract-table row is the subject of a dedicated follow-up origin whose filename carries the script's slug under `docs/history/backlog/` (a row naming multiple files closes with one dedicated origin per named file, each filename carrying that file's distinguishing stem, e.g. done-sweep-gates-lib and done-sweep-gates; a parenthetical-labeled row uses the parenthetical filename's slug, e.g. scan-public-hygiene; index files such as PLAN-PROMPTS.md are excluded from the count). Until a row's origin exists, that script holds its legacy exit semantics and makes no contract-coverage claim.

## Review Scope

- `docs/history/plans/2026-10-02-script-outcome-contract.md`
- `scripts/OUTCOME_CONTRACT.md`
- `scripts/dirt_regression_gate.py`
- `scripts/test_dirt_regression_gate.py`
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`
- `scripts/test_parallel_work_regressions.py`
- `docs/history/backlog/2026-10-02-script-indeterminate-results-and-agent-escalation.md`

## Validation Commands

Authoring-time records: (1) Rule 19 RED-today evidence: the witnessed residual re-derived 2026-10-02 in the authoring worktree at base 98310582: a restored binary file's `git diff HEAD --unified=0` output carries `Binary files a/app.txt and b/app.txt differ` and no hunk headers, so `_hunks` returns an empty list and the gate prints `dirt gate: PASS` and exits 0; file suite baseline 15 passed. (2) Baselines on the base tree, 2026-10-02: `bash scripts/check_maintenance_pins.sh` exit 0; the two gate pins (lines 1440, 1442) key caller literals this plan preserves; exit-2 asserts at test lines 183, 193, and test_parallel_work_regressions.py line 329 (each re-read and context-anchored); the machinery inventory carries the gate under `reverse-squash-dirt-gates`. (3) Rule 29 pre-round gates on the plan bytes: em-dash `touched` exit 0; public-hygiene scan exit 0; `plan_readiness.py --pre-round` clean (with the facts copy in the worktree, the gate being untracked-primary-only). (4) Rule 22 mechanical audit plus rule 44 extraction proof: the plan's fences were extracted mechanically (signature-keyed; the validation fence precedes the task fences) and applied to a scratch clone of main with the plan committed onto the clone's main first (execution semantics), then the ENTIRE Validation block was executed end to end from the extracted bytes with exit 0, and the flip probes (contract document deleted; the gate's indeterminate arm reverted; a caller obligation line deleted) each aborted fail-closed with their own diagnostics; both flips restored and the block re-ran green. (5) r1 fold receipt and later receipts: recorded as rounds land.

```bash
set -e
# Executor note: run from the repository root. set -e makes the block fail
# closed: the first failing check aborts with its own non-zero status. Each
# byte-level arm carries its own diagnostic.

# 0) the validated bytes are the branch's bytes (bind the working tree to
#    HEAD before any arm reads it)
[ -z "$(git status --porcelain -- scripts/OUTCOME_CONTRACT.md scripts/dirt_regression_gate.py scripts/test_dirt_regression_gate.py scripts/test_parallel_work_regressions.py agents/skills/done/SKILL.md agents/skills/maintenance/prompt-templates.md)" ] || { echo "check 0: validation targets dirty against HEAD:"; git status --porcelain -- scripts/OUTCOME_CONTRACT.md scripts/dirt_regression_gate.py scripts/test_dirt_regression_gate.py scripts/test_parallel_work_regressions.py agents/skills/done/SKILL.md agents/skills/maintenance/prompt-templates.md; exit 1; }

# 1) public hygiene (exit 0 required)
bash ~/.ai-playbook/scripts/scan-public-hygiene.sh

# 2) em-dash gate over the changed bytes against main
bash scripts/check-no-em-dash.sh added-lines --base main

# 3) the full pins suite (the two gate pins key preserved caller text; exit 0 required)
bash scripts/check_maintenance_pins.sh

# 4) the migrated gate's suite, new outcome fixtures included (exit 0 required)
TEST_PY="$(~/.agents/venvs/ai-playbook-test/bin/python -c 'import pytest' 2>/dev/null && echo ~/.agents/venvs/ai-playbook-test/bin/python || command -v python3)"
"$TEST_PY" -m pytest scripts/test_dirt_regression_gate.py -q
tc="$("$TEST_PY" -m pytest scripts/test_dirt_regression_gate.py --collect-only -q 2>/dev/null | grep -c '::')"
[ "$tc" -eq 25 ] || { echo "check 4: dirt gate test collection drifted: $tc != 25"; exit 1; }

# 5) the sibling caller suite stays green (its exit-3 tool-error assert updated)
"$TEST_PY" -m pytest scripts/test_parallel_work_regressions.py -q

# 6) landed bytes: the contract exists, the gate carries the indeterminate and
#    tool-error arms, and both callers carry the obligation text (each count 1)
[ "$(grep -c 'OUTCOME: <pass|fail|indeterminate|tool_error>' scripts/OUTCOME_CONTRACT.md)" -eq 1 ] || { echo "check 6: contract convention line count"; exit 1; }
[ "$(grep -c 'dirt INDETERMINATE' scripts/dirt_regression_gate.py)" -eq 1 ] || { echo "check 6: gate indeterminate line count"; exit 1; }
[ "$(grep -c 'OUTCOME: fail' scripts/dirt_regression_gate.py)" -eq 1 ] || { echo "check 6: gate fail outcome line"; exit 1; }
[ "$(grep -c 'OUTCOME: fail' scripts/test_dirt_regression_gate.py)" -ge 1 ] || { echo "check 6: fail-outcome test witness"; exit 1; }
[ "$(grep -c 'OUTCOME: tool_error' scripts/dirt_regression_gate.py)" -eq 4 ] || { echo "check 6: gate tool-error outcome lines (the argparse error helper, unresolvable base, missing HEAD, and the per-path git-failure catch)"; exit 1; }
[ "$(grep -c 'outcome contract' agents/skills/done/SKILL.md)" -eq 1 ] || { echo "check 6: done caller obligation count"; exit 1; }
[ "$(grep -c 'outcome contract' agents/skills/maintenance/prompt-templates.md)" -eq 2 ] || { echo "check 6: blueprint caller obligation count (final-merge step + duty line)"; exit 1; }
[ "$(grep -c 'dirt_regression_gate.py --base' agents/skills/maintenance/prompt-templates.md)" -eq 2 ] || { echo "check 6: pinned caller literal drift (the blueprint entry and the final-merge step each carry it once at base)"; exit 1; }
[ "$(grep -c 'dirt_regression_gate.py' agents/skills/done/SKILL.md)" -eq 1 ] || { echo "check 6: pinned done caller literal drift"; exit 1; }

# 7) changed-file scope: main is an ancestor of the execution branch at its
#    tip, and the branch differs from main in exactly the six files (the plan
#    bytes are already on main at execution)
[ "$(git rev-parse main)" = "$(git merge-base main HEAD)" ] || { echo "main is not an ancestor of the execution branch tip"; exit 1; }
[ "$(git diff --name-only main | LC_ALL=C sort)" = "$(printf 'agents/skills/done/SKILL.md\nagents/skills/maintenance/prompt-templates.md\nscripts/OUTCOME_CONTRACT.md\nscripts/dirt_regression_gate.py\nscripts/test_dirt_regression_gate.py\nscripts/test_parallel_work_regressions.py')" ] || { echo "unexpected changed-file set against main:"; git diff --name-only main; exit 1; }
```

### Task 1: the outcome contract document

Files:
- `scripts/OUTCOME_CONTRACT.md` *(new)* (absent at base, verified count 0 at authoring time)

Evidence:
- Validation check 6 (first arm)

One verbatim whole-file insertion; the fence is the byte contract for the new file.

```
# Script outcome contract

Decision-making scripts (scripts that classify or gate agent work: staging,
commits, restoration, cleanup, archival, review closure, landing, or other
workflow transitions) report exactly one of four outcomes:

- **pass** (exit 0): evidence satisfies the script's stated condition.
- **fail** (exit 1): evidence establishes a modeled violation; the offending
  evidence is identified in the script's output.
- **indeterminate** (exit 2): available evidence is insufficient,
  contradictory, partially parsed, or outside the modeled cases; the script
  reports what it observed and what it could not determine and leaves the
  decision to the agent.
- **tool error** (exit 3): the script could not perform its check reliably
  (missing inputs, unsupported data, internal failure, or an unheld
  operating-context assumption). A tool error is never represented as a pass
  or as a domain finding.

## The convention

The exit code and a final stdout line `OUTCOME: <pass|fail|indeterminate|tool_error>`
carry the outcome together; human-readable evidence lines precede the final
line. Callers parse the final `OUTCOME:` line and the exit code together, and
must not infer an outcome from anything else. For a migrated script, a run
that emits no final `OUTCOME:` line (a crash, an interruption, a truncated
capture) is not a pass: treat it as tool error, stop the dependent action,
and re-derive the state from disk. Help and version metadata exits (`--help`, `--version`) emit
no `OUTCOME:` line and sit outside the contract; callers must not invoke
scripts in metadata mode inside gated flows. When a single run classifies
multiple inputs and both regressed and indeterminate paths are observed, the
run reports `indeterminate` (exit 2) and still names every regressed path in
its evidence lines: uncertainty dominates, and the caller stops and
re-derives rather than acting on the definitive subset.

## Caller obligation

An agent must not treat `indeterminate` or `tool error` as pass or fail, and
must not continue a dependent destructive or landing action on such a result:
report the script's observed/could-not-determine or error lines and re-derive
the state from disk before proceeding. Known cases keep deterministic
behavior; escalation is for uncertainty, never a substitute for implementing
expected cases.

## Operating-context assumptions (per script)

An unheld assumption classifies as tool error (environment or invocation
unheld) or indeterminate (input outside the modeled cases), never as a domain
pass or fail.

| Script | Assumptions declared | Status |
| --- | --- | --- |
| `dirt_regression_gate.py` | invocation inside the repository; `--base` resolves to a commit and HEAD exists; listed paths exist in the worktree, are HEAD-tracked, or are staged deletions (an existing worktree path HEAD never tracked classifies clean by design: the gate models reversions of lines HEAD gained since the base, and a path HEAD does not track has no gained lines, so its classification is clean regardless of restored content, including base-era content of a file HEAD deleted; resurrection of such a path is the callers' enumeration and review discipline's responsibility); `git diff` output well-formed; blob content decodable as UTF-8 text (the decode codec is pinned utf-8 strict; non-decodable output is tool error) | migrated (this plan) |
| `landing_parentage_gate.py` |  | queued |
| `plan_readiness.py` |  | queued |
| `validate_review_staging.py` |  | queued |
| `done_sweep_gates_lib.py` / `done_sweep_gates.sh` |  | queued |
| `done-lock.sh` |  | queued |
| `check_plan_origins_closed.py` |  | queued |
| `check_maintenance_pins.sh` |  | queued |
| `prestage_freshness_gate.py` |  | queued |
| `review_thread_gate.py` |  | queued |
| `revert_set_classifier.py` |  | queued |
| `check_cleanup_scope_baseline.py` |  | queued |
| `rearm_on_touch.py` |  | queued |
| public-hygiene scan (`scan-public-hygiene.sh`) |  | queued |

The ranking orders the table by the consequence of a wrong classification
(landing and closeout gates above advisory checks) and by assumption
volatility. The table is the migration register, not a claim of complete
coverage: a decision script absent from it is still outside the contract
until its own row lands. Assumptions are declared at each migration's
authoring, never pre-registered here. Scripts still on legacy semantics keep
their documented exit meanings (several use exit 2 as tool failure) until
their own migration lands; the contract's readings (exit-2-means-
indeterminate and the no-final-OUTCOME-line rule) apply only to migrated
scripts.

## Compatibility note

`dirt_regression_gate.py` migrated 2026-10-02: its former exit 2 (usage and
git-environment errors) became exit 3 (tool error) and exit 2 now means
indeterminate. No caller branched on the old exit 2 (both callers key on the
named `dirt REGRESSION` lines); the gate's output gained the final `OUTCOME:`
line additively.
```

- [ ] Run → expect RED: `test -e scripts/OUTCOME_CONTRACT.md` fails on the base tree (re-derived at main 98310582, 2026-10-02) [class: REPOSITORY_TEST]
- [ ] Create the file with exactly the fenced bytes [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `grep -c 'OUTCOME: <pass|fail|indeterminate|tool_error>' scripts/OUTCOME_CONTRACT.md` prints exactly 1 [class: REPOSITORY_TEST]

### Task 2: the dirt gate reports the four outcomes

Files:
- `scripts/dirt_regression_gate.py`

Evidence:
- Validation checks 4 and 6

Five verbatim edits. Edit (a) replaces the docstring's exit-code paragraph:

```
Exit codes: 0 when no restored path regresses; 1 when at least one path
regresses (one ``dirt REGRESSION`` line per regressed file on stdout); 2 on
usage or git-environment errors (unresolvable ``--base``, missing HEAD, path
outside the repository).
```

with:

```
Outcome contract (scripts/OUTCOME_CONTRACT.md): the gate reports exactly one
of four outcomes as the final ``OUTCOME:`` line on stdout and its exit code.
Exit codes: 0 pass (no restored path regresses); 1 fail (at least one path
regresses; one ``dirt REGRESSION`` line per regressed file on stdout);
2 indeterminate (an observed diff shape the classifier does not model; the
observed and could-not-determine lines precede the OUTCOME line); 3 tool
error (usage or git-environment errors: unresolvable ``--base``, missing
HEAD, a path outside the repository, an absent path HEAD never tracked, any
git failure, or an argparse usage error). Operating-context assumptions this gate's result
depends on, declared per the contract: the invocation runs inside the
repository (checkout context); ``--base`` resolves to a commit and HEAD
exists (branch state); the listed paths exist in the worktree, are HEAD-
tracked, or are staged deletions (input presence); ``git diff`` output is
well-formed and blob content decodable as the pinned utf-8 strict codec.
An unheld assumption surfaces as tool error (exit 3), never as a domain
pass or fail; a diff shape outside the modeled cases surfaces as
indeterminate (exit 2), never as pass. Operating-context assumptions are
declared in scripts/OUTCOME_CONTRACT.md (the authoritative surface).
```

Edit (b) changes `classify_path`'s signature and docstring:

```
def classify_path(path: str, base: str, cwd: Path) -> tuple[bool, str]:
    """Classify one restored path. Returns (is_regression, detail)."""
```

to:

```
def classify_path(path: str, base: str, cwd: Path) -> tuple[str, str]:
    """Classify one restored path. Returns (status, detail).

    status is "regression", "clean", or "indeterminate" per the outcome
    contract (scripts/OUTCOME_CONTRACT.md); "indeterminate" marks a diff
    shape the classifier does not model, never a pass or a fail.
    """
```

Edit (c) inserts the indeterminate arm and rewrites the two returns. Replace:

```
    diff_text = _git("diff", "HEAD", "--unified=0", "--", path, cwd=cwd)
    hunks = _hunks(diff_text)
    removed_counts = Counter(line for removed, _ in hunks for line in removed)
```

with:

```
    diff_text = _git("diff", "HEAD", "--unified=0", "--", path, cwd=cwd)
    hunks = _hunks(diff_text)
    if diff_text.strip() and not hunks:
        # Unmodeled diff shape: content the classifier cannot see (a binary
        # restored file is the witnessed class, and a binary payload riding a
        # mode flip or a rename header is the same class). Modeled hunk-less
        # shapes are PURE rename ("similarity index"/"rename from"/"rename
        # to") or PURE mode change ("old mode"/"new mode") with no binary
        # payload line. Uncertainty is indeterminate, never a silent pass.
        modeled = (
            "Binary files" not in diff_text
            and "GIT binary patch" not in diff_text
            and (
                "similarity index" in diff_text
                or "old mode" in diff_text
                or "new mode" in diff_text
            )
        )
        if not modeled:
            return (
                "indeterminate",
                "diff carries no classifiable hunks (binary or unrecognized "
                "shape); observed "
                f"{len(diff_text.splitlines())} diff lines, could not "
                "determine restored-content polarity",
            )
    removed_counts = Counter(line for removed, _ in hunks for line in removed)
```

then replace:

```
            return True, "restores base-era text over lines HEAD gained"
```

with:

```
            return "regression", "restores base-era text over lines HEAD gained"
```

and replace:

```
    return False, ""
```

with:

```
    return "clean", ""
```

Edit (e) pins the decode codec and converts unsupported data at the single bytes-to-text boundary; replace:

```
def _git(*args: str, cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {proc.stderr.strip()}"
        )
    return proc.stdout


def _git_ok(*args: str, cwd: Path) -> bool:
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True
    )
    return proc.returncode == 0
```

with:

```
def _git(*args: str, cwd: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
        )
    except UnicodeDecodeError:
        # Unsupported data per the outcome contract: output git produced but
        # the gate cannot decode (a non-UTF-8 tracked blob or diff text) is
        # tool error, never a domain pass or fail.
        raise RuntimeError(
            f"git {' '.join(args)} failed: unsupported data: output not "
            "decodable as utf-8 text"
        )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {proc.stderr.strip()}"
        )
    return proc.stdout


def _git_ok(*args: str, cwd: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
        )
    except UnicodeDecodeError:
        # The gate's other decode boundary; both are guarded so a decode
        # failure is tool error everywhere.
        raise RuntimeError(
            f"git {' '.join(args)} failed: unsupported data: output not "
            "decodable as utf-8 text"
        )
    return proc.returncode == 0
```

Routing the conversion through `_git` covers the `git show`, `git diff`, and
`git ls-files` call sites in one stroke; `_blob_lines` keeps its original
two-line body, and the per-path RuntimeError catch in `main` prints the
OUTCOME line and returns 3 unchanged.

Edit (d) routes argparse usage errors through the contract's tool-error
outcome by replacing the parser construction site (the documented extension
point is the error() override; the construction site is the only
`argparse.ArgumentParser(` construction in the file). Replace:

```
    parser = argparse.ArgumentParser(
        description=(
            "Fail on restored dirt hunks that restore merge-base-era text over "
            "content HEAD gained since the given merge base."
        )
    )
```

with:

```
    class _GateParser(argparse.ArgumentParser):
        # Usage errors are tool error (exit 3) per the outcome contract;
        # argparse's documented extension point is the error() override.
        def error(self, message: str) -> None:
            print(f"dirt gate: {message}", file=sys.stderr)
            print("OUTCOME: tool_error")
            raise SystemExit(3)

    parser = _GateParser(
        description=(
            "Fail on restored dirt hunks that restore merge-base-era text over "
            "content HEAD gained since the given merge base."
        )
    )
```

replace:

```
        print(
            f"dirt gate: --base does not resolve to a commit: {args.base}",
            file=sys.stderr,
        )
        return 2
```

with:

```
        print(
            f"dirt gate: --base does not resolve to a commit: {args.base}",
            file=sys.stderr,
        )
        print("OUTCOME: tool_error")
        return 3
```

replace:

```
        print("dirt gate: repository has no HEAD commit", file=sys.stderr)
        return 2
```

with:

```
        print("dirt gate: repository has no HEAD commit", file=sys.stderr)
        print("OUTCOME: tool_error")
        return 3
```

and replace:

```
    regressed: list[str] = []
    for path in args.paths:
        try:
            is_regression, detail = classify_path(path, args.base, cwd)
        except RuntimeError as exc:
            print(f"dirt gate: {exc}", file=sys.stderr)
            return 2
        if args.stamp:
            _report_stamp(path, sys.stdout, sys.stderr)
        if is_regression:
            regressed.append(path)
            print(f"dirt REGRESSION: {path} ({detail} since {args.base[:12]})")

    if regressed:
        return 1
    print(f"dirt gate: PASS ({len(args.paths)} file(s) checked)")
    return 0
```

with:

```
    regressed: list[str] = []
    indeterminate: list[str] = []
    for path in args.paths:
        try:
            status, detail = classify_path(path, args.base, cwd)
        except RuntimeError as exc:
            print(f"dirt gate: {exc}", file=sys.stderr)
            print("OUTCOME: tool_error")
            return 3
        if args.stamp:
            _report_stamp(path, sys.stdout, sys.stderr)
        if status == "regression":
            regressed.append(path)
            print(f"dirt REGRESSION: {path} ({detail} since {args.base[:12]})")
        elif status == "indeterminate":
            indeterminate.append(path)
            print(f"dirt INDETERMINATE: {path} ({detail})")

    if indeterminate:
        # Uncertainty dominates a mixed run (the contract's precedence rule):
        # every regressed path is still named in the evidence lines above, and
        # the caller stops and re-derives instead of acting on the subset.
        print("OUTCOME: indeterminate")
        return 2
    if regressed:
        print("OUTCOME: fail")
        return 1
    print(f"dirt gate: PASS ({len(args.paths)} file(s) checked)")
    print("OUTCOME: pass")
    return 0
```

- [ ] Run → expect RED: the file at base has no `dirt INDETERMINATE` line and exits 0 on a hunk-less diff (the witnessed residual; re-derived at main 98310582, 2026-10-02) [class: REPOSITORY_TEST]
- [ ] Apply edits (a) through (e), each anchor single-occurrence (verified count 1 at authoring time) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `python3 -m py_compile scripts/dirt_regression_gate.py` exits 0, and the gate's literals land: `grep -c 'dirt INDETERMINATE' scripts/dirt_regression_gate.py` prints exactly 1, `grep -c 'OUTCOME: tool_error' scripts/dirt_regression_gate.py` prints exactly 4 (the _GateParser error override, the unresolvable-base arm, the missing-HEAD arm, and the per-path git-failure catch), and `grep -c 'OUTCOME: pass' scripts/dirt_regression_gate.py` prints exactly 1 [class: REPOSITORY_TEST]

### Task 3: the callers branch on every outcome

Files:
- `agents/skills/done/SKILL.md`
- `agents/skills/maintenance/prompt-templates.md`

Evidence:
- Validation check 6 (arms 5 through 8)

Three verbatim edits: one insertion (a) and two context-anchored replaces (b, c). Edit (a) in `agents/skills/done/SKILL.md`, inserted immediately after the pre-commit guard's closing witness parenthetical:

```
(Witness: 2026-07-23 group-leftover-crypto-warnings r6; see project `development_lessons.md` lesson on this family.)
```

inserting (one space after, same paragraph):

```
 The gate reports the outcome contract's four outcomes (scripts/OUTCOME_CONTRACT.md, final `OUTCOME:` line): on pass proceed; on fail restore the named files; on indeterminate or tool error stop this staging pass (do not stage or commit): report the gate's observed/could-not-determine or error lines and re-derive the tree from disk before any further staging. A run that emits no final `OUTCOME:` line is tool error under the contract: stop and re-derive. An indeterminate or tool-error result is never treated as pass or fail, and no dependent destructive or landing action continues on it.
```

Edit (b) in `agents/skills/maintenance/prompt-templates.md`; replace the anchor line (single occurrence, verified at authoring time):

```
not trigger the release/keep-branch abort; then verify the landed commit on the repository's default branch:
```

with:

```
not trigger the release/keep-branch abort; the gate reports the outcome contract's four outcomes (scripts/OUTCOME_CONTRACT.md, final `OUTCOME:` line): a finding is fail (remedy in place as above); an indeterminate or tool-error result stops the merge step (do not delete the branch, do not report the merge complete; take the gate-failure release arm: release via merge-release-repo with the acquired exports, keep the branch, and report): report the gate's lines and re-derive the landed tree from disk outside the held critical section before retrying; only a determinate pass or fail verdict proceeds to branch deletion; a run that emits no final `OUTCOME:` line is tool error under the contract and stops the merge step the same way; then verify the landed commit on the repository's default branch:
```

Edit (c) extends the changelog duty sentence in `agents/skills/maintenance/prompt-templates.md` (the duty line summarizes the step's contract; keeping it one-outcome would preserve the stale mental model); replace:

```
a finding is remedied in place (restore the regressed file from HEAD, one summary line per restored file) and is NOT a gate failure triggering the release/keep-branch abort.
```

with:

```
a finding is remedied in place (restore the regressed file from HEAD, one summary line per restored file) and is NOT a gate failure triggering the release/keep-branch abort; the gate reports the outcome contract's four outcomes (scripts/OUTCOME_CONTRACT.md), and an indeterminate or tool-error result stops the merge step per the final-merge paragraph's release arm.
```

- [ ] Apply edits (a) through (c) (each anchor single-occurrence; verified at authoring time) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `grep -c 'outcome contract' agents/skills/done/SKILL.md` prints exactly 1, `grep -c 'outcome contract' agents/skills/maintenance/prompt-templates.md` prints exactly 2 (the final-merge step and the duty line), and both pinned caller literals hold (`grep -c 'dirt_regression_gate.py --base' agents/skills/maintenance/prompt-templates.md` prints exactly 2, its base count; `grep -c 'dirt_regression_gate.py' agents/skills/done/SKILL.md` prints exactly 1), and `bash scripts/check_maintenance_pins.sh` exits 0 [class: REPOSITORY_TEST]

### Task 4: the test suites carry the outcome fixtures

Files:
- `scripts/test_dirt_regression_gate.py`
- `scripts/test_parallel_work_regressions.py`

Evidence:
- Validation checks 4 and 5

Four verbatim edits. Edit (a) updates the two fail-closed asserts in `scripts/test_dirt_regression_gate.py`; replace:

```
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not inside repository", proc.stderr)
```

with:

```
        self.assertEqual(proc.returncode, 3)
        self.assertIn("not inside repository", proc.stderr)
```

and replace:

```
        self.assertEqual(proc.returncode, 2)
        self.assertIn("does not exist", proc.stderr)
```

with:

```
        self.assertEqual(proc.returncode, 3)
        self.assertIn("does not exist", proc.stderr)
```

Edit (b) appends ten fixtures at the end of `DirtRegressionGateTest` in the same file, inserted immediately before the file's `if __name__ == "__main__":` guard (end of class scope, one blank line after the final test method; the guard occurs exactly once, verified at authoring time):

```
    def test_binary_dirt_is_indeterminate(self) -> None:
        base_sha = self._seed_head_gained_lines()
        # Dirt replaces the text file with binary bytes: the diff carries the
        # Binary files line and no hunks, the witnessed unmodeled shape.
        (self.repo / "app.txt").write_bytes(b"\x00\x01\x02binary\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 2, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt INDETERMINATE", stdout)
        self.assertIn("could not", stdout)
        self.assertIn("OUTCOME: indeterminate", stdout)

    def test_binary_dirt_with_mode_flip_is_indeterminate(self) -> None:
        base_sha = self._seed_head_gained_lines()
        # Binary dirt riding a mode flip: the diff carries old/new mode lines
        # AND the Binary files line; the payload is still unclassifiable.
        target = self.repo / "app.txt"
        target.write_bytes(b"\x00\x01\x02binary\n")
        import os as _os
        _os.chmod(target, 0o755)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 2, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: indeterminate", stdout)

    def test_mode_change_dirt_stays_clean(self) -> None:
        base_sha = self._seed_head_gained_lines()
        # A pure mode flip with no content change is a modeled hunk-less
        # shape and stays clean (the preserved known case).
        import os as _os
        _os.chmod(self.repo / "app.txt", 0o755)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: pass", stdout)

    def test_mixed_regression_and_indeterminate_reports_indeterminate(self) -> None:
        base_sha = self._seed_head_gained_lines()
        self._commit("bin.dat", "text\n", "tracked binary candidate")
        # Mixed batch: one true regression plus one binary-restored TRACKED
        # path (an untracked path is invisible to git diff HEAD and is not a
        # gate input). Uncertainty dominates the verdict (exit 2) and both
        # evidence lines are still printed for the caller.
        self._set_dirt("app.txt", BASE_TEXT)
        (self.repo / "bin.dat").write_bytes(b"\x00\x01binary\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt", "bin.dat")
        self.assertEqual(code, 2, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("dirt REGRESSION: app.txt", stdout)
        self.assertIn("dirt INDETERMINATE: bin.dat", stdout)
        self.assertIn("OUTCOME: indeterminate", stdout)

    def test_nonutf8_blob_is_tool_error(self) -> None:
        # A tracked blob git cannot decode as text is unsupported data: the
        # gate reports tool error, never a domain verdict (contract Terms).
        self._commit("seed.txt", "seed\n", "seed")
        blob = self.repo / "bin.dat"
        blob.write_bytes(b"\xff\xfe\x00binary\xff\n")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "binary blob")
        blob.write_bytes(b"\xff\xfe\x00binary\xff\nmore\n")
        code, stdout, stderr = self._run_gate("--base", "HEAD", "bin.dat")
        self.assertEqual(code, 3, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("unsupported data", stderr)
        self.assertIn("OUTCOME: tool_error", stdout)

    def test_nonutf8_worktree_dirt_is_tool_error(self) -> None:
        base_sha = self._seed_head_gained_lines()
        # NUL-free non-UTF-8 dirt: git diffs it as text, the gate cannot
        # decode the diff output, and the contract routes it to tool error.
        (self.repo / "app.txt").write_bytes(
            HEAD_TEXT.encode("utf-8") + b"caf\xe9-latin1\n"
        )
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 3, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("unsupported data", stderr)
        self.assertIn("OUTCOME: tool_error", stdout)

    def test_usage_error_is_tool_error(self) -> None:
        self._commit("seed.txt", "seed\n", "seed")
        code, stdout, stderr = self._run_gate("--no-such-flag", "seed.txt")
        self.assertEqual(code, 3, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: tool_error", stdout)

    def test_missing_head_is_tool_error(self) -> None:
        empty = self.tmp / "empty-repo"
        empty.mkdir()
        self._git("init", "-q", "-b", "main", cwd=empty)
        (empty / "x.txt").write_text("x\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--base", "main", "x.txt"],
            capture_output=True,
            text=True,
            cwd=str(empty),
            env=self._git_env(),
        )
        self.assertEqual(proc.returncode, 3, f"stderr: {proc.stderr}")
        self.assertIn("OUTCOME: tool_error", proc.stdout)

    def test_unresolvable_base_is_tool_error(self) -> None:
        self._commit("seed.txt", "seed\n", "seed")
        code, stdout, stderr = self._run_gate(
            "--base", "0" * 40, "seed.txt"
        )
        self.assertEqual(code, 3, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: tool_error", stdout)

    def test_outcome_final_line_pass(self) -> None:
        base_sha = self._seed_head_gained_lines()
        self._set_dirt("app.txt", HEAD_TEXT + "forward-note\n")
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 0, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("OUTCOME: pass", stdout)
```

Edit (c) witnesses the fail outcome's machine-readable line in the existing regression fixture; replace (the anchor is the method head through its three asserts, unique in the file because two sibling regression tests repeat the tail asserts without the head):

```
    def test_reverting_hunk_is_regression(self):
        base_sha = self._seed_head_gained_lines()
        # Dirt restores the exact base-era file: a byte-identical whole-file
        # revert of content HEAD gained since the merge base.
        self._set_dirt("app.txt", BASE_TEXT)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("app.txt", stdout)
        self.assertIn("dirt REGRESSION", stdout)
```

with:

```
    def test_reverting_hunk_is_regression(self):
        base_sha = self._seed_head_gained_lines()
        # Dirt restores the exact base-era file: a byte-identical whole-file
        # revert of content HEAD gained since the merge base.
        self._set_dirt("app.txt", BASE_TEXT)
        code, stdout, stderr = self._run_gate("--base", base_sha, "app.txt")
        self.assertEqual(code, 1, f"stderr: {stderr}; stdout: {stdout}")
        self.assertIn("app.txt", stdout)
        self.assertIn("dirt REGRESSION", stdout)
        self.assertIn("OUTCOME: fail", stdout)
```

Edit (d) in `scripts/test_parallel_work_regressions.py` carries three replaces. Replace:

```
        proc = self._run_dirt_gate("--base", base_sha, "ghost.txt")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("does not exist or is not a tracked file", proc.stderr)
```

with:

```
        proc = self._run_dirt_gate("--base", base_sha, "ghost.txt")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("does not exist or is not a tracked file", proc.stderr)
```

replace:

```
        never-tracked ghost path still fails closed with exit 2."""
```

with:

```
        never-tracked ghost path still fails closed with exit 3 (tool error)."""
```

and replace:

```
        # the rc 2 git-environment error this family used to produce.
```

with:

```
        # the rc 3 tool error this family used to produce.
```

- [ ] Run → expect RED: after Task 2 and before this task's edits, `pytest scripts/test_dirt_regression_gate.py` collects 15 and fails the two asserts at lines 183 and 193, and `pytest scripts/test_parallel_work_regressions.py` fails the assert at line 329 (three failures across the two files, each actual 3 != expected 2 after Task 2's remap); at base both suites are green (15 and 3 collected), and a hand-run binary-shape case against the base gate exits 0 (the witnessed residual); no binary-shape fixture exists until edit (b) (re-derived 2026-10-02) [class: REPOSITORY_TEST]
- [ ] Apply edits (a) through (d) (each context-anchored replace single-occurrence; verified at authoring time) [class: IMPLEMENTATION_REQUIRED]
- [ ] Run → expect GREEN: `~/.agents/venvs/ai-playbook-test/bin/python -m pytest scripts/test_dirt_regression_gate.py -q` exits 0 with 25 collected, and `~/.agents/venvs/ai-playbook-test/bin/python -m pytest scripts/test_parallel_work_regressions.py -q` exits 0 [class: REPOSITORY_TEST]
- [ ] Commit: `scripts: outcome contract (pass, fail, indeterminate, tool error) wired into the dirt gate and its callers` [class: IMPLEMENTATION_REQUIRED]

### Task 5: validation

Files:
- none; verification-only task

Evidence:
- the full Validation Commands block

- [ ] Run the full Validation Commands block from the repository root; every line exits 0 [class: REPOSITORY_TEST]

## Residual findings (cap closure)

(none at authoring time; this section records the cap round's dispositions if the loop reaches its configured cap)

## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-02-script-indeterminate-results-and-agent-escalation.md`: this plan's own promoted origin. On completion, fold disposition into the archived plan (contract landed, gate migrated, callers bound, ranked inventory recorded, tail follow-up origins filed) and delete the origin file in the same completion pass per the archive gate.
