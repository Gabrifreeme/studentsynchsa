"""Self-contained test for the _final_answer drop-in block.

Run: python dropin_final_answer.py
"""

_DEVICE_TOOLS = ("ui_app_open", "ui_tap", "ui_swipe", "ui_type", "ui_key",
                 "ui_dump", "ui_screenshot", "ui_device")


def _collect_tool_evidence(llm_messages, max_chars=12000):
    """Every tool result in the conversation, oldest first, under one budget."""
    out, used = [], 0
    for m in llm_messages:
        if m.get("role") != "tool":
            continue
        content = str(m.get("content") or "")
        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(content) > remaining:
            content = content[:remaining] + "\n...[TRUNCATED %d further chars]" % (
                len(content) - remaining)
        used += len(content)
        out.append({"tool": str(m.get("name") or "unknown_tool"), "content": content})
    return out


def _last_user_question(llm_messages):
    """The most recent real user turn - not one of the loop's injected nudges."""
    _NUDGE_MARKERS = ("tool call", "SCREEN STATE", "You only described",
                      "You stopped narrating", "You replied with text",
                      "Your previous reply was cut off", "Now provide your final")
    for m in reversed(llm_messages):
        if m.get("role") != "user":
            continue
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        if any(marker.lower() in content.lower() for marker in _NUDGE_MARKERS):
            continue
        return content
    return "the original request"


def _evidence_fallback(evidence, names, max_chars=400):
    """No model available? Show the user the actual findings."""
    lines = []
    if names:
        lines.append("Tools run: %s." % ", ".join(dict.fromkeys(names)))
    if not evidence:
        lines.append("None of them returned usable content.")
        return "\n".join(lines)
    lines.append("What they returned:")
    for i, e in enumerate(evidence, 1):
        snippet = e["content"].strip().replace("\n", " ")
        if len(snippet) > max_chars:
            snippet = snippet[:max_chars] + "..."
        lines.append("%d. %s - %s" % (i, e["tool"], snippet))
    return "\n".join(lines)


def _build_grounded_prompt(question, evidence):
    if not evidence:
        body = "NO TOOL RESULTS WERE COLLECTED. No tool call succeeded in this run."
    else:
        body = "\n\n".join(
            "--- RESULT %d from `%s` ---\n%s" % (i, e["tool"], e["content"])
            for i, e in enumerate(evidence, 1))
    return (
        "Question: %s\n\n"
        "Below is every tool result collected during this run.\n\n"
        "%s\n\n"
        "Answer using ONLY the results above. Cite which result supports each claim, "
        "by its number.\n"
        "If these results do not contain the answer, say exactly: \"The searches did "
        "not establish this.\" Do NOT guess and do NOT answer from memory.\n"
        "Never list tool names as findings - \"web_search\" is not a result."
        % (question, body))


def _final_answer(llm_messages, names, last_screen, active, user_message,
                  chat_one=None):
    """The reply to show the user when the loop ends with work done.

    Replaces the block that produced
    "I performed %d device actions (%s)."
    Never claims device actions for a non-device task, and never reports tool names
    as findings.
    """
    evidence = _collect_tool_evidence(llm_messages)
    device_acts = [n for n in names if n in _DEVICE_TOOLS]

    # Build the prompt for the right kind of task.
    if evidence:
        prompt = _build_grounded_prompt(
            _last_user_question(llm_messages) or user_message, evidence)
        schema = None                      # the summariser must not call tools
    elif device_acts:
        prompt = (
            "The device actions are complete. Actions executed: %s.\n"
            "Write a short final summary (2-3 sentences) of what you did and where "
            "the process ended up. Cite real text from the screen dump below. "
            "Do not call any tools." % ", ".join(dict.fromkeys(device_acts)))
        if last_screen:
            prompt += "\nLast screen seen:\n%s" % last_screen[:3000]
        schema = None
    else:
        # Nothing usable. Say so plainly - never "Actions executed: none."
        return _evidence_fallback(evidence, names)

    # Ask the model, if we can.
    if chat_one is not None and active:
        try:
            msgs = list(llm_messages) + [{"role": "user", "content": prompt}]
            got = chat_one(active[0], active[1], active[2], active[3], msgs,
                           tools_schema=[], tool_choice="none")
        except Exception:
            got = None
        if got:
            text = (got[0] or "").strip() if isinstance(got, (tuple, list)) else str(got).strip()
            if text:
                return text

    # No model, or it failed: still hand back the real findings.
    return _evidence_fallback(evidence, names)


