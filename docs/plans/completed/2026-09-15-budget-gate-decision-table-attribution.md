# Plan: budget-gate decision-table attribution isolation

Backlog origin: `docs/history/backlog/2026-09-13-budget-gate-decision-table-attribution.md` (scope of record; this plan SUPERSEDES its contradiction-triggered "When to act" posture)
Procedure home amended by this plan: `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md` (the canonical item owning the Ship-when drive procedure, the post-drive decision table, and the real-pause observation)
Language guidelines: `projects/.ai-playbook/python_guidelines.md`

## Terms

- **deny-envelope drive**: the single live Ship-when check that arms the budget-guard flag, drives one real tool call in a trusted Codex session, and observes the denial, recorded in the sibling item's "Ship-when live check".
- **fired marker**: `~/.ai-playbook/runtime/budget-guard.fired`, written best-effort by the budget-guard core on the FIRST block in a window (anti-thrash) by ANY session's hook run, in either registered runtime; content is the reset epoch it fired for.
- **co-registered matcher-`.*` hooks**: the `PreToolUse` hooks in `~/.codex/hooks.json` matching every tool call; today that is `require-luna.py` (model check) and the budget-guard `codex.sh` itself.
- **attribution gate**: a per-verdict check that the drive's outcome is attributable to the budget-guard envelope (marker baseline match, codex-and-zcode session checks clean, contingency steps restored); missing or unverifiable gate evidence means the verdict is contaminated.
- **trust-hash coupling**: the codex binary hash-gates each hooks.json hook group via `trusted_hash` under `[hooks.state]` in `~/.codex/config.toml`; any hooks.json edit invalidates the affected groups' trust (including the budget-guard hook's when group indices shift) until a fresh approval in a session started after the edit.

## Design Invariants (CR Guard)

1. The four existing post-drive verdicts keep their semantics; this plan adds attribution gates, it does not re-label outcomes (a failed gate marks a verdict contaminated, it does not create a fifth verdict).
2. The human Codex hook trust prompt remains the drive's external gate; nothing in this plan schedules or performs the drive.
3. `~/.codex/hooks.json` is user-global config: the plan records every manipulation as procedure text only; executing them is part of the drive (Ship-when prose), never a plan task.
4. Read-only isolation (marker baseline, codex-and-zcode session checks) is always-on; the hooks.json disable is a row-2-triggered contingency only, because the edit invalidates hook trust for the budget-guard hook itself and all Codex sessions on the host.
5. The narrow `codex-budget-reset-guard` hook (matcher `^mcp__codex_app__consume_usage_reset$`) is out of scope: it cannot deny a generic tool call.

## Assumptions

- assume proactive read-only isolation (marker baseline plus codex-and-zcode session checks) on every drive, upgrading the origin item's contradiction-triggered posture; basis: the origin item's Finding section (a concurrent same-window writer of the host-global fired marker fakes the row-3 verdict with no contradiction signal) and standing pre-authorization to take recommended options.
- assume the hooks.json disable is demoted to a row-2-triggered contingency with the trust cycle documented; basis: row 2's ISO string check already routes co-registered-hook denials to a do-not-close verdict, so the always-on disable adds trust invalidation and host-wide exposure without closing a gap the table leaves open (three review workers converged on this).
- assume the exact backup/restore commands for `~/.codex/hooks.json` belong in the sibling item's procedure text as Ship-when prose; basis: the checklist inclusion gate classifies user-global config writes as external-environment actions, never plan tasks.
- assume the README closure sentence at `agents/hooks/budget-guard/README.md` becomes necessary-but-not-sufficient after this plan and gains one appended clause; basis: row 1 closure additionally requires the attribution gate post-amendment.

