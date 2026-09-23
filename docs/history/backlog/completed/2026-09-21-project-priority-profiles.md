# Backlog: project-priority profiles — per-project deferral classes for formal hardening and security

Status: done
Priority: high
Workflow: backlog
Source: user directive 2026-09-21 (Andrey, this repo): formal fixes are not a priority on this personal repo and must be deferred with recorded reasons; deferral classes are a PROJECT property — pet/personal projects defer formal hardening AND security concerns, while company projects may invert that (security first), and priority conflicts on company projects should be consulted with the user each time rather than decided silently.
Severity: High (the triage/exit/selection rules currently rank all valid findings on one global severity scale, so every consumer project inherits this repo's priorities whether or not they fit; the P32/P33 formal triage — 10 of 14 origins formal — and the 2026-09-11 security-threat-model deferral are the witnesses)

## Problem

Guidelines section 64 fixes one global principle ordering (efficiency, token usage, simplicity, code quality), and the triage/exit/selection rules treat every valid finding as one severity-ranked queue. Nothing records that DEFERRAL CLASSES are a per-project property: the same finding — a Low robustness pin, a defense-in-depth hardening suggestion, a security-label concern — is defer-by-default on a personal repo and may be fix-by-default on a company repo. Today that judgment lives only in ad-hoc triage notes and user corrections.

## What it should become

1. **Priority profile in facts**: each project's `facts.md` (or equivalent) carries a profile — at minimum `priority_order` and a `deferred_classes` list (e.g. `formal-hardening`, `security-hardening`, `prose-polish`). Unspecified projects fall back to the global guidelines ordering with formal-hardening defer-by-default.
2. **Triage class step**: `receiving-review` / `review-loop` triage classifies each finding real vs formal before severity: real = witnessed failure, recovered wall-clock/tokens, or correctness of behavior; formal = gates-on-gates, naming/wording/pin audits, vacuity checks, hypothetical-input hardening. Formal findings route to deferred-backlog with the class + one-line reason (the existing deferral-line convention), never folded at exit.
3. **Selection skip AND profile-aware grouping**: the maintenance skill's survey/grouping step (which decides which items batch into which plan) must group by profile-aware families — deferred-class items are skipped without re-triage (the stand-down guard already checks `deferred/`; extend it to consult the profile), and the grouping itself must respect the profile: on this repo, formal items never ride along as fillers in a real-fix batch (the P30/P34 mixed-grouping problem this week), while a company-profile project might legitimately batch hardening items a personal profile would defer. The skill's survey output should record the class of every item it groups, so a plan's origin list is auditable against the profile.
4. **Consultation rule**: when a triage would defer a security or correctness finding on a company-profile project (or fold one on a personal-profile project), surface to the user instead of deciding silently.
5. **Witnesses to cite**: 2026-09-11 threat-model deferral (malicious-worker apparatus), 2026-09-21 formal-hardening triage (13 items deferred in one pass), the P32/P33 groups.

## Grill points

Where the profile lives (per-repo facts vs guidelines table); default-profile semantics; whether "security" is a deferral class or a lens that modulates severity; interaction with guidelines section 64's fixed global ordering.
