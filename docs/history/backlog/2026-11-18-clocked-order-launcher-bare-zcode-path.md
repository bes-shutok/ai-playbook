# Backlog: the clocked-order fire template shells a bare `zcode`, which launchd's PATH cannot resolve

- **Filed:** 2026-11-18, learn run over the interactive exec carrier session (sess_0df7e07a)
- **Status:** open
- **Workflow:** backlog
- **Priority:** high
- **Class:** fix-class
- **Origin class:** witnessed environment-contract defect (silent scheduler-fire loss)
- **Skill/step:** `scripts/execute_plan_resume_watcher.py` (`clocked_order_fire_command`, the `zcode = str(zcode_executable or "zcode")` default) and the launchd clocked-order chain (`scripts/execute_plan_runtime.py --operation clocked-order-schedule`)
- **Cluster:** docs/history/backlog/2026-11-13-known-red-gates-consumed-baseline.md (carrier machinery defects family; that row owns gate-baseline consumption, this row owns the launcher's binary-resolution contract)

## Observed versus expected

**Observed:** four scheduled carriers (15:53, 16:11, 16:29, 16:47 local, 2026-11-18) fired on time, touched their sentinels, and exited 127 - `/bin/sh: zcode: command not found`. The fire template embeds a bare `zcode --prompt ...`, resolved interactively from a user-local bin directory; launchd's `/bin/sh` PATH (`/usr/bin:/bin:/usr/sbin:/sbin`) never carries that directory, so every launchd-fired carrier died before starting its session, and the loss surfaced only when the operator asked why sessions did not start. The in-session workaround patched each generated plist to the discovered absolute binary path and reloaded the jobs.

**Expected:** `clocked_order_fire_command` resolves the harness binary at schedule time (the module already imports `shutil.which` patterns elsewhere): resolve `zcode` through `shutil.which`, fail the `clocked-order-schedule` operation with a named refusal when unresolved, and embed the absolute path in the template. A schedule-time probe (run the resolved binary's `--version` once) would additionally gate "template generated" from "template runnable".

## Reproduction evidence (trimmed)

`launchctl list` rows for the fired labels show exit status 127; each job's `.err.log` carries `/bin/sh: zcode: command not found`; the sentinels were touched at fire times. Re-arming the same orders with the absolute path in the generated plist string (plus `launchctl unload/load`) is the recorded successful workaround.

## Environment context

launchd agents, macOS; the harness binary lives in a user-local bin directory (the interactive shell resolves it via profile PATH). Witnessed 2026-11-18 on the clocked-order chain; the same bare-binary shape applies to any fire template this module composes.

## Suspected root area

The `zcode_executable or "zcode"` default predates the binary's move off the system PATH; no schedule-time resolution or probe gates the generated template on the binary being resolvable in the fire environment.
