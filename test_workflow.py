# -*- coding: utf-8 -*-
"""End-to-end test of ACEsi's find -> fix -> verify workflow.
Run:  python D:\\projects\\acesi\\test_workflow.py
"""
import sys, os, requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server

BASE = "http://127.0.0.1:5000"
PASS, FAIL = "PASS", "FAIL"
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_workflow_test.py")


def section(n, title):
    print("\n" + "=" * 64)
    print("TEST %s: %s" % (n, title))
    print("=" * 64)


# ---------------------------------------------------------------- TEST 1
section(1, "project_doctor - structured checklist of ALL project errors")
ok, report = server.tool_project_doctor()
print(report[:500])
print("  result:", PASS if ok else FAIL)

# ---------------------------------------------------------------- TEST 2
section(2, "doctor_verify_file - clean vs broken file")
with open(TMP, "w", encoding="utf-8") as f:
    f.write("x = 1\n")
clean = server.doctor_verify_file(TMP)
with open(TMP, "w", encoding="utf-8") as f:
    f.write("def broken(:\n  pass\n")
broken = server.doctor_verify_file(TMP)
print("  clean file:", clean, "->", PASS if clean[0] else FAIL)
print("  broken file verified:", broken[0], "| errors:", broken[1][:1])
print("  result:", PASS if (clean[0] and not broken[0]) else FAIL)

# ---------------------------------------------------------------- TEST 3
section(3, "/api/save-file - verified save (clean + broken)")
r1 = requests.post(BASE + "/api/save-file",
                   json={"content": "y = 2\n", "filename": "_workflow_test.py"}, timeout=30).json()
r2 = requests.post(BASE + "/api/save-file",
                   json={"content": "def bad(:\n", "filename": "_workflow_test.py"}, timeout=30).json()
print("  clean save  -> verified:", r1.get("verified"), "| errors:", r1.get("errors"))
print("  broken save -> verified:", r2.get("verified"), "| errors:", (r2.get("errors") or [])[:1])
print("  result:", PASS if (r1.get("verified") is True and r2.get("verified") is False) else FAIL)

# ---------------------------------------------------------------- TEST 4
section(4, "/api/autofix - grounded fix with analyzer diagnostics")
r = requests.post(BASE + "/api/autofix",
                  json={"code": "def f():\n  return 1\n", "filename": "_workflow_test.py"}, timeout=90)
d = r.json()
print("  ok:", d.get("ok"), "| has errors_before:", "errors_before" in d,
      "| filename:", d.get("filename"))
print("  result:", PASS if (d.get("ok") and "errors_before" in d) else FAIL)

# ---------------------------------------------------------------- TEST 5
section(5, "Full loop: broken file -> doctor flags -> save fix -> verified clean")
with open(TMP, "w", encoding="utf-8") as f:
    f.write("def broken(:\n  pass\n")
before = server.doctor_verify_file(TMP)
r = requests.post(BASE + "/api/save-file",
                  json={"content": "def fixed():\n    return 42\n", "filename": "_workflow_test.py"}, timeout=30).json()
after = server.doctor_verify_file(TMP)
print("  before verified:", before[0], "| after verified:", after[0],
      "| save verified:", r.get("verified"))
print("  result:", PASS if (not before[0] and after[0] and r.get("verified")) else FAIL)

# cleanup
try:
    os.remove(TMP)
except OSError:
    pass

print("\n" + "=" * 64)
print("WORKFLOW TEST COMPLETE")
print("=" * 64)
