# Severity calibration (code review)

Canonical severity rules for all code-review sub-agents and orchestrators (`doing-code-review`, `review-loop`, branch/plan code passes). Severity reflects **user impact and operability risk**, not comment length or reviewer effort.

**Upstream pattern:** adapted from [umputun/cc-thingz](https://github.com/umputun/cc-thingz) planning exec review prompts; deep links in `skill-upstream-catalog.md` **Merged pattern index**. Mapped to this repo's four-tier model below.

## Required on every finding

1. Set `severity` explicitly to one of: `Critical`, `High`, `Medium`, `Low`.
2. When uncertain after applying the decision procedure, choose **`Low`** (same default as upstream `MINOR` when no tag is present).
3. In `body`, include one sentence **why this severity** (orchestrator copies to Analysis / Severity calibration).

Orchestrators may **upgrade** or **downgrade** after verification; record deltas in staging **Severity calibration** with a reason tied to this file.

## Tier definitions

| Tier | Meaning | Merge posture (typical) |
|------|---------|-------------------------|
| **Critical** | Safe deploy is unreasonable without fix: exploitable security with trivial reach, guaranteed data loss/corruption in enabled traffic, crash/panic on normal startup path, total feature outage when flag is on | Block merge; `REQUEST_CHANGES` when posting |
| **High** | Wrong result, data loss, or security exposure reachable in normal or flag-enabled traffic without exotic timing; silent corruption; auth bypass | Block merge; `REQUEST_CHANGES` when posting |
| **Medium** | Behavior regression or contract drift in normal traffic; documented edge-case correctness gap; missing test where the **untested path itself** prevents a real failure mode | Non-blocking `COMMENT` by default; counts toward review-loop Medium+ thresholds |
| **Low** | Style, naming, simplification/yagni nits, observability gap while behavior is correct, dead code, doc/comment-only fixes, optional cleanup | Non-blocking; optional inline comment |

**Critical vs High:** use **Critical** when the failure is immediate and total for typical operators (deploy breaks, exploit needs no preconditions, corruption is guaranteed). Use **High** when impact is real but narrower (edge timing, flag-gated path that will ship enabled, wrong totals on common inputs).

## Decision procedure (apply in order)

1. **Wrong outcome for users or data?** (money, PII, auth, persisted state, API contract violated in happy path) → **High** or **Critical** (step 1 split above).
2. **Security exposure?** Untrusted input reaches dangerous sink without validation → **High** minimum; **Critical** if trivially exploitable in production config.
3. **Crash, panic, or unrecoverable error on common path?** → **Critical** if on deploy/startup; **High** if on typical request handling.
4. **Behavior wrong only in edge case, race, or documented MVP limitation?** → **Medium** unless data loss/security in that edge → then **High**.
5. **Underlying behavior correct; gap is tests, metrics, docs, naming, or simplification?** → **Low**.
6. Still unsure → **Low**.

## Category defaults

| Finding type | Default | Promote to Medium when | Promote to High/Critical when |
|--------------|---------|------------------------|--------------------------------|
| **Simplification / yagni / over-engineering** | Low | Complexity hides a correctness bug or makes a safe fix impossible | (rare) abstraction causes active data loss |
| **Metrics / observability** | Low | Missing telemetry masks an active production problem on a hot path | (essentially never) |
| **Missing test** | Low | Untested path is the **only** guard for a real failure mode (blast-radius bound) | Untested path allows data loss or security bypass |
| **Documentation / inline comment** | Low | (none) | Contract in PR-visible doc contradicts code → **Medium** (contract drift) |
| **Prose clarity** | Low | (none) | (none) |
| **Concurrency / race** | Medium | Race window achievable under stated TTL/load; verify I/O cost before claiming | Data loss or double-spend in achievable window → **High** |
| **Security** | High | (none) | Trivial exploit → **Critical** |
| **Feature-flag gated bug** | Same as ungated | Flag does **not** reduce severity; judge impact when flag is on |

**Pre-existing pattern** does not reduce severity of **new** code introduced by this PR. Note pre-existing instances as EXISTING debt at **Low** or omit (`doing-code-review` §4.11).

**NEW vs EXISTING debt:** structural/size findings on files this PR only touched lightly → downgrade to **Low** or omit.

## Upstream mapping (cc-thingz)

| cc-thingz tag | Typical local severity |
|---------------|------------------------|
| `CRITICAL` | `Critical` or `High` (use decision procedure) |
| `MAJOR` | `Medium` or `High` |
| `MINOR` | `Low` |
| (missing tag) | `Low` |

## Sub-agent output

Return JSON findings with `severity` set per this file. Lead `body` with the issue; include **Why this severity** (one sentence) in `body` or under `**Analysis**`.

**Depth by severity** (orchestrator `doing-code-review` §4.12): `Medium+` needs four Comment sections; `Low` needs claim + evidence + suggestion.

## Orchestrator synthesis

When merging duplicate findings from multiple agents, stage the **highest** verified severity unless evidence supports downgrade (record in **Severity calibration**).

**Blocking summary line** (optional in staging Counts): `Blocking: yes` when any staged **Critical** or **High** finding remains after triage; `Blocking: no` otherwise. Aligns with cc-thingz `has_blocking` when CRITICAL/MAJOR present.
