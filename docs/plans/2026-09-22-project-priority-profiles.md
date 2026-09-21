# Plan: Project-Priority Profiles (Per-Project Deferral Classes)

Backlog origin: `docs/history/backlog/2026-09-21-project-priority-profiles.md` (P39, HIGH, 1 origin; Source: user directive 2026-09-21). The origin item is the scope of record; its semantics are user-decided. This plan implements them.

## Terms

- **Priority profile**: the per-project block in the project facts document that declares `priority_order` (ranked finding priorities) and `deferred_classes` (deferral class slugs).
- **Deferral class**: a named class of findings a project defers by default; initial vocabulary `formal-hardening`, `security-hardening`, `prose-polish`.
- **Triage class (real vs formal)**: the pre-severity classification of a finding. Real means a witnessed failure, recovered wall-clock or token cost, or correctness of behavior. Formal means gates-on-gates, naming/wording/pin audits, vacuity checks, or hypothetical-input hardening.
- **Default profile**: the profile an unspecified project gets: the guidelines section 64 ordering plus formal-hardening defer-by-default.
- **Profile-aware grouping**: the maintenance survey and selection duty that batches backlog items into plan families respecting the project profile, recording each grouped item's class.

## Design Invariants (CR Guard)

- Guidelines section 64's global ordering is the fallback, never rewritten by this plan; a profile supersedes it for the declaring project only.
- Severity calibration (`review-agents/severity-calibration.md`) is untouched; the triage class routes findings, it never re-ranks them.
- The existing execute-plan Phase 3 two-class bound in receiving-review is referenced as precedent, not duplicated or contradicted.
- Backlog capture destinations are unchanged; formal findings use the existing capture rule with the class recorded in the item.
- No new scripts or validators: class assignment is judgment work, and section 64 ranks simplicity third (less mechanism wins).

## Assumptions

- assume the profile lives in the project facts document (`facts_path` from the facts TOML, `.ai-playbook/facts.md` default); basis: origin item "What it should become" #1 and the Source user directive 2026-09-21.
- assume the default profile is the section 64 ordering plus formal-hardening defer-by-default; basis: origin item #1 fallback sentence.
- assume `security-hardening` is a deferral class, not a severity lens: a security finding's severity calibrates normally, the class governs deferral routing only; basis: origin Source line (personal projects defer formal hardening AND security concerns) and item #4's fold-consultation asymmetry.
- assume this repo's own profile application is a local, uncommitted runtime change (facts.md is gitignored, session-verified), recorded under Ship when; basis: facts_path conventions.
- assume prose-only implementation in the four named surfaces; basis: the repo scripts-over-prose preference targets deterministic steps, and class assignment is judgment.

