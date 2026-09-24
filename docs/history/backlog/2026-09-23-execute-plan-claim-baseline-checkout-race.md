# Execute-plan launch baseline can capture a peer checkout

## Problem

The runtime records a claim's Git `HEAD` as its launch baseline. In a shared
checkout, another session can change the checked-out branch between task
claim and launch, so the stored baseline may belong to a sibling branch. The
done gate then rejects a correctly scoped, reachable task commit even when
both histories share an ancestor.

## Desired outcome

Bind the launch receipt to a stable checkout/worktree identity and branch
revision captured atomically with the launch authorization. Detect branch or
HEAD movement between claim, launch, and done; reconcile a legitimate peer
checkout without attributing its commit to the current task. Keep the task's
immutable path allowlist and captured verification evidence as the authority
for the task commit.

## Current mitigation

The done boundary allows a non-descendant baseline only when Git proves a
shared merge base, while retaining reachable-commit, first-parent path,
symlink, and configured source-evidence checks. Unrelated histories and
out-of-scope commits remain refused.

## Acceptance evidence

- A race test switches branches between claim and launch and proves the
  receipt identifies the checkout revision actually used.
- A second worktree or session cannot rotate another claim's baseline.
- Replay, unrelated histories, out-of-scope commits, and missing checkout
  evidence fail closed.
- Concurrent execution uses independent worktrees or otherwise supplies a
  driver-validated checkout identity.
