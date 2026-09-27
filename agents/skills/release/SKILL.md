---
name: release
description: >
  Squash the unpushed main pile into a few feature commits, write a plain-language CHANGELOG
  entry, and publish to origin after safety and privacy gates. Use when the user asks to
  "release", "cut a release", "publish unpushed commits", or wants "release notes" for the
  unpushed work.
---

# Release

Publishing is one deliberate act: cluster the unpushed `main` pile into a few feature
commits, write a plain-language `CHANGELOG.md` entry, and send the result to the remote
only after the safety and privacy gates pass. The mechanical carriers of the behavior are
`scripts/release-authoring.sh` (authoring mechanics) and `scripts/release-rewrite.sh`
(gated history rewrite). This file is their workflow contract: it tells the running agent
what to decide, what to run, and what to report.

## When to Run

Run this skill only when the user asks for it: "release", "cut a release", "publish
unpushed commits", or "release notes" for the unpushed work. A release is never a side
effect of another workflow.

One release run:

- Measures the publish delta: the commits in `<remote>/main..main` and the files they
  change (remote name from Configuration, default `origin`).
- Squashes that delta into a few feature commits, oldest group first, without reordering.
- Writes one dated `CHANGELOG.md` section and commits only that file (the notes commit).
- Creates a backup ref before any mutation, rewrites in an ad-hoc worktree outside the
  repository, proves the final tree byte-identical, scans every published blob and message
  for private data, and moves `main` with a compare-and-swap.
- Publishes only at the end, from a separate shell call, by executing the persisted push
  script: a plain fast-forward of the verified rewritten tip. Forced pushes are never used.

Uncommitted work in the checkout is never touched. Already-pushed history is never
rewritten. Every abort path stops before the publish step and releases the done lock.

Preconditions (the scripts also enforce them): HEAD is `refs/heads/main`; `CHANGELOG.md`
carries no uncommitted changes; the publish delta is linear (a merge commit inside it
aborts the run); local `main` is a descendant of `<remote>/main`.

## Core Concepts

- **Publish delta**: the commit range `<remote>/main..main` and the files it changes;
  everything a release sends to the remote for the first time.
- **Feature group**: a maximal run of consecutive commits in the publish delta that
  belong to one feature. Groups never reorder commits; interleaved features stay in
  separate groups.
- **Drafted section file**: the input to `release-authoring.sh`: the `CHANGELOG.md`
  section markdown, then a single `release-groups:` marker line, then alternating
  `group <count>` and `msg <subject>` lines, oldest group first.
- **Backup ref**: `refs/release-backup/pre-release-<date>` (suffix `-N` on a same-day
  collision) at the pre-rewrite tip. It is the only recovery path for the original
  boundaries; it lives outside the pushable branch namespace and is never published.
- **Rewrite worktree**: a temporary `git worktree` outside the repository tree where the
  rewrite happens; the primary checkout is never touched by rewrite commands.
- **Persisted push script**: the 0700 script `release-rewrite.sh` writes after a
  successful rewrite. It re-asserts the tip, the working-tree snapshot, and the remote
  position, then publishes the verified tip value as a plain fast-forward, and removes
  itself on every exit.

## Configuration (from facts document)