Decision points requiring a grill: profile-home resolved to per-repo facts document with the semantics SOT in guidelines rule 68 (origin item #1 plus user directive 2026-09-21; affects Assumptions and Task 1); default-profile resolved to section 64 ordering plus formal-hardening defer-by-default (origin item #1; affects Task 1 and Task 4); security-class resolved to deferral-class-not-lens with cross-fold consultation (origin Source line and item #4; affects Task 1 and Task 2); guidelines-64-interaction resolved to project-only supersession with the code-quality proviso carried (origin item #1 plus the committed 2026-09-12 amendment note in section 64; affects Task 1)

## Gist & Examples

Today, guidelines section 64 fixes one global principle ordering (efficiency, token usage, simplicity, code quality) and the triage, exit, and selection rules treat every valid finding as one severity-ranked queue. Nothing records that deferral classes are a per-project property: the same finding, a Low robustness pin or a defense-in-depth hardening suggestion, is defer-by-default on this personal repo and may be fix-by-default on a company repo. The judgment lives only in ad-hoc triage notes and user corrections.

Witnesses: the origin item records the P32/P33 formal triage (10 of 14 origins formal) and the 2026-09-11 security threat-model deferral; the committed section 64 amendment note (2026-09-12) records the same tension (the 2026-09-11 efficiency triage wrongly parked code-quality items); the 2026-09-21 formal-residual backlog batch that landed in 8719edff (8 items: pin, wording, and registry residuals) is a same-week formal-class family. The origin item's own P-number labels are attributed to the origin, not re-verified as corpus facts.

This plan adds four connected duties:

1. **Guidelines rule 68** (new, in `agent_workflow_guidelines.md`): the SOT for priority profiles. Where the profile lives (facts document), its schema, the default profile, the class vocabulary, the security-is-a-class rule, the section 64 interaction, and the consultation rule statement.
2. **receiving-review**: a `## Triage class (real vs formal)` section applied before severity ranking. Formal findings under a deferring profile route to deferred-backlog with the class and a one-line reason (the existing deferral-line convention), never folded at exit. Includes the cross-profile consultation rule.
3. **review-loop**: the one-iteration triage step applies the class before the fix-vs-defer decision.
4. **maintenance**: the survey resolves each open item's profile and class, skips profile-deferred items without re-triage (skip reason `profile-deferred`), and groups families profile-aware: formal-class findings never ride along as fillers in a real-fix batch under a personal profile.

Example (this repo, default-plus-declared profile): a review finding proposes hardening a validator against a hypothetical malformed input. Triage classifies it formal (hypothetical-input hardening) before severity. Under this repo's profile (`deferred_classes: [formal-hardening, security-hardening]`), it routes to Backlog capture with class `formal-hardening` and a one-line reason instead of being fixed inline or folded at exit. The next maintenance survey records its class and skips it with `profile-deferred`, so it stops re-appearing as plan-uncovered queue pressure.

Example (company profile): a project declares `deferred_classes: []` (or omits deferral of security) and a triage would still defer a security finding; the consultation rule surfaces that disposition to the user instead of deciding silently.

## Evaluation Criteria

**Quality dimensions:**
- correctness: class definitions are faithful to the origin item's wording; section 64 text outside the new rule is unmodified.
- integration symmetry: the provider/consumer rows exist in both directions and name each peer's actual section headings (verified against the files, not assumed).
- gate strength: every duty above is pinned by a dedicated fail-closed grep in Validation Commands; the block passes `bash -n`; the pins are RED on the pre-task tree and GREEN only after the tasks land.
- scope discipline: only the four must-fix files change; no authoring-session constraints leak into the plan surfaces.

**Done when:**
- `python3 scripts/plan_readiness.py docs/plans/2026-09-22-project-priority-profiles.md` exits 0 on the final bytes.
- Every Validation Commands gate exits 0 on the post-task tree.
- The repo's no-em-dash scan and public hygiene scan exit 0 over the touched paths.

**Ship when:**
- [class: OPERATIONS_FOLLOW_UP] Apply this repo's personal profile (declared `deferred_classes: [formal-hardening, security-hardening]`, default `priority_order`) to the local gitignored `.ai-playbook/facts.md` under a `## Priority profile` heading. Evidence owner: the user's runtime sessions on this host. Closure condition: the profile block is present in the local facts document and the next maintenance survey records skip reason `profile-deferred` for formal items. This is a runtime fact-document change, not a committed repository artifact; it cannot ride the plan's commit by design.

## Review Scope

**Explicit must-fix**; findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `projects/.ai-playbook/agent_workflow_guidelines.md` (new rule 68 appended after rule 67)
- `agents/skills/receiving-review/SKILL.md` (new section before `## Triage Decision Rule`; Integration Points rows)
- `agents/skills/review-loop/SKILL.md` (One iteration step 2 row; Consumes `receiving-review` row)
- `agents/skills/maintenance/SKILL.md` (Step 1 survey bullet; D2 selection addition)

**Tests:**
- none; prose-and-workflow surfaces are gated by the Validation Commands greps.

**Plan-related extension**; implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `README.md`; no skill catalog change (no new skills, no renames).
- `docs/maintenance/document-registry.md`; no new document is created.
- `agents/skills/maintenance/prompt-templates.md`; child payloads are unchanged (the survey output and state decision fields carry the class, not the prompt text).
- `agents/skills/review-agents/severity-calibration.md`; severity is untouched by design.
- `.ai-playbook/facts.md`; gitignored runtime document, covered by the Ship when operations follow-up.

## Validation Commands

```bash
REPO="$(git rev-parse --show-toplevel)"
G="$REPO/projects/.ai-playbook/agent_workflow_guidelines.md"
RR="$REPO/agents/skills/receiving-review/SKILL.md"
RL="$REPO/agents/skills/review-loop/SKILL.md"
M="$REPO/agents/skills/maintenance/SKILL.md"
for f in "$G" "$RR" "$RL" "$M"; do
  [ -f "$f" ] || { echo "FAIL missing must-fix file: $f"; exit 1; }
done

# G1: guidelines rule 68 (each obligation its own dedicated grep)
grep -qF '## 68. Project-Priority Profiles: Per-Project Deferral Classes' "$G" \
  || { echo "FAIL G1a rule 68 heading absent"; exit 1; }
grep -qF 'priority_order' "$G" \
  || { echo "FAIL G1b priority_order absent"; exit 1; }
grep -qF 'deferred_classes' "$G" \
  || { echo "FAIL G1c deferred_classes absent"; exit 1; }
grep -qF 'formal-hardening defer-by-default' "$G" \
  || { echo "FAIL G1d default profile absent"; exit 1; }
grep -qF 'a deferral class, not a severity lens' "$G" \
  || { echo "FAIL G1e security-class rule absent"; exit 1; }
grep -qF 'supersedes the section 64 ranking for that project only' "$G" \
  || { echo "FAIL G1f section 64 supersession absent"; exit 1; }
grep -qF 'consulted with the user each time rather than decided silently' "$G" \
  || { echo "FAIL G1g consultation statement absent"; exit 1; }
grep -qF 'prose-polish' "$G" \
  || { echo "FAIL G1h class vocabulary absent"; exit 1; }
grep -qF '## Priority profile' "$G" \
  || { echo "FAIL G1i facts block heading absent"; exit 1; }
grep -qF '2026-09-12 amendment note in section 64' "$G" \
  || { echo "FAIL G1j witnesses sentence absent"; exit 1; }
grep -qF 'defaults to the section 64 principle ordering' "$G" \
  || { echo "FAIL G1k priority_order default typing absent"; exit 1; }
grep -qF 'folding a security or correctness finding on a personal-profile project' "$G" \
  || { echo "FAIL G1l consultation fold direction absent"; exit 1; }

# G2: receiving-review triage class section
grep -qF '## Triage class (real vs formal)' "$RR" \
  || { echo "FAIL G2a triage class section absent"; exit 1; }
grep -qF 'before severity ranking' "$RR" \
  || { echo "FAIL G2b before-severity ordering absent"; exit 1; }
grep -qF 'with its class and a one-line deferral reason' "$RR" \
  || { echo "FAIL G2c formal deferral routing absent"; exit 1; }
grep -qF 'never folded at exit' "$RR" \
  || { echo "FAIL G2d no-fold-at-exit absent"; exit 1; }
grep -qF 'A blocking formal finding is never silently backlogged' "$RR" \
  || { echo "FAIL G2e blocking parity absent"; exit 1; }
grep -qF 'Consultation rule (cross-profile dispositions)' "$RR" \
  || { echo "FAIL G2f consultation rule absent"; exit 1; }
grep -qF 'a witnessed failure, recovered wall-clock or token cost' "$RR" \
  || { echo "FAIL G2g real-class definition absent"; exit 1; }
grep -qF 'vacuity checks, or hypothetical-input hardening' "$RR" \
  || { echo "FAIL G2h formal-class definition absent"; exit 1; }

# G3: review-loop integration
grep -qF 'classify each finding real vs formal per receiving-review' "$RL" \
  || { echo "FAIL G3a iteration step class duty absent"; exit 1; }
grep -qF 'before the fix-vs-defer decision' "$RL" \
  || { echo "FAIL G3b consumer row class duty absent"; exit 1; }

# G4: maintenance survey and selection
grep -qF 'Priority profile resolution' "$M" \
  || { echo "FAIL G4a survey profile resolution absent"; exit 1; }
grep -qF 'profile-deferred' "$M" \
  || { echo "FAIL G4b profile-deferred skip absent"; exit 1; }
grep -qF 'never ride along as fillers in a real-fix batch' "$M" \
  || { echo "FAIL G4c grouping duty absent"; exit 1; }
grep -qF 'the class of every item it groups' "$M" \
  || { echo "FAIL G4d class audit recording absent"; exit 1; }
grep -qF 'class=<real|formal>' "$M" \
  || { echo "FAIL G4e per-item class token form absent"; exit 1; }

# G5: integration symmetry (both directions)
grep -qF '### With `maintenance` skill' "$RR" \
  || { echo "FAIL G5a receiving-review maintenance row absent"; exit 1; }
grep -qF 'Triage class (real vs formal)' "$M" \
  || { echo "FAIL G5b maintenance names the provider section absent"; exit 1; }

echo "validation: all gates green"
```

Rule 15 note: every gate above is a positive-presence pin over one of the four must-fix files; none sweeps this plan file, so no self-match escape is needed.

### Task 1: Guidelines rule 68 (profile semantics SOT)

Files:
- `projects/.ai-playbook/agent_workflow_guidelines.md` *(append at end of file, after the rule 67 block)*

- [ ] Append a new section with heading exactly `## 68. Project-Priority Profiles: Per-Project Deferral Classes`, containing in order: [class: IMPLEMENTATION_REQUIRED]
  - The profile home paragraph: each project's facts document carries the profile under a `## Priority profile` heading with two keys, `priority_order` (ranked list of finding priorities for that project) and `deferred_classes` (list of class slugs, initial vocabulary `formal-hardening`, `security-hardening`, `prose-polish`; a project may declare others).
  - The default-profile sentence, containing verbatim: an unspecified project falls back to the section 64 ordering with `formal-hardening defer-by-default`; the profile's `priority_order` `defaults to the section 64 principle ordering` (efficiency, token usage, simplicity, code quality).
  - The security rule sentence, containing verbatim: `security-hardening` is `a deferral class, not a severity lens`; a security finding's severity calibrates normally and the class governs deferral routing only.
  - The section 64 interaction sentence, containing verbatim: a declared `priority_order` `supersedes the section 64 ranking for that project only`; section 64 stays the fallback, and its code-quality proviso carries (a deferral whose cost is real code quality records that cost in the deferral line).
  - The consultation statement, containing verbatim: on a company-profile project, priority conflicts that would defer security or correctness findings are `consulted with the user each time rather than decided silently`, and the mirror case, `folding a security or correctness finding on a personal-profile project`, is consulted the same way (the SOT statement; Task 2 operationalizes both directions).
  - The witnesses sentence, containing verbatim: the origin backlog item and the `2026-09-12 amendment note in section 64` are the rule's witnesses.
- [ ] Run the G1 gate lines of Validation Commands → expect GREEN for G1a-G1l; G2-G5 still RED at this task point. [class: REPOSITORY_TEST]
- [ ] Commit: `guidelines: project-priority profile rule 68 (deferral classes as a project property)` [class: IMPLEMENTATION_REQUIRED]

### Task 2: receiving-review triage class and consultation

Files:
- `agents/skills/receiving-review/SKILL.md`

- [ ] Insert a new section `## Triage class (real vs formal)` immediately before the `## Triage Decision Rule` heading, containing: [class: IMPLEMENTATION_REQUIRED]
  - The ordering duty: classify each finding real or formal `before severity ranking`; real means `a witnessed failure, recovered wall-clock or token cost`, or correctness of behavior; formal means gates-on-gates, naming/wording/pin audits, `vacuity checks, or hypothetical-input hardening`.
  - The routing duty: a formal finding under a profile whose `deferred_classes` includes `formal-hardening` (including the default profile) routes to **Backlog capture** `with its class and a one-line deferral reason` per the existing deferral-line convention, `never folded at exit`.
  - The bound sentence: this section bounds **Address every review finding by default** the same way the existing execute-plan Phase 3 two-class bound does in the section above; `A blocking formal finding is never silently backlogged`, it follows the blocking re-evaluation procedure of **Fix-risk triage when fixes regenerate findings**.
  - The paragraph `Consultation rule (cross-profile dispositions):` deferring a security or correctness finding on a company-profile project, or folding one on a personal-profile project, is surfaced to the user instead of decided silently; in a non-interactive run record it returned-for-ask per review-staging's receiving-review consumer row (the convention receiving-review's own returned-for-ask references point at).
