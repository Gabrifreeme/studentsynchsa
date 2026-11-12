import io
path = r"C:\Users\chris\LipSyncStudent\lib\core\router\app_router.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify
assert lines[325].strip() == "),", f"L326 mismatch: {lines[325]!r}"
assert lines[326].strip() == ");", f"L327 mismatch: {lines[326]!r}"

# Insert missing `),` for Container before the Scaffold closer
lines.insert(326, "      )," + eol)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE: Added missing Container closing paren")
