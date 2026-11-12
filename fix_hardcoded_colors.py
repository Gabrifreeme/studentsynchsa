import io

files = [
    r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\funding\funding_list_screen.dart",
    r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\universities\universities_screen.dart",
]

# Replace hardcoded old colors with amber equivalents
replacements = {
    "0xFF2A3A6A": "0xFFFF9D00",  # border -> amber
    "0xFF1E293B": "0xFF333333",  # divider -> dark grey
    "0xFF7C3AED": "0xFFFF9D00",  # primary purple -> amber
    "0xFF1A1F35": "0xFF111111",  # surface -> dark grey
}

for path in files:
    with io.open(path, "r", encoding="utf-8", newline="") as f:
        content = f.read()
    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)
    if content != original:
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        print(f"UPDATED: {path.split(chr(92))[-1]}")
    else:
        print(f"SKIPPED: {path.split(chr(92))[-1]}")

print("PATCH COMPLETE")
