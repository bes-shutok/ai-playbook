# Plan: Backlog inbox location gate

Backlog origin: `docs/history/backlog/2026-08-30-backlog-inbox-location-gate.md`

## Terms

- **Backlog inbox shape**: a tracked file whose NAME contains `backlog` or
  `deferred` (case-insensitive) in a location that is not the resolved backlog
  home. Content is never inspected.
- **Backlog home**: `{backlog_dir}` and `{backlog_completed_dir}` resolved from
  `.ai-playbook/facts.md` TOML; fallback `docs/history/backlog/` and
  `docs/history/backlog/completed/` when the keys are missing.
- **Named hot dirs**: `docs/maintenance/`, `docs/architecture/`, `docs/tmp/`:
  the locations the 2026-08-30 invented-destination incident actually used.
- **Selftest**: the script's built-in fixture run (`--selftest`), same
  convention as `scripts/validate_review_staging.py --selftest`.
- **Skill-gate marker**: consent marker at
  `~/.ai-playbook/runtime/skill-invoked/plans.<project>.<session>.marker`,
  refreshed before every plan-file write per
  `agents/hooks/skill-gate/README.md` Marker WRITE RECIPE (constants and
  `project`/`session` derivation live there and in `skill_gate.py`; the shared
  subprocess is `python3 ~/.ai-playbook/scripts/session_channel.py`).
- **Session key**: the value of the shared `session_channel.py` subprocess;
  empty-after-strip becomes the literal `no-session`, otherwise
  `sha1(value)[:16]` hex.

## Assumptions

- assume a two-surface scan: rule 2 (token pair) over tracked files via
  `git ls-files` (idempotent full tree; probe 2026-09-03 showed green today),
  and rule 1 (hot dirs) over a FILESYSTEM walk so gitignored shadow paths are
  seen: in ai-playbook-layout repos `docs/` is a gitignored shadow, and the
  invented `docs/maintenance/*-deferred-backlog.md` from the 2026-08-30
  incident was untracked; a tracked-only scan never fires in exactly the
  configuration this gate exists for.
- assume done-step placement between Step 2.65 and Step 2.64; basis: the done
  skill is the canonical commit path, and `scan-public-hygiene.sh` excludes
  `docs/**` where misfiled inboxes land.
- assume stdlib-only Python 3 like sibling validators; basis: repo convention
  (`validate_review_staging.py`, `summarize_review_stats.py`).

## Gist & Examples

A `docs/plans/`-less repo once caused review/done agents to invent
`docs/maintenance/<TICKET>-*-deferred-backlog.md` as a backlog inbox. The skill
layer now fails closed, but nothing mechanical rejects the write. This plan adds
a repo-agnostic filename-shape gate: `scripts/check_backlog_inbox_location.py`.

Rule (both parts, case-insensitive on the filename only):

1. filename contains `backlog` OR `deferred`, AND the path is under one of the
   named hot dirs (`docs/maintenance/`, `docs/architecture/`, `docs/tmp/`);
2. OR filename contains BOTH `backlog` AND `deferred`, AND the path is outside
   the backlog home.

Examples:

- `docs/maintenance/TT-123-deferred-backlog.md` → violation (rule 1: hot dir +
  both tokens).
- `docs/tmp/round-2-backlog-notes.md` → violation (rule 1).
- `docs/architecture/deferred-queue-design.md` → violation (rule 1: `deferred`
  in a hot dir; hot-dir hits fire on either token).
- `docs/plans/2026-09-03-x-deferred-backlog.md` → violation (rule 2: both
  tokens outside the backlog home).
- `docs/maintenance/confluence-sync-manifest.json` → allowed (no token).
- `docs/history/backlog/2026-09-03-anything.md` and
  `docs/history/backlog/completed/2026-08-28-fence-scanner-family.md` →
  allowed (inside the backlog home).
- `docs/reviews/2026-09-01-plan-review-x-r2.md` → allowed (no token).

facts resolution reads `backlog_dir` / `backlog_completed_dir` from
`.ai-playbook/facts.md`; missing keys fall back to the defaults above with a
warning on stderr. The named hot dirs stay gated regardless of facts state
(that is the incident shape: facts were missing when the invention happened).