Decision points requiring a grill: isolation posture = proactive read-only isolation always-on plus the hooks.json disable demoted to a row-2-triggered contingency (supersedes, without editing at authoring time, the origin item's reactive "When to act" wording; Task 4 adds the supersession note at the top of that section); source: origin item Finding section, review workers' convergence across two rounds, standing pre-authorization; 2026-09-15; affects Gist, Tasks 1 to 4, Evaluation Criteria.

## Gist & Examples

What changes: the deny-envelope drive procedure in the sibling item currently isolates attribution only AFTER a suspicious outcome ("isolate before trusting a verdict that contradicts the fixture probes"). This plan makes the read-only isolation steps mandatory before every drive and wires an attribution gate into every decision-table verdict. Before the drive the operator records the drive session's own PID, runs a process check covering both registered runtimes (treating any unmatched line outside the recorded PID, its descendants, and the host's desktop-app helpers as contamination), records the fired marker's baseline stat (presence, mtime, content epoch) as part of the existing absence check, and records the co-registered matcher-`.*` hooks and their trust status; the session check re-runs at the drive boundary (flag-arm to tool call) and after the drive. After the drive, each verdict is trusted only when its attribution gate passes; missing or unverifiable gate evidence means contaminated. The hooks.json disable of `require-luna.py` moves out of the always-on path: it becomes the row-2 contingency, invoked only when a foreign denial is observed, with the full trust cycle documented (the edit invalidates `trusted_hash` for the affected groups, so a fresh trusted session and re-approval are required before re-driving, and the post-restore trust prompt is expected to reappear because the recorded trust keys are positional (group index and content), so it is approved in the next fresh session with a clean diff against the runtime backup).

Why: the current rows can be faked silently in one mode that has no at-the-table signal: a fired marker written by a CONCURRENT session's hook run in either runtime (the flag is host-global, so any session's tool call triggers the guard) produces the row-3 observation "marker PRESENT, no denial" without contradicting the fixture probes. Recording the marker baseline and checking for concurrent codex AND zcode processes converts that mode from undetectable to gated for the pre-call writer class; the point checks bound but do not prove window exclusivity, so a marker mtime not within 60 seconds of the drive call timestamp is treated as contaminated and the verdict is re-opened if later evidence contradicts it. The co-registered-hook denial mode is already routed to a conservative do-not-close by row 2's ISO check, so the always-on disable would add trust invalidation and host-wide exposure without closing a remaining gap, and it moves to the contingency path where its costs are paid only when a foreign denial makes attribution necessary.

Before (today): the drive runs with no marker baseline and no session check. A peer session's hook run writes the fired marker during the drive window; the operator observes "no denial, marker PRESENT" and records the row-3 verdict (envelope rejected), which is false attribution: this drive's hook may never have run, and nothing in the procedure detects the contamination.

After (this plan): the same drive first verifies no other codex or zcode process is running (pgrep over both runtime names, re-checked at the boundary and after), records "marker ABSENT, mtime none" as the baseline plus the co-registered hooks' trust status, then drives. Post-drive, the row-3 verdict requires its attribution gate: the marker appeared during the window with no concurrent codex or zcode process at any check, a marker mtime not near the drive call timestamp is contaminated, and a residual-risk note records that point checks bound but do not prove exclusivity. A require-luna denial (row 2) triggers the documented contingency: backup hooks.json (diff-verified), disable the co-registered hook, start a fresh trusted session and re-approve the trust prompt, re-drive with a re-taken baseline, then restore diff-verified; the hook trust prompt is expected to reappear for the shifted groups, and approving it in the next fresh session with a clean diff against the runtime backup is the correct terminal action.

Edge cases that shaped the design: the marker's content (reset epoch) matches the armed flag by construction, so content equality alone cannot discriminate writers; the mtime baseline plus the session checks carry that weight, and a short-lived session that ran outside the 60-second comparison window surfaces as a marker mtime inconsistent with the drive call timestamp, which the row-3 gate treats as contaminated, while a writer inside the window whose mtime lands near the call timestamp remains undetectable by mtime - the gate bounds that residual risk rather than proving exclusivity. The trust-hash coupling means the contingency's hooks.json edit needs its own fresh trust approval before the re-drive.

## Evaluation Criteria

