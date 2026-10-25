# Plan: Landing-subject grammar end to end

Backlog origin: docs/history/backlog/2026-10-13-reverse-squash-execute-plan-landing-prefix-gap.md
Driving force: code-quality (primary) + efficiency (secondary)
Plan review record: .ai-playbook/reviews/2026-10-23-plan-review-landing-subject-grammar-end-to-end-r*.md
Execution budget: 2.25h total, largest task 1h
Authoring claim: docs/tmp/authoring-claims/2026-10-13-reverse-squash-execute-plan-landing-prefix-gap.md (session zcode-interactive-20261023T1623-ad1)

## Terms

- **Landing-claim grammar:** the commit-subject shape `plans: land <plan-slug> (<detail>)` and its lane family variants; the recognized prefixes live in one constant in the guard script.
- **Landing-claim anchor:** the landing commit a post-landing sweep walk anchors on; an anchor whose subject matches no recognized prefix is refused as not a landing-claiming commit.
- **Compose-time notice:** a warning line the landing helper prints before composing the landing commit when the message's subject line matches no recognized prefix; it never changes an exit code or an outcome.
- **Guard constant:** `LANDING_CLAIM_PREFIXES` in `scripts/reverse_squash_guard.py`, the single source of the recognized prefixes.

## Why

The post-landing residue sweep classifies landings by subject prefix, but the recognized set covers only two lane families. Two witnessed landing families used conformant subjects the set never learned, and one landing composed a free-form subject; each lost the sweep's mechanical coverage, and the free-form case was repaired with a message-only amend that left a permanent reflog row. The grammar is enforced nowhere upstream of the post-landing audit.

## Gist & Examples

TLDR: teach the landing-claim grammar upstream and warn at compose time, so every landing anchors the post-landing sweep without hand verification or amend repairs.

Before (today): an execute-plan landing lands with the subject `execute-plan: land plan-review-cross-task-lifecycle (...)`. The post-landing sweep refuses the anchor ("not a landing-claiming commit") and the run verifies single parenthood by hand with `git rev-list --parents -1`, losing the sweep's mechanical coverage for the most frequent landing family. A later landing composed free-form (`skills: separate ...`); the sweep refused the anchor and the repair was a message-only amend into the grammar, which the base reflog audit flags as one permanent backward-move row.

After (this plan): the same execute-plan landing's subject anchors the sweep directly with the execution kind, and an authoring self-landing's `author: land <slug> (...)` subject anchors with the authoring kind. A landing message without any recognized prefix still lands unchanged, but the helper prints one warning naming the recognized grammar before the landing commit exists, so the composer can stop and rephrase instead of amending after the fact.

Edge cases: a message whose subject is free-form but whose body carries the grammar is still warned (the anchor reads the subject line only); a landing in `land` mode whose guard copy cannot be imported at the notice point prints one note line and proceeds (in `land-worktree` mode the wired check-landing gate refuses a missing guard copy before the notice point is reached); historical landings in the batch walk window classify under the widened set with their lane kinds.

## Outcome

Every landing family's subject anchors the post-landing sweep mechanically, and a grammar-less landing message is flagged before the landing commit exists.

- Execute-plan and authoring landings keep the sweep's residue coverage without the hand-run rev-list fallback.
- The compose-time warning removes the amend-and-reflog-row repair class for future landings.
- The recognized prefix set has one home in the guard constant; the kind mapping stays derived from that constant rather than a parallel table, the helper's notice reads the grammar through the guard module rather than restating it, and the landing guidance names the constant as the single source.

Gate delta: remove the false "not a landing-claiming commit" refusal for the execute-plan and author landing families (two witnessed classes, origin row evidence); add no new refusal class, hard gate, fence, protocol layer, schema field, or dispatch-pausing condition; one warning-only compose-time notice (printed line, exit code and outcome unchanged) whose ledger entry is its promotion path; no blocking review-layer duty is added.

## Assumptions

- The shared landing-claim family is the widened prefix set: `execute-plan: land ` (execution kind) and `author: land ` (authoring kind) beside the existing two; basis: both are witnessed landing subjects (2f6d61b73, e9788b875), the origin row names both, and preserving the lane-to-kind mapping keeps follow-up classification semantics unchanged; a single shared prefix would rewrite lane vocabulary and change anchor-kind consumers for no classification gain.
- The compose-time check imports the guard module rather than adding a CLI subcommand; basis: the landing helper already resolves the guard script path, a subcommand is a new surface for one boolean read, and the admission protocol prices new surfaces.
- A guard import failure at the notice point prints one note line and continues; basis: the notice is warning-only and a missing guard copy must not block a landing. In `land-worktree` mode the wired check-landing gate already refuses a landing whose guard copy is missing from every resolved path before the notice point, so the note-line path is reachable and exercised in `land` mode; the `land-worktree` fixture surface does not reach it and is not pinned to it.
- The notice's incident rows are recorded through the ledger record CLI so a later true catch is countable at promotion time; basis: the description-length row's witnessed lesson that an unledgered true catch is invisible.
- Maintenance-selected decision receipts: prefix family and import mechanism as above; source: origin row Expected plus the entry's scope arms; date: 2026-10-23; affected sections: Outcome, Evaluation Criteria, Review Scope, Tasks 1-3.
- Machinery admission (compose-time notice): incident: the three witnessed anchor refusals and the amend repair (origin row evidence lines); expected catch frequency: every compose-time grammar miss, three in ten days across the landing families; false-positive cost: zero on a grammar-conformant message, one note line when the guard copy is absent; sunset or review: warning-only until a true catch, promotion via a pre-registered registry-removal row, review riding the next `land_squash.sh` touch.
- Sources inspected: not a tracker-linked request.
Decision points requiring a grill: none remain.

