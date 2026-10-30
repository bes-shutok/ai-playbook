# Plan: Derive a per-session channel on ZCode
Backlog origin: docs/history/backlog/2026-10-26-session-channel-zcode-runtime-derivation-empty.md
Driving force: correctness
Plan review record: the staging series .ai-playbook/reviews/2026-10-30-plan-review-session-channel-zcode-runtime-derivation-empty-r*.md
Execution budget: 1.0h total, largest task 1.0h
Authoring claim: docs/tmp/authoring-claims/2026-10-26-session-channel-zcode-runtime-derivation-empty.md (session 01a187b9-0f15-73d1-ad77-61ec1831ebcb)

## Terms

- **Session channel**: The opaque per-session value passed to marker consumers so separate sessions do not share a marker key.
- **ZCode source**: The stable current-session identity exposed by ZCode runtime context and passed explicitly to the shared helper.

## Why

The shared helper returns an empty value in ZCode because it recognizes only Claude, Cursor, and Codex environment variables. Marker writes then use the common `no-session` key, so distinct ZCode sessions share marker state.

## Gist & Examples

TLDR: Give ZCode marker writers a verified per-session identity through the shared helper, preserving marker isolation for the correctness force.

Before: Two ZCode sessions with no recognized environment variable both write to the `no-session` marker key.

After: ZCode marker recipes pass the current runtime session identity explicitly through the shared helper, so each session uses its own marker key.

Edge cases: Do not use generic `SESSION_ID`, an unstable process identifier, or a value shared by all ZCode sessions. If the explicit identity is empty, the marker write fails before creating a shared `no-session` marker.

## Outcome

ZCode marker writers pass a stable per-session value from runtime context through the shared helper; a missing value does not create a shared marker.

- Distinct ZCode sessions no longer share the `no-session` marker namespace.
- Existing runtime values and precedence retain their current behavior.

## Gate delta

No new workflow gate or refusal class. The helper's explicit identity argument uses ordinary input validation for an empty value; the marker recipe's existing fail-loud path and absent-marker gate remain unchanged. The origin records the shared-key failure; expected missing-source catches are zero once the ZCode runtime contract is verified, the false-positive cost is one refused marker write and the existing gate refusing its protected write, and review occurs after the first execution verifies fresh and resumed sessions.

## Assumptions

- The shared helper remains the single source used by marker writers and hook adapters. Evidence: `scripts/session_channel.py` and the skill-gate adapter contract both invoke the helper as a subprocess.
- ZCode runtime context exposes the same stable current-session identity to every plans and learn marker invocation, including resumed sessions. Evidence: `agents/skills/maintenance/zcode.md` describes the active session identifier; the task verifies availability and stability for every invocation. If this contract cannot be verified, keep the origin open and report the provider prerequisite.
- An explicit ZCode identity takes precedence over unrelated inherited runtime variables; callers without that explicit input keep the existing Claude, Cursor, and Codex environment precedence. Evidence: `scripts/session_channel.py` currently selects the first nonempty environment value, and `skill_gate.py` accepts an opaque `--session-id`. Empty explicit input must fail before the marker core and cannot use `no-session`.

Decision points requiring a grill: none remain.

## Evaluation Criteria

- **Correctness:** Every supported ZCode marker write uses its stable runtime session ID; two sessions produce different keys and repeated writes in one session use the same key. An empty explicit ID creates no `no-session` marker.
- **Compatibility:** Claude, Cursor, and Codex values retain their current environment-only precedence; no generic `SESSION_ID` fallback is introduced.
- **Documentation:** The canonical precedence contract and shared marker recipe describe the explicit ZCode source. The ZCode overlay states that this marker-only source does not enable dead-run conversion; conversion remains unsupported until a trusted channel reaches its gateway and its status-command and provider-smoke prerequisites pass.
- **Done when:** The helper selftest covers explicit-source precedence over inherited runtime variables and rejects empty explicit input; marker checks verify distinct session keys and no shared-key marker on missing input; live probes cover fresh and resumed ZCode sessions. The plan makes no dead-run conversion support claim.
- **Ship when:** No external release or human-owned prerequisite applies.

## Review Scope

**Explicit must-fix:**
- `scripts/session_channel.py` (Task 1)
- `agents/hooks/lessons-recall/README.md` (Task 1)
- `agents/hooks/skill-gate/README.md` (Task 1)
- `agents/skills/maintenance/zcode.md` (Task 1)

## Validation Commands

```bash
python3 scripts/session_channel.py --selftest
rg -n "ZCode|ZCODE|no-session" agents/hooks/skill-gate/README.md
rg -n "ZCode|ZCODE|no-session" agents/skills/maintenance/zcode.md
rg -n "ZCode|ZCODE|no-session" agents/hooks/lessons-recall/README.md
python3 scripts/plan_readiness.py docs/history/plans/2026-10-30-session-channel-zcode-runtime-derivation-empty.md
```

### Task 1: Add the verified ZCode session source to the shared helper

Context surface: `_derive()`'s existing source precedence and selftest in `scripts/session_channel.py`, the canonical precedence contract in `agents/hooks/lessons-recall/README.md`, and the observed ZCode empty-session behavior in the backlog origin.

Files:
- `scripts/session_channel.py`
- `agents/hooks/lessons-recall/README.md`
- `agents/hooks/skill-gate/README.md`
- `agents/skills/maintenance/zcode.md`

Primary class anchors:
- `_derive()` in `scripts/session_channel.py`, which selects the shared session-channel value.
- `main()` in `scripts/session_channel.py`, which parses explicit identity input and writes the selected value.

- [ ] Verify ZCode exposes a stable current-session identity in runtime context for every plans and learn marker invocation, including resumed sessions; pass it explicitly through the helper. If the runtime contract cannot guarantee this, keep the origin open and report the provider prerequisite rather than claiming support. [class: IMPLEMENTATION_REQUIRED]
- [ ] A focused selftest pins all four recognized session environment variables per fixture, passes two explicit identities while `CODEX_SESSION_ID` is set, and verifies each wins unchanged; an empty explicit identity fails before the marker core and creates no shared-key marker. [class: IMPLEMENTATION_REQUIRED]
- [ ] Marker checks use an injected temporary runtime directory and explicit project root; two distinct ZCode sessions produce different keys, and repeated writes in one session use the same key. Callers without explicit identity retain existing environment precedence, no-newline output, and empty-source behavior. [class: REPOSITORY_TEST]
- [ ] An empty explicit ZCode identity does not invoke the marker core or create a `no-session` marker in the injected temporary runtime directory; the marker recipe reports the existing fail-loud write error. Preserve existing environment-only behavior for callers without explicit identity. [class: REPOSITORY_TEST]
- [ ] The canonical precedence documentation and shared marker recipe describe the explicit identity input. The ZCode overlay says this marker-only input does not satisfy the gateway's trusted session-channel requirement; dead-run conversion remains unsupported until the gateway receives that identity and the status-command and provider-smoke requirements pass. [class: IMPLEMENTATION_REQUIRED]
- [ ] Commit: `fix: derive session channel on ZCode` [class: IMPLEMENTATION_REQUIRED]
