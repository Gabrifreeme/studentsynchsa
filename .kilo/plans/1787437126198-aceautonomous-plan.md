# Plan: Make ACEsi Fully Autonomous & General-Purpose

## Goal
Transform ACEsi from a StudentSyncSA-specific automation tool into a **general-purpose autonomous agent framework** that can handle any instructed task — code, UI, network, system — without app-specific hardcoding, while staying fully autonomous (self-directing, self-healing, self-hosting).

## Context (from codebase inspection)

### Current Architecture
- **`server.py`** (5857 lines): Core Flask brain. LLM dispatch loop, tool execution, CDP bridge, memory/journal/tasks system, ntfy inbox auto-poll, /chat and /opencode agent loops.
- **LLM providers**: Groq (primary), Cerebras, OpenRouter (with fallbacks), local Ollama as offline fallback. Uses full `TOOLS_SCHEMA` for cloud, `OLLAMA_TOOLS_SCHEMA` for local.
- **Tools**: 40+ tools in 4 domains: `ui` (Android adb + CDP), `code` (file/git/flutter), `net` (curl), `ctrl` (restart/notify).
- **`CODE_AGENT_PROMPT`**: 3250+ char system prompt, deeply StudentSyncSA-specific (KNOWN_APP_STRUCTURE, specific URLs, build_apk, flutter_test, etc.).
- **Autonomy**: ntfy inbox loop, deterministic step-list executor (parses user prose → tool calls), ITS shortcut replay, auto-bypass cert warnings, auto ui_dump after actions, screen-state guards, round caps, repeat detection.
- **Memory**: SQLite (conversations, memories, journal, config), JSON (tasks/events/timers/alarms/sessions).

### Hardcoded StudentSyncSA Dependencies (block generalization)
1. `APP_PACKAGE = "com.studentsyncsa.studentsyncsa"` in devtools_service.py
2. `ACE_PACKAGE` in server.py — "com.studentsyncsa.studentsyncsa"
3. `university_webview_screen.dart` — navfix injection specific to ITS portal
4. `CODE_AGENT_PROMPT` — mentions "StudentSyncSA Flutter project" throughout
5. `_ITS_TASK_KEY` / `_ITS_SHORTCUT_RE` / `_resolve_ui_task` — ITS form shortcut only
6. `_classify_message()` — domain keywords include "its portal", "univen"
7. `build_apk` — hardcoded `flutter build apk` for StudentSyncSA
8. `_UI_KEYS` — hardcoded Android key codes
9. `_cert_warning_directive` — references "ITS portal" specifically
10. `UNIVEN_ITS_STARTUP_URL` — hardcoded Venda ITS URL
11. `ui_app_open` always opens StudentSyncSA
12. `ntfy` topic is "ACEsi" (could be per-context)

### Existing Autonomous Capabilities (to preserve + generalize)
1. ntfy.sh inbox auto-poll (message → model → reply → phone notification)
2. Deterministic step-list parser (`_ui_script_steps`, `_execute_ui_script`) — bypasses LLM for structured instructions
3. ITS shortcut replay (memory-saved task → splice into message → execute)
4. Auto ui_dump after every screen-changing action
5. Cert bypass auto-typing ("thisisunsafe")
6. Round caps, repeat-call detection, stall recovery
7. `_extract_calls` supports multiple tool-call formats (CALL: JSON, fenced JSON, single-line JSON)
8. Self-hosting watchdog (`ace_host.py` respawns server.py)

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Generalize approach | **Config-driven plugin system** | Hardcoding removal via YAML/JSON config + modular adapters. Keeps single server.py codebase; no need for separate repos. |
| Prompt layer | **Abstract + per-context override** | Replace `CODE_AGENT_PROMPT` with `BASE_AGENT_PROMPT` + context-specific overlays. System prompt injects target app/tool list dynamically. |
| Tool system | **Capability-gated, registry-based** | Tools self-declare capabilities (requires_app, requires_cdp, requires_project). `_call_tool` checks capability gates. General tools always available; specialized tools need config. |
| Device access | **Abstract device manager** | Replace hardcoded `APP_PACKAGE` with `DeviceContext` that can switch between apps, simulators, browsers. CDP target selectable by URL fragment or package name. |
| Task execution | **General step-list executor** | Extend `_ui_script_steps` to handle generic verbs: `run`, `edit`, `fetch`, `tap`, `type`, `assert`, `wait_for`, `loop`, `if`. Not just UI steps. |
| Autonomy model | **Goal-directed + self-correcting** | Each task has a goal predicate. After each action, check if goal is met. If not, re-plan. Auto-recover from failures. |
| Memory model | **Namespaced context memory** | Per-context keys (`memory.get("univen:id_number")`, `memory.get("github:token")`). Memory persists across sessions but is scoped to the task domain. |
| Provider config | **Per-context LLM profiles** | Allow each context to specify preferred provider + fallback chain (e.g. "code-heavy tasks use Groq, offline tasks use Ollama"). |

