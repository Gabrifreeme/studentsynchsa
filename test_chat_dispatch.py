# Regression test: /chat's agent loop must EXECUTE tool calls (ui_*, etc.)
# instead of deferring to the user. Run: python -m unittest test_chat_dispatch -v
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import server


class ChatDispatchTest(unittest.TestCase):
    def setUp(self):
        # Scripted model: turn 1 -> ui_app_open, turn 2 -> ui_tap, turn 3 ->
        # ui_dump, turn 4 -> ui_screenshot, turn 5 -> plain text reply.
        # Simulates correct navigation (an action + reading the screen).
        self.executed = []
        self.script = [
            ("", [("ui_app_open", {})]),
            ("", [("ui_tap", {"x": 540, "y": 2300})]),
            ("", [("ui_dump", {})]),
            ("", [("ui_screenshot", {"name": "navigation"})]),
            ("Opened the app and captured ui_screenshots/navigation.png.", []),
        ]

        def fake_chat_one(name, endpoint, api_key, model, msgs, timeout=(10, 90), extra_options=None, tools_schema=None, tool_choice="auto"):
            return self.script.pop(0)

        def fake_call_tool(name, args):
            self.executed.append((name, args))
            if name == "ui_app_open":
                return True, "app launched (monkey)"
            if name == "ui_tap":
                return True, "tap sent (monkey)"
            if name == "ui_dump":
                return True, "mock screen dump"
            if name == "ui_assert_text":
                return True, "PASS: found mock label"
            return True, "saved ui_screenshots/navigation.png (monkey)"

        def fake_auto_dump():
            return True, "mock screen dump"

        server._chat_one = fake_chat_one
        server._call_tool = fake_call_tool
        server._ui_auto_dump = fake_auto_dump

    def tearDown(self):
        import importlib
        importlib.reload(server)  # restore real _chat_one/_call_tool/_ui_auto_dump

    def test_ui_instructions_execute_tools(self):
        msgs = [{"role": "system", "content": "test"},
                {"role": "user", "content": "open the app, navigate, and take a screenshot"}]
        reply = server._chat_dispatch(msgs, max_rounds=5,
                                      user_message="open the app, navigate, and take a screenshot")
        self.assertEqual(reply, "Opened the app and captured ui_screenshots/navigation.png.")
        self.assertEqual([t[0] for t in self.executed],
                         ["ui_app_open", "ui_tap", "ui_dump", "ui_screenshot"])
        # tool results were fed back to the model between rounds
        roles = [m["role"] for m in msgs]
        self.assertIn("tool", roles)

    def test_fake_navigation_is_rejected(self):
        # Model opens the app and screenshots WITHOUT navigating/reading the
        # screen. The nav gate must reject the "done" text and force more work.
        self.script = [
            ("", [("ui_app_open", {})]),
            ("", [("ui_screenshot", {"name": "login"})]),
            ("Done, here is the screenshot.", []),          # must be rejected
            ("", [("ui_tap", {"x": 540, "y": 2300})]),      # corrected behaviour
            ("", [("ui_dump", {})]),
            ("", [("ui_screenshot", {"name": "portal"})]),
            ("Reached the portal.", []),
        ]
        msgs = [{"role": "system", "content": "test"},
                {"role": "user", "content": "open the app and navigate to the portal, screenshot it"}]
        reply = server._chat_dispatch(msgs, max_rounds=8,
                                      user_message="open the app and navigate to the portal, screenshot it")
        self.assertEqual(reply, "Reached the portal.")
        self.assertIn("ui_dump", [t[0] for t in self.executed])
        self.assertIn("ui_tap", [t[0] for t in self.executed])
        # The corrective message was fed back before the model corrected itself
        corrective = [m["content"] for m in msgs if isinstance(m.get("content"), str)
                      and "You took a screenshot but" in m["content"]]
        self.assertTrue(corrective)

    def test_plain_reply_does_not_need_tools(self):
        server._chat_one = lambda *a, **k: ("Just chatting.", [])
        msgs = [{"role": "system", "content": "test"},
                {"role": "user", "content": "hello"}]
        reply = server._chat_dispatch(msgs, max_rounds=3, user_message="hello")
        self.assertEqual(reply, "Just chatting.")

    def test_narrated_plan_is_pushed_to_call_tools(self):
        # Model answers a navigation request with prose only (no tool calls) —
        # the dispatch must reject it and push the model to emit a real tool
        # call, not return the narrated plan as the reply.
        self.script = [
            ("My plan: open the app, then dump the UI, then tap the Venda portal "
             "tile, then screenshot.", []),                # prose, no tools -> pushed
            ("", [("ui_app_open", {})]),
            ("", [("ui_tap", {"x": 540, "y": 2300})]),
            ("", [("ui_dump", {})]),
            ("", [("ui_screenshot", {"name": "portal"})]),
            ("Reached the portal.", []),
        ]
        msgs = [{"role": "system", "content": "test"},
                {"role": "user", "content": "open the app and navigate to the portal, screenshot it"}]
        reply = server._chat_dispatch(msgs, max_rounds=8,
                                      user_message="open the app and navigate to the portal, screenshot it")
        self.assertEqual(reply, "Reached the portal.")
        self.assertEqual([t[0] for t in self.executed],
                         ["ui_app_open", "ui_tap", "ui_dump", "ui_screenshot"])
        pushed = [m["content"] for m in msgs if isinstance(m.get("content"), str)
                  and "only described a plan" in m["content"]]
        self.assertTrue(pushed)

    def test_all_providers_down_returns_none(self):
        server._chat_one = lambda *a, **k: None
        reply = server._chat_dispatch([{"role": "user", "content": "hi"}], max_rounds=2,
                                      user_message="hi")
        self.assertIsNone(reply)


class RunAgentNavGateTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import server as s
        self.server = s

    def tearDown(self):
        import importlib
        importlib.reload(self.server)  # restore real llm_reply/_call_tool/_ui_auto_dump

    def test_run_agent_gates_plain_text_screenshot_reply(self):
        # Native tool-calling model that finishes with plain prose (no FINAL:
        # prefix) after opening the app + screenshot. The gate must reject it,
        # push the model to use ui_dump/navigation, and only accept once it
        # reads the screen before the final screenshot.
        self.executed = []
        script = [
            (None, [("ui_app_open", {})]),
            (None, [("ui_screenshot", {"name": "login"})]),
            ("Done. Screenshot saved.", []),              # plain text -> must be gated
            (None, [("ui_tap", {"x": 540, "y": 2300})]),
            (None, [("ui_dump", {})]),
            (None, [("ui_screenshot", {"name": "portal"})]),
            ("FINAL: Reached the portal.", []),
        ]

        def fake_llm(messages, **kw):
            return script.pop(0)

        def fake_call_tool(name, args):
            self.executed.append(name)
            return True, "mock ok"

        def fake_auto_dump():
            return True, "mock screen"

        self.server.llm_reply = fake_llm
        self.server._call_tool = fake_call_tool
        self.server._ui_auto_dump = fake_auto_dump
        self.server.run_agent("open the app, navigate to the portal, take a screenshot, show me")
        self.assertEqual(self.server._AGENT["last_reply"], "Reached the portal.")
        # The plain-text "Done. Screenshot saved." was NOT accepted as final —
        # the loop gated it and kept going until the model navigated (ui_tap)
        # and read the screen (ui_dump) before the final screenshot.
        self.assertEqual(self.executed, ["ui_app_open", "ui_screenshot",
                                         "ui_tap", "ui_dump", "ui_screenshot"])


    def test_run_agent_executes_emitted_plan_in_order(self):
        # The model emits a full navigation plan in ONE reply (open -> tap ->
        # dump -> screenshot). The server must execute all of it in order and
        # feed results back — not drop everything but the first call.
        self.executed = []
        script = [
            (None, [("ui_app_open", {}),
                    ("ui_tap", {"x": 540, "y": 1200}),
                    ("ui_dump", {}),
                    ("ui_screenshot", {"name": "portal"})]),
            ("FINAL: Reached the portal.", []),
        ]

        def fake_llm(messages, **kw):
            return script.pop(0)

        def fake_call_tool(name, args):
            self.executed.append((name, args))
            return True, "mock ok"

        def fake_auto_dump():
            return True, "mock screen"

        self.server.llm_reply = fake_llm
        self.server._call_tool = fake_call_tool
        self.server._ui_auto_dump = fake_auto_dump
        self.server.run_agent("open the app and go to the portal, take a screenshot")
        self.assertEqual(self.server._AGENT["last_reply"], "Reached the portal.")
        self.assertEqual([t[0] for t in self.executed],
                         ["ui_app_open", "ui_tap", "ui_dump", "ui_screenshot"])