Scan surface: rule 2 runs over tracked files (`git ls-files -z`). Rule 1 runs
over a filesystem walk of the three hot dirs, so untracked and gitignored files
(a gitignored `docs/` shadow tree) are gated too. Two carve-outs keep the gate
green against this repo's own conventions, both keyed on the relative path
inside `docs/tmp/`: paths containing the `plan-requirements-` filename prefix
(plans-skill requirements buffers legitimately use backlog-item slugs) and
paths under `docs/tmp/execute-plan/` (session-log trees named after plan
slugs). Both carve-outs match on path-segment boundaries: `docs/tmp/execute-plan-sibling/evil-backlog.md`
is NOT covered and must fail. The `plan-requirements-` carve-out is a BASENAME-PREFIX test
(`basename().startswith("plan-requirements-")`), never a substring match
anywhere in the relative path, so a planted `docs/tmp/notes/plan-requirements-fake/evil-backlog.md`
still fires. Only file basenames are token-matched; directory names never fire.
Everything else under the hot dirs, tracked or not, is gated.

Wiring: a new `done` skill step runs the validator (exit 1 aborts the commit
flow). On violations the fix is disposition-dependent: a file that is genuine
backlog material moves into the resolved `{backlog_dir}` (rename to the
`YYYY-MM-DD-<slug>.md` convention when needed); a legitimate Layer 2 doc that
merely trips the filename shape is renamed to a compliant name, asking the user
when the run is interactive; never a silent move that misfiles real content.

## Evaluation Criteria

**Quality dimensions:**

- correctness: `--selftest` green: every violation fixture exits 1 with the
  path listed, every allowed fixture exits 0; real tracked tree exits 0 today.
- maintainability: stdlib-only, `--selftest` / `--help` conventions match
  `scripts/validate_review_staging.py`; no content-based matching anywhere.
- observability: each violation prints the path and which rule (1 or 2) fired.

**Done when:**

- `python3 scripts/check_backlog_inbox_location.py --selftest` exits 0.
- `python3 scripts/check_backlog_inbox_location.py` exits 0 on the tracked tree.
- done skill runs the gate as a numbered step with updated chain lines, and
  Validation Command 3 (`python3 -m py_compile`) holds for the new script.

**Ship when:**

- the runtime copy at `~/.ai-playbook/scripts/check_backlog_inbox_location.py`
  is refreshed by the existing copy-sync redeploy flow (external to this repo;
  not a checklist item).

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and
fix if valid):

**Production code:**

- `scripts/check_backlog_inbox_location.py` *(new)*

**Docs/instructions:**

- `agents/skills/done/SKILL.md` (new step + chain lines + workflow-continuity
  line; all other steps frozen)
- `agents/skills/receiving-review/SKILL.md` (one-line second-line-of-defense
  note in Backlog capture; rest of the file frozen)
- `README.md` (one catalog row for the new script; rest frozen)

**Plan-related extension**; implementation and review may change files not
listed above. Treat a finding as in scope when it is **causally related to this
plan**: it implements or completes a plan task, fixes a regression introduced by
plan work, closes wiring or docs implied by an explicit must-fix change, or
contradicts a contract the plan changed. If the link to the plan is weak or
speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**

- `scripts/scan-public-hygiene.sh`; reason: deliberately NOT the gate home
  (scan excludes `docs/**`); changing its scope is a different plan.
- `agents/skills/bootstrap-ai-playbook/` and `agents/skills/doc-hierarchy/`;
  reason: their hardening landed 2026-08-30; this plan only consumes the
  backlog keys.

## Validation Commands

```bash
# 1. Selftest: synthetic violation + allowed fixtures (fail-closed block)
python3 scripts/check_backlog_inbox_location.py --selftest || { echo 'FAIL: selftest'; exit 1; }

# 2. Real tree is green (allowed backlog home, no misfiled inboxes)
python3 scripts/check_backlog_inbox_location.py || { echo 'FAIL: real tree flagged'; exit 1; }

# 3. Syntax check of the new script
python3 -m py_compile scripts/check_backlog_inbox_location.py || { echo 'FAIL: compile'; exit 1; }

# 4. done skill wiring: gate step exists, runs the canonical runtime/repo
#    validator, and aborts on failure (presence probes, one per obligation)
grep -q '^## Step 2.645: Backlog inbox location gate' agents/skills/done/SKILL.md \
  || { echo 'FAIL: gate step header missing'; exit 1; }
grep -q 'check_backlog_inbox_location[.]py' agents/skills/done/SKILL.md \
  || { echo 'FAIL: gate step does not invoke the validator'; exit 1; }
grep -q 'continue to Step 2.645' agents/skills/done/SKILL.md \
  || { echo 'FAIL: chain into gate step missing'; exit 1; }

# 5. Old chain line superseded: 2.65 must no longer continue straight to 2.64.
#    The [^0-9] tail guard keeps the mandated "continue to Step 2.645" lines
#    from matching (after "2.64" they carry a digit), so only the stale
#    2.65->2.64 edge fires; the bracket-escaped literal is intentional so this
#    document cannot self-match; exclude this plan file from any broader sweep.
if tr '\n' ' ' < agents/skills/done/SKILL.md \
   | grep -Eq 'Step 2[.]65 completes, immediately continue to Step 2[.]64([^0-9]|$)'; then
  echo 'FAIL: stale chain line 2.65->2.64 still present'; exit 1
fi

# 6. receiving-review carries the second-line-of-defense note
grep -q 'check_backlog_inbox_location[.]py' agents/skills/receiving-review/SKILL.md \
  || { echo 'FAIL: receiving-review note missing'; exit 1; }

# 7. README catalog row exists
grep -q 'scripts/check_backlog_inbox_location[.]py' README.md \
  || { echo 'FAIL: README row missing'; exit 1; }
```

