# Backlog: review-plan round sub-agents die to harness inactivity timeouts and transient rate limits without anti-idle prompt discipline

Status: done
Priority: medium
Workflow: backlog

## Observed vs expected

During one plans-authoring run (2026-09-19/20), review-plan rounds launched as sub-agents
failed three ways before the anti-idle prompt discipline was added: two attempts killed by
the harness's 600-second inactivity window (the agents were alive but quiet during long
reads/worker phases), one killed by a transient provider 429 with no retry. After the
prompt gained explicit anti-idle discipline (no more than ~2-3 minutes without a tool call
or progress message; file reads chunked to <=400 lines; no single command expected over 60
seconds; one retry on rate-limit errors), every subsequent round completed. Expected: the
plans skill's Plan Quality Gate sub-agent template carries this discipline by default
instead of each authoring session rediscovering it.

## Suggested fix

Add to the plans skill's Plan Quality Gate sub-agent prompt template (and review-plan's
orchestrator guidance): the anti-idle runtime-discipline paragraph (short calls, chunked
reads, bounded commands, progress messages between workers, retry-once-on-429) as required
text for every review-round launch.

## Witnesses

- 2026-09-19 ~22:30: two r3 launches returned "Subagent was inactive for 600000ms".
- 2026-09-20 ~07:00: an r3 relaunch died on `[1302]` rate limit mid-round.
- 2026-09-20 12:00: r4 launches with the discipline paragraph completed in 18-22 minutes
  with no timeouts.
