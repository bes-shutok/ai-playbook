# Plan: Verify Claude follows the shared ASD-STE100 rule

Backlog origin: `docs/history/backlog/2026-11-16-asd-ste100-claude-runtime-adoption.md`
Cluster: `docs/history/backlog/2026-11-16-asd-ste100-zcode-runtime-adoption.md`
Required agent type: claude
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-17-plan-review-asd-ste100-claude-runtime-p19fa7e7b-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h
Executed: yes (adc749dd92fc6fa6b40054432a799988e47efc5b)
Authoring claim: 2026-11-16-asd-ste100-claude-runtime-adoption.md (session 9843e57c-b32b-4f3e-bcec-0d606200f62b)

## Terms

- **Shared policy:** The "Clear technical English" rule in `docs/AGENTS.md`. It applies ASD-STE100 Simplified Technical English, Issue 9, to authored English prose. It is the only owner of the rule.
- **Claude entrypoint:** The file `~/.claude/CLAUDE.md`. It is a regular file that imports `docs/AGENTS.md`. Claude Code reads it when a session starts.
- **Fresh session:** A Claude session that started after the Codex policy landed (commit 282787049) and whose loaded instructions contain the shared policy bullet.
- **Probe:** One prompt given to a fresh session, and the answer it returns. There are three probe classes: plain prose, structured output, and exact technical literals.
- **Gap:** A probe answer that clearly breaks a rule of the shared policy while the policy is loaded in the session. A borderline style choice is an observation, not a gap.
- **Verification record:** The wiring evidence, the three probe samples, the judgment of each, and the disposition. It is folded into the completed plan by the completion pass.

## Why

The shared policy now exists, but nobody has checked that Claude loads it or that Claude output follows it. The import path alone shows wiring, not behavior. This plan checks both and records the evidence without adding a second policy copy.

## Gist & Examples

TLDR: verify that Claude loads and follows the shared ASD-STE100 rule and record the evidence, for code-quality.

Before (today): `~/.claude/CLAUDE.md` imports the shared policy file, and the runtime map says Claude uses it. No record shows what a Claude session loads or how its answers look. A session that started before the Codex landing has an old copy of `docs/AGENTS.md` without the rule, so wiring alone cannot prove conformance.

After (this plan): a fresh Claude session shows the rule in its loaded instructions. It then answers three probes: a short explanation, a four-row table, and a request that includes a shell command and an exact error text. Each answer is checked against the shared policy. The exact error text must stay byte-identical, the answer must not claim certification, and it must not expose private reasoning. The record then names the result.

Example of a passing literal probe: given the request to repeat `error: ENOENT: no such file or directory, open /tmp/x.json`, the answer contains that exact string, and `grep -F` on the saved answer finds it.

Example of a gap: the answer rewrites the error text into simpler words, and the repeat sample does the same. The run stops and keeps the evidence. The operator then scopes a change to the owning Claude surface through a plan amendment or a new plan. It is not patched inside this plan.

## Outcome

Claude's use of the shared ASD-STE100 policy is checked in a live session and recorded, with no second policy copy.

- The wiring facts (entrypoint, import, skill path) are confirmed against the runtime map with command output.
- Three probe answers are saved and judged against the shared policy.
- The disposition is recorded: no gap and no edit, or a gap that the operator scopes through a plan amendment or a new plan.
- No change lands in `docs/AGENTS.md`, shared skills, or the runtime map.

Follow-up disposition: a demonstrated Claude gap is not patched here. The executor stops, records the evidence, and asks the operator to scope the smallest change to the verified Claude-owned surface through a plan amendment or a new plan. A manual run has no execute-plan run record, so no automatic referral exists. A copy of the policy in a Claude-only file is a rejected disposition. The runtime map and the shared policy stay unchanged unless the observed wiring itself changed.

Gate delta: none. This plan adds no refusal, hard gate, fence, protocol layer, schema field, or pausing condition, removes none, and adds no blocking review-layer duty.

## Assumptions