if __name__ == "__main__":
    HARVARD = [
        {"role": "user", "content": "what is the oldest book in the Harvard library?"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "t0"}]},
        {"role": "tool", "tool_call_id": "t0", "name": "web_search",
         "content": '{"results":[{"title":"Papyri at Houghton Library","snippet":"84 manuscripts dating from the 3rd century BCE to the 6th century CE"}]}'},
        {"role": "user", "content": "You replied with text but called no tool. Emit a tool call NOW."},
    ]
    NAMES = ["web_search"]

    # ---- what ACEsi shows today (server.py:1596-1611, verbatim) ----
    acts = ", ".join(n for n in NAMES if n in _DEVICE_TOOLS)
    today = "I performed %d device actions (%s). %s" % (len(NAMES), acts, "")
    today += " The model didn't produce a final summary before the action cap."
    print("TODAY:")
    print("  " + today)

    # ---- no model available: the fallback floor ----
    no_model = _final_answer(HARVARD, NAMES, None, None, "q", chat_one=None)
    print("\nAFTER (no model reachable):")
    for line in no_model.splitlines():
        print("  " + line)

    # ---- with a model: it receives a grounded prompt ----
    seen = {}

    def fake_chat_one(name, endpoint, key, model, msgs, tools_schema=None, **kw):
        seen["prompt"] = msgs[-1]["content"]
        seen["schema"] = tools_schema
        return ("Result 1 identifies Houghton's papyri, dating from the 3rd century "
                "BCE to the 6th century CE.", [], "stop")

    active = ("Groq", "https://api.groq.com/v1", "key", "llama-3.3-70b")
    answered = _final_answer(HARVARD, NAMES, None, active, "q", chat_one=fake_chat_one)
    print("\nAFTER (model available):")
    print("  " + answered)

    checks = [
        ("today's message is the broken one", "device actions" in today),
        ("fallback never says 'device actions'", "device actions" not in no_model),
        ("fallback shows real findings", "3rd century BCE" in no_model),
        ("fallback does not list bare tool names as findings",
         no_model != "web_search, web_search"),
        ("model got the evidence in its prompt", "3rd century BCE" in seen.get("prompt", "")),
        ("model was told not to list tool names",
         "Never list tool names as findings" in seen.get("prompt", "")),
        ("summariser cannot call tools", seen.get("schema") == []),
        ("model's grounded answer is returned", "3rd century BCE" in answered),
        ("nudge text is not used as the question",
         "what is the oldest book" in seen.get("prompt", "")),
    ]

    print("\n" + "=" * 62)
    ok = True
    for label, passed in checks:
        print("  %s  %s" % ("PASS" if passed else "FAIL", label))
        ok = ok and passed
    print("=" * 62)
    print("ALL PASS" if ok else "SOME FAILED")

    # device-task path must still work
    DEV = [{"role": "user", "content": "open the app and tap login"},
           {"role": "tool", "name": "ui_dump", "content": "LOGIN button at [100,200]"}]
    dev_out = _final_answer(DEV, ["ui_app_open", "ui_dump"], "LOGIN button", active,
                            "q", chat_one=lambda *a, **k: ("Opened the app and tapped login.", [], "stop"))
    print("\nDEVICE TASK still works:", "Opened the app" in dev_out)

    # nothing-at-all path
    empty = _final_answer([{"role": "user", "content": "hi"}], [], None, None, "q", chat_one=None)
    print("EMPTY RUN says so plainly:", "None of them returned usable content." in empty)
