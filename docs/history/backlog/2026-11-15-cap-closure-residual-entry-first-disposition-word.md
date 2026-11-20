# Backlog: cap-closure residual entries are parsed by the first "disposition" word, so a finding title containing that word never validates

- **Filed:** 2026-11-15, closeout capture (learn Step 1.8, skills-corpus)
- **Status:** open
- **Priority:** high
- **Origin class:** session-witnessed gate behaviour (the entry grammar was derived from a refusal, not from the skill text)
- **Workflow:** backlog
- **Class:** fix-class (a matcher that reads the first label-like word instead of the entry's own explicit disposition token)
- **Skill and step:** `agents/skills/review-plan/SKILL.md` cap-closure terminal shape; matcher `_cap_closure_entry_disposition` in `scripts/plan_readiness.py`

## Observed vs expected

Observed: a plan's `## Residual findings (cap closure)` section listed one entry per staged finding, each ending `(disposition: folded)`. The readiness gate refused with "cap closure terminal state under-reports the round's staged findings: no body entry carries a folded or accepted disposition for [one pattern]". That entry's title read "Follow-up disposition says none expected ...". The matcher regex takes the first `disposition` word on the line and reads the next word as the label; here that word was `says`, outside the vocabulary, so the entry was rejected although it ended with an explicit `(disposition: folded)` token.

Expected: the matcher reads the entry's explicit `disposition: <word>` token deliberately (the last one on the line, or one anchored at the entry end), or the refusal quotes the offending label word so a producer fixes it on the first pass.

## Reproduction evidence (trimmed)

1. Entry line: "- F16 `<pattern>`: The follow-up disposition says none expected although ... (disposition: folded)".
2. Run the readiness gate over a sidecar declaring the cap closure: the refusal names that pattern as under-reported.
3. Reword the title to avoid the word ("follow-up line") and re-run: the gate passes.

## Environment

- Playbook skills repo scripts, deployed copy, 2026-11-15.

## Suspected root area

The label regex is applied with a first-match search over the whole entry. The docstring says an explicit label is authoritative, but the first label-like word wins over the explicit token. Fix options: use the last match; require the parenthesized `(disposition: <word>)` form; at minimum make the refusal name the entry and the rejected word.