- The active identity `claude` is compatible with the origin's `Required agent type: claude`; basis: the runtime inventory canonical id `claude` and the affinity contract in `projects/.ai-playbook/agent-runtime-layout.md`.
- The shared policy is the single "Clear technical English" bullet in `docs/AGENTS.md`; basis: commit 282787049 and a grep of that file on 2026-11-17.
- Today's wiring equals the runtime map; basis: on 2026-11-17 `~/.claude/CLAUDE.md` is a regular file with an `@` import of `docs/AGENTS.md`, `~/.claude/skills` is a symlink to the repository `agents/skills`, and `claude/skills` in the repository points to `../agents/skills`.
- Claude loads instructions at session start, so only a session that started after the landing has the rule; basis: the authoring session's own loaded copy of `docs/AGENTS.md` had no such bullet.
- Headless `claude -p` is not usable until the operator signs in again, so the probes run in the live Claude session that executes this plan; basis: four failed `claude -p` attempts on 2026-11-17 with the message that the login reached its time limit.
- The plan runs by the manual execution arm in a Claude session; basis: the runtime inventory lists `claude` as deferred with no verified adapter, so execute-plan cannot launch it.
- One sample per probe class is enough to detect a gap, and a failing sample is run once more before it counts; basis: the origin names one test per class, and a larger sample is not requested.
- The shared policy, shared skills, and runtime map stay unedited; basis: the origin prompt and its rejected alternatives.

Decision points requiring a grill: gap routing is a verification-only plan with an operator-scoped plan amendment or new plan, not a pre-written patch task (user confirmed 2026-11-17 in the requirements confirmation; affects Tasks and Review Scope); evidence home is the completed plan's disposition with no other tracked edit (user confirmed 2026-11-17 in the requirements confirmation; affects Evaluation Criteria).

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each probe answer is judged on four checks. Exact literals stay byte-identical (`grep -F`). No certification or compliance claim appears. No private reasoning is disclosed. The prose follows the Issue 9 writing rules. The shared policy names the standard as the authority and does not list rules, so the record cites each breach by its rule number in the official specification, and only a clear breach counts as a gap.
- Evidence quality: every statement in the Verification record cites a command output or a quoted answer.
- Minimality: `git diff` against the base shows no change to `docs/AGENTS.md`, any shared skill, or `projects/.ai-playbook/agent-runtime-layout.md`, unless the observed wiring changed.

**Done when:**
- The wiring check output is recorded and matches the runtime map.
- The session precondition is recorded: the loaded instructions contain the shared policy bullet.
- Three probe answers are recorded with a pass or gap judgment for each check.
- The disposition is recorded: no gap, or a gap with the operator's scoping request.

