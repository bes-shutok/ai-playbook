# Plan: Verify ZCode follows the shared ASD-STE100 rule

Backlog origin: `docs/history/backlog/2026-11-16-asd-ste100-zcode-runtime-adoption.md`
Cluster: `docs/history/plans/completed/2026-11-16-asd-ste100-codex-shared-corpus.md`; `docs/history/plans/completed/2026-11-17-asd-ste100-claude-runtime.md` (completed twins of the group rows)
Required agent type: zcode
Driving force: code-quality
Plan review record: the staging series .ai-playbook/reviews/2026-11-19-plan-review-asd-ste100-zcode-runtime-pd6542706-r*.md (the highest rN for this source-plan path is authoritative, including any deferred-residual list)
Execution budget: 1h total, largest task 0.5h
Executed: yes (7af2f2bc8147913e77fe3a62c018815d051cfed0)
Authoring claim: 2026-11-16-asd-ste100-zcode-runtime-adoption.md (session sess_45c86f72-4057-4b14-b04a-431df96b1556)

## Terms

- **Shared policy:** The "Clear technical English" rule in `docs/AGENTS.md`. It applies ASD-STE100 Simplified Technical English, Issue 9, to authored English prose. It is the only owner of the rule.
- **ZCode entrypoint:** The file `~/.zcode/AGENTS.md`. It is a regular file whose body imports this repository's `docs/AGENTS.md` with an `@` import line.
- **Shared skill registry:** The `~/.agents/skills` registry. The live ZCode session's skill list resolves the workflow skills there.
- **Fresh session:** A ZCode session that started after the Codex policy landed and whose loaded instructions contain the shared policy bullet.
- **Probe:** One prompt given to a fresh session, and the answer it returns. There are three probe classes: plain prose, structured output, and exact technical literals.
- **Gap:** A probe answer that clearly breaks a rule of the shared policy while the policy is loaded in the session. A borderline style choice is an observation, not a gap.
- **Verification record:** The wiring evidence, the three probe samples, the judgment of each, and the disposition. It is folded into the completed plan by the completion pass.

## Why

The shared policy is landed, and the Claude runtime is verified, but nobody has checked that ZCode loads the canonical file or follows the policy in its answers. The runtime map records no verified ZCode wiring, and the import line alone shows wiring, not behavior. This plan checks both and records the evidence without adding a second policy copy.

## Gist & Examples

TLDR: verify that ZCode loads and follows the shared ASD-STE100 rule and record the evidence, for code-quality.

Before (today): `~/.zcode/AGENTS.md` imports the shared policy file, and the live ZCode session loads its content, but no record shows the wiring checked against the runtime map or how ZCode answers look. A session that started before the Codex landing has an old copy of `docs/AGENTS.md` without the rule, so wiring alone cannot prove conformance.

After (this plan): a fresh ZCode session shows the rule in its loaded instructions. It then answers three probes: a short explanation, a four-row table, and a request that includes a shell command and an exact error text. Each answer is checked against the shared policy. The exact error text must stay byte-identical, the answer must not claim certification, and it must not expose private reasoning. The record then names the result.

Example of a passing literal probe: given the request to repeat `error: ENOENT: no such file or directory, open /tmp/x.json`, the answer contains that exact string, and `grep -F` on the saved answer finds it.

Example of a gap: the answer rewrites the error text into simpler words, and the repeat sample does the same. The run stops and keeps the evidence. The operator then scopes a change to the owning ZCode surface through a plan amendment or a new plan, and that amendment updates the runtime map with the observed facts. It is not patched inside this plan.

## Outcome

ZCode's use of the shared ASD-STE100 policy is checked in a live ZCode session and recorded, with no second policy copy.

- The wiring facts (entrypoint, import, skill path) are confirmed against the runtime map with command output.
- Three probe answers are saved and judged against the shared policy.
- The disposition is recorded: no gap and no edit, or a gap that the operator scopes through a plan amendment or a new plan.
- No change lands in `docs/AGENTS.md` or shared skills; the runtime map changes only when the observed wiring itself changed or an operator-scoped amendment directs it.

Follow-up disposition: a demonstrated ZCode gap is not patched here. The executor stops, records the evidence, and asks the operator to scope the smallest change to the verified ZCode-owned surface through a plan amendment or a new plan; the runtime map update with observed facts rides that amendment. A copy of the policy in a ZCode-only file is a rejected disposition. The shared policy and shared skills stay unchanged unless the observed wiring itself changed.

Gate delta: none. This plan adds no refusal, hard gate, fence, protocol layer, schema field, or pausing condition, removes none, and adds no blocking review-layer duty.

