# Plan: Named closeout baseline refusal for migrate

Backlog origin: docs/history/backlog/2026-10-31-malformed-closeout-baseline-json-refusal.md
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-15-plan-review-malformed-closeout-baseline-json-refusal-p214c32c8-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list; a series in which no round carries a source-plan identity resolves to its highest rN lexically)
Execution budget: 0.5h total, largest task 0.5h
Authoring claim: 2026-10-31-malformed-closeout-baseline-json-refusal.md (session sess_300f7308-32a8-4ac0-a549-e60137129798)
Executed: yes (7d83cc4fd4b687505d5e63df9cc4c90ecfcd330b)

## Terms

- Closeout baseline: the JSON record the `capture` command writes (captured_at, dirs, files, skipped) that `migrate` reads to decide which artifacts are new or modified; the file passed as the `--baseline` operand.
- Named refusal: the script's fail-closed error shape for bad input: one `ERROR:` line on stderr naming the offending path or shape, a stable exit code, and no partial effect (nothing copied).
- Skip sibling: the `closeout-baseline-skip.json` file a failed Phase 0 capture writes where the baseline would live; it never substitutes for a present baseline.
- `_cmd_migrate`: the function in `scripts/worktree_closeout_migrate.py` owning the migrate command's baseline load, guard sequence, and copy loop.
- Lesson #142 tuple: the project lessons rule (Family G, "A Fail-Closed State Reader Catches Decode Errors With I/O Errors"): a fail-closed reader guards its state read with `except (OSError, ValueError)`, because undecodable bytes raise `UnicodeDecodeError`, a `ValueError` subclass an `except OSError` arm never catches, and the mode is pinned with a test feeding undecodable bytes.

## Why

migrate reads a present baseline with an unguarded JSON parse: malformed or undecodable baseline bytes crash the command with a raw traceback (exit 1) instead of the named exit-2 refusal every neighboring bad-input path in the same script uses. The witnessed run stayed fail-closed (nothing was copied), but the operator-facing error surface is a Python stack trace where the script's own contract (lessons #142) requires a named refusal.

## Gist & Examples

TLDR: one guarded read turns the closeout migrate's baseline traceback into the script's standard named exit-2 refusal, restoring the bad-input contract every sibling path already follows (code-quality).

Before (today): `migrate --baseline <file with "{invalid json">` exits 1 with an uncaught `JSONDecodeError` traceback; a baseline holding invalid UTF-8 bytes crashes with a `UnicodeDecodeError` traceback; the witnessed validation record shows exactly this shape (exit 1, traceback, no target copy).

After (this plan): the same inputs produce one `ERROR: baseline unreadable or not valid JSON: <baseline path> (<exception detail>)` line on stderr, exit code 2, and nothing copied; a valid skip sibling does not substitute for the malformed baseline; the missing-baseline and baseline-lacks-dirs refusals are unchanged.

Edge cases: a read OSError between the existence check and the read (a permission change or a race) lands in the same refusal; baseline JSON that parses to a non-object keeps today's behavior (recorded as an omit-extension disposition in Assumptions: decided, not tasked, no backlog row); no schema validation is added, per the predecessor completed plan's explicit decline (docs/history/plans/completed/2026-10-27-plan-closeout-missing-phase0-baseline.md).

## Outcome

A malformed or undecodable closeout baseline reports as the script's named exit-2 refusal instead of a raw traceback.

- The origin's three named failure classes (read OSError, text decode, JSON parse) each resolve to the same named refusal with nothing copied; RuntimeError-class parse escapes beyond them (pathological nesting depth) keep today's fail-closed crash.
- A present malformed baseline still refuses even when a valid skip sibling exists (present-baseline precedence preserved).
- The script's existing refusal family (missing baseline, baseline lacks dirs, manifest not JSON, scoped inventory unreadable) stays green.