**Ship when:**
- Nothing outside this repository is required; the run ends with the completion record. If a gap is found, scoping its fix is a plan amendment or a new plan, not a ship condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `docs/history/plans/2026-11-17-asd-ste100-claude-runtime.md` (review-only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is causally related to this plan: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/AGENTS.md`; the shared policy belongs to the Codex-owned work and stays unchanged.
- `agents/skills/`; shared skills belong to the Codex-owned work and stay unchanged.
- `projects/.ai-playbook/agent-runtime-layout.md`; it changes only if the observed wiring changed.

## Validation Commands

```bash
test -f ~/.claude/CLAUDE.md && ! test -L ~/.claude/CLAUDE.md && grep -q '^@.*docs/AGENTS.md' ~/.claude/CLAUDE.md
test -L ~/.claude/skills && test -L claude/skills
grep -c 'Clear technical English' docs/AGENTS.md
git diff --stat main -- docs/AGENTS.md agents/skills projects/.ai-playbook/agent-runtime-layout.md
```

### Task 1: Confirm the session precondition and the wiring

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- none (read-only checks; no tracked repository edit)

- [x] Session precondition holds: given the executing Claude session, expects its loaded instructions contain the "Clear technical English" bullet and the record quotes its first eight words; a session without the bullet stops the run and a new Claude session takes over [class: REPOSITORY_TEST]
- [x] Entrypoint wiring matches the runtime map: given the Validation Commands wiring checks, expects `~/.claude/CLAUDE.md` is a regular file with an import of `docs/AGENTS.md`, and `~/.claude/skills` and `claude/skills` are symlinks to the shared skills [class: REPOSITORY_TEST]
- [x] Safety witness: given a wiring result that differs from the runtime map, expects the difference is recorded as observed wiring change evidence and no file is edited in this task [class: REPOSITORY_TEST]
- [x] Record the command outputs for the Verification record [class: REPOSITORY_TEST]

### Task 2: Run and judge the three probes

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- none (read-only probes; no tracked repository edit)

- [x] Plain prose probe passes: given a request for a three-sentence explanation of a technical topic, expects an answer with no certification claim, no private reasoning shown, and no clear breach of an Issue 9 writing rule, each breach cited by its rule number in the official specification [class: REPOSITORY_TEST]
- [x] Structured probe passes: given a request for a four-row table with three columns, expects a four-row table whose cells use the same checks as the prose probe [class: REPOSITORY_TEST]
- [x] Literal probe passes: given a request for a shell command and the exact text `error: ENOENT: no such file or directory, open /tmp/x.json`, expects the command and the text unchanged, and `grep -F` on the saved answer finds the text [class: REPOSITORY_TEST]
- [x] Negative witness: given one failing sample, expects the same probe runs once more and only a second failing sample counts as a gap [class: REPOSITORY_TEST]
- [x] Save each probe class as a file in the run's tmp directory (the exact prompt and the full answer text, unedited), run `grep -F` for the literal on the saved literal answer, and record each answer, its check results, and any observation for the Verification record; the record states that the executing session judges its own answers while it holds the expected literal, so the literal check is the mechanical evidence and the other checks cite quoted text [class: REPOSITORY_TEST]

### Task 3: Record the disposition

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- none (the Verification record is folded into the completed plan by the completion pass; no other tracked repository edit)

- [x] Disposition is recorded: given no gap and no wiring change, expects the Verification record states no gap and `git diff --stat main -- docs/AGENTS.md agents/skills projects/.ai-playbook/agent-runtime-layout.md` is empty; given a confirmed gap, expects the run stops, the record names the failing probe and its quoted answer, and the operator is asked to scope the smallest change to the verified Claude-owned surface through a plan amendment or a new plan [class: REPOSITORY_TEST]
- [x] Safety witness: given any outcome, expects no copy of the policy is written to a Claude-only file and `docs/AGENTS.md` and the shared skills stay byte-identical [class: REPOSITORY_TEST]
- [x] Hand the Verification record to the completion pass for the completed plan's disposition section [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

- `docs/history/backlog/2026-11-16-asd-ste100-claude-runtime-adoption.md`: completed by this plan. The run found no gap, so no Claude-side edit was needed. The former origin is deleted in this completion pass. The ZCode runtime adoption origin stays open.

## Verification record

Executed on 2026-11-17 in the primary checkout on `main` by a Claude session (Sonnet 5.5). The run changed no tracked file. It did not use a worktree, an execution claim, a per-task worker, or the Phase 3 review panel, because every task was read-only.

**Task 1: precondition and wiring**
- The loaded `docs/AGENTS.md` contained the bullet. Its first eight words: "Clear technical English: Use ASD-STE100 Simplified Technical English,".
- `grep -c 'Clear technical English' docs/AGENTS.md` returned 1.
- `~/.claude/CLAUDE.md` is a regular file, not a symlink, with a line that matches `^@.*docs/AGENTS.md`.
- `~/.claude/skills` and `claude/skills` are symlinks to the shared skills (`../agents/skills` for the repository link). This matches the runtime map. No wiring change was observed.
- `plan_readiness.py --pre-round` returned `OUTCOME: pass`.

**Task 2: probes** (prompt and full answer saved unedited in the run's tmp directory)

The executing session judged its own answers while it held the expected literal. The `grep -F` result is the only mechanical evidence. The other checks cite quoted text.

| Probe | Result | Evidence |
|---|---|---|
| Prose (symbolic link, three sentences) | pass | Sentences of 14, 16, and 14 words. Active voice. No certification claim, no private reasoning, no em dash, no clear Issue 9 breach. |
| Structured (3 columns, 4 data rows plus header) | pass | Short active cells. Observation only: "moved for good" is a mild idiom. It is not a clear breach. |
| Literal (command and exact error text) | pass | `grep -F 'error: ENOENT: no such file or directory, open /tmp/x.json'` on the saved answer matched (exit 0). The command `cat /tmp/x.json` was unchanged. |

No sample failed, so the negative witness needed no rerun.

**Task 3: disposition**
- No gap and no edit.
- `git diff --stat main -- docs/AGENTS.md agents/skills projects/.ai-playbook/agent-runtime-layout.md` was empty. No policy copy was written to a Claude-only file.
