# Phone auto-connect guard plan

## Context

Chris gave ACEsi (this repo, `server.py`) the task:

> "Connect to my Android phone using the auto-connect tool Kilo Code gave you. Then call ui_dump and report device id, screen size, foreground app, and USB/TCP-IP."

The task was hijacked by the deterministic step-list executor and re-ran a previous ITS login test instead:

```
cdp_navigate https://the-internet.herokuapp.com/login
cdp_evaluate #username = 'tomsmith'
cdp_evaluate #password = 'SuperSecretPassword!'
cdp_evaluate button[type=submit].click()
Done — steps executed: ui_dump.
```

Chris wants four facts confirmed, then a bailout guard in `_execute_ui_script` matching the pattern OpenCode added for `cdp_navigate`.

## Answers to the four questions (already established by reading the code)

1. **Tool name: `ui_connect`** — literal string in all registries.
2. **Present in all four layers:**
   - `TOOLS_SCHEMA` (server.py:7021) — yes
   - `_TOOLS` dispatcher (server.py:6904) — yes
   - `_TOOL_DOMAINS` (server.py:7650, domain `"ui"`) — yes
   - context tool-cap list (`ace_config.yaml` studentsyncsa, line 50) — yes
3. **ADB binary:** no configured path. `_ui_adb` (server.py:5683) calls `["adb"]` on PATH. `_android_device_id` (server.py:4346) also bare `adb`. No `platform-tools` path constant exists.
4. **Commands run by `tool_ui_connect` (server.py:5765):** `adb devices -l` only (via `_adb_connected_devices`). No `adb kill-server`, no `adb start-server`, no `adb connect` retry loop — it does ONE `adb connect <host>` per candidate (server.py:5802), then re-checks `adb devices -l`. Wireless fallback is mDNS discovery (`adb mdns services`) + `ACE_ADB_TARGETS` env. On failure it returns the raw `adb said:` line (truncated 400 chars) plus a diagnosis, not a generic message.

## Root cause of the hijack

`_execute_ui_script` already has two bail-out guards (server.py:10083, 10087), but neither fires for this task:

- `_needs_model_driven_ui` requires `https?://`, `dev tools`, `cdp_`, `f12`, `network ...`, `status code`, `console ...`, `dom state`, `javascript console`. The task has none.
- `_needs_phone_link` requires `adb`, `scrcpy`, `auto-connect`, `wireless debugging`, `device id/serial/list`, `foreground app`, `usb`, `tcp/ip`, `adb over ...`, `connect to ... phone/device/tablet`, `phone/device/tablet connect/attach/pair`, `unauthorized`, `no devices/emulators`. The task contains none of these tokens — "phone" appears only inside "Android phone", which the regex does not match because it requires `phone` adjacent to a connect verb.

So both guards pass. Then:

- `_resolve_ui_task` returns None for this message — verified: `_ITS_RERUN_RE` does not match, and the message is 220+ chars so the bare-shortcut branch is skipped. The canned ITS login list is NOT the source.
- `_ui_script_steps` is called on the raw message. It gates on `_ui_task(user_message)`, which is True because the message literally contains the token `ui_dump` (server.py:8824). The parser therefore extracts `("ui_dump", ...)` and the executor runs `_call_tool("ui_dump", {})`.
- With no phone attached, `ui_dump` falls back to the attached browser/WebView and returns the login DOM. The executor reports `Done — steps executed: ui_dump.` — exactly the observed output.

So the hijack is: **the task text names a real tool (`ui_dump`) that the deterministic parser treats as a step list, and the executor runs it in isolation without first doing the connect step the task requires.** The missing piece is a guard that recognizes "this is a device-reachability task, not a tap script" and defers to the model-driven loop, where `ui_connect` + `ui_device` are available.

## Plan

### Task 1 — Add a phone-connect bailout guard to `_execute_ui_script`

Insert a third bail-out check before `_resolve_ui_task`, mirroring the existing two (server.py:10083-10093):

- New regex `_PHONE_CONNECT_TASK_RE` covering the phrasings Chris actually uses: bare `phone`/`device`/`tablet` with a connect verb, `auto-connect`/`auto connect`, `adb`, `wireless debugging`, `device id`/`screen size`/`foreground app`, `usb`/`tcp`/`tcp-ip`, `connect to my ...`, `unauthorized`, `no devices`.
- Function `_needs_phone_connect(user_message)` returning bool.
- In `_execute_ui_script`, after the two existing checks, call it and `return None` (defers to the model-driven loop where `ui_connect`/`ui_device` live) with a print line matching the existing style.

### Task 2 — Verify the guard fires and the other paths stay clean

- Run the exact task text through `_needs_phone_connect`, `_needs_model_driven_ui`, `_needs_phone_link`, `_resolve_ui_task`, `_ui_script_steps` and confirm only the first returns True and the rest return None/empty.
- Confirm `ui_connect` is resolvable via `_resolve_tool_name` and callable via `_call_tool("ui_connect", {})`.
- Restart the server and re-run the task end-to-end; confirm the model-driven loop is reached and `ui_connect` is offered in the schema.

## Out of scope

- Adding `adb kill-server`/`start-server` to `tool_ui_connect` (Chris asked what it does, not to change it).
- Touching the OpenCode harness itself (separate project).