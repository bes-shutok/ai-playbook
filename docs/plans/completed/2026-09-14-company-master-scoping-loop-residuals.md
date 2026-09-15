# Plan: company-master scoping loop residuals

Backlog origin: `docs/history/backlog/2026-09-12-company-master-scoping-loop-residuals.md` (4 items; scope of record). Origin reviews: `docs/reviews/2026-09-12-branch-review-2026-09-11-execute-plan-runtime-residuals-r3.md` (items 1 and 2) and `docs/reviews/2026-09-12-branch-review-2026-09-11-execute-plan-runtime-residuals-r5.md` (items 3 and 4).

## Terms

- **fork (2b)**: learn Step 1.2 item 4 placement-fork sub-bullet "(2b) Company-wide convention"; routes a company-wide rule to the company master. Distinct from the literal Step 1.2 item 2b (formatting).
- **item 2b (formatting)**: the literal learn Step 1.2 item 2b, "Format using the standard Principle-based Template"; unrelated to fork (2b) and never renamed by this plan.
- **item 5c (placement receipt)**: learn Step 1.2 receipt item; also carries the blocking placement question for an unresolved company master.
- **item 5d**: the new numbered item this plan creates; the canonical home of the ownership-scoping resolution test, inserted immediately before item 5c.
- **ownership-scoping resolution test**: decides whether the company master resolves (incident repo under the company root AND the key path exists, with component-wise containment mechanics).
- **company master**: the `company_guidelines_master` facts key and the file it resolves to.
- **drift / drift WARNING**: the repo sits under the company root with the key path missing; the WARNING line `config drift: company guidelines master not found; company duplicate audit not run` printed by done 4a.
- **done 4a**: `agents/skills/done/SKILL.md` Step 3 item 4a, the pre-commit lesson scope audit.
- **witness line**: the out-of-scope note, drift WARNING, or cold-start warning done 4a emits when the mechanical duplicate check does not run.

## Assumptions

- assume item 1 is realized as candidate (a), the drift-path commit-body witness, not candidate (b) transcript-only documentation; basis: first-listed backlog candidate, delivers the item's stated durable-trail goal, accepted per standing pre-authorization in the 2026-09-14 authoring task
- assume item 2 realizes "own numbered item" as item 5d inserted immediately before the current item 5c, the receipt keeps label 5c, and only test-meaning citations flip 5c to 5d; basis: backlog candidate direction ("for example 5d immediately before 5c") plus the citation inventory (receipt-meaning citations in done 544, generalize 258, the learn blocking-question phrases, and the facts routing line then stay stable)
- assume the promoted 5d text is a pure relocation of the test block from 5c with zero semantic change; basis: the item is a promotion and renumber ask, deferred at r3 exactly to avoid semantic churn
- assume item 3 fixes each bare citation to "fork (2b)", matching how the section names the fork elsewhere; basis: r5 F1 suggested fix
- assume item 4 drops the qualifier rather than restating it in token terms; basis: first-listed backlog candidate; token-only lock semantics are already documented in done near Step 6
- assume the facts `Guideline canonical homes` paragraph is edited in the same change set as the learn promotion, with no commit step; basis: the 5b living-surfaces inventory lists it, and `~/.ai-playbook` has no `.git` (verified 2026-09-14)
- assume the backlog item stays in `docs/history/backlog/` while this plan is open; basis: plans-skill backlog-origin rule (the completion pass moves it)

Decision points requiring a grill: item 1 direction = drift-path commit-body witness (recommended option accepted per standing pre-authorization, authoring task 2026-09-14, affects Gist and Task 2); item 2 numbering = item 5d inserted immediately before item 5c with the receipt keeping 5c (backlog candidate direction 2026-09-12, affects Task 4); item 3 wording = fork (2b) per section naming (r5 F1 suggested fix, affects Task 3); item 4 wording = qualifier dropped (first backlog candidate, affects Task 1)

## Gist & Examples

