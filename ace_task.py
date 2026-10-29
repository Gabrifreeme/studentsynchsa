# ace_task.py
# General-purpose step-list executor for ACEsi.
#
# A "task" is a list of steps, where each step is either:
#   - A tool call: {"tool": "ui_tap", "args": {"x": 540, "y": 1200}}
#   - A sub-task (recursive): {"task": [...]}
#   - A wait/condition: {"wait_for": {"tool": "ui_dump", "contains": "Home"}}
#
# The executor walks the steps in order, calling tools via the server's TOOLS
# dispatch. It respects auto_dump gating: ui_tap/ui_swipe only fire after the
# most recent ui_dump. It can also run in "autonomous" mode where a model is
# driven step-by-step (the model produces the next step each turn).
#
# Usage from server.py:
#   from ace_task import run_task_steps, TaskResult
#   result = run_task_steps(steps, task_name="...", server=server_ref)

import time
import threading


class TaskResult:
    def __init__(self, name=""):
        self.name = name
        self.steps_run = 0
        self.steps_passed = 0
        self.steps_failed = 0
        self.errors = []
        self.outputs = []
        self.start_time = time.time()
        self.end_time = None
        self.aborted = False

    def summary(self):
        self.end_time = time.time()
        elapsed = round(self.end_time - self.start_time, 1)
        status = "ABORTED" if self.aborted else ("PASSED" if self.steps_failed == 0 else "FAILED")
        return {
            "name": self.name,
            "status": status,
            "steps_run": self.steps_run,
            "passed": self.steps_passed,
            "failed": self.steps_failed,
            "errors": self.errors,
            "elapsed": elapsed,
        }


def _call_tool(server, name, args):
    """Wrapper that calls server module's _call_tool with proper arg unpacking."""
    try:
        import server as srv
        return srv._call_tool(name, args or {})
    except Exception as e:
        return False, str(e)


def run_task_steps(steps, task_name="", server=None, max_steps=500,
                   auto_dump=True, on_step=None):
    """Execute a list of step dicts against `server`'s TOOLS registry.

    Args:
        steps: list of step dicts (see module docstring).
        task_name: label stored in the result.
        server: server instance with _call_tool(name, args_dict).
        max_steps: safety cap on total tool calls.
        auto_dump: if True, inject ui_dump before ui_tap/ui_swipe unless
                   the last step was a ui_dump.
        on_step: optional callback(step_dict, result_dict) called after each step.
    Returns: TaskResult
    """
    if server is None:
        # Try to import the running server module lazily
        try:
            import server as srv_mod
            server = getattr(srv_mod, "server_instance", None)
        except Exception:
            pass
    if server is None:
        r = TaskResult(task_name)
        r.aborted = True
        r.errors.append("run_task_steps: no server instance available")
        r.end_time = time.time()
        return r

    result = TaskResult(task_name)
    last_was_dump = not auto_dump
    call_count = 0

    for i, step in enumerate(steps):
        if call_count >= max_steps:
            result.aborted = True
            result.errors.append(f"max_steps ({max_steps}) reached at step {i}")
            break

        if not isinstance(step, dict):
            result.steps_failed += 1
            result.errors.append(f"step {i}: not a dict ({step!r})")
            continue

        # Sub-task recursion
        if "task" in step:
            sub = run_task_steps(step["task"], task_name=f"{task_name}.{i}",
                                 server=server, max_steps=max_steps,
                                 auto_dump=auto_dump, on_step=on_step)
            result.steps_run += sub.steps_run
            result.steps_passed += sub.steps_passed
            result.steps_failed += sub.steps_failed
            result.errors.extend(sub.errors)
            result.outputs.extend(sub.outputs)
            if sub.steps_failed > 0:
                result.steps_failed += 1
                result.errors.append(f"sub-task {i} failed")
                if on_step:
                    on_step(step, sub.summary())
                break
            if on_step:
                on_step(step, sub.summary())
            continue

        # Wait-for condition
        if "wait_for" in step:
            wf = step["wait_for"]
            tool = wf.get("tool", "ui_dump")
            contains = wf.get("contains", "")
            timeout = wf.get("timeout", 30)
            deadline = time.time() + timeout
            found = False
            while time.time() < deadline:
                ok, msg = _call_tool(server, tool, wf.get("args", {}))
                call_count += 1
                result.steps_run += 1
                if ok and contains and contains.lower() in str(msg).lower():
                    found = True
                    result.steps_passed += 1
                    result.outputs.append({"step": i, "tool": tool, "result": "PASS"})
                    break
                time.sleep(0.5)
            last_was_dump = tool == "ui_dump"
            if not found:
                result.steps_failed += 1
                result.errors.append(f"step {i}: wait_for '{tool}' did not contain '{contains}' in {timeout}s")
            if on_step:
                on_step(step, {"step": i, "result": "PASS" if found else "FAIL"})
            continue

        # Regular tool call with auto-dump injection
        tool_name = step.get("tool") or step.get("command")
        args = step.get("args") or step.get("arguments") or {}

        if not tool_name:
            result.steps_failed += 1
            result.errors.append(f"step {i}: missing 'tool' key")
            continue

        # Auto-dump before tap/swipe
        if auto_dump and tool_name in ("ui_tap", "ui_swipe") and not last_was_dump:
            ok, msg = _call_tool(server, "ui_dump", {})
            call_count += 1
            result.steps_run += 1
            if ok:
                result.steps_passed += 1
                result.outputs.append({"step": i, "tool": "ui_dump", "result": "auto-injected PASS"})

        ok, msg = _call_tool(server, tool_name, args)
        call_count += 1
        result.steps_run += 1

        step_out = {"step": i, "tool": tool_name, "args": args,
                    "ok": ok, "msg": str(msg)[:300]}
        result.outputs.append(step_out)

        if ok:
            result.steps_passed += 1
        else:
            result.steps_failed += 1
            result.errors.append(f"step {i}: {tool_name} -> {msg}")
            if on_step:
                on_step(step, step_out)
            break  # stop on first failure

        last_was_dump = tool_name in ("ui_dump", "ui_assert_text", "ui_assert_visible")

        if on_step:
            on_step(step, step_out)

    return result


