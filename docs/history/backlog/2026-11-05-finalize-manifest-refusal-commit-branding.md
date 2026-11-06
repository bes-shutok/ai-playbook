# Backlog: finalize --manifest refusals diagnose under the commit subcommand's branding with a false "nothing committed" claim

- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** execution code review r1 of this run (2026-11-05-done-finalize-resume-marking-honesty)
- **Class:** fix-class (diagnostic branding correction; no behavior change)
- **Driving force:** observability
- **Secondary force:** simplicity (the doubled diagnostic print rides the same row)
- **Source:** `.ai-playbook/reviews/2026-11-05-done-finalize-resume-marking-honesty-code-review-r1.md`, round r1, finding F7 (Low, non-blocking); captured by the r1 address pass per the receiving-review Backlog capture flow
- **Dedup probe:** keyword search over the open backlog corpus filenames and Problem bodies (`resolve_manifest`, `manifest selection`, `nothing committed`, `commit branding`, `finalize diagnostic`) returned no matching item; the nearest family (`2026-10-06-done-boundary-review-candidates.md`) concerns held-lock fixture witnesses, not resolver diagnostic branding. No merge candidate; distinct root cause.
- **Capture hygiene:** scan-public-hygiene --files pass (2026-11-05, exit 0, OUTCOME: pass)

## Problem

Task 2 of the plan wired finalize's `--manifest` through `resolve_manifest_path` for the first time, making the resolver's explicit-arm diagnostics reachable from finalize. Those diagnostics are commit-branded and claim a commit outcome finalize never owns: an operator following done SKILL.md Step 6 who passes a missing or shadow-named `--manifest` reads, twice (cmd_finalize's resolve plus resolve_run_id's internal re-resolution), `done_run commit: run manifest selection: ...; nothing committed` on a finalize invocation. The true disposition (the unbound-resolution refusal, or the fallback resolution the invocation went on to evaluate) is stated by the following finalize lines, but the doubled, wrongly-branded diagnostic costs a misdirection round: it attributes the refusal to `done_run commit` and asserts "nothing committed" about a subcommand that was never invoked.

## Exact location

- `scripts/done_run.sh`, `resolve_manifest_path` explicit-arm diagnostics (the commit-branded `done_run commit: run manifest selection: ...` emissions, including the two "noncanonical shadow name" refusals and the "missing or unreadable" refusal; `nothing committed` in each)
- The finalize reachability: `cmd_finalize`'s resolve call and `resolve_run_id`'s internal re-resolution, both downstream of Task 2's `COMMIT_MANIFEST="$FINALIZE_MANIFEST"` wiring (plan `docs/history/plans/completed/2026-11-02-done-finalize-resume-marking-honesty.md`, Task 2; archived 2026-11-05 at the execution landing)

## Suggested fix

Thread a caller label through `resolve_manifest_path`'s diagnostics: the label defaults to `commit` (the frozen commit-path echo surface and its pins stay byte-identical), and finalize sets its own label (`done_run finalize: run manifest selection: ...`) with a finalize-accurate outcome clause replacing "nothing committed". Dedupe of the doubled print (cmd_finalize's resolve and resolve_run_id's internal re-resolution emitting the same diagnostic twice) rides the same row. Options considered: suppressing the resolver diagnostics under finalize (loses the named cause the refusal advice points back to) - rejected; post-filtering the finalize-visible lines (fragile string coupling to a frozen surface) - rejected in favor of the label parameter.

## Why not fixed now

Dropped at the r1 address pass (round r1 of the code review above): the remedy reshapes the resolver's echo surface that the frozen commit-path contract text and its pins depend on; the frozen commit surface must stay byte-identical, and the churn risk to a frozen-adjacent shared surface outweighs a Low naming-level misdirection whose true disposition the following finalize lines state correctly. Decision made by the r1 address pass (execution code review, receiving-review Backlog capture).

## Ship when

A finalize `--manifest` refusal diagnoses under the finalize label with no "nothing committed" claim, the commit-path diagnostics are byte-identical to today (existing pins green), and the doubled print is deduped or named as accepted cost.
