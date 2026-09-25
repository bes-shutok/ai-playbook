# Plan: done plan-deliverables log: single append home + trustworthy session window

Backlog origin:
- `docs/history/backlog/2026-09-04-done-plan-deliverable-append-dedupe.md`
- `docs/history/backlog/2026-09-04-done-4c-mutation-append-wording.md`
- `docs/history/backlog/2026-09-04-done-deliverables-removal-undergate.md`

## Terms

- `{plans_dir}`, `{plans_completed_dir}`, `{tmp_dir}`, `{reviews_dir}`: resolved from the TOML block in `.ai-playbook/facts.md` (using-skills Step 0). In this repo: `docs/plans/`, `docs/plans/completed/`, `docs/tmp/`, `docs/reviews/`.
- **Deliverables log**: `{tmp_dir}/done-session/plan-deliverables.txt`; one repo-relative plan path per line; blank lines and `#` comments ignored.
- **Ignored arm**: `git status --porcelain --ignored=matching -- <plans_dir>`; a path listed there with the ignored marker is an `!!` plan.
- **Session window**: the interval from the anchor to gate time; it decides which `!!` plans count as this session's deliverables.
- **Run-start marker**: an empty file `{tmp_dir}/done-session/run-start-<UTCtimestamp>` that every `done` run writes at Step 0; the newest one anchors the session window.
- **Readiness gate**: done Step 1.5 plan-readiness verification via `scripts/plan_readiness.py` (repo-local copy; deployed runtime copy is a symlink to it).
- **Producer**: a workflow action that appends plan paths to the deliverables log.
- **Skill-gate marker**: `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`; refreshed by the plans skill before EVERY plan-file write per `agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (ensure the runtime dir exists, atomic write mode 0600, benign `FileExistsError`, fail-loud on unwritable).
- **Session key**: output of `python3 ~/.ai-playbook/scripts/session_channel.py` (no trailing newline); empty after strip means the literal `no-session`; otherwise `sha1(value)[:16]` hex. The project key derives via `facts_paths.resolve_project_key`; do not re-implement either derivation. These two entries exist for the plans-skill marker recipe during plan authoring (the marker is refreshed before every plan-file write); no execution task below writes markers.

## Assumptions

- assume one plan covers all three backlog items; basis: all three target `agents/skills/done/SKILL.md` Step 1.5 / Step 3, and the wording item itself says it is likely subsumed by the dedupe fix.
- assume a doc-only change validated by grep probes and `bash -n`; basis: skills are markdown instruction sets with no test pipeline; this plan changes no script behavior.
- assume no redeploy task is needed; basis: the runtime registry is unified symlinks into this repo (2026-09-04), so `~/.agents/skills` and `~/.ai-playbook/scripts` reflect repo bytes immediately.
- assume no Step 3 renumbering after the 4c deletion; basis: a repo-wide grep shows item 4c is referenced only inside `agents/skills/done/SKILL.md` (Step 1.5 paragraph and the item itself), so deleting it leaves no dangling external references and 4b/5 keep their labels.

## Gist & Examples

**What changes (plain language).** The done skill keeps four promises about plan deliverables, and this plan fixes three cracks in them:

1. **One commit-time append home.** Step 3 item 0b (append staged `{plans_dir}` paths before any `git commit`) and item 4c (append committed plan paths after the done commit) both write the same log. 0b already runs before every commit, including the done commit itself, so 4c is fully redundant: a plan committed only inside this done still lands in the log before that commit, which is exactly the "feeds a later done in the same chat" guarantee 4c existed for. The plan deletes 4c, keeps 0b as the single commit-time home, and shrinks Step 1.5's producer list from three to two. The stale "Write append" wording inside 4c (the plans skill's producer was widened to Write/Edit/StrReplace) dies with the item.
2. **A trustworthy session-window anchor.** Step 1.5 anchors the session window on "the creation time of the log/session files" under `{tmp_dir}/done-session/`, falling back to "the earliest `plan-deliverables.txt` entry timestamp". Both halves are broken: producers write paths only, never timestamps, and the log is itself a done-session artifact, so its absence implies no entries either way (the fallback is dead); and the log intentionally persists across done runs, so its creation time can predate the current chat, widening the window and producing spurious refusals. The plan has every done run write a fresh per-run marker at Step 0 and anchors the window on the newest marker written by a previous done run (the current run's own marker never anchors its own window, so mutations from earlier in the chat stay inside the window); the dead fallback clause is deleted and replaced with conservative gating (an unanchorable window treats every `!!` plan as this session's deliverable, so the gate names its targets instead of silently skipping them).
3. **A unified ignored-arm rule.** Today a `!!` plan counts only when listed in the log, and an unlisted `!!` plan is blanket-exempted whenever the log exists. That is the r8 under-gate: a plan mutated by a non-plans skill under a gitignored `{plans_dir}` (so the normal porcelain arm is inert), whose producer append was skipped, and which drifted after a prior manifest exemption, is silently never gated. The plan classifies a `!!` plan as a session deliverable when it is listed in the log OR its mtime falls inside the session window; unanchorable windows gate conservatively; only unlisted, out-of-window plans (stale, belonging to their authoring session) get no gate.

**Examples.**

- Shadow repo (gitignored `{plans_dir}`), plan mutated by a non-plans skill at 14:00, done run at 17:00, log exists from a prior chat. Before: the plan is unlisted, so "an unlisted `!!` plan is not this session's deliverable" applies and nothing gates it. After: the widened producer obligation makes any plan-file mutator append the path, so it is listed and gated; if that obligation was skipped, the 14:00 mtime still falls inside the window anchored at the last done run's marker, so the gate catches it; if no previous-run marker exists at all (first done after this change), the window is unanchorable and conservative gating names the plan. The only silent path left requires an unlisted plan whose mtime predates the last done run, which is the intended "stale plan belongs to its authoring session" case.
- Same shadow repo, prior-chat plan untouched this chat. Before: the window anchored on the log's prior-chat creation time includes the whole prior chat, so a prior-chat mtime trips the gate (spurious refusal, fail-closed noise). After: the anchor is the newest marker written by a previous done run, so mtimes from before that done fall outside and the stale plan is correctly left alone; only drift from after the last done run stays inside the window, which is exactly the un-gated territory the gate exists for.
- A plan committed inside the done commit, then a second done in the same chat. Before and after: 0b appended it before the commit; the first done gates it and the removal rule drops it from the log; the second done sees it committed and clean, so it is not a candidate. No behavior change; 4c's removal costs nothing.

**Edge cases that shaped the design.** Multiple done runs in one chat: each writes its own marker, and each run's window anchors on the previous run's marker, so drift between two dones in the same chat stays inside the later run's window. Old run-start markers accumulate as empty files; pruning must keep the newest marker written by a previous done run (it is the next run's anchor) and the current run's marker; everything older may go. `{plans_completed_dir}` stays excluded even when nested under `{plans_dir}`, and committed plans this session never touched still get no gate and no refusal (they belong to their authoring session).

## Evaluation Criteria

**Quality dimensions:**

- correctness: every acceptance criterion from the three backlog items maps to a dedicated probe in Validation Commands; each forbidden sweep fired against the pre-fix tree and each new-wording probe was absent at authoring time (recorded below in Validation Commands).
- consistency: Step 0, Step 1.5, and Step 3 agree on one append home (0b), one anchor (newest run-start marker), one `!!` classification; zero residual references to item 4c, "Write append", the dead fallback, or the creation-time anchor.
- fail-closed direction: the unanchorable case gates and names its targets rather than silently skipping; the fail-closed posture of the readiness gate is preserved.
- minimality: no Step 3 renumbering, no new skills, no script changes; the diff touches one file.

**Done when:**

- The full Validation Commands block exits 0 from the repo root on the modified tree.
- A fresh review-plan round on the final bytes reports `ready=yes` with zero unresolved blocking findings and a matching sidecar digest.

**Ship when:**

- No external condition. The deployed runtime (`~/.agents/skills`, `~/.ai-playbook/scripts`) already symlinks into this repo, so the new wording is live the moment the repo bytes land; there is no separate deploy step to schedule.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/done/SKILL.md` (Step 0 run-start marker insertion; Step 1.5 anchor sentence, `!!` classification, and producer list; Step 3 item 4c deletion)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/plans/SKILL.md`; already widened to "(Write, Edit, or StrReplace)" and no task edits it; a regression guard probe pins its vocabulary.
- `scripts/plan_readiness.py`; the validator's behavior is unchanged by this plan.
- `README.md`, `projects/.ai-playbook/agent-runtime-layout.md`; no skill catalog, path, or usage changes.
- `docs/history/backlog/2026-09-04-*.md`; the three items are the scope of record and stay in place until plan completion moves them.

## Design Invariants (CR Guard)

- **Fail-closed direction preserved.** The 2026-09-03 readiness-gate design gates unanchorable plans conservatively rather than skipping them; no task may reintroduce a silent no-gate path. (Source: r8 finding AB3 acceptance criteria in the undergate backlog item.)
- **Session-scoped gate doctrine preserved for anchorable windows.** Committed stale plans this session never touched and never listed get no gate and no refusal when the session window is anchorable; they belong to their authoring session. The unanchorable conservative branch is the deliberate fail-closed exception: on a first run with no previous-run marker (or a lost marker store), every `!!` plan gates. `{plans_completed_dir}` stays excluded even when nested under `{plans_dir}`. (Source: done Step 1.5; the exception is new in this plan per the undergate backlog item.)
- **execute-plan manifest exemption preserved.** The active-manifest exclusion with the `updated:` freshness check is untouched; the checkbox-drift and resume rules keep their current wording. (Source: done Step 1.5, r5-r9 readiness-gate review rounds.)
- **Single commit-time append home.** After this plan, exactly one Step 3 item (0b) appends at commit time, and it runs before any `git commit`, done or not. Do not reintroduce a second commit-time append. (Source: dedupe backlog item.)
- **No renumbering.** Step 3 item labels (0b, 4b, 5) stay stable after the 4c deletion; item 5's "(including 4b when it applies)" reference stays valid.

## Validation Commands

Run from the repo root. Sweeps target `agents/skills/done/SKILL.md` ONLY; this plan file's own mentions of the patterns below are checker literals, not stale references, and are never swept. Every check aborts non-zero on miss or forbidden match; the swept file is pre-checked for existence so a missing-file error cannot read as a pass.

At authoring time (pre-fix tree) every forbidden sweep was executed and FIRED (hit counts: `4c.` 1, `item 4c` 2, `backup producer` 1, `Write append` 1, `entry timestamp` 1, `creation time of the log/session files` 1, `it scopes the ignored arm` 1, `fall back to judging each` 1), and every new-wording probe was ABSENT (0 hits), flipping GREEN exactly when its task lands; the two regression guards were GREEN (1 hit each).

```bash
#!/usr/bin/env bash
set -u
F="agents/skills/done/SKILL.md"
P="agents/skills/plans/SKILL.md"
fail() { echo "VALIDATION FAIL: $1" >&2; exit 1; }
test -f "$F" || fail "done SKILL.md missing"
test -f "$P" || fail "plans SKILL.md missing"
FLAT="$(tr '\n' ' ' < "$F")"

