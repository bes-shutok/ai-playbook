# plan-readiness host gate

Desired host-level enforcement around the agent-agnostic readiness validator
`scripts/plan_readiness.py`: block the agent's FINAL response in a session whose
deliverable is a plan file, when that plan's latest review round does not report
`ready=yes` over the current plan bytes (stale digest, missing or malformed
`.stats.json` sidecar, `ready=no` verdict, or unresolved blocking findings).

## What the gate would do

Before the final response is delivered, run the validator with the project git
root as cwd, resolving the script via env-var override with two fallbacks
(repo-local copy if present, then the deployed runtime copy):

```bash
GATE_TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PLAN_READINESS_VALIDATOR="${PLAN_READINESS_VALIDATOR:-}"
if [ -z "$PLAN_READINESS_VALIDATOR" ] && [ -f "$GATE_TOP/scripts/plan_readiness.py" ]; then
  PLAN_READINESS_VALIDATOR="$GATE_TOP/scripts/plan_readiness.py"
fi
PLAN_READINESS_VALIDATOR="${PLAN_READINESS_VALIDATOR:-$HOME/.ai-playbook/scripts/plan_readiness.py}"
python3 "$PLAN_READINESS_VALIDATOR" <plan-path>
```

Exit 0 releases the response; a non-zero exit (with its first-failed-condition
reason) blocks it, so an unreviewed or post-review-edited plan cannot be
presented as ready for execution. This mirrors what the `skill-gate` adapters do
for gated writes, but at the session-finalization boundary instead of the
tool-call boundary. Where the runtime copy of the validator resolves is
governed by the deployment note below.

**Deployment note:** the validator's canonical copy lives at
`scripts/plan_readiness.py` in the skills repository; the command above resolves
the runtime copy at `~/.ai-playbook/scripts/plan_readiness.py` (overridable via
`PLAN_READINESS_VALIDATOR`). The runtime copy is deployed as a symlink to the
canonical repo file (decision recorded in
`docs/history/backlog/completed/2026-09-04-deploy-plan-readiness-runtime-copy.md`);
if that symlink is removed, the command resolves to a path that does not exist
and fails loudly rather than silently passing.

Sibling compatibility handshake: `validate_review_staging.py` declares
`COMPAT_VERSION`; the readiness validator checks it at every launch (gate,
sweep, and selftest modes) and fails loudly on a missing or mismatched value.
The check catches a partially updated deployment in both repo-local and
runtime copies, and post-symlink-unification it also trips when a symlink is
replaced by a stale snapshot copy unless the whole pair was replaced together
(the both-stale-consistent case stays invisible; accepted Low-severity
residual). The check lives ONLY in the plan_readiness launch path;
validate_review_staging.py never imports plan_readiness.

## Current host limitation (documented, not hidden)

Hosts differ in what final-response events they expose. Claude Code ships a
blocking Stop-adjacent event (the `Stop` hook can block the turn's final
response); the current Codex host cannot block the final response: its config
surface carries only `post_tool_use` (which cannot block) and one-shot
`SessionStart` arrays, with no stop/final-response event to register a blocker
against. The capability is recorded as UNSUPPORTED per agent in
`scripts/hooks_probe.py` (see the table below) because no adapter is
implemented in this install for ANY host (including Claude): the scope decision
is to ship the enforcement unwired and flip rows via the wiring recipe when an
adapter is actually built. Hosts that do expose a stop-adjacent event are the
natural first candidates for that recipe.

This is also a payload rule: an event that cannot block, or cannot carry the
plan path and review evidence needed by the validator, cannot enforce the
policy. Keep that protocol translation in a thin per-runtime adapter. The
agent-neutral validator and the runtime profile registry remain the sources of
truth; the capability probe reports missing adapter, missing registration,
unsupported event, and degraded fallback separately and fails closed for
malformed adapter data.

**Round-4 adjudication:** the plan-review r4 round raised that Claude Code
ships a blocking `Stop` event, contradicting an earlier "no supported host
ships such an event" claim. This wording resolves that finding: the honest
statement is host divergence plus unwired-by-scope, not universal absence.

## Compensating enforcement until a host event exists

Until an adapter is wired for a host, enforcement is carried by the skill-layer
gates, both fail-closed:

- **Execution gate** (`execute-plan` Step 0.5, "Plan readiness gate"): runs
  the readiness validator before any task implementation; a non-zero exit is a
  hard stop with the first failed readiness condition, and any plan edit
  (digest change) requires a fresh `review-plan` round before re-execution.
- **Finalization gate** (`done` skill): runs the same validator before
  finalizing a plan-creation session and refuses to finalize on failure, except
  when the user explicitly chooses to stop without finalization and that choice
  is recorded in the session log.

The validator itself is the single source of readiness truth; both gates call
it rather than re-implementing its conditions.

## Verdict representation (consumer rule and precedence)

