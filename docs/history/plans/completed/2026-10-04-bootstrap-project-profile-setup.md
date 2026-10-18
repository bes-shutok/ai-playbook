# Plan: bootstrap-ai-playbook project-profile setup interview

Backlog origin: none
Driving force: new-capability
Plan review record: the staging series docs/reviews/2026-10-04-plan-review-bootstrap-project-profile-setup-r*.md (the highest rN is the authoritative record, including any deferred-residual list)

## Outcome

A bootstrap run sets up the project profile surfaces a target repo's `.ai-playbook/facts.md` is missing: worktree placement, project class and ownership status, and the priority profile, so run-policy config is explicit and operator-confirmed instead of silent defaults.

- On a repo whose facts lack the profile surfaces, one bootstrap run asks about exactly the missing surfaces, confirms the full effective profile in one batch pass, and persists the confirmed values.
- A declined or unanswered interview persists nothing, so every absent-key default in the consumer skills keeps its exact current meaning.
- The company-vs-pet answer and the priority profile become recorded facts a future session can read instead of re-deriving or guessing.
- The silent persistence arm for `project_class` on company-scoped repos is removed; the interview's status ask becomes its only writer, so the class value is always operator-confirmed.
- No consumer reading semantics change: execute-plan, plans, done, maintenance, and receiving-review read the same keys and blocks they read today; the single consumer-file edit is the using-skills Step 0 dispatcher sync that names the new trigger, without which the interview never fires on healthy-facts repos.

Gate delta: adds two ask-family entries, the profile interview (three profile surfaces, per-surface persist, one batch-confirm pass) and its worktree_root arm, inside bootstrap's existing ask machinery; priced by their paying sibling arms, the greenfield layout ask and the backlog-home ask (same trigger machinery, same once-per-session-per-family budget, same decline-persists-nothing posture). Schema growth is optional TOML keys plus one prose block convention under the existing opening-fence parse rule; no new fence, refusal class, hard gate, or protocol layer. Removals: one, the Path Discovery company-scoped silent `project_class` auto-persist arm, deleted because its role moves into the interview's status ask as the interview-recommended default (the silent write is the concrete removal; without it the plan would create two writers for one key on every company-scoped repo).

## Terms

- **Profile surface**: one of the three setup subjects: worktree placement (keys `worktree_policy`, `worktree_root`), project class and ownership status (key `project_class` plus an ownership prose line), priority profile (the `## Priority profile` prose block).
- **Profile interview**: the ask flow bootstrap runs for the profile surfaces: individual asks for missing surfaces, then one batch-confirm pass over the full effective profile.
- **Effective value**: what a consumer resolves for a surface today: the persisted value when present, else the documented absent-key default.
- **Ask budget**: each bootstrap ask family (greenfield layout, backlog home, profile interview, the `worktree_root` arm) holds its own once-per-session entry; one family's decline never suppresses another family's ask; a declined or unanswered ask consumes only its own family's entry.

## Assumptions

