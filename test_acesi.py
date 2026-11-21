# -*- coding: utf-8 -*-
"""Test suite for: rate-limit display, auto-delegate guidance, delegate project-root.
Run from any folder:  python D:\\projects\\acesi\\test_acesi.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server

PASS = "PASS"
FAIL = "FAIL"

print("=" * 64)
print("TEST 1: rate-limit header capture + API exposure")
print("=" * 64)
server._record_rate_headers("Groq", {
    "x-ratelimit-limit-tokens": "8000",
    "x-ratelimit-remaining-tokens": "6420",
    "x-ratelimit-reset-tokens": "1m",
    "retry-after": "3",
})
cap = server._RATE_LIMIT_INFO.get("Groq", {})
ok1 = cap.get("remaining_tokens") == "6420" and cap.get("limit_tokens") == "8000"
print("  capture:", cap)
print("  result:", PASS if ok1 else FAIL)

import requests
try:
    d = requests.get("http://127.0.0.1:5000/api/ai/usage", timeout=10).json()
    ok1b = "rate_limits" in d
    print("  /api/ai/usage has rate_limits:", PASS if ok1b else FAIL)
    print("  keys:", sorted(d.keys()))
except Exception as e:
    print("  /api/ai/usage:", FAIL, e)
    ok1b = False

print()
print("=" * 64)
print("TEST 2: auto-delegate guidance in prompts")
print("=" * 64)
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py"), encoding="utf-8").read()
has_full = "DELEGATION:" in src and "use the delegate" in src.lower()
has_reduced = "DEEP INVESTIGATIONS:" in src and "delegate" in src.lower()
print("  full system prompt hint:", PASS if has_full else FAIL)
print("  reduced prompt hint:", PASS if has_reduced else FAIL)

print()
print("=" * 64)
print("TEST 3: delegate sub-agent (live LLM call - needs providers up)")
print("=" * 64)
try:
    ok, report = server.tool_delegate("What is 2+2? Answer in one word.", scope="read")
    ok3 = ok and bool(report.strip())
    print("  OK:", ok)
    print("  report:", report[:200])
    print("  result:", PASS if ok3 else FAIL)
except Exception as e:
    print("  result: FAIL", e)
    ok3 = False

print()
print("=" * 64)
allok = ok1 and ok1b and has_full and has_reduced and ok3
print("OVERALL:", PASS if allok else "PARTIAL (providers may be down)")
print("=" * 64)