## Evaluation Criteria

**Quality dimensions:**
- correctness: `check-single-commit` anchors landings in all four recognized prefixes with the right lane kind, and the batch walk picks up the witnessed historical subjects.
- warning-only posture: the compose-time notice changes no exit code or outcome in any fixture; a grammar-conformant message produces no warning line.
- single source: the guidance sentences name the guard constant as the grammar source; the pins suite passes over the skill-text edits.

**Done when:**
- Focused tests prove the widened constant, both kind mappings, and the warning line (present on a free-form message, absent on a grammar message, landing outcome unchanged in both).
- The pins suite, the em-dash scan, and the public-hygiene scan pass over the changed set.

**Ship when:**
- The plan is reviewed and landed; the origin row resolves covered with the landing as witness.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Production code:**
- `scripts/reverse_squash_guard.py` (the prefix constant and `anchor_kind` only)
- `scripts/land_squash.sh` (the compose-time notice only)
- `agents/skills/execute-plan/worktree-first.md` (the landing step's one grammar sentence)
- `agents/skills/maintenance/template-authoring.md` (the landing paragraph's by-reference wording only)
- `agents/skills/maintenance/template-execution.md` (the landing paragraph's by-reference wording only)
- `agents/skills/maintenance/decisions.md` (the landing-completion sentence's by-reference wording only)

**Tests:**
- `scripts/test_reverse_squash_guard.py` (prefix and kind fixtures only)
- `scripts/test_land_squash.py` (warning-line fixtures only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, or contradicts a contract the plan changed. A pinned-span breakage in the pins suite caused by a guidance edit is in scope as the edit's own repair.

**Out of scope; reject unless plan-related:**
- `scripts/done_run.sh`; the done closeout's commit path is not this plan's surface.
- Promotion of the notice to a blocking gate; the admission protocol reserves promotion for a true catch with a pre-registered registry-removal row.
- Grammar enforcement for non-landing commits (flip, prune, closeout classes keep their own prefixes unchanged).

## Validation Commands

Run from the repository root:

```bash
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_reverse_squash_guard.py'
PATH="$HOME/.agents/venvs/ai-playbook-test/bin:$PATH" python3 -m unittest discover -s scripts -p 'test_land_squash.py'
bash scripts/check_maintenance_pins.sh
bash scripts/check-no-em-dash.sh touched
bash scripts/scan-public-hygiene.sh --files scripts/reverse_squash_guard.py scripts/land_squash.sh scripts/test_reverse_squash_guard.py scripts/test_land_squash.py agents/skills/execute-plan/worktree-first.md agents/skills/maintenance/template-authoring.md agents/skills/maintenance/template-execution.md agents/skills/maintenance/decisions.md
```

The guard fixtures must anchor a landing per added prefix with the expected lane kind and exercise the batch walk over a history containing the witnessed subject shapes. The helper fixtures must land a free-form-message branch with the warning line present and the landing outcome unchanged, land a grammar-message branch with no warning line, and cover the guard-import-failure note. The pins suite runs after the skill-text edits; a pinned-span breakage is repaired by adjusting the edit, never by editing the pin.

### Task 1: Widen the landing-claim prefix set

Context surface: this plan's Terms, Outcome, Standing constraints (none), Assumptions, and Evaluation Criteria; the origin row's Problem, Evidence, and Expected sections; the entry's Orientation and rejected alternatives.

Files:
- `scripts/reverse_squash_guard.py`
- `scripts/test_reverse_squash_guard.py`

Primary class anchors:
- `LANDING_CLAIM_PREFIXES` in `scripts/reverse_squash_guard.py`
- `anchor_kind` in `scripts/reverse_squash_guard.py`
- `is_landing_claim` in `scripts/reverse_squash_guard.py`

- [x] `is_landing_claim` recognizes the two added prefixes: given a landing whose subject starts with `execute-plan: land ` or `author: land `, expects the anchor classification to accept it. [class: IMPLEMENTATION_REQUIRED]
- [x] `anchor_kind` maps the added prefixes to their lane kinds: given the same subjects, expects the execution kind for `execute-plan: land ` and the authoring kind for `author: land `, keeping the existing two mappings byte-identical in behavior. [class: IMPLEMENTATION_REQUIRED]
- [x] Add fixtures: one landing per added prefix anchors `check-single-commit` with the expected kind and no hand-verification fallback, and a batch walk over a history containing the witnessed subject shapes (`execute-plan: land <slug> (...)`, `author: land <slug> (...)`) classifies both as anchors. [class: REPOSITORY_TEST]
- [x] Run → expect RED: the added-prefix anchor fixtures fail against the current two-prefix constant. [class: REPOSITORY_TEST]
- [x] Implement the constant widening and kind mapping minimally, with the mapping anchored in the one constant (no second prefix table beside it). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the focused guard test file passes with the new fixtures and all existing controls. [class: REPOSITORY_TEST]
- [x] One-line guard comment beside the widened constant naming the trust-on-subject class (a non-landing commit whose subject carries a recognized prefix can terminate a residue window early and mask follow-up residue from the closeout receipts), so the exposure is recorded where the next prefix addition lands. [class: IMPLEMENTATION_REQUIRED]
- [x] Commit: `fix: recognize execute-plan and author landing subjects in the guard constant` [class: IMPLEMENTATION_REQUIRED]

### Task 2: Compose-time grammar notice in the landing helper

Context surface: this plan's Terms, Outcome, Assumptions, and Evaluation Criteria; the origin row's second arm; the entry's Machinery admission block.

Files:
- `scripts/land_squash.sh`
- `scripts/test_land_squash.py`

Primary class anchors:
- `REVERSE_GUARD` in `scripts/land_squash.sh`
- `emit_outcome` in `scripts/land_squash.sh`

- [x] Safety witness: given a landing message whose first line matches no recognized prefix, expects one warning line naming the recognized grammar (read from the guard constant through a module import) before the landing commit is composed, with the landing outcome, exit code, and composed commit unchanged. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a landing message whose first line carries a recognized prefix, expects no warning line and behavior identical to today. [class: IMPLEMENTATION_REQUIRED]
- [x] Safety witness: given a guard import failure at the notice point in `land` mode (a missing or erroring guard copy), expects one note line and an unchanged landing; in `land-worktree` mode the wired check-landing gate refuses a missing guard copy first and this case is not reachable. [class: IMPLEMENTATION_REQUIRED]
- [x] Add fixtures in the helper test file, pinned to `land` mode: a free-form-message landing asserts the warning line in the helper output and an unchanged outcome; a grammar-message landing asserts no warning line; the import-failure case asserts the note line. The warning text is read from the guard constant through the module import, no literal grammar string in the helper. [class: REPOSITORY_TEST]
- [x] Run → expect RED: the free-form warning fixture fails against the helper without the notice. [class: REPOSITORY_TEST]
- [x] Implement the notice in both landing modes before the landing commit composition, reading the constant through the guard module import over the already-resolved guard script path and reusing the guard's constant (no second copy of the prefix set in the helper). [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the focused helper test file passes with the new fixtures and all existing controls. [class: REPOSITORY_TEST]
- [x] Commit: `feat: warn when a landing message lacks the landing-claim grammar` [class: IMPLEMENTATION_REQUIRED]

### Task 3: Guidance pin and ledger entry

Context surface: this plan's Terms, Outcome, Assumptions, and Evaluation Criteria; the entry's Guidance pin scope arm; development lesson 50's rule made operative at the recipe layer.

Files:
- `agents/skills/execute-plan/worktree-first.md`
- `agents/skills/maintenance/template-authoring.md`
- `agents/skills/maintenance/template-execution.md`
- `agents/skills/maintenance/decisions.md`

Primary class anchors:
- `Land under the lock` in `agents/skills/execute-plan/worktree-first.md`

- [x] One canonical sentence in the Worktree-first standard's landing step: the `--message` subject follows the landing-claim grammar with a prefix drawn from the guard constant, named as the single source (the sentence the blueprint references point at). [class: IMPLEMENTATION_REQUIRED]
- [x] By-reference wording in the two maintenance blueprint landing paragraphs and the decisions landing-completion sentence: each names the landing-claim grammar pin by reference instead of restating the grammar. [class: IMPLEMENTATION_REQUIRED]
- [x] Before editing each guidance span, grep the pins suite for spans inside the edited paragraph; a pinsuite breakage after the edits is repaired by adjusting the edit. [class: REPOSITORY_TEST]
- [x] Record the notice's incident rows through the ledger record CLI under the guard id `compose-time-landing-grammar-notice` (three witnessed anchor refusals and the amend repair) so a later true catch is countable at promotion review. [class: IMPLEMENTATION_REQUIRED]
- [x] Run → expect GREEN: the pins suite, the em-dash scan, and the public-hygiene scan pass over the changed set. [class: REPOSITORY_TEST]
- [x] Commit: `docs: pin the landing-claim grammar to the guard constant` [class: IMPLEMENTATION_REQUIRED]
