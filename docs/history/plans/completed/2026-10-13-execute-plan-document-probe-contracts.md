# Plan: execute-plan document probe contracts

Backlog origin: docs/history/backlog/2026-10-08-execute-plan-document-probes-check-only-keyword.md

Driving force: code-quality

Plan review record: the staging series {reviews_dir}/2026-10-13-plan-review-execute-plan-document-probe-contracts-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

Execution budget: 2h total, largest task 0.75h

## Terms

- `predecessor declaration`: the JSON document an orchestrator builds from a plan's `Predecessors:` block and passes to `scripts/execute_plan_runtime.py --operation precondition --predecessors-file <json>`.
- `artifact outcome`: a predecessor outcome of `kind: artifact`; it verifies the content of one repository file at the declared `path`.
- `required clause`: a non-empty literal declared in `contains`; the string form declares one clause, the list form declares several and every clause must appear in the file.
- `forbidden clause`: a non-empty literal declared in the optional `must_not_contain` (string or list); any hit blocks the outcome.
- `named-clause evidence`: the blocked result's evidence text for a predecessor that names each missing required clause and each present forbidden clause, instead of only the file path.

## Why

The retained predecessor check verifies an artifact outcome by the presence of one substring. A document can satisfy it with an unrelated keyword or a contradictory legacy clause while the real contract wording is absent, and a blocked result names only the file path. A 2026-10-08 execution run first refused a correct document update and then passed it after a keyword sentence was added (origin Evidence); the verdict must bind to declared clauses, not keyword luck.

## Gist & Examples

TLDR: the predecessor artifact probe checks every declared required clause, rejects declared forbidden clauses, and names the missing or contradictory clause on refusal, so document verification stops passing on keyword luck (code-quality).

Before (today): reproducing the origin against the live mechanism on 2026-10-13, a predecessor declaration with `"contains": "remove"` verifies true against a `docs/guide.md` whose only `remove` hit is an unrelated filler line, while a contradictory legacy sentence ("removal of restrictions is forbidden here") sits in the same file; when the real clause is absent, the blocked evidence reads "outcomes tried: artifact docs/guide.md" and names no clause.

After (this plan): the same outcome declares `"contains": ["staged-doc restrictions were lifted for the guide"]` and `"must_not_contain": "removal of restrictions is forbidden here"`; a file missing a required clause is blocked with that clause named; a file carrying the forbidden legacy clause is blocked naming it; a semantically complete updated document verifies. Single-string `contains` keeps today's reading (one required clause), so existing declarations behave unchanged.

Edge cases: an empty `contains` list or a list with a non-string member is a malformed declaration (same structured blocked envelope, the evidence naming the malformed field); a wrong-typed `must_not_contain` is malformed; a file that cannot be read stays unverified as today; the `history-ref`, `ancestry`, and `validator` outcome kinds are untouched.

## Outcome

The retained predecessor artifact probe verifies declared document contract clauses instead of keyword presence.

- A declaration can require several clauses (all must appear) and forbid legacy clauses (none may appear).
- A blocked artifact result names each missing required clause and each present forbidden clause.
- Single-string declarations, the CLI result envelope, and the other outcome kinds behave exactly as today.

Gate delta: adds no gate, refusal class, fence, protocol layer, or schema-mandatory field. The artifact outcome's checked-condition set grows (the `contains` list form and the optional `must_not_contain` arm) and its blocked evidence grows clause names; priced by the origin's witnessed false pass: the 2026-10-08 probe first refused a correct update, then passed on an added keyword sentence (docs/history/backlog/2026-10-08-execute-plan-document-probes-check-only-keyword.md, Evidence section). Nothing is removed; the CLI envelope (status, reason_code, action_scope, checkpoint_identity, next_action, resume_allowed) is unchanged.

## Assumptions