**Quality dimensions:**
- completeness: each of the four decision-table rows' follow-through contains its own distinct attribution-gate parenthetical (one flattened fixed-string probe per row) and the real-pause section carries its own gate sentence anchored to its section; the drive procedure names the session check first, then the marker baseline, each step's failure aborting before irreversible action.
- executability: the contingency's backup, disable, trust-cycle, restore, and abort paths are exact, reversible, and name the real paths.
- docs consistency: existence greps (flattened, fixed-string) prove the new obligation lines exist; two negated flattened sweeps prove the contradiction-only caveat and the row-2 stale pointer are gone.

**Done when:**
- every task checkbox is checked and the Validation Commands block exits 0 against the edited items.

**Ship when:**
- the human-approved Codex hook trust prompt and the actual drive remain external prerequisites, unchanged from the sibling item.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

This plan amends procedure documents; the amended artifacts are the explicit must-fix paths below. There are no production-code or test paths.

**Documentation:**
- `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md` (the amended procedure home)
- `docs/history/backlog/2026-09-13-budget-gate-decision-table-attribution.md` (the origin item; Task 4 appends the supersession note)
- `agents/hooks/budget-guard/README.md` (Task 3 appends one closure clause)

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/hooks/budget-guard/budget_guard_core.py` and `codex.sh`; reason: hook code is out of scope; marker semantics verified against the current bytes
- `~/.codex/hooks.json`; reason: user-global config, procedure text only
- `agents/hooks/codex-budget-reset-guard/`; reason: narrow matcher, cannot deny a generic tool call

## Validation Commands

```bash
set -u
fail() { echo "VALIDATION FAIL: $1"; exit 1; }

ITEM=docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md
ORIGIN=docs/history/backlog/2026-09-13-budget-gate-decision-table-attribution.md
README=agents/hooks/budget-guard/README.md
test -f "$ITEM" || fail "sibling item missing"
test -f "$ORIGIN" || fail "origin item missing"
test -f "$README" || fail "README missing"

FLAT=$(tr '\n' ' ' < "$ITEM" | tr -s ' ')
# one flattened fixed-string probe per obligation (rule 7); all RED-today
case "$FLAT" in *"records the drive session's own PID at baseline"*) ;; *) fail "session-check step missing" ;; esac
case "$FLAT" in *"records the fired marker's baseline stat (presence, mtime, content epoch) and the co-registered matcher-"*) ;; *) fail "marker-baseline plus hooks-status step missing" ;; esac
case "$FLAT" in *"re-checked at the drive boundary and after the drive"*) ;; *) fail "session re-check missing" ;; esac
case "$FLAT" in *"whose gate evidence is missing or unverifiable is contaminated"*) ;; *) fail "missing-evidence rule missing" ;; esac
N3=$(printf '%s' "$FLAT" | grep -oF "written at step 3" | wc -l | tr -d ' ')
[ "$N3" -eq 2 ] || fail "renumbered step-3 references missing (found $N3 of 2)"
case "$FLAT" in *"before step 5"*) ;; *) fail "renumbered abort-clause reference missing" ;; esac
case "$FLAT" in *"written at step 2"*|*"before step 4"*) fail "stale step references remain" ;; esac
case "$FLAT" in *'hooks.json.budget-drive-backup'*) ;; *) fail "contingency backup path missing" ;; esac
case "$FLAT" in *"restore the hooks.json backup (diff-verified) in addition to removing the flag and the fired marker"*) ;; *) fail "abort-restore clause missing" ;; esac
case "$FLAT" in *"the hook trust prompt is EXPECTED to reappear for the shifted groups after the restore"*) ;; *) fail "trust-restore expectation missing" ;; esac
case "$FLAT" in *"the PreToolUse model check is disabled host-wide during the window"*) ;; *) fail "exposure warning missing" ;; esac
case "$FLAT" in *"bound the window to the single re-drive"*) ;; *) fail "window bound missing" ;; esac
# r2 (G5): one flattened fixed-string probe per r1-added obligation
case "$FLAT" in *"re-arm the guard flag at the canonical flag path with a FRESH"*) ;; *) fail "contingency fresh re-arm missing" ;; esac
case "$FLAT" in *"denial ISO check compares against the fresh"*) ;; *) fail "re-drive fresh-ISO comparison missing" ;; esac
case "$FLAT" in *'verify the `trusted_hash` entries for the restored groups'*) ;; *) fail "not-reappear trust-verification guard missing" ;; esac
case "$FLAT" in *'falling back to `~/.codex/hooks.json.budget-drive-backup`'*) ;; *) fail "restore-source fallback order missing" ;; esac
case "$FLAT" in *"retire both fixed-name backups by deleting them"*) ;; *) fail "backup retirement step missing" ;; esac

