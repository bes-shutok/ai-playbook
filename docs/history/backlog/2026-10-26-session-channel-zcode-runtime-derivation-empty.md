# Backlog: session-channel derivation returns empty on the ZCode runtime

Filed: 2026-10-26
Status: covered (docs/history/plans/2026-10-30-session-channel-zcode-runtime-derivation-empty.md)
Priority: high
Required agent type: zcode

Witness-only affinity annotation (added 2026-10-30, the agent-type-affinity-before-plan-work plan): the Environment context below explicitly names the ZCode desktop runtime; this row is Status: covered, so the label witnesses the affinity contract's catch record (the 2026-10-27 Codex session that selected this origin) and carries no live selection effect.

- **Class:** fix-class
- **Origin class:** learn Step 1.8 skill-usage issue (witnessed 2026-10-26, learn run over an exec carrier session)
- **Skill/step:** `scripts/session_channel.py` `_derive()` (consumed by the learn skill's Step 1 marker recipe, the plans skill's marker recipe, and the skill-gate README's invocation contract)
- **Driving force:** correctness; secondary: code-quality
- **Cluster:** the registry consult's state-record read-root defect is covered (landed read-root sentence, EXEC-PROMPTS entry registry-due-read-primary-root); this row owns the shared session-channel helper returning empty on the ZCode runtime

## Observed versus expected

Observed: invoking the shared session-channel helper on this host's ZCode runtime prints an empty string: `_derive()` reads only the Claude (`CLAUDE_CODE_SESSION_ID`), Cursor (`CURSOR_SESSION_ID`, `CURSOR_CONVERSATION_ID`), and Codex (`CODEX_SESSION_ID`) environment variables, and ZCode sets none of them. The learn marker recipe then writes the marker under the helper's `no-session` key, so every ZCode session shares one marker namespace (per-session marker isolation silently degrades to per-runtime) instead of the expected per-session key the (project, session) marker contract promises.

Expected: the helper returns a stable per-session identifier on every runtime the skill-gate learn class supports, or the learn/plans marker recipes name a runtime-specific fallback derivation for runtimes without a known session env var.

## Reproduction evidence (trimmed)

`python3 scripts/session_channel.py` under the ZCode Bash tool prints nothing (exit 0); `skill_gate.py --write-marker learn --session-id ""` then creates `learn.<project>.no-session.marker` in the runtime skill-invoked directory (the empty session id resolves to the mechanism's `NO_SESSION_KEY` arm).

## Environment context

ZCode desktop runtime, 2026-10-26; repo-local script copy (agents and scripts deployed from this repository); the marker write itself succeeds, so no gate blocks - the loss is marker isolation quality only.

## Suspected root area

`scripts/session_channel.py` `_derive()`'s runtime coverage: add a ZCode session-env source or a documented no-session fallback contract for marker-consuming recipes.
