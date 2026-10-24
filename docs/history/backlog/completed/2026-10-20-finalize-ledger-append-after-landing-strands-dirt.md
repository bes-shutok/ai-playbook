# Backlog: finalize's guard-liveness ledger append lands on a tracked file after the landing commit, stranding dirt

- **Filed:** 2026-10-20, done closeout of the execute-plan description fix (learn Step 1.8 capture, second cycle)
- **Status:** covered (docs/history/plans/2026-10-24-done-run-lock-span-and-append-ordering.md)
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** session-witnessed runner ordering friction (twice witnessed)
- **Class:** fix-class
- **Driving force:** simplicity (one closeout should land its own records; today a catch-recording run needs a second full setup, learn, commit, finalize cycle, or leaves tracked dirt)
- **Skill/step:** `agents/skills/done/SKILL.md` Step 6 (finalize advisory appends: `--guard-firing`); `scripts/done_run.sh` finalize `advisory-appends` stage; `scripts/gate_liveness_ledger.py record`; the tracked ledger `scripts/gate_liveness_ledger.json`
- **Capture hygiene:** repo-relative paths only; no personal or machine-specific data.
- **Dedup probe:** searched open backlog text for `gate_liveness_ledger`, `guard-liveness`, `ledger append`, `advisory append`; nearest rows are `2026-10-13-done-landing-commit-lock-span.md` (the owned-commits ledger and lock spans, not the guard-liveness file), `2026-10-11-lock-span-review-hardening-nits.md` item 4 (an evidence pointer inside one ledger row), and `2026-10-20-done-run-authorized-restoration-hardening-candidates.md` item 7 (the owned-commits ledger gap on the authorized path); no open row owns the guard-liveness append's placement after the landing commit.

- **Cluster:** docs/history/backlog/completed/2026-10-20-done-setup-classification-stop-holds-lock-blocks-retry.md (shared mechanism: same runner or gate family; investigate 2026-10-20 roster)
- **Cluster:** docs/history/backlog/completed/2026-10-13-done-landing-commit-lock-span.md (shared mechanism: same runner or gate family; investigate 2026-10-20 roster)
## Problem

`done_run.sh finalize` appends each `--guard-firing` row to `scripts/gate_liveness_ledger.json` in its advisory-appends stage, which runs after the landing commit (made by the commit subcommand) and immediately before the done-lock release. The ledger is a tracked file (the machinery admission protocol cites its catch counts as promotion evidence, so tracking is intended). The result of every catch-recording closeout is therefore a modified tracked file with the lock released and no commit step left in the run: the dangling-change stop names it, and the only in-contract remedies are a second full cycle or standing down with the dirt recorded.

Witnessed twice: on 2026-10-19 the cached-diff catch landed as a standalone follow-up commit (`chore: record cached-diff incident`, ledger file only); on 2026-10-20 the description-length catch (lesson 135) left the ledger dirty after a passing finalize and this closeout ran a second setup, learn, commit, finalize cycle to land one row.

## Expected

A closeout that records a guard firing lands the ledger row inside the same run, under the same lock, with no second cycle and no tracked residue.

## Suggested fix

Smallest form first:

1. Accept `--guard-firing` on the commit subcommand and perform the ledger append before the landing sweep, so the row rides the landing commit as a declared staged path (the sweep gates then see it like any other owned edit). Finalize keeps accepting the flag for runs with no landing commit.
2. On the finalize path, when a ledger append changed a tracked file and the lock is still held, land it as one additive commit before the release (the shape the 2026-10-19 precedent already used by hand), or refuse the append with a named error naming option 1.

Rejected: making the ledger gitignored runtime state (its catch counts are the tracked promotion evidence the protocol reads); documenting the second cycle as the procedure (it doubles closeout cost to land one line, the opposite of the admission protocol's fewer-blockers direction).

## Witness 2026-10-20 (learn capture, scheduled authoring run): the appended evidence string is unscanned

A third firing landed the same shape (tracked ledger dirty, lock released, no commit step left), and its two appended `incident` rows carry free-text `evidence` strings naming a foreign ticket prefix and a pre-landing sha. The `--guard-firing <gate>:catch:<evidence>:<note>` path writes the evidence verbatim into a tracked file that the public hygiene scan only sees at the next explicit commit, so a closeout that lands the row per fix 1 or 2 above would carry the prefix onto the base branch unless the append itself runs the hygiene deny-pattern scan over the evidence and note fields and refuses or masks a hit before writing. Add that scan to whichever fix lands (the ledger is tracked promotion evidence and this repository is public). Priority re-affirmed: high.
