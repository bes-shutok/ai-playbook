# agent-runtime-layout still lists retired `receiving-code-review` as a review-staging consumer

- **Driving force:** reliability — `projects/.ai-playbook/agent-runtime-layout.md` names `receiving-code-review` as a review-staging consumer; that skill was renamed to `receiving-review`, so the mapping points at a dead name and silently misroutes (same incident class as the pr-review-hook-skill-name-ownership plan, witnessed during its Task 1 intermediate review 2026-11-20).
- **Status:** open
