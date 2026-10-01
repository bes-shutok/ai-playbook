# Plan: Verify tracker and linked-contract sources before planning

Backlog origin: docs/history/backlog/2026-10-01-plans-verify-ticket-and-linked-contract-sources.md
Driving force: external (consumer-feedback origin above; the item's Consumer urgency line is the implementation justification: a company project consumed the shared planning skill and absorbed avoidable scope and estimate rework because the authoritative sources went unread)
Plan review record: the staging series docs/reviews/2026-10-01-plan-review-plans-tracker-source-reconciliation-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

The planning workflow's requirements discovery reconciles, for a tracker-linked request, the tracker issue's live fields and every named linked contract before any scope, dependency, estimate, or MVP/post-MVP recommendation, and the discovery record proves which sources were read.

- A tracker-linked request can no longer draft scope from conversational context or repository documents while the issue's acceptance criteria, estimate, status, parent, and linked issues go unread; the recommendation-ordering failure the origin witnessed is closed at the same step where it happened.
- For tracker-linked requests, named cross-service DTO, API, or interface expectations are read in their owning repository or canonical design page before the plan decides what to expose, so external contract facts stop entering plans as assumptions.
- The Step 1.4 confirmation block renders a Sources inspected record on every run (each authoritative source with its read state, or why an unavailable source could not be read), and the durable copy rides the plan's Assumptions, so review and later phases can verify the reconciliation instead of trusting it.
- Adjacent-issue and existing-mechanism ownership is checked before the plan proposes any new task or recovery path, closing the duplicate-mechanism failure the origin witnessed.

Gate delta: four additions, no removals, no simplifications, no script gates. Each addition's payment is its cited completed-integrity-failure witness; the named precedent arms show the same mechanism family already exists, they are not themselves the payment (none of them is deleted or simplified by this plan). (1) Phase 1 Step 1.1 gains the tracker-source reconciliation duty, a grown checked-condition set on requirements discovery; precedent arm: the Third-party AI-conversation sources arm one paragraph above it (same Phase 1 source-ordering family, same requirements-buffer record channel); paying witness: the origin's recorded consumer failure (required API treated as optional, MVP misjudged, duplicate recovery path proposed, repeated user corrections). (2) Step 1.2 gains confirm-element 7 and the Step 1.4 confirmation block gains the always-render Sources inspected line, a new record channel; precedent arm: the Scope extensions always-render block in the same confirmation block (same mechanism family, same always-render and detectable-violation wording); paying witness: the same origin failure. (3) The plans Assumptions rules bullet gains the durable sources bullet duty for tracker-linked plans; precedent arm: the existing assumptions-with-basis bullet channel (same section, same shape); paying witness: the same origin failure. (4) review-plan Step 1 gains the tracker-source audit (item 9), a review-layer duty declared on this line separately; it raises ordinary (non-blocking) findings only, so it is not a counted addition under review-plan's review-layer rule; precedent arm: item 7's unresolved decision-point audit (same Step 1 pre-flight audit family, same correctness-completeness finding class); paying witness: the same origin failure. No script gate is added and none is needed for the origin's regression demand: the confirmation block is requirements discovery's pass/fail boundary ("Wait for explicit confirmation before proceeding"), the always-render Sources inspected line makes that boundary unable to complete without the record, and a plan_readiness check keyed on the audit's own trigger surfaces (a tracker reference in header, backlog origin, tasks, or filename stem) would run unexercised on a corpus where no plan carries a ticket-reference header line while false-positive-prone on reference-shaped tokens the corpus legitimately carries (ADR cross-references, quoted example keys); the measurement behind that claim is recorded in the Validation preamble, and the prose confirmation boundary stays the regression case of record.

## Terms

- **Tracker-linked request**: a plan request that names a tracker issue (Jira or an equivalent issue tracker) or otherwise carries a ticket reference for the work being planned. A plan produced from a tracker-linked request is a tracker-linked plan; the review-plan audit recognizes it by a tracker-issue reference in the header, backlog origin, tasks, or story-key filename stem, with the reference shape insertion (f) defines.
- **Authoritative source**: the live tracker issue fields, every named linked contract, and, for a tracker-linked request, the repository RFC or TDD once read; conversational context and other repository documents are secondary until reconciled against them.
- **Linked contract**: a cross-service DTO, API, or interface expectation named by the request or by the named tracker issue or a linked issue, owned in another repository or a canonical design page.
- **Sources inspected record**: the confirmation-block line naming each authoritative source with its read state, or why an unavailable source could not be read; it renders in the Step 1.4 confirmation as the Sources inspected block, and its durable copy rides the plan's Assumptions.
- **Requirements buffer**: the existing `{tmp_dir}/plan-requirements-<slug>.md` notes file Phase 1 already writes; it gains the Step 1.1 source-reconciliation record (conflicts, current ownership, and estimate implications).

## Assumptions

- assume the duty lands as skill prose in exactly two files with no new script gate; basis: the corpus measurement in the Gate delta (zero plans carry a header ticket reference, so no byte-level trigger exists), the confirmation block already being requirements discovery's pass/fail boundary, and the machinery cost-benefit adjudication of 2026-09-28 (short gate list; blockers cost real work).
- assume tracker tooling stays generic in the skill bytes ("a tracker issue", Jira named only as an example); basis: the repository guideline forbidding org-specific ticket prefixes and team identifiers in skill files.
- assume the review-plan audit lives in the Step 1 pre-flight list rather than a worker lens; basis: items 7 and 8 set the precedent that plan-structure audits are Step 1 pre-flight items with a named finding class and owner worker.
- assume the Step 1.4 meta-rule's always-render enumeration stays at its two named blocks (Scope extensions, Decision points) and the Sources inspected always-render obligation is declared in Step 1.2 element 7 rather than in the meta-rule comment; basis: the meta-rule comment carries the grilling sync-note's protected clause families, the element 7 declaration mirrors element 6's own always-render sentence (which likewise restates outside the meta-rule), and no witness requires extending the sync-bound surface.
- assume the consuming project's own corrected plan needs no fix in this repository; basis: the origin's Why-not-fixed-now section.
- assume the Step 1.4 grilling sync note is not triggered; basis: the note binds the generic-acknowledgement, lifecycle-verb, answer-state, and opt-in-phrase rule families, none of which this plan touches (the Sources inspected addition is a new always-render record, not an acknowledgement rule).

Decision points requiring a grill: none remain.

## Gist & Examples

TLDR: requirements discovery must read the tracker issue's live fields and every named linked contract before recommending scope or estimates, and record which sources it read, closing a witnessed consumer rework failure (external force).

A tracker-backed plan was drafted from conversational context and repository documents: a required API was treated as optional, MVP membership was misjudged, and a duplicate recovery path was proposed next to an existing job mechanism. The user had to supply the tracker issue and a linked Platform DTO to settle all three facts, causing avoidable scope and estimate rework. After this change, the same request reads the issue's description, acceptance criteria, estimate, status, and parent, plus every linked issue and named contract, before any recommendation; conflicts with the repository RFC are recorded in the requirements buffer; unresolved alternatives route to the grill instead of into assumptions. The Step 1.4 confirmation then renders one Sources inspected line, for example `Sources inspected: <issue key> fields (read live), <linked DTO path> in its owning repository (read), repository TDD (read, one conflict recorded)` or, when a source cannot be read, `Sources inspected: <linked design page> unavailable: access denied, decision on the contract shape grilled instead`. The durable copy of that line rides the plan's Assumptions so reviewers can check the reconciliation.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every prescribed insertion lands at its prescribed anchor with its named tail surviving, and every pin in the Validation block passes at exactly-once (or exactly-twice where stated) counts, verified by the fail-closed block exiting zero.
- maintainability: the duty rides existing mechanisms (requirements buffer, confirmation block, Assumptions bullets, Integration Points) with zero new gates or scripts; the shared-body neutrality and ContractContentParity probes and the em-dash added-lines gate stay green, and the root-instruction-files instruction-size background gate stays green (the skill bodies are not in its default file set, so it is a background signal, not this plan's size proof).
- reviewability: the review-plan audit names its trigger, its required evidence, its finding class, and its vacuous-pass boundary, so a reviewer can apply it without re-deriving the duty.

**Done when:**
- Both skill files carry the prescribed insertions; both Integration Points sections carry the bidirectional entries; the full Validation Commands block exits zero end to end.
- `bash scripts/check_maintenance_pins.sh` exits zero, except the tolerated runtime-state pin class (validation check 5 records it): no external pin literal or count over either file moved.
- The pre-round structural readiness invocation passes on this plan's own bytes.

**Ship when:**
- Consuming company projects pick up the revised shared skill on their next vendored sync; no deployed condition is owned by this repository.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/plans/SKILL.md`
- `agents/skills/review-plan/SKILL.md`

**Tests:** no test bytes change; the suites listed under Validation Commands run unmodified.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason. Landing-time note: after any rebase onto a moved base branch, re-run the complete Validation Commands block on the rebased tree before landing; peers actively land plan-driven insertions into both target files, and the span pins and ordered chains are exactly the assertions such a landing would silently invalidate on the base while this worktree stays green.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: the Gate delta records why no script gate is added, and this plan changes no readiness-enforced plan element.
- `agents/skills/execute-plan/SKILL.md` and `agents/skills/execute-plan/runtime-contract.md`; reason: frozen; the ContractContentParity probes read them and no runtime obligation changes.
- `agents/skills/grilling/` and `agents/skills/grill-with-docs/`; reason: the Step 1.4 sync note binds only the acknowledgement rule families, which this plan does not touch.
- `agents/skills/review-agents/`; reason: untouched, so the portability and doors checks are not triggered.

## Validation Commands

Authoring-time records: (1) Rule 19 RED-today evidence: every span pinned below was grepped against the base tree at authoring time and returned zero matches in both files ("Tracker and linked-contract sources", "Sources inspected", "Tracker-source audit" all absent), so the presence pins are RED now and flip GREEN exactly when Tasks 1 and 2 land. (2) Rule 22 mechanical audit plus rule 44 extraction proof: the block passed `bash -n`; all seven insertion blocks were then extracted mechanically from this plan's own fenced task blocks, applied at their anchors to a scratch clone of the base tree, and the ENTIRE Validation block was executed end to end against that tree: exit 0, final line `validation: all checks passed` (spans at exact counts, ordered chains green, parity and neutrality probes 21 passed, instruction-size exit 0 on its root-instruction-files default set, em-dash added-lines clean). A flip probe stripping insertion (b) made the block abort with `PIN FAIL (0 != 1)` on the first check, proving the gates fail closed. The full-block run and the flip probe are re-executed on the folded bytes after every fold. (3) Rule 29 pre-round gates, re-executed on the folded bytes: `bash scripts/check-no-em-dash.sh touched` exit 0 (plan bytes are the authoring-time touched set), the public-hygiene scan PASS, and `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-01-plans-tracker-source-reconciliation.md` clean (one tolerated iteration fixed before round 1: the two Task commit checklist lines lacked classification tags, the same validator gotcha prior plans hit); the staging series below is created at round 1 close and these inline outcomes are the interim re-runnable evidence; any structural failure blocks round 1. (4) Baseline gates green on the base tree: the shared-body neutrality and ContractContentParity probes pass, the instruction-size gate exits zero, and `bash scripts/check_maintenance_pins.sh` fails on the untouched base tree only with the prompt-log all-served runtime-state pin (live peer-loop state, the exact tolerance class check 5 records), which is why check 5 tolerates exactly that message and still exits non-zero on any other PIN FAIL. Both test interpreters (`~/.agents/venvs/ai-playbook-test/bin/python` and `~/.ai-playbook/venvs/ai-playbook-test/bin/python3`) carry pytest 9.1.1, so the check 6 TEST_PY resolution is satisfied either way. (5) Corpus measurement behind the no-script-gate claim, re-runnable: `for f in docs/history/plans/*.md docs/history/plans/completed/*.md; do sed -n '2,6p' "$f" | grep -icE 'jira|ticket|crm-[0-9]|rfc|prd'; done` over the 270-file corpus matches 7 files including this plan (6 besides), and none is a tracker reference line: two completed plans assert the negation "No RFC/ticket" in prose, and the rest match on backlog filenames, an incident narrative, a review-record path, and backlog-origin paths; a second sweep for issue-key-shaped tokens (`grep -rnE '\b[A-Z]{2,8}-[0-9]+\b'`) over the same corpus returns SHA-256 digest literals, ADR and lesson cross-reference tokens (ADR-0001, CRG-017), per-finding review ids, quoted example ticket keys, and encoding and timezone labels; none is a header ticket-reference line. Zero plans carry the header ticket reference line a plan_readiness check would key on.

```bash
# Executor note: run from the repository root. Presence pins are RED on the
# base tree and flip GREEN exactly when Tasks 1-2 land. Every check aborts
# non-zero on miss; no count or order check relies on bare exit status
# alone, while checks 6 through 8 are real gates whose exit status is their
# contract.
set -u
P=agents/skills/plans/SKILL.md
RP=agents/skills/review-plan/SKILL.md
[ -f "$P" ] || { echo "missing $P"; exit 1; }
[ -f "$RP" ] || { echo "missing $RP"; exit 1; }

# 1) Task 1 spans: each exactly once in plans SKILL.md.
while IFS= read -r span; do
  [ -n "$span" ] || continue
  n="$(grep -oF -- "$span" "$P" | wc -l | tr -d ' ')"
  [ "$n" -eq 1 ] || { echo "PIN FAIL ($n != 1): $span"; exit 1; }
done <<'SPANS'
Tracker and linked-contract sources (tracker-linked requests)
Conversational context and other repository documents are secondary for tracker-linked requests
7. **Sources inspected (tracker-linked requests):**
**Sources inspected:** <source>: <read (what was read and when), or unavailable: why>
A tracker-linked plan also carries the confirmation block's Sources inspected record
Plan review's Step 1 tracker-source audit consumes the Sources inspected record
SPANS

# 2) The always-render literal is defined twice by design (item 7 and the
# block line): exactly two occurrences, one deletion or stray copy fails.
n="$(grep -oF -- 'Sources inspected: not a tracker-linked request.' "$P" | wc -l | tr -d ' ')"
[ "$n" -eq 2 ] || { echo "PIN FAIL ($n != 2): always-render literal"; exit 1; }

# 3) Task 2 spans: each exactly once in review-plan SKILL.md.
while IFS= read -r span; do
  [ -n "$span" ] || continue
  n="$(grep -oF -- "$span" "$RP" | wc -l | tr -d ' ')"
  [ "$n" -eq 1 ] || { echo "PIN FAIL ($n != 1): $span"; exit 1; }
done <<'SPANS'
9. **Tracker-source audit**:
a plan whose header, backlog origin, tasks, or story-key filename stem reference a tracker issue
A plan with no tracker reference passes vacuously
Plan review's Step 1 tracker-source audit (item 9) consumes the Sources inspected record
SPANS

# 4) Ordered placement, full chain (rule 8). Step 1.1 block sits after the
# Third-party paragraph and before Step 1.2; item 7 after item 6; the block
# line after the Scope extensions line and before the meta-rule comment;
# the Assumptions sentence after the rules bullet's trailer tail.
# Stage note: at the Task 1 boundary the two review-plan-side chains
# (anchors m/n2/s and o/p/t) fail by design until Task 2 lands; the Task 1
# pass condition is checks 1, 2, and the plans-side chains (a..l with r).
a="$(grep -nF 'already collected.)' "$P" | head -1 | cut -d: -f1)"
b="$(grep -nF 'Tracker and linked-contract sources (tracker-linked requests)' "$P" | head -1 | cut -d: -f1)"
c="$(grep -nF '### Step 1.2: Verify key decisions explicitly' "$P" | head -1 | cut -d: -f1)"
[ -n "$a" ] && [ -n "$b" ] && [ -n "$c" ] || { echo "anchor miss: Step 1.1 chain"; exit 1; }
[ "$a" -lt "$b" ] && [ "$b" -lt "$c" ] || { echo "ORDER FAIL: Step 1.1 block placement"; exit 1; }
d="$(grep -nF '6. **Scope extensions:**' "$P" | head -1 | cut -d: -f1)"
e="$(grep -nF '7. **Sources inspected (tracker-linked requests):**' "$P" | head -1 | cut -d: -f1)"
q="$(grep -nF '**Example confirmation questions:**' "$P" | head -1 | cut -d: -f1)"
[ -n "$d" ] && [ -n "$e" ] && [ -n "$q" ] || { echo "anchor miss: Step 1.2 item 7"; exit 1; }
[ "$d" -lt "$e" ] && [ "$e" -lt "$q" ] || { echo "ORDER FAIL: item 7 placement"; exit 1; }
f="$(grep -nF '**Sources inspected:** <source>:' "$P" | head -1 | cut -d: -f1)"
g="$(grep -nF '<!-- Meta-rule for the authoring agent' "$P" | head -1 | cut -d: -f1)"
h="$(grep -nF '**Scope extensions (grilled):**' "$P" | head -1 | cut -d: -f1)"
[ -n "$f" ] && [ -n "$g" ] && [ -n "$h" ] || { echo "anchor miss: Step 1.4 block line"; exit 1; }
[ "$h" -lt "$f" ] && [ "$f" -lt "$g" ] || { echo "ORDER FAIL: block line between Scope extensions and meta-rule"; exit 1; }
# (d) shares its line with the rules bullet (an appended sentence), so the
# order assertion is character-order inside the matched line, not line order.
assump_line="$(grep -F 'for the exact date and exemption semantics)' "$P" | head -1)"
[ -n "$assump_line" ] || { echo "anchor miss: Assumptions rules bullet"; exit 1; }
case "$assump_line" in
  *"exemption semantics). A tracker-linked plan also carries the confirmation block's Sources inspected record"*) : ;;
  *) echo "ORDER FAIL: Assumptions sentence placement"; exit 1 ;;
esac
k="$(grep -nF "owned by receiving-review's Backlog capture." "$P" | head -1 | cut -d: -f1)"
l="$(grep -nF "Plan review's Step 1 tracker-source audit consumes the Sources inspected record" "$P" | head -1 | cut -d: -f1)"
r="$(grep -nF '### With `grill-with-docs` skill' "$P" | head -1 | cut -d: -f1)"
[ -n "$k" ] && [ -n "$l" ] && [ -n "$r" ] || { echo "anchor miss: plans Integration Points"; exit 1; }
[ "$k" -lt "$l" ] && [ "$l" -lt "$r" ] || { echo "ORDER FAIL: plans Integration Points placement"; exit 1; }
m="$(grep -nF 'like any other required element)' "$RP" | head -1 | cut -d: -f1)"
n2="$(grep -nF '9. **Tracker-source audit**:' "$RP" | head -1 | cut -d: -f1)"
s="$(grep -nF '## Step 2: Launch Workers in Parallel' "$RP" | head -1 | cut -d: -f1)"
[ -n "$m" ] && [ -n "$n2" ] && [ -n "$s" ] || { echo "anchor miss: review-plan item 9"; exit 1; }
[ "$m" -lt "$n2" ] && [ "$n2" -lt "$s" ] || { echo "ORDER FAIL: item 9 placement"; exit 1; }
o="$(grep -nF "receiving-review's Backlog capture)" "$RP" | head -1 | cut -d: -f1)"
p="$(grep -nF "Plan review's Step 1 tracker-source audit (item 9) consumes the Sources inspected record" "$RP" | head -1 | cut -d: -f1)"
t="$(grep -nF '### With the plan readiness gate' "$RP" | head -1 | cut -d: -f1)"
[ -n "$o" ] && [ -n "$p" ] && [ -n "$t" ] || { echo "anchor miss: review-plan Integration Points"; exit 1; }
[ "$o" -lt "$p" ] && [ "$p" -lt "$t" ] || { echo "ORDER FAIL: review-plan Integration Points placement"; exit 1; }

# 5) External pin sweep: the repository's own pin suite must stay green over
# both edited files (guards every check_maintenance_pins.sh literal and
# count over $PL and $RP, including the whole-file 'Driving force: <tag>'
# and 'TLDR: <what changes>' count pins my insertions must not disturb).
# One failure class is tolerated and printed for the record: the prompt-log
# all-served pin reads live peer-loop runtime state, not repository bytes
# (witnessed failing on the untouched base tree on 2026-10-01, the foreign
# peer-loop machine-state class); any other PIN FAIL exits non-zero.
# The tolerance cannot distinguish a stale entry from a crashed checker by
# exit code alone (an unhandled exception also exits 1), so the probe's
# output is classified too: rc 2 or more aborts; on rc 1 the output must
# carry one of the checker's documented verdict lines (SERVED, LIVE, STALE)
# and no traceback, otherwise it aborts like any other pin failure.
probe_out="$(python3 scripts/check_prompt_log_origins.py 2>&1)"
health="$?"
[ "$health" -le 1 ] || { echo "prompt-log checker unhealthy (rc=$health)"; exit 1; }
if [ "$health" -eq 1 ]; then
  case "$probe_out" in
    *Traceback*) echo "prompt-log checker crashed (traceback at rc=1)"; exit 1 ;;
  esac
  case "$probe_out" in
    *SERVED:*|*LIVE:*|*STALE:*) : ;;
    *) echo "prompt-log checker output matches no documented verdict line"; exit 1 ;;
  esac
fi
pins_out="$(bash scripts/check_maintenance_pins.sh 2>&1)" || {
  printf '%s\n' "$pins_out"
  case "$pins_out" in
    *"prompt log has no all-served"*)
      [ "$(printf '%s\n' "$pins_out" | grep -c 'PIN FAIL:')" -eq 1 ] || { echo "maintenance pins FAIL"; exit 1; }
      [ "$(printf '%s\n' "$pins_out" | grep -c '^missing ')" -eq 0 ] || { echo "maintenance pins FAIL"; exit 1; }
      echo "recorded: pre-existing runtime-state pin failure (foreign peer-loop state), not a plan defect" ;;
    *) echo "maintenance pins FAIL"; exit 1 ;;
  esac
}

# 6) Shared-body neutrality and contract-content parity over the edited
# skill bytes; the interpreter resolves the project test venv when present
# and falls back to the system python3 (the repo's established TEST_PY form).
TEST_PY="$(~/.agents/venvs/ai-playbook-test/bin/python -c 'import pytest' 2>/dev/null && echo ~/.agents/venvs/ai-playbook-test/bin/python || command -v python3)"
"$TEST_PY" -m pytest scripts/test_execute_plan_runtime.py -k 'shared_skill_bodies_remain_runtime_neutral or ContractContentParity' -q || { echo "suite FAIL"; exit 1; }

# 7) Instruction-size background gate. Its default file set is the
# repository's root instruction files, not the two skill bodies, so this
# check is a background signal that the gate stays green; it is not this
# plan's size proof for the insertions.
bash "$HOME/.ai-playbook/scripts/check-instruction-size.sh" || { echo "instruction-size FAIL"; exit 1; }

# 8) Em-dash gate scoped to this plan's insertions: added lines against the
# base branch only (both files carry no committed violations, but the
# added-lines scope keeps the gate exact if either file ever gains frozen
# legacy spans). The base is this repository's default branch, which both
# the authoring and execution branches derive from; re-derive the default at
# execution time if it has moved.
bash scripts/check-no-em-dash.sh added-lines --base main -- "$P" "$RP" || { echo "em-dash added-lines FAIL"; exit 1; }

echo "validation: all checks passed"
```

### Task 1: plans SKILL.md tracker-source reconciliation arms

Files:
- `agents/skills/plans/SKILL.md`

Evidence:
- Validation block checks 1, 2, and 4 (plans SKILL.md pins and the ordered chains ending at `plans Integration Points placement`); covers every Task 1 checklist criterion
- `bash scripts/check_maintenance_pins.sh`; covers the no-external-pin-breaks criterion

The five verbatim insertions for this task. Each lands as one paragraph (or one list item) exactly as written; none contains a fenced-block boundary, so a three-backtick copy of any block is the prescribed bytes. Task 2 adds the remaining two, for seven in total.

(a) into Phase 1 Step 1.1, immediately after the paragraph ending `already collected.)` and before the `### Step 1.2: Verify key decisions explicitly` heading; the heading and its position are the named tail and must survive, one blank line on each side of the insertion:

```
**Tracker and linked-contract sources (tracker-linked requests):** when the request names a tracker issue or otherwise carries a ticket reference, read its live description, acceptance criteria, estimate, status, and parent or epic, plus every linked or named related issue, before making any scope, dependency, estimate, or MVP/post-MVP recommendation. For a named cross-service DTO, API, or interface expectation, read the source contract in its owning repository or canonical design page before deciding what the plan must expose or implement. Check whether the proposed work is already owned by an adjacent issue or an existing system mechanism, and do not propose a new task or recovery path until that reconciliation is complete. Reconcile what those sources say against the repository RFC or TDD and record conflicts, current ownership, and estimate implications in the requirements buffer; treat unresolved alternatives as decisions to grill, never as facts to assume. When a source cannot be read, record why beside the Sources inspected record (Step 1.4). Conversational context and other repository documents are secondary for tracker-linked requests until reconciled against the authoritative sources. (Witness: a tracker-backed plan drafted from conversational context treated a required API as optional, misjudged MVP scope, and proposed a duplicate recovery path; the user had to supply the issue and the linked DTO to settle all three.)
```

(b) into Step 1.2's Confirm-these-elements list, immediately after element 6 (the `6. **Scope extensions:**` item):

```
7. **Sources inspected (tracker-linked requests):** each authoritative source for a tracker-linked request (the live issue fields, every named linked contract, the repository RFC or TDD) carries its read state, or why an unavailable source could not be read. The Sources inspected block always renders in the Step 1.4 confirmation; when the request is not tracker-linked it renders the literal line `Sources inspected: not a tracker-linked request.`; an absent Sources inspected block is itself a detectable violation of this gate.
```

(c) into the Step 1.4 confirmation block, between the `**Scope extensions (grilled):**` line and the `<!-- Meta-rule` comment line, separated by blank lines like its siblings:

```
**Sources inspected:** <source>: <read (what was read and when), or unavailable: why>; or the literal line `Sources inspected: not a tracker-linked request.` when the request is not tracker-linked.
```

(d) appended to the Rules list bullet that ends `for the exact date and exemption semantics).` (same paragraph, one space before the new sentence):

```
A tracker-linked plan also carries the confirmation block's Sources inspected record as its own Assumptions bullet, so the reconciliation survives into the reviewed plan bytes.
```

(e) into the Integration Points section under the `### With \`review-plan\` skill` heading, as a new paragraph after the paragraph ending `owned by receiving-review's Backlog capture.`:

```
Plan review's Step 1 tracker-source audit consumes the Sources inspected record this skill renders at Step 1.4 confirmation and carries into the plan's Assumptions; plans owns the record's shape, review-plan owns the audit and its finding class (provider: plans; consumer: review-plan).
```

- [ ] Insert block (a) at its prescribed anchor; tail `### Step 1.2: Verify key decisions explicitly` survives [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert block (b) as element 7 after element 6 [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert block (c) between the Scope extensions line and the meta-rule comment [class: IMPLEMENTATION_REQUIRED]
- [ ] Append block (d) to the rules bullet ending `for the exact date and exemption semantics).` [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert block (e) as a new paragraph in the With `review-plan` Integration Points subsection [class: IMPLEMENTATION_REQUIRED]
- [ ] `Plans-side span pins RED then GREEN`: on the base tree validation check 1 exits 1 on its first span (authoring-time RED evidence recorded in the Validation preamble); after this task checks 1, 2, and the plans-side check 4 chains exit 0 with every span at its exact count [class: REPOSITORY_TEST]
- [ ] Run `bash scripts/check_maintenance_pins.sh` (validation check 5), expect pass: no external pin literal or count over `agents/skills/plans/SKILL.md` moved; the prompt-log runtime-state failure class is tolerated and recorded, any other PIN FAIL stops the task [class: REPOSITORY_TEST]
- [ ] Commit: `skills: add tracker-source reconciliation duty to plans Phase 1` (this commit must not land or merge without Task 2's commit: the one-series item in Task 2 owns the guard) [class: IMPLEMENTATION_REQUIRED]

### Task 2: review-plan tracker-source audit

Files:
- `agents/skills/review-plan/SKILL.md`

Evidence:
- Validation block check 3 and the check 4 chains `review-plan item 9` and `review-plan Integration Points placement`; covers every Task 2 checklist criterion
- `bash scripts/check_maintenance_pins.sh`; covers the no-external-pin-breaks criterion

The two verbatim insertions for this task:

(f) into Step 1's pre-flight list, immediately after item 8 (the Declaration audit item ending `like any other required element)`):

```
9. **Tracker-source audit**: for a plan whose header, backlog origin, tasks, or story-key filename stem reference a tracker issue (a reference means an issue-key-shaped token or a tracker URL appearing in those surfaces; a filename, path, or prose token that merely contains a ticket-shaped word, and non-tracker key-shaped tokens such as ADR, lesson, or review ids, quoted example keys, digest literals, encoding labels, and timezone labels, is not a reference), verify the plan carries the Sources inspected record (an Assumptions bullet naming each authoritative source with its read state, or why an unavailable source could not be read). A missing record, or a record that names no source for a linked contract named by the request or issue that the tasks expose or implement, is an ordinary correctness-completeness finding. A plan with no tracker reference passes vacuously; the vacuous pass means only that no byte-level reference exists, and when the origin request is available to review and names an issue for the work being planned (per the Tracker-linked request definition), the request-keyed Phase 1 trigger applies instead of the byte-level one.
```

(g) into the Integration Points section under the `### With \`plans\` skill` heading, as a new paragraph after the paragraph ending `receiving-review's Backlog capture).`:

```
Plan review's Step 1 tracker-source audit (item 9) consumes the Sources inspected record plans renders at Step 1.4 and carries into Assumptions; plans SKILL.md owns the record's shape (provider: plans; consumer: review-plan).
```

- [ ] Insert block (f) as item 9 after item 8 [class: IMPLEMENTATION_REQUIRED]
- [ ] Insert block (g) as a new paragraph in the With `plans` Integration Points subsection [class: IMPLEMENTATION_REQUIRED]
- [ ] `review-plan span pins RED then GREEN`: on the base tree validation check 3 exits 1 on its first span; after this task check 3 and the review-plan-side check 4 chains exit 0 with every span exactly once [class: REPOSITORY_TEST]
- [ ] The two task commits land as one series: Task 1's commit carries insertion (e), which references the audit that only this task's commit creates, so the branch never lands or merges with Task 1's commit alone [class: IMPLEMENTATION_REQUIRED]
- [ ] Run `bash scripts/check_maintenance_pins.sh` (validation check 5), expect pass: no external pin literal or count over `agents/skills/review-plan/SKILL.md` moved; the prompt-log runtime-state failure class is tolerated and recorded, any other PIN FAIL stops the task [class: REPOSITORY_TEST]
- [ ] Commit: `skills: add tracker-source audit to review-plan pre-flight` [class: IMPLEMENTATION_REQUIRED]

### Task 3: cross-surface gate sweep

Files: none (validation-only task; no file bytes change).

Evidence:
- Validation block checks 5 through 8; covers every Task 3 checklist criterion

- [ ] Run the shared-body neutrality and ContractContentParity probes as one pytest invocation (check 6), expect green: proves no pre-existing plans-skill structural probe broke [class: REPOSITORY_TEST]
- [ ] Run the instruction-size background gate (check 7), expect exit 0: the repository's root instruction files still fit; the two skill bodies are not in its default file set, so this is not the size proof for the insertions [class: REPOSITORY_TEST]
- [ ] Run the em-dash added-lines gate over both files against the base branch (check 8), expect clean [class: REPOSITORY_TEST]
- [ ] Run the complete Validation Commands block start to finish, expect the final `validation: all checks passed` line and exit 0 [class: REPOSITORY_TEST]
- [ ] Immediately before landing, after any rebase onto a moved base branch, re-run the complete Validation Commands block on the rebased tree, expect exit 0: the span pins and ordered chains are exactly the assertions a peer landing of a similar span would invalidate on the base while the authoring worktree stays green [class: REPOSITORY_TEST]


## Disposition of migrated backlog items

- `docs/history/backlog/2026-10-01-plans-verify-ticket-and-linked-contract-sources.md` - the plan's sole origin; executed+landed 2026-10-02 (landing ff097606), origin file deleted per the fold-and-delete rule with this section as its disposition record.