This plan lands the four residuals deferred from the company-master ownership-scoping loop: a durable audit trail for skip decisions (item 1), promotion of the ownership-scoping resolution test to its own numbered item (item 2), disambiguation of three bare "item 2b" citations (item 3), and removal of an orphaned lock-generation phrase (item 4). All four are instruction-document edits in two skill files plus one facts paragraph; no runtime code changes.

Durable skip audit (item 1). Trigger: a done session commits lesson-corpus changes while the repo sits under the company root with the master key path missing (config drift). The 4a audit prints the drift WARNING, counts the outcome as passed-with-drift, and the Step 3 commit proceeds without the company duplicate check having run.
**Before (today):** the skip exists only in the session transcript and the Step 7 outcome report echo; an auditor working from repository history alone sees a normal corpus commit with no trace of the skipped check.
**After (this plan):** the same commit's message body carries `lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run` on its own body line, so repository history alone reconstructs the skip decision. The out-of-scope and cold-start witness paths stay transcript-only: the backlog scopes this item to the drift path, the only skip where an audit against a resolvable master was expected and did not run.

Citation integrity (items 2 and 3). Trigger: a fan-out executor or checklist verifier is told to update a living surface of the ownership-scoping resolution test and greps the label it was given.
**Before (today):** the label "item 5c" lands on the placement-receipt paragraph where the canonical test is buried mid-paragraph, and a bare "item 2b" can resolve to the literal formatting item 2b, leaving fork (2b) unmirrored or the sibling-search scoping misjudged.
**After (this plan):** the test has its own numbered item 5d immediately before 5c; every test-meaning citation says 5d, every receipt-meaning citation still says 5c, and the three bare "item 2b" phrases say fork (2b), so the first grep hop resolves each citation to the right surface.

Lock wording (item 4). Trigger: a reader of the done-lock Abandoned definition cross-checks it against the lock script selftest.
**Before (today):** the definition ends "and there is no matching `<repo>/.ai-playbook/done-lock.session` for the lock generation", but the lock-generation concept was removed (token-only locks; the selftest asserts the meta file carries no `generation=` key).
**After (this plan):** the orphaned qualifier is dropped; the definition reads "and there is no matching `<repo>/.ai-playbook/done-lock.session`."

Edge cases that shaped the design: the blocking-question citations ("route through the item 5c blocking placement question", "report the item 5c blocking placement question") reference the receipt item's blocking question, not the test, so they stay 5c; against the backlog's five-surface inventory the Step 6 checklist carries only receipt-meaning 5c citations (the sibling-search list and the placement-receipt mention), so the checklist needs no flip while the facts paragraph's one test-meaning citation does flip; the literal formatting item 2b is never renamed; the drift WARNING print text is unchanged because the done-side skip semantics (passed-with-drift, non-blocking) were settled at r3.

## Evaluation Criteria

**Quality dimensions:**
- correctness: every insertion and extraction matches the byte spans prescribed in the tasks; the full Validation Commands block exits 0 from the repo root
- citation integrity: every test-meaning citation resolves to item 5d and every receipt-meaning citation still resolves to item 5c, proven by per-file preservation gates over learn, done, generalize, and facts
- scope discipline: only `agents/skills/learn/SKILL.md`, `agents/skills/done/SKILL.md`, and the facts paragraph change; frozen regions of both skill files untouched
- hygiene: zero em-dashes in the two edited skill files (both at zero today) and public hygiene scan exit 0

**Done when:**
- all task checklists are complete and the full Validation Commands block exits 0
- the four backlog dispositions are realized: qualifier gone, drift witness durable in the corpus commit body, three bare citations disambiguated, test promoted with the citation fan-out updated
- preservation gates confirm the receipt-meaning 5c citations and the literal formatting item 2b are unchanged