# Forbidden: item 4c fully removed (dedupe; the stale Write-append wording dies with it)
if grep -iqF "4c." "$F"; then fail "Step 3 item 4c still present"; fi
if grep -iqF "item 4c" "$F"; then fail "residual item-4c reference (case-insensitive)"; fi
case "$FLAT" in *"backup producer"*) fail "backup-producer framing still present";; esac
case "$FLAT" in *"Write append"*) fail "stale Write-append wording still present";; esac

# Forbidden: dead fallback clause removed (r9: it can never fire)
case "$FLAT" in *"entry timestamp"*) fail "dead log-entry-timestamp fallback still present";; esac

# Forbidden: stale creation-time anchor removed (r9: it can predate the current chat)
case "$FLAT" in *"creation time of the log/session files"*) fail "stale creation-time anchor still present";; esac

# Forbidden: old log-scoped ignored-arm classification removed (r8 under-gate)
case "$FLAT" in *"it scopes the ignored arm"*) fail "old log-scoped ignored-arm rule still present";; esac
case "$FLAT" in *"fall back to judging each"*) fail "old log-absent fallback wording still present";; esac

# Positive: Step 0 writes the per-run start marker (anchor witness)
grep -Fq "run-start-" "$F" || fail "run-start marker not prescribed anywhere"
grep -Fq "immediately after the lock is acquired, write an empty per-run marker file" "$F" || fail "Step 0 run-start marker obligation missing"