## Assumptions

- The active identity `zcode` is compatible with the origin's `Required agent type: zcode`; basis: the runtime inventory canonical id `zcode` and the affinity contract in `projects/.ai-playbook/agent-runtime-layout.md`.
- The shared policy is the single "Clear technical English" bullet in `docs/AGENTS.md`; basis: a grep of that file on 2026-11-19 returning one match.
- Today's wiring equals the observed state from 2026-11-19: `~/.zcode/AGENTS.md` is a regular file whose body imports `docs/AGENTS.md` through an `@` import line, and the live ZCode session's skill registry resolves the workflow skills under `~/.agents/skills`; basis: a direct file read and the authoring session's own loaded skill list in this repository.
- ZCode loads instructions at session start, so only a session that started after the policy landing has the rule; basis: the authoring session's own loaded context contains the canonical bullet.
- The plan runs by the manual execution arm in a ZCode session; basis: the runtime map lists `zcode` as deferred with no verified execute-plan adapter, so execute-plan cannot launch it, and the executed sibling plan for Claude ran the same arm.
- One sample per probe class is enough to detect a gap, and a failing sample is run once more before it counts; basis: the origin names one test per class, and a larger sample is not requested.
- The verification-only gap routing holds: a confirmed gap stops the run, and the operator scopes the fix through a plan amendment or a new plan with the runtime map update riding that amendment; basis: the executed sibling plan's recorded requirements confirmation (`docs/history/plans/completed/2026-11-17-asd-ste100-claude-runtime.md`) and this plan's standing-authorization receipt below; the origin's Expected gap branch directs a ZCode-owned adapter add, which stays the operator's amendment scope rather than a pre-written task here.
- `docs/AGENTS.md` and the shared skills stay unedited in this run; basis: the origin prompt and its rejected alternatives.

Decision points requiring a grill: gap routing is verification-only: a confirmed gap stops the run and the operator scopes the fix through a plan amendment or a new plan, with the runtime map update riding that amendment (standing authorization receipt, maintenance-selected arm, 2026-11-19; affects Assumptions and the Outcome Follow-up disposition).

## Evaluation Criteria

**Quality dimensions:**
- Correctness: each probe answer is judged on four checks. Exact literals stay byte-identical (`grep -F`). No certification or compliance claim appears. No private reasoning is disclosed. The prose follows the Issue 9 writing rules. The shared policy names the standard as the authority and does not list rules, so the record cites each breach by its rule number in the official specification, and only a clear breach counts as a gap.
- Evidence quality: every statement in the Verification record cites a command output or a quoted answer.
- Minimality: `git diff` against the base shows no change to `docs/AGENTS.md`, any shared skill, or `projects/.ai-playbook/agent-runtime-layout.md`, unless the observed wiring changed or an operator-scoped amendment directed the map edit.

