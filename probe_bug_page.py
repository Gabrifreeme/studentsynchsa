"""What the debug tab holds right now: requests, console, page identity."""
import server as S

ok, msg = S._call_tool("cdp_connect", {"target": "localhost:9999"})
print("connect:", ok, str(msg)[:120])
ok, dom = S._call_tool("cdp_dom_state", {"limit": 2})
print("page   :", S._bug_dom_digest(dom))
ok, logs = S._call_tool("cdp_console_logs", {})
print("console:", S._bug_console_digest(logs)[:500])
for args in ({}, {"filter_status": "4xx,5xx"}, {"filter_url": "attendance"}):
    ok, net = S._call_tool("cdp_network_requests", args)
    txt = str(net)
    print("\nnet %s -> %s" % (args, ok))
    print(txt[:1500])