The validator's consumer rule for the verdict is a TOTAL rule: any line in the
review's `## Summary` containing a word-bounded `ready=yes` / `ready=no` token
is a verdict line, and the LAST occurrence in the section wins. A prose
mention is a verdict under this rule; the fail-open concern is covered by the
other readiness conditions (sidecar schema, digest match, `is_review_ready`
zero-blocking). The producer contract (`review-plan` skill) now mandates a
final canonical line exactly `Verdict: ready=yes` or `Verdict: ready=no` in
every round's `## Summary`, so post-adoption artifacts never depend on legacy
shapes. Consumer precedence is sidecar verdict field > Summary total rule (per-line, last occurrence wins): when the latest round's sidecar carries a `verdict` field (`yes`/`no`,
written by `review-plan` since the 2026-09-05 plan-readiness-migration plan),
it decides; artifacts whose sidecar lacks the field fall back to that rule. Deleting the legacy Summary grammar is TIME-GATED: eligible only
once `--sweep` coverage reports a positive total with covered equal to total
over the live plan-review corpus; tracked in
`docs/history/backlog/2026-09-05-plan-readiness-legacy-verdict-grammar-deletion.md`.

Legacy review artifacts that predate the `## Summary` convention can never
pass readiness (fail-closed by design); the producer contract now mandates
`## Summary`.

## Drift check: `--sweep`

`python3 scripts/plan_readiness.py --sweep` sweeps `{reviews_dir}` (from the
facts TOML) for `*-plan-review-*.md` files whose `## Summary` text contains a
`ready=` mention but whose parse under the total rule yields no verdict token
(cross-line or malformed cases; there should be none). Exit 0 when zero
anomalies, exit 1 listing them. A configured `reviews_dir` that is missing on
disk exits 1 with its own reason (never a silent zero-artifact pass), and
`--sweep` takes no plan operand. The sweep also prints a coverage line
counting live plan-review artifacts whose sidecar carries a conforming
`verdict` field; it is informational and never changes the exit code. Wiring
note: review-loop runs this sweep before every round (its verdict-shape drift
check).

Sweep limits (known blind spots; r5 Y11):

- **Wrong winner, last-wins hazard**: when a Summary carries multiple verdict
  tokens, only the LAST one decides; an earlier, semantically intended
  `ready=yes` superseded by a stray later `ready=no` (or vice versa) is
  invisible to the sweep, which only checks mention-vs-token presence.
- **Verdicts without `=`**: a Summary that communicates its verdict without a
  `ready=` token (e.g. prose "the plan is ready") never fires the mention
  regex and is invisible to the sweep (the readiness gate itself rejects it,
  fail-closed).
- **Summary-less artifacts**: review artifacts without a `## Summary` section
  yield an empty Summary and are invisible to the sweep.
- **Negated mentions**: under the adjudicated total rule, a token inside a
  negation ("no longer holds... ready=yes" style) still counts as a verdict
  token (r5 Y13 residual, accepted; mitigated by the sidecar schema/digest
  and zero-blocking conditions).

Future option (backlogged, not wired): flag Summaries carrying multiple
verdict tokens so last-wins supersession gets human eyes.

## Wiring recipe (add when a host event ships)

When a host gains a blocking final-response (stop-equivalent) event:

1. Author an adapter under `agents/hooks/plan-readiness/` per agent (modeled
   on the `agents/hooks/skill-gate/` adapters; follow every adapter invariant
   documented in `agents/hooks/skill-gate/README.md` rather than restating them
   here): derive the plan path for the session's deliverable, run the readiness
   validator with the env-override resolution shown above, with a host-level
   hook timeout of at least 10 seconds, and translate the non-zero exit into
   the host's block contract.
2. Symlink the adapter into the host's hooks directory (as the skill-gate
   install block does) and register it under the new event in the host config,
   preserving every existing wired hook.
3. Flip that agent's `plan-readiness` row in the `PROBE_MATRIX` of
   `scripts/hooks_probe.py` from UNSUPPORTED to the wired expectation
   (FULL or DEGRADED), and update the `frozen_agents_listed` cell
   count if rows change. Detecting a wired-but-unflipped adapter is
   process discipline, not a probe property: the probe cannot see a working
   adapter whose row was never flipped, so the row flip is a mandatory part
   of the wiring recipe, not an optional cleanup.
4. Re-run `python3 scripts/hooks_probe.py --selftest` and `--all`; the row must
   reflect the wired tier, and the probe must still never PASS while unwired.

## Capability probe (steady state)

`python3 scripts/hooks_probe.py --all` reports one `plan-readiness` row per
agent, in the probe's `Agent | Hook | Status | Expected | Detail` columns.
Until an adapter is implemented for a host, every row is honest steady state
UNSUPPORTED: the limitation recorded, not hidden. Run
`python3 scripts/hooks_probe.py --all` for the live table; one illustrative
row:

| Agent | Hook | Status | Expected | Detail |
|-------|------|--------|----------|--------|
| Claude | plan-readiness | UNSUPPORTED | UNSUPPORTED | no adapter implemented (unwired by scope) |

Invariant: while a `plan-readiness` row reads UNSUPPORTED, no adapter for that
agent may exist on disk (an UNSUPPORTED row asserts "unwired by scope";
wiring an adapter without flipping the row breaks that assertion; see the
wiring recipe step 3).

The probe never PASSes for a `plan-readiness` cell while the capability is
unwired: an UNSUPPORTED expected tier
resolves before any adapter or config check, and no tier below UNSUPPORTED is
reported while the capability is unwired.

No adapter ships today; there is nothing to install. Enforcement lives in the
`execute-plan` and `done` skill gates until the wiring recipe above applies.
