# Unit tests for ACEsi's UI validation tools:
# ui_assert_text / ui_assert_element / ui_assert_visible / ui_expect / ui_test_run.
# Run: python -m unittest test_ui_validation -v
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import server

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.studentsyncsa" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,0][1080,2412]" visible-to-user="true">
    <node index="1" text="Welcome" resource-id="com.studentsyncsa:id/txt_welcome" class="android.widget.TextView" package="com.studentsyncsa" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[100,300][980,400]" visible-to-user="true"/>
    <node index="2" text="" resource-id="com.studentsyncsa:id/btn_login" class="android.widget.Button" package="com.studentsyncsa" content-desc="Log in" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[300,500][780,680]" visible-to-user="true"/>
    <node index="3" text="Forgot password?" resource-id="" class="android.widget.TextView" package="com.studentsyncsa" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,3000][1080,3100]" visible-to-user="false"/>
  </node>
</hierarchy>"""


class UiAssertTest(unittest.TestCase):
    def setUp(self):
        server._ui_dump_nodes = lambda timeout=45: (True, server._ui_parse_nodes(SAMPLE_XML))
        server._ui_screen_size = lambda: (1080, 2412)

    def test_assert_text_finds_substring(self):
        ok, out = server.tool_ui_assert_text("lcome")
        self.assertTrue(ok)
        self.assertIn("PASS", out)

    def test_assert_text_case_insensitive(self):
        ok, out = server.tool_ui_assert_text("WELCOME")
        self.assertTrue(ok)

    def test_assert_text_missing_fails_with_labels(self):
        ok, out = server.tool_ui_assert_text("DefinitelyNotHere")
        self.assertFalse(ok)
        self.assertIn("FAIL", out)
        self.assertIn("Welcome", out)

    def test_assert_text_absent_pass(self):
        ok, out = server.tool_ui_assert_text("DefinitelyNotHere", present=False)
        self.assertTrue(ok)

    def test_assert_text_present_false_when_found(self):
        ok, out = server.tool_ui_assert_text("Welcome", present=False)
        self.assertFalse(ok)

    def test_assert_element_by_resource_id(self):
        ok, out = server.tool_ui_assert_element(resource_id="com.studentsyncsa:id/btn_login")
        self.assertTrue(ok)
        self.assertIn("PASS", out)

    def test_assert_element_by_text(self):
        ok, out = server.tool_ui_assert_element(text="welcome")
        self.assertTrue(ok)

    def test_assert_element_by_desc(self):
        ok, out = server.tool_ui_assert_element(desc="Log in")
        self.assertTrue(ok)

    def test_assert_element_missing(self):
        ok, out = server.tool_ui_assert_element(resource_id="com.studentsyncsa:id/nope")
        self.assertFalse(ok)
        self.assertIn("FAIL", out)

    def test_assert_element_absent_pass(self):
        ok, out = server.tool_ui_assert_element(resource_id="com.studentsyncsa:id/nope", present=False)
        self.assertTrue(ok)

    def test_assert_element_no_selector(self):
        ok, out = server.tool_ui_assert_element()
        self.assertFalse(ok)
        self.assertIn("usage", out)

    def test_assert_visible_visible(self):
        ok, out = server.tool_ui_assert_visible(resource_id="com.studentsyncsa:id/btn_login")
        self.assertTrue(ok)
        self.assertIn("VISIBLE", out)

    def test_assert_visible_offscreen_offscreen(self):
        # "Forgot password?" has bounds starting at y=3000 which exceed screen 2412
        ok, out = server.tool_ui_assert_visible(text="Forgot password?")
        self.assertFalse(ok)
        self.assertIn("FAIL", out)

    def test_assert_visible_by_text(self):
        ok, out = server.tool_ui_assert_visible(text="welcome")
        self.assertTrue(ok)


class UiExpectTest(unittest.TestCase):
    def setUp(self):
        server._ui_dump_nodes = lambda timeout=45: (True, server._ui_parse_nodes(SAMPLE_XML))

    def test_expect_plain_text_present(self):
        ok, out = server.tool_ui_expect("Welcome, Log in")
        self.assertTrue(ok)
        self.assertIn("PASS", out)

    def test_expect_json_present_absent(self):
        ok, out = server.tool_ui_expect('{"present": ["Welcome"], "absent": ["Error", "Oops"]}')
        self.assertTrue(ok)

    def test_expect_missing_fails(self):
        ok, out = server.tool_ui_expect('{"present": ["Welcome", "Error"], "absent": []}')
        self.assertFalse(ok)
        self.assertIn("'Error'", out)

    def test_expect_unexpected_present(self):
        ok, out = server.tool_ui_expect('{"present": [], "absent": ["Log in"]}')
        self.assertFalse(ok)
        self.assertIn("Log in", out)

    def test_expect_empty(self):
        ok, out = server.tool_ui_expect("")
        self.assertFalse(ok)

    def test_expect_newline_fragments(self):
        ok, out = server.tool_ui_expect("Welcome\nLog in")
        self.assertTrue(ok)


class UiTestRunTest(unittest.TestCase):
    def setUp(self):
        server._ui_dump_nodes = lambda timeout=45: (True, server._ui_parse_nodes(SAMPLE_XML))
        server._ui_screen_size = lambda: (1080, 2412)
        self.executed = []

        def fake_call_tool(name, args):
            self.executed.append((name, args))
            if name in ("ui_assert_text", "ui_assert_element", "ui_assert_visible", "ui_expect"):
                return server.TOOLS[name][0](**args)
            return True, "mock ok"

        server._call_tool = fake_call_tool

    def test_run_all_pass(self):
        steps = [
            {"tool": "ui_app_open", "args": {}},
            {"tool": "ui_assert_text", "args": {"text": "Welcome"}},
            {"tool": "ui_assert_element", "args": {"resource_id": "com.studentsyncsa:id/btn_login"}},
            {"tool": "ui_assert_visible", "args": {"text": "Welcome"}},
            {"tool": "ui_expect", "args": {"expected": '{"present": ["Welcome"], "absent": ["Error"]}'}},
        ]
        ok, out = server.tool_ui_test_run(steps, name="login smoke")
        self.assertTrue(ok)
        self.assertIn("TEST PASSED (5/5)", out)
        self.assertEqual([n for n, _ in self.executed],
                         ["ui_app_open", "ui_assert_text", "ui_assert_element",
                          "ui_assert_visible", "ui_expect"])

    def test_run_one_failure(self):
        steps = [
            {"tool": "ui_assert_text", "args": {"text": "Welcome"}},
            {"tool": "ui_assert_text", "args": {"text": "Nope"}},
        ]
        ok, out = server.tool_ui_test_run(steps)
        self.assertFalse(ok)
        self.assertIn("TEST FAILED (1/2)", out)
        self.assertIn("FAIL", out)

    def test_run_json_steps_string(self):
        steps = '[{"tool": "ui_assert_text", "args": {"text": "Welcome"}}]'
        ok, out = server.tool_ui_test_run(steps)
        self.assertTrue(ok)

    def test_run_unknown_tool(self):
        ok, out = server.tool_ui_test_run([{"tool": "nope", "args": {}}])
        self.assertFalse(ok)
        self.assertIn("unknown tool", out)

    def test_run_empty_steps(self):
        ok, out = server.tool_ui_test_run([])
        self.assertFalse(ok)

    def test_last_test_result_recorded(self):
        server.tool_ui_test_run([{"tool": "ui_assert_text", "args": {"text": "Welcome"}}],
                                name="x")
        self.assertEqual(server._UI_LAST_TEST["passed"], 1)
        self.assertEqual(server._UI_LAST_TEST["total"], 1)


class ToolsRegisteredTest(unittest.TestCase):
    def test_new_tools_in_registry_and_schemas(self):
        for name in ("ui_assert_text", "ui_assert_element", "ui_assert_visible",
                     "ui_expect", "ui_test_run"):
            self.assertIn(name, server.TOOLS)
            schema_names = [t["function"]["name"] for t in server.TOOLS_SCHEMA]
            self.assertIn(name, schema_names)
            ollama_names = [t["function"]["name"] for t in server.OLLAMA_TOOLS_SCHEMA]
            self.assertIn(name, ollama_names)

    def test_required_args_matches_schema(self):
        self.assertIn("text", server._REQUIRED_ARGS.get("ui_assert_text", []))
        self.assertIn("expected", server._REQUIRED_ARGS.get("ui_expect", []))
        self.assertIn("steps", server._REQUIRED_ARGS.get("ui_test_run", []))
        self.assertEqual(server._REQUIRED_ARGS.get("ui_assert_visible", []), [])

    def test_call_tool_requires_text(self):
        ok, out = server._call_tool("ui_assert_text", {})
        self.assertFalse(ok)
        self.assertIn("missing REQUIRED argument", out)


class TestBudgetTest(unittest.TestCase):
    def test_test_task_detected(self):
        self.assertTrue(server._test_task("Run the ui_test_run harness and validate the UI"))
        self.assertTrue(server._test_task("assert the login button is visible"))
        self.assertFalse(server._test_task("hello there"))

    def test_test_task_not_nav(self):
        # A validation run is different from a quick screenshot request
        self.assertFalse(server._test_task("open the app and screenshot it"))
        self.assertTrue(server._nav_task("open the app and screenshot it"))

    def test_test_budget_boost_rounds(self):
        # A test task should get a larger max_rounds than the default 20
        result = {}
        import types

        def fake_chat_one(*a, **k):
            return ("FINAL: tests passed", [])

        call_tool_orig = server._call_tool
        server._chat_one = fake_chat_one
        server._call_tool = lambda name, args: (True, "mock")
        server._ui_auto_dump = lambda: (True, "mock")
        msgs = [{"role": "user", "content": "run a ui test run to validate the login screen"}]
        reply = server._chat_dispatch(msgs, max_rounds=20,
                                      user_message="ui_test_run validate login screen")
        server._call_tool = call_tool_orig
        self.assertEqual(reply, "FINAL: tests passed")


class CurlTest(unittest.TestCase):
    def test_usage_when_no_url(self):
        ok, out = server.tool_curl("")
        self.assertFalse(ok)
        self.assertIn("usage", out)

    def test_up_site_returns_2xx(self):
        ok, out = server.tool_curl("https://www.univen.ac.za", timeout=15)
        self.assertTrue(ok)
        self.assertIn("HTTP 200", out)

    def test_down_service_returns_false(self):
        # The ITS portal is currently refusing connections — curl should surface
        # ok=False with a network-level failure (this is the exact 'no web
        # service' signal ACEsi uses to tell Chris the domain is right but the
        # service is down).
        ok, out = server.tool_curl("https://univenierp01.univen.ac.za/pls/prodi41/w99pkg.mi_login",
                                   timeout=15)
        self.assertFalse(ok)
        self.assertIn("curl FAIL", out)

    def test_4xx_is_success_for_caller(self):
        # A server *responding* with 404 still means a web service is up; only
        # transport failures return ok=False.
        ok, out = server.tool_curl("https://www.univen.ac.za/does-not-exist-zzz",
                                   timeout=15, allow_redirects=True)
        self.assertTrue(ok)
        self.assertIn("HTTP", out)

    def test_redirect_off(self):
        ok, out = server.tool_curl("https://www.univen.ac.za", timeout=15,
                                   allow_redirects=False)
        self.assertTrue(ok)
        self.assertIn("HTTP", out)


class DomainGateTest(unittest.TestCase):
    def test_classify_single_domains(self):
        self.assertEqual(server._classify_message("open the app, screenshot it"), {"ui"})
        self.assertEqual(server._classify_message("curl https://x.com"), {"net"})
        self.assertEqual(server._classify_message("read lib/main.dart"), {"code"})
        self.assertEqual(server._classify_message("hello how are you"), {"general"})

    def test_classify_ambiguous_two_domains(self):
        # Asking for BOTH device and URL probe at once is ambiguous
        self.assertGreaterEqual(
            len(server._classify_message("navigate the app to the ITS portal and curl https://univenierp01.univen.ac.za")),
            2)

    def test_domain_tool_names_general_excludes_ui(self):
        names = server._domain_tool_names("general")
        self.assertIn("read_file", names)
        self.assertIn("curl", names)
        self.assertNotIn("ui_tap", names)
        self.assertNotIn("ui_app_open", names)

    def test_domain_tool_names_ui_includes_assertions(self):
        names = server._domain_tool_names("ui")
        self.assertIn("ui_assert_text", names)
        self.assertIn("ui_test_run", names)
        self.assertIn("ui_tap", names)

    def test_ambiguous_request_returns_clarification(self):
        msgs = [{"role": "system", "content": "test"},
                {"role": "user", "content": "curl https://example.com and tap the login button on the emulator"}]
        reply = server._chat_dispatch(msgs, max_rounds=5,
                                      user_message="curl https://example.com and tap the login button on the emulator")
        self.assertIn("which would you like", reply.lower())

    def test_filter_schema(self):
        ui_only = server._filter_tools_schema(server.OLLAMA_TOOLS_SCHEMA,
                                              server._domain_tool_names("ui"))
        names = [t["function"]["name"] for t in ui_only]
        self.assertIn("ui_dump", names)
        self.assertIn("ui_assert_text", names)
        # ui domain excludes network/code tools
        self.assertNotIn("curl", names)
        self.assertNotIn("run_command", names)

    def test_general_schema_includes_net_and_code(self):
        gen = server._filter_tools_schema(server.OLLAMA_TOOLS_SCHEMA,
                                          server._domain_tool_names("general"))
        names = {t["function"]["name"] for t in gen}
        self.assertIn("curl", names)
        self.assertIn("run_command", names)
        self.assertNotIn("ui_tap", names)

    def test_assert_tool_domains_registered(self):
        for n in ("ui_assert_text", "ui_assert_element", "ui_assert_visible",
                  "ui_expect", "ui_test_run", "curl"):
            self.assertEqual(server._TOOL_DOMAINS[n],
                             "ui" if n.startswith("ui_") else "net")


if __name__ == "__main__":
    unittest.main()