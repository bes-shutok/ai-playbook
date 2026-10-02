# Make the docs-branch sync fail loud when its script is executed without the Documentation-paths fence

- **Filed:** 2026-10-03
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Origin class:** self-serving
- **Class:** fence-class
- **Driving force:** reliability

## Problem

The docs-branch skill splits Step 2's executable across two bash fences: the "Documentation paths" fence defines `SHADOW_CANDIDATES`, the `docs_branch_candidate_ignored` probe, and the extra-shadow-dirs parser, and the Step 2 sync fence consumes them. An agent that extracts and executes only the sync fence (the larger, self-titled one) gets a **silent no-op**: `SHADOW_CANDIDATES` is undefined, expands empty (no `set -u`), the candidate loop runs zero times, `SHADOW_PATHS` stays empty, and the script reaches its `SHADOW_PATHS empty -> exit 0` early return — exit code 0, no stderr, no worktree, no commit. Every downstream verification that trusts the sync's exit status reads "nothing to sync" while the shadow branch drifts.

This is not hypothetical: a consumer repository's done closeout ran the sync fence alone twice on 2026-10-03 (rc 0 both times), and inspection showed the repo's `docs` branch had gone a week without a real commit (last shadow sync Sept 26) while plans were archived, reviews landed, and backlog items completed. Re-running with both fences assembled into one invocation landed a 142-file catch-up commit and the tmp-sweep drops. The same silent shape likely explains interim sessions' syncs landing nothing.

## Expected

One plan that makes the partial-extraction no-op loud and the assembly dependency explicit:

1. Guard at sync-fence entry: when `SHADOW_CANDIDATES` is unset or empty at the top of the Step 2 script, print a named error (`docs-branch: SHADOW_CANDIDATES empty at entry; the Documentation-paths fence was not assembled with the sync fence; refusing to no-op silently`) and exit non-zero, instead of reaching the empty-paths early return. The existing legitimate empty case (no candidate exists on disk) must still exit 0, so the guard keys on the variable being UNSET or the candidates list never having been built, not merely on an empty result after disk checks.
2. A one-line note in the Step 2 prose stating the two fences must be concatenated into a single bash invocation, so an agent assembling the script from the SKILL.md source (rather than executing it in place) extracts both.
3. Optional hardening: a post-sync verification line echoing the docs branch tip before and after, so even a legitimate no-op commit-wise run states "branch tip unchanged" rather than silence.

## Evidence

- Failure witness: consumer-repo done closeout 2026-10-03; two rc-0 no-op sync invocations; `git log -1 refs/heads/docs` showed the Sept 26 tip while disk held a week of shadow changes; assembled-fence re-run landed the catch-up commit (`03f7c37` in that repo's docs branch, 142 files, +30936/−2230, including tmp-sweep drops).
- Structure: the sync fence's own comment says "Build SHADOW_CANDIDATES per Documentation paths section above (the assembled section also defines the shared candidate-ignored probe used below)" — the dependency is documented only as a build instruction inside the consuming fence, with no runtime check that it was honored.