# r3 (H10): per-site restore-fallback probes - BOTH restore sites must carry
# the fallback needle, not merely one site somewhere in the item
SSSEG=${FLAT#*"Single-source restore branch"}
SSSEG=${SSSEG%%"Both-bad branch"*}
case "$SSSEG" in *'falling back to `~/.codex/hooks.json.budget-drive-backup`'*) ;; *) fail "single-source restore branch lacks the fallback needle" ;; esac
SOSEG=${FLAT#*"Standing order"}
case "$SOSEG" in *'or against `~/.codex/hooks.json.budget-drive-backup` when the runtime copy is the missing or mismatched one'*) ;; *) fail "standing order lacks the fallback diff target" ;; esac
# r3 (H11): flattened guards for obligations that were deletable while green
case "$FLAT" in *'Do not edit `~/.codex/config.toml`'*) ;; *) fail "do-not-edit-config mismatch-stop guard missing" ;; esac
case "$FLAT" in *"a second consecutive foreign denial is terminal"*) ;; *) fail "second-denial terminal rule missing" ;; esac

# r4 (I1): one flattened fixed-string probe per obligation that was
# deletable while green (pinned to the post-r4 item bytes)
case "$FLAT" in *"do not prove window exclusivity"*) ;; *) fail "residual-risk note missing" ;; esac
case "$FLAT" in *"for an unattended pause the substitute evidence"*) ;; *) fail "unattended-pause substitute-evidence rule missing" ;; esac
case "$FLAT" in *"an unidentified writer stops the drive"*) ;; *) fail "live-window unidentified-writer stop rule missing" ;; esac
case "$FLAT" in *"delete the whole group object"*) ;; *) fail "disable-step group-object deletion missing" ;; esac
case "$FLAT" in *"records the wall-clock timestamp of the drive tool call"*) ;; *) fail "wall-clock boundary recording missing" ;; esac
case "$FLAT" in *"Quiesce the first drive session"*) ;; *) fail "quiesce obligation missing" ;; esac
case "$FLAT" in *"the contamination modes are documented in docs/history/backlog/2026-09-13-budget-gate-decision-table-attribution.md"*) ;; *) fail "origin contamination-modes citation missing" ;; esac
case "$FLAT" in *"the core auto-removes the stale marker, so no anti-thrash suppression is possible"*) ;; *) fail "step-4 defense-in-depth note missing" ;; esac
# r4 (I7): flattened probes for the r3-added protocol branches
case "$FLAT" in *"confirms an intentional edit"*) ;; *) fail "superseded-edit branch missing" ;; esac
case "$FLAT" in *"refresh both fixed-name backups"*) ;; *) fail "superseded-edit refresh option missing" ;; esac
case "$FLAT" in *"stop and do not re-drive"*) ;; *) fail "stop trigger missing" ;; esac

# per-row gates: flattened fixed-string probe per distinct parenthetical,
# then region/total counts as secondary gates
case "$FLAT" in *"(co-registered hooks status recorded, marker baseline matched)"*) ;; *) fail "row-1 gate missing" ;; esac
case "$FLAT" in *"(marker baseline re-taken after the first drive)"*) ;; *) fail "row-2 gate missing" ;; esac
case "$FLAT" in *"(marker mtime within 60 seconds of the drive call timestamp, no concurrent codex or zcode process at any check"*) ;; *) fail "row-3 gate missing" ;; esac
case "$FLAT" in *"(baseline hooks trust status recorded and unchanged, marker baseline matched; when the contingency was invoked: contingency restore diff-verified, trust state confirmed)"*) ;; *) fail "row-4 gate missing" ;; esac
ROWS=$(sed -n '/## Decision table/,/## Real-pause/p' "$ITEM" | tr '\n' ' ' | tr -s ' ' | grep -o "attribution gate" | wc -l | tr -d ' ')
[ "$ROWS" -eq 4 ] || fail "expected exactly 4 row attribution gates, found $ROWS"
TOTAL=$(tr '\n' ' ' < "$ITEM" | tr -s ' ' | grep -o "attribution gate" | wc -l | tr -d ' ')
[ "$TOTAL" -eq 5 ] || fail "expected exactly 5 attribution-gate mentions (4 rows + real-pause), found $TOTAL"
RP=$(sed -n '/## Real-pause/,$p' "$ITEM" | tr '\n' ' ' | tr -s ' ')
case "$RP" in *"the same attribution gate passes"*) ;; *) fail "real-pause gate missing or misplaced" ;; esac