- [ ] Extend `## Integration Points`: add a `### With \`maintenance\` skill` row (the maintenance survey resolves each open item's profile and class per this section and groups families profile-aware), and extend the existing `### With \`review-loop\` skill` row with one sentence: the loop's triage step applies **Triage class (real vs formal)** before the fix-vs-defer decision. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the G2 and G5a gate lines → expect GREEN for G2a-G2h and G5a; G3, G4, G5b still RED at this task point. [class: REPOSITORY_TEST]
- [ ] Commit: `receiving-review: real vs formal triage class before severity (profile-aware deferral routing, consultation rule)` [class: IMPLEMENTATION_REQUIRED]

### Task 3: review-loop integration

Files:
- `agents/skills/review-loop/SKILL.md`

- [ ] In the `## One iteration` table, extend step 2 (Triage) so the row contains verbatim: `classify each finding real vs formal per receiving-review` followed by the section name **Triage class (real vs formal)** and `before severity ranking`. [class: IMPLEMENTATION_REQUIRED]
- [ ] In the `### Consumes \`receiving-review\` skill` row, add one sentence containing verbatim: the step-3 triage pass applies the class step `before the fix-vs-defer decision`, and formal findings follow the class routing instead of the fix-everything default. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the G3 gate lines → expect GREEN for G3a-G3b; G4, G5b still RED at this task point. [class: REPOSITORY_TEST]
- [ ] Commit: `review-loop: apply real vs formal triage class in the iteration triage step` [class: IMPLEMENTATION_REQUIRED]

### Task 4: maintenance survey class recording and profile-aware grouping

Files:
- `agents/skills/maintenance/SKILL.md`

- [ ] In `### Step 1: survey`, add a bullet after the Open backlog items bullet, led by the exact phrase `Priority profile resolution:`, containing: [class: IMPLEMENTATION_REQUIRED]
  - Read the facts document's `## Priority profile` block per guidelines rule 68; when absent, use the default profile.
  - For each open backlog item, record in the survey output the item's priority group per the profile's `priority_order` and the item's class, judged real or formal per the receiving-review `## Triage class (real vs formal)` section, in the token form `<backlog-item-basename>:class=<real|formal>` carried by the turn's decision_reason summary strings (the survey output's persistent record home; no state-schema change); the survey records `the class of every item it groups`, so a plan's origin list is auditable against the profile.
  - An item whose class is in the profile's `deferred_classes` is recorded with skip reason `profile-deferred` and is not re-triaged on later turns, the same shape as the survey's other recorded skip reasons.
- [ ] In the `D2 (author)` decision, add: selection excludes items recorded with skip reason `profile-deferred` (no re-triage on later turns; the survey's skip-reason recording is the audit trail for the exclusion, the same shape as its other recorded skip reasons), highest-priority reads the profile's `priority_order` (default: the section 64 principle ordering), and the family-grouping duty: under a personal profile, formal-class findings `never ride along as fillers in a real-fix batch`; a company-profile project may batch hardening items a personal profile defers; the survey's per-item class is the audit trail for any plan origin list. [class: IMPLEMENTATION_REQUIRED]
- [ ] Run the G4 and G5b gate lines → expect GREEN; the full Validation Commands block now exits 0 end to end. [class: REPOSITORY_TEST]
- [ ] Commit: `maintenance: profile-resolved survey classes, profile-deferred skip, profile-aware grouping` [class: IMPLEMENTATION_REQUIRED]

### Task 5: full validation and certification sweep

Files:
- none new; verification only.

- [ ] Run the entire Validation Commands block → expect exit 0 with `validation: all gates green`. [class: REPOSITORY_TEST]
- [ ] Run `bash -n` over the Validation Commands block → expect exit 0. [class: REPOSITORY_TEST]
- [ ] Run `bash scripts/check-no-em-dash.sh touched` from the repo root → expect exit 0. [class: REPOSITORY_TEST]
- [ ] Run the public hygiene scan (`bash scripts/scan-public-hygiene.sh` from the repo root) → expect exit 0. [class: REPOSITORY_TEST]
- [ ] Run `python3 scripts/plan_readiness.py docs/plans/2026-09-22-project-priority-profiles.md` → expect exit 0 after the review loop closes with a matching sidecar digest. [class: REPOSITORY_TEST]
- [ ] Commit any residual wording fixes from this sweep: `plans: priority-profiles validation sweep fixes` (skip when nothing changed). [class: IMPLEMENTATION_REQUIRED]