## Implementation Plan (Ordered)

### Phase 1: Configuration & Context System (foundation)
1. **Create `ace_config.yaml`** — root config with contexts (key-value namespace, not hardcoded).
   - Each context: `name`, `app_package` (optional), `cdp_url_fragment` (optional), `project_root` (optional), `llm_profile` (primary + fallbacks), `allowed_domains` (ui/code/net/ctrl subset), `memories` (key-value defaults), `env` (env var values).
2. **Create `ace_context.py`** — Context manager:
   - `load_context(name)` → returns context dict with defaults merged.
   - `active_context()` / `set_context(name)` → switches active context.
   - Context exposes: `app_package`, `project_root`, `allowed_tools`, `llm_profile`, `startup_url`, `memories`.
3. **Refactor `server.py` globals** — replace `ACE_PACKAGE`/`UNIVEN_ITS_STARTUP_URL` with context lookups. Keep backward compat via `ace_config.yaml` defaults for the StudentSyncSA context.

### Phase 2: Abstract Tool System
4. **Create `ace_tools.py`** — tool registry with capability declarations:
   - Each tool annotated with `capabilities`: `["app_open"]`, `["cdp"]`, `["file_system"]`, `["network"]`, `["build"]`, etc.
   - Registry resolves tools to actual function + required context.
   - `ui_app_open` generalized: `ui_app_open({"package": "com.x.app"})` — if package omitted, use active context's `app_package`.
   - `build_apk` → `build_app({"project": "path", "platform": "apk|aab"})` — generic.
5. **Refactor `_call_tool`** to consult registry + context capabilities before dispatch. Reject tools whose capabilities aren't satisfied by the active context.
6. **Migrate `/chat` and `/opencode` dispatch** to use the registry + context for tool schema filtering.

### Phase 3: General-Purpose Prompt System
7. **Replace `CODE_AGENT_PROMPT`** with a templated `BASE_AGENT_PROMPT`:
   - Injects `active_context.tool_list` (the tools available in this context).
   - Injects `active_context.goal_template` (optional: task-specific goal framing).
   - Injects `active_context.known_structure` (optional: app structure description).
   - Keeps the anti-stall directives (force tools, dump-before-tap, round caps, repeat detection) — these are general.
8. **Create `CHAT_AGENT_PROMPT`** — generic agent prompt for non-code tasks (UI navigation, network probing, system tasks). Reuses the CODE_AGENT_PROMPT structure but with broader tool set.
9. **Create `AUTONOMOUS_AGENT_PROMPT`** — for self-directing tasks: "You have goal X. Plan, execute tools, verify, re-plan if needed. Maximize autonomy."

### Phase 4: General Step-List Executor
10. **Extend `_ui_script_steps` → `ace_task.py:parse_steps(text)`**:
    - Parse verbs: `run`, `edit`, `fetch`, `write`, `read`, `tap`, `type`, `swipe`, `dump`, `screenshot`, `assert`, `wait_for`, `loop`, `if`, `else`.
    - Support `ui_select`, `ui_fill`, `ui_scroll`, `ui_key`, `restart`, `cdp_*`, `curl`.
    - Each step: `(action, args, verifier, timeout)`.
    - `verifier`: optional lambda/text that checks result (e.g., "assert 'Login' appears", "assert url contains 'portal'").
11. **Create `ace_task.py:execute_task(steps, goal_predicate)`**:
    - Iterates steps, calls tools via `_call_tool`.
    - After each screen-changing step, auto-dumps (ui_dump / cdp_dom_state).
    - Checks `goal_predicate(result)` after each step — if met, stop early.
    - On failure: re-plan (call LLM with failure context → new step list) up to N retries.
    - Returns: `TaskResult(status, steps_executed, final_state, errors)`.

