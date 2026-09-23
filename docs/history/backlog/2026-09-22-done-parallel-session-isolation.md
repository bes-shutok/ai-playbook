# Backlog: done must isolate its session state from parallel work

Status: open
Priority: high

## Driving force

The `done` workflow was blocked while finalizing a clean plan branch because another session advanced `main`, committed related documentation, and produced review artifacts in the same checkout. The current gates treated those changes as belonging to the active `done` run.

## Observed behavior

1. `done_sweep_gates` retained an old `docs/tmp/done-session/session-start-head.txt` after a prior gate failure. The next run used that stale commit as the document-registry baseline and rechecked unrelated completed-history writes.
2. The review-staging gate selected ignored review files by repository path and modification time within the shared session window. It could not distinguish a review produced by a parallel session from one produced by the current session.
3. A rebase onto a newer `main` removed the unrelated committed changes from the branch diff, but did not remove the parallel review file from the mtime-based candidate set.
4. Repeated `done` runs therefore surfaced different unrelated blockers without a durable ownership or baseline handoff protocol.

## Expected behavior

Each `done` run should validate only the files and commits owned by that run, while still preserving concurrent work. A peer commit, ignored review record, or branch rebase must not become an active run's gate failure unless the run explicitly adopted that artifact.

## Root cause

Session identity is inferred from shared filesystem state and a mutable baseline rather than from an ownership-scoped run record. The run marker records only a repository root, and the ignored-file filter relies on mtime. The document-registry baseline is advanced only after a successful gate pass, so a failed run leaves a stale baseline that expands the next run's committed-change set.

## Desired fix shape

Design and implement an explicit session-isolation protocol for `done` and its sweep gates:

- Create a unique run identifier and ownership manifest at Step 0.
- Record the starting commit, starting index/worktree state, and the run-owned plan/review paths in that manifest.
- Make every gate consume the manifest instead of inferring ownership from global mtimes or a stale shared baseline.
- Advance or checkpoint the registry baseline in a failure-safe way that cannot expand the next run's scope, while retaining enough evidence to retry the failed run.
- Treat peer commits and peer ignored files as foreign, preserve them, and report them as excluded rather than as failures.
- Serialize only the operations that require serialization, such as docs-branch sync and commits, while allowing independent sessions to author work in separate worktrees.
- Add explicit recovery for a session that is interrupted after creating its marker but before finalizing its manifest.

## Acceptance criteria

- Two concurrent `done` runs with disjoint plan and review artifacts can both complete without either run validating the other's ignored files.
- A failed pre-docs gate can be retried without rechecking unrelated commits from before the retry's ownership boundary.
- A rebase or fast-forward of `main` during a run does not turn peer commits into registry failures.
- A peer review file with invalid staging metadata is preserved and reported as foreign, while the active run's valid review remains eligible for validation.
- The protocol remains fail-closed for artifacts explicitly claimed by the active run.
- Tests cover concurrent markers, stale baselines, peer commits, peer ignored files, rebases, interrupted runs, and retry behavior.
- The workflow documents which operations require the per-repository done lock and which may proceed concurrently.

## Reproduction evidence

1. Start a `done` run and create its run marker.
2. In another session, advance `main`, add a review record, and update completed-history documentation.
3. Let the first run fail before the document-registry gate can re-anchor its baseline.
4. Retry `done` from the first session.
5. Observe that the registry gate reports the peer's completed-history writes and the review-staging gate validates the peer's review file.

## Non-goals

- Do not rewrite or delete a peer's review record merely to make the active `done` run green.
- Do not weaken immutable-history or review-staging validation for artifacts owned by the active run.
- Do not require all agents to share one global branch or one long-lived lock for authoring work.
