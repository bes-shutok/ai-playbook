# Scope domain redaction by repository visibility and preserve valid service links

Captured: 2026-09-28 (source: consumer closeout, done pre-commit sensitive-data scan)
Status: done (2026-09-30; executed+landed docs/history/plans/completed/2026-09-30-done-scan-visibility-scoped-redaction.md, squash main c397a6a1, exec review r1 ready=yes zero blocking)
Priority: high
Workflow: backlog
Class: correctness
Driving force: utility
Origin class: consumer-feedback (company)
Consumer urgency: Consumer projects using the done workflow need domain-redaction rules scoped to repository visibility; the skills-repo personal priority profile must not defer this shared-skill fix as formal-hardening for the skills repo alone.

## Problem

During a consumer project closeout, the pre-commit sensitive-data gate treated an ordinary internal Jira hostname as sensitive. The link contained no credential, token, or secret query value. To pass the gate, the hostname was removed and only the ticket identifier remained. That made the plan less useful and changed its digest, requiring another review pass.

An internal service hostname is not inherently a secret. The closeout ran in a company project, where a normal Jira link is useful provenance. Public-artifact hygiene may need to redact employer-specific hostnames, but that rule should not erase valid links in private company repositories. This backlog uses no actual hostname or ticket identifier.

A second consumer closeout reproduced the issue in source brag records: the generic pre-commit scan flagged valid internal Jira links in untracked files, even though the project owner confirmed those links are expected evidence in this repository. This confirms the need to distinguish repository policy from credential detection and public-artifact redaction.

## Expected

- Preserve valid internal service links in private company repositories unless the URL contains actual credential or token material.
- Apply employer-domain and hostname redaction when preparing public artifacts, not as a blanket rule for every repository.
- Keep secret checks for credentials, access tokens, signed or secret query parameters, and known secret formats active in both private and public repositories.
- Do not solve this with a global Jira-host allowlist. Make the decision depend on repository visibility or an explicit confidentiality policy, then inspect the whole URL for secrets.
- Add fixtures for a valid internal Jira link in a private-repository scan, the same link in a public-artifact scan, and credential-bearing URLs in both contexts.

## Evidence

The review record shows the prior round no longer matched the plan after only its host was stripped; a fresh full panel then found no blockers. The host edit did not change the implementation contract or readiness evidence.

## Suspected root area

The done gate applies public-hygiene employer-domain checks without first distinguishing a private project repository from a public artifact. Trace whether the scanner receives repository visibility or has a facts-derived policy for that boundary before selecting the smallest correction.

## Exact location

`agents/skills/done/SKILL.md`, pre-commit sensitive-data-scan gate and its remediation guidance; then trace the resolved scanner and employer-domain patterns.

## Severity and source reference

Severity: medium

Source: consumer closeout, plan review became stale after host-only sanitation; capture hygiene: scan-public-hygiene --files pass.

## Why not fixed now

The user requested durable backlog work and has not authorized changing the shared done policy in this capture task.

## Dedup probe

Search terms: `sensitive-data scan`, `hostname`, `domain redaction`, `valid service link`. Nearest: `docs/history/backlog/rejected/2026-09-22-done-sensitive-data-scan-credential-shaped-patterns.md`, which covers bare credential vocabulary false positives and explicitly deferred domain changes without a witnessed consumer failure. This item is distinct: it records a witnessed host-only redaction in a private consumer repository and asks for visibility-scoped policy.

## Suggested fix

Pass repository visibility or an explicit confidentiality classification into the done gate and apply employer-domain redaction only to public artifacts. Keep credential-pattern checks active everywhere, and add focused private/public link fixtures before changing remediation guidance.