Notes on the checks: commands 4-7 are positive-presence probes and are RED
until their tasks land (the step, note, and row do not exist today (verified
by probe 2026-09-03). Command 5's `if grep ...; then fail` form is a
forbidden-match sweep; the flatten step makes it wrap-tolerant, and the
`[.]` escapes in commands 4, 6, 7 and inside 5's pattern are intentional
self-match immunity (this plan file is committed; its own command text must not
satisfy the probes; commands 4/6/7 anchor on file paths in the TARGET files,
so the plan's own text never counts).

### Task 1: Validator script with built-in selftest (RED → GREEN)

Files:
- `scripts/check_backlog_inbox_location.py` *(new)*

- [x] Write the failing skeleton: `--selftest` builds a synthetic tree in a
  temp dir containing the Gist's violation fixtures (hot-dir `backlog` token,
  hot-dir `deferred` token, hot-dir both tokens in a subdirectory
  `docs/maintenance/sub/`, both tokens outside backlog home under
  `docs/plans/`) and allowed fixtures (backlog home item, completed home item,
  token-free hot-dir file, token filename outside any hot dir and without the
  second token, e.g. `docs/reviews/x-deferred.md` → allowed by rule 2 since
  `backlog` is absent; record this asymmetry in a selftest comment) plus a
  facts-less variant exercising the fallback backlog home; plus an UNTRACKED
  gitignored violation fixture inside a hot dir (synthetic git repo: one
  commit with explicit `-c user.email=… -c user.name=…` so the fixture does
  not depend on ambient git identity, then create the file without `git add`)
  proving the rule-1 filesystem
  walk sees shadow-tree files, and allowed carve-out fixtures under `docs/tmp/`
  (`plan-requirements-<slug>.md` with a backlog slug; a file under
  `docs/tmp/execute-plan/<plan-slug-with-backlog>/` whose basename itself MUST
  contain the token (a token-free basename would pass even with the carve-out
  removed, since directory names never fire); the carve-out fixture must also include the segment-boundary
  discriminator `docs/tmp/execute-plan-sibling/evil-backlog.md`, which must
  FAIL, so an over-broad substring carve-out cannot pass), and a CARVE-OPT-OUT
  discriminator fixture `docs/tmp/notes/plan-requirements-fake/evil-backlog.md`
  that must FAIL despite the substring (proves the prefix-only carve-out),
  and an UPPERCASE-token fixture (`docs/architecture/BACKLOG-notes.md` must
  fail) proving the case-insensitive token match. All rule-2 fixtures (token
  pair outside the backlog home) must be COMMITTED in the synthetic repo's
  single commit so `git ls-files` sees them; the hot-dir walk must tolerate
  absent dirs (`docs/architecture/` does not exist in the real repo);
  assert exit codes.
  Run → expect RED: `python3 scripts/check_backlog_inbox_location.py --selftest`
  (rule functions are stubs, violations pass through).
- [x] Implement the rule per Gist: rule 2 over `git ls-files -z`, rule 1 over
  an `os.walk` of the three hot dirs (untracked files included), both under
  `--repo-root` (default: git toplevel of the current directory, CWD fallback
  when git is unavailable); case-insensitive basename token test only,
  `docs/tmp/` carve-outs by relative path, backlog-home exclusion from facts
  TOML with stderr warning fallback; print `<path>: rule <N>` per violation;
  exit 1 when any violation, else 0.
- [x] Run → expect GREEN: `python3 scripts/check_backlog_inbox_location.py --selftest`
- [x] Run → expect GREEN: `python3 scripts/check_backlog_inbox_location.py`
  against the real tracked tree (probe verified green 2026-09-03).
- [x] Run → expect GREEN: `python3 -m py_compile scripts/check_backlog_inbox_location.py`
- [x] Commit: `scripts: add backlog inbox location gate validator`

### Task 2: Wire the gate into the done skill

Files:
- `agents/skills/done/SKILL.md`

- [x] Insert `## Step 2.645: Backlog inbox location gate` between Step 2.65's
  continuation line and Step 2.64, following the step template of Step 2.64:
  resolve the validator as `VALIDATOR="${BACKLOG_LOCATION_GATE:-$HOME/.ai-playbook/scripts/check_backlog_inbox_location.py}"`,
  falling back to the repo-relative `scripts/check_backlog_inbox_location.py`
  when the runtime copy is absent. If NEITHER copy exists, print a one-line
  warning naming the missing script and CONTINUE (fail-open): the gate is the
  second line of defense behind the receiving-review skill hardening, and the
  done skill is vendored to project repos where the copy-sync has not landed;
  a hard abort there would block every commit until an external redeploy.
  When a copy exists, run it over its full scan surface (rule 2 tracked tree
  plus rule 1 hot-dir filesystem walk) with `|| exit 1`; on
  failure, fix per the Gist remediation paragraph (backlog material moves to
  the resolved `{backlog_dir}` per `receiving-review` Backlog capture; a
  legitimate Layer 2 doc is renamed, asking the user when interactive) before
  continuing.
- [x] Update the two chain lines: "After Step 2.65 completes, immediately
  continue to Step 2.645." and "After Step 2.645 completes, immediately
  continue to Step 2.64."; update the workflow-continuity line (line ~22) to
  include 2.645 in the step sequence and the empty-tree exception list.
- [x] Run → expect GREEN: Validation Commands 4 and 5.
- [x] Commit: `skills: wire backlog inbox location gate into done flow`

### Task 3: Cross-references (receiving-review note + README row)

Files:
- `agents/skills/receiving-review/SKILL.md`
- `README.md`

- [x] Add one sentence to `receiving-review` **Backlog capture** (after the
  destination-resolution paragraph): the mechanical second line of defense is
  `scripts/check_backlog_inbox_location.py`, run by the done flow, which
  rejects files matching backlog-inbox filename shapes outside the backlog
  home, over both the tracked tree and untracked files inside the named hot
  dirs (the 2026-08-30 incident file was untracked). Do not restate the rule
  body (single source: the script).
- [x] Add one `README.md` catalog row for `scripts/check_backlog_inbox_location.py`
  beside the `validate_review_staging.py` row: one-line purpose +
  `--selftest` convention.
- [x] Run → expect GREEN: Validation Commands 6 and 7.
- [x] Run → expect GREEN: full Validation Commands block, all commands.
- [x] Commit: `docs: catalog backlog inbox location gate + receiving-review note`

## Disposition of migrated backlog items
- docs/history/backlog/completed/2026-09-03-backlog-gate-absolute-home-fixture.md: disposition folded into 2026-09-03-backlog-inbox-location-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-03-backlog-gate-collapse-classification-tail.md: disposition folded into 2026-09-03-backlog-inbox-location-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-03-backlog-gate-hot-dirs-facts-key.md: disposition folded into 2026-09-03-backlog-inbox-location-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-03-backlog-gate-parser-unavailable-fixture.md: disposition folded into 2026-09-03-backlog-inbox-location-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-03-backlog-gate-symlink-dir-bypass.md: disposition folded into 2026-09-03-backlog-inbox-location-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-07-backlog-gate-r5-doc-drift.md: disposition folded into 2026-09-03-backlog-inbox-location-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-07-backlog-gate-windows-portability.md: disposition folded into 2026-09-03-backlog-inbox-location-gate.md (2026-09-25); per-item file deleted.
- docs/history/backlog/completed/2026-09-16-review-backlog-redaction-gate.md: disposition folded into 2026-09-03-backlog-inbox-location-gate.md (2026-09-25); per-item file deleted.

- docs/history/backlog/completed/2026-08-30-backlog-inbox-location-gate.md: disposition folded into 2026-09-03-backlog-inbox-location-gate.md (2026-09-25); per-item file deleted.