# region-anchored placement probes (review r1 F11): each fails on the broken
# placement it guards against, not only on absence
POS_SESSION=$(printf '%s' "$FLAT" | grep -boF "records the drive session's own PID at baseline" | head -1 | cut -d: -f1)
POS_MARKER=$(printf '%s' "$FLAT" | grep -boF "records the fired marker's baseline stat" | head -1 | cut -d: -f1)
if [ -z "$POS_SESSION" ] || [ -z "$POS_MARKER" ] || [ "$POS_SESSION" -ge "$POS_MARKER" ]; then
  fail "session check must precede the marker-baseline step (byte offsets $POS_SESSION vs $POS_MARKER)"
fi
grep -F "Envelope accepted" "$ITEM" | grep -F "(co-registered hooks status recorded, marker baseline matched)" >/dev/null || fail "row-1 gate not anchored to its verdict line"
grep -F "attribution unknown" "$ITEM" | grep -F "(marker baseline re-taken after the first drive)" >/dev/null || fail "row-2 gate not anchored to its verdict line"
grep -F "the envelope was rejected" "$ITEM" | grep -F "no concurrent codex or zcode process at any check" >/dev/null || fail "row-3 gate not anchored to its verdict line"
grep -F "trust or registration gap" "$ITEM" | grep -F "contingency restore diff-verified, trust state confirmed" >/dev/null || fail "row-4 gate not anchored to its verdict line"
BSEG=${FLAT%%"recording a checksum"*}
case "$BSEG" in *'AND to `~/.ai-playbook/runtime/hooks.json.budget-drive-backup`'*) ;; *) fail "runtime backup destination not recorded at the backup step" ;; esac
WTFLAT=$(sed -n '/^## When to act/,$p' "$ORIGIN" | tr '\n' ' ' | tr -s ' ')
case "$WTFLAT" in "## When to act Superseded by docs/plans/2026-09-15-budget-gate-decision-table-attribution.md"*) ;; *) fail "supersession note not at the top of the When to act section" ;; esac

# supersession and README closure clauses (flattened)
OFLAT=$(tr '\n' ' ' < "$ORIGIN" | tr -s ' ')
case "$OFLAT" in *"Superseded by docs/plans/2026-09-15-budget-gate-decision-table-attribution.md"*) ;; *) fail "origin supersession note missing" ;; esac
RFLAT=$(tr '\n' ' ' < "$README" | tr -s ' ')
case "$RFLAT" in *"and the item's attribution gate passes"*) ;; *) fail "README closure clause missing" ;; esac