- assume the plan's scope is the predecessor artifact probe: the origin's two named probes (`discover-task-3-doc-0` and `discover-task-3-doc-1`) and their per-run producer no longer exist after the 2026-10-11 sequential adapter removal (a repo grep for `discover-task` producers returns nothing; the origin's cited docs/tmp run artifact is gone; `scripts/execute_plan_runtime.py` is now the retained manifest-free helper module per its own docstring); the artifact arm is the surviving probe of the same class; basis: repository state read 2026-10-13.
- assume the origin's declared Class (verification-contract gap) carries fix-class substance: the body records a false-positive-accepting probe and a refusal that cannot name its reason, so the arms remove the false positive and repair the refusal evidence; the naming disagreement is recorded, the body substance governs the arm shapes; basis: the origin's Problem and Evidence sections.
- assume the driving force: the origin declares reliability, which is outside the closed taxonomy; declared here as code-quality; basis: the closed taxonomy in the plans skill.
- assume backward compatibility: single-string `contains` keeps today's semantics (one required clause); no active plan in the plans root carries a `Predecessors:` block, and the three plans that do are completed archive records whose single-string declarations read identically under the unchanged string form (recursive grep over the plans root at authoring: only docs/history/plans/completed/2026-09-11-execute-plan-runtime-guardrails.md, 2026-09-13-budget-gate-quota-fixes.md, and 2026-09-14-budget-gate-family-residuals.md); basis: repository grep 2026-10-13.
- assume list-form `contains` means conjunction and `must_not_contain` means absence: the narrowest durable predicates expressible in the existing JSON declaration format; basis: the dispatch entry's Prompt (narrowest durable predicate; no literal wording that only one valid phrasing can satisfy).

Decision points requiring a grill: none remain.

## Standing constraints

- Plan scripts and validators run under python3; all commands stay repo-relative with no machine-specific absolute paths, and committed text carries no em dashes.
- The pins suite is load-bearing for execute-plan SKILL.md spans and currently exits 1 with the 21 recorded baseline failures (docs/history/backlog/2026-10-12-pins-suite-main-baseline-21-failures.md); no task may add a new failing pin description; the Validation block's subset guard is the regression fence, not a repair duty.
- Git history is immutable: no task rewrites or amends commits; plan bytes after review move only through the classifier-gated fold path.
- Driver tests follow the repository python conventions in projects/.ai-playbook/python_guidelines.md (silent-failure patterns; no bare except).

## Evaluation Criteria

**Quality dimensions:**
- correctness: every declared required clause is checked in both declaration forms and every forbidden clause is enforced; the driver tests cover absent clause, forbidden hit, unrelated keyword, valid updated text, and both malformed shapes.
- auditability: every blocked artifact outcome names the missing required clause or the present forbidden clause, never only the path.
- compatibility: single-string `contains`, the CLI result envelope, and the `history-ref`, `ancestry`, and `validator` outcome kinds behave as today; the suite proves the single-string arm and the envelope fields.

**Done when:**
- `scripts/test_execute_plan_precondition_cli.py` passes with the new contract tests for both declaration forms, both refusal-evidence duties, and the unchanged envelope.
- the Validation block's live CLI smoke verifies a valid updated document and blocks an absent-clause document and a forbidden-clause document with named evidence.
- `agents/skills/execute-plan/SKILL.md` Step 0.6 documents the clause fields, the conjunction reading, and the named-evidence behavior.
- the pins failing-description set after the change is a subset of the recorded 21-line baseline.

**Ship when:**
- consumer projects running the shared skills checkout pick up the tightened probe at their next vendored sync; no external release action is owned by this plan.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/execute_plan_runtime.py`

**Tests:**
- `scripts/test_execute_plan_precondition_cli.py`

**Documentation:**
- `agents/skills/execute-plan/SKILL.md` (Step 0.6 paragraph only; the rest of the file is frozen: reject any finding touching other spans)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/runtime_capabilities.py`; reason: its checklist-echo guard owns the removed worker-manifest `verification_commands` schema, a different surface this plan does not touch.
- `scripts/done_sweep_gates_lib.py`; reason: the done sweep's closeout gates are a disjoint surface.
- `scripts/check_maintenance_pins.sh` pin expectations; reason: the pins are the compatibility surface this plan keeps green, not a surface to retune.

## Validation Commands

The pins suite baseline below was recorded at authoring time (2026-10-13, worktree base e327d2d4f): the suite exits 1 printing exactly these 21 failing descriptions; the guard fails on any description not in the baseline and treats rc 2 or higher as a tool error (a later upstream fix that shrinks the set passes the subset check by design).

RED-today record (rule 19, executed pre-implementation against the base tree on 2026-10-13): the block was run as extracted bytes (`bash -n` clean) and aborted fail-closed at its FIRST failing gate, gate 2a, block rc 1: the new-style declaration (list `contains` plus `must_not_contain`) is malformed-today and cannot verify. The remaining gates were probed individually and observed: gate 1 vacuous-green (the suite runs only the pre-existing malformed-file test today); gate 2b fails (blocked evidence says only "malformed declaration", the missing clause is not named); gate 2c fails (the field is ignored, status success); gate 2d green (single-string `remove` verifies, the regression pin holds in both worlds); gate 2e vacuous-green (an empty list is malformed-today for the wrong reason, green for the right one after); all three Step 0.6 span gates fail (spans absent); the pins subset guard green (rc 1, 21 failing descriptions, all in the baseline); the hygiene scan green; gate 6 vacuous on the empty base range with the firing proof executed in a scratch repository (an added em-dash line, rc 1 naming the file and line).

Export `PLAN_BASE=<merge-base of the execution branch with main>` before running the block; the em-dash gate is never run argless (argless prints usage and exits 0 scanning nothing).

```bash
set -u
repo="$(git rev-parse --show-toplevel)" || exit 1
cd "$repo" || exit 1
fail() { echo "VALIDATION FAIL: $*" >&2; exit 1; }

# 1. Focused CLI contract suite (owner: Tasks 1-2)
python3 scripts/test_execute_plan_precondition_cli.py >/dev/null 2>&1 || fail "focused precondition CLI suite"

# 2. Live CLI smoke over a scratch fixture (created under mktemp, torn down on exit)
SMOKE="$(mktemp -d)" || fail "mktemp"
trap 'rm -rf "$SMOKE"' EXIT
mkdir -p "$SMOKE/repo/docs" || fail "fixture dirs"
printf 'legacy: removal of restrictions is forbidden here\nfiller line mentioning remove\nv2: staged-doc restrictions were lifted for the guide\n' > "$SMOKE/repo/docs/guide.md" || fail "fixture file"

# 2a fixture: the valid updated document (the legacy forbidden clause is gone; the shared guide.md keeps it for gates 2b-2d)
printf 'filler line mentioning remove\nv2: staged-doc restrictions were lifted for the guide\n' > "$SMOKE/repo/docs/guide-v2.md" || fail "valid fixture file"
# 2a. valid updated text: required clause present, forbidden clause absent, envelope unchanged
cat > "$SMOKE/valid.json" <<'EOF'
{"predecessors":[{"ref":"guide","outcomes":[{"kind":"artifact","path":"docs/guide-v2.md","contains":["staged-doc restrictions were lifted for the guide"],"must_not_contain":"removal of restrictions is forbidden here"}]}]}
EOF
python3 scripts/execute_plan_runtime.py --operation precondition --predecessors-file "$SMOKE/valid.json" --repo-root "$SMOKE/repo" > "$SMOKE/valid.out.json" || fail "valid-text smoke run"
python3 - "$SMOKE/valid.out.json" <<'EOF' || fail "valid-text smoke verdict"
import json, sys
r = json.load(open(sys.argv[1]))
p = r["predecessors"][0]
assert r["status"] == "success", r
assert r["action_scope"] == "repository-read", r
assert r["checkpoint_identity"] == "precondition:verify", r
assert p["verified"] is True and p["verified_by"]["kind"] == "artifact", p
EOF

# 2b. absent required clause: blocked, the missing clause named, the present clause and the unrelated keyword not credited
cat > "$SMOKE/absent.json" <<'EOF'
{"predecessors":[{"ref":"guide","outcomes":[{"kind":"artifact","path":"docs/guide.md","contains":["staged-doc restrictions were lifted for the guide","no such clause exists anywhere"]}]}]}
EOF
python3 scripts/execute_plan_runtime.py --operation precondition --predecessors-file "$SMOKE/absent.json" --repo-root "$SMOKE/repo" > "$SMOKE/absent.out.json" || fail "absent-clause smoke run"
python3 - "$SMOKE/absent.out.json" <<'EOF' || fail "absent-clause smoke verdict"
import json, sys
r = json.load(open(sys.argv[1]))
assert r["status"] == "blocked" and r["reason_code"] == "precondition-unverified", r
joined = " ".join(r["evidence"])
assert "no such clause exists anywhere" in joined, r["evidence"]
assert "staged-doc restrictions were lifted" not in joined, r["evidence"]
EOF

# 2c. forbidden clause present: blocked, the contradictory clause named
cat > "$SMOKE/forbidden.json" <<'EOF'
{"predecessors":[{"ref":"guide","outcomes":[{"kind":"artifact","path":"docs/guide.md","contains":"staged-doc restrictions were lifted for the guide","must_not_contain":["removal of restrictions is forbidden here"]}]}]}
EOF
python3 scripts/execute_plan_runtime.py --operation precondition --predecessors-file "$SMOKE/forbidden.json" --repo-root "$SMOKE/repo" > "$SMOKE/forbidden.out.json" || fail "forbidden-clause smoke run"
python3 - "$SMOKE/forbidden.out.json" <<'EOF' || fail "forbidden-clause smoke verdict"
import json, sys
r = json.load(open(sys.argv[1]))
assert r["status"] == "blocked", r
assert "removal of restrictions is forbidden here" in " ".join(r["evidence"]), r["evidence"]
assert r["predecessors"][0]["verified"] is False, r
EOF

# 2d. single-string contains keeps today's reading: one required clause, present verifies (regression pin)
cat > "$SMOKE/compat.json" <<'EOF'
{"predecessors":[{"ref":"guide","outcomes":[{"kind":"artifact","path":"docs/guide.md","contains":"remove"}]}]}
EOF
python3 scripts/execute_plan_runtime.py --operation precondition --predecessors-file "$SMOKE/compat.json" --repo-root "$SMOKE/repo" > "$SMOKE/compat.out.json" || fail "compat smoke run"
python3 - "$SMOKE/compat.out.json" <<'EOF' || fail "compat smoke verdict"
import json, sys
r = json.load(open(sys.argv[1]))
assert r["predecessors"][0]["verified"] is True, r
EOF

# 2e. malformed list form: empty contains list is a malformed declaration in the structured blocked envelope
cat > "$SMOKE/malformed.json" <<'EOF'
{"predecessors":[{"ref":"guide","outcomes":[{"kind":"artifact","path":"docs/guide.md","contains":[]}]}]}
EOF
python3 scripts/execute_plan_runtime.py --operation precondition --predecessors-file "$SMOKE/malformed.json" --repo-root "$SMOKE/repo" > "$SMOKE/malformed.out.json" || fail "malformed smoke run"
python3 - "$SMOKE/malformed.out.json" <<'EOF' || fail "malformed smoke verdict"
import json, sys
r = json.load(open(sys.argv[1]))
assert r["status"] == "blocked" and r["reason_code"] == "precondition-unverified", r
assert "malformed" in " ".join(r["evidence"]).lower(), r["evidence"]
EOF

# 3. Step 0.6 documents the clause contract (wrap-tolerant presence pins over the flattened file)
FLAT="$(tr '\n' ' ' < agents/skills/execute-plan/SKILL.md | tr -s ' ')"
case "$FLAT" in *"must_not_contain"*) ;; *) fail "Step 0.6 does not document the forbidden-clause field";; esac
case "$FLAT" in *"every clause must appear"*) ;; *) fail "Step 0.6 does not document the required-clause conjunction";; esac
case "$FLAT" in *"names the missing or contradictory clause"*) ;; *) fail "Step 0.6 does not document named evidence";; esac

# 4. Pins regression subset guard (baseline recorded 2026-10-13 at e327d2d4f)
PINS_OUT="$(bash scripts/check_maintenance_pins.sh 2>&1)"; PINS_RC=$?
[ "$PINS_RC" -le 1 ] || fail "pins suite tool error (rc $PINS_RC)"
CURRENT_PINS="$(printf '%s\n' "$PINS_OUT" | grep '^PIN FAIL' | sed 's/^PIN FAIL: //' | sort -u)"
BASELINE_PINS="$(cat <<'PIN_BASELINE'
resume-fit --fire-at check at resume-scheduling boundaries
resume-pricing defers to the reported defer_to
preservation: canonical lineage-cap branch span count 0 != 1
preservation: Resume carrier fallback ordering heading span count 0 != 1
preservation: OffPeakCreate pause rung span count 0 != 1
preservation: launchd wired mark span count 0 != 1
preservation: OffPeakCreate prompt contract span count 0 != 1
preservation: canonical carrier-aware record span count 0 != 1
rate-limited end resolves its open claim
claim-less end derives from stop lines
post-backoff success writes a recovery marker
state table derives the claim-less case
contract mirrors the claim boundary
contract derives the claim-less case from stop lines
resume backoff carries a floor
serialized cap doubles the intermediate-panel bound
serialized cap doubles the Step 3.1 bound
serialized cap doubles the omnibus bound
stop line token format pinned
dispatch_failed record literal
dispatch_failed tracking-list entry head
PIN_BASELINE
)"
NEW_FAILS="$(comm -23 <(printf '%s\n' "$CURRENT_PINS" | sort -u) <(printf '%s\n' "$BASELINE_PINS" | sort -u))"
[ -z "$NEW_FAILS" ] || { echo "NEW PIN FAILURES:" >&2; printf '%s\n' "$NEW_FAILS" >&2; fail "pins regression: new failing descriptions"; }
echo "pins subset guard: no new failing descriptions"

# 5. Public hygiene scan (anchored to the repo root)
( cd "$repo" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" >/dev/null 2>&1 ) || fail "public hygiene scan"

# 6. Em-dash residue over the landing range (never argless; PLAN_BASE exported by the caller)
bash scripts/check-no-em-dash.sh added-lines --base "$PLAN_BASE" >/dev/null 2>&1 || fail "em-dash residue in added lines"

echo "VALIDATION: all gates green"
```

### Task 1: required-clause conjunction with named evidence

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_precondition_cli.py`

Primary class anchors:
- `verify_preconditions` in `scripts/execute_plan_runtime.py`

- [x] the artifact outcome accepts `contains` as one clause string or a non-empty list of clause strings; the list form verifies only when every declared clause appears in the file [class: IMPLEMENTATION_REQUIRED]
- [x] given `contains: []`, a list carrying a non-string member, or an empty-string clause, the outcome is a malformed declaration in the structured blocked envelope, its evidence naming the malformed field (today's empty-string refusal shape preserved) [class: IMPLEMENTATION_REQUIRED]
- [x] a blocked artifact outcome names each missing required clause in the predecessor's evidence, and a present clause is never named as missing [class: IMPLEMENTATION_REQUIRED]
- [x] given a file whose only keyword hits are an unrelated filler line and a contradictory legacy clause, a declaration whose required clause enumerates the real contract wording is blocked with that clause named, the unrelated keyword satisfying nothing [class: IMPLEMENTATION_REQUIRED]
- [x] the single-string `contains` form keeps today's reading (one required clause; present verifies, absent blocks), proven by a test expected green before and after the change [class: REPOSITORY_TEST]
- [x] Run → expect RED: this task's new contract tests fail against today's single-literal arm (a list form is malformed-today, and blocked evidence names no clause), while the pre-existing malformed-file CLI test stays green [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the focused suite passes with this task's tests in and no Task 2 tests yet written [class: REPOSITORY_TEST]
- [x] Commit: `feat: predecessor artifact probe verifies every declared required clause` [class: IMPLEMENTATION_REQUIRED]

### Task 2: forbidden-clause arm with named evidence

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `scripts/execute_plan_runtime.py`
- `scripts/test_execute_plan_precondition_cli.py`

Primary class anchors:
- `verify_preconditions` in `scripts/execute_plan_runtime.py`

- [x] the artifact outcome accepts the optional `must_not_contain` as one clause string or a list; any forbidden clause present in the file blocks the outcome even when every required clause is present [class: IMPLEMENTATION_REQUIRED]
- [x] a predecessor blocked by a forbidden clause reads `verified: false` with `verified_by: null` in the per-predecessor record, even when every required clause matched [class: IMPLEMENTATION_REQUIRED]
- [x] a blocked-by-forbidden outcome names the present forbidden clause in the predecessor's evidence [class: IMPLEMENTATION_REQUIRED]
- [x] a `must_not_contain` of a wrong type, an empty string, or a list carrying a non-string member is a malformed declaration; the field's absence keeps today's shape [class: IMPLEMENTATION_REQUIRED]
- [x] driver tests (written failing first): forbidden clause present blocks naming it with the per-predecessor record reading verified false; forbidden clause absent with required clauses present verifies; a clean file with no forbidden hit verifies [class: REPOSITORY_TEST]
- [x] Run → expect RED: the forbidden-arm tests fail today (the field is ignored), while Task 1's tests stay green [class: REPOSITORY_TEST]
- [x] Write minimal implementation [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the focused suite passes with both tasks' tests in [class: REPOSITORY_TEST]
- [x] Commit: `feat: predecessor artifact probe rejects declared forbidden clauses` [class: IMPLEMENTATION_REQUIRED]

### Task 3: document the probe contract at its single home

Context surface: the plan's Terms, this task, and `## Standing constraints`; referenced, never restated.

Files:
- `agents/skills/execute-plan/SKILL.md`

- [x] Step 0.6's paragraph documents the artifact outcome fields: `contains` as one required clause or a list where every clause must appear, the optional `must_not_contain` clauses that must not appear, and that a blocked result names the missing or contradictory clause [class: IMPLEMENTATION_REQUIRED]
- [x] the same paragraph carries the narrowest-predicate guidance: prefer several specific required clauses over one broad keyword [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect the three Step 0.6 span gates in Validation Commands section 3 green, with the pins subset guard unchanged [class: REPOSITORY_TEST]
- [x] Commit: `docs: document the predecessor artifact clause contract in Step 0.6` [class: IMPLEMENTATION_REQUIRED]

### Task 4: validation pass

Context surface: the plan's `## Validation Commands` and `## Standing constraints`; referenced, never restated.

- [x] run the whole Validation Commands block with `PLAN_BASE` exported; expect every gate green with the pins subset guard reporting no new failing descriptions against the recorded baseline [class: REPOSITORY_TEST]

Evidence: the Validation block's own final `VALIDATION: all gates green` line, the pins subset guard line, and the focused suite's pass count recorded in the run log.