**Ship when:** the edits reach the repository's default branch via the normal merge flow; no deploy, external system, or cross-team condition applies.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/learn/SKILL.md` (sites: item 2b line test citation; item 4c line test citation; 5b living-surfaces list; the new item 5d line; the item 5c routing-boundary sentence; the 5c test-block extraction and pointer; the Completion Checklist line). All other content in this file is frozen; reject any finding that touches it.
- `agents/skills/done/SKILL.md` (sites: the Abandoned definition qualifier; the 4a drift branch; the 4a echo note; the 4a test citation flip; the Step 3 item 6 commit-message pointer). All other content in this file is frozen; reject any finding that touches it.
- `~/.ai-playbook/facts.md` (`Guideline canonical homes` paragraph test citation; outside this repository, so validated by grep rather than diff review; no commit applies)

**Tests:** none; the surfaces are instruction documents and this plan's gates are the Validation Commands greps.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring implied by an explicit must-fix change (for example a citation the item 5d move breaks), or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/generalize/SKILL.md`; its placement-receipt citation stays 5c by design (preservation gate)
- `scripts/done-lock.sh`; its selftest failure message ("takeover reused lock generation") is runtime test code outside the backlog item's anchors
- `docs/reviews/**` and `docs/history/backlog/**`; review history is immutable context and the backlog item moves only at plan completion
- `README.md`; no skill name, path, or usage change

## Validation Commands