# negated flattened sweeps: the contradiction-only caveat and the row-2 stale pointer are gone
case "$FLAT" in *"isolate before trusting a verdict that contradicts the fixture probes"*) fail "old contradiction-only caveat still present" ;; esac
case "$FLAT" in *"Isolate per the attribution caveat below"*) fail "row-2 stale caveat pointer still present" ;; esac
echo "VALIDATION OK"
```

### Task 1: always-on read-only isolation in the Ship-when live check

Files:
- `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md`

- [x] Record the pre-edit RED first: run the Validation Commands block once (it exits non-zero at the first failure; expected first-failure line "session-check step missing"), then run a per-probe pass (evaluate each case probe without exit) to record the full RED set: ALL obligation probes fire today including the missing-evidence and backup-path probes, all four row probes fire, both counts read 0, real-pause/supersession/README fire, AND both negated sweeps FAIL today (both caveat phrases exist in the current item; they turn GREEN only at Task 2).
- [x] Insert, as the FIRST pre-drive step (fail-closed order: the session check precedes any state change): "The operator records the drive session's own PID at baseline, runs pgrep -fl 'codex|zcode', and treats any unmatched line (excluding the recorded PID, its descendants, and the host's ChatGPT/Codex desktop-app helper processes) as contamination, stopping before the flag is armed; the same check is re-checked at the drive boundary and after the drive."
- [x] Extend the existing fired-marker absence step (do not add a parallel step): it records the fired marker's baseline stat (presence, mtime, content epoch) and the co-registered matcher-`.*` hooks and their trust status from the trusted session; a marker already PRESENT at baseline whose content matches no live window is removed before the drive, and a marker matching a live window is an abort-and-investigate condition (its writer is unknown); the operator also records the wall-clock timestamp of the drive tool call at the boundary re-check, which the row-3 mtime comparison uses.
- [x] Renumber every step reference in the item after the insertion: the drive step's and row 1's "step 2" become "step 3"; the abort clause's "step 4" becomes "step 5" (the clause's own text is extended in Task 2).
- [x] Run → expect: the re-run block still exits non-zero overall (later tasks' probes are still RED), but the three Task-1 probes (session-check, marker-baseline, re-check) now pass and both negated sweeps remain RED until Task 2; record the output.
- [x] Commit (staging exactly this task's Files list; insert the quoted text literally, without markdown backticks around the pgrep command, so the probes match): `docs: budget-gate drive procedure gains read-only attribution isolation`

### Task 2: attribution gates, the row-2 contingency, and the abort-restore clause

Files:
- `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md`

- [x] Append one attribution-gate sentence to each of the four rows' follow-through, quoting these exactly (each contains the phrase "attribution gate"): row 1 "verdict trusted only when the attribution gate passes (co-registered hooks status recorded, marker baseline matched)"; row 2 "verdict trusted only when the attribution gate passes (marker baseline re-taken after the first drive)"; row 3 "verdict trusted only when the attribution gate passes (marker mtime within 60 seconds of the drive call timestamp, no concurrent codex or zcode process at any check; a marker mtime not within 60 seconds of the call timestamp is contaminated)"; row 4 "verdict trusted only when the attribution gate passes (baseline hooks trust status recorded and unchanged, marker baseline matched; when the contingency was invoked: contingency restore diff-verified, trust state confirmed)".
- [x] Add the missing-evidence rule after the table: "a verdict whose gate evidence is missing or unverifiable is contaminated", followed by the residual-risk note: "the session checks are point-in-time bounds and do not prove window exclusivity; a verdict is re-opened if later evidence contradicts it".
- [x] Replace row 2's stale "Isolate per the attribution caveat below" pointer and the trailing caveat paragraph with the row-2 contingency as NUMBERED steps plus a separate abort clause (the paragraph carries the origin citation "the contamination modes are documented in docs/history/backlog/2026-09-13-budget-gate-decision-table-attribution.md" and must not contain the phrase "attribution gate"; the count gates reserve that phrase for the four rows and the real-pause section), and prescribe closing (or recording and excluding) the first drive session's PID before the re-drive baseline. Steps: (1) on a foreign denial, copy `~/.codex/hooks.json` to `~/.codex/hooks.json.budget-drive-backup` AND to `~/.ai-playbook/runtime/hooks.json.budget-drive-backup`, recording a checksum of each and verifying with `diff` before any edit; (2) disable the co-registered matcher-`.*` hooks other than the budget-guard hook; (3) start a FRESH trusted Codex session and re-approve the hook trust prompt (the edit invalidates `trusted_hash` for the affected groups); (4) quiesce the first drive session (close it, or record its PID for exclusion), re-take the marker baseline, and re-drive; (5) restore `~/.codex/hooks.json` from the backup (diff-verified); because the recorded trust keys are positional (group index and content), the hook trust prompt is EXPECTED to reappear for the shifted groups after the restore - approving it in the next fresh session, with the diff against the runtime backup clean, is the correct terminal action; record the extra approval. Safety clauses: "the PreToolUse model check is disabled host-wide during the window" and "bound the window to the single re-drive; a second consecutive foreign denial is terminal for this item's question and is reported, not re-driven". Abort clause, separate sentence: "If at any point the backup is missing, a checksum or diff mismatches, or the session dies mid-contingency: stop, restore require-luna's registration from `~/.ai-playbook/runtime/hooks.json.budget-drive-backup` (diff-verified), and do not re-drive; at the next Codex session start after any contingency, diff live `~/.codex/hooks.json` against the runtime backup and restore diff-verified on mismatch with no contingency in progress."
- [x] Extend the abort clause: if the drive aborts, restore the hooks.json backup (diff-verified) in addition to removing the flag and the fired marker, when the contingency was invoked.
- [x] Run → expect: the block exits non-zero with first-failure line "expected exactly 5 attribution-gate mentions ... found 4" (real-pause, supersession, README probes and the TOTAL count still RED), via a per-probe pass (evaluate each probe without exit), the four row probes, the region count (4), the missing-evidence rule, the backup-path, trust-confirmation, exposure, window-bound, and abort-restore probes, and both negated sweeps pass, while the TOTAL count, real-pause, supersession, and README probes remain RED; record the output.
- [x] Commit: `docs: decision-table verdicts gain attribution gates and the row-2 contingency`

r1/r2 note (2026-09-18): the item's current text supersedes the quoted snapshots above (row-3 negation relocated to the post-table paragraph; contingency/abort branches extended); the Validation Commands block is the only normative matcher.

### Task 3: real-pause gate and README closure clause

Files:
- `docs/history/backlog/2026-09-13-codex-deny-envelope-verification.md`
- `agents/hooks/budget-guard/README.md`

- [x] Extend the "Real-pause Ship-when observation" section: the observed backstop block counts as enforcement evidence only when the same attribution gate passes, with the baseline conjunct disjunctive for the backstop's primary scenario (a marker record already present at the boundary baseline whose content matches the pause's reset epoch, OR the marker's mtime inside the pause window with content matching that epoch) and the concurrent-writer check at the pause boundary as the shared conjunct; the boundary check requires an attended pause, and for an unattended pause the substitute evidence is the blocked session's own transcript showing the block reason, marker evidence alone being insufficient.
- [x] Append one clause to the README's ISO-closure sentence (the "a denial closes the question only when its reason embeds the armed flag's reset_at_iso" sentence in the Open envelope question section): "and the item's attribution gate passes".
- [x] Run → expect: the block exits non-zero at the supersession probe; via a per-probe pass, the real-pause probe, the total count gate (exactly 5), and the README probe pass; record the output. Embed appended clauses mid-sentence, lowercase as quoted (the needles are case-sensitive fixed strings).
- [x] Commit: `docs: real-pause observation inherits the attribution gate`

### Task 4: origin-item supersession note and final validation

Files:
- `docs/history/backlog/2026-09-13-budget-gate-decision-table-attribution.md`

- [x] Insert at the TOP of the origin item's "When to act" section: "Superseded by docs/plans/2026-09-15-budget-gate-decision-table-attribution.md: isolation is now mandatory pre-drive per the sibling item's procedure; this item remains the historical record of the finding, as does the completed budget-gate-family-residuals plan's Ship-when line (the sibling item is the sole procedure home)."
- [x] Run → expect GREEN: the full Validation Commands block exits 0 (the supersession probe included); record the output.
- [x] Commit: `docs: origin item superseded by proactive attribution isolation`

r1/r2 note (2026-09-18): the item's current text supersedes the quoted snapshots above (row-3 negation relocated to the post-table paragraph; contingency/abort branches extended); the Validation Commands block is the only normative matcher. The Task 4 quote also omits the item's second supersession sentence ("The imperative paragraph below is retained as historical record only: it is not a live instruction, and the sibling item's procedure is the only current isolation procedure."), added by r1 F6; the r2 pass additionally qualified the first supersession sentence to read-only isolation (session checks plus marker and hooks-trust baselines) with the hooks.json disable row-2-contingency-only.