- assume `bootstrap-ai-playbook` is the home skill and `doc-hierarchy` stays read-only (it receives only an Integration-Points row sync); basis: doc-hierarchy family table reserves writes to doc-hierarchy-migrate, bootstrap owns facts.md writes, confirmed in the grill tail batch 2026-10-04.
- assume the skills that read the three surfaces stay byte-untouched (execute-plan, plans, done, maintenance, receiving-review); using-skills joins the change set as the dispatcher contract sync, not a reading change: its Step 0 trigger enumeration must name the new trigger or the interview never fires on healthy-facts repos; basis: the reading surfaces cited at grill Q3 and Q5 2026-10-04, plus review r2 F1 (four-worker echo) for the dispatcher sync.
- assume the runtime skills directory symlinks into this repository, so a landed skill edit is live with no vendored-sync step; basis: on-disk check 2026-10-04, the runtime skills directory resolves into this repo. Note for the executor: the skill text itself stays path-free.
- assume the priority profile block reuses the existing shape (`priority_order`, `deferred_classes` bullets) and the maintenance skill's documented default profile as the presented default; basis: maintenance SKILL.md profile-resolution paragraph (the default defers formal-hardening only) and this repo's own facts.md block, which is a declared personal profile, not the default.
- assume the interview composes with, and never duplicates, the greenfield layout ask and the backlog-home ask; the three ask families keep separate once-per-session entries; basis: bootstrap SKILL.md greenfield and recovery-rerun rules.
- assume this plan does not include running the interview against this repository; after landing, the next bootstrap trigger here offers it naturally (this repo's facts already carry a Priority profile block, so only the two missing surfaces would be asked); basis: grill tail batch 2026-10-04.

Decision points requiring a grill: scope membership (three policy surfaces: worktree placement, project class/status, priority profile): user answer, grill Q2, 2026-10-04, Scope and Tasks; worktree vocabulary (existing two values, no consumer-semantics change): user answer, grill Q3, 2026-10-04, Scope OUT; interview shape (trigger-driven, ask missing individually, batch-confirm shows all effective values including defaults): user answers Q4 plus tail refinement, 2026-10-04, Task 1; ownership modeling (persist `project_class` only, ownership as prose): user answer, grill Q5, 2026-10-04, Task 1; tail batch (home skill, no apply-here task, existing profile block shape, `worktree_root` only when policy is `worktrees`): user acceptance, 2026-10-04, Files and Scope.

## Gist & Examples

TLDR: bootstrap gains a project-profile setup interview, worktree placement, project class and ownership status, priority profile, so repos carry explicit confirmed run-policy config instead of silent defaults; new-capability force.

Today a fresh repo's facts.md carries only the doc-path keys. `worktree_policy` absent means the Worktree-first standard's unconfigured resolution (ordinary work in the primary checkout, plan lanes in worktrees); `project_class` absent means derivation at read time from the user facts' company root or the `default-branch-integration` default, except on company-scoped repos, where bootstrap's Path Discovery rule persists `checkout-flow` silently during discovery today, the silent arm this plan removes; a missing `## Priority profile` block means maintenance's built-in default. Operators hand-add the remaining keys when they care; this repo's own facts.md shows the pattern. After this plan, the bootstrap trigger machinery notices the missing surfaces, asks about them once per session with recommended answers, shows the whole resolved profile for one confirming pass, and persists what was confirmed.

Example facts.md after a confirmed interview on a pet repo that opts into worktrees:

````markdown
```toml
plans_dir = "docs/history/plans/"
# ...doc-path keys as today...
worktree_policy = "worktrees"
project_class = "default-branch-integration"
```

## Priority profile

Profile confirmed by the bootstrap project-profile interview 2026-10-04 (pet project).

- priority_order: default (efficiency, token usage, simplicity, code quality)
- deferred_classes: [formal-hardening]
````

The example's `deferred_classes` is the documented default (formal-hardening only; security-hardening is an operator-added class, not part of the default). A repo whose operator declines every surface, or a non-interactive run where the ask goes unanswered, keeps today's bytes: no profile keys, no block, all absent-key defaults applying.

## Evaluation Criteria

**Quality dimensions:**
- Correctness: the persisted facts.md parses under the existing opening-fence rule; `worktree_policy` carries only `worktrees` or `primary`; `project_class` carries only `default-branch-integration` or `checkout-flow`; the `## Priority profile` block matches the shape maintenance's profile-resolution paragraph reads; prose outside the owned block is preserved byte-for-byte by the atomic merge.
- Compatibility: the five reading consumers stay byte-untouched (execute-plan, plans, done, maintenance, receiving-review); the only consumer-side edit is the using-skills Step 0 dispatcher contract sync; with every profile surface absent or declined, no consumer resolves anything differently.
- Usability: at most one profile interview per session; a decline persists nothing and consumes only the interview's own ask-family entry; the batch-confirm pass shows every surface's effective value, persisted or defaulted, overridable in one pass.
- Portability: the skill text stays tool-agnostic and free of personal paths; the hygiene scan exits 0.

**Done when:**
- All task checklists complete on `agents/skills/bootstrap-ai-playbook/SKILL.md`, `agents/skills/doc-hierarchy/SKILL.md`, `agents/skills/using-skills/SKILL.md`, and `README.md`.
- The full Validation Commands block exits 0.
- Hygiene scan exit 0, no-em-dash added-lines clean over the branch's own diff window, readiness validator pre-round `OUTCOME: pass`.
- One fresh blocking-clean review round over the final digest.

**Ship when:** no external gates; the runtime picks the change up through the existing skills symlink at landing.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/doc-hierarchy/SKILL.md`
- `agents/skills/using-skills/SKILL.md`
- `README.md`

**Tests:** none; the deliverable is skill specification text validated by the grep and gate probes in Validation Commands.

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `agents/skills/execute-plan/SKILL.md`, `agents/skills/maintenance/SKILL.md`, `agents/skills/receiving-review/SKILL.md`, `agents/skills/plans/SKILL.md`, `agents/skills/done/SKILL.md`; reason: consumers stay byte-untouched by design (grill Q3 and Q5, 2026-10-04); a finding there is a separate concern, and the primary-checkout execution gap has its own origin, `docs/history/backlog/2026-10-04-execute-plan-primary-checkout-policy.md`.
- `.ai-playbook/facts.md`; reason: gitignored runtime output of the skill, never a repository implementation artifact.

## Validation Commands

Probes F0-F6 and F12-F13 scope their greps to the new interview section extracted with a fail-closed anchor; probes F7-F11 and F14-F16 pin needles that exist only after the change (each needle occurs exactly once in the task text that prescribes it, checked once per owning surface where two surfaces mirror one phrase); probes F24-F26 pin the trigger-routing chain across both surfaces (the using-skills enumeration, the bootstrap trigger-list entry, and the using-skills no-op qualification). The consumer-untouched and formatting gates (F17-F21) diff from the merge-base window, the branch's own added lines only, immune to base-tip divergence; that window choice and the r1 re-anchor fold are recorded here (2026-10-04).

```bash
set -e
cd "$(git rev-parse --show-toplevel)"

# 0. Interview section extraction with fail-closed anchor
SECTION="$(awk '/^## Project profile setup$/{f=1;next} /^## /{f=0} f' agents/skills/bootstrap-ai-playbook/SKILL.md)"
test -n "$SECTION" || { echo "F0 interview section missing or empty"; exit 1; }

# 1. Interview section obligations (needles exist only inside the new section)
printf '%s' "$SECTION" | grep -qF "its own once-per-session entry" || { echo "F1 missing per-family ask budget"; exit 1; }
printf '%s' "$SECTION" | grep -qF "records the open profile ask" || { echo "F2 missing non-interactive posture"; exit 1; }
printf '%s' "$SECTION" | grep -qF "persists nothing for a declined surface" || { echo "F3 missing decline posture"; exit 1; }
printf '%s' "$SECTION" | grep -qF "default-branch-integration" || { echo "F4 missing integration value"; exit 1; }
printf '%s' "$SECTION" | grep -qF "checkout-flow" || { echo "F5 missing checkout-flow value"; exit 1; }
printf '%s' "$SECTION" | grep -qF "only when the confirmed placement is worktrees" || { echo "F6 missing worktree_root conditionality"; exit 1; }

# 2. Structural amendments outside the section (needles unique to the amended paragraphs)
grep -qF "profile-interview ask" agents/skills/bootstrap-ai-playbook/SKILL.md || { echo "F7 missing recovery-rerun exception extension"; exit 1; }
grep -qF "instead of the no-op stop" agents/skills/bootstrap-ai-playbook/SKILL.md || { echo "F8 missing no-op amendment"; exit 1; }
grep -qF "interview-recommended default" agents/skills/bootstrap-ai-playbook/SKILL.md || { echo "F9 missing company-rule amendment"; exit 1; }
grep -qF "profile keys ride" agents/skills/bootstrap-ai-playbook/SKILL.md || { echo "F10 missing persist amendment"; exit 1; }
grep -qF "peer-persisted profile value" agents/skills/bootstrap-ai-playbook/SKILL.md || { echo "F11 missing owned-region reconciliation"; exit 1; }

# 3. Priority profile block shape matches the maintenance reader's expectations
printf '%s' "$SECTION" | grep -qF "priority_order" || { echo "F12 missing priority_order"; exit 1; }
printf '%s' "$SECTION" | grep -qF "deferred_classes" || { echo "F13 missing deferred_classes"; exit 1; }

# 4. Bidirectional integration sync: bootstrap names the new consumption; doc-hierarchy names the interview
grep -qF "worktree placement keys" agents/skills/bootstrap-ai-playbook/SKILL.md || { echo "F14 missing integration rows extension"; exit 1; }
grep -qF "project-profile" agents/skills/doc-hierarchy/SKILL.md || { echo "F15 missing doc-hierarchy sync"; exit 1; }
grep -qF "project-profile" README.md || { echo "F16 missing README sync"; exit 1; }
grep -qF "missing-profile-surface trigger" agents/skills/using-skills/SKILL.md || { echo "F24 missing dispatcher sync"; exit 1; }
grep -qF "missing-profile-surface trigger" agents/skills/bootstrap-ai-playbook/SKILL.md || { echo "F25 missing bootstrap trigger-list entry"; exit 1; }
grep -qF "routes into the interview" agents/skills/using-skills/SKILL.md || { echo "F26 missing no-op qualification"; exit 1; }

# 5. Consumer-untouched invariant over the branch's own diff window, fail-closed on git failure
BASE="$(git merge-base main HEAD)" || { echo "F17 base resolution failed"; exit 1; }
DIFFLIST="$(mktemp)"
git diff --name-only "${BASE}..HEAD" > "$DIFFLIST" || { echo "F18 diff failed"; rm -f "$DIFFLIST"; exit 1; }
if grep -qE "agents/skills/(execute-plan|maintenance|receiving-review|plans|done)/" "$DIFFLIST"; then echo "F19 consumer file touched"; rm -f "$DIFFLIST"; exit 1; fi
if grep -qF "docs/history/backlog/2026-10-04-execute-plan-primary-checkout-policy.md" "$DIFFLIST"; then echo "F20 backlog origin touched"; rm -f "$DIFFLIST"; exit 1; fi
rm -f "$DIFFLIST"

# 6. Formatting and readiness gates over the same window
bash scripts/check-no-em-dash.sh added-lines --base "$BASE" || { echo "F21 em-dash hit"; exit 1; }
bash scripts/scan-public-hygiene.sh || { echo "F22 hygiene hit"; exit 1; }
python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-04-bootstrap-project-profile-setup.md || { echo "F23 readiness hit"; exit 1; }
```

Authoring-time RED-today record (2026-10-04, after the r3 fold): the block is fail-fast, so the whole-block run stops at its first failing gate, F0 (interview section absent, exit 1); the remaining reds are verified by individual execution: F1-F16 red (F5 because the section extract is empty, its checkout-flow needle existing elsewhere in the file today; F16 because the README needle is absent), F24-F26 red by their absent dispatcher and trigger-chain needles; F17-F23 verified green by individual execution (the merge-base window contains only the plan file, which is em-dash clean, hygiene-clean, and readiness-clean).

### Task 1: Profile interview and persistence in bootstrap-ai-playbook

Files:
- `agents/skills/bootstrap-ai-playbook/SKILL.md`

Evidence:
- `test -n "$SECTION"` over the extracted interview section (Validation Commands F0); covers the interview section obligation (F0)
- `printf '%s' "$SECTION" | grep -qF "its own once-per-session entry"`; covers the per-family ask budget obligation (F1)
- `printf '%s' "$SECTION" | grep -qF "only when the confirmed placement is worktrees"`; covers the worktree_root conditionality obligation (F6)
- `grep -qF "interview-recommended default" agents/skills/bootstrap-ai-playbook/SKILL.md`; covers the company-rule supersession obligation (F9)

- [x] Add a `## Project profile setup` section (executed 2026-10-04; F0-F6, F12-F13 GREEN) placed between Path Discovery and Implementation Workflow, carrying: the trigger rule (runs within any bootstrap run when a profile surface is missing, at most once per session, each ask family holding its own once-per-session entry; the trigger tests surfaces, not individual keys: the status surface is satisfied by the persisted `project_class` key alone, the ownership prose line rides the Priority block's provenance and is not part of the trigger test, and a persisted placement satisfies the placement surface even when `worktree_root` stays absent by sanctioned empty answer); the three surfaces with their vocabularies; the individual-ask shapes with one recommended answer each (placement: present `worktrees` and `primary` as one-line intent summaries, worktrees meaning ad-hoc worktrees are allowed for warranted runs and primary meaning ordinary work stays in the primary checkout with named lanes stopping for operator direction, plus a pointer to the Worktree-first standard policy paragraph for full semantics, plus leave-unconfigured; status: company-owned vs pet, recommended from the `company_projects_root` resolution when it resolves, pet otherwise, presenting `default-branch-integration` and `checkout-flow` and persisting the confirmed value, plus an ownership prose line only when the Priority profile surface is also confirmed (a declined block leaves the confirmed `project_class` key alone carrying the status fact); priority profile: present the default profile, which defers formal-hardening only, and persist the block on confirm); the batch-confirm pass rendering every surface's effective value, persisted or defaulted, overridable in one pass; the decline and non-interactive postures (persists nothing for a declined surface, consuming only the interview's own ask-family entry; an unanswered ask in a non-interactive run records the open profile ask and persists nothing, mirroring the greenfield rule; a declined interview re-offers on a later bootstrap trigger in a later session as a deliberate bounded posture: per-surface declines leave those surfaces missing, so the trigger keeps firing for them; a full confirmation resolves the trigger exactly as the greenfield ask's does; and a persistent decline latch stays out of this plan) [class: IMPLEMENTATION_REQUIRED]
- [x] Add the `worktree_root` arm (executed 2026-10-04; F6 GREEN): asked only when the confirmed placement is worktrees; an empty answer persists no key and the Worktree-first standard's fallback location rule applies [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the When-to-Use no-op paragraph (executed 2026-10-04; F8 GREEN) so a missing profile surface routes into the interview section instead of the no-op stop [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the Recovery-rerun exception enumeration (executed 2026-10-04; F7 GREEN) with the profile-interview ask awaiting the user, so the record-the-open-ask posture classifies as a re-ask-once-per-session case rather than a validation failure [class: IMPLEMENTATION_REQUIRED]
- [x] Amend the Path Discovery company-scoped rule (executed 2026-10-04; F9 GREEN): delete the silent `project_class` persist; the company resolution feeds the interview's status ask as the interview-recommended default instead [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the When to Use trigger list (executed 2026-10-04; F25 GREEN) with the missing-profile-surface trigger, marked as routing into the interview section rather than rerunning discovery [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the optional keys table (executed 2026-10-04; three rows added) with `worktree_policy`, `worktree_root`, and `project_class` rows: the same vocabularies the status and placement asks present, persist-on-confirm hint, and the note that absence keeps the documented consumer defaults [class: IMPLEMENTATION_REQUIRED]
- [x] Specify the `## Priority profile` block shape (executed 2026-10-04; F12/F13 GREEN, prose-only spec) bootstrap persists: the two bullet keys `priority_order` and `deferred_classes` matching the maintenance reader's expectations, plus a provenance prose line naming the interview date and, when the status ask was confirmed, the ownership answer (a status-declined run records the date alone; a run where the status surface is already satisfied preserves the block's existing ownership line unchanged); the in-section block-shape specification is prose or inline code only, never a fenced example whose lines start with a heading, the full fenced example staying in Facts File Shape per the example bullet above; existing block content is refreshed only through an explicit confirmed answer, never silently [class: IMPLEMENTATION_REQUIRED]
- [x] Amend Step 4 Persist (executed 2026-10-04; F10/F11 GREEN): profile keys ride the single atomic re-read-before-write merge, with the peer-value reconciliation, the prose compose, and the mv inside one shell invocation reading the live file state; a peer-persisted profile value or block present at persist time and authored by another session is reported and the ask re-offered once (the residual single-invocation collision window is the documented baseline posture of the atomic-replace pattern); the interview owns the Priority profile block region and only its keys, all other prose preserved unchanged [class: IMPLEMENTATION_REQUIRED]
- [x] Update the Facts File Shape example (executed 2026-10-04; interview-output keys and block added) to include one persisted profile key set and the block, values marked as interview outputs rather than defaults [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: add project-profile setup interview to bootstrap-ai-playbook` (a984e8f7, amended with F10 fix) [class: IMPLEMENTATION_REQUIRED]

### Task 2: Integration and catalog sync

Files:
- `agents/skills/bootstrap-ai-playbook/SKILL.md`
- `agents/skills/doc-hierarchy/SKILL.md`
- `agents/skills/using-skills/SKILL.md`
- `README.md`

Evidence:
- `grep -qF "worktree placement keys" agents/skills/bootstrap-ai-playbook/SKILL.md`; covers the integration rows extension obligation (F14)
- `grep -qF "project-profile" agents/skills/doc-hierarchy/SKILL.md`; covers the doc-hierarchy sync obligation (F15)
- `grep -qF "project-profile" README.md`; covers the README sync obligation (F16)

- [x] Extend the bootstrap Integration Points table (executed 2026-10-04; claims verified against execute-plan:237/360, done:64, plans:44, maintenance:70, receiving-review:198; F14 GREEN): `execute-plan`, `plans`, `done` consume the persisted worktree placement keys per the Worktree-first standard policy paragraph; `maintenance` and `receiving-review` consume the persisted `## Priority profile` block; verify each claim against the peer skill's actual steps before writing the row [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the doc-hierarchy Integration Points bootstrap row (executed 2026-10-04; F15 GREEN) to name the project-profile interview (placement, class and ownership status, priority profile) so the family table and the provider row agree [class: IMPLEMENTATION_REQUIRED]
- [x] Extend the README catalog row description (executed 2026-10-04; F16 GREEN) for `bootstrap-ai-playbook` with the profile setup in one clause naming the project-profile interview [class: IMPLEMENTATION_REQUIRED]
- [x] Sync using-skills Step 0 (executed 2026-10-04; F24/F26 GREEN): enumerate the missing-profile-surface trigger alongside the five existing bootstrap triggers and qualify the fresh-file no-op so it routes into the interview instead of the no-op stop [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `docs: sync project-profile interview across bootstrap, doc-hierarchy, using-skills, README` (34900a99, amended with F10 fix; pre-amend b7e5e5e4) [class: IMPLEMENTATION_REQUIRED]

### Task 3: Validation and formatting gates

Files:
- the round's review staging record under the resolved reviews directory (output home for the recorded gate results); verification only

Evidence:
- `bash scripts/check-no-em-dash.sh added-lines --base "$BASE"`; covers the added-lines formatting gate over the branch's own diff window (F21)
- `python3 scripts/plan_readiness.py --pre-round docs/history/plans/2026-10-04-bootstrap-project-profile-setup.md`; covers the structural readiness gate (F23)

- [x] Run the full Validation Commands block (executed 2026-10-04; ALL-GATES-GREEN, exit 0) from the repository root; expect every probe green and exit 0 [class: REPOSITORY_TEST]
- [x] Record the pre-round readiness outcome (recorded beside the r1 exec review record) and the em-dash and hygiene results beside the review record [class: REPOSITORY_TEST]

## Disposition

Executed 2026-10-04 from worktree ai-playbook-wt-bpps (branch plan-bpps-exec). Task 1 landed as a984e8f7 (interview section between Path Discovery and Implementation Workflow, worktree_root arm, no-op routing, recovery-rerun extension, company-rule silent persist deleted, trigger-list entry, optional-keys rows, Priority block shape spec, Step 4 persist amendment, Facts File Shape example). Task 2 landed as 34900a99 (bootstrap Integration Points rows, doc-hierarchy row, README row, using-skills Step 0 dispatcher sync). Receipts commit 56536b19. Validation block ALL-GATES-GREEN exit 0. Exec review r1 ready=yes zero blocking; 3 Low folded same-pass (receipt sha correction, review-record anchor written, decline-posture wording repair with F3 needle preserved). No origin row (Backlog origin: none). Not run against this repository per the plan's assumption; the next bootstrap trigger here offers the interview naturally.