# Positive: unified ignored-arm classification + conservative unanchorable path
grep -Fq "or its modification time falls inside the session window" "$F" || fail "unified in-window ignored-arm rule missing"
grep -Fq "apply conservative gating and treat every" "$F" || fail "conservative unanchorable rule missing"

# Positive: anchor is the newest run-start marker from a PREVIOUS done run
grep -Fq "anchor is the newest" "$F" || fail "previous-run anchor wording missing"
grep -Fq "written by a previous done run" "$F" || fail "previous-run anchor witness missing"
grep -Fq "does not anchor its own window" "$F" || fail "self-anchor guard missing"

# Positive: producer (1) widened to any plan-file mutator
grep -Fq "any other skill or tool that mutates a plan file" "$F" || fail "widened producer obligation missing"

# Regression guards: producer (2) still anchors on item 0b; plans skill vocabulary intact
grep -Fq "binding agent commit hygiene; see Step 3 item 0b" "$F" || fail "producer (2) lost its item 0b anchor"
grep -Fq "Write, Edit, or StrReplace" "$P" || fail "plans skill mutation vocabulary regressed"

echo "VALIDATION OK"
```

### Task 1: done Step 0 writes the per-run start marker

*Post-archive annotation (2026-09-06): the Step 0 snippet evolved during Phase 3 review rounds (r1: REPO_TOP resolution, the $REPO_TOP-anchored fallback, the MARKER variable, the printf echo; r2: head -n 1 and the case "$TMP_DIR" relative-path anchor; 2026-09-06 wording-trio plan: the content-bearing marker line). The verbatim/four-lines claim in the checklist text reflects authoring time, not the final snippet. Post-archive annotation addendum (2026-09-07, wording-trio review r1 F2): the `write an empty per-run marker file` probe in the frozen Validation Commands block below reflects the pre-2026-09-06 wording and no longer passes against the current tree (the wording-trio plan reworded `empty` to `content-bearing`); a failed re-run of that frozen block at this probe is expected stale-wording, not tree drift.*

Files:
- `agents/skills/done/SKILL.md`

Insert immediately after the paragraph ending "Do not run learn, docs-branch, or project commits before Step 0 succeeds." a new paragraph with exactly this obligation sentence and snippet:

> **Run-start marker:** immediately after the lock is acquired, write an empty per-run marker file under `{tmp_dir}/done-session/` named `run-start-<UTCtimestamp>` (filename format `run-start-YYYYmmddTHHMMSSZ`, UTC; create the directory if missing). Step 1.5 anchors this run's session window on the newest marker written by a previous done run (the current run's marker does not anchor its own window). Markers older than that anchor may be pruned; never delete the newest marker written by a previous done run, and never delete the current run's marker.

```bash
TMP_DIR="$(sed -n 's/^tmp_dir = "\(.*\)"$/\1/p' .ai-playbook/facts.md 2>/dev/null)"
TMP_DIR="${TMP_DIR:-docs/tmp/}"
mkdir -p "${TMP_DIR%/}/done-session"
: > "${TMP_DIR%/}/done-session/run-start-$(date -u +%Y%m%dT%H%M%SZ)"
```

- [x] The obligation sentence and snippet are inserted verbatim in Step 0 (after the lock-acquire paragraph, before "## Step 1")
- [x] Interim probe (scoped to this task, rule 16): `grep -Fq "immediately after the lock is acquired, write an empty per-run marker file" agents/skills/done/SKILL.md` and `grep -Fq "run-start-" agents/skills/done/SKILL.md` both succeed
- [x] `bash -n` over the inserted snippet passes (extract the four lines into a temp file and syntax-check them)
- [x] Commit: `skills: done Step 0 writes per-run start marker (session-window anchor witness)`

### Task 2: Step 1.5 anchor, unified ignored-arm rule, two-producer list

Files:
- `agents/skills/done/SKILL.md`

Three edits inside the Step 1.5 gate paragraph:

Edit (a): replace the text from "; but a plan it lists with the ignored marker" through "entry timestamp when no such artifact exists." with exactly:

> ; a plan the ignored arm lists with the ignored marker (`!!`) counts as a session-deliverable candidate when that same path is listed in `{tmp_dir}/done-session/plan-deliverables.txt` or its modification time falls inside the session window (an unlisted `!!` plan with a modification time outside the window belongs to its authoring session and gets no gate). The session window's anchor is the newest `run-start-` marker written by a previous done run under `{tmp_dir}/done-session/` (every done run writes its own marker at Step 0; the current run's own marker does not anchor its own window; the window runs from the anchor marker's timestamp to gate time; markers older than the anchor may be pruned, but never the anchor itself). When no marker from a previous run exists at all, the window is unanchorable: apply conservative gating and treat every `!!` plan as this session's deliverable (the gate names each gated plan; it never silently skips them).

Edit (b): replace the producers list from "**Producers (must run before this gate):**" through "commits that already happened earlier in the session." with exactly:

> **Producers (must run before this gate):** (1) any plan-file mutation under `{plans_dir}` (excluding `{plans_completed_dir}`) appends the path to `{tmp_dir}/done-session/plan-deliverables.txt` (the `plans` skill does this on every Write, Edit, or StrReplace; any other skill or tool that mutates a plan file under `{plans_dir}` does the same, so the log stays complete even for edits made outside the `plans` skill); (2) any `git commit` that stages `{plans_dir}` paths appends those paths in the same turn before `git commit` returns (binding agent commit hygiene; see Step 3 item 0b).

- [x] Both edits applied verbatim; the sentence beginning "Do not treat Step 3 item 4c" no longer exists
- [x] Forbidden interim probes (scoped to this task; each `grep -c` prints a count and must print 0; grep's own exit status is 1 when the count is 0, so judge the printed count, never the exit code; abort the task on any nonzero count): `grep -cF "entry timestamp"`, `grep -cF "creation time of the log/session files"`, `grep -cF "it scopes the ignored arm"`, `grep -cF "fall back to judging each"`, `grep -icF "Step 3 item 4c"` (scoped to the Step 1.5 references this task removes; the 4c item text itself dies in Task 3)
- [x] Positive interim probes (scoped to this task; each must print at least 1, judge the printed count and abort the task if any prints 0): `grep -cF "or its modification time falls inside the session window"`, `grep -cF "apply conservative gating and treat every"`, `grep -cF "anchor is the newest"`, `grep -cF "written by a previous done run"`, `grep -cF "does not anchor its own window"`, `grep -cF "any other skill or tool that mutates a plan file"`, `grep -cF "binding agent commit hygiene; see Step 3 item 0b"`
- [x] Commit: `skills: done Step 1.5 unified ignored-arm rule, run-start anchor, two-producer list`

### Task 3: delete Step 3 item 4c

Files:
- `agents/skills/done/SKILL.md`

Delete the entire item 4c line ("4c. **Session plan-deliverable log (backup producer):** ..."). Do not renumber: 4b and 5 keep their labels, and item 5's "(including 4b when it applies)" stays valid.

- [x] The item 4c line is gone; items 0b, 4b, and 5 are otherwise untouched
- [x] Interim probes (scoped to this task): forbidden `grep -cF "4c."`, `grep -cF "backup producer"`, and `grep -cF "Write append"` all return 0 on `agents/skills/done/SKILL.md`, aborting non-zero on any hit
- [x] Commit: `skills: done drops Step 3 item 4c; item 0b is the single commit-time deliverable append`

### Task 4: full validation sweep

Files:
- none (verification only)

- [x] Run the full Validation Commands block from the repo root → expect exit 0 with `VALIDATION OK`
- [x] `bash -n` over the Validation Commands block → expect exit 0
- [x] Mechanical pin audit (rule 22): for each pinned fragment in the Validation Commands block, `grep -cF` on `agents/skills/done/SKILL.md` returns exactly 1 for the single-site obligation probes (`immediately after the lock is acquired, write an empty per-run marker file`, `or its modification time falls inside the session window`, `apply conservative gating and treat every`, `anchor is the newest`, `any other skill or tool that mutates a plan file`, `binding agent commit hygiene; see Step 3 item 0b`) and at least 1 for the multi-site probes (`run-start-`, `written by a previous done run`, `does not anchor its own window`), and returns 0 for every forbidden pattern (the two 4c probes case-insensitively); fix both sides of any mismatch in the same edit

## Post-archive addendum (2026-09-06): run-start marker probe pins

Added by the wording-trio plan for backlog 2026-09-06-done-run-start-probe-coverage (r1-r4 probe literals; the original Validation Commands block stays frozen; counts re-measured at authoring). Run from the repo root.

```bash
F=agents/skills/done/SKILL.md
fail() { echo "FAIL: $1"; exit 1; }
[ -f "$F" ] || fail "done SKILL.md missing"
grep -Fq 'mkdir -p "${TMP_DIR%/}/done-session"' "$F" || fail "snippet mkdir line"
grep -Fq 'run-start-$(date -u +%Y%m%dT%H%M%SZ)' "$F" || fail "marker filename literal"
grep -Fq 'MARKER="$(cd "$(dirname "$MARKER")" && pwd)/$(basename "$MARKER")"' "$F" || fail "canonicalization line"
# the sed literal is pinned as two fixed fragments (shell-quoting the whole line would need embedded single-quote escapes)
grep -Fq 's/^tmp_dir = ["' "$F" || fail "sed literal head"
grep -Fq '\1/p' "$F" || fail "sed literal tail"
grep -Fq "matches no marker at gate time" "$F" || fail "echo-loss canonical statement"
grep -Fq "Keep the echoed marker path in chat context" "$F" || fail "marker-echo chat-context sentence"
grep -Fq "apply the Step 0 echo-loss fallback" "$F" || fail "Step 1.5 back-reference"
grep -Fq "never substitute the newest on-disk marker" "$F" || fail "never-recency clause"
grep -Fq 'prune no `run-start-*` markers this run' "$F" || fail "Step 2.62 prune-skip clause"
grep -Fq "prunes no" "$F" || fail "Step 0 canonical prune clause"
grep -Fq "NEVER remove the newest previous-run marker" "$F" || fail "never-delete pruning"
grep -Fq "create the directory if missing" "$F" || fail "directory creation"
grep -Fq 'excluding `{plans_completed_dir}`' "$F" || fail "producer scope exclusion"
grep -Fq "remove every line listing that path" "$F" || fail "removal rule"
grep -Fq "one repo-relative path per line" "$F" || fail "repo-relative path form"
grep -Fq 'head -n 1' "$F" || fail "r2 head -n 1"
grep -Fq 'case "$TMP_DIR"' "$F" || fail "r2 relative-path anchor"
echo "ADDENDUM PROBES OK"
```

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-04-done-plan-deliverable-append-dedupe.md: disposition folded into 2026-09-04-done-deliverables-log-dedupe-and-anchors.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-09-04-done-deliverables-removal-undergate.md: disposition folded into 2026-09-04-done-deliverables-log-dedupe-and-anchors.md (2026-09-25); per-item file deleted.