**Done when:**
- The wiring check output is recorded against the observed sources (`docs/AGENTS.md` Verify wiring record; the runtime map's deferred `zcode` row), and any difference is recorded as observed wiring change evidence.
- The session precondition is recorded: the loaded instructions contain the shared policy bullet.
- Three probe answers are recorded with a pass or gap judgment for each check.
- The disposition is recorded: no gap, or a gap with the operator's scoping request.

**Ship when:**
- Nothing outside this repository is required; the run ends with the completion record. If a gap is found, scoping its fix is a plan amendment or a new plan, not a ship condition.

## Review Scope

**Explicit must-fix:** findings on these paths are always in scope (review and fix if valid):

**Documentation:**
- `docs/history/plans/2026-11-19-asd-ste100-zcode-runtime.md` (review-only)

**Plan-related extension:** implementation and review may change files not listed above. Treat a finding as in scope when it is **causally related to this plan**: it implements or completes a plan task, fixes a regression introduced by plan work, closes wiring or docs implied by an explicit must-fix change, or contradicts a contract the plan changed. If the link to the plan is weak or speculative, drop as out of scope with a one-line reason.

**Out of scope; reject unless plan-related:**
- `docs/AGENTS.md`; the shared policy belongs to the Codex-owned work and stays unchanged.
- `agents/skills/`; shared skills belong to the Codex-owned work and stay unchanged.
- `projects/.ai-playbook/agent-runtime-layout.md`; it changes only when the observed wiring changed or the operator scopes a gap amendment.

## Validation Commands

```bash
test -f ~/.zcode/AGENTS.md && ! test -L ~/.zcode/AGENTS.md && grep -q '^@.*docs/AGENTS.md' ~/.zcode/AGENTS.md
grep -c 'Clear technical English' docs/AGENTS.md
git diff --stat main -- docs/AGENTS.md agents/skills projects/.ai-playbook/agent-runtime-layout.md
```

### Task 1: Confirm the session precondition and the wiring

Context surface: the plan's Terms, this task, and `## Standing constraints` when present; referenced, never restated.

Files:
- none (read-only checks; no tracked repository edit)

- [x] Session precondition holds: given the executing ZCode session, expects its loaded instructions contain the "Clear technical English" bullet and the record quotes its first eight words; a session without the bullet stops the run and a new ZCode session takes over [class: REPOSITORY_TEST]
- [x] Entrypoint wiring matches the recorded sources: given the Validation Commands wiring checks, expects `~/.zcode/AGENTS.md` is a regular file with an import of `docs/AGENTS.md`, and the executing session's loaded skill list names at least one workflow skill resolved from `~/.agents/skills`; compare against `docs/AGENTS.md`'s Verify wiring record, because the runtime map records no ZCode entrypoint [class: REPOSITORY_TEST]
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

- [x] No-gap disposition: given no gap and no wiring change, expects the Verification record states no gap and `git diff --stat main -- docs/AGENTS.md agents/skills projects/.ai-playbook/agent-runtime-layout.md` is empty [class: REPOSITORY_TEST]
- [ ] Gap disposition: given a confirmed gap, expects the run stops, the record names the failing probe and its quoted answer, and the operator is asked to scope the smallest change to the verified ZCode-owned surface through a plan amendment or a new plan, with the runtime map update riding that amendment [class: REPOSITORY_TEST]
- [x] Safety witness: given any outcome, expects no copy of the policy is written to a ZCode-only file and `docs/AGENTS.md` and the shared skills stay byte-identical [class: REPOSITORY_TEST]
- [x] Hand the Verification record to the completion pass for the completed plan's disposition section [class: REPOSITORY_TEST]

## Disposition of migrated backlog items

Origin row `docs/history/backlog/2026-11-16-asd-ste100-zcode-runtime-adoption.md` flips to `covered (docs/history/plans/completed/2026-11-19-asd-ste100-zcode-runtime.md)` through the execution flip in this run's archive transition; the row file stays in place as the witness.

## Verification record (completion pass)

Executed 2026-11-19 WET by session sess_45c86f72-4057-4b14-b04a-431df96b1556 in the executing ZCode session itself, manual arm, read-only verification lane (every task's Files list declares none, so no implement workers, no per-task commits, and no code-review panel ran). Evidence: session task logs and the three unedited probe files under the run's session directory (task1.log.md, task2.log.md, task3.log.md, probe1-plain-prose.md, probe2-structured.md, probe3-literal.md).

1. Session precondition: holds. The executing session's loaded instructions contain the shared policy bullet through the `~/.zcode/AGENTS.md` @ import of `docs/AGENTS.md`; first eight words: "Clear technical English: Use ASD-STE100 Simplified Technical English".
2. Wiring: `~/.zcode/AGENTS.md` is a regular file importing `docs/AGENTS.md`; all three plan Validation Commands pass; the state matches `docs/AGENTS.md`'s Verify wiring record (line 15) and the runtime map's deferred `zcode` row (no execute-plan adapter; the manual arm ran, as the plan's Assumptions state). No observed wiring change.
3. Probes: all three classes pass. Plain prose: no certification claim, no private reasoning, no clear Issue 9 breach (one observation, not a gap: "redirection" is a retained subject-specific technical noun). Structured: four rows, three columns, same checks. Literal: `grep -F 'error: ENOENT: no such file or directory, open /tmp/x.json'` finds the text unchanged in the saved answer. The executing session judged its own answers while holding the expected literal, so the literal check is the mechanical evidence and the other checks cite the quoted answers.
4. Disposition: no gap and no wiring change. `git diff --stat main -- docs/AGENTS.md agents/skills projects/.ai-playbook/agent-runtime-layout.md` empty, run fresh at 2026-11-19T07:17:45Z. No edit landed in `docs/AGENTS.md` or shared skills; the runtime map is unchanged (no observed wiring change; no operator-scoped gap amendment exists). The gap-disposition branch never triggered, so its checkbox stays unchecked as the honest record.
5. Safety witness: no copy of the policy was written to any ZCode-only file; `~/.zcode/AGENTS.md` and `~/.zcode/agents.md` are import-only shells (ASD-STE100 and "Clear technical English" grep: 0 hits in each), and `docs/AGENTS.md` plus the shared skills stayed byte-identical through the run.