def _truncate_messages(messages, max_tokens=2000):
    """Keep conversation under token budget by trimming old tool results.
    Preserves the system prompt and the most recent ~8 messages."""
    import server as srv_mod
    if len(messages) <= 10:
        return messages
    # Keep system + last 8 user/assistant/tool messages
    kept = messages[:1] + messages[-8:]
    return kept


def run_task_autonomous(prompt, task_name="", server=None, model=None,
                        max_turns=40, auto_dump=True, extra_system_prompt=None):
    """Run a task in autonomous model-driven mode.

    Like run_task_steps but instead of pre-defined steps, the model is queried
    each turn to produce the next action. The model is given the task result
    history and a constrained prompt (same style as CODE_AGENT_PROMPT) so it
    navigates the UI / runs tools until the task is done.

    Args:
        prompt: the user's instruction.
        task_name: label.
        server: server instance (needs _chat_with_model or similar).
        model: optional model name to override.
        max_turns: safety cap on model interactions.
        auto_dump: whether to inject UI navigation protocol for UI tasks.
        extra_system_prompt: optional extra instructions appended to the
                             system prompt (e.g. RESEARCH_WORKFLOW_INSTRUCTIONS).

    Returns: TaskResult with outputs containing the model's trajectory.
    """
    if server is None:
        try:
            import server as srv_mod
            server = getattr(srv_mod, "server_instance", None)
        except Exception:
            pass
    result = TaskResult(task_name)
    if server is None:
        result.aborted = True
        result.errors.append("run_task_autonomous: no server instance")
        return result

    from ace_prompt import build_task_prompt

    system_prompt = build_task_prompt(server, auto_dump=auto_dump)
    if extra_system_prompt:
        system_prompt += "\n\n" + extra_system_prompt
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}]

    for turn in range(max_turns):
        import server as srv
        messages = _truncate_messages(messages, max_tokens=2000)
        response = srv.llm_reply(messages, max_tokens=512, temperature=0.3, tool_choice="auto")
        if not response:
            result.aborted = True
            result.errors.append(f"turn {turn}: no model response")
            break

        text, tcs = response if response else ("", [])

        # Model decides next action via tool call or FINAL
        if not tcs:
            final_text = srv._extract_final(text) if text else None
            if final_text or (text and text.strip()):
                result.outputs.append({"turn": turn, "final": final_text or text})
                result.steps_passed += 1
                break
            else:
                result.aborted = True
                result.errors.append(f"turn {turn}: model returned empty reply")
                break

        # Build assistant message with tool_calls so the API can match tool results
        import json as _json
        assistant_msg = {"role": "assistant", "content": text or ""}
        if tcs:
            assistant_msg["tool_calls"] = [
                {"id": "call_%d_%d" % (turn, j), "type": "function",
                 "function": {"name": nm, "arguments": _json.dumps(a or {})}}
                for j, (nm, a) in enumerate(tcs)
            ]
        messages.append(assistant_msg)

        for j, (name, args) in enumerate(tcs):
            args = args if isinstance(args, dict) else {}
            result.steps_run += 1
            ok, msg = _call_tool(server, name, args)
            if ok:
                result.steps_passed += 1
            else:
                result.steps_failed += 1
                result.errors.append(f"turn {turn}: {name} -> {msg}")
            result.outputs.append({"turn": turn, "tool": name, "args": args,
                                   "ok": ok, "msg": str(msg)[:200]})
            messages.append({"role": "tool", "tool_call_id": "call_%d_%d" % (turn, j),
                            "name": name, "content": str(msg)[:2000]})

        if result.steps_failed > 0:
            break
    else:
        result.aborted = (result.steps_failed == 0)
        result.outputs.append({"warning": "max_turns reached"})

    return result
