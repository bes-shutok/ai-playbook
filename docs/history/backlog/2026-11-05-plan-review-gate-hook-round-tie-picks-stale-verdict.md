Status: open
Priority: high
Class: fix-class (false-positive block with a manual workaround; the gate over-refuses when two review rounds share a modification time)
Origin class: consumer-feedback (company)

# Plan-review gate hook picks the "newest" review round by modification time, so a same-second tie lets a superseded No-Go round block a commit

## Problem

The Claude Code PreToolUse hook `check-plan-review-gate.sh` blocks a `git commit` that stages a plan file when the "newest" matching review artifact records a No-Go verdict. It picks the newest artifact with bash `-nt` (modification time only). When two review rounds for the same plan slug carry the same modification time (the superseded round N-1 with a No-Go verdict and the latest round N with `ready=yes`, both written within one second), `-nt` is false in both directions, so the winner is whichever file `find` happened to list first. In the witnessed run the older No-Go round won the tie and the hook blocked a plan-checkbox commit even though the latest round said `ready=yes`. The workaround was to touch the latest round file (content unchanged) so its mtime moved ahead.

## Observed vs expected

Observed: the verdict of an older round decides the gate whenever mtimes tie, and the outcome depends on directory listing order, so it is not even stable between invocations.
Expected: the gate evaluates the highest `-r<N>` round number for the plan slug (numeric compare, so r10 outranks r9), falling back to mtime only when no round number parses. A tie in mtime must never change which round is judged.

## Evidence (trimmed)

- Verified in isolation: two files `x-r13.md` and `x-r14.md` given the same mtime via `touch -t`; `[ x-r14.md -nt x-r13.md ]` and `[ x-r13.md -nt x-r14.md ]` are both false.
- In the witnessed run, the superseded round and the ready round existed side by side under the repo's reviews directory with consecutive round numbers; the only change that unblocked the commit was touching the newer file.
- The hook's selection loop keeps the first candidate and replaces it only when a later candidate is strictly newer (`[ "$r" -nt "$newest" ] && newest="$r"`), which is what makes the tie resolve to listing order.

## Environment context

Runtime hook on the operator machine, 2026-11-05. The hook is an ordinary file at `~/.claude/hooks/check-plan-review-gate.sh`, not a symlink: unlike the sibling hooks `lessons-recall.sh` and `skill-gate.sh`, it has NO versioned source under the skills repo's `agents/hooks/` tree (the skill-gate README only references it as "the only wired precedent" and requires its settings entry be preserved). So the fix has no repo copy to patch today.

## Suspected root area

- Runtime file `~/.claude/hooks/check-plan-review-gate.sh`, the loop under the comment "keep the most-recently-modified" (newest-review selection).
- Missing deployment: no versioned source and no test for this hook in the skills repo; the fix should first version it under `agents/hooks/` (for example a `plan-review-gate/` directory with the script and a README, symlinked into `~/.claude/hooks/` like its siblings) so the change is reviewable and testable.
- Adjacent, not witnessed this run: the verdict check greps the whole selected file for `No-Go`, `ready=no`, or `Ready for execution: No`, so a ready round whose prose merely mentions a prior No-Go verdict could also block. Evaluate when the selection is fixed; do not widen the first fix without a witness.

## Ship when

The hook (versioned in the skills repo and symlinked into the runtime hooks directory) selects the review round by highest parsed round number for the slug, with a test pinning: equal mtimes with a No-Go older round and a ready newer round allows the commit; the reverse (older ready, newer No-Go) blocks; r10 outranks r9; an unparseable name falls back to mtime. The temporary workaround of touching a review file is no longer needed.

Dedup probe: searched open backlog filenames and bodies for `check-plan-review-gate`, `plan-review-gate`, `review gate hook`, `-nt`, and `mtime`; the only hits are unrelated items (a gate-removal residue item citing a review artifact name, and arrival-marker mtime items about a different script). No family match, so no fold.