Gate delta: one added named refusal arm (baseline unreadable or not valid JSON, exit 2) and the removal of the crash exit path it replaces (the uncaught-exception exit the origin witnesses at exit 1 with a traceback); a fix-class refusal-path addition priced by validation-authoring-rules rule 42's origin-cited no-exit justification: the origin row and its PLAN-PROMPTS dispatch entry record and reject every alternative (keep the raw traceback, rejected by the Family G #142 named-refusal contract; a sibling-skip override of malformed JSON, rejected by the predecessor completed plan's present-baseline rule; a baseline-schema validator, rejected as unwitnessed machinery the predecessor plan explicitly declines; docs-only or classifying the traceback as a passing refusal, rejected because the parse stays unguarded); the three class-default alternatives are each impossible (add the sanctioned exit: treating an unreadable baseline as an implicit empty baseline would silently skip pre-existing artifacts, the failure the script's refusal family prevents, as the missing-baseline arm records; remove the false positive: the crash is a genuine bad-input failure and no valid-input path is refused; simplify the flow: the guarded read is already the minimal statement in the load path and no simplification removes the need to refuse on bad input); no gate, validator, lock, ledger, schema field, or dispatch-pausing condition added or removed.

## Assumptions

- assume exit code 2 for the new refusal; basis: every neighboring bad-input path in the same script (missing baseline, baseline lacks dirs, manifest not JSON, scoped inventory unreadable, git-env sanitize) returns 2 (verified in source, 2026-11-15).
- assume the refusal is one `ERROR:` stderr line without a remedy block; basis: the single-line sibling refusals of the same load region (scoped inventory unreadable, baseline lacks dirs) and the origin's concise-refusal ask; the nearest missing-baseline refusal carries a remedy block but names a different condition (absence, not unreadability); simpler-design comparison recorded 2026-11-15 (receipt in the trailer).
- assume the guard tuple is `except (OSError, ValueError)`; basis: lessons #142 (undecodable bytes raise UnicodeDecodeError, a ValueError subclass; derive the tuple from the read's full raise surface) and the same file's scoped-inventory arm already uses exactly this tuple; simpler-design comparison recorded 2026-11-15 (receipt in the trailer).
- assume the exact refusal text `ERROR: baseline unreadable or not valid JSON: <baseline path> (<exception detail>)`; basis: generated at authoring time 2026-11-15 from the sibling inventory-unreadable message form in the same file (same family prefix and parenthesized exception, distinct subject noun), matching the single-line sibling shape.
- assume the focused regression cases live beside the existing baseline refusal pins in `scripts/test_worktree_closeout_migrate.py`; basis: that file holds the skip-sibling, missing-baseline, and lacks-dirs pins (anchors verified in source 2026-11-15).
- assume no schema or type validation is added; basis: the predecessor completed plan explicitly declines broader schema validation, and the origin's three named failure classes (read, text-decode, JSON-parse) bound the work.
- assume the fix site is `_cmd_migrate`'s baseline load, the statement `baseline = json.loads(baseline_path.read_text(encoding="utf-8"))`; basis: verified in source 2026-11-15 at this plan's base tip; the origin's line pin (1119) has drifted as the file grew, so tasks anchor by function and statement shape, never by line number.
- assume the origin row's `Quarantine: 2026-11-04` field does not gate authoring; basis: the payload-side authoring procedure (agents/skills/maintenance/template-authoring.md, run under the operator's binding PLAN-PROMPTS walk mandate; its start gates are covered/gone, merge-or-rebase/done-lock, foreign-claim, and the availability walk) names no quarantine gate, and the PLAN-PROMPTS dispatch entry admits this row with work-type verdict plan-worthy; decisions.md D2's selection-layer quarantine exclusion is a survey-time gate, not the operative path for a dispatched entry.
- valid-JSON non-object baseline shape (for example a JSON array): omit-extension (maintenance-selected arm); today that shape crashes on the statement following the guarded read with an AttributeError, the same crash class one line below the guarded statement, but the origin and its PLAN-PROMPTS dispatch entry enumerate exactly three failure classes and the predecessor completed plan declines shape expansion, so the shape stays untouched and no backlog row is filed.
- the origin row's `Driving force:` field reads observability; this plan declares code-quality deliberately: the named-refusal contract being restored is the fail-closed verifier's code-quality correctness rule (lessons #142), not an observability surface; basis recorded at authoring and re-recorded here 2026-11-15.

Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: each named bad-input mode (malformed JSON, undecodable bytes, read OSError) exits 2 with the named refusal and no traceback, exercised through the real CLI entry by the focused tests; the CLI probe in Validation Commands exercises the malformed-JSON and undecodable-bytes modes.
- invariant preservation: present-baseline-over-skip precedence, missing-baseline refusal, lacks-dirs refusal, and manifest-not-JSON refusal unchanged, witnessed by the existing pins staying green; the inventory-unreadable refusal unchanged (its arm sits outside this plan's editable region and is frozen, not pin-witnessed).
- consistency: the refusal line matches the file's existing named-refusal pattern (ERROR: prefix, offending path named, exception detail in parentheses).

**Done when:**
- The focused bad-input regression cases (malformed JSON with a valid skip sibling; undecodable bytes; baseline read raising OSError) pass in `scripts/test_worktree_closeout_migrate.py`.
- The focused migrate suite `scripts/test_worktree_closeout_migrate.py` passes in full.
- The CLI probe in Validation Commands shows exit 2, the refusal line, no traceback, and an empty target directory.

**Ship when:**
- Nothing external; this plan is fully repository-verifiable.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/worktree_closeout_migrate.py` (Task 1) (partially in scope: only `_cmd_migrate`'s baseline load region; all other functions and command arms in this file are frozen; reject any review finding that touches them)

**Tests:**
- `scripts/test_worktree_closeout_migrate.py` (Task 1) (focused additions beside the existing baseline refusal pins; existing tests in this file are frozen, and any refusal-message pin that must be re-pinned is reported)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/worktree_closeout_migrate.py` regions outside `_cmd_migrate`'s baseline load region; reason: frozen per the partial-scope note above
- the manifest path's unguarded read OSError surface in the same function; reason: a different input path, unwitnessed, and outside the origin's three named failure classes
- the sibling cluster rows `docs/history/backlog/2026-10-31-closeout-zero-delta-report-arm-coverage.md` and `docs/history/backlog/2026-11-06-phase0-baseline-midflow-entry-order.md`; reason: distinct surfaces owning their own rows (Cluster context only)

## Validation Commands

Authoring-time record (2026-11-15, this plan's bytes at authoring): fix_plan_em_dashes.py pass (0 substitutions, run over the file before this write's bytes landed); check-no-em-dash.sh touched pass; scan-public-hygiene.sh pass (final OUTCOME line read); pre-round structural gate pass (OUTCOME: pass); rule 22 audit: bash -n over the Validation Commands block clean; rule 19 RED-today evidence, executed 2026-11-15 against the base tip: the malformed-baseline CLI probe below fails today with exit 1 and a JSONDecodeError traceback (probed, recorded), so the probe's exit-2 and refusal-line checks are RED until Task 1 lands; the undecodable-bytes probe fails today with exit 1 and a UnicodeDecodeError traceback (probed, recorded). Round-start state for r1: the authoring branch tip at authoring, plan bytes at the pre-round pass digest.

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
PY=python3
[ -x "$HOME/.agents/venvs/ai-playbook-test/bin/python" ] && PY="$HOME/.agents/venvs/ai-playbook-test/bin/python"
"$PY" -m pytest scripts/test_worktree_closeout_migrate.py -q || exit 1
# witnessed-invocation probes over the executed tree: a malformed or
# undecodable baseline refuses with the named exit-2 refusal, never a
# traceback, and copies nothing
PROBE_TMP="$(mktemp -d)"
mkdir -p "$PROBE_TMP/source" "$PROBE_TMP/target"
printf '{invalid json' > "$PROBE_TMP/baseline.json"
"$PY" scripts/worktree_closeout_migrate.py migrate --baseline "$PROBE_TMP/baseline.json" --source "$PROBE_TMP/source" --target "$PROBE_TMP/target" --manifest "$PROBE_TMP/manifest.json" > "$PROBE_TMP/out.txt" 2> "$PROBE_TMP/err.txt"
PROBE_RC=$?
[ "$PROBE_RC" -eq 2 ] || { echo "malformed-baseline probe: expected exit 2, got $PROBE_RC"; rm -rf "$PROBE_TMP"; exit 1; }
grep -qF "ERROR: baseline unreadable or not valid JSON:" "$PROBE_TMP/err.txt" || { echo "malformed-baseline probe: refusal line missing"; rm -rf "$PROBE_TMP"; exit 1; }
grep -qF "$PROBE_TMP/baseline.json" "$PROBE_TMP/err.txt" || { echo "malformed-baseline probe: baseline path not named"; rm -rf "$PROBE_TMP"; exit 1; }
SWEEP_RC=0
grep -qi "traceback" "$PROBE_TMP/err.txt" || SWEEP_RC=$?
[ "$SWEEP_RC" -le 1 ] || { echo "malformed-baseline probe: traceback sweep tool error rc=$SWEEP_RC"; rm -rf "$PROBE_TMP"; exit 1; }
[ "$SWEEP_RC" -eq 1 ] || { echo "malformed-baseline probe: traceback present"; rm -rf "$PROBE_TMP"; exit 1; }
[ -z "$(ls -A "$PROBE_TMP/target")" ] || { echo "malformed-baseline probe: target directory not empty"; rm -rf "$PROBE_TMP"; exit 1; }
printf '\377\376\001bad' > "$PROBE_TMP/baseline2.json"
"$PY" scripts/worktree_closeout_migrate.py migrate --baseline "$PROBE_TMP/baseline2.json" --source "$PROBE_TMP/source" --target "$PROBE_TMP/target" --manifest "$PROBE_TMP/manifest.json" > "$PROBE_TMP/out2.txt" 2> "$PROBE_TMP/err2.txt"
PROBE2_RC=$?
[ "$PROBE2_RC" -eq 2 ] || { echo "undecodable-baseline probe: expected exit 2, got $PROBE2_RC"; rm -rf "$PROBE_TMP"; exit 1; }
grep -qF "ERROR: baseline unreadable or not valid JSON:" "$PROBE_TMP/err2.txt" || { echo "undecodable-baseline probe: refusal line missing"; rm -rf "$PROBE_TMP"; exit 1; }
grep -qF "$PROBE_TMP/baseline2.json" "$PROBE_TMP/err2.txt" || { echo "undecodable-baseline probe: baseline path not named"; rm -rf "$PROBE_TMP"; exit 1; }
SWEEP2_RC=0
grep -qi "traceback" "$PROBE_TMP/err2.txt" || SWEEP2_RC=$?
[ "$SWEEP2_RC" -le 1 ] || { echo "undecodable-baseline probe: traceback sweep tool error rc=$SWEEP2_RC"; rm -rf "$PROBE_TMP"; exit 1; }
[ "$SWEEP2_RC" -eq 1 ] || { echo "undecodable-baseline probe: traceback present"; rm -rf "$PROBE_TMP"; exit 1; }
[ -z "$(ls -A "$PROBE_TMP/target")" ] || { echo "undecodable-baseline probe: target directory not empty"; rm -rf "$PROBE_TMP"; exit 1; }
rm -rf "$PROBE_TMP"
```

### Task 1: Named baseline refusal in migrate

Context surface: the plan's Terms and this task.

Files:
- `scripts/worktree_closeout_migrate.py`
- `scripts/test_worktree_closeout_migrate.py`

Primary class anchors:
- `_cmd_migrate` in `scripts/worktree_closeout_migrate.py`

- [x] `_cmd_migrate` delivers the baseline read and parse refusal: given a baseline file containing malformed JSON text, expects exit code 2, one `ERROR: baseline unreadable or not valid JSON:` stderr line naming the baseline path with the exception detail, no traceback, and no files copied to the target [class: IMPLEMENTATION_REQUIRED]
- [x] `_cmd_migrate` delivers the same refusal for undecodable bytes: given a baseline file whose bytes are invalid UTF-8, expects exit code 2, the same named refusal line, and no copy [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a malformed baseline and a valid `closeout-baseline-skip.json` sibling beside it, expects the refusal to stand unchanged with the sibling present and no copy; sibling-substitution precedence is additionally witnessed by the existing `test_skip_sibling_never_substitutes_for_baseline` pin [class: IMPLEMENTATION_REQUIRED]
- [x] `_cmd_migrate` delivers the same refusal when the baseline read raises OSError: given a readable-looking baseline made unreadable after the existence check (chmod 0o000; skip the case when running as root, the baseline read has no patch seam), expects exit code 2, the same named refusal line, and no copy [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect RED: the focused malformed-JSON, undecodable-bytes, and read-OSError cases fail against the unguarded parse (traceback, exit 1) while the existing missing-baseline, lacks-dirs, and skip-sibling pins already pass [class: REPOSITORY_TEST]
- [x] Wrap the baseline read and parse in the `except (OSError, ValueError)` guard emitting the exact refusal text from Assumptions; write the minimal implementation only (no schema or type checks) [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the focused cases pass, the existing refusal pins pass, and the focused migrate suite passes in full [class: REPOSITORY_TEST]
- [x] Commit: `fix: name the closeout baseline read and parse refusals in migrate` [class: IMPLEMENTATION_REQUIRED]