| Key | Purpose | Fallback |
|-----|---------|----------|
| `DONE_LOCK_SCRIPT` | Lock implementation for acquire, `status`, and `release-repo` | `${HOME}/.ai-playbook/scripts/done-lock.sh` |
| `DONE_LOCK_HOLDER_PID` | Holder identity recorded in the lock metadata. `release-authoring.sh` exports it (pinned to its invoking shell) right before the wait-acquire, so the hold outlives the short-lived authoring process and dead-holder recovery cannot reclaim the lock mid-run. An explicit caller pin to a longer-lived process wins | set automatically by `release-authoring.sh` (the invoking shell's PID) |
| `RELEASE_REMOTE` | Remote name; every `<remote>/main` range expression in either script resolves through it | `origin` |
| `RELEASE_HYGIENE_SCANNER` | Repo-relative privacy-scanner path, resolved against the primary checkout | `scripts/scan-public-hygiene.sh` |
| `PUBLIC_HYGIENE_PATTERNS_FILE` | Deny-pattern override handed to the privacy gate; when set, the effective value is printed to the run output and carried into the summary | unset (scanner default) |
| `RELEASE_LOCK_MAX_WAIT` | Seconds the short agent wait may poll for the done lock | `60` |

## CHANGELOG authoring rules

These rules are judgment work the running agent performs; no script writes the prose.

- Cluster the publish delta into features first: read the pile with
  `git log --reverse --format='%h %an %s' <remote>/main..main`, and use commit bodies and
  touched paths (`git show --stat <sha>`) to decide what belongs together.
- Write ONE section headed `## <today>` (verify today's date from the system environment;
  format `YYYY-MM-DD`). Under the heading write one sentence on what the release improves
  overall, then one `### <area>` subheading per reader-visible area (for example:
  planning and reviews, scripts, docs), and one bullet per improvement.
- Every bullet says what changed for the reader, never how it was implemented. Name the
  visible effect, not the mechanism.
- Write in the plain-language house style: short sentences, common words, active voice,
  no unexplained jargon.
- No em dash anywhere in the section: the authoring gate aborts the run before
  `CHANGELOG.md` is touched.
- If a `## <today>` section already exists, placement is automatic: the authoring step
  replaces it in place when an unpushed notes commit of this release lineage introduced
  it, and prepends a new section when the existing one is already published, so a
  same-day second release keeps its own notes.
- The group subjects in the draft become the published commit messages: short,
  imperative, feature-level subjects in the repository's `<area>: <summary>` style.
- Example section shape:

```markdown
## 2026-09-26

This release makes the assistant's maintenance loop cheaper to run and easier to trust.

### Planning and reviews
- Plans now carry a short outcome summary at the top, so a reader can see the aim
  without reading the whole plan.
```

## Step 1: Draft the section file and the feature groups

1. Fetch first: `git fetch <remote>` (remote name from Configuration), so the
   remote-tracking ref is fresh; a stale one would misreport the delta.
2. Measure the delta: `git rev-list --count "refs/remotes/<remote>/main..main"`. Call the
   value N.
3. Cluster the delta into feature groups (see the authoring rules above) and give each
   group its commit count.
4. Size the counts so they tile the whole range. When this run creates a notes commit
   (the usual case), the counts must sum to N + 1: the extra one is the notes commit, and
   it folds into the LAST group. The only case where the counts sum to N alone is a
   re-run whose drafted section is byte-identical to the section already at HEAD: the
   authoring step then skips the notes commit, and the previous notes commit, newest in
   the measured pile, folds into the last group.
5. Reserve a scratch path outside the repository tree, so the draft never shows up in
   `git status`:

```bash
mktemp "${TMPDIR:-/tmp}/release-draft.XXXXXXXX"
```

6. Write the draft to that path with the file-writing capability, in exactly this shape:

```markdown
<section markdown per the CHANGELOG authoring rules>

release-groups:
group <count>
msg <subject>
group <count>
msg <subject>
```

Oldest group first; the `group` and `msg` lines must alternate one for one.

## Step 2: Author the notes commit and rewrite history (one shell call)

Run `release-authoring.sh` and `release-rewrite.sh` in ONE shell invocation: shell state
does not survive between shell calls, and the lock exports and the groups-file path must
stay in this shell.

The authoring script acquires the per-worktree done lock (label `release-<date>`),
re-checks the preconditions, applies the drafted section to `CHANGELOG.md` (commit
message `changelog: release notes for <today>`), writes the groups file, and prints the
lock export lines plus a final `groups-file <path>` data line on stdout. The one-line
`groups-file` helper turns that data line into an assignment, so the whole stdout evals
as shell. The rewrite script re-asserts the lock and the branch, creates the backup ref,
rewrites in the ad-hoc worktree, runs the privacy gate over every published blob and
message, moves `main` with a compare-and-swap, and prints the persisted push script path
on stdout.

```bash
unset DONE_LOCK_DIR DONE_LOCK_TOKEN RELEASE_GROUPS_FILE PUSH_SCRIPT
groups-file() { RELEASE_GROUPS_FILE="$1"; }
eval "$(bash scripts/release-authoring.sh "<draft-path-from-step-1>")" || true
if [ -z "${RELEASE_GROUPS_FILE:-}" ]; then
  # The authoring step aborted; its FATAL line above says why. Remove the
  # Step 1 draft, release the lock when the acquire had already succeeded,
  # then stop.
  rm -f -- "<draft-path-from-step-1>"
  if [ -n "${DONE_LOCK_DIR:-}" ] && [ -n "${DONE_LOCK_TOKEN:-}" ]; then
    DONE_LOCK_DIR="$DONE_LOCK_DIR" DONE_LOCK_TOKEN="$DONE_LOCK_TOKEN" \
      "${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}" release-repo || true
  fi
  exit 1
fi
# Re-print the lock exports to the chat context exactly as done Step 0 item 2
# does: the final shell call runs with a fresh environment and re-exports both
# values from this output for the release step.
printf 'export DONE_LOCK_DIR=%q\n' "$DONE_LOCK_DIR"
printf 'export DONE_LOCK_TOKEN=%q\n' "$DONE_LOCK_TOKEN"
rm -f -- "<draft-path-from-step-1>"
PUSH_SCRIPT=""
rewrite_rc=0
PUSH_SCRIPT="$(bash scripts/release-rewrite.sh "$RELEASE_GROUPS_FILE")" || rewrite_rc=$?
if [ "$rewrite_rc" -ne 0 ]; then
  DONE_LOCK_DIR="${DONE_LOCK_DIR:?}" DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN:?}" \
    "${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}" release-repo || true
  echo "release: rewrite aborted (exit $rewrite_rc); the lock is released; fix the reported cause and re-run from Step 1" >&2
  exit "$rewrite_rc"
fi
printf 'push script: %s\n' "$PUSH_SCRIPT"
```

Notes on this call:

- Run it with bash, not zsh. Do not install an exit trap: on success the lock must stay
  held across the call boundary, and the final shell call releases it. If the session
  itself dies while the lock is held, recover through the lock script's `status` and
  `stale-clean` rules, as the done skill's Step 0 describes.
- On every abort path the call releases the lock before exiting, so a waiting run can
  proceed. On a pre-acquire abort no exports exist and nothing is released.
- Rewrite-step exit codes: exit 2 is always `REGROUP REQUIRED` (the groups no longer
  tile the current range, usually because a concurrent commit landed on `main`): re-run
  from Step 1 and redraft from the new tip; a backup ref created before the abort stays
  in place. Exit 3 is a privacy-gate environment failure (the scanner itself exited 2):
  no scan verdict exists, so fix the scanner setup and re-run from Step 1. Exit 1 covers
  a privacy hit (the `PRIVACY GATE FAILED` sentinel naming the offending paths) or any
  other abort.
- The rewrite step also prints a report-only inventory of leftover scratch artifacts
  (stale push scripts, authoring run dirs, materialization roots, temp branches,
  rewrite worktrees). It never
  cleans them. Offer cleanup to the user, gated on their confirmation that no other
  release run is active, and never treat anything under `refs/release-backup/` as a
  cleanup candidate.
- Keep the printed backup ref line and the privacy-gate output (the excluded-path skip
  notes, and the patterns-override line when `PUBLIC_HYGIENE_PATTERNS_FILE` is set) for
  the final summary.

## Step 3: Publish, release the lock, and report (a separate shell call)

Run this in a NEW shell call, substituting the six values this run captured: the two
lock exports and the push-script path from Step 2's output, plus the backup ref, the
rewritten tip, and the remote name from the rewrite step's output lines. Change nothing
in the working tree between the two calls: the push script re-asserts a snapshot of the
post-swap state and aborts on any drift.

```bash
export DONE_LOCK_DIR="<paste from step 2 output: authoring export line>"
export DONE_LOCK_TOKEN="<paste from step 2 output: authoring export line>"
PUSH_SCRIPT="<paste from step 2 output: rewrite stdout>"
BACKUP_REF="<paste from step 2 output: rewrite backup-ref line>"
EXPECTED_TIP="<paste from step 2 output: rewritten tip from the swap-complete line>"
RELEASE_REMOTE="<paste from step 2 output: the remote this run used>"
REMOTE="${RELEASE_REMOTE:-origin}"
LOCK_SCRIPT="${DONE_LOCK_SCRIPT:-${HOME}/.ai-playbook/scripts/done-lock.sh}"
push_rc=0
push_ran=1
if [ -f "$PUSH_SCRIPT" ]; then
  bash "$PUSH_SCRIPT" || push_rc=$?
else
  push_ran=0
fi
if [ "$push_ran" -eq 0 ]; then
  # The push script removes itself after ANY run, so its absence alone proves
  # nothing. Verify both tips against the recorded one before claiming the
  # publish step already ran.
  recorded="$(git rev-parse --short "$EXPECTED_TIP" 2>/dev/null || printf '%s' "$EXPECTED_TIP")"
  published="$(git rev-parse --short main 2>/dev/null || echo missing)"
  remote_tip="$(git rev-parse --short "refs/remotes/$REMOTE/main" 2>/dev/null || echo missing)"
  if [ "$published" = "$recorded" ] && [ "$remote_tip" = "$recorded" ]; then
    echo "release: push script already gone; main and $REMOTE/main both sit at the recorded tip $recorded: the publish step already ran" >&2
  else
    echo "release: UNVERIFIED: the push script is gone but main ($published) and $REMOTE/main ($remote_tip) do not both equal the recorded tip $recorded; the publish state cannot be confirmed. Recovery: reset main to the backup ref $BACKUP_REF, reconcile with the remote, then re-run the release from Step 1." >&2
  fi
fi
lock_rc=0
DONE_LOCK_DIR="${DONE_LOCK_DIR:?}" DONE_LOCK_TOKEN="${DONE_LOCK_TOKEN:?}" "$LOCK_SCRIPT" release-repo || lock_rc=$?
if [ "$lock_rc" -ne 0 ]; then
  echo "release: lock release failed; run '$LOCK_SCRIPT' status and report the holder state (status free means the hold is already gone)" >&2
fi
"$LOCK_SCRIPT" status
# Report-only: sibling branches sharing pre-release-only history. Publishing any
# of them would send commits this run's privacy gate never scanned.
while read -r ref sha; do
  if ! git merge-base --is-ancestor "$(git merge-base "$sha" "$BACKUP_REF")" "refs/remotes/$REMOTE/main"; then
    echo "sibling branch pointing into the rewritten range (or forked from it): $ref"
  fi
done < <(git for-each-ref --format='%(refname) %(objectname)' refs/heads/)
if [ "$push_rc" -ne 0 ]; then exit "$push_rc"; fi
exit "$lock_rc"
```

The lock release runs on every exit path of this call, exactly as the done skill's Step 6
releases with `release-repo` from the re-exported `DONE_LOCK_DIR` and `DONE_LOCK_TOKEN`.

If the push script aborts, nothing was published: its ABORT lines name the backup ref and
the restore path (reset `main` to the backup ref, reconcile with the advanced remote,
re-run the release). Report that state; the block above still released the lock.

Then report the summary to the user, in this order:

1. The feature commits now on `main`:
   `git log --oneline --reverse "<backup-ref>..main"` (the backup ref marks the
   pre-rewrite tip, so this range is exactly the squashed feature commits; the
   remote-tracking range is already empty after the push).
2. The privacy-gate outcome: every published blob and message scanned and passed; carry
   the gate's excluded-path skip notes, and the patterns-override line when one was
   printed.
3. The backup ref name, stated as local-only and never published.
4. The lock: released, and `status` shows free.
5. The sibling-branch warning: publishing any branch the loop named would publish
   commits this run's gate never scanned; when none were named, say so.
6. A statement that the materialized copies were destroyed: the rewrite worktree, the
   temp branch, the materialization root, and the run temp dir were torn down on every
   path, and the push script removed itself after running.

## Integration Points

### With `done` skill
The per-worktree done lock serializes a release run exactly as it serializes a done run: the authoring step acquires it (label `release-<date>`) and the final shell call releases it on every exit path, as done Steps 0 and 6 do. Commit ownership is one sentence: done (with learn's, docs-branch's, and release's own notes commit excepted) owns all other commit flows. A release run commits only its own CHANGELOG notes commit and performs its own publish; it never runs the done workflow, and a done run stays out of the checkout for the duration of the release.

## Rules

- The publish is a plain fast-forward of the verified rewritten tip; forced pushes are
  never used, and the persisted push script names the recorded tip value rather than the
  bare branch name.
- One release at a time per checkout: the done lock serializes runs. Never release a
  lock this run did not acquire.
- Every exit path releases the done lock: the authoring-and-rewrite call releases on its
  abort paths; the final call releases on every path.
- `refs/release-backup/*` refs are the only recovery path for the original boundaries.
  Never delete, move, or publish them in this workflow; they accumulate one per release
  and stay local-only.
- Never hand-edit `main` to fix a failed release; fix the reported cause and re-run from
  Step 1.
- Nothing between the two shell calls may touch the working tree or `main`.
- The release never rewrites already-pushed history and never touches uncommitted work.