```bash
cd "$(git rev-parse --show-toplevel)" || exit 1
fail() { echo "FAIL: $1"; exit 1; }

test -f agents/skills/learn/SKILL.md || fail "missing learn/SKILL.md"
test -f agents/skills/done/SKILL.md || fail "missing done/SKILL.md"
test -f agents/skills/generalize/SKILL.md || fail "missing generalize/SKILL.md"
test -f "$HOME/.ai-playbook/facts.md" || fail "missing user facts document"

# Item 2 promotion (learn item 5d)
test "$(grep -oF '5d. **Ownership-scoping resolution test:**' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "5d heading missing or duplicated"
test "$(grep -oF 'The resolution outcome is decided by the ownership-scoping resolution test (item 5d).' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "5c pointer sentence missing"
test "$(grep -oF 'ownership-scoping resolution test in item 5d' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "item 2b test citation not flipped to 5d"
test "$(grep -oF 'per the item 5d ownership-scoping resolution test' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "item 4c test citation not flipped to 5d"
test "$(grep -oF 'fork (2b), item 5d,' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "5b living-surfaces inventory not finalized"
test "$(grep -oF 'which `done` Step 3 item 4a audits at commit time as a non-blocking drift WARNING' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "moved test block not present exactly once"
test "$(grep -oF 'the master resolves only when the incident repo (per item 3b) sits under the company workspace root' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "test definition duplicated or lost"
test "$(grep -oF 'Containment compares fully resolved absolute paths component by component' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "5d containment sentence missing or duplicated"
test "$(grep -oF 'A repo at the root itself is not under it, and a directory sharing only a leading substring with the root does not match' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "5d boundary sentence missing or duplicated"

# Item 3 disambiguation (learn)
test "$(grep -oF 'The routing answer respects fork (2b): outside the company root' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "5c routing sentence not disambiguated"
test "$(grep -oF 'wherever required by fork (2b), item 4c, or item 5c' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "checklist sibling-search list not disambiguated"
test "$(grep -oF 'company scope, per fork (2b))' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "checklist drift parenthetical not disambiguated"
rc=0; grep -q "item 2b" agents/skills/learn/SKILL.md || rc=$?
if [ "$rc" -eq 0 ]; then fail "bare item-2b citation remains in learn"; fi
if [ "$rc" -ge 2 ]; then fail "grep error on learn/SKILL.md (rc=$rc)"; fi

# Item 1 drift-path witness (done 4a)
test "$(grep -oF 'lesson-scope-audit: config drift: company guidelines master not found' agents/skills/done/SKILL.md | wc -l)" -eq 1 || fail "commit-body witness instruction missing"
test "$(grep -oF 'so the skip decision is reconstructable from repository history alone' agents/skills/done/SKILL.md | wc -l)" -eq 1 || fail "drift-branch rationale missing"
test "$(grep -oF 'additionally carried durably in the corpus commit message body' agents/skills/done/SKILL.md | wc -l)" -eq 1 || fail "4a echo note not extended"
test "$(grep -oF 'lesson-scope-audit' agents/skills/done/SKILL.md | wc -l)" -eq 2 || fail "commit-body witness not wired at both 4a and the Step 3 item 6 pointer"
test "$(grep -oF 'print a one-line WARNING (`config drift: company guidelines master not found; company duplicate audit not run`)' agents/skills/done/SKILL.md | wc -l)" -eq 1 || fail "drift WARNING print text changed"

# Item 4 qualifier dropped (done Abandoned definition)
rc=0; grep -qF "for the lock generation" agents/skills/done/SKILL.md || rc=$?
if [ "$rc" -eq 0 ]; then fail "orphaned lock-generation qualifier still present"; fi
if [ "$rc" -ge 2 ]; then fail "grep error on done/SKILL.md (rc=$rc)"; fi
test "$(grep -oF 'no matching `<repo>/.ai-playbook/done-lock.session`.' agents/skills/done/SKILL.md | wc -l)" -eq 1 || fail "Abandoned definition altered beyond the qualifier drop"

# Citation fan-out across files (item 2)
test "$(grep -oF 'ownership-scoping resolution test (`learn` Step 1.2 item 5d, anchored to the repo being audited)' agents/skills/done/SKILL.md | wc -l)" -eq 1 || fail "done 4a test citation not flipped to 5d"
test "$(grep -oF 'This is the test `learn` Step 1.2 item 5d and `done` Step 3 item 4a apply' "$HOME/.ai-playbook/facts.md" | wc -l)" -eq 1 || fail "facts test citation not flipped to 5d"

# Preservation gates (receipt-meaning 5c citations stay; literal formatting item 2b stays)
test "$(grep -oF 'route through the item 5c blocking placement question' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "item 2b blocking-question citation lost"
test "$(grep -oF 'report the item 5c blocking placement question' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "item 4c blocking-question citation lost"
test "$(grep -oF 'a placement receipt (item 5c)' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "checklist receipt citation lost"
test "$(grep -oF 'placement receipt (`learn` Step 1.2 item 5c)' agents/skills/done/SKILL.md | wc -l)" -eq 1 || fail "done 544 receipt citation lost"
test "$(grep -oF 'placement receipt (`learn` Step 1.2 item 5c)' agents/skills/generalize/SKILL.md | wc -l)" -eq 1 || fail "generalize receipt citation lost"
test "$(grep -oF '`learn` Step 1.2 item 5c routes it through the blocking placement question' "$HOME/.ai-playbook/facts.md" | wc -l)" -eq 1 || fail "facts routing citation lost"
test "$(grep -oF '2b. **Format using the standard Principle-based Template**' agents/skills/learn/SKILL.md | wc -l)" -eq 1 || fail "literal formatting item 2b altered"

# Hygiene (the em-dash byte is built at runtime so this plan file stays free of it)
EM=$(printf '\xe2\x80\x94')
rc=0; grep -lq "$EM" agents/skills/learn/SKILL.md agents/skills/done/SKILL.md || rc=$?
if [ "$rc" -eq 0 ]; then fail "em-dash introduced into an edited skill file"; fi
if [ "$rc" -ge 2 ]; then fail "grep error in em-dash check (rc=$rc)"; fi
( cd "$(git rev-parse --show-toplevel)" && bash "$HOME/.ai-playbook/scripts/scan-public-hygiene.sh" ) || fail "public hygiene scan failed"

echo "ALL GATES GREEN"
```

