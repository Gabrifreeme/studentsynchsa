"""Force a real reload and see whether any requests are captured at all."""
import server as S

print(S._call_tool("cdp_connect", {"target": "localhost:9999"}))
ok, msg = S._call_tool("cdp_navigate", {"url": "http://localhost:9999/?probe=1#/dashboard",
                                        "wait": True, "wait_for": "load"})
print("navigate:", ok, str(msg)[:200])
ok, net = S._call_tool("cdp_network_requests", {"limit": 100})
print("ALL REQUESTS:")
for line in str(net).splitlines()[:30]:
    print("  ", line[:150])
ok, st = S._call_tool("cdp_status", {})
print("status:", str(st)[:300])