def test_round_cap_returns_action_summary(self):
        # Model keeps emitting tool calls and never produces a final text reply.
        # The dispatch must not return None/"Error: no models available" — it
        # reports the actions actually performed on the device.
        server._chat_one = lambda *a, **k: ("", [("ui_tap", {"x": 540, "y": 1200})])
        msgs = [{"role": "system", "content": "test"},
                {"role": "user", "content": "navigate to the portal and screenshot"}]
        reply = server._chat_dispatch(msgs, max_rounds=3,
                                      user_message="navigate to the portal and screenshot")
        self.assertIn("device actions", reply)
        self.assertIn("ui_tap", reply)


class ChatDispatchProseCallTest(unittest.TestCase):
    """Small models (Ollama qwen2.5) often write tool calls in PROSE --
    'CALL: ui_tap {...}' / fenced JSON -- instead of native tool_calls.
    /chat must execute those too (like run_agent), otherwise the run stalls at
    'I performed 2 device actions' with no real navigation."""

    def setUp(self):
        self.executed = []
        self.script = [
            # turn 1: prose CALL lines, NO native tool_calls
            ("I will open the app and navigate.\nCALL: ui_app_open {}\n"
             "CALL: ui_dump {}\nNow tapping the portal.\n", []),
            ("CALL: ui_tap {\"x\": 540, \"y\": 2300}\n",
             [("ui_tap", {"x": 540, "y": 2300})]),
            ("Done, I reached the portal.", []),
        ]

        def fake_chat_one(name, endpoint, api_key, model, msgs, timeout=(10, 90), extra_options=None, tools_schema=None, tool_choice="auto"):
            return self.script.pop(0)

        def fake_call_tool(name, args):
            self.executed.append((name, args))
            if name == "ui_app_open":
                return True, "app launched"
            if name == "ui_tap":
                return True, "tap sent"
            if name == "ui_dump":
                return True, "mock screen dump"
            return True, "mock"

        def fake_auto_dump():
            return True, "mock screen dump"

        server._chat_one = fake_chat_one
        server._call_tool = fake_call_tool
        server._ui_auto_dump = fake_auto_dump

    def tearDown(self):
        import importlib
        importlib.reload(server)

    def test_chat_executes_prose_call_lines(self):
        msgs = [{"role": "system", "content": "test"},
                {"role": "user", "content": "open the app, go to the portal, screenshot it"}]
        reply = server._chat_dispatch(msgs, max_rounds=5,
                                      user_message="open the app, go to the portal, screenshot it")
        self.assertEqual(reply, "Done, I reached the portal.")
        # The two prose CALL: lines from turn 1 must have been EXECUTED even
        # though they arrived with zero native tool_calls, AND since the user
        # asked to screenshot it but the model finished text-only, the server
        # auto-captures a screenshot (ui_screenshot appended by _chat_dispatch).
        self.assertEqual([t[0] for t in self.executed],
                         ["ui_app_open", "ui_dump", "ui_tap", "ui_screenshot"])


class CertWarningTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import server as s
        self.server = s

    def test_directive_detects_cert_warning(self):
        dump = "15 labeled nodes\nYour connection is not private @ tap(539,731)\nNET::ERR_CERT_DATE_INVALID"
        directive = self.server._cert_warning_directive(dump)
        self.assertTrue(directive)
        self.assertIn("thisisunsafe", directive)

    def test_directive_empty_on_normal_screen(self):
        dump = "33 labeled nodes\nUniversities @ tap(540,1792)\nHome @ tap(120,2226)"
        self.assertEqual(self.server._cert_warning_directive(dump), "")

    def test_auto_bypass_types_thisisunsafe(self):
        called = []
        self.server._call_tool = lambda name, args: (called.append((name, args)) or True, "typed")
        fake_dump = lambda: (True, "Your connection is not private @ tap(539,731)")
        self.server._ui_auto_dump = fake_dump
        msgs = self.server._auto_bypass_cert_warning("NET::ERR_CERT_DATE_INVALID You cannot visit")
        self.assertEqual(called[0], ("ui_type", {"text": "thisisunsafe"}))
        text = "\n".join(m["content"] for m in msgs)
        self.assertIn("thisisunsafe", text)


class NullArgsTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import server as s
        self.server = s

    def test_ui_tap_null_args_rejected_with_clear_error(self):
        ok, err = self.server._call_tool("ui_tap", {"x": None, "y": None})
        self.assertFalse(ok)
        self.assertIn("missing REQUIRED argument", err)
        self.assertIn("x", err)
        self.assertIn("y", err)

    def test_ui_type_null_text_rejected(self):
        ok, err = self.server._call_tool("ui_type", {"text": None})
        self.assertFalse(ok)
        self.assertIn("text", err)

    def test_ui_key_null_rejected(self):
        ok, err = self.server._call_tool("ui_key", {"key": None})
        self.assertFalse(ok)
        self.assertIn("key", err)

    def test_missing_key_treated_like_null(self):
        ok, err = self.server._call_tool("ui_tap", {"x": 100})
        self.assertFalse(ok)
        self.assertIn("y", err)


class ScreenshotBehaviorTest(unittest.TestCase):
    """ui_screenshot must NOT write to disk by default; it buffers in memory
    for the frontend popup and only saves when Chris asks (save=true)."""

    def setUp(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import server as s
        self.server = s
        self.server._LAST_SHOT["png"] = b""
        self.server._LAST_SHOT["ts"] = 0

    def _fake_screencap(self, png=True):
        class R:
            stdout = b"\x89PNG\r\n\x1a\nfakeimage" if png else b"not-a-png"
            stderr = ""
        self.server.subprocess.run = lambda *a, **k: R()

    def test_screenshot_not_saved_by_default(self):
        self._fake_screencap()
        shots_dir = self.server.ACE_UI_SHOTS
        before = set(os.listdir(shots_dir))
        ok, res = self.server.tool_ui_screenshot()
        after = set(os.listdir(shots_dir))
        self.assertTrue(ok)
        self.assertEqual(before, after)  # NOTHING written to disk
        self.assertIn("NOT saved", res)
        self.assertIn("popup", res)
        self.assertEqual(self.server._LAST_SHOT["ts"], 1)
        self.assertTrue(self.server._LAST_SHOT["png"].startswith(b"\x89PNG"))

    def test_screenshot_saved_only_when_requested(self):
        self._fake_screencap()
        shots_dir = self.server.ACE_UI_SHOTS
        before = set(os.listdir(shots_dir))
        ok, res = self.server.tool_ui_screenshot(save=True)
        after = set(os.listdir(shots_dir))
        self.assertTrue(ok)
        self.assertEqual(len(after - before), 1)  # exactly ONE new file
        self.assertIn("SAVED", res)
        self.assertEqual(self.server._LAST_SHOT["ts"], 1)
        # cleanup the file we just created
        for f in after - before:
            os.remove(os.path.join(shots_dir, f))

    def test_ui_screenshot_with_save_arg_through_call_tool(self):
        # The model's emitted plan may pass save:true; _call_tool must forward it.
        self._fake_screencap()
        shots_dir = self.server.ACE_UI_SHOTS
        before = set(os.listdir(shots_dir))
        ok, res = self.server._call_tool("ui_screenshot", {"name": "portal", "save": True})
        after = set(os.listdir(shots_dir))
        self.assertTrue(ok)
        self.assertEqual(len(after - before), 1)
        self.assertIn("SAVED", res)
        for f in after - before:
            os.remove(os.path.join(shots_dir, f))


if __name__ == "__main__":
    unittest.main()
