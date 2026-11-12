import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[9615].endswith("\r\n") else "\n"

# Verify (1-indexed 9617 -> 0-indexed 9616) is blank, and 9619 (0-indexed 9618) is "try {"
assert "var fullKey" in lines[9615], f"L9616 mismatch: {lines[9615]!r}"

# Insert duplicate check AFTER line 9616 (0-indexed 9615) and before try block
check_block = (
    "" + eol +
    "        // Duplicate check" + eol +
    "        try {" + eol +
    "          var checkResp = await fetch(\"http://127.0.0.1:5000/memory/get?key=\" + encodeURIComponent(fullKey));" + eol +
    "          if (checkResp.ok) {" + eol +
    "            var checkData = await checkResp.json();" + eol +
    "            if (checkData && checkData.value !== undefined && checkData.value !== null) {" + eol +
    "              if (window.showAceToast) window.showAceToast(\"Skill already exists: \" + fullKey, 'error', 4000);" + eol +
    "              return;" + eol +
    "            }" + eol +
    "          }" + eol +
    "        } catch(e) { /* ignore check errors */ }" + eol
)

# Insert at index 9616 (after line 9616)
lines.insert(9616, check_block)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Inserted duplicate check after line 9616")