Authoring-time check 2026-09-14: every new-span gate, both stale-text forbidden-pattern gates (the bare item-2b sweep and the dropped-qualifier sweep), and the Abandoned-definition count pin were executed against the pre-change tree and failed as expected (RED-today; the pin's needle exists only once Task 1 drops the qualifier). The em-dash gate is a forbidden-pattern gate that passes on pre-change bytes by design: both files are em-dash-free today and must stay that way. Every preservation gate and moved-block count gate passed at count 1; the four moved-block count gates (first sentence, containment sentence, boundary sentence, tail) stay at count 1 after Task 4 moves the block, which is what makes them truncation catchers rather than RED gates. Re-verify by running the full block in Task 5.

### Task 1: drop the orphaned lock-generation qualifier (backlog item 4)

Files:
- `agents/skills/done/SKILL.md`

- [x] Record the session base sha in the session notes (`git rev-parse HEAD`; called `<session-base>` below); Task 5 anchors its committed-diff check on it
- [x] In the Abandoned-lock definition, replace ``and there is no matching `<repo>/.ai-playbook/done-lock.session` for the lock generation.`` with ``and there is no matching `<repo>/.ai-playbook/done-lock.session`.``
- [x] Run → expect: the forbidden-match gate for the dropped qualifier passes (it fails on pre-change bytes) and the Abandoned-definition pin passes; the not-yet-landed new-span gates and the bare item-2b stale-text gate still fail (Tasks 2 through 4), while the moved-block count gates, every preservation gate, and the unchanged-content pins (drift WARNING print, done receipt citation) pass throughout
- [x] Commit: `skills: drop orphaned lock-generation qualifier from done Abandoned definition`

### Task 2: carry the drift-path lesson-scope witness in the commit body (backlog item 1)

Files:
- `agents/skills/done/SKILL.md`

- [x] In the Step 3 item 4a drift branch, replace ``(the placement-evidence check below still applies); it is not a failed audit.`` with ``(the placement-evidence check below still applies); it is not a failed audit. Because the duplicate check did not run, the commit message body of the Step 3 commit that stages this corpus change carries the drift witness on its own body line, `lesson-scope-audit: config drift: company guidelines master not found; company duplicate audit not run`, so the skip decision is reconstructable from repository history alone.``
- [x] In the Step 3 item 4a echo note, replace ``is echoed into the Step 7 outcome report so the skip decision is reconstructable after the session.`` with ``is echoed into the Step 7 outcome report so the skip decision is reconstructable after the session; on the drift path the witness is additionally carried durably in the corpus commit message body, so repository history alone identifies the skip.``
- [x] In the same Step 3, append to item 6 (the commit-message item): replace ``Focus on the "why" not the "what".`` with ``Focus on the "why" not the "what". When the item 4a audit fired the drift witness, the commit body includes the `lesson-scope-audit:` body line exactly as specified in item 4a.``
- [x] Run → expect: the three new-span gates for the drift branch and echo note pass (they fail on pre-change bytes), the drift WARNING print pin passes, and the Task 1 gates stay green; the not-yet-prescribed learn new-span gates, the bare item-2b stale-text sweep, and both cross-file fan-out gates (the done 4a and facts citation flips, Task 4) still fail (Tasks 3 and 4), while the moved-block count gates and all preservation gates pass throughout
- [x] Commit: `skills: carry drift-path lesson-scope witness in the corpus commit body`

### Task 3: disambiguate bare item-2b citations to fork (2b) (backlog item 3)

Files:
- `agents/skills/learn/SKILL.md`

- [x] In the item 5c routing-boundary sentence, replace ``The routing answer respects item 2b: outside the company root`` with ``The routing answer respects fork (2b): outside the company root``
- [x] In the Step 6 Completion Checklist line, replace ``wherever required by items 2b/4c/5c`` with ``wherever required by fork (2b), item 4c, or item 5c``
- [x] In the same checklist line, replace ``without counting against company scope, per item 2b)`` with ``without counting against company scope, per fork (2b))``
- [x] In the item 5b living-surfaces parenthetical, replace ``facts `Guideline canonical homes`, item 2b, item 5c,`` with ``facts `Guideline canonical homes`, fork (2b), item 5c,`` (the 5c to 5d flip in this list happens in Task 4; at this task point 5c is still the test's home, so the intermediate state is consistent)
- [x] Run → expect: the three disambiguation-span gates pass, the bare item-2b forbidden-match gate passes (it fails on pre-change bytes), and the checklist receipt-citation preservation gate passes; the not-yet-prescribed item 5d new-span gates still fail (Task 4), while the moved-block count gates pass throughout
- [x] Commit: `skills: disambiguate bare item-2b citations to fork (2b) in learn`

### Task 4: promote the ownership-scoping resolution test to item 5d (backlog item 2)

Files:
- `agents/skills/learn/SKILL.md`
- `agents/skills/done/SKILL.md`
- `~/.ai-playbook/facts.md`

- [x] In learn Step 1.2, insert the following new line between the item 5b line and the item 5c line (it carries the test block moved out of item 5c; the mechanics wording is byte-identical to today's 5c block, prefixed with the item number and title):

```text
5d. **Ownership-scoping resolution test:** the master resolves only when the incident repo (per item 3b) sits under the company workspace root (`company_projects_root` in facts) AND the key's path exists. Containment compares fully resolved absolute paths component by component: resolve symlinks, expand the tilde, strip trailing separators, normalize Unicode to a single form, and normalize case when the filesystem is case-insensitive (mechanics mirrored in the facts `Guideline canonical homes` paragraph; update both per item 5b). A repo at the root itself is not under it, and a directory sharing only a leading substring with the root does not match. Outside the company root (a repo under the personal root, or under neither workspace root) the key is treated as unresolved even though the user-level facts table lists a global value; under the root with the path missing it is also unresolved (reason: config drift), which `done` Step 3 item 4a audits at commit time as a non-blocking drift WARNING.
```

- [x] In item 5c, replace the extracted block (from ``**Ownership-scoping resolution test:** the master resolves only when`` through ``audits at commit time as a non-blocking drift WARNING.`` inclusive) with ``The resolution outcome is decided by the ownership-scoping resolution test (item 5d).``
- [x] In the learn item 2b line, replace ``ownership-scoping resolution test in item 5c`` with ``ownership-scoping resolution test in item 5d``
- [x] In the learn item 4c line, replace ``per the item 5c ownership-scoping resolution test`` with ``per the item 5d ownership-scoping resolution test``
- [x] In the learn item 5b living-surfaces parenthetical, replace ``fork (2b), item 5c,`` with ``fork (2b), item 5d,``
- [x] In done Step 3 item 4a, replace ``ownership-scoping resolution test (`learn` Step 1.2 item 5c, anchored to the repo being audited)`` with ``ownership-scoping resolution test (`learn` Step 1.2 item 5d, anchored to the repo being audited)``
- [x] In the facts `Guideline canonical homes` paragraph, replace ``This is the test `learn` Step 1.2 item 5c and `done` Step 3 item 4a apply`` with ``This is the test `learn` Step 1.2 item 5d and `done` Step 3 item 4a apply``; this file is outside any git repository (verified 2026-09-14), so no commit step applies to it
- [x] Run → expect: every item 5d new-span gate and both cross-file fan-out gates pass, all preservation gates pass (the receipt-meaning 5c citations must not have been touched), and the bare item-2b gate stays green
- [x] Commit (learn and done only): `skills: promote ownership-scoping resolution test to learn item 5d`

### Task 5: full validation sweep

Files: none (gates only)

- [x] Run the complete Validation Commands block from the repo root → expect exit 0 with `ALL GATES GREEN`; on any failure, fix the offending span in the owning file and re-run the block
- [x] Run `git diff --name-only <session-base>..HEAD -- agents/skills/` (the base sha Task 1 recorded) → expect exactly `agents/skills/learn/SKILL.md` and `agents/skills/done/SKILL.md`; any further `agents/skills/` path in that diff belongs to a peer session: report it and leave it untouched, never stage or revert it
- [x] No commit; the validation task leaves the tree with the four task commits in place
