import io
path = r"C:\Users\chris\LipSyncStudent\lib\core\router\app_router.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify
assert "bottomNavigationBar: BottomAppBar(" in lines[290], f"L291 mismatch: {lines[290]!r}"
assert "color: AppColors.surface," in lines[291], f"L292 mismatch: {lines[291]!r}"
assert "elevation: 0," in lines[292], f"L293 mismatch: {lines[292]!r}"

# Replace the three lines with an amber-bordered black bar
new_block = (
    "      bottomNavigationBar: Container(" + eol +
    "        decoration: const BoxDecoration(" + eol +
    "          color: Color(0xFF000000)," + eol +
    "          border: Border(top: BorderSide(color: Color(0xFFFF9D00), width: 1))," + eol +
    "        )," + eol +
    "        child: BottomAppBar(" + eol +
    "        color: Color(0xFF000000)," + eol +
    "        elevation: 0," + eol
)

# Replace lines 291-293 (0-indexed 290-292) with the new block
new_lines = lines[:290] + [new_block] + lines[293:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print("PATCH COMPLETE: BottomAppBar has amber top border")