### Phase 5: Generic Task Entry Points
12. **New `/run_task` endpoint** — POST `{"task": "...", "context": "optional"}`:
    - Resolves context (or auto-detects from task content).
    - If task matches a saved shortcut (generalized ITS pattern), splice it.
    - If task matches step-list format, execute via `parse_steps` → `execute_task`.
    - If not, fall back to chat LLM loop with appropriate prompt.
    - Returns task progress stream + final result.
13. **New `/autonomous` endpoint** — POST `{"goal": "...", "context": "..."}`:
    - Uses `AUTONOMOUS_AGENT_PROMPT` + full tool schema.
    - Goal: a predicate (e.g., "page contains 'Done'").
    - Self-directing: plan → execute → verify → re-plan until goal met or budget exhausted.

### Phase 6: Generalize Device & CDP Access
14. **Refactor `devtools_service.py`**:
    - Remove hardcoded `APP_PACKAGE`.
    - Add `set_device_context(package, url_fragment)`.
    - CDP discovery picks target by `url_fragment` or `package`.
    - `ui_app_open` uses active context's package.
15. **Generalize `tool_ui_app_open`**: accept `package` arg; default to context.

### Phase 7: Generalize Autonomy Features
16. **Generalize ITS shortcut**: Rename concept to "saved task". `/task/save` stores a step-list in memory. `/task/rerun` replays. Pattern: "do X again" → splice saved steps.
17. **Generalize cert bypass**: Any HTTPS warning → type "thisisunsafe" (already generic, just remove ITS-specific comment).
18. **Generalize ntfy**: Topic per context. `/notify/config` to set topic.
19. **Generalize auto-dump**: After any tool that changes state (`ui_tap`, `cdp_evaluate` that navigates, `run_command` that builds). Hook into `_call_tool` result.

### Phase 8: Self-Hosting & Watchdog
20. **Generalize `ace_host.py`**: Already respawns server.py. Add config for which contexts to pre-load.
21. **Add `ace_watch.py`** — monitors task queue, triggers `_run_task` autonomously on schedule or ntfy message.
22. **Background task scheduler**: `/tasks/schedule` — POST `{"cron": "...", "task": "...", "context": "..."}` → runs task on schedule without user prompting.

### Phase 9: Testing & Validation
23. **Write `ace_general_test.py`** — tests:
    - Context switching (StudentSyncSA → generic web task).
    - Tool capability gating (code tools fail without project context).
    - Step-list parsing for `edit`, `run`, `tap`, `curl`.
    - Task execution with goal predicate.
    - ntfy inbox → task → reply round trip.
24. **Node-verify the navfix JS generation still produces valid JS** (use the existing test infrastructure).

## Open Questions / Risks

1. **Model quality**: Ollama qwen2.5:3b is weak for complex multi-step tasks. Consider requiring cloud provider for autonomous mode (fallback to Ollama only when offline).
   - *Resolution*: `llm_profile` per context. Autonomous tasks default to cloud if available; local model only for UI tap/coordinate tasks where the step-list executor handles planning.

2. **Safety / scope creep**: A general autonomous agent could do destructive things. Need strong capability gating.
   - *Resolution*: Tools declare capabilities. Context config restricts `allowed_tools`. Destructive tools (`write_file`, `run_command` with shell) require explicit context enable.

3. **Backward compatibility**: StudentSyncSA-specific shortcuts and workflows must keep working.
   - *Resolution*: StudentSyncSA becomes one named context in `ace_config.yaml` with all current behavior as defaults. Existing `/chat`, `/opencode`, ntfy loops work identically with the StudentSyncSA context.

4. **Prompt size on local model**: Injecting full tool schema + context + goal may exceed Ollama context limits.
   - *Resolution*: Use `OLLAMA_TOOLS_SCHEMA` (compact) for Ollama. Trim context block for local model (light mode `build_context_block` already does this).

## Validation Plan
- `python -m pytest ace_general_test.py` (or `python ace_general_test.py`) — all tests green.
- `python server.py` — starts, loads StudentSyncSA context by default.
- `curl -X POST /autonomous -d '{"goal":"navigate to https://example.com and screenshot","context":"generic"}'` — navigates + returns screenshot.
- `curl -X POST /run_task -d '{"task":"1. read_file lib/main.dart\n2. grep TODO\n3. edit_file ...\n4. flutter_test"}' — executes step list.
- ntfy: send "do the ITS application again" to the topic → ACEsi executes the saved task.
