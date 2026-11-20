# Plan: plan-readiness seal leg diagnostics separation

Backlog origin: docs/history/backlog/2026-11-09-plan-readiness-seal-breaks-on-rebase-and-post-review-plan-edits.md
Authoring claim: 2026-11-09-plan-readiness-seal-breaks-on-rebase-and-post-review-plan-edits.md (session sess_9625dcb1-108b-406b-8058-4c786ec1badc)
Driving force: reliability (primary), efficiency (secondary)
Force justification: reliability is outside the closed driving-force taxonomy; this plan is implemented anyway because a fail-closed guard whose refusal cannot name its failure world turns operators away from readiness output (the origin row's witnessed misdiagnosis, re-witnessed 2026-11-14), and park-triage would not take it because the class re-fires on every hand-minted or history-rewritten seal.
Plan review record: the staging series .ai-playbook/reviews/2026-11-15-plan-review-plan-readiness-seal-leg-diagnostics-separation-pd63db312-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 2h total, largest task 1h
Executed: yes (45019ebb5)

## Terms

- seal entry: the `## round <N>` block in `.ai-playbook/review-certs/<artifact-slug>.md` carrying `round_start_commit`, `round_start_digest`, `round_close_commit` (read by `load_seal_entry` in `scripts/corrections_record.py`).
- round-start commit: the commit whose plan blob bytes hash to the seal's `round_start_digest`.
- round-close commit: the commit the certified round closed on; the seal's dating anchor.
- landed anchor (byte-resolved substitute): the first-parent ancestor `resolve_landed_anchor` finds whose plan blob re-hashes to `round_start_digest`, used when a recorded anchor is no longer an ancestor of HEAD.
- first-parent scan: the `git rev-list --first-parent` enumeration inside `resolve_landed_anchor`, bounded by `LANDED_ANCHOR_SCAN_LIMIT`.
- ordering arm: the seal-integrity dating refusal that fires when the round-start commit postdates the round-close commit.
- sanctioned exits: the origin row's option (a)/(b) design: widen the byte search to any HEAD-reachable commit and add a recorded exit for legitimately amended plans. Priced here, not implemented.
- mint-time existence verification: verifying at seal-mint time that a declared anchor sha resolves (`git cat-file`), development lessons #449; carried as skill-text context, never a validator.
- machinery admission fields: the four fields the repository guidelines' Machinery admission protocol requires of any blocking addition: incident link, expected catch frequency, false-positive cost, sunset/review date.

## Why

The seal verification legs refuse with one undifferentiated voice: a transcribed-but-nonexistent anchor sha, a deliberately moved anchor, and a legitimate history rewrite all surface as look-alike refusals, and the 2026-11-14 witness surfaced an unresolvable anchor under the dating leg's "anchors were moved" message. The operator repaired a one-character transcription error through anchor-move forensics. The sanctioned-exits design that would stop rebases from costing review rounds exists as an origin-row option but has never been priced under the machinery admission protocol.

## Gist & Examples

TLDR: name the failing seal world in the refusal itself and price the sanctioned exits, so a transcription fix no longer reads as anchor forensics and a rebase stops costing a review round, restoring trust in the readiness gate (reliability).

Before (today): an authoring closeout runs `python3 scripts/plan_readiness.py <plan>` over a seal whose `round_start_commit` was hand-transcribed with a dropped character. The anchor is missing, the byte-identity fallback silently resolves the sealed bytes at a later commit, and the ordering arm refuses with `the round-start commit postdates the round-close commit: the seal entry's anchors were moved`. Nothing in the refusal says the declared sha never existed, which commit the substitute is, or which leg fired. The operator greps history for an anchor-move attack that never happened.

After (this plan): the same input refuses with a message that names the declared sha as unresolvable (`does not resolve in this repository`), and when a byte-resolved substitute is in play, whatever leg refuses says so (`byte-resolved substitute` plus the substitute commit and the firing leg). The transcription fix is a one-line `git cat-file -t` check by the reader; forensics are unnecessary. A second record, the pricing doc, carries the sanctioned-exits design with its four admission fields so the promotion decision can be made on its own future plan instead of being re-derived each time.

Edge cases that shaped the scope: a moved anchor with no byte identity must keep refusing exactly as today (the safety witness); real git plumbing failures keep their existing arms; the ordering refusal's fail-closed identity is byte-retained and only extended with the substitution naming.

## Outcome

Execute this plan and the seal verification refusals become self-describing: each refusal names its firing leg and its failure world, and the sanctioned-exits promotion decision carries priced admission evidence instead of folklore.

- A transcription error in a seal anchor is diagnosable from the refusal text alone; no history forensics needed.
- A byte-resolved substitute feeding a refusal is visible in that refusal (substitute commit and firing leg), so the anti-move ordering arm's refusals become auditable.
- The sanctioned-exits arm has a durable pricing record with its machinery admission fields, ready for its own promotion plan.
- The gate delta is zero: no new refusal class, gate, fence, or schema field.

Gate delta: none (message text inside the existing refusal classes only; Task 2 adds a pricing record and a one-line skill-text context pointer; no gate, fence, protocol layer, schema field, or checked-set growth; no removal).

Follow-up disposition: the sanctioned-exits arm stays unimplemented by design; its route is the pricing record's promotion path (a future plan under the machinery admission protocol, promoted only after a true catch with a pre-registered registry-removal row). The origin row stays open covered-pending-execution and carries no additional follow-up candidates.

## Assumptions

- assume Task 1 is message text and test work only in `scripts/corrections_record.py`; basis: the dispatch entry's "(message-only change)" and the origin row's diagnostics framing.
- assume `scripts/plan_readiness.py` needs no change; basis: source read shows it surfaces `verify_corrections` refusal strings verbatim.
- assume the pricing record's durable home is a dated analysis doc under `docs/maintenance/`; basis: the repo's convention for machinery pricing analyses (for example `machinery-blocker-audit-2026-10-09.md`).
- assume the mint-time pointer lands beside the Round-close seal paragraph in `agents/skills/review-plan/SKILL.md`, the seal-field writer of record; basis: the origin row names review-plan as the seal-field writer and the paragraph is the mint site.
- assume the origin row's option (a)/(b) implementation stays out of scope (priced only); basis: the dispatch entry prices it as a guard-bearing change for its own promotion cycle; this narrowing is recorded here, not silently dropped.
Decision points requiring a grill: none remain.

## Standing constraints

- Every refusal stays fail-closed; no leg may become a pass (`verify_corrections` returns False in every case it refuses today).
- The ordering arm's refusal keeps its pinned prefix (`the round-start commit postdates the round-close commit`) and its verdict semantics byte-retained; both tasks may only extend the message.
- No new validator, gate, schema field, or state surface; Task 2's record and pointer are documentation only.
- Plan and code bytes carry no em dashes (the write-time fence and the boundary scans own this).

## Evaluation Criteria

**Quality dimensions:**
- correctness: the three witnessed worlds (unresolvable declared sha; byte-resolved substitute refused by the ordering arm; moved anchor with no byte identity) produce three distinguishable refusal texts; the suite proves each.
- fail-closed integrity: no refusal becomes a pass; the pre-existing not-an-ancestor refusal and the ordering refusal keep their verdicts and pinned prefixes.
- pricing completeness: the pricing record carries all four machinery admission fields with concrete values.
- no-growth: zero gate delta; the skill-text addition is a one-line context pointer citing an existing lesson.

**Done when:**
- `scripts/corrections_record.py` emits the leg-naming diagnostics and the pinned phrases from Validation Commands are present in the source.
- `scripts/test_corrections_record.py` passes in full, including the pre-existing tests, with new assertions pinning the three worlds.
- `docs/maintenance/seal-sanctioned-exits-pricing-2026-11-15.md` exists with the four admission fields.
- `agents/skills/review-plan/SKILL.md` carries the mint-time pointer beside the Round-close seal paragraph.
- The byte-budget gate reports zero ceiling breaches and the maintenance pins suite reports no new failure beyond its recorded baseline row.

**Ship when:**
- The next witness of the misdiagnosis class reads a self-describing refusal and repairs without forensics (human-observed, prose only).
- The exits-arm promotion decision is taken on its own future plan using the priced record.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/corrections_record.py` (Task 1); partially in scope: only the seal verification legs' refusal-text assembly (`verify_corrections`, the substitution handling around `resolve_landed_anchor`'s result, `_ANCHOR_COMMIT_LABELS` consumers). All other methods in this file are frozen; reject any review finding that touches them.

**Tests:**
- `scripts/test_corrections_record.py` (Task 1)

**Documentation:**
- `docs/maintenance/seal-sanctioned-exits-pricing-2026-11-15.md` (Task 2) *(new)*
- `agents/skills/review-plan/SKILL.md` (Task 2); in scope only for the mint-time pointer insertion beside the Round-close seal paragraph; the rest of the file is frozen.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `scripts/plan_readiness.py`; reason: surfaces refusal strings verbatim, no change needed (assumption above).
- Any implementation of the sanctioned-exits arm itself; reason: priced only, promotion rides its own future plan.
- `scripts/check_maintenance_pins.sh` or the EXEC-PROMPTS receipt header; reason: the suite's baseline-red row pre-exists this plan (recorded below) and no task touches it.

## Validation Commands

Validation preamble (authoring record, rule 29): the block below was executed over the plan bytes and the current tree before round 1. RED-today evidence at authoring time (2026-11-15, worktree of `authoring/2026-11-09-plan-readiness-seal-breaks-on-rebase-and-post-review-plan-edits`): the Task 1 obligation pins `does not resolve in this repository` and `byte-resolved substitute` were absent from `scripts/corrections_record.py` (expected RED; they flip GREEN exactly when Task 1 lands), while `the round-start commit postdates the round-close commit` and `no first-parent ancestor carries the sealed` were present (regression pins, GREEN today). The em-dash touched scan, the public hygiene scan, and the readiness pre-round gate were run over the plan bytes; outcomes are recorded per round in the staging records. The pins suite carries one recorded baseline-red row at authoring time: `PIN FAIL: EXEC-PROMPTS receipt delta named in the log header` (pre-existing 2026-11-14 peer landing; no task touches that file); the block's pins arm passes when that row is the only failing pin.

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO" || exit 1
# Task 1 obligations pinned in scripts/corrections_record.py (the first two are RED until Task 1 lands)
grep -qF 'does not resolve in this repository' scripts/corrections_record.py || { echo 'FAIL: unresolvable-anchor obligation absent'; exit 1; }
grep -qF 'byte-resolved substitute' scripts/corrections_record.py || { echo 'FAIL: substitute-naming obligation absent'; exit 1; }
grep -qF 'the round-start commit postdates the round-close' scripts/corrections_record.py || { echo 'FAIL: pinned ordering refusal absent'; exit 1; }
grep -qF 'no first-parent ancestor carries the sealed' scripts/corrections_record.py || { echo 'FAIL: not-an-ancestor refusal absent'; exit 1; }
# corrections suite, focused per the repository suite policy
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m pytest scripts/test_corrections_record.py -q || { echo 'FAIL: corrections suite'; exit 1; }
# Task 2 pricing record carries the four machinery admission fields (dedicated per-field probes)
P=docs/maintenance/seal-sanctioned-exits-pricing-2026-11-15.md
test -f "$P" || { echo 'FAIL: pricing record missing'; exit 1; }
grep -qF '2026-11-09-plan-readiness-seal-breaks-on-rebase-and-post-review-plan-edits.md' "$P" || { echo 'FAIL: incident link absent'; exit 1; }
grep -qF 'Expected catch frequency:' "$P" || { echo 'FAIL: catch-frequency field absent'; exit 1; }
grep -qF 'False-positive cost:' "$P" || { echo 'FAIL: false-positive-cost field absent'; exit 1; }
grep -qF 'Sunset/review date:' "$P" || { echo 'FAIL: review-date field absent'; exit 1; }
grep -qF 'byte-resolved substitute' "$P" || { echo 'FAIL: pricing record missing the substitute design'; exit 1; }
# mint-time pointer carried as skill-text context beside the seal-field writer's Round-close seal paragraph
grep -qF 'Round-close seal' agents/skills/review-plan/SKILL.md || { echo 'FAIL: seal paragraph anchor absent'; exit 1; }
LN="$(grep -n 'Round-close seal' agents/skills/review-plan/SKILL.md | head -1 | cut -d: -f1)"
SEALSPAN="$(sed -n "${LN},$((LN+3))p" agents/skills/review-plan/SKILL.md | tr '\n' ' ' | tr -s ' ')"
printf '%s' "$SEALSPAN" | grep -qF 'development_lessons.md' || { echo 'FAIL: pointer not beside the Round-close seal paragraph'; exit 1; }
printf '%s' "$SEALSPAN" | grep -qE 'lesson 449|lessons #449|#449' || { echo 'FAIL: lesson 449 citation absent beside the seal paragraph'; exit 1; }
# shared-body gates over the touched skill file (blocking class only)
python3 scripts/skill_text_budget.py --check || { echo 'FAIL: byte-budget ceiling breach'; exit 1; }
# maintenance pins suite with its recorded baseline row exempted by name
PINS_OUT="$(mktemp)"; bash scripts/check_maintenance_pins.sh >"$PINS_OUT" 2>&1; PINS_RC=$?
if [ "$PINS_RC" -ge 2 ]; then echo "FAIL: pins suite tool error rc=$PINS_RC"; rm -f "$PINS_OUT"; exit 1; fi
if [ "$PINS_RC" -eq 1 ]; then
  N="$(grep -c 'PIN FAIL' "$PINS_OUT" || true)"
  if [ "$N" -ne 1 ] || ! grep -qF 'PIN FAIL: EXEC-PROMPTS receipt delta named in the log header' "$PINS_OUT"; then
    echo 'FAIL: new pins failure beyond the recorded baseline row'; rm -f "$PINS_OUT"; exit 1
  fi
  echo 'NOTE: only the recorded baseline pin row failed'
fi
rm -f "$PINS_OUT"
# per-round text-policy sweep over this plan's own landing range
bash scripts/check-no-em-dash.sh added-lines --base "$(git merge-base main HEAD)" || { echo 'FAIL: em-dash added lines'; exit 1; }
bash scripts/scan-public-hygiene.sh || { echo 'FAIL: public hygiene scan'; exit 1; }
```

### Task 1: leg-naming diagnostics in the seal verification refusals

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `scripts/corrections_record.py`
- `scripts/test_corrections_record.py`

Primary class anchors:
- `verify_corrections` in `scripts/corrections_record.py`
- `resolve_landed_anchor` in `scripts/corrections_record.py`

- [x] RED canary, unresolvable-anchor world: given a seal entry whose declared `round_start_commit` is a nonexistent hex40 and no ancestor carries the sealed bytes, expects the anchor-leg refusal to contain the declared sha, the phrase `does not resolve in this repository`, and the leg label `anchor leg refused`; run the corrections suite selection for this world → expect RED [class: REPOSITORY_TEST]
- [x] RED canary, substitute world: given the byte-identity fallback resolving a substitute that postdates `round_close_commit`, expects the ordering refusal to keep `the round-start commit postdates the round-close commit` and to name the substitute commit with the phrase `byte-resolved substitute` and the firing leg; run the selection → expect RED [class: REPOSITORY_TEST]
- [x] RED canary, composed world (r1 F1): given a nonexistent declared `round_start_commit` whose sealed bytes the fallback resolves at a later substitute that postdates `round_close_commit`, expects one refusal carrying BOTH namings together: the declared sha with `does not resolve in this repository`, and the substitute commit with `byte-resolved substitute` and the firing leg; run the selection → expect RED [class: REPOSITORY_TEST]
- [x] RED canary, second post-substitution leg (r1 F1): given a byte-resolved substitute in play and a declared digest the substituted round-start bytes do not match (the bare-rewrite arm, zero hops), expects the bare-rewrite refusal to also carry the substitution naming (the substitute commit and `byte-resolved substitute`); run the selection → expect RED [class: REPOSITORY_TEST]
- [x] Regression pin, no-bypass safety witness: given a moved anchor with no byte identity anywhere in the scan, expects the existing not-an-ancestor refusal (`no first-parent ancestor carries the sealed`) to still refuse; run the selection → expect GREEN today and GREEN after [class: REPOSITORY_TEST]
- [x] Regression pin, plumbing-failure arms unchanged: given a real git plumbing failure during the scan or dating, expects the existing plumbing-failure refusals verbatim; run the selection → expect GREEN today and GREEN after [class: REPOSITORY_TEST]
- [x] Write minimal implementation, unresolvable-anchor naming: message-only edit in the anchor legs so a declared anchor sha that has no commit object is named as unresolvable; keep `does not resolve in this repository` as a contiguous single-line string literal so the Validation pin matches [class: IMPLEMENTATION_REQUIRED]
- [x] Write minimal implementation, substitution naming: when a declared anchor is replaced by a byte-resolved substitute, every later refusal in the same verification names the substitute commit and the firing leg, composing with the unresolvable-anchor naming when both worlds co-occur (the composed canary's single refusal); keep `byte-resolved substitute` as a contiguous single-line string literal so the Validation pin matches [class: IMPLEMENTATION_REQUIRED]
- [x] Write minimal implementation, ordering prefix retained: the ordering refusal's verdict semantics and pinned prefix byte-retained; today's source splits the message across string continuations, so the existing single-line fragment `the round-start commit postdates the round-close` survives on one line [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the whole corrections suite passes, including the pre-existing tests; where an existing assertion pins the old message text, the assertion is updated to the new text in the same change and the update is named in the commit message [class: REPOSITORY_TEST]
- [x] Commit: `fix: name the failing seal world in corrections refusals` [class: IMPLEMENTATION_REQUIRED]

### Task 2: price the sanctioned-exits arm and carry the mint-time pointer

Context surface: the plan's Terms, this task, and `## Standing constraints`.

Files:
- `docs/maintenance/seal-sanctioned-exits-pricing-2026-11-15.md` *(new)*
- `agents/skills/review-plan/SKILL.md`

- [x] Create the pricing record's design statement: widen the first-parent byte search in `resolve_landed_anchor` to any HEAD-reachable commit, and add a recorded exit for legitimately amended plans; state that the pinned ordering refusal is retained under the arm, sharing the byte-resolved substitute vocabulary with the Task 1 messages [class: IMPLEMENTATION_REQUIRED]
- [x] Create the pricing record's four machinery admission fields with concrete values: `Incident:` naming the origin row and development lessons #449; `Expected catch frequency:`; `False-positive cost:`; `Sunset/review date:` [class: IMPLEMENTATION_REQUIRED]
- [x] Add the mint-time existence pointer as one context line beside the Round-close seal paragraph in `agents/skills/review-plan/SKILL.md`, citing development lessons lesson 449 (verify the lesson number in `docs/maintenance/development_lessons.md` before inserting); the pointer sits within the Round-close seal paragraph's own region (the adjacency the Validation probes pin); context only, no validator, gate, or required ceremony [class: IMPLEMENTATION_REQUIRED]
- [x] Run the shared-body gates over the touched skill file: byte-budget check reports zero ceiling breaches; where the insertion grows the file past its cap, the same change deletes equivalent bytes in that file (the paying arm); maintenance pins suite reports no new failure beyond the recorded baseline row; run both → expect pass [class: REPOSITORY_TEST]
- [x] Commit: `docs: price the seal sanctioned-exits arm and carry the mint-time pointer` [class: IMPLEMENTATION_REQUIRED]
