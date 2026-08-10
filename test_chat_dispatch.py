# Regression test: /chat's agent loop must EXECUTE tool calls (ui_*, etc.)
# instead of deferring to the user. Run: python -m unittest test_chat_dispatch -v
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import server


class ChatDispatchTest(unittest.TestCase):
    def setUp(self):
        # Scripted model: turn 1 -> ui_app_open, turn 2 -> ui_screenshot,
        # turn 3 -> plain text reply. Simulates the reported failure case.
        self.executed = []
        self.script = [
            ("", [("ui_app_open", {})]),
            ("", [("ui_screenshot", {"name": "navigation"})]),
            ("Opened the app and captured ui_screenshots/navigation.png.", []),
        ]

        def fake_chat_one(name, endpoint, api_key, model, msgs, timeout=(10, 90)):
            return self.script.pop(0)

        def fake_call_tool(name, args):
            self.executed.append((name, args))
            if name == "ui_app_open":
                return True, "app launched (monkey)"
            return True, "saved ui_screenshots/navigation.png (monkey)"

        server._chat_one = fake_chat_one
        server._call_tool = fake_call_tool

    def tearDown(self):
        import importlib
        importlib.reload(server)  # restore real _chat_one/_call_tool

    def test_ui_instructions_execute_tools(self):
        msgs = [{"role": "system", "content": "test"},
                {"role": "user", "content": "open the app, navigate, and take a screenshot"}]
        reply = server._chat_dispatch(msgs, max_rounds=5)
        self.assertEqual(reply, "Opened the app and captured ui_screenshots/navigation.png.")
        self.assertEqual([t[0] for t in self.executed], ["ui_app_open", "ui_screenshot"])
        # tool results were fed back to the model between rounds
        roles = [m["role"] for m in msgs]
        self.assertIn("tool", roles)

    def test_plain_reply_does_not_need_tools(self):
        server._chat_one = lambda *a, **k: ("Just chatting.", [])
        msgs = [{"role": "system", "content": "test"},
                {"role": "user", "content": "hello"}]
        reply = server._chat_dispatch(msgs, max_rounds=3)
        self.assertEqual(reply, "Just chatting.")

    def test_all_providers_down_returns_none(self):
        server._chat_one = lambda *a, **k: None
        reply = server._chat_dispatch([{"role": "user", "content": "hi"}], max_rounds=2)
        self.assertIsNone(reply)


if __name__ == "__main__":
    unittest.main()
